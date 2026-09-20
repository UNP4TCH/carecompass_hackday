import { Check } from "./icons";
import { STAGES } from "../lib/presentation";

const STATUS_LABEL = {
  intake: "Ready",
  assessment: "Assessment in progress",
  result: "Guidance ready",
  emergency: "Safety action",
  unavailable: "Service unavailable",
  document: "Document simplifier",
};

export function SkipLink() {
  return (
    <a className="skip-link" href="#main">
      Skip to main content
    </a>
  );
}

function BrandMark() {
  return (
    <span className="brand-mark" aria-hidden="true">
      <i />
      <i />
      <b />
    </span>
  );
}

export function Header({ view, onReset, toolMode = "assessment", onSwitchMode }) {
  return (
    <header className="site-header">
      <div className="container header-inner">
        <button
          type="button"
          className="brand"
          onClick={onReset}
          aria-label="CareCompass, return to the start"
        >
          <BrandMark />
          <span className="brand-text">
            <strong>CareCompass</strong>
            <small>Care navigation</small>
          </span>
        </button>

        <nav className="header-nav" aria-label="Feature navigation">
          <button
            type="button"
            className={`header-nav-btn${toolMode === "assessment" ? " is-active" : ""}`}
            onClick={() => onSwitchMode?.("assessment")}
          >
            Symptom guidance
          </button>
          <button
            type="button"
            className={`header-nav-btn${toolMode === "document" ? " is-active" : ""}`}
            onClick={() => onSwitchMode?.("document")}
          >
            Prescription simplifier
          </button>
        </nav>

        <p className="header-status">
          <span
            className={`status-dot${view === "emergency" ? " is-alert" : ""}`}
            aria-hidden="true"
          />
          <span className="header-status-text">{STATUS_LABEL[view] || "Ready"}</span>
        </p>
      </div>
    </header>
  );
}


export function StageNav({ active }) {
  return (
    <nav className="stage-nav" aria-label="Where you are in CareCompass">
      <ol>
        {STAGES.map((stage, index) => {
          const complete = index < active;
          const current = index === active;
          const state = complete ? "complete" : current ? "current" : "upcoming";

          return (
            <li
              key={stage}
              className={`stage is-${state}`}
              aria-current={current ? "step" : undefined}
            >
              <span className="stage-bar" aria-hidden="true" />
              <span className="stage-label">
                <span className="stage-index" aria-hidden="true">
                  {complete ? <Check width={12} height={12} strokeWidth={3} /> : index + 1}
                </span>
                <span className="stage-name">{stage}</span>
                {complete && <span className="sr-only"> (completed)</span>}
                {current && <span className="sr-only"> (current step)</span>}
              </span>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}

export function Footer() {
  return (
    <footer className="site-footer">
      <div className="container footer-inner">
        <span>CareCompass · AI-powered healthcare navigation</span>
        <span>Preliminary guidance only · Not a diagnosis</span>
      </div>
    </footer>
  );
}
