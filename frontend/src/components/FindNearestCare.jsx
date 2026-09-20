import { useEffect, useRef, useState } from "react";
import { MapPin, Refresh } from "./icons";
import {
  GEOLOCATION_OPTIONS,
  REQUEST_WATCHDOG_MS,
  buildMapsUrl,
  describeLocationIssue,
  issueKindFromError,
} from "../lib/nearestCare";

// Explicit, one-shot "find care near me" action.
//
// Flow: person presses the button -> browser asks for location -> we open a
// Google Maps search around that point in a new tab. There is no tracking
// (no watchPosition), no backend call and nothing is written to storage.
// The Maps URL is held in component state only so a fallback link can be
// shown if the browser blocks the new tab; it disappears with the view.
export default function FindNearestCare() {
  const [status, setStatus] = useState("idle"); // idle | locating | opened | error
  const [issue, setIssue] = useState(null);
  const [mapsUrl, setMapsUrl] = useState(null);
  const [blocked, setBlocked] = useState(false);

  // Ignore a late browser callback if the person has already left the
  // result screen (e.g. started a new assessment) or asked again.
  const requestId = useRef(0);
  const watchdog = useRef(null);
  useEffect(
    () => () => {
      requestId.current += 1;
      clearTimeout(watchdog.current);
    },
    [],
  );

  const locating = status === "locating";
  const failed = status === "error";

  const fail = (kind) => {
    clearTimeout(watchdog.current);
    setIssue(describeLocationIssue(kind));
    setMapsUrl(null);
    setStatus("error");
  };

  const findCare = () => {
    if (locating) return;

    if (typeof navigator === "undefined" || !("geolocation" in navigator)) {
      fail("unsupported");
      return;
    }
    if (typeof window !== "undefined" && window.isSecureContext === false) {
      fail("insecure");
      return;
    }

    const id = ++requestId.current;
    setIssue(null);
    setMapsUrl(null);
    setBlocked(false);
    setStatus("locating");

    clearTimeout(watchdog.current);
    watchdog.current = setTimeout(() => {
      if (id !== requestId.current) return;
      requestId.current += 1; // drop any late answer from the browser
      fail("timeout");
    }, REQUEST_WATCHDOG_MS);

    try {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          if (id !== requestId.current) return;
          clearTimeout(watchdog.current);

          const url = buildMapsUrl(
            position?.coords?.latitude,
            position?.coords?.longitude,
          );
          if (!url) {
            fail("unavailable");
            return;
          }

          const opened = window.open(url, "_blank");
          if (opened) opened.opener = null;

          setMapsUrl(url);
          setBlocked(!opened);
          setStatus("opened");
        },
        (error) => {
          if (id !== requestId.current) return;
          fail(issueKindFromError(error));
        },
        GEOLOCATION_OPTIONS,
      );
    } catch {
      fail("unsupported");
    }
  };

  const canRetry = failed && issue?.canRetry;
  const label = locating
    ? "Finding your location…"
    : canRetry
      ? "Try again"
      : "Find nearest care";

  return (
    <section className="nearest-care" aria-labelledby="nearest-care-heading">
      <h2 id="nearest-care-heading" className="section-label">
        Find care near you
      </h2>

      <p className="nearest-care-note">
        Your browser will ask to share your location only after you press the
        button. It is used once to open a Google Maps search in a new tab, and
        CareCompass does not receive or save it.
      </p>

      {/* aria-disabled (not disabled) so keyboard focus stays on the button
          while the browser's permission prompt is open. */}
      {!(failed && !issue?.canRetry) && (
        <button
          type="button"
          className="btn btn-quiet nearest-care-btn"
          onClick={findCare}
          aria-disabled={locating ? "true" : undefined}
          aria-busy={locating ? "true" : undefined}
        >
          {canRetry ? <Refresh /> : <MapPin />}
          {label}
        </button>
      )}

      <div className="nearest-care-status" aria-live="polite" aria-atomic="true">
        {locating && (
          <p className="nearest-care-msg" role="status">
            Waiting for your location. If your browser asks, choose Allow.
          </p>
        )}

        {failed && issue && (
          <div className="nearest-care-msg">
            <p>{issue.message}</p>
            <p className="nearest-care-hint">{issue.hint}</p>
          </div>
        )}

        {status === "opened" && mapsUrl && (
          <div className="nearest-care-msg">
            <p>
              {blocked
                ? "Your browser blocked the new tab."
                : "Google Maps opened in a new tab. Choose a facility there."}{" "}
              <a href={mapsUrl} target="_blank" rel="noopener noreferrer">
                Open nearby care in Google Maps
                <span className="sr-only"> (opens in a new tab)</span>
              </a>
            </p>
          </div>
        )}
      </div>
    </section>
  );
}
