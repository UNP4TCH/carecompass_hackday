import { useEffect, useRef } from "react";
import { ArrowRight, Restart } from "./icons";
import { buildRecord } from "../lib/presentation";
import { useFocusOnMount } from "../lib/useFocusOnMount";

function ProgressPanel({ progress, turnCount, maxTurns }) {
  const current = Math.min(turnCount + 1, maxTurns);
  const remaining = Math.max(maxTurns - turnCount, 0);
  const percent = Math.round(progress);

  return (
    <section className="rail-block" aria-labelledby="progress-heading">
      <h2 id="progress-heading" className="rail-heading">
        Assessment progress
      </h2>

      <p className="rail-count">
        <strong>Question {current}</strong>
        <span>of up to {maxTurns}</span>
      </p>

      <div
        className="meter"
        role="progressbar"
        aria-labelledby="progress-heading"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={percent}
      >
        <div className="meter-fill" style={{ width: `${progress}%` }} />
      </div>

      <p className="rail-meta">
        <span>
          {remaining === 0
            ? "Finalizing guidance"
            : `Up to ${remaining} question${remaining === 1 ? "" : "s"} remain`}
        </span>
        <span aria-hidden="true">{percent}%</span>
      </p>
    </section>
  );
}

function RecordPanel({ messages }) {
  const { initial, pairs } = buildRecord(messages);

  if (!initial) return null;

  return (
    <details className="rail-block record" open>
      <summary>Previous answers</summary>

      <div className="record-initial">
        <span className="record-label">What you first described</span>
        <p>{initial}</p>
      </div>

      {pairs.length > 0 && (
        <ol className="record-list">
          {pairs.map((pair, index) => (
            <li key={`${index}-${pair.answer}`}>
              {pair.question && <span className="record-q">{pair.question}</span>}
              <span className="record-a">{pair.answer}</span>
            </li>
          ))}
        </ol>
      )}
    </details>
  );
}

export default function AssessmentView({
  currentQuestion,
  loading,
  messages,
  progress,
  turnCount,
  maxTurns,
  error,
  onSubmit,
  onReset,
}) {
  const headingRef = useFocusOnMount();
  const answerRef = useRef(null);

  const question = currentQuestion?.question;
  const last = messages[messages.length - 1];
  const clarification =
    last && last.role === "assistant" && last.kind === "clarification"
      ? last.text
      : null;

  const stuck = !currentQuestion && !loading;

  // Return the cursor to the answer box whenever a new question is ready
  // (skipped on touch devices, where it would open the keyboard and cover
  // the question).
  useEffect(() => {
    if (!question || loading) return;
    if (window.matchMedia?.("(pointer: coarse)").matches) return;
    answerRef.current?.focus();
  }, [question, loading]);

  function handleKeyDown(event) {
    if (
      event.key === "Enter" &&
      !event.shiftKey &&
      !event.nativeEvent.isComposing
    ) {
      event.preventDefault();
      event.currentTarget.form?.requestSubmit();
    }
  }

  return (
    <section className="view assessment">
      <div className="assessment-grid">
        <div className="assessment-main">
          <div className="view-topline">
            <p className="kicker">Assessment</p>
            {!stuck && (
              <button type="button" className="btn btn-text" onClick={onReset}>
                <Restart width={16} height={16} />
                Start over
              </button>
            )}
          </div>

          {clarification && (
            <div className="clarification" role="note">
              <strong>CareCompass</strong>
              <p>{clarification}</p>
            </div>
          )}

          <div aria-live="polite" aria-atomic="true">
            <h1
              id="question-heading"
              ref={headingRef}
              tabIndex={-1}
              className="question focus-target"
            >
              {question ||
                (stuck
                  ? "We couldn’t continue this assessment."
                  : "Reviewing what you shared…")}
            </h1>
          </div>

          {stuck ? (
            <div className="stuck">
              <div className="error-banner" role="alert">
                {error ||
                  "Something went wrong. You can start over and try again."}
              </div>
              <button type="button" className="btn btn-primary" onClick={onReset}>
                <Restart />
                Start over
              </button>
            </div>
          ) : (
            <form className="answer-form" onSubmit={onSubmit}>
              {error && (
                <div className="error-banner form-error" role="alert">
                  {error}
                </div>
              )}

              <label id="answer-label" htmlFor="answer" className="field-label">
                Your answer
              </label>

              <textarea
                id="answer"
                name="answer"
                ref={answerRef}
                className="field"
                rows={4}
                maxLength={3000}
                autoComplete="off"
                placeholder="Answer in your own words"
                disabled={loading || !currentQuestion}
                aria-describedby="question-heading answer-hint"
                onKeyDown={handleKeyDown}
              />

              <div className="answer-actions">
                <p id="answer-hint" className="fine">
                  Press Enter to continue. Shift + Enter adds a new line.
                </p>

                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={loading || !currentQuestion}
                >
                  {loading ? "Reviewing…" : "Continue"}
                  {!loading && <ArrowRight />}
                </button>
              </div>

              {loading && (
                <div
                  className="thinking"
                  role="status"
                  aria-label="Reviewing your answer"
                >
                  <span />
                </div>
              )}
            </form>
          )}

          {currentQuestion?.why && (
            <div className="why-note">
              <strong>Why this matters</strong>
              <p>{currentQuestion.why}</p>
            </div>
          )}
        </div>

        <aside className="rail" aria-label="Progress and record">
          <ProgressPanel
            progress={progress}
            turnCount={turnCount}
            maxTurns={maxTurns}
          />

          <RecordPanel messages={messages} />

          <section className="rail-block rail-note" aria-labelledby="about-heading">
            <h2 id="about-heading" className="rail-heading">
              Navigation, not diagnosis
            </h2>
            <p>
              CareCompass gathers context, checks safety signals, and helps
              identify an appropriate care level.
            </p>
            <p>
              <strong>Deterministic red-flag screening.</strong> The safety
              layer is independent of the AI reasoning layer.
            </p>
          </section>
        </aside>
      </div>
    </section>
  );
}
