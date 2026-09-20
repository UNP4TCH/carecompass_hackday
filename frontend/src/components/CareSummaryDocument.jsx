import {
  URGENCY_LABEL,
  buildRecord,
  formatAssessmentDate,
  formatCareLevel,
  formatFlag,
} from "../lib/presentation";

export default function CareSummaryDocument({
  assessment,
  emergency,
  messages = [],
  assessmentDate,
}) {
  const { initial, pairs } = buildRecord(messages);
  const isEmergency = Boolean(
    emergency ||
      assessment?.navigation?.level === "emergency" ||
      assessment?.care_level === "emergency"
  );

  const navigation = assessment?.navigation;

  // Determine standard navigation level
  let navLevel = "routine";
  if (isEmergency) {
    navLevel = "emergency";
  } else if (navigation?.level) {
    navLevel = navigation.level;
  } else if (assessment?.care_level) {
    navLevel = assessment.care_level;
  }

  // Display label for navigation level
  const navLabel = isEmergency
    ? "Emergency"
    : navigation?.label ||
      URGENCY_LABEL[assessment?.urgency] ||
      formatCareLevel(navLevel);

  // Recommended next step action
  const primaryAction = isEmergency
    ? emergency?.message ||
      navigation?.action ||
      assessment?.recommended_action ||
      "Seek immediate professional medical attention or contact your local emergency service."
    : navigation?.action || assessment?.recommended_action;

  const secondaryAction =
    !isEmergency &&
    navigation?.action &&
    assessment?.recommended_action &&
    navigation.action.trim().toLowerCase() !==
      assessment.recommended_action.trim().toLowerCase()
      ? assessment.recommended_action
      : null;

  // Timing & Setting
  const timeframe = isEmergency
    ? "Immediate / Now"
    : navigation?.timeframe || null;

  const setting = isEmergency
    ? "Emergency medical care"
    : navigation?.setting || null;

  // Escalation guidance
  const escalation = isEmergency
    ? "Do not wait for symptoms to improve before seeking emergency help. Call your local emergency service or proceed to the nearest emergency department immediately."
    : navigation?.escalation || null;

  // Safety / Warning signs
  const emergencySigns = emergency?.detected_signs || [];
  const warningSigns = assessment?.warning_signs || [];

  const formattedDate = formatAssessmentDate(assessmentDate);

  return (
    <article
      className={`care-summary-doc ${isEmergency ? "is-emergency" : ""}`}
      aria-label="Care Assessment Summary"
    >
      {/* Document Header */}
      <header className="care-summary-header">
        <div className="care-summary-brand">
          <div className="care-summary-brand-title">CareCompass</div>
          <div className="care-summary-brand-sub">
            Health Navigation &amp; Care Summary
          </div>
        </div>
        <div className="care-summary-meta">
          <div className="care-summary-meta-item">
            <span className="care-summary-meta-label">Assessment Date:</span>{" "}
            <strong>{formattedDate}</strong>
          </div>
          <div className="care-summary-meta-item">
            <span className="care-summary-meta-label">Document Purpose:</span>{" "}
            <span>Clinical Discussion Summary</span>
          </div>
        </div>
      </header>

      {/* Navigation Level & Action Callout */}
      <section className={`care-summary-level-banner level-${navLevel}`}>
        <div className="care-summary-level-tag">
          <span className="level-badge">{navLabel.toUpperCase()}</span>
          <span className="level-heading-text">
            {isEmergency
              ? "Immediate Medical Attention Required"
              : navLevel === "urgent"
              ? "Prompt Medical Evaluation Recommended"
              : "Routine Care / Scheduled Consultation"}
          </span>
        </div>

        <div className="care-summary-action-box">
          <div className="care-summary-field">
            <span className="field-title">Recommended Next Step</span>
            <p className="field-content action-emphasis">{primaryAction}</p>
            {secondaryAction && (
              <p className="field-content action-secondary">{secondaryAction}</p>
            )}
          </div>

          {(timeframe || setting) && (
            <div className="care-summary-grid">
              {timeframe && (
                <div className="care-summary-field">
                  <span className="field-title">Timeframe</span>
                  <p className="field-content">{timeframe}</p>
                </div>
              )}
              {setting && (
                <div className="care-summary-field">
                  <span className="field-title">Recommended Setting</span>
                  <p className="field-content">{setting}</p>
                </div>
              )}
            </div>
          )}

          {escalation && (
            <div className="care-summary-field escalation-block">
              <span className="field-title">Escalation Guidance</span>
              <p className="field-content">{escalation}</p>
            </div>
          )}
        </div>
      </section>

      {/* Patient Reported Symptoms */}
      <section className="care-summary-section">
        <h2 className="care-summary-section-title">
          Patient-Reported Information
        </h2>

        <div className="care-summary-field">
          <span className="field-title">Initial Description of Symptoms</span>
          <p className="field-content reported-text">
            {initial || "Initial symptoms provided during assessment intake."}
          </p>
        </div>

        {/* Assessment Questions and Answers */}
        <div className="care-summary-qa">
          <span className="field-title">
            Assessment Questions &amp; Responses
          </span>
          {pairs.length > 0 ? (
            <ol className="qa-list">
              {pairs.map((pair, idx) => (
                <li key={`${idx}-${pair.answer}`} className="qa-item">
                  <p className="qa-question">
                    <strong>Q{idx + 1}:</strong>{" "}
                    {pair.question || "Follow-up question"}
                  </p>
                  <p className="qa-answer">
                    <strong>Response:</strong> {pair.answer}
                  </p>
                </li>
              ))}
            </ol>
          ) : (
            <p className="qa-empty">
              {isEmergency
                ? "Immediate safety screening triggered prior to follow-up questions."
                : "No follow-up questions were required for this assessment."}
            </p>
          )}
        </div>
      </section>

      {/* Safety and Clinical Information */}
      {(emergencySigns.length > 0 ||
        warningSigns.length > 0 ||
        assessment?.why ||
        assessment?.summary) && (
        <section className="care-summary-section">
          <h2 className="care-summary-section-title">
            Clinical Context &amp; Safety Information
          </h2>

          {emergencySigns.length > 0 && (
            <div className="care-summary-field warning-box">
              <span className="field-title warning-title">
                Emergency Warning Signs Identified
              </span>
              <ul className="signs-list">
                {emergencySigns.map((flag) => (
                  <li key={flag} className="sign-item">
                    {formatFlag(flag)}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {warningSigns.length > 0 && (
            <div className="care-summary-field warning-box">
              <span className="field-title warning-title">
                Warning Signs to Watch For
              </span>
              <ul className="signs-list">
                {warningSigns.map((warning) => (
                  <li key={warning} className="sign-item">
                    {warning}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {assessment?.summary && (
            <div className="care-summary-field">
              <span className="field-title">Assessment Summary</span>
              <p className="field-content">{assessment.summary}</p>
            </div>
          )}

          {assessment?.why && (
            <div className="care-summary-field">
              <span className="field-title">Rationale for Guidance</span>
              <p className="field-content">{assessment.why}</p>
            </div>
          )}
        </section>
      )}

      {/* Medical Boundary Disclaimer */}
      <footer className="care-summary-footer">
        <p className="care-summary-disclaimer">
          <strong>Important Medical Notice:</strong> CareCompass provides
          health-navigation support, not a medical diagnosis. This summary
          reflects information provided during the assessment. Share this summary
          with a qualified healthcare professional for medical evaluation.
        </p>
      </footer>
    </article>
  );
}
