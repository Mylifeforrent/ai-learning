# 🧠 Essential Skills for AI-Assisted Coding

> Beyond just writing `CLAUDE.md` or `.cursorrules`, there are **10 critical skills** that separate effective AI-powered developers from those who struggle with hallucinations, wasted tokens, and low-quality output.

---

## 📋 Table of Contents

1. [Skill 1: Rules & Instructions Files](#skill-1-rules--instructions-files)
2. [Skill 2: Memory Bank Pattern](#skill-2-memory-bank-pattern)
3. [Skill 3: Context Engineering](#skill-3-context-engineering)
4. [Skill 4: Prompt Engineering for Code](#skill-4-prompt-engineering-for-code)
5. [Skill 5: MCP (Model Context Protocol)](#skill-5-mcp-model-context-protocol)
6. [Skill 6: Git Worktrees for Parallel AI Agents](#skill-6-git-worktrees-for-parallel-ai-agents)
7. [Skill 7: TDD with AI (Red-Green-Refactor)](#skill-7-tdd-with-ai-red-green-refactor)
8. [Skill 8: Spec-Driven Development (SDD)](#skill-8-spec-driven-development-sdd)
9. [Skill 9: Anti-Pattern Recognition & Prevention](#skill-9-anti-pattern-recognition--prevention)
10. [Skill 10: Multi-Agent Orchestration](#skill-10-multi-agent-orchestration)
11. [Quick Reference Cheat Sheet](#quick-reference-cheat-sheet)

---

## Skill 1: Rules & Instructions Files

### What is it?

Rules files are **persistent instruction sets** stored in your project repo that automatically load into the AI's context. They act as an "onboarding document" that teaches the AI your project's coding standards, architecture, and conventions.

### Where each tool looks for rules:

| Tool | File / Location | Auto-loaded? |
|:---|:---|:---|
| **Claude Code** | `CLAUDE.md` (root + subdirectories) | ✅ Yes |
| **Cursor** | `.cursor/rules/*.mdc` | ✅ Yes (with globs) |
| **Cursor (legacy)** | `.cursorrules` | ✅ Yes |
| **GitHub Copilot** | `.github/copilot-instructions.md` | ✅ Yes |
| **Cline** | `.clinerules` | ✅ Yes |
| **Windsurf** | `.windsurfrules` | ✅ Yes |
| **Gemini (Antigravity)** | Knowledge Items / KIs | ✅ Yes |

### Best Practices

```
✅ DO:
  • Keep rules concise — under 500 lines per file
  • Use specific, actionable language ("Use functional components")
  • Include project-specific patterns, NOT general programming knowledge
  • Use multiple files for different concerns (modular rules)
  • Update rules when the AI repeatedly makes the same mistake

❌ DON'T:
  • Write generic rules like "be a senior developer"
  • Document standard language syntax
  • Create a massive monolithic rules file
  • Pre-emptively create hundreds of rules — add them as needed
```

### Template: `CLAUDE.md`

```markdown
# Project: [Your Project Name]

## Overview
[1-2 sentences describing what the project does]

## Tech Stack
- Frontend: React 19 + TypeScript + Vite
- Backend: Node.js + Express
- Database: PostgreSQL
- Testing: Vitest + Playwright
- Package Manager: pnpm

## Architecture
- State management: Zustand stores in `src/stores/`
- API layer: React Query hooks in `src/hooks/`
- Components: Atomic design in `src/components/{atoms,molecules,organisms}/`
- Routes: File-based routing via React Router in `src/pages/`

## Coding Standards
- Always use TypeScript strict mode
- Use functional components with hooks (no class components)
- Prefer named exports over default exports
- All API calls go through `src/lib/api-client.ts`
- Error boundaries wrap every page component
- Use `zod` for all runtime validation

## Commands
- `pnpm dev` — Start development server
- `pnpm test` — Run unit tests
- `pnpm test:e2e` — Run Playwright E2E tests
- `pnpm lint` — Lint with ESLint
- `pnpm build` — Production build

## Git Conventions
- Branch format: `feat/`, `fix/`, `chore/`
- Commit format: Conventional Commits (e.g., `feat: add login page`)
- Always create a PR; never push directly to `main`

## Things to Avoid
- NEVER use `any` type in TypeScript
- NEVER modify `package.json` without explicit approval
- NEVER use inline styles; always use CSS modules
- NEVER store secrets in code; use environment variables
```

### Template: `.cursor/rules/typescript.mdc`

```markdown
---
description: TypeScript coding standards for this project
globs: "**/*.ts,**/*.tsx"
alwaysApply: false
---

# TypeScript Rules

## Types
- Use `interface` for object shapes, `type` for unions/intersections
- Never use `any` — use `unknown` and narrow with type guards
- Always define return types for exported functions

## Patterns
- Use discriminated unions for state management
- Prefer `const assertions` (`as const`) for literal types
- Use branded types for IDs: `type UserId = string & { __brand: 'UserId' }`

## Imports
- Use path aliases (`@/components/...` not `../../../components/...`)
- Group imports: React → external libs → internal modules → types
```

### Template: `.cursor/rules/testing.mdc`

```markdown
---
description: Testing conventions and patterns
globs: "**/*.test.ts,**/*.test.tsx,**/*.spec.ts"
alwaysApply: false
---

# Testing Rules

## Structure
- Use `describe` → `it` pattern (not `test`)
- Name tests: "should [expected behavior] when [condition]"
- One assertion per test where possible

## Mocking
- Prefer dependency injection over module mocking
- Use `vi.fn()` for function mocks
- Always reset mocks in `beforeEach`

## Data
- Use factory functions for test data (e.g., `createMockUser()`)
- Never use production data in tests
```

---

## Skill 2: Memory Bank Pattern

### What is it?

The Memory Bank is a system for **persisting project knowledge across AI sessions**. Since AI agents are stateless (each new chat starts fresh), the Memory Bank gives them "long-term memory" by storing structured context in markdown files within your repo.

### Why it matters

Without a Memory Bank:
```
Session 1: "Here's our project structure..."  ← you explain everything
Session 2: "Here's our project structure..."  ← you explain AGAIN
Session 3: "Here's our project structure..."  ← and AGAIN
```

With a Memory Bank:
```
Session 1: AI reads memory-bank/ → instantly knows the project
Session 2: AI reads memory-bank/ → picks up where you left off
Session 3: AI reads memory-bank/ → continuous, cumulative progress
```

### Directory Structure

```
your-project/
├── memory-bank/
│   ├── projectbrief.md        # What are we building? Why?
│   ├── productContext.md      # UX goals, user problems, target audience
│   ├── systemPatterns.md      # Architecture, design patterns, key decisions
│   ├── techContext.md         # Tech stack, dependencies, environment setup
│   ├── activeContext.md       # Current work focus, pending decisions
│   └── progress.md           # Completed work, known issues, status log
├── CLAUDE.md                  # Points AI to read memory-bank/ first
└── ...
```

### Template: `memory-bank/projectbrief.md`

```markdown
# Project Brief

## Project Name
Task Tracker Pro

## Core Purpose
A lightweight, team-oriented task management tool for small dev teams
who need Kanban-style boards without the overhead of Jira.

## Target Users
- Small development teams (2-10 people)
- Freelance developers managing multiple clients
- Startups in pre-seed/seed stage

## Key Features (MVP)
1. Kanban board with drag-and-drop
2. Task creation with title, description, priority, assignee
3. Real-time updates (WebSocket)
4. Basic authentication (email/password)

## Success Criteria
- Team of 5 can manage a sprint from start to finish
- Page load time < 2 seconds
- 95% uptime on production
```

### Template: `memory-bank/activeContext.md`

```markdown
# Active Context

## Current Sprint: Sprint 3 (Apr 7–21, 2026)

## In Progress
- [ ] Implementing WebSocket real-time updates for task status changes
  - Using Socket.IO on the backend
  - React context for WebSocket connection on frontend
  - Blocked: deciding between room-per-board vs. room-per-project

## Recent Decisions
- **2026-04-10**: Chose Socket.IO over raw WebSocket for better
  reconnection handling and room support
- **2026-04-08**: Decided to use Redis adapter for Socket.IO to
  support horizontal scaling

## Open Questions
- Should we implement optimistic updates on the client side?
- How do we handle WebSocket auth token refresh?

## Known Issues
- Task drag-and-drop occasionally duplicates the task visually (UI-only bug)
- Search indexing is slow for projects with 500+ tasks
```

### Template: `memory-bank/systemPatterns.md`

```markdown
# System Patterns

## Architecture Style
Modular monolith with clear module boundaries, designed to be split into
microservices later if needed.

## Key Patterns

### API Design
- RESTful with resource-based URLs
- Consistent response format: `{ data, error, meta }`
- Pagination: cursor-based (not offset-based)

### State Management (Frontend)
- Zustand for client state (UI state, preferences)
- React Query (TanStack Query) for server state (API data)
- No Redux — too much boilerplate for our scale

### Error Handling
- Backend: Express error middleware catches all errors
- Frontend: Error boundaries at page level + toast notifications
- All errors logged to Sentry

### Database
- PostgreSQL with Prisma ORM
- Migrations managed via `prisma migrate`
- Soft deletes for all user-facing entities (`deletedAt` column)

## Component Relationships
┌──────────┐     ┌──────────┐     ┌──────────┐
│ React    │────→│ Express  │────→│ PostgreSQL│
│ Frontend │     │ API      │     │ Database  │
│          │←───→│          │←───→│           │
│ (Vite)   │ WS  │ (Socket) │     │ (Prisma)  │
└──────────┘     └──────────┘     └──────────┘
```

### How to integrate with `CLAUDE.md`

Add this to the top of your `CLAUDE.md`:

```markdown
## Memory Bank
At the start of every task, read all files in `memory-bank/` to understand
the current project state. After completing significant work, update
`memory-bank/activeContext.md` and `memory-bank/progress.md`.
```

---

## Skill 3: Context Engineering

### What is it?

Context Engineering is the discipline of **curating what information the AI sees** at any given moment. It's the difference between "prompt engineering" (how you phrase your question) and "context engineering" (what data surrounds your question).

> _"Prompt engineering is choosing the right words. Context engineering is choosing the right information."_
> — Anthropic, 2026

### The Context Window Problem

```
┌──────────────────────────────────────────────────┐
│            AI Context Window (200K tokens)        │
│                                                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ System   │  │ Your     │  │ Code     │        │
│  │ Prompt   │  │ Rules    │  │ Context  │        │
│  │ (fixed)  │  │ files    │  │ (files)  │        │
│  └──────────┘  └──────────┘  └──────────┘        │
│                                                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ Chat     │  │ Search   │  │ YOUR     │        │
│  │ History  │  │ Results  │  │ PROMPT   │        │
│  │ (grows!) │  │ (RAG)    │  │          │        │
│  └──────────┘  └──────────┘  └──────────┘        │
│                                                    │
│  ⚠️ When this fills up → "Context Rot" begins    │
│     AI forgets earlier instructions, hallucinates │
└──────────────────────────────────────────────────┘
```

### Key Techniques

#### 1. Selective Reference (Use `@` Mentions)

```
❌ Bad:  Copy-paste 500 lines of code into the chat
✅ Good: "Look at @src/api/tasks.ts and fix the validation bug on line 42"
```

#### 2. Workspace Hygiene

```
❌ Bad:  Keep 20 tabs open in your IDE → AI gets confused by irrelevant files
✅ Good: Only keep files relevant to the current task open
```

#### 3. Strategic Context Resets

```
When to reset context (start a new chat):
• The chat is over 30-40 messages long
• The AI starts "forgetting" earlier instructions
• The AI is stuck in a loop, repeating the same fix
• You're switching to a completely different task
```

#### 4. Atomic Task Decomposition

```
❌ Bad:  "Build me a full authentication system with OAuth, JWT,
         email verification, password reset, and admin roles"

✅ Good: Break into sequential prompts:
  1. "Create the User model with email and password hash fields"
  2. "Implement POST /auth/register with bcrypt password hashing"
  3. "Implement POST /auth/login with JWT token generation"
  4. "Add JWT verification middleware"
  5. "Implement password reset flow with email tokens"
```

#### 5. Plan Mode → Execute Mode

```
Most AI coding tools support this pattern:

┌──────────────┐     Human      ┌──────────────┐
│  PLAN MODE   │ ──approves──→  │ EXECUTE MODE │
│              │                 │              │
│ AI analyzes  │                 │ AI writes    │
│ the codebase │                 │ the actual   │
│ and proposes │                 │ code changes │
│ a plan       │                 │              │
└──────────────┘                 └──────────────┘

Cursor:   Shift+Tab to toggle Plan Mode
Claude:   "First, analyze the codebase and propose a plan. Do NOT write
           any code yet."
```

#### 6. Context Compaction

```markdown
When your chat gets long, summarize the progress so far:

"Here's what we've done so far:
1. ✅ Created User model with Prisma
2. ✅ Implemented /auth/register endpoint
3. ✅ Implemented /auth/login with JWT
4. 🔄 Current: Adding JWT middleware
5. ⬜ Next: Password reset flow

Continue from step 4. The JWT middleware should..."
```

---

## Skill 4: Prompt Engineering for Code

### What is it?

Structured techniques for writing prompts that produce higher-quality, more accurate code from AI assistants.

### The SCOPE Framework

```
S — Specify the exact task and scope
C — Constraints and limitations
O — Output format and structure
P — Provide examples or references
E — Edge cases to handle
```

### Template: Feature Implementation Prompt

```markdown
## Task
Implement a rate limiter middleware for the Express API.

## Context
- We use Express 4 with TypeScript
- Rate limits should be per-IP address
- We already have Redis configured (see `src/lib/redis.ts`)

## Constraints
- Use the sliding window algorithm (not fixed window)
- Store rate limit data in Redis (not in-memory)
- Do NOT add any new npm dependencies — use our existing `ioredis` client
- Must work behind a reverse proxy (use `X-Forwarded-For` header)

## Expected Output
1. A middleware function at `src/middleware/rate-limiter.ts`
2. Unit tests at `src/middleware/rate-limiter.test.ts`
3. Updated `src/app.ts` to apply the middleware

## Configuration
- Default: 100 requests per 15 minutes
- Auth endpoints: 20 requests per 15 minutes
- Health check: No rate limit

## Edge Cases
- What if Redis is down? → Fall back to allowing all requests (fail-open)
- What if X-Forwarded-For has multiple IPs? → Use the first one
- What if the request has no identifiable IP? → Use a default bucket
```

### Template: Bug Fix Prompt

```markdown
## Bug
Users report that task drag-and-drop sometimes duplicates the task card
visually (the data is correct in the DB, it's a UI-only bug).

## Steps to Reproduce
1. Open a board with 5+ tasks in the "To Do" column
2. Quickly drag a task from "To Do" to "In Progress"
3. While the animation is running, scroll the board
4. The task appears in both columns until refresh

## Expected Behavior
The task should immediately appear only in the target column.

## Relevant Files
- `src/components/KanbanBoard.tsx` (the board container)
- `src/components/TaskCard.tsx` (individual task card)
- `src/hooks/useTaskDrag.ts` (drag-and-drop logic using dnd-kit)

## My Hypothesis
I think the optimistic update in React Query is running before the
dnd-kit animation completes, causing a brief double-render.

## Constraints
- Do NOT refactor the entire drag system
- Keep the fix minimal and targeted
```

### Template: Code Review Prompt

```markdown
## Request
Review the following code for:
1. Security vulnerabilities
2. Performance issues
3. Error handling gaps
4. TypeScript type safety

Be specific about line numbers and provide concrete fixes.
Do NOT suggest cosmetic/stylistic changes.

## Code
[paste code or @reference file]
```

### Power Prompt Patterns

| Pattern | Example | Use Case |
|:---|:---|:---|
| **Chain of Thought** | "Think step by step before writing code" | Complex algorithms |
| **Role Assignment** | "You are a security engineer reviewing this code" | Specialized reviews |
| **Few-Shot** | "Here's an example of how we do X... Now do Y the same way" | Consistency with existing patterns |
| **Negative Constraints** | "Do NOT use any external libraries" | Preventing scope creep |
| **Output Scaffolding** | "Return your answer as: 1) Analysis 2) Plan 3) Code" | Structured output |
| **Self-Critique** | "After writing the code, list 3 potential issues with it" | Self-correction |

---

## Skill 5: MCP (Model Context Protocol)

### What is it?

MCP is a **universal protocol** (like USB-C for AI) that lets AI coding agents connect to external tools and data sources: databases, issue trackers, monitoring systems, documentation, and more.

### Why it matters

```
Without MCP:
  You: "The Jira ticket says..."  ← copy-paste from browser
  You: "The error in Sentry is..." ← copy-paste from Sentry
  You: "The schema looks like..."   ← copy-paste from DB client

With MCP:
  AI: *reads Jira ticket directly*
  AI: *reads Sentry error directly*
  AI: *queries database schema directly*
  AI: "Based on ticket PROJ-123, the Sentry error, and the current
       schema, here's my fix..."
```

### Architecture

```
┌───────────────┐
│  AI Agent     │ (Claude Code, Cursor, etc.)
│  (MCP Client) │
└──────┬────────┘
       │ MCP Protocol (JSON-RPC over stdio/SSE)
       │
  ┌────┴─────┬───────────┬────────────┬──────────┐
  │          │           │            │          │
  ▼          ▼           ▼            ▼          ▼
┌──────┐ ┌──────┐  ┌──────────┐ ┌──────┐ ┌────────┐
│GitHub│ │ Jira │  │PostgreSQL│ │Sentry│ │Filesys.│
│Server│ │Server│  │  Server  │ │Server│ │ Server │
└──────┘ └──────┘  └──────────┘ └──────┘ └────────┘
```

### Setup Example: Claude Code with MCP

```json
// ~/.claude/claude_desktop_config.json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"
      }
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/project"],
    },
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": {
        "POSTGRES_CONNECTION_STRING": "${DATABASE_URL}"
      }
    },
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"]
    }
  }
}
```

### Popular MCP Servers

| Server | Purpose | Source |
|:---|:---|:---|
| `server-github` | Read issues, PRs, repos | Official |
| `server-filesystem` | Read/write project files | Official |
| `server-postgres` | Query databases | Official |
| `server-memory` | Persistent key-value memory | Official |
| `server-brave-search` | Web search | Official |
| `server-sentry` | Error monitoring | Community |
| `server-linear` | Issue tracking | Community |
| `server-notion` | Wiki/documentation | Community |

### Security Best Practices

```
✅ DO:
  • Use environment variables for all API keys/tokens
  • Explicitly define allowed directories for filesystem access
  • Use read-only database connections for MCP
  • Audit which MCP servers are configured regularly

❌ DON'T:
  • Hardcode secrets in config files
  • Give filesystem MCP access to your entire home directory
  • Use production database credentials with write access
  • Install untrusted community MCP servers without reviewing code
```

---

## Skill 6: Git Worktrees for Parallel AI Agents

### What is it?

Git worktrees let you **check out multiple branches simultaneously** in different directories, sharing the same `.git` history. This enables you to run multiple AI agent sessions in parallel without conflicts.

### Why it matters

```
Without worktrees:
  Agent A works on feature-auth → must finish before
  Agent B works on feature-search → can start

With worktrees:
  /project/                    ← main (your "HQ")
  /project-feat-auth/          ← Agent A working here
  /project-feat-search/        ← Agent B working here
  /project-bugfix-login/       ← Agent C working here
  All running SIMULTANEOUSLY 🚀
```

### Step-by-Step Setup

```bash
# 1. Create your main project (the "HQ")
cd ~/projects/task-tracker

# 2. Create worktrees for parallel tasks
git worktree add ../task-tracker-feat-auth   feat/auth
git worktree add ../task-tracker-feat-search feat/search
git worktree add ../task-tracker-bugfix-login fix/login-bug

# 3. List all worktrees
git worktree list
# /Users/you/projects/task-tracker               abc1234 [main]
# /Users/you/projects/task-tracker-feat-auth      def5678 [feat/auth]
# /Users/you/projects/task-tracker-feat-search    ghi9012 [feat/search]
# /Users/you/projects/task-tracker-bugfix-login   jkl3456 [fix/login-bug]

# 4. Open each worktree in a separate IDE window
#    → Launch a separate AI agent session in each

# 5. When done, merge and clean up
cd ~/projects/task-tracker
git merge feat/auth
git worktree remove ../task-tracker-feat-auth

git merge feat/search
git worktree remove ../task-tracker-feat-search
```

### The "Agent HQ" Pattern

```
┌────────────────────────────────────────────────────┐
│                 AGENT HQ (main branch)             │
│  Purpose: Orchestration, planning, code review     │
│  You sit here and coordinate                       │
└───────┬────────────────┬───────────────┬───────────┘
        │                │               │
        ▼                ▼               ▼
  ┌──────────┐    ┌──────────┐    ┌──────────┐
  │ Worktree │    │ Worktree │    │ Worktree │
  │ Agent A  │    │ Agent B  │    │ Agent C  │
  │ feat/auth│    │ feat/ui  │    │ fix/perf │
  └──────────┘    └──────────┘    └──────────┘
       │                │               │
       └────────────────┴───────────────┘
                        │
                   Git Merge
                   (handled by HQ)
```

### Best Practices

```
1. Always run tests in the worktree BEFORE starting the AI agent
   → Establishes a known-good baseline

2. Use descriptive naming: {project}-{type}-{description}
   → task-tracker-feat-websocket
   → task-tracker-fix-drag-bug

3. Keep CLAUDE.md / .cursorrules in the repo so each worktree
   automatically gets the same rules

4. Start with 1-2 parallel agents, then scale up as you build
   "orchestration muscle"

5. Clean up worktrees immediately after merging to avoid clutter
```

---

## Skill 7: TDD with AI (Red-Green-Refactor)

### What is it?

Using AI agents to follow the **Test-Driven Development** cycle: write failing tests first (Red), implement code to pass them (Green), then improve the code (Refactor).

### Why TDD is especially important with AI

```
Without TDD:
  AI writes code → "looks right" → you accept → bug found in production 💥

With TDD:
  AI writes test → test fails (Red) → AI writes code → test passes (Green)
  → You have proof the code works ✅
```

### The Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                    TDD with AI                              │
│                                                             │
│  Step 1: RED 🔴                                             │
│  ├─ Describe the feature to the AI                          │
│  ├─ AI writes tests based on acceptance criteria            │
│  └─ Run tests → ALL SHOULD FAIL (this confirms tests work) │
│                                                             │
│  Step 2: GREEN 🟢                                           │
│  ├─ AI implements the minimum code to make tests pass       │
│  ├─ Run tests → ALL SHOULD PASS                             │
│  └─ If tests fail → AI iterates until they pass             │
│                                                             │
│  Step 3: REFACTOR 🔵                                        │
│  ├─ AI reviews its own code for quality                     │
│  ├─ Improve naming, remove duplication, optimize            │
│  └─ Run tests again → STILL SHOULD PASS                    │
│                                                             │
│  Step 4: COMMIT ✅                                           │
│  └─ git commit -m "feat: implement [feature]"               │
└─────────────────────────────────────────────────────────────┘
```

### Prompt Template for TDD

```markdown
## Task
Implement a password strength validator function.

## Instructions
Follow TDD strictly:

### Phase 1 (Red)
Write comprehensive tests first. The function should:
- Return "weak" for passwords < 8 chars
- Return "weak" if missing uppercase, lowercase, or numbers
- Return "medium" for 8-12 chars with mixed case and numbers
- Return "strong" for 12+ chars with mixed case, numbers, and symbols
- Return "weak" for common passwords (e.g., "Password123")

### Phase 2 (Green)
Implement the function to make ALL tests pass.

### Phase 3 (Refactor)
Review your code and optimize without breaking any tests.

## File Locations
- Tests: `src/utils/password-strength.test.ts`
- Implementation: `src/utils/password-strength.ts`
```

---

## Skill 8: Spec-Driven Development (SDD)

### What is it?

Writing a **detailed specification** before asking the AI to write any code. The spec becomes the "contract" between you and the AI — it defines exactly what to build, how to build it, and what success looks like.

### Why it matters

```
Without specs:
  "Build me a login page" → AI builds something → "No, not like that"
  → AI rebuilds → "Still not right" → 3 hours wasted

With specs:
  You write a 20-line spec → AI builds exactly what you described
  → First attempt is 90% correct → 20 minutes total
```

### Spec Template

```markdown
# Feature Spec: User Authentication

## 1. Overview
Implement email/password authentication with JWT tokens.

## 2. User Stories
- As a user, I can register with email and password
- As a user, I can login and receive a JWT token
- As a user, I can access protected routes with my token
- As a user, I see clear error messages for invalid credentials

## 3. API Endpoints

### POST /auth/register
- **Request**: `{ email: string, password: string, name: string }`
- **Response 201**: `{ user: { id, email, name }, token: string }`
- **Response 400**: `{ error: "Email already exists" }`
- **Validation**: Email format, password min 8 chars

### POST /auth/login
- **Request**: `{ email: string, password: string }`
- **Response 200**: `{ user: { id, email, name }, token: string }`
- **Response 401**: `{ error: "Invalid credentials" }`

### GET /auth/me (protected)
- **Headers**: `Authorization: Bearer <token>`
- **Response 200**: `{ user: { id, email, name } }`
- **Response 401**: `{ error: "Unauthorized" }`

## 4. Data Model
```prisma
model User {
  id        String   @id @default(cuid())
  email     String   @unique
  name      String
  password  String   // bcrypt hash
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
}
```

## 5. Security Requirements
- Passwords hashed with bcrypt (12 rounds)
- JWT expires in 7 days
- Rate limit: 5 login attempts per 15 minutes per IP
- JWT secret from environment variable

## 6. File Structure
- `src/routes/auth.ts` — Route handlers
- `src/middleware/auth.ts` — JWT verification middleware
- `src/lib/jwt.ts` — Token generation/verification helpers
- `tests/auth.test.ts` — Integration tests

## 7. Acceptance Criteria
- [ ] All 3 endpoints work as specified
- [ ] Passwords are never stored in plaintext
- [ ] JWT tokens expire correctly
- [ ] Rate limiting works
- [ ] All tests pass with >90% coverage
```

### Where to store specs

```
your-project/
├── docs/
│   └── specs/
│       ├── 001-auth.md
│       ├── 002-kanban-board.md
│       └── 003-real-time-updates.md
├── .openspec/                  # If using OpenSpec
│   └── proposals/
│       ├── 001-auth.md
│       └── ...
└── ...
```

---

## Skill 9: Anti-Pattern Recognition & Prevention

### What is it?

Knowing the common failure modes when coding with AI and how to avoid them.

### The 8 Deadly Anti-Patterns

#### 1. 🎰 The "Vending Machine" Mindset
```
❌ "Build me a REST API" → accept whatever comes out
✅ "Build me a REST API" → review every line → understand every decision
```

#### 2. 📚 The "Context Dump"
```
❌ Paste 1000 lines of code: "Fix the bug"
✅ Paste the specific 20-line function + the error message + expected behavior
```

#### 3. 🏗️ The "One Giant Prompt"
```
❌ "Build a full e-commerce site with cart, checkout, payments,
    inventory, user accounts, admin dashboard, and analytics"
✅ Break into 7 separate, sequential tasks
```

#### 4. 🔄 The "Infinite Loop"
```
❌ AI fails → ask again → AI fails again → ask again → ...
   (after 3 failed attempts with the same approach)
✅ Stop. Revert. Rethink. Try a completely different approach.
   Or write the logic manually.
```

#### 5. 🐟 The "Fish Scale" Pattern
```
❌ AI generates overlapping, partially redundant code paths
   (construct → discard → reconstruct → partially use)
✅ Ask AI to refactor into a single, clean implementation
   "Simplify this function. There seem to be redundant code paths."
```

#### 6. 🙈 The "Blind Trust"
```
❌ "The code looks right" → ship without testing
✅ "The code looks right" → run tests → check edge cases
   → review for security → THEN ship
```

#### 7. 📦 The "Dependency Monster"
```
❌ AI adds 5 new npm packages to solve a simple problem
✅ "Solve this WITHOUT adding new dependencies.
    Use only what's already in package.json."
```

#### 8. 🔧 The "Config Destroyer"
```
❌ AI modifies package.json, tsconfig.json, docker-compose.yml
    without being asked → breaks the entire project
✅ Add to rules: "NEVER modify config files without explicit approval"
```

### Prevention Checklist

```markdown
Before accepting AI-generated code, verify:
□ Does it compile/lint without errors?
□ Do all existing tests still pass?
□ Are there tests for the new code?
□ Did it add any unexpected dependencies?
□ Did it modify any config files?
□ Are there any security issues? (SQL injection, XSS, exposed secrets)
□ Does the code follow our established patterns? (check systemPatterns.md)
□ Would I accept this in a code review from a junior developer?
```

---

## Skill 10: Multi-Agent Orchestration

### What is it?

Using **multiple AI agents** for different roles in a single development workflow — just like managing a team of specialists.

### The Agent Team Pattern

```
┌─────────────────────────────────────────────────────────────┐
│                    Agent Orchestration                       │
│                                                             │
│  ┌────────────┐  You define the task and coordinate         │
│  │   Human    │  between agents like a tech lead            │
│  │ (The Lead) │                                             │
│  └─────┬──────┘                                             │
│        │                                                    │
│   ┌────┴────┬──────────┬───────────┬──────────┐            │
│   ▼         ▼          ▼           ▼          ▼            │
│ ┌──────┐ ┌──────┐ ┌────────┐ ┌────────┐ ┌────────┐       │
│ │ Spec │ │ Code │ │ Review │ │  Test  │ │ DocGen │       │
│ │Agent │ │Agent │ │ Agent  │ │ Agent  │ │ Agent  │       │
│ │      │ │      │ │        │ │        │ │        │       │
│ │Write │ │Write │ │Reviews │ │Writes &│ │Writes  │       │
│ │specs │ │code  │ │code for│ │runs    │ │API docs│       │
│ │& PRD │ │      │ │quality │ │tests   │ │README  │       │
│ └──────┘ └──────┘ └────────┘ └────────┘ └────────┘       │
└─────────────────────────────────────────────────────────────┘
```

### Practical Setup

```bash
# Terminal 1: Code Agent (Claude Code in worktree)
cd ~/projects/task-tracker-feat-auth
claude "Implement the auth module based on docs/specs/001-auth.md"

# Terminal 2: Test Agent (another Claude Code session)
cd ~/projects/task-tracker-test-auth
claude "Write comprehensive tests for the auth module.
        Read docs/specs/001-auth.md for requirements."

# Terminal 3: Review Agent (yet another session)
# After Code Agent finishes:
claude "Review the changes in feat/auth branch against
        docs/specs/001-auth.md. Focus on security and
        error handling. List all issues found."
```

### When to Use Multi-Agent

| Scenario | Agents | Benefit |
|:---|:---|:---|
| Feature implementation | Code + Test agents in parallel | 2x faster |
| Large refactoring | Multiple code agents on different modules | Parallel progress |
| Code review | Dedicated review agent | Catches issues the coder missed |
| Documentation | Doc agent runs after coding is done | Automated docs |
| Bug investigation | Investigator agent + Fix agent | Separation of concern |

---

## Quick Reference Cheat Sheet

### 📁 Files to Add to Every Project

```
your-project/
├── CLAUDE.md                    # Claude Code instructions
├── .cursor/rules/
│   ├── general.mdc              # Project-wide rules
│   ├── typescript.mdc           # Language-specific rules
│   └── testing.mdc              # Testing conventions
├── .github/
│   └── copilot-instructions.md  # GitHub Copilot rules
├── memory-bank/
│   ├── projectbrief.md          # What we're building
│   ├── productContext.md        # UX & users
│   ├── systemPatterns.md        # Architecture patterns
│   ├── techContext.md           # Tech stack details
│   ├── activeContext.md         # Current work focus
│   └── progress.md             # Status log
├── docs/
│   └── specs/                   # Feature specifications
│       └── 001-feature.md
└── .gitignore
```

### 🎯 Daily Workflow

```
1. 📖 READ    → Check memory-bank/activeContext.md
2. 🗺️ PLAN    → Use Plan Mode, write/review spec first
3. 🧪 TEST    → Write failing tests (Red)
4. 💻 CODE    → Implement to pass tests (Green)
5. 🔍 REVIEW  → Read diffs, check for anti-patterns
6. ✨ REFACTOR → Clean up without breaking tests
7. 📝 COMMIT  → Small, focused commits
8. 🧠 UPDATE  → Update memory-bank/activeContext.md
```

### ⚡ Power Tips

| Tip | Why |
|:---|:---|
| Commit before every AI refactor | Instant rollback if things break |
| Use `@` mentions, not copy-paste | Keeps context clean and accurate |
| One task per chat session | Prevents context pollution |
| Add rules reactively, not proactively | Only add when AI repeats a mistake |
| Review diffs, not finished code | Easier to catch mistakes in the diff |
| Use AI to review AI | Second agent catches first agent's errors |

---

## 📚 Further Reading

| Resource | Link |
|:---|:---|
| Anthropic: Context Engineering | [anthropic.com/research](https://anthropic.com) |
| Martin Fowler: Context Engineering | [martinfowler.com](https://martinfowler.com) |
| Cursor Rules Directory | [cursor.directory](https://cursor.directory) |
| MCP Official Docs | [modelcontextprotocol.io](https://modelcontextprotocol.io) |
| Superpowers (TDD Skills) | [github.com/obra/superpowers](https://github.com/obra/superpowers) |
| OpenSpec (SDD) | [github.com/Fission-AI/OpenSpec](https://github.com/Fission-AI/OpenSpec) |

---

*Last updated: 2026-04-14*
