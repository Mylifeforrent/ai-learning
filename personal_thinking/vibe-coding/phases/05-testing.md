# Phase 5: Testing — Quality Assurance

## Purpose

Validate that the software meets requirements, is free of defects, and performs well under expected conditions.

## Recommended Tools

| Tool | Type | Best For | Link |
|:---|:---|:---|:---|
| **Browser-Use** | OSS | AI browser agents for E2E testing | [GitHub: browser-use](https://github.com/langchain-ai/browser-use) |
| **Stagehand** | OSS | AI + Playwright bridge | [GitHub: browserbase/stagehand](https://github.com/browserbase/stagehand) |
| **Playwright** | OSS | E2E browser testing | [playwright.dev](https://playwright.dev) |
| **Vitest** | OSS | Unit & integration tests (JS) | [vitest.dev](https://vitest.dev) |
| **pytest** | OSS | Unit & integration tests (Python) | [pytest.org](https://pytest.org) |
| **LaVague** | OSS | Natural language → test automation | [GitHub: lavague-ai](https://github.com/lavague-ai/lavague) |
| **QA Wolf** | Platform | AI-generated Playwright tests | [qawolf.com](https://qawolf.com) |

## Should You Build an AI Agent for Testing?

**Yes — but strategically.** Here's when and how:

| Scenario | Recommendation |
|:---|:---|
| **Unit tests** | Use AI code assistants (Copilot, Claude) to *generate* tests. No custom agent needed. |
| **E2E / UI tests** | ✅ Build or use an AI testing agent (Browser-Use, Stagehand). High ROI. |
| **Regression testing** | ✅ AI agent can detect UI changes and self-heal locators. |
| **Exploratory testing** | ✅ AI agent can crawl your app and find unexpected behaviors. |
| **Load/Performance testing** | Use traditional tools (k6, Artillery). AI not yet cost-effective here. |

## The Testing Pyramid with AI

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

## Key Steps

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

## Demo: AI-Powered E2E Testing with Stagehand

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

## Demo: Building a Simple AI Testing Agent with Browser-Use

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

← [Back to Overview](../overall-view.md)
