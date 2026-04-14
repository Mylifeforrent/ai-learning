# Phase 1: Product — Vision, Requirements & Prototype

## Purpose

Define **what** to build, **for whom**, and **why**. This phase produces the Product Requirements Document (PRD), user stories, acceptance criteria, **and visual prototypes** that align stakeholders before any code is written.

## Recommended Tools

| Tool | Type | Best For | Link |
|:---|:---|:---|:---|
| **OpenSpec** | OSS Framework | Spec-driven development with AI agents | [GitHub: Fission-AI/OpenSpec](https://github.com/Fission-AI/OpenSpec) |
| **ChatPRD** | AI SaaS | Rapid PRD drafting from ideas | [chatprd.ai](https://chatprd.ai) |
| **Notion AI** | Platform | PRD + wiki + team collaboration | [notion.so](https://notion.so) |
| **Claude / ChatGPT** | LLM | Brainstorming, user story generation | - |

## Should You Use Superpowers or OpenSpec?

| Criteria | OpenSpec ✅ | Superpowers ❌ |
|:---|:---|:---|
| **Product/Requirements phase** | ✅ Designed for specs & proposals | ❌ Focused on code execution |
| **Output** | PRDs, proposals, design docs | Working, tested code |
| **Best Phase** | Product → Architecture | Development → Testing |

> **Recommendation**: Use **OpenSpec** for the Product phase. It forces you to write structured specs (Propose → Apply → Archive) before any code is written, which is the single most important best practice for AI-assisted development.

## Key Steps

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

Step 7: Prototype & Wireframe Design  ← NEW
  └─→ Low-fi wireframes → High-fi mockups → Interactive prototypes
  └─→ Use AI tools (v0, Figma AI, Uizard) to accelerate

Step 8: Stakeholder Review & Sign-off
  └─→ Walk through prototype with stakeholders before moving to architecture
```

## Prototype & Wireframe Design (Often Overlooked!)

Prototyping is a **critical sub-phase** that bridges Product and Architecture. Without it, developers build based on text specs alone, leading to costly rework.

### Why Prototype Before Coding?

```
Without Prototyping:
  PRD (text) → Developer interprets → Builds UI → "That's not what I meant"
  → Rework → Delay → Frustration

With Prototyping:
  PRD (text) → Prototype (visual) → Stakeholder says "YES, that's it!"
  → Developer builds exactly what was approved → Ship on time ✅
```

### Recommended Prototype Tools

| Tool | Type | Best For | Link |
|:---|:---|:---|:---|
| **v0 (by Vercel)** | AI Platform | Text → production-ready React/Tailwind code | [v0.dev](https://v0.dev) |
| **Figma AI** | Platform | Design system-aware wireframes & mockups | [figma.com](https://figma.com) |
| **Uizard** | AI Platform | Fast low-fi wireframes from text/sketches | [uizard.io](https://uizard.io) |
| **Excalidraw** | OSS | Quick hand-drawn style wireframes | [excalidraw.com](https://excalidraw.com) |
| **Whimsical** | Platform | Flowcharts + wireframes combined | [whimsical.com](https://whimsical.com) |

### The 3-Stage Prototype Workflow

```
┌──────────────────────────────────────────────────────────────────────────┐
│                     Prototype Design Workflow                           │
│                                                                          │
│  Stage 1: LOW-FI WIREFRAME                                               │
│  ├─ Tool: Excalidraw or Uizard                                          │
│  ├─ Focus: Layout, information hierarchy, user flow                     │
│  ├─ Time: 1-2 hours                                                     │
│  └─ Output: Rough sketches of key screens                               │
│                                                                          │
│  Stage 2: MID-FI MOCKUP                                                  │
│  ├─ Tool: Figma AI or Uizard                                            │
│  ├─ Focus: Component structure, spacing, navigation                     │
│  ├─ Time: 2-4 hours                                                     │
│  └─ Output: Grayscale mockups with real content                         │
│                                                                          │
│  Stage 3: HI-FI INTERACTIVE PROTOTYPE                                    │
│  ├─ Tool: v0.dev (generates real code) or Figma Prototype               │
│  ├─ Focus: Colors, typography, animations, clickable flows              │
│  ├─ Time: 4-8 hours                                                     │
│  └─ Output: Clickable prototype for stakeholder review                  │
│             OR actual React components ready for development            │
└──────────────────────────────────────────────────────────────────────────┘
```

### Best Practices for AI-Assisted Prototyping

```
✅ DO:
  • Build component-by-component, not entire pages at once
  • Provide design constraints ("use 8px grid", "dark mode", "mobile-first")
  • Use v0's "Fork" feature to explore multiple UI directions in parallel
  • Export v0 components into your actual codebase via "Add to Codebase"
  • Share interactive prototypes with stakeholders BEFORE coding starts

❌ DON'T:
  • Skip wireframing and jump straight to hi-fi design
  • Push AI-generated UI directly to production without review
  • Ignore mobile responsiveness in prototypes
  • Design in isolation — involve frontend devs in prototype review
```

### Demo: Using v0 to Prototype the Task Tracker

```markdown
## v0 Prompt for Task Tracker Kanban Board

"Create a Kanban board with three columns: To Do, In Progress, and Done.
Each column should have task cards that show:
- Task title
- Priority badge (Low=green, Medium=yellow, High=red)
- Assignee avatar
- Due date

Include a 'New Task' button with a modal form.
Use a dark theme with subtle gradients.
Make it responsive for mobile (cards stack vertically).
Use shadcn/ui components."
```

```markdown
## Expected Output from v0
- Functional React + Tailwind component code
- Responsive layout (desktop 3-column, mobile stacked)
- Interactive modal for task creation
- Ready to integrate into your Vite project

## Next Steps After v0 Prototype
1. Review with stakeholders → collect feedback
2. Fork the v0 project for alternative designs
3. Once approved, export components to your project:
   v0.dev → "Add to Codebase" → copies to your repo
4. Integrate with your API layer (see API-First section below)
```

## Demo: Creating a PRD with OpenSpec

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

← [Back to Overview](../overall-view.md)
