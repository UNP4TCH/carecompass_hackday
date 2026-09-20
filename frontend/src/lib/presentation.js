// Presentation helpers only.
// Nothing in this file decides urgency or care level — the backend does.
// These helpers map values the backend already returned onto labels/colours.

export function formatFlag(flag) {
  return (flag || "")
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

// Labels for the backend `urgency` field.
export const URGENCY_LABEL = {
  emergency: "Emergency",
  prompt_medical_attention: "Prompt medical attention",
  routine_follow_up: "Routine follow-up",
  self_care_monitoring: "Self-care & monitoring",
};

// Labels for the backend `care_level` / `navigation.level` field.
export function formatCareLevel(level) {
  const labels = {
    emergency: "Emergency",
    urgent: "Urgent",
    routine: "Routine",
    self_care: "Self-care",
  };

  return labels[level] || level || "—";
}

// Presentation state for a backend `navigation.level`.
//   emergency          -> red
//   urgent             -> amber
//   routine / self_care-> green
// Any other value (including a missing navigation object) is rendered
// neutral. It is never assumed to be reassuring.
export function severityFor(level) {
  switch (level) {
    case "emergency":
      return { tone: "red", label: "Emergency", icon: "alert" };
    case "urgent":
      return { tone: "amber", label: "Urgent", icon: "clock" };
    case "routine":
      return { tone: "green", label: "Routine", icon: "check" };
    case "self_care":
      return { tone: "green", label: "Self-care", icon: "check" };
    default:
      return { tone: "neutral", label: null, icon: null };
  }
}

// Which of UNDERSTAND / ASK / ASSESS / GUIDE is active.
// Derived from state the app already tracks; no new assessment logic.
export const STAGES = ["Understand", "Ask", "Assess", "Guide"];

export function stageFor(view, { hasQuestion, progress }) {
  if (view === "result") return 3;
  if (view === "assessment") {
    if (!hasQuestion) return 0;
    return progress > 55 ? 2 : 1;
  }
  return 0;
}

// Turns the flat message list into the initial description plus
// question -> answer pairs, for the "Previous answers" record.
// Clarification replies are not questions and are skipped here.
export function buildRecord(messages) {
  const initial =
    messages[0] && messages[0].role === "user" ? messages[0].text : null;

  const pairs = [];
  let question = null;

  messages.slice(1).forEach((message) => {
    if (message.role === "assistant") {
      if (message.kind !== "clarification") question = message.text;
      return;
    }

    pairs.push({ question, answer: message.text });
  });

  return { initial, pairs };
}

export function formatAssessmentDate(dateInput) {
  const date = dateInput
    ? typeof dateInput === "string"
      ? new Date(dateInput)
      : dateInput
    : new Date();

  if (isNaN(date.getTime())) {
    return new Date().toLocaleDateString(undefined, { dateStyle: "long" });
  }

  return new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
    timeZoneName: "short",
  }).format(date);
}

