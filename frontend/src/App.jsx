import { useMemo, useState } from "react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const EXAMPLES = [
  "I have had a headache since yesterday and it gets worse when I move.",
  "I have a sore throat and fever that started two days ago.",
  "I've been feeling tired for about a week and I'm not sleeping well.",
];

function App() {
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

  const urgencyLabel = {
    emergency: "Emergency",
    prompt_medical_attention: "Prompt medical attention",
    routine_follow_up: "Routine follow-up",
    self_care_monitoring: "Self-care & monitoring",
  };

  function formatCareLevel(level) {
    const labels = {
      emergency: "Emergency",
      urgent: "Urgent",
      routine: "Routine",
      self_care: "Self-care",
    };

    return labels[level] || level || "—";
  }

  function formatFlag(flag) {
    return (flag || "")
      .replaceAll("_", " ")
      .replace(/\b\w/g, (letter) => letter.toUpperCase());
  }

  return (
    <div className="app-shell">

      {/* =========================================================
          TOP BAR
          ========================================================= */}

      <header className="topbar">
        <div
          className="brand"
          onClick={resetAssessment}
          role="button"
          tabIndex={0}
        >
          <div className="compass-mark">
            <span>+</span>
          </div>

          <div>
            <strong>CareCompass</strong>
            <small>
              Healthcare navigation
            </small>
          </div>
        </div>

        <div className="top-status">
          <span className="status-dot" />
          Safety-aware AI
        </div>
      </header>


      {/* =========================================================
          MAIN
          ========================================================= */}

      <main className="main">

        {/* =======================================================
            LANDING / INTAKE
            ======================================================= */}

        {!inAssessment &&
          !emergency &&
          !aiUnavailable && (
            <section className="hero">

              <div className="eyebrow-pill">
                FIRST-STEP HEALTH GUIDANCE
              </div>

              <h1>
                Know what to do{" "}
                <em>next.</em>
              </h1>

              <p className="hero-copy">
                Describe what you're experiencing.
                CareCompass asks relevant follow-up
                questions, checks for safety-critical
                warning signs, and helps you navigate
                an appropriate next step.
              </p>

              <div className="intake-card">

                <textarea
                  value={symptoms}
                  onChange={(e) =>
                    setSymptoms(e.target.value)
                  }
                  placeholder="Tell me what you're experiencing in your own words…"
                  rows={6}
                  maxLength={5000}
                />

                <div className="intake-footer">
                  <span>
                    {symptoms.length}/5000 · Avoid
                    names, addresses, or other
                    unnecessary personal details.
                  </span>

                  <button
                    className="primary"
                    onClick={() =>
                      startAssessment()
                    }
                    disabled={
                      loading ||
                      !symptoms.trim()
                    }
                  >
                    {loading
                      ? "Starting…"
                      : "Begin assessment →"}
                  </button>
                </div>

              </div>

              <div className="examples">
                <span>
                  Try an example
                </span>

                {EXAMPLES.map((example) => (
                  <button
                    key={example}
                    onClick={() =>
                      setSymptoms(example)
                    }
                  >
                    {example}
                  </button>
                ))}
              </div>

              <div className="trust-row">
                <div>
                  <b>01</b>
                  <span>Understand</span>
                </div>

                <div>
                  <b>02</b>
                  <span>Ask</span>
                </div>

                <div>
                  <b>03</b>
                  <span>Assess</span>
                </div>

                <div>
                  <b>04</b>
                  <span>Guide</span>
                </div>
              </div>

            </section>
          )}


        {/* =======================================================
            ASSESSMENT WORKSPACE
            ======================================================= */}

        {(inAssessment ||
          emergency ||
          aiUnavailable) && (
          <section className="workspace">

            <div className="workspace-head">

              <div>
                <span className="eyebrow">
                  CARECOMPASS ASSESSMENT
                </span>

                <h2>
                  {emergency
                    ? "Safety check triggered"
                    : completed
                    ? "Your guidance is ready"
                    : "Let's understand the situation"}
                </h2>
              </div>

              <button
                className="ghost"
                onClick={resetAssessment}
              >
                Start over
              </button>

            </div>


            {/* =================================================
                PROGRESS
                ================================================= */}

            {!emergency &&
              !aiUnavailable &&
              !completed && (
                <div className="progress-wrap">

                  <div className="progress-label">
                    <span>
                      Assessment progress
                    </span>

                    <span>
                      {Math.round(progress)}%
                    </span>
                  </div>

                  <div className="progress">
                    <div
                      style={{
                        width: `${progress}%`,
                      }}
                    />
                  </div>

                </div>
              )}


            {/* =================================================
                EMERGENCY
                ================================================= */}

            {emergency && (
              <div className="emergency-card">

                <div className="danger-icon">
                  !
                </div>

                <div>

                  <span className="danger-kicker">
                    SAFETY FIRST
                  </span>

                  <h3>
                    Potential emergency
                    warning signs detected.
                  </h3>

                  <p>
                    {emergency.message}
                  </p>

                  {emergency.detected_signs?.length >
                    0 && (
                    <div className="flag-list">

                      {emergency.detected_signs.map(
                        (flag) => (
                          <span key={flag}>
                            {formatFlag(flag)}
                          </span>
                        )
                      )}

                    </div>
                  )}

                  <p className="fine-print">
                    CareCompass is not an
                    emergency service and cannot
                    diagnose a condition.
                  </p>

                </div>

              </div>
            )}


            {/* =================================================
                AI UNAVAILABLE
                ================================================= */}

            {aiUnavailable && (
              <div className="notice-card">

                <div className="notice-icon">
                  ↻
                </div>

                <div>

                  <h3>
                    AI service unavailable
                  </h3>

                  <p>
                    {aiUnavailable}
                  </p>

                  <p className="fine-print">
                    No AI-generated assessment is
                    shown when the reasoning
                    service is unavailable.
                  </p>

                </div>

              </div>
            )}


            {/* =================================================
                CONVERSATION
                ================================================= */}

            {inAssessment &&
              !emergency &&
              !aiUnavailable && (
                <div className="conversation-layout">

                  <div className="chat-card">

                    <div className="chat-head">
                      <span className="live-dot" />
                      Live assessment
                    </div>

                    <div className="messages">

                      {messages.map(
                        (message, index) => (
                          <div
                            key={index}
                            className={`message-row ${message.role}`}
                          >

                            {message.role ===
                              "assistant" && (
                              <div className="mini-mark">
                                +
                              </div>
                            )}

                            <div className="bubble">
                              {message.text}
                            </div>

                          </div>
                        )
                      )}

                      {loading && (
                        <div className="message-row assistant">

                          <div className="mini-mark">
                            +
                          </div>

                          <div className="bubble thinking">
                            <i />
                            <i />
                            <i />
                          </div>

                        </div>
                      )}

                    </div>

                    {currentQuestion &&
                      !completed && (
                        <form
                          className="answer-form"
                          onSubmit={
                            handleAnswerSubmit
                          }
                        >

                          <input
                            name="answer"
                            placeholder="Type your answer…"
                            autoComplete="off"
                            disabled={loading}
                          />

                          <button
                            className="primary"
                            disabled={loading}
                          >
                            Send
                          </button>

                        </form>
                      )}

                  </div>


                  <aside className="side-card">

                    <div className="side-icon">
                      🧭
                    </div>

                    <h3>
                      Navigation, not diagnosis.
                    </h3>

                    <p>
                      CareCompass gathers context,
                      checks safety signals, and
                      helps identify an appropriate
                      care level.
                    </p>

                    <div className="side-rule" />

                    <span className="small-label">
                      SAFETY LAYER
                    </span>

                    <strong>
                      Deterministic red-flag
                      screening
                    </strong>

                    <p className="muted">
                      The safety layer is
                      independent of the AI
                      reasoning layer.
                    </p>

                  </aside>

                </div>
              )}


            {/* =================================================
                FINAL RESULTS
                ================================================= */}

            {completed &&
              finalAssessment && (
                <section className="results-card">

                  <div className="results-top">

                    <div>
                      <span className="eyebrow">
                        PRELIMINARY GUIDANCE
                      </span>

                      <h3>
                        What CareCompass found
                      </h3>
                    </div>

                    <span
                      className={`urgency ${finalAssessment.urgency}`}
                    >
                      {urgencyLabel[
                        finalAssessment.urgency
                      ] ||
                        finalAssessment.urgency}
                    </span>

                  </div>


                  <div className="result-grid">

                    {/* =========================================
                        MAIN RESULT
                        ========================================= */}

                    <div className="result-main">

                      <div className="result-block">
                        <span>
                          WHAT WE UNDERSTOOD
                        </span>

                        <p>
                          {finalAssessment.summary}
                        </p>
                      </div>


                      <div className="action-box">
                        <span>
                          RECOMMENDED NEXT STEP
                        </span>

                        <p>
                          {
                            finalAssessment.recommended_action
                          }
                        </p>
                      </div>


                      <div className="result-block">
                        <span>
                          WHY
                        </span>

                        <p>
                          {finalAssessment.why}
                        </p>
                      </div>

                    </div>


                    {/* =========================================
                        CARE NAVIGATION
                        ========================================= */}

                    <div className="result-side">

                      {finalAssessment.navigation && (
                        <div
                          className={`navigation-box navigation-${finalAssessment.navigation.level}`}
                        >

                          <span className="navigation-kicker">
                            YOUR NEXT STEP
                          </span>

                          <strong className="navigation-title">
                            {
                              finalAssessment
                                .navigation
                                .label
                            }
                          </strong>


                          <div className="navigation-detail">
                            <span>
                              WHEN
                            </span>

                            <p>
                              {
                                finalAssessment
                                  .navigation
                                  .timeframe
                              }
                            </p>
                          </div>


                          <div className="navigation-detail">
                            <span>
                              WHERE
                            </span>

                            <p>
                              {
                                finalAssessment
                                  .navigation
                                  .setting
                              }
                            </p>
                          </div>


                          <div className="navigation-action">
                            <span>
                              WHAT TO DO
                            </span>

                            <p>
                              {
                                finalAssessment
                                  .navigation
                                  .action
                              }
                            </p>
                          </div>


                          <div className="navigation-escalation">
                            <span>
                              WHEN TO ESCALATE
                            </span>

                            <p>
                              {
                                finalAssessment
                                  .navigation
                                  .escalation
                              }
                            </p>
                          </div>

                        </div>
                      )}


                      {/* =======================================
                          CARE LEVEL
                          ======================================= */}

                      <div className="care-level">

                        <span>
                          CARE LEVEL
                        </span>

                        <strong>
                          {formatCareLevel(finalAssessment.care_level)}
                        </strong>

                      </div>


                      {/* =======================================
                          WARNING SIGNS
                          ======================================= */}

                      {finalAssessment.warning_signs
                        ?.length > 0 && (
                        <div className="warnings">

                          <span>
                            WATCH FOR
                          </span>

                          <ul>
                            {finalAssessment.warning_signs.map(
                              (warning) => (
                                <li key={warning}>
                                  {warning}
                                </li>
                              )
                            )}
                          </ul>

                        </div>
                      )}

                    </div>

                  </div>


                  {/* ===========================================
                      DISCLAIMER
                      =========================================== */}

                  <div className="disclaimer">

                    <strong>
                      Important
                    </strong>

                    <p>
                      {finalAssessment.disclaimer}
                    </p>

                  </div>


                  <button
                    className="primary wide"
                    onClick={resetAssessment}
                  >
                    Start a new assessment
                  </button>

                </section>
              )}


            {/* =================================================
                GENERAL ERROR
                ================================================= */}

            {error && (
              <div className="error-banner">
                {error}
              </div>
            )}

          </section>
        )}

      </main>


      {/* =========================================================
          FOOTER
          ========================================================= */}

      <footer className="footer">

        <span>
          CareCompass · AI-powered healthcare
          navigation
        </span>

        <span>
          Preliminary guidance only · Not a diagnosis
        </span>

      </footer>

    </div>
  );
}

export default App;