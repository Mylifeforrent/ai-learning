const form = document.querySelector("#requirementForm");
const input = document.querySelector("#requirementInput");
const messages = document.querySelector("#messages");
const output = document.querySelector("#resultOutput");
const traceOutput = document.querySelector("#traceOutput");
const statusText = document.querySelector("#statusText");
const submitButton = document.querySelector("#submitButton");
const sampleButton = document.querySelector("#sampleButton");
const copyButton = document.querySelector("#copyButton");
const health = document.querySelector("#health");
const reviewControls = document.querySelector("#reviewControls");
const feedbackInput = document.querySelector("#feedbackInput");
const rejectButton = document.querySelector("#rejectButton");
const approveButton = document.querySelector("#approveButton");
const counterOutput = document.querySelector("#counterOutput");
const counterValue = document.querySelector("#counterValue");
const counterSummary = document.querySelector("#counterSummary");

let currentReview = null;

const sampleRequirement = `Build a login feature for a web application.

Functional requirements:
- Users can log in with email and password.
- Email must use a valid email format.
- Password is required and must not be empty.
- Valid users are redirected to the dashboard.
- Invalid credentials show a clear error message.
- After five consecutive failed attempts, the account is locked for 15 minutes.

Non-functional requirements:
- Normal login response time should be under 2 seconds.
- Error messages must not reveal whether the email or password was incorrect.
- The login page must support keyboard navigation.`;

function addMessage(role, content) {
  const article = document.createElement("article");
  article.className = `message ${role}`;

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = content;

  article.appendChild(bubble);
  messages.appendChild(article);
  messages.scrollTop = messages.scrollHeight;
}

function setLoading(isLoading) {
  submitButton.disabled = isLoading;
  input.disabled = isLoading;
  rejectButton.disabled = isLoading;
  approveButton.disabled = isLoading;
  if (isLoading) {
    statusText.textContent = "Agents are working...";
  }
}

function setReviewControlsVisible(isVisible) {
  reviewControls.hidden = !isVisible;
}

function renderCounter(data) {
  const count = data.chinese_character_count;
  counterOutput.hidden = count === null || count === undefined;
  counterValue.textContent = String(count ?? 0);
  counterSummary.textContent = data.counter_summary || "Tool call completed.";
}

function renderTrace(messagesList = []) {
  traceOutput.innerHTML = "";

  for (const message of messagesList) {
    const item = document.createElement("div");
    item.className = "trace-item";

    const source = document.createElement("strong");
    source.textContent = `${message.source} · ${message.type}`;

    const content = document.createElement("span");
    content.textContent = message.content;

    item.append(source, content);
    traceOutput.appendChild(item);
  }
}

async function checkHealth() {
  try {
    const response = await fetch("/health");
    health.textContent = response.ok ? "online" : "error";
  } catch {
    health.textContent = "offline";
  }
}

async function postJson(url, payload) {
  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || "Backend request failed");
  }

  return data;
}

async function generateReview(requirement) {
  return postJson("/api/review", {
    requirement,
    max_messages: 12,
  });
}

async function reviseReview() {
  const feedback = feedbackInput.value.trim();
  if (feedback.length < 3) {
    statusText.textContent = "Add rejection feedback first";
    feedbackInput.focus();
    return;
  }

  if (!currentReview) {
    statusText.textContent = "No draft to revise";
    return;
  }

  addMessage("user", `Rejected with feedback:\n${feedback}`);
  addMessage("assistant", "Sending feedback to TestCaseWriter and TestCaseReviewer...");
    output.textContent = "Revising test cases...";
    counterOutput.hidden = true;
    setLoading(true);

  try {
    const data = await postJson("/api/revise", {
      requirement: currentReview.requirement,
      previous_test_cases: currentReview.draft_test_cases,
      reviewer_comments: currentReview.review,
      human_feedback: feedback,
      max_messages: 12,
    });

    currentReview = {
      ...data,
      requirement: currentReview.requirement,
    };
    output.textContent = data.draft_test_cases || data.final_test_cases || "No draft returned.";
    renderCounter(data);
    renderTrace([...(data.messages || []), ...(data.counter_trace || [])]);
    feedbackInput.value = "";
    setReviewControlsVisible(true);
    addMessage("assistant", "Revision ready. Please approve or reject again with feedback.");
    statusText.textContent = "Awaiting human review";
  } catch (error) {
    addMessage("assistant", `Revision failed: ${error.message}`);
    statusText.textContent = "Error";
  } finally {
    setLoading(false);
  }
}

sampleButton.addEventListener("click", () => {
  input.value = sampleRequirement;
  input.focus();
});

copyButton.addEventListener("click", async () => {
  await navigator.clipboard.writeText(output.textContent);
  statusText.textContent = "Copied";
  window.setTimeout(() => {
    statusText.textContent = "Ready";
  }, 1200);
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const requirement = input.value.trim();
  if (requirement.length < 10) {
    statusText.textContent = "Requirement is too short";
    return;
  }

  addMessage("user", requirement);
  addMessage("assistant", "Received. Running TestCaseWriter and TestCaseReviewer...");
  output.textContent = "Generating draft test cases and reviewer comments...";
  traceOutput.innerHTML = "";
  counterOutput.hidden = true;
  copyButton.disabled = true;
  currentReview = null;
  feedbackInput.value = "";
  setReviewControlsVisible(false);
  setLoading(true);

  try {
    const data = await generateReview(requirement);
    currentReview = {
      ...data,
      requirement,
    };
    output.textContent = data.draft_test_cases || data.final_test_cases || "No draft returned.";
    renderCounter(data);
    renderTrace([...(data.messages || []), ...(data.counter_trace || [])]);
    setReviewControlsVisible(true);
    addMessage("assistant", "Draft and AI review are ready. Please approve or reject with feedback.");
    statusText.textContent = "Awaiting human review";
  } catch (error) {
    output.textContent = "";
    addMessage("assistant", `Request failed: ${error.message}`);
    statusText.textContent = "Error";
  } finally {
    setLoading(false);
  }
});

rejectButton.addEventListener("click", reviseReview);

approveButton.addEventListener("click", () => {
  if (!currentReview) {
    statusText.textContent = "No draft to approve";
    return;
  }

  setReviewControlsVisible(false);
  copyButton.disabled = false;
  statusText.textContent = "Approved";
  addMessage("user", "Approved final test cases.");
  addMessage("assistant", "Done. Human approval recorded.");
});

checkHealth();
