const uploadForm = document.querySelector("#uploadForm");
const fileInput = document.querySelector("#fileInput");
const dropZone = document.querySelector("#dropZone");
const parseButton = document.querySelector("#parseButton");
const manualInput = document.querySelector("#manualInput");
const useManualButton = document.querySelector("#useManualButton");
const sampleButton = document.querySelector("#sampleButton");
const parsedContentInput = document.querySelector("#parsedContentInput");
const confirmParseButton = document.querySelector("#confirmParseButton");
const generateButton = document.querySelector("#generateButton");
const output = document.querySelector("#resultOutput");
const traceOutput = document.querySelector("#traceOutput");
const statusText = document.querySelector("#statusText");
const copyButton = document.querySelector("#copyButton");
const health = document.querySelector("#health");
const reviewControls = document.querySelector("#reviewControls");
const feedbackInput = document.querySelector("#feedbackInput");
const rejectButton = document.querySelector("#rejectButton");
const approveButton = document.querySelector("#approveButton");
const parseSummary = document.querySelector("#parseSummary");
const parsedFilename = document.querySelector("#parsedFilename");
const parsedParser = document.querySelector("#parsedParser");
const parsedQuality = document.querySelector("#parsedQuality");
const warningList = document.querySelector("#warningList");
const steps = [...document.querySelectorAll(".steps li")];

let currentParsedDocument = null;
let confirmedContent = "";
let currentReview = null;
let parseConfirmed = false;
let activeTimelineItems = new Map();
let writerStreamBuffer = "";
let selectedStep = "upload";

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

function setActiveStep(stepName) {
  selectedStep = stepName;
  let reachedActive = false;
  for (const step of steps) {
    const isActive = step.dataset.step === stepName;
    step.classList.toggle("is-active", isActive);
    step.classList.toggle("is-complete", !reachedActive && !isActive);
    if (isActive) {
      reachedActive = true;
    }
  }
}

function setBusy(isBusy) {
  parseButton.disabled = isBusy;
  fileInput.disabled = isBusy;
  useManualButton.disabled = isBusy;
  confirmParseButton.disabled = isBusy || !currentParsedDocument;
  generateButton.disabled = isBusy || !parseConfirmed;
  rejectButton.disabled = isBusy;
  approveButton.disabled = isBusy;
  if (isBusy) {
    statusText.textContent = "Agents are working...";
  }
}

function setReviewControlsVisible(isVisible) {
  reviewControls.hidden = !isVisible;
}

function resetTimeline() {
  traceOutput.innerHTML = "";
  activeTimelineItems = new Map();
}

function resetReviewState() {
  currentReview = null;
  writerStreamBuffer = "";
  output.textContent = "Confirm parsed content, then generate reviewed test cases.";
  copyButton.disabled = true;
  setReviewControlsVisible(false);
  feedbackInput.value = "";
}

function resetParseConfirmation() {
  parseConfirmed = false;
  confirmedContent = "";
  currentReview = null;
  generateButton.disabled = true;
  copyButton.disabled = true;
  setReviewControlsVisible(false);
}

function formatTime() {
  return new Date().toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function timelineKey(event) {
  if (event.event === "chunk") {
    return `${event.source}:stream`;
  }
  return `${event.source}:${event.type}:${Date.now()}:${Math.random()}`;
}

function createTimelineItem(event, content = "") {
  const details = document.createElement("details");
  details.className = `timeline-item ${event.source || "system"}`;
  details.open = event.event === "chunk" || event.event === "error";

  const summary = document.createElement("summary");
  const title = document.createElement("strong");
  title.textContent = event.source || "system";

  const meta = document.createElement("span");
  meta.textContent = `${event.type || event.event} · ${formatTime()}`;

  summary.append(title, meta);

  const body = document.createElement("pre");
  body.textContent = content;

  details.append(summary, body);
  traceOutput.appendChild(details);
  traceOutput.scrollTop = traceOutput.scrollHeight;

  return { details, body };
}

function appendTimelineEvent(event) {
  const content = event.content || "";

  if (event.event === "chunk") {
    const key = timelineKey(event);
    let item = activeTimelineItems.get(key);
    if (!item) {
      item = createTimelineItem({ ...event, type: "Streaming" });
      activeTimelineItems.set(key, item);
    }
    item.body.textContent += content;
    traceOutput.scrollTop = traceOutput.scrollHeight;
    return;
  }

  if (event.event === "message") {
    activeTimelineItems.delete(`${event.source}:stream`);
  }

  createTimelineItem(event, content);
}

async function checkHealth() {
  try {
    const response = await fetch("/health");
    health.textContent = response.ok ? "online" : "error";
  } catch {
    health.textContent = "offline";
  }
}

function updateParseSummary(parsedDocument) {
  parseSummary.hidden = false;
  parsedFilename.textContent = parsedDocument.filename || "-";
  parsedParser.textContent = parsedDocument.parser || "-";
  parsedQuality.textContent =
    parsedDocument.parse_quality_score === null || parsedDocument.parse_quality_score === undefined
      ? "-"
      : String(parsedDocument.parse_quality_score);

  const warnings = parsedDocument.warnings || [];
  warningList.hidden = warnings.length === 0;
  warningList.innerHTML = "";
  for (const warning of warnings) {
    const item = document.createElement("p");
    item.textContent = warning;
    warningList.appendChild(item);
  }
}

function handleStreamEvent(event) {
  appendTimelineEvent(event);

  if (event.source === "FileReadAgent") {
    setActiveStep("file-read");
  }

  if (event.source === "DocumentParseAgent") {
    setActiveStep(event.event === "final" ? "parse-confirm" : "parse");
  }

  if (event.source === "TestCaseWriter") {
    setActiveStep("writer");
  }

  if (event.source === "TestCaseReviewer") {
    setActiveStep("reviewer");
  }

  if (event.event === "chunk" && event.source === "TestCaseWriter") {
    writerStreamBuffer += event.content || "";
    output.textContent = writerStreamBuffer;
  }

  if (event.event === "message" && event.source === "TestCaseWriter") {
    writerStreamBuffer = event.content || writerStreamBuffer;
    output.textContent = writerStreamBuffer;
  }

  if (event.event === "status") {
    statusText.textContent = event.content || "Running";
  }

  if (event.parsed_document) {
    currentParsedDocument = event.parsed_document;
    parsedContentInput.value = currentParsedDocument.content_markdown || "";
    updateParseSummary(currentParsedDocument);
    confirmParseButton.disabled = false;
  }
}

async function postStream(url, payload) {
  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  return readEventStream(response);
}

async function postFormStream(url, formData) {
  const response = await fetch(url, {
    method: "POST",
    body: formData,
  });

  return readEventStream(response);
}

async function readEventStream(response) {
  if (!response.ok || !response.body) {
    let detail = "Backend request failed";
    try {
      const data = await response.json();
      detail = data.detail || detail;
    } catch {
      detail = response.statusText || detail;
    }
    throw new Error(detail);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let finalPayload = null;

  while (true) {
    const { value, done } = await reader.read();
    if (done) {
      break;
    }

    buffer += decoder.decode(value, { stream: true });
    const frames = buffer.split("\n\n");
    buffer = frames.pop() || "";

    for (const frame of frames) {
      const dataLine = frame.split("\n").find((line) => line.startsWith("data:"));
      if (!dataLine) {
        continue;
      }

      const event = JSON.parse(dataLine.slice(5).trim());
      handleStreamEvent(event);

      if (event.event === "error") {
        throw new Error(event.content || "Stream failed");
      }

      if (event.event === "final") {
        finalPayload = event;
      }
    }
  }

  if (!finalPayload) {
    throw new Error("Stream finished without final payload");
  }
  return finalPayload;
}

async function parseSelectedFile() {
  const file = fileInput.files?.[0];
  if (!file) {
    statusText.textContent = "Choose a file first";
    return;
  }

  resetTimeline();
  resetParseConfirmation();
  resetReviewState();
  setActiveStep("upload");
  setBusy(true);
  statusText.textContent = "Uploading file...";

  const formData = new FormData();
  formData.append("file", file);

  try {
    const data = await postFormStream("/api/documents/parse/stream", formData);
    currentParsedDocument = data.parsed_document;
    parsedContentInput.value = currentParsedDocument.content_markdown || "";
    updateParseSummary(currentParsedDocument);
    confirmParseButton.disabled = false;
    statusText.textContent = "Parsed. Awaiting parse confirmation";
  } catch (error) {
    currentParsedDocument = null;
    parsedContentInput.value = "";
    parseSummary.hidden = true;
    statusText.textContent = "Parse failed";
    appendTimelineEvent({
      event: "error",
      source: "DocumentParseAgent",
      type: "FrontendError",
      content: `${error.message}\nUse pasted text fallback if needed.`,
    });
  } finally {
    setBusy(false);
  }
}

function useManualText() {
  const content = manualInput.value.trim();
  if (content.length < 10) {
    statusText.textContent = "Pasted text is too short";
    manualInput.focus();
    return;
  }

  resetTimeline();
  resetParseConfirmation();
  resetReviewState();
  currentParsedDocument = {
    document_id: `manual-${Date.now()}`,
    filename: "pasted-requirement.md",
    mime_type: "text/markdown",
    parser: "plain_text",
    content_markdown: content,
    metadata: {
      source: "manual_text",
      character_count: content.length,
    },
    warnings: [],
    parse_quality_score: null,
  };

  parsedContentInput.value = content;
  updateParseSummary(currentParsedDocument);
  confirmParseButton.disabled = false;
  setActiveStep("parse-confirm");
  appendTimelineEvent({
    event: "final",
    source: "DocumentParseAgent",
    type: "ManualText",
    content: "Manual text wrapped as parsed Markdown. Awaiting human parse confirmation.",
  });
  statusText.textContent = "Awaiting parse confirmation";
}

function confirmParsedContent() {
  const content = parsedContentInput.value.trim();
  if (!currentParsedDocument || content.length < 10) {
    statusText.textContent = "Parsed content is too short";
    parsedContentInput.focus();
    return;
  }

  confirmedContent = content;
  parseConfirmed = true;
  generateButton.disabled = false;
  currentParsedDocument = {
    ...currentParsedDocument,
    content_markdown: content,
  };
  appendTimelineEvent({
    event: "message",
    source: "HumanParseConfirm",
    type: "TextMessage",
    content: "Parsed document content confirmed by human.",
  });
  setActiveStep("writer");
  statusText.textContent = "Parse confirmed. Ready to generate";
}

async function generateReview() {
  if (!parseConfirmed || !confirmedContent) {
    statusText.textContent = "Confirm parsed content first";
    return;
  }

  writerStreamBuffer = "";
  currentReview = null;
  output.textContent = "Generating draft test cases and reviewer comments...";
  copyButton.disabled = true;
  setReviewControlsVisible(false);
  setBusy(true);

  try {
    const data = await postStream("/api/review/stream", {
      parsed_document_id: currentParsedDocument?.document_id,
      confirmed_content: confirmedContent,
      parsed_document: currentParsedDocument,
      max_messages: 12,
    });

    currentReview = {
      ...data,
      confirmed_content: confirmedContent,
    };
    output.textContent = data.draft_test_cases || data.final_test_cases || "No draft returned.";
    setReviewControlsVisible(true);
    setActiveStep("final-confirm");
    statusText.textContent = "Awaiting final human review";
  } catch (error) {
    output.textContent = "";
    appendTimelineEvent({
      event: "error",
      source: "system",
      type: "FrontendError",
      content: error.message,
    });
    statusText.textContent = "Error";
  } finally {
    setBusy(false);
  }
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

  appendTimelineEvent({
    event: "message",
    source: "HumanFinalConfirm",
    type: "TextMessage",
    content: `Rejected with feedback:\n${feedback}`,
  });
  output.textContent = "Revising test cases...";
  setActiveStep("writer");
  setBusy(true);

  try {
    writerStreamBuffer = "";
    const data = await postStream("/api/revise/stream", {
      parsed_document_id: currentParsedDocument?.document_id,
      confirmed_content: confirmedContent,
      previous_test_cases: currentReview.draft_test_cases,
      reviewer_comments: currentReview.review,
      human_feedback: feedback,
      max_messages: 12,
    });

    currentReview = {
      ...data,
      confirmed_content: confirmedContent,
    };
    output.textContent = data.draft_test_cases || data.final_test_cases || "No draft returned.";
    feedbackInput.value = "";
    setReviewControlsVisible(true);
    setActiveStep("final-confirm");
    statusText.textContent = "Awaiting final human review";
  } catch (error) {
    appendTimelineEvent({
      event: "error",
      source: "system",
      type: "FrontendError",
      content: error.message,
    });
    statusText.textContent = "Error";
  } finally {
    setBusy(false);
  }
}

function approveFinal() {
  if (!currentReview) {
    statusText.textContent = "No draft to approve";
    return;
  }

  setReviewControlsVisible(false);
  copyButton.disabled = false;
  setActiveStep("final-confirm");
  statusText.textContent = "Approved";
  appendTimelineEvent({
    event: "message",
    source: "HumanFinalConfirm",
    type: "TextMessage",
    content: "Final test cases approved by human.",
  });
}

sampleButton.addEventListener("click", () => {
  manualInput.value = sampleRequirement;
  manualInput.focus();
});

uploadForm.addEventListener("submit", (event) => {
  event.preventDefault();
  parseSelectedFile();
});

dropZone.addEventListener("dragover", (event) => {
  event.preventDefault();
  dropZone.classList.add("is-dragging");
});

dropZone.addEventListener("dragleave", () => {
  dropZone.classList.remove("is-dragging");
});

dropZone.addEventListener("drop", (event) => {
  event.preventDefault();
  dropZone.classList.remove("is-dragging");
  if (event.dataTransfer.files.length) {
    fileInput.files = event.dataTransfer.files;
    statusText.textContent = event.dataTransfer.files[0].name;
  }
});

fileInput.addEventListener("change", () => {
  const file = fileInput.files?.[0];
  statusText.textContent = file ? file.name : "Ready";
});

parsedContentInput.addEventListener("input", () => {
  if (parseConfirmed) {
    resetParseConfirmation();
    statusText.textContent = "Parsed content changed. Confirm again";
  }
});

useManualButton.addEventListener("click", useManualText);
confirmParseButton.addEventListener("click", confirmParsedContent);
generateButton.addEventListener("click", generateReview);
rejectButton.addEventListener("click", reviseReview);
approveButton.addEventListener("click", approveFinal);

copyButton.addEventListener("click", async () => {
  await navigator.clipboard.writeText(output.textContent);
  statusText.textContent = "Copied";
  window.setTimeout(() => {
    statusText.textContent = selectedStep === "final-confirm" ? "Approved" : "Ready";
  }, 1200);
});

setActiveStep("upload");
checkHealth();
