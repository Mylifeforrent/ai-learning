# test-case-multi-agents

This project demonstrates a Microsoft AutoGen AgentChat workflow for:

1. Test-case generation from requirements.
2. AI review of the generated test cases.
3. Human review and double confirmation.
4. Final test-case output to a markdown file.

The implementation follows the AutoGen AgentChat team pattern from the official Teams tutorial and uses a suitable termination setup based on the Termination tutorial:

- `RoundRobinGroupChat` runs `TestCaseWriter -> TestCaseReviewer -> HumanReviewer` in order.
- `UserProxyAgent` pauses for human review in the console.
- `TextMentionTermination("HUMAN_APPROVED")` stops the workflow when the human approves.
- `MaxMessageTermination` is a safety stop so the loop cannot continue forever.

Official references:

- Teams: https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/teams.html
- Human-in-the-loop: https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/human-in-the-loop.html
- Termination: https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/termination.html

## Setup

```bash
cd 03_AssistantAgent及Team核心基础/test-case-multi-agents
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
```

Edit `.env` and set `DEEPSEEK_API_KEY`.

By default the project uses DeepSeek's OpenAI-compatible endpoint:

```text
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash
```

The backend loads `.env` from the project root. If your env file is somewhere else, set:

```bash
export DEEPSEEK_ENV_PATH=/absolute/path/to/your/.env
```

## Run

```bash
test-case-agents
```

Or run the module directly:

```bash
python -m test_case_multi_agents.main
```

When the console asks for human input:

- Type feedback to request another revision.
- Type `HUMAN_APPROVED` to confirm the reviewed test cases and terminate the team.

The final output is written to:

```text
outputs/final_test_cases.md
```

## Stream Event Handling

The CLI consumes `team.run_stream(...)` directly instead of using `Console(...)`.
This makes the workflow easier to understand and customize:

- `ModelClientStreamingChunkEvent`: token/chunk-level streaming output from an LLM-backed agent.
- `TextMessage`: one complete message from an agent or the human reviewer.
- `TaskResult`: final result for the whole team run, including all messages and the stop reason.

Because `RoundRobinGroupChat` rotates through the participants in order, human feedback that does not
contain `HUMAN_APPROVED` becomes part of the conversation history and the next turn returns to
`TestCaseWriter` for another revision.

## Custom Requirement File

```bash
test-case-agents --requirements path/to/your_requirement.md --output outputs/my_test_cases.md
```

You can also override the DeepSeek model or endpoint:

```bash
test-case-agents --model deepseek-v4-pro --base-url https://api.deepseek.com
```

## Web Frontend

This project also includes a lightweight HTML/CSS/JS frontend served by FastAPI.

```bash
test-case-agents-api --host 127.0.0.1 --port 8000
```

Then open:

```text
http://127.0.0.1:8000
```

The frontend posts the user's requirement to:

```text
POST /api/review
```

The backend returns a draft from `TestCaseWriter`, review comments from `TestCaseReviewer`, and then
waits for the user to approve or reject in the browser. Rejection feedback is sent to:

```text
POST /api/revise
```

The final result is only marked done in the UI after the user clicks `Approve final`.
The web review team stops when `TestCaseReviewer` responds, with `max_messages` kept as a safety limit.
Do not set `max_messages` below `4`, because AutoGen can count the initial task message as part of the run.

After each draft or revision, the backend also runs `TestCaseCounter`, an AutoGen assistant with the
`count_chinese_characters` tool. Its `ToolCallRequestEvent`, `ToolCallExecutionEvent`, and
`ToolCallSummaryMessage` are included in the frontend agent trace, and the Chinese-character count is
shown above the human review controls.
