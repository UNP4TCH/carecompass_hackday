import FindNearestCare from "./FindNearestCare";
import { FileText, Restart, SeverityIcon } from "./icons";
import CareSummaryDocument from "./CareSummaryDocument";
import {
  URGENCY_LABEL,
  formatCareLevel,
  severityFor,
} from "../lib/presentation";
import { useFocusOnMount } from "../lib/useFocusOnMount";

function Row({ label, emphasis = false, tone = false, children }) {
  return (
    <div className="row">
      <dt className={tone ? "tone-text" : undefined}>{label}</dt>
      <dd className={emphasis ? "row-emphasis" : undefined}>{children}</dd>
    </div>
  );
}

const same = (a, b) =>
  (a || "").trim().toLowerCase() === (b || "").trim().toLowerCase();

// Presents the backend final assessment. Severity colour comes ONLY from
// `navigation.level`; the frontend never derives urgency itself.
export default function ResultView({
  assessment,
  messages,
  assessmentDate,
  onReset,
}) {
  const headingRef = useFocusOnMount();

  function handleDownloadSummary() {
    window.print();
  }

  const navigation = assessment.navigation;
  const severity = severityFor(navigation?.level);

  const headline =
    navigation?.label ||
    URGENCY_LABEL[assessment.urgency] ||
    formatCareLevel(assessment.care_level);

  // "What to do": the level-mapped action first, then the situation-
  // specific recommendation when it says something different.
  const primaryAction = navigation?.action || assessment.recommended_action;
  const secondaryAction =
    navigation?.action &&
    assessment.recommended_action &&
    !same(navigation.action, assessment.recommended_action)
      ? assessment.recommended_action
      : null;

  const warnings = assessment.warning_signs || [];

  return (
    <section
      className={`view result tone-${severity.tone}`}
      aria-labelledby="result-heading"
    >
      <div className="result-bar" aria-hidden="true" />

      <div className="result-body">
        <div className="result-head">
          <p className="kicker kicker-tone">Your next step</p>

          {severity.label && (
            <span className="severity-chip">
              <SeverityIcon name={severity.icon} width={16} height={16} />
              {severity.label}
            </span>
          )}
        </div>

        <h1
          id="result-heading"
          ref={headingRef}
          tabIndex={-1}
          className="result-title focus-target"
        >
          {headline}
        </h1>

        {assessment.summary && <p className="lead">{assessment.summary}</p>}

        <dl className="rows">
          {primaryAction && (
            <Row label="What to do" emphasis>
              <p>{primaryAction}</p>
              {secondaryAction && (
                <p className="row-secondary">{secondaryAction}</p>
              )}
            </Row>
          )}

          {navigation?.timeframe && (
            <Row label="When">
              <p>{navigation.timeframe}</p>
            </Row>
          )}

          {navigation?.setting && (
            <Row label="Where">
              <p>{navigation.setting}</p>
            </Row>
          )}

          {navigation?.escalation && (
            <Row label="Escalation" tone>
              <p>{navigation.escalation}</p>
            </Row>
          )}
        </dl>

        <div className="result-detail">
          {(assessment.why || assessment.urgency || assessment.care_level) && (
            <section>
              <h2 className="section-label">Why this guidance</h2>
              {assessment.why && <p>{assessment.why}</p>}

              <p className="care-meta">
                {assessment.urgency && (
                  <span>
                    Urgency:{" "}
                    <strong>
                      {URGENCY_LABEL[assessment.urgency] || assessment.urgency}
                    </strong>
                  </span>
                )}
                {assessment.care_level && (
                  <span>
                    Care level:{" "}
                    <strong>{formatCareLevel(assessment.care_level)}</strong>
                  </span>
                )}
              </p>
            </section>
          )}

          {warnings.length > 0 && (
            <section>
              <h2 className="section-label tone-text">Watch for</h2>
              <ul className="watch-list">
                {warnings.map((warning) => (
                  <li key={warning}>{warning}</li>
                ))}
              </ul>
            </section>
          )}
        </div>

        <FindNearestCare />

        <div className="result-foot">
          <div className="disclaimer">
            <strong>Important</strong>
            <p>{assessment.disclaimer}</p>
          </div>

          <div className="result-actions">
            <button
              type="button"
              className="btn btn-quiet download-summary-btn"
              onClick={handleDownloadSummary}
              aria-label="Download Care Summary"
            >
              <FileText width={18} height={18} />
              Download Care Summary
            </button>

            <button type="button" className="btn btn-primary" onClick={onReset}>
              <Restart />
              Start a new assessment
            </button>
          </div>
        </div>
      </div>

      <CareSummaryDocument
        assessment={assessment}
        messages={messages}
        assessmentDate={assessmentDate}
      />
    </section>
  );
}
