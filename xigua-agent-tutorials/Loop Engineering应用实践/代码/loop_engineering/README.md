# Loop Engineering: Documentation Agent

A modular Python project that turns the documentation-agent example from LangChain's **[The Art of Loop Engineering](https://www.langchain.com/blog/the-art-of-loop-engineering)** article into runnable code.

The article describes an internal agent that receives documentation requests, edits a repository, verifies the result, runs from external events, and improves its harness from traces. The internal Fleet and LangSmith Engine implementation is not published, so this repository recreates the same architecture with open, inspectable components:

1. **Agent loop** — LangChain `create_agent` repeatedly calls repository tools.
2. **Verification loop** — deterministic checks and an optional LLM judge grade the diff; failed attempts are retried with feedback.
3. **Event-driven loop** — FastAPI accepts a Slack-like documentation request and runs it in an isolated Git clone.
4. **Hill-climbing loop** — local traces are analyzed into a bounded harness-improvement proposal that requires human approval.

The project deliberately creates a **local pull-request draft** rather than pushing to GitHub. That makes the video safe and reproducible. A production implementation can replace the publisher adapter with a GitHub App integration.

## Architecture

```text
                    External Request / CLI
                            |
                            v
                +---------------------------+
                | Loop 3 (optional facade)  |
                | FastAPI / CLI / Slack     |
                +---------------------------+
                            |
                            v
                 Create isolated workspace
                            |
                            v
        +-------------------------------------------+
        |       Loop 2: Verification Loop           |
        |-------------------------------------------|
        |                                           |
        |  Run Loop 1                               |
        |       |                                   |
        |       v                                   |
        |  Agent edits documentation                |
        |       |                                   |
        |       v                                   |
        |  Deterministic checks                     |
        |  + LLM judge                              |
        |       |                                   |
        |       +------ Pass? ------------------+   |
        |              |                        |   |
        |             No                        |Yes|
        |              |                        |   |
        |      Feedback to Loop 1              Exit |
        |___________________________________________|
                            |
                            v
                Save trace + PR draft
                            |
                            v
                  Local Trace Repository
                            |
                            v
        +-------------------------------------------+
        | Loop 4: Improvement / Meta-Agent          |
        |-------------------------------------------|
        | Read many traces                          |
        | Detect repeated patterns                  |
        | Propose prompt/verifier improvements      |
        | Human approval                            |
        +-------------------------------------------+
                            |
                            v
                   config/harness.json
```

## Folder structure

```text
loop-engineering-docs-agent/
├── .env.example
├── .gitignore
├── Makefile
├── README.md
├── pyproject.toml
├── config/
│   └── harness.json
├── sample_repo/
│   ├── README.md
│   └── docs/
│       ├── configuration.md
│       └── getting-started.md
├── scripts/
│   ├── call_webhook.sh
│   └── demo_request.json
├── src/loop_engineering/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py
│   ├── config.py
│   ├── schemas.py
│   ├── agent/
│   │   ├── factory.py
│   │   └── runner.py
│   ├── events/
│   │   ├── api.py
│   │   ├── service.py
│   │   └── store.py
│   ├── improvement/
│   │   ├── analyzer.py
│   │   └── apply.py
│   ├── observability/
│   │   └── tracing.py
│   ├── repository/
│   │   ├── git.py
│   │   ├── local.py
│   │   └── pull_request.py
│   ├── tools/
│   │   └── docs_tools.py
│   └── verification/
│       ├── deterministic.py
│       ├── llm_judge.py
│       └── loop.py
└── tests/
    ├── test_repository.py
    └── test_verification.py
```

## What each file is responsible for

### Configuration and contracts

- `config/harness.json` — editable system prompt, permissions, learned rules, and improvement history.
- `config.py` — environment settings plus load/save logic for the harness.
- `schemas.py` — Pydantic contracts shared across all four loops.

### Loop 1: agent

- `agent/factory.py` — initializes the chat model and builds LangChain's `create_agent` harness.
- `agent/runner.py` — invokes the agent and injects verifier feedback into retry attempts.
- `tools/docs_tools.py` — exposes only narrow tools: list, search, read, write, and inspect diff.
- `repository/local.py` — safe filesystem adapter with path traversal protection and extension restrictions.
- `repository/git.py` — Git baseline, diff, reset, status, and isolated local clone operations.

### Loop 2: verification

- `verification/deterministic.py` — checks that a diff exists, only docs changed, links resolve, placeholders are absent, and `git diff --check` passes.
- `verification/llm_judge.py` — optional structured-output grader for semantic correctness and scope.
- `verification/loop.py` — runs up to `MAX_VERIFICATION_ATTEMPTS`, feeds failures back to the agent, saves traces, and publishes a PR draft after success.
- `repository/pull_request.py` — writes a reviewable Markdown PR artifact instead of modifying a real remote.

### Loop 3: event-driven execution

- `events/api.py` — FastAPI endpoints for receiving requests and polling run status.
- `events/service.py` — creates an isolated Git clone and executes the verification loop.
- `events/store.py` — persists queued/running/succeeded/failed event records as JSON.

### Loop 4: hill climbing

- `observability/tracing.py` — local trace storage. When LangSmith tracing is enabled, LangChain also sends the full model/tool trace to LangSmith.
- `improvement/analyzer.py` — analyzes repeated failures with an LLM or an offline frequency-based fallback and writes a proposal.
- `improvement/apply.py` — requires explicit approval and applies only additive prompt rules.

### Entry points and tests

- `cli.py` — `run`, `serve`, `improve`, `approve`, and `traces` commands.
- `tests/` — tests repository boundaries and deterministic verification without making model calls.
- `scripts/demo_request.json` — event payload for the video.
- `scripts/call_webhook.sh` — sends the payload to the local API.

## Installation

### Option A: `venv` and pip

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
cp .env.example .env
```

Add your provider API key to `.env`:

```dotenv
GEMINI_API_KEY=your-key
```

The model is configurable. Change `MODEL`, `GRADER_MODEL`, and `IMPROVEMENT_MODEL` to any LangChain-supported provider/model identifier.

### Option B: uv

```bash
uv sync --extra dev
cp .env.example .env
```

## Run loops 1 and 2

```bash
docs-loop run \
  "Improve the getting-started guide. State the Python requirement, add the pip installation command, and keep the link to the configuration guide. Make only the necessary documentation changes." \
  --reset
```

What happens:

1. The sample repository is initialized as a Git repository.
2. The agent inspects and edits the documentation using tools.
3. Deterministic checks inspect the working-tree diff.
4. The optional LLM judge checks whether the change actually satisfies the request.
5. On failure, the report becomes feedback for the next attempt.
6. On success, a PR draft is written under `data/pull_request_drafts/`.
7. Every attempt is saved under `data/traces/`.

Use deterministic verification only:

```bash
docs-loop run "Clarify the installation section." --reset --no-llm-judge
```

## Run loop 3: event-driven mode

Start the API:

```bash
docs-loop serve --reload
```

Send the example event from another terminal:

```bash
./scripts/call_webhook.sh
```

The endpoint immediately returns a queued run record:

```json
{
  "run_id": "...",
  "status": "queued",
  "request": {
    "source": "slack",
    "instruction": "Improve the getting-started guide..."
  }
}
```

Poll the run:

```bash
curl http://127.0.0.1:8000/runs/RUN_ID
```

FastAPI `BackgroundTasks` is intentionally used for a small educational demo. In production, use a durable queue, idempotency keys, signed webhook verification, isolated credentials, and one worktree/container per run.

## Run loop 4: analyze and improve the harness

Use the LLM analyzer:

```bash
docs-loop improve
```

Or use the offline failure-frequency analyzer:

```bash
docs-loop improve --offline
```

Both commands write a proposal under `data/harness_proposals/`. Nothing changes automatically.

Review the JSON proposal, then explicitly approve it:

```bash
docs-loop approve data/harness_proposals/PROPOSAL_ID.json \
  --approved-by "Achyut"
```

The approved prompt rules are added to `config/harness.json`. The next `create_agent` call composes those reviewed rules into the system prompt.

## Enable LangSmith traces

Set:

```dotenv
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your-langsmith-key
LANGSMITH_PROJECT=loop-engineering-docs-agent
```

Because this project uses LangChain's agent runtime, model calls and tool calls are traced automatically when LangSmith tracing is enabled. The local JSON trace is separate: it stores a compact, application-owned record that the loop-4 demo can analyze without depending on a managed API.

## Test the non-LLM layers

```bash
pytest -q
ruff check src tests
```

The tests do not require an API key.
