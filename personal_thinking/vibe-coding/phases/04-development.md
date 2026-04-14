# Phase 4: Development — Implementation, Review & Security

## Purpose

Write code following the architecture and specs. Use AI agents to accelerate implementation while maintaining quality. **Enforce code review, dependency management, and security scanning as integral parts of development — not afterthoughts.**

## Recommended Tools

| Tool | Type | Best For | Link |
|:---|:---|:---|:---|
| **Superpowers** | OSS Framework | Disciplined AI coding (TDD, planning) | [GitHub: obra/superpowers](https://github.com/obra/superpowers) |
| **Claude Code** | AI Agent | Autonomous coding agent | [anthropic.com](https://anthropic.com) |
| **Cursor** | AI IDE | AI-first code editor | [cursor.com](https://cursor.com) |
| **GitHub Copilot** | AI Extension | Inline code suggestions | [github.com/copilot](https://github.com/copilot) |
| **OpenSpec** | OSS Framework | Spec → code implementation | [GitHub: Fission-AI/OpenSpec](https://github.com/Fission-AI/OpenSpec) |
| **Cline** | OSS Extension | Autonomous coding in VS Code | [GitHub: cline/cline](https://github.com/cline/cline) |

## Should You Use Superpowers or OpenSpec?

| Criteria | Superpowers ✅ | OpenSpec |
|:---|:---|:---|
| **Development phase** | ✅ Enforces TDD, planning, sub-agents | Specs already written in Product phase |
| **Workflow** | Brainstorm → Plan → Execute → Review | Propose → Apply → Archive |
| **Best For** | Ensuring AI writes *quality* code | Ensuring AI writes *the right* code |

> **Recommendation**: Use **both together**:
> 1. **OpenSpec** creates the spec (what to build)
> 2. **Superpowers** governs how AI builds it (TDD, review, sub-agents)

## The Superpowers Workflow

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

## Key Steps

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

Step 4: Code Review  ← EXPANDED BELOW
  └─→ AI generates PR description
  └─→ Human reviews diff for correctness, security, performance
  └─→ Use a second AI agent as a "review agent" for cross-checking

Step 5: Dependency Management & Security  ← NEW
  └─→ Audit dependencies: `npm audit`, `snyk test`
  └─→ Generate SBOM (Software Bill of Materials)
  └─→ Enforce: no new deps without explicit approval

Step 6: Documentation
  └─→ AI generates inline docs, README updates, API docs
```

## Code Review Best Practices (Human + AI)

Code review is even MORE critical when AI generates code, because AI can produce code that "looks right" but has subtle bugs, security holes, or architectural violations.

### The Dual-Review Pattern

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Code Review Pipeline                                 │
│                                                                         │
│  Developer (or AI) submits PR                                           │
│       │                                                                 │
│       ▼                                                                 │
│  ┌──────────────┐                                                       │
│  │ AUTOMATED     │ Lint, format, type-check, unit tests, security scan  │
│  │ REVIEW        │ (Must all pass before human review)                  │
│  └──────┬───────┘                                                       │
│         │                                                               │
│         ▼                                                               │
│  ┌──────────────┐                                                       │
│  │ AI REVIEW     │ A second AI agent reviews the diff for:              │
│  │ AGENT         │ • Security vulnerabilities                           │
│  │               │ • Logic errors                                       │
│  │               │ • Architectural violations                           │
│  │               │ • Missing error handling                              │
│  └──────┬───────┘                                                       │
│         │                                                               │
│         ▼                                                               │
│  ┌──────────────┐                                                       │
│  │ HUMAN REVIEW  │ Focus on:                                            │
│  │               │ • Business logic correctness                         │
│  │               │ • Architecture fit                                   │
│  │               │ • Edge cases the AI might miss                       │
│  │               │ • "Does this actually solve the problem?"             │
│  └──────┬───────┘                                                       │
│         │                                                               │
│         ▼                                                               │
│  ✅ MERGE (after all checks pass + human approval)                      │
└─────────────────────────────────────────────────────────────────────────┘
```

### PR Review Checklist

```markdown
## PR Review Checklist (Copy to Your PR Template)

### Automated (CI must pass)
- [ ] Lint & format checks pass
- [ ] All existing tests pass
- [ ] New tests added for new functionality
- [ ] Type checking passes (no `any` types)
- [ ] Security scan passes (no known vulnerabilities)
- [ ] Test coverage ≥ 80%

### AI Review Agent
- [ ] No SQL injection risks
- [ ] No XSS vulnerabilities
- [ ] No exposed secrets/tokens
- [ ] Error handling covers all failure paths
- [ ] API contract matches OpenAPI spec

### Human Review
- [ ] PR is small and focused (< 400 lines)
- [ ] Business logic is correct
- [ ] Code follows established architecture patterns
- [ ] No unnecessary dependencies added
- [ ] No config files modified without approval
- [ ] Documentation updated if needed
```

## Dependency Management & Supply Chain Security

AI agents frequently add new dependencies without considering security, licensing, or bundle size. This is a critical risk.

### Rules for Dependencies

```
1. LOCK YOUR DEPENDENCIES
   Always commit package-lock.json / pnpm-lock.yaml
   Use exact versions, not ranges: "express": "4.18.2" not "^4.18.2"

2. AUDIT REGULARLY
   npm audit / pnpm audit → fix critical & high vulnerabilities
   snyk test → deeper vulnerability scanning

3. GENERATE SBOM (Software Bill of Materials)
   The SBOM is a complete inventory of all components in your software.
   Required by many compliance frameworks (EU Cyber Resilience Act).

   npx @cyclonedx/cyclonedx-npm --output-file sbom.json

4. ADD TO YOUR CLAUDE.md / RULES
   "NEVER add new npm dependencies without explicit human approval.
    If you need a new library, propose it first with:
    - Why it's needed
    - Bundle size impact
    - License type
    - Security audit status"

5. DEPENDABOT / RENOVATE
   Automate dependency updates with PR-based bots.
   Configure in .github/dependabot.yml
```

### Demo: Dependency Security Setup

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "npm"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10
    reviewers:
      - "your-team"
    labels:
      - "dependencies"
    # Group minor/patch updates together
    groups:
      production-deps:
        patterns:
          - "*"
        update-types:
          - "minor"
          - "patch"
```

## Demo: Implementing a Feature with Superpowers + Claude Code

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

← [Back to Overview](../overall-view.md)
