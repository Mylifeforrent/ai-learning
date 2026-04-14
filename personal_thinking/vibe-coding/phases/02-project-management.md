# Phase 2: Project Management — Planning & Tracking

## Purpose

Break down the PRD into actionable work items, estimate effort, assign ownership, and track progress.

## Recommended Tools

| Tool | Type | Best For | Link |
|:---|:---|:---|:---|
| **Linear** | Platform | AI-powered triage, capacity planning | [linear.app](https://linear.app) |
| **Jira + Rovo AI** | Platform | Enterprise teams, AI backlog management | [atlassian.com](https://atlassian.com) |
| **GitHub Projects** | Platform | Dev teams already on GitHub | [github.com](https://github.com) |
| **Claude / ChatGPT** | LLM | Story decomposition, estimation | - |

## How to Plan Project Management Based on User Stories

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

## Demo: Decomposing User Stories into Sprint Tasks

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

← [Back to Overview](../overall-view.md)
