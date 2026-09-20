import FindNearestCare from "./FindNearestCare";
import { Alert, FileText, Restart } from "./icons";
import CareSummaryDocument from "./CareSummaryDocument";
import { formatFlag } from "../lib/presentation";
import { useFocusOnMount } from "../lib/useFocusOnMount";

// Presentation of the backend emergency payload (`triage`).
// The message, detected signs and recommended action come from the
// deterministic safety engine and are shown exactly as received.
export default function EmergencyView({
  emergency,
  messages,
  assessmentDate,
  onReset,
}) {
  const headingRef = useFocusOnMount();
  const signs = emergency?.detected_signs || [];

  function handleDownloadSummary() {
    window.print();
  }

  return (
    <section
      className="view result tone-red"
      role="alert"
      aria-labelledby="emergency-heading"
    >
      <div className="result-bar" aria-hidden="true" />

      <div className="result-body">
        <div className="result-head">
          <p className="kicker kicker-tone">Your next step</p>
          <span className="severity-chip">
            <Alert width={16} height={16} />
            Emergency
          </span>
        </div>

        <h1
          id="emergency-heading"
          ref={headingRef}
          tabIndex={-1}
          className="result-title focus-target"
        >
          Potential emergency warning signs detected.
        </h1>

        <p className="lead lead-strong">{emergency?.message}</p>

        <div className="emergency-signs">
          <h2 className="section-label tone-text">Warning signs identified</h2>

          {signs.length > 0 ? (
            <ul>
              {signs.map((flag) => (
                <li key={flag}>{formatFlag(flag)}</li>
              ))}
            </ul>
          ) : (
            <p className="muted">
              Safety screening indicated a potential emergency.
            </p>
          )}
        </div>

        <FindNearestCare />

        <div className="result-foot">
          <p className="fine">
            CareCompass is not an emergency service and cannot diagnose a
            condition.
          </p>
          <div className="result-actions">
            <button
              type="button"
              className="btn btn-primary download-summary-btn"
              onClick={handleDownloadSummary}
              aria-label="Download Care Summary"
            >
              <FileText width={18} height={18} />
              Download Care Summary
            </button>
            <button type="button" className="btn btn-quiet" onClick={onReset}>
              <Restart />
              Start over
            </button>
          </div>
        </div>
      </div>

      <CareSummaryDocument
        emergency={emergency}
        messages={messages}
        assessmentDate={assessmentDate}
      />
    </section>
  );
}
