import { useMemo, useState } from "react";

import { Footer, Header, SkipLink, StageNav } from "./components/Chrome";
import IntakeView from "./components/IntakeView";
import AssessmentView from "./components/AssessmentView";
import EmergencyView from "./components/EmergencyView";
import UnavailableView from "./components/UnavailableView";
import ResultView from "./components/ResultView";
import DocumentSimplifierView from "./components/DocumentSimplifierView";
import { stageFor } from "./lib/presentation";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const EXAMPLES = [
  {
    label: "Headache that worsens with movement",
    text: "I have had a headache since yesterday and it gets worse when I move.",
  },
  {
    label: "Sore throat and fever",
    text: "I have a sore throat and fever that started two days ago.",
  },
  {
    label: "Tired for a week, sleeping poorly",
    text: "I've been feeling tired for about a week and I'm not sleeping well.",
  },
];

function App() {
  const [toolMode, setToolMode] = useState("assessment");
  const [symptoms, setSymptoms] = useState("");
  const [messages, setMessages] = useState([]);
  const [conversationId, setConversationId] = useState(null);
  const [currentQuestion, setCurrentQuestion] = useState(null);
  const [loading, setLoading] = useState(false);
  const [completed, setCompleted] = useState(false);
  const [finalAssessment, setFinalAssessment] = useState(null);
  const [emergency, setEmergency] = useState(null);
  const [error, setError] = useState(null);
  const [aiUnavailable, setAiUnavailable] = useState(null);
  const [turnCount, setTurnCount] = useState(0);
  const [maxTurns, setMaxTurns] = useState(7);
  const [assessmentDate, setAssessmentDate] = useState(null);

  const inAssessment = messages.length > 0;

  const progress = useMemo(() => {
    if (completed) return 100;
    if (!inAssessment) return 0;
    return Math.min(
      92,
      18 + (turnCount / Math.max(maxTurns, 1)) * 74
    );
  }, [completed, inAssessment, turnCount, maxTurns]);

  function resetAssessment() {
    setSymptoms("");
    setMessages([]);
    setConversationId(null);
    setCurrentQuestion(null);
    setLoading(false);
    setCompleted(false);
    setFinalAssessment(null);
    setEmergency(null);
    setError(null);
    setAiUnavailable(null);
    setTurnCount(0);
    setMaxTurns(7);
    setAssessmentDate(null);
    setToolMode("assessment");
  }

  async function startAssessment(text = symptoms) {
    const value = text.trim();

    if (!value || loading) return;

    setSymptoms(value);
    setLoading(true);
    setError(null);
    setAiUnavailable(null);
    setEmergency(null);
    setCompleted(false);
    setFinalAssessment(null);
    setAssessmentDate(new Date().toISOString());
    setMessages([{ role: "user", text: value }]);

    try {
      const response = await fetch(
        `${API_URL}/api/conversation/start`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            symptoms: value,
          }),
        }
      );

      const data = await response.json();

      setConversationId(
        data.conversation_id || null
      );

      setTurnCount(
        data.turn_count || 0
      );

      setMaxTurns(
        data.max_turns || 7
      );

      if (data.status === "emergency") {
        setEmergency(data.triage);
        setCurrentQuestion(null);
        return;
      }

      if (data.status === "ai_unavailable") {
        setAiUnavailable(data.message);
        setCurrentQuestion(null);
        return;
      }

      if (data.status === "validation_error") {
        setError(data.message);
        return;
      }

      if (data.next_question) {
        setCurrentQuestion(
          data.next_question
        );

        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            text: data.next_question.question,
          },
        ]);

        setSymptoms("");
        return;
      }

      if (data.final_assessment) {
        setFinalAssessment(
          data.final_assessment
        );

        setCompleted(true);
      }
    } catch (err) {
      console.error(err);

      setError(
        "Unable to connect to CareCompass. Make sure the backend is running on port 8000."
      );
    } finally {
      setLoading(false);
    }
  }

  async function submitAnswer(answer) {
    const value = answer.trim();

    if (!value || loading || !conversationId) {
      return;
    }

    setLoading(true);
    setError(null);
    setAiUnavailable(null);

    setMessages((prev) => [
      ...prev,
      {
        role: "user",
        text: value,
      },
    ]);

    try {
      const response = await fetch(
        `${API_URL}/api/conversation/answer`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            conversation_id: conversationId,
            answer: value,
          }),
        }
      );

      const data = await response.json();

      setTurnCount(
        data.turn_count || turnCount
      );

      setMaxTurns(
        data.max_turns || maxTurns
      );

      if (data.status === "emergency") {
        setEmergency(data.triage);
        setCurrentQuestion(null);
        return;
      }

      if (data.status === "ai_unavailable") {
        setAiUnavailable(data.message);
        setCurrentQuestion(null);
        return;
      }

      if (data.status === "question_clarification") {
        if (data.assistant_message) {
          setMessages((prev) => [
            ...prev,
            {
              role: "assistant",
              kind: "clarification",
              text: data.assistant_message,
            },
          ]);
        }

        setCurrentQuestion(
          data.next_question || currentQuestion
        );

        return;
      }

      if (data.next_question) {
        setCurrentQuestion(
          data.next_question
        );

        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            text: data.next_question.question,
          },
        ]);

        return;
      }

      if (data.final_assessment) {
        setCurrentQuestion(null);

        setFinalAssessment(
          data.final_assessment
        );

        setCompleted(true);
      }
    } catch (err) {
      console.error(err);

      setError(
        "Unable to process that response. Please check the backend and try again."
      );
    } finally {
      setLoading(false);
    }
  }

  function handleAnswerSubmit(event) {
    event.preventDefault();

    const form = event.currentTarget;
    const value = form.elements.answer.value;

    if (!value.trim()) return;

    form.reset();
    submitAnswer(value);
  }

  // ---- presentation only: which screen to show, from existing state ----
  const view = emergency
    ? "emergency"
    : aiUnavailable
    ? "unavailable"
    : completed && finalAssessment
    ? "result"
    : inAssessment
    ? "assessment"
    : "intake";

  const activeStage = stageFor(view, {
    hasQuestion: Boolean(currentQuestion),
    progress,
  });

  const showStages =
    toolMode === "assessment" &&
    (view === "intake" || view === "assessment" || view === "result");

  const headerView = toolMode === "document" ? "document" : view;

  return (
    <div className="app-shell">
      <SkipLink />

      <Header
        view={headerView}
        onReset={resetAssessment}
        toolMode={toolMode}
        onSwitchMode={setToolMode}
      />

      <main id="main" className="main" tabIndex={-1}>
        <div className="container">
          {toolMode === "document" ? (
            <DocumentSimplifierView
              onBackToAssessment={() => setToolMode("assessment")}
            />
          ) : (
            <>
              {showStages && <StageNav active={activeStage} />}

              {view === "intake" && (
                <IntakeView
                  symptoms={symptoms}
                  onSymptomsChange={setSymptoms}
                  loading={loading}
                  onStart={startAssessment}
                  examples={EXAMPLES}
                  onOpenDocumentSimplifier={() => setToolMode("document")}
                />
              )}

              {view === "assessment" && (
                <AssessmentView
                  currentQuestion={currentQuestion}
                  loading={loading}
                  messages={messages}
                  progress={progress}
                  turnCount={turnCount}
                  maxTurns={maxTurns}
                  error={error}
                  onSubmit={handleAnswerSubmit}
                  onReset={resetAssessment}
                />
              )}

              {view === "emergency" && (
                <EmergencyView
                  emergency={emergency}
                  messages={messages}
                  assessmentDate={assessmentDate}
                  onReset={resetAssessment}
                />
              )}

              {view === "unavailable" && (
                <UnavailableView
                  message={aiUnavailable}
                  onReset={resetAssessment}
                />
              )}

              {view === "result" && (
                <ResultView
                  assessment={finalAssessment}
                  messages={messages}
                  assessmentDate={assessmentDate}
                  onReset={resetAssessment}
                />
              )}

              {error && view !== "assessment" && (
                <div className="error-banner" role="alert">
                  {error}
                </div>
              )}
            </>
          )}
        </div>
      </main>

      <Footer />
    </div>
  );

}

export default App;
