# 🚀 AI-Powered Software Development Lifecycle (SDLC) — Complete Guide

> **Goal**: A comprehensive, actionable guide for building software with AI across all phases—from ideation to production—covering Product, Project Management, Architecture, Development, Testing, and Deployment.

---

## 📋 Table of Contents

1. [Overview & Philosophy](#1-overview--philosophy)
2. [Phase 1: Product — Vision & Requirements](#2-phase-1-product--vision--requirements)
3. [Phase 2: Project Management — Planning & Tracking](#3-phase-2-project-management--planning--tracking)
4. [Phase 3: Architecture — System Design](#4-phase-3-architecture--system-design)
5. [Phase 4: Development — Implementation](#5-phase-4-development--implementation)
6. [Phase 5: Testing — Quality Assurance](#6-phase-5-testing--quality-assurance)
7. [Phase 6: Deployment — CI/CD & Release](#7-phase-6-deployment--cicd--release)
8. [Tool Comparison Matrix](#8-tool-comparison-matrix)
9. [End-to-End Demo: Building a "Task Tracker" App](#9-end-to-end-demo-building-a-task-tracker-app)

---

## 1. Overview & Philosophy

### The AI-First SDLC Mindset (2025–2026)

The software development lifecycle has evolved from **AI-assisted** (autocomplete, copilot) to **AI-agentic** (autonomous reasoning, multi-step execution). The key shifts are:

| Traditional SDLC | AI-Powered SDLC |
|:---|:---|
| Developers write all code | AI generates code; humans review & architect |
| Manual documentation | Spec-driven, AI-generated docs |
| Manual test writing | AI agents generate & maintain tests |
| Periodic deployments | Continuous, AI-monitored deployments |
| Reactive debugging | Proactive, AI-driven observability |

### Core Principles

1. **Spec-Driven Development (SDD)**: Always write a clear spec *before* AI writes code. "Vague in → vague out."
2. **Human-in-the-Loop**: AI drafts, humans review. Never blindly trust AI output.
3. **Two-Phase Workflow**: Split every task into **Planning** → **Implementation**. Have AI generate a plan first, then execute.
4. **Governance & Reversibility**: Treat AI output as "unreviewed junior code." Keep all changes reversible.

### Lifecycle Diagram

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    AI-Powered SDLC Pipeline                             │
│                                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ PRODUCT  │→│ PROJECT  │→│  ARCH    │→│   DEV    │→│  TEST    │  │
│  │ Vision & │  │ Planning │  │ Design  │  │ Coding  │  │  QA &    │  │
│  │ Specs    │  │ & Track  │  │ & Model │  │ & Build │  │ Validate │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
│                                                              │          │
│                                                              ▼          │
│                                                        ┌──────────┐    │
│                                                        │ DEPLOY   │    │
│                                                        │ CI/CD &  │    │
│                                                        │ Monitor  │    │
│                                                        └──────────┘    │
│                                                              │          │
│                              ◄─── Feedback Loop ────────────┘          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Phase 1: Product — Vision & Requirements

### 2.1 Purpose

Define **what** to build, **for whom**, and **why**. This phase produces the Product Requirements Document (PRD), user stories, and acceptance criteria.

### 2.2 Recommended Tools

| Tool | Type | Best For | Link |
|:---|:---|:---|:---|
| **OpenSpec** | OSS Framework | Spec-driven development with AI agents | [GitHub: Fission-AI/OpenSpec](https://github.com/Fission-AI/OpenSpec) |
| **ChatPRD** | AI SaaS | Rapid PRD drafting from ideas | [chatprd.ai](https://chatprd.ai) |
| **Notion AI** | Platform | PRD + wiki + team collaboration | [notion.so](https://notion.so) |
| **Claude / ChatGPT** | LLM | Brainstorming, user story generation | - |

### 2.3 Should You Use Superpowers or OpenSpec?

| Criteria | OpenSpec ✅ | Superpowers ❌ |
|:---|:---|:---|
| **Product/Requirements phase** | ✅ Designed for specs & proposals | ❌ Focused on code execution |
| **Output** | PRDs, proposals, design docs | Working, tested code |
| **Best Phase** | Product → Architecture | Development → Testing |

> **Recommendation**: Use **OpenSpec** for the Product phase. It forces you to write structured specs (Propose → Apply → Archive) before any code is written, which is the single most important best practice for AI-assisted development.

### 2.4 Key Steps

```
Step 1: Define the Problem
  └─→ "What pain point are we solving?"

Step 2: Identify Target Users
  └─→ Create user personas with AI assistance

Step 3: Draft PRD using OpenSpec
  └─→ openspec propose → creates .openspec/proposals/

Step 4: Write User Stories (Given/When/Then)
  └─→ AI generates from PRD → human reviews

Step 5: Define Acceptance Criteria
  └─→ Measurable, testable criteria per story

Step 6: Prioritize (MoSCoW / RICE)
  └─→ Must-have / Should-have / Could-have / Won't-have
```

### 2.5 Demo: Creating a PRD with OpenSpec

```bash
# 1. Install OpenSpec in your project
cd your-project
npx openspec init

# 2. Create a proposal
npx openspec propose

# This creates a structured markdown file at:
# .openspec/proposals/001-feature-name.md
```

**Example PRD Output** (`.openspec/proposals/001-task-tracker.md`):

```markdown
# Proposal: Task Tracker MVP

## Problem Statement
Teams need a lightweight task management tool that integrates with their
existing workflow without the complexity of enterprise solutions.

## Target Users
- Small development teams (2-10 people)
- Freelancers managing multiple projects

## User Stories

### US-001: Create a Task
**As a** team member
**I want to** create a new task with title, description, and priority
**So that** I can track my work items

**Acceptance Criteria:**
- Given I am on the dashboard
- When I click "New Task" and fill in the form
- Then a new task appears in my task list with status "To Do"

### US-002: Drag-and-Drop Status Change
**As a** team member
**I want to** drag tasks between columns (To Do / In Progress / Done)
**So that** I can quickly update task status

### US-003: Filter and Search
**As a** team member
**I want to** filter tasks by priority and search by keyword
**So that** I can quickly find relevant tasks

## Non-Functional Requirements
- Page load time < 2 seconds
- Mobile-responsive design
- Data persists across sessions (localStorage or backend)

## Out of Scope (v1)
- User authentication
- Real-time collaboration
- File attachments
```

```bash
# 3. After team review, apply the proposal
npx openspec apply 001-task-tracker

# 4. Archive for documentation
npx openspec archive 001-task-tracker
```

---

## 3. Phase 2: Project Management — Planning & Tracking

### 3.1 Purpose

Break down the PRD into actionable work items, estimate effort, assign ownership, and track progress.

### 3.2 Recommended Tools

| Tool | Type | Best For | Link |
|:---|:---|:---|:---|
| **Linear** | Platform | AI-powered triage, capacity planning | [linear.app](https://linear.app) |
| **Jira + Rovo AI** | Platform | Enterprise teams, AI backlog management | [atlassian.com](https://atlassian.com) |
| **GitHub Projects** | Platform | Dev teams already on GitHub | [github.com](https://github.com) |
| **Claude / ChatGPT** | LLM | Story decomposition, estimation | - |

### 3.3 How to Plan Project Management Based on User Stories

```
PRD (User Stories)
    │
    ▼
┌─────────────────────────────────┐
│  Step 1: Story Decomposition    │
│  Break each user story into     │
│  technical tasks (frontend,     │
│  backend, database, testing)    │
└───────────────┬─────────────────┘
                │
                ▼
┌─────────────────────────────────┐
│  Step 2: Estimation             │
│  T-shirt sizing (S/M/L/XL)     │
│  or Story Points (1/2/3/5/8)   │
│  Use AI to suggest estimates    │
└───────────────┬─────────────────┘
                │
                ▼
┌─────────────────────────────────┐
│  Step 3: Sprint Planning        │
│  Group tasks into 1-2 week      │
│  sprints based on priority      │
│  and team capacity              │
└───────────────┬─────────────────┘
                │
                ▼
┌─────────────────────────────────┐
│  Step 4: Track & Iterate        │
│  Daily standups, burndown       │
│  charts, retrospectives         │
└─────────────────────────────────┘
```

### 3.4 Demo: Decomposing User Stories into Sprint Tasks

**Input**: User Story US-001 (Create a Task)

**AI-Generated Task Breakdown**:

```markdown
## Sprint 1: Task Tracker Foundation

### Epic: US-001 — Create a Task

| ID | Task | Type | Size | Priority | Assignee |
|:---|:---|:---|:---|:---|:---|
| T-001 | Design task data model (schema) | Backend | S | P0 | Dev A |
| T-002 | Create task form UI component | Frontend | M | P0 | Dev B |
| T-003 | Implement task creation API endpoint | Backend | M | P0 | Dev A |
| T-004 | Connect form to API with validation | Frontend | M | P0 | Dev B |
| T-005 | Write unit tests for task creation | Testing | S | P1 | Dev A |
| T-006 | Write E2E test for create task flow | Testing | M | P1 | Dev B |
| T-007 | Add error handling & loading states | Frontend | S | P1 | Dev B |

### Epic: US-002 — Drag-and-Drop Status Change

| ID | Task | Type | Size | Priority | Assignee |
|:---|:---|:---|:---|:---|:---|
| T-008 | Implement Kanban board layout | Frontend | L | P0 | Dev B |
| T-009 | Add drag-and-drop with dnd-kit | Frontend | L | P0 | Dev B |
| T-010 | Implement status update API | Backend | S | P0 | Dev A |
| T-011 | Write E2E test for drag-and-drop | Testing | M | P1 | Dev A |

### Sprint Velocity Target: ~25 story points
### Sprint Duration: 2 weeks
```

**Using AI to Generate This**:

```
Prompt to AI:
"Given the following user stories for a Task Tracker app, decompose each story
into technical tasks. For each task, specify: type (frontend/backend/testing),
T-shirt size (S/M/L/XL), priority (P0-P3), and suggest an assignment strategy
for a 2-person dev team. Format as a markdown table."

[Paste user stories here]
```

---

## 4. Phase 3: Architecture — System Design

### 4.1 Purpose

Define the high-level technical structure: components, data flow, technology stack, and system boundaries.

### 4.2 Recommended Tools

| Tool | Type | Best For | Link |
|:---|:---|:---|:---|
| **Structurizr** | OSS | C4 model, "models as code" | [GitHub: structurizr](https://github.com/structurizr) |
| **Mermaid.js** | OSS | Diagrams in markdown/GitHub | [mermaid.js.org](https://mermaid.js.org) |
| **C4-PlantUML** | OSS | C4 diagrams with PlantUML | [GitHub: C4-PlantUML](https://github.com/plantuml-stdlib/C4-PlantUML) |
| **draw.io** | OSS | Visual architecture diagrams | [diagrams.net](https://www.diagrams.net) |
| **Eraser.io** | Platform | AI-generated diagrams | [eraser.io](https://eraser.io) |
| **OpenSpec** | OSS | Architecture design documents | [GitHub: Fission-AI/OpenSpec](https://github.com/Fission-AI/OpenSpec) |

### 4.3 Should You Use OpenSpec/Superpowers or Open-Source Repos?

| Approach | When to Use |
|:---|:---|
| **OpenSpec** | When you need structured design docs before coding. Best for documenting component decisions. |
| **Structurizr + Mermaid** | When you need formal C4 architecture diagrams that live in your repo as code. |
| **AI + Eraser.io** | When you want to quickly draft architecture from a prompt and iterate visually. |

> **Recommendation**: Use a combination:
> 1. **OpenSpec** for architecture decision records (ADRs) and design proposals
> 2. **Mermaid.js** for diagrams embedded in your markdown docs (renders natively on GitHub)
> 3. **Structurizr** for formal C4 model if you need multi-level zoom (Context → Container → Component)

### 4.4 Key Steps

```
Step 1: Choose Architecture Style
  └─→ Monolith vs. Microservices vs. Serverless vs. Modular Monolith

Step 2: Define System Context (C4 Level 1)
  └─→ Who uses the system? What external systems does it interact with?

Step 3: Define Container Diagram (C4 Level 2)
  └─→ Frontend, Backend API, Database, Message Queue, etc.

Step 4: Define Component Diagram (C4 Level 3)
  └─→ Internal modules, services, and their responsibilities

Step 5: Define Data Model
  └─→ Entity-Relationship Diagram, database schema

Step 6: Document Architecture Decision Records (ADRs)
  └─→ Why did we choose X over Y?

Step 7: Review & Validate
  └─→ Ensure NFRs (performance, security, scalability) are addressed
```

### 4.5 Demo: Architecture Design for Task Tracker

#### C4 Context Diagram (Mermaid)

```mermaid
C4Context
    title System Context — Task Tracker

    Person(user, "Team Member", "Creates and manages tasks")
    System(taskTracker, "Task Tracker", "Lightweight task management application")
    System_Ext(email, "Email Service", "Sends notifications")
    System_Ext(github, "GitHub", "Links tasks to commits/PRs")

    Rel(user, taskTracker, "Uses", "HTTPS")
    Rel(taskTracker, email, "Sends notifications", "SMTP")
    Rel(taskTracker, github, "Fetches PR status", "REST API")
```

#### Container Diagram (Mermaid)

```mermaid
C4Container
    title Container Diagram — Task Tracker

    Person(user, "Team Member")

    Container_Boundary(app, "Task Tracker") {
        Container(spa, "Web App", "React + Vite", "Single-page application")
        Container(api, "API Server", "Node.js + Express", "REST API for task CRUD")
        ContainerDb(db, "Database", "PostgreSQL", "Stores tasks, users, projects")
        Container(cache, "Cache", "Redis", "Session & query caching")
    }

    Rel(user, spa, "Uses", "HTTPS")
    Rel(spa, api, "Calls", "JSON/HTTPS")
    Rel(api, db, "Reads/Writes", "SQL")
    Rel(api, cache, "Reads/Writes", "TCP")
```

#### Technology Stack Decision

```markdown
## Architecture Decision Record: ADR-001 — Technology Stack

### Context
We need to select a technology stack for the Task Tracker MVP.

### Decision
| Layer | Choice | Rationale |
|:---|:---|:---|
| Frontend | React + Vite | Fast build, modern DX, large ecosystem |
| Backend | Node.js + Express | JavaScript full-stack, easy API development |
| Database | PostgreSQL | Relational, robust, free |
| Cache | Redis | Fast session/query caching |
| Hosting | Vercel (FE) + Railway (BE) | Free tiers, easy deployment |

### Alternatives Considered
- **Next.js (Full-stack)**: Overkill for MVP, adds SSR complexity
- **SQLite**: Simpler but less scalable
- **Firebase**: Vendor lock-in concerns

### Status: Accepted
```

---

## 5. Phase 4: Development — Implementation

### 5.1 Purpose

Write code following the architecture and specs. Use AI agents to accelerate implementation while maintaining quality.

### 5.2 Recommended Tools

| Tool | Type | Best For | Link |
|:---|:---|:---|:---|
| **Superpowers** | OSS Framework | Disciplined AI coding (TDD, planning) | [GitHub: obra/superpowers](https://github.com/obra/superpowers) |
| **Claude Code** | AI Agent | Autonomous coding agent | [anthropic.com](https://anthropic.com) |
| **Cursor** | AI IDE | AI-first code editor | [cursor.com](https://cursor.com) |
| **GitHub Copilot** | AI Extension | Inline code suggestions | [github.com/copilot](https://github.com/copilot) |
| **OpenSpec** | OSS Framework | Spec → code implementation | [GitHub: Fission-AI/OpenSpec](https://github.com/Fission-AI/OpenSpec) |
| **Cline** | OSS Extension | Autonomous coding in VS Code | [GitHub: cline/cline](https://github.com/cline/cline) |

### 5.3 Should You Use Superpowers or OpenSpec?

| Criteria | Superpowers ✅ | OpenSpec |
|:---|:---|:---|
| **Development phase** | ✅ Enforces TDD, planning, sub-agents | Specs already written in Product phase |
| **Workflow** | Brainstorm → Plan → Execute → Review | Propose → Apply → Archive |
| **Best For** | Ensuring AI writes *quality* code | Ensuring AI writes *the right* code |

> **Recommendation**: Use **both together**:
> 1. **OpenSpec** creates the spec (what to build)
> 2. **Superpowers** governs how AI builds it (TDD, review, sub-agents)

### 5.4 The Superpowers Workflow

```
┌──────────────────────────────────────────────────────────────┐
│                 Superpowers Mandatory Pipeline                │
│                                                              │
│  1. BRAINSTORM                                               │
│     └─→ AI explores the problem space, asks clarifying Qs   │
│                                                              │
│  2. PLAN (with TDD)                                          │
│     └─→ AI creates a design doc + writes tests FIRST         │
│     └─→ Tests must FAIL (Red phase of Red-Green-Refactor)    │
│                                                              │
│  3. EXECUTE (Sub-agents)                                     │
│     └─→ AI writes code to make tests pass (Green phase)      │
│     └─→ Work is split into focused sub-agents                │
│                                                              │
│  4. REVIEW                                                   │
│     └─→ AI reviews its own work against the plan             │
│     └─→ Refactor phase: clean up, optimize                   │
└──────────────────────────────────────────────────────────────┘
```

### 5.5 Key Steps

```
Step 1: Set Up Project Scaffold
  └─→ Initialize repo, install dependencies, configure linting/formatting

Step 2: Configure AI Tools
  └─→ Install Superpowers skills, configure .cursorrules or CLAUDE.md

Step 3: Implement Feature-by-Feature
  └─→ For each user story:
      a) Write failing tests first (TDD)
      b) Implement the feature
      c) Make all tests pass
      d) Refactor and review

Step 4: Code Review
  └─→ AI generates PR description
  └─→ Human reviews diff for correctness, security, performance

Step 5: Documentation
  └─→ AI generates inline docs, README updates, API docs
```

### 5.6 Demo: Implementing a Feature with Superpowers + Claude Code

```bash
# 1. Install Superpowers in your project
git clone https://github.com/obra/superpowers.git .superpowers

# 2. Configure Claude Code to use Superpowers skills
cat >> CLAUDE.md << 'EOF'
## Development Process
Always follow the Superpowers workflow:
1. Brainstorm before planning
2. Plan with TDD (write tests first)
3. Execute in focused sub-tasks
4. Review against the plan
Consult .superpowers/skills/ for detailed process instructions.
EOF
```

**Example: Implementing "Create Task" endpoint**

```javascript
// ---- STEP 1: Write the test FIRST (Red) ----
// tests/api/tasks.test.js
import { describe, it, expect, beforeEach } from 'vitest';
import request from 'supertest';
import { app } from '../../src/app.js';
import { db } from '../../src/db.js';

describe('POST /api/tasks', () => {
  beforeEach(async () => {
    await db.query('DELETE FROM tasks');
  });

  it('should create a new task with valid data', async () => {
    const newTask = {
      title: 'Build login page',
      description: 'Create a responsive login form',
      priority: 'high',
    };

    const response = await request(app)
      .post('/api/tasks')
      .send(newTask)
      .expect(201);

    expect(response.body).toMatchObject({
      id: expect.any(String),
      title: 'Build login page',
      description: 'Create a responsive login form',
      priority: 'high',
      status: 'todo',
      createdAt: expect.any(String),
    });
  });

  it('should return 400 if title is missing', async () => {
    const response = await request(app)
      .post('/api/tasks')
      .send({ description: 'No title' })
      .expect(400);

    expect(response.body.error).toBe('Title is required');
  });

  it('should default priority to "medium" if not provided', async () => {
    const response = await request(app)
      .post('/api/tasks')
      .send({ title: 'Default priority task' })
      .expect(201);

    expect(response.body.priority).toBe('medium');
  });
});
```

```javascript
// ---- STEP 2: Implement the feature (Green) ----
// src/routes/tasks.js
import { Router } from 'express';
import { v4 as uuidv4 } from 'uuid';
import { db } from '../db.js';

const router = Router();

router.post('/', async (req, res) => {
  const { title, description = '', priority = 'medium' } = req.body;

  // Validation
  if (!title || title.trim() === '') {
    return res.status(400).json({ error: 'Title is required' });
  }

  const validPriorities = ['low', 'medium', 'high', 'urgent'];
  const taskPriority = validPriorities.includes(priority) ? priority : 'medium';

  // Create task
  const task = {
    id: uuidv4(),
    title: title.trim(),
    description: description.trim(),
    priority: taskPriority,
    status: 'todo',
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  };

  await db.query(
    `INSERT INTO tasks (id, title, description, priority, status, created_at, updated_at)
     VALUES ($1, $2, $3, $4, $5, $6, $7)`,
    [task.id, task.title, task.description, task.priority, task.status, task.createdAt, task.updatedAt]
  );

  return res.status(201).json(task);
});

export default router;
```

```bash
# ---- STEP 3: Run tests to confirm (Green ✅) ----
npx vitest run tests/api/tasks.test.js

# Output:
# ✓ should create a new task with valid data
# ✓ should return 400 if title is missing
# ✓ should default priority to "medium" if not provided
# Test Files  1 passed
# Tests       3 passed
```

---

## 6. Phase 5: Testing — Quality Assurance

### 6.1 Purpose

Validate that the software meets requirements, is free of defects, and performs well under expected conditions.

### 6.2 Recommended Tools

| Tool | Type | Best For | Link |
|:---|:---|:---|:---|
| **Browser-Use** | OSS | AI browser agents for E2E testing | [GitHub: browser-use](https://github.com/langchain-ai/browser-use) |
| **Stagehand** | OSS | AI + Playwright bridge | [GitHub: browserbase/stagehand](https://github.com/browserbase/stagehand) |
| **Playwright** | OSS | E2E browser testing | [playwright.dev](https://playwright.dev) |
| **Vitest** | OSS | Unit & integration tests (JS) | [vitest.dev](https://vitest.dev) |
| **pytest** | OSS | Unit & integration tests (Python) | [pytest.org](https://pytest.org) |
| **LaVague** | OSS | Natural language → test automation | [GitHub: lavague-ai](https://github.com/lavague-ai/lavague) |
| **QA Wolf** | Platform | AI-generated Playwright tests | [qawolf.com](https://qawolf.com) |

### 6.3 Should You Build an AI Agent for Testing?

**Yes — but strategically.** Here's when and how:

| Scenario | Recommendation |
|:---|:---|
| **Unit tests** | Use AI code assistants (Copilot, Claude) to *generate* tests. No custom agent needed. |
| **E2E / UI tests** | ✅ Build or use an AI testing agent (Browser-Use, Stagehand). High ROI. |
| **Regression testing** | ✅ AI agent can detect UI changes and self-heal locators. |
| **Exploratory testing** | ✅ AI agent can crawl your app and find unexpected behaviors. |
| **Load/Performance testing** | Use traditional tools (k6, Artillery). AI not yet cost-effective here. |

### 6.4 The Testing Pyramid with AI

```
                    ▲
                   / \
                  / E2E \          ← AI Agents (Browser-Use, Stagehand)
                 /  Tests \           Autonomous browser testing
                /───────────\
               / Integration \     ← AI-Generated (Claude, Copilot)
              /    Tests      \       API contract tests, DB tests
             /─────────────────\
            /    Unit Tests     \   ← AI-Generated (Superpowers TDD)
           /     (Foundation)    \     Fast, deterministic, high volume
          /───────────────────────\
```

### 6.5 Key Steps

```
Step 1: Write Unit Tests (TDD with Superpowers)
  └─→ Test individual functions, edge cases, error handling

Step 2: Write Integration Tests
  └─→ Test API endpoints, database interactions, service communication

Step 3: Write E2E Tests
  └─→ Test complete user flows in a real browser

Step 4: Set Up AI Testing Agent (optional but recommended)
  └─→ Configure Browser-Use or Stagehand for autonomous UI testing

Step 5: Set Up Test Coverage Reporting
  └─→ Enforce minimum coverage thresholds (e.g., 80%)

Step 6: Integrate Tests into CI/CD
  └─→ Tests must pass before merge/deploy
```

### 6.6 Demo: AI-Powered E2E Testing with Stagehand

```typescript
// tests/e2e/create-task.test.ts
// Using Stagehand — AI + Playwright bridge

import { Stagehand } from '@browserbase/stagehand';

async function testCreateTask() {
  const stagehand = new Stagehand({
    env: 'LOCAL',
    enableCaching: true,
  });
  await stagehand.init();

  // Navigate to the app
  await stagehand.page.goto('http://localhost:3000');

  // AI-powered action: click "New Task" button
  // Stagehand uses AI to find the right element even if selectors change
  await stagehand.act({ action: 'click the New Task button' });

  // AI-powered action: fill in the form
  await stagehand.act({ action: 'type "Build login page" in the task title field' });
  await stagehand.act({ action: 'type "Create a responsive login form" in the description field' });
  await stagehand.act({ action: 'select "High" from the priority dropdown' });
  await stagehand.act({ action: 'click the Submit button' });

  // AI-powered extraction: verify the result
  const result = await stagehand.extract({
    instruction: 'Extract the title and status of the most recently created task',
    schema: {
      type: 'object',
      properties: {
        title: { type: 'string' },
        status: { type: 'string' },
      },
    },
  });

  console.assert(result.title === 'Build login page', 'Task title should match');
  console.assert(result.status === 'To Do', 'Task status should be "To Do"');

  console.log('✅ Create Task E2E test passed!');
  await stagehand.close();
}

testCreateTask().catch(console.error);
```

### 6.7 Demo: Building a Simple AI Testing Agent with Browser-Use

```python
# tests/ai_agent/test_agent.py
# AI testing agent using Browser-Use

from langchain_openai import ChatOpenAI
from browser_use import Agent

import asyncio

async def run_test_agent():
    """
    An AI agent that autonomously tests the Task Tracker app.
    It navigates the UI, performs actions, and validates results.
    """

    agent = Agent(
        task="""
        You are a QA tester for a Task Tracker application at http://localhost:3000.

        Please perform the following test cases:

        1. CREATE TEST:
           - Click "New Task"
           - Fill in title: "Test Task from AI Agent"
           - Set priority to "High"
           - Submit the form
           - Verify the task appears in the "To Do" column

        2. DRAG TEST:
           - Drag "Test Task from AI Agent" to the "In Progress" column
           - Verify the task is now in "In Progress"

        3. SEARCH TEST:
           - Use the search bar to search for "AI Agent"
           - Verify the task "Test Task from AI Agent" appears in results

        4. DELETE TEST:
           - Delete "Test Task from AI Agent"
           - Verify it no longer appears

        Report PASS or FAIL for each test case with details.
        """,
        llm=ChatOpenAI(model="gpt-4o"),
    )

    result = await agent.run()
    print("Test Results:")
    print(result)

asyncio.run(run_test_agent())
```

---

## 7. Phase 6: Deployment — CI/CD & Release

### 7.1 Purpose

Automate the path from code commit to production, ensuring consistent, reliable, and safe releases.

### 7.2 Recommended Tools

| Tool | Type | Best For | Link |
|:---|:---|:---|:---|
| **GitHub Actions** | Platform | CI/CD automation | [github.com/actions](https://github.com/features/actions) |
| **Docker** | OSS | Containerization | [docker.com](https://docker.com) |
| **Vercel** | Platform | Frontend deployment | [vercel.com](https://vercel.com) |
| **Railway** | Platform | Backend + DB deployment | [railway.app](https://railway.app) |
| **Terraform** | OSS | Infrastructure as Code | [terraform.io](https://terraform.io) |
| **ArgoCD** | OSS | Kubernetes GitOps | [argoproj.github.io](https://argoproj.github.io/cd) |

### 7.3 Key Steps

```
Step 1: Containerize Your Application
  └─→ Write Dockerfiles for frontend & backend

Step 2: Set Up CI Pipeline (Build + Test)
  └─→ On every PR: lint → test → build → security scan

Step 3: Set Up CD Pipeline (Deploy)
  └─→ On merge to main: deploy to staging
  └─→ On release tag: deploy to production

Step 4: Configure Environment Management
  └─→ Development → Staging → Production
  └─→ Use environment-specific secrets

Step 5: Set Up Monitoring & Alerting
  └─→ Health checks, error tracking, performance monitoring

Step 6: Implement Rollback Strategy
  └─→ Blue-green or canary deployments for zero-downtime
```

### 7.4 CI/CD Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     CI/CD Pipeline                              │
│                                                                 │
│  Developer Push                                                 │
│       │                                                         │
│       ▼                                                         │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐    │
│  │  LINT    │→│   TEST   │→│  BUILD   │→│ SECURITY │    │
│  │ ESLint   │  │ Unit     │  │ Docker   │  │  Scan    │    │
│  │ Prettier │  │ Integr.  │  │ Image    │  │ Trivy    │    │
│  │          │  │ E2E      │  │          │  │ Snyk     │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
│                                                 │               │
│                                                 ▼               │
│                              ┌──────────────────────────┐       │
│                              │    DEPLOY TO STAGING     │       │
│                              │    (automatic on main)   │       │
│                              └────────────┬─────────────┘       │
│                                           │                     │
│                                    Manual Approval               │
│                                           │                     │
│                                           ▼                     │
│                              ┌──────────────────────────┐       │
│                              │   DEPLOY TO PRODUCTION   │       │
│                              │   (on release tag)       │       │
│                              └──────────────┬───────────┘       │
│                                             │                   │
│                                             ▼                   │
│                              ┌──────────────────────────┐       │
│                              │      MONITOR & ALERT     │       │
│                              │   Health checks, logs,   │       │
│                              │   error rates, latency   │       │
│                              └──────────────────────────┘       │
└─────────────────────────────────────────────────────────────────┘
```

### 7.5 Demo: Complete GitHub Actions CI/CD Pipeline

```yaml
# .github/workflows/ci-cd.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  release:
    types: [published]

env:
  NODE_VERSION: '20'
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  # ──────────────────────────────
  # Stage 1: Lint & Format Check
  # ──────────────────────────────
  lint:
    name: 🔍 Lint & Format
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
      - run: npm ci
      - run: npm run lint
      - run: npm run format:check

  # ──────────────────────────────
  # Stage 2: Unit & Integration Tests
  # ──────────────────────────────
  test:
    name: 🧪 Test
    runs-on: ubuntu-latest
    needs: lint
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB: tasktracker_test
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
      - run: npm ci
      - run: npm run test:ci
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/tasktracker_test
      - name: Upload coverage
        uses: actions/upload-artifact@v4
        with:
          name: coverage-report
          path: coverage/

  # ──────────────────────────────
  # Stage 3: E2E Tests
  # ──────────────────────────────
  e2e:
    name: 🌐 E2E Tests
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
      - run: npm ci
      - run: npx playwright install --with-deps
      - run: npm run test:e2e
      - name: Upload E2E results
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: playwright-report
          path: playwright-report/

  # ──────────────────────────────
  # Stage 4: Build & Push Docker Image
  # ──────────────────────────────
  build:
    name: 🐳 Build Docker Image
    runs-on: ubuntu-latest
    needs: [test, e2e]
    if: github.ref == 'refs/heads/main' || github.event_name == 'release'
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v4
      - uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - uses: docker/metadata-action@v5
        id: meta
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=sha
            type=ref,event=branch
            type=semver,pattern={{version}}
      - uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}

  # ──────────────────────────────
  # Stage 5: Security Scan
  # ──────────────────────────────
  security:
    name: 🔒 Security Scan
    runs-on: ubuntu-latest
    needs: build
    steps:
      - uses: actions/checkout@v4
      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:sha-${{ github.sha }}
          format: 'sarif'
          output: 'trivy-results.sarif'
      - name: Upload Trivy scan results
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: 'trivy-results.sarif'

  # ──────────────────────────────
  # Stage 6: Deploy to Staging
  # ──────────────────────────────
  deploy-staging:
    name: 🚀 Deploy to Staging
    runs-on: ubuntu-latest
    needs: [build, security]
    if: github.ref == 'refs/heads/main'
    environment:
      name: staging
      url: https://staging.tasktracker.example.com
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to staging
        run: |
          echo "Deploying to staging..."
          # Example: Deploy to Railway, Vercel, or Kubernetes
          # railway up --environment staging
          # OR
          # kubectl set image deployment/tasktracker \
          #   api=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:sha-${{ github.sha }}
      - name: Run smoke tests
        run: |
          curl -f https://staging.tasktracker.example.com/health || exit 1

  # ──────────────────────────────
  # Stage 7: Deploy to Production
  # ──────────────────────────────
  deploy-production:
    name: 🎯 Deploy to Production
    runs-on: ubuntu-latest
    needs: deploy-staging
    if: github.event_name == 'release'
    environment:
      name: production
      url: https://tasktracker.example.com
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to production
        run: |
          echo "Deploying to production..."
          # railway up --environment production
      - name: Verify deployment
        run: |
          curl -f https://tasktracker.example.com/health || exit 1
      - name: Notify team
        run: |
          echo "✅ Deployed version ${{ github.event.release.tag_name }} to production"
```

### 7.6 Demo: Dockerfile

```dockerfile
# Dockerfile — Multi-stage build for Task Tracker API

# ── Stage 1: Build ──
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --production=false
COPY . .
RUN npm run build

# ── Stage 2: Production ──
FROM node:20-alpine AS production
WORKDIR /app

# Security: run as non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S tasktracker -u 1001
USER tasktracker

COPY --from=builder --chown=tasktracker:nodejs /app/dist ./dist
COPY --from=builder --chown=tasktracker:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=tasktracker:nodejs /app/package.json ./

EXPOSE 3001

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3001/health || exit 1

CMD ["node", "dist/server.js"]
```

---

## 8. Tool Comparison Matrix

### When to Use What — Complete Recommendation

| Phase | Primary Tool | Secondary Tool | Open Source? |
|:---|:---|:---|:---|
| **Product / PRD** | OpenSpec | ChatPRD, Notion AI | ✅ (OpenSpec) |
| **Project Management** | Linear / Jira | GitHub Projects | ❌ (SaaS) |
| **Architecture** | Mermaid + Structurizr | OpenSpec (ADRs), Eraser.io | ✅ |
| **Development** | Superpowers + Claude Code | Cursor, GitHub Copilot | ✅ (Superpowers) |
| **Testing** | Vitest + Playwright | Stagehand, Browser-Use | ✅ |
| **Deployment** | GitHub Actions + Docker | Railway, Vercel | ✅ (GH Actions) |

### OpenSpec vs. Superpowers — Side by Side

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│  ┌──────────────────────────┐     ┌──────────────────────────────────┐  │
│  │       OpenSpec           │     │         Superpowers              │  │
│  │  "What to build"         │     │    "How to build it well"        │  │
│  │                          │     │                                  │  │
│  │  • Propose specs         │ ──→ │  • Brainstorm approach           │  │
│  │  • Define requirements   │     │  • Plan with TDD                 │  │
│  │  • Create design docs    │     │  • Execute via sub-agents        │  │
│  │  • Archive decisions     │     │  • Review & refactor             │  │
│  │                          │     │                                  │  │
│  │  Phase: Product, Arch    │     │  Phase: Development, Testing     │  │
│  └──────────────────────────┘     └──────────────────────────────────┘  │
│                                                                         │
│  Together they form a complete AI-powered development workflow          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 9. End-to-End Demo: Building a "Task Tracker" App

This section summarizes how all phases connect for the Task Tracker example used throughout this guide.

### Phase Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Task Tracker — Full Lifecycle                    │
│                                                                         │
│  1. PRODUCT ──────────────────────────────────────────────────────────  │
│     │  Tool: OpenSpec                                                   │
│     │  Output: PRD with 3 user stories (Create, Drag, Search)          │
│     │  Demo: .openspec/proposals/001-task-tracker.md                    │
│     ▼                                                                   │
│  2. PROJECT MANAGEMENT ──────────────────────────────────────────────  │
│     │  Tool: Linear / GitHub Projects                                   │
│     │  Output: 11 tasks across 2 epics, Sprint 1 planned               │
│     │  Demo: Sprint backlog with T-shirt estimates                     │
│     ▼                                                                   │
│  3. ARCHITECTURE ────────────────────────────────────────────────────  │
│     │  Tool: Mermaid.js, OpenSpec (ADRs)                                │
│     │  Output: C4 diagrams, ADR-001 (tech stack decision)              │
│     │  Demo: Context + Container diagrams                              │
│     ▼                                                                   │
│  4. DEVELOPMENT ─────────────────────────────────────────────────────  │
│     │  Tool: Superpowers + Claude Code                                  │
│     │  Output: Working API & UI, TDD-driven implementation             │
│     │  Demo: POST /api/tasks with tests passing                        │
│     ▼                                                                   │
│  5. TESTING ─────────────────────────────────────────────────────────  │
│     │  Tool: Vitest (unit), Playwright (E2E), Stagehand (AI agent)     │
│     │  Output: Test suite with >80% coverage                           │
│     │  Demo: AI agent autonomously tests CRUD + drag-and-drop          │
│     ▼                                                                   │
│  6. DEPLOYMENT ──────────────────────────────────────────────────────  │
│     │  Tool: GitHub Actions, Docker, Railway + Vercel                   │
│     │  Output: CI/CD pipeline, staging + production environments       │
│     │  Demo: 7-stage pipeline YAML                                     │
│     ▼                                                                   │
│  ✅ LIVE IN PRODUCTION                                                  │
│     │  Monitor → Feedback → Iterate (back to Step 1)                   │
└─────────────────────────────────────────────────────────────────────────┘
```

### Quick Start Checklist

- [ ] **Product**: Initialize OpenSpec → Write PRD → Get stakeholder approval
- [ ] **Project**: Decompose user stories → Estimate → Plan Sprint 1
- [ ] **Architecture**: Draw C4 diagrams → Write ADRs → Choose tech stack
- [ ] **Development**: Set up Superpowers → Write tests first → Implement features
- [ ] **Testing**: Unit tests → Integration tests → E2E with AI agent
- [ ] **Deployment**: Dockerfile → GitHub Actions CI/CD → Deploy to staging → Production

---

## 📚 Essential GitHub Repositories

| Repository | Stars | Purpose |
|:---|:---|:---|
| [Fission-AI/OpenSpec](https://github.com/Fission-AI/OpenSpec) | ⭐ | Spec-driven development framework |
| [obra/superpowers](https://github.com/obra/superpowers) | ⭐ | Agentic coding skills (TDD, planning) |
| [langchain-ai/browser-use](https://github.com/langchain-ai/browser-use) | ⭐ | AI browser agent for testing |
| [browserbase/stagehand](https://github.com/browserbase/stagehand) | ⭐ | AI + Playwright bridge |
| [lavague-ai/lavague](https://github.com/lavague-ai/lavague) | ⭐ | Natural language → browser automation |
| [structurizr/dsl](https://github.com/structurizr/dsl) | ⭐ | C4 Architecture as Code |
| [plantuml-stdlib/C4-PlantUML](https://github.com/plantuml-stdlib/C4-PlantUML) | ⭐ | C4 diagrams with PlantUML |
| [microsoft/playwright](https://github.com/microsoft/playwright) | ⭐ | Browser automation & E2E testing |
| [cline/cline](https://github.com/cline/cline) | ⭐ | Autonomous AI coding in VS Code |

---

## 🔑 Key Takeaways

1. **Specs before code**: Use **OpenSpec** to define *what* to build before writing any code.
2. **Discipline during coding**: Use **Superpowers** to enforce TDD and structured workflows.
3. **AI for testing**: Build or adopt an AI testing agent (**Browser-Use** or **Stagehand**) for E2E testing — it's high ROI.
4. **Automate everything**: CI/CD with **GitHub Actions** + **Docker** ensures consistent, reliable deployments.
5. **Human-in-the-loop always**: AI drafts, humans review. Never skip code review.
6. **Iterate continuously**: The lifecycle is a loop, not a waterfall. Feedback from production drives the next cycle.

---

*Last updated: 2026-04-14*
