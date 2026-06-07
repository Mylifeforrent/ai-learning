# test-case-multi-agents

This project demonstrates a Microsoft AutoGen AgentChat workflow for document-driven test-case generation:

1. User uploads or pastes a requirement document.
2. `FileReadAgent` reads the file metadata and bytes.
3. `DocumentParseAgent` parses supported formats into Markdown.
4. A human confirms or edits the parsed Markdown.
5. `TestCaseWriter` generates test cases from the confirmed parsed content.
6. `TestCaseReviewer` reviews the generated test cases.
7. A human approves the final result or rejects it with feedback for another writer/reviewer cycle.

The implementation follows the AutoGen AgentChat team pattern from the official Teams tutorial and uses a suitable termination setup based on the Termination tutorial:

- `RoundRobinGroupChat` runs `TestCaseWriter -> TestCaseReviewer -> HumanReviewer` in order for the CLI.
- `UserProxyAgent` pauses for human review in the console.
- `TextMentionTermination("HUMAN_APPROVED")` stops the workflow when the human approves.
- `MaxMessageTermination` is a safety stop so the loop cannot continue forever.
- The web frontend adds a pre-generation human confirmation gate for parsed document content.

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

The app dependencies are locked to AutoGen `0.7.5`.

Local Marker parsing must be installed in a separate parser environment because current
`marker-pdf` releases require `Pillow<11`, while `autogen-core` requires `Pillow>=11`.
The latest stable Marker version is pinned in `requirements/marker.txt`:

```bash
python -m venv .venv-marker
source .venv-marker/bin/activate
pip install -r requirements/marker.txt
```

For tests and generated fixtures:

```bash
pip install -e ".[test]"
```

Edit `.env` and set `DEEPSEEK_API_KEY`.

By default the project uses DeepSeek's OpenAI-compatible endpoint:

```text
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash
```

Document parsing configuration:

```text
DOCUMENT_MAX_UPLOAD_MB=20
DOCUMENT_PARSER_MODE=local_first
DATALAB_API_KEY=
MARKER_OUTPUT_FORMAT=markdown
MARKER_USE_LLM=true
MARKER_LLM_PROVIDER=qianwen
MARKER_FORCE_OCR=false
MARKER_PAGE_RANGE=
MARKER_DISABLE_IMAGE_EXTRACTION=false
MARKER_BLOCK_CORRECTION_PROMPT=
MARKER_QIANWEN_API_KEY=
MARKER_QIANWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
MARKER_QIANWEN_MODEL=qwen3-vl-flash
MARKER_DEEPSEEK_API_KEY=
MARKER_DEEPSEEK_BASE_URL=https://api.deepseek.com
MARKER_DEEPSEEK_MODEL=deepseek-v4-flash
MARKER_OPENAI_API_KEY=
MARKER_OPENAI_BASE_URL=
MARKER_OPENAI_MODEL=
```

The default parser is intentionally lightweight. It supports `md`, `txt`, `csv`, and `xlsx` locally.
`pdf`, `docx`, images, and other complex documents are routed to the optional local Marker backend.
If `marker-pdf` is not installed, the parser returns a clear setup error with the `requirements/marker.txt` install hint.

Marker LLM enhancement is enabled by default through a provider adapter:

- `MARKER_LLM_PROVIDER=qianwen` uses Alibaba Cloud Bailian/DashScope's OpenAI-compatible endpoint and defaults to `qwen3-vl-flash`. Use `qwen3-vl-plus` when you prefer stronger multimodal quality over speed/cost.
- `MARKER_LLM_PROVIDER=deepseek` uses DeepSeek's OpenAI-compatible endpoint and defaults to `deepseek-v4-flash`.
- `MARKER_LLM_PROVIDER=custom` uses the generic `MARKER_OPENAI_API_KEY`, `MARKER_OPENAI_BASE_URL`, and `MARKER_OPENAI_MODEL` values.

Official references:

- DeepSeek OpenAI-compatible API: https://api-docs.deepseek.com/
- Qwen-VL OpenAI-compatible API: https://help.aliyun.com/zh/model-studio/qwen-vl-compatible-with-openai

## Portable Document Parse Agent

The reusable parser lives in `src/document_parse_agent/` and has no AutoGen or FastAPI dependency.
You can migrate it to another project as a small standalone package:

```python
from document_parse_agent import DocumentParseAgent, ParseOptions

agent = DocumentParseAgent(
    ParseOptions(
        output_format="markdown",
        use_llm=True,
        llm_provider="qianwen",
    )
)

result = agent.parse_file("requirements.pdf")
print(result.content_markdown)
```

Public entry points:

- `parse_bytes(filename, content, mime_type="")`
- `parse_file(path, mime_type="")`
- `parse_text(content, filename="pasted-requirement.md")`

The normalized result includes `document_id`, `filename`, `mime_type`, `backend`, `parser` compatibility alias,
`output_format`, `content_markdown`, `content_raw`, `metadata`, `warnings`, `parse_quality_score`, and `assets`.

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

The frontend first uploads a document to:

```text
POST /api/documents/parse/stream
```

This endpoint streams `FileReadAgent` and `DocumentParseAgent` events and returns parsed Markdown.
The user can edit and confirm that parsed Markdown before generation.

After parse confirmation, the frontend posts the human-confirmed content to:

```text
POST /api/review
```

or the streaming endpoint:

```text
POST /api/review/stream
```

The backend returns a draft from `TestCaseWriter`, review comments from `TestCaseReviewer`, and then
waits for the user to approve or reject in the browser. Rejection feedback is sent to:

```text
POST /api/revise
```

The final result is only marked done in the UI after the user clicks `Approve final`.
The web review team stops when `TestCaseReviewer` responds, with `max_messages` kept as a safety limit.
Do not set `max_messages` below `4`, because AutoGen can count the initial task message as part of the run.

The old text-only `/api/review` shape remains backward compatible through the `requirement` field.
New clients should send `confirmed_content`, `parsed_document_id`, and optionally `parsed_document`.
