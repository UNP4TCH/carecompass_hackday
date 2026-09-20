import { ArrowRight, FileText } from "./icons";

export default function IntakeView({
  symptoms,
  onSymptomsChange,
  loading,
  onStart,
  examples,
  onOpenDocumentSimplifier,
}) {
  return (
    <section className="view intake" aria-labelledby="symptoms-label">
      <div className="intake-main">
        <p className="kicker">Tell us what’s happening</p>

        <div className="intake-title-row">
          <label id="symptoms-label" htmlFor="symptoms" className="intake-title">
            What are you experiencing?
          </label>
          <span className="char-count" aria-hidden="true">
            {symptoms.length} / 5000
          </span>
        </div>

        <textarea
          id="symptoms"
          className="field field-large"
          value={symptoms}
          onChange={(event) => onSymptomsChange(event.target.value)}
          placeholder="Describe what you’re noticing, when it started, and what has changed…"
          rows={8}
          maxLength={5000}
          aria-describedby="symptoms-help symptoms-privacy"
        />

        <div className="intake-actions">
          <p id="symptoms-help" className="reassure">
            <strong>You don’t need to know what’s wrong.</strong>
            Tell us what’s happening.
          </p>

          <button
            type="button"
            className="btn btn-primary"
            onClick={() => onStart()}
            disabled={loading || !symptoms.trim()}
          >
            {loading ? "Starting…" : "Begin assessment"}
            {!loading && <ArrowRight />}
          </button>
        </div>

        <p id="symptoms-privacy" className="fine">
          Avoid names, addresses, or other unnecessary personal details.
        </p>
      </div>

      <aside className="intake-side" aria-labelledby="examples-heading">
        {onOpenDocumentSimplifier && (
          <div className="intake-doc-card">
            <div className="doc-card-head">
              <FileText width={20} height={20} />
              <h2 className="doc-card-title">Have a prescription?</h2>
            </div>
            <p className="doc-card-desc">
              Upload a prescription or discharge note to translate written medication instructions into plain language.
            </p>
            <button
              type="button"
              className="btn btn-quiet doc-card-btn"
              onClick={onOpenDocumentSimplifier}
            >
              Simplify prescription
              <ArrowRight width={14} height={14} />
            </button>
          </div>
        )}

        <h2 id="examples-heading">Need a starting point?</h2>
        <p>Choose one to place it in the description, then edit it.</p>

        <ul className="example-list">
          {examples.map((example) => (
            <li key={example.text}>
              <button
                type="button"
                className="example"
                onClick={() => onSymptomsChange(example.text)}
              >
                <span>{example.label}</span>
                <ArrowRight width={16} height={16} />
              </button>
            </li>
          ))}
        </ul>
      </aside>
    </section>
  );
}

