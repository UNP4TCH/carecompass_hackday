import { Refresh, Restart } from "./icons";
import { useFocusOnMount } from "../lib/useFocusOnMount";

export default function UnavailableView({ message, onReset }) {
  const headingRef = useFocusOnMount();

  return (
    <section
      className="view result tone-neutral notice"
      role="status"
      aria-labelledby="unavailable-heading"
    >
      <div className="result-bar" aria-hidden="true" />

      <div className="result-body">
        <div className="result-head">
          <p className="kicker">Service status</p>
          <span className="severity-chip">
            <Refresh width={16} height={16} />
            Unavailable
          </span>
        </div>

        <h1
          id="unavailable-heading"
          ref={headingRef}
          tabIndex={-1}
          className="result-title result-title-sm focus-target"
        >
          AI service unavailable
        </h1>

        <p className="lead">{message}</p>

        <div className="result-foot">
          <p className="fine">
            No AI-generated assessment is shown when the reasoning service is
            unavailable.
          </p>
          <button type="button" className="btn btn-quiet" onClick={onReset}>
            <Restart />
            Start over
          </button>
        </div>
      </div>
    </section>
  );
}
