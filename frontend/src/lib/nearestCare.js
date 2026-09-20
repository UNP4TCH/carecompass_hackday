// "Find Nearest Care" helpers — presentation/plumbing only.
//
// Nothing here decides urgency, care level or what kind of facility the
// person needs; the backend does that. This file only turns a browser
// position into an external Google Maps search URL, and turns Geolocation
// failures into plain-language messages. Coordinates never leave the browser
// except inside that Maps URL, and they are never persisted.

// One fixed, neutral search term for every result. It is deliberately not
// derived from the assessment so the frontend never invents guidance.
export const MAPS_QUERY = "hospitals and clinics";

// Fresh-ish fix, short wait, no high-accuracy GPS drain. One-shot only.
export const GEOLOCATION_OPTIONS = {
  enableHighAccuracy: false,
  timeout: 15000,
  maximumAge: 30000,
};

// Some browsers (notably Firefox's "Not now") never call back when the
// permission prompt is dismissed, and the timeout above only starts counting
// once permission is granted. This watchdog stops the button being stuck.
export const REQUEST_WATCHDOG_MS = 30000;

const isCoordinate = (value, limit) =>
  typeof value === "number" && Number.isFinite(value) && Math.abs(value) <= limit;

// -> https://www.google.com/maps/search/hospitals+and+clinics/@LAT,LON,14z
// Returns null when the coordinates are not usable numbers.
export function buildMapsUrl(latitude, longitude) {
  if (!isCoordinate(latitude, 90) || !isCoordinate(longitude, 180)) return null;

  const query = encodeURIComponent(MAPS_QUERY).replace(/%20/g, "+");
  return `https://www.google.com/maps/search/${query}/@${latitude.toFixed(5)},${longitude.toFixed(5)},14z`;
}

const FALLBACK_HINT =
  "You can also search for a hospital or clinic directly in your maps app.";

// Maps a GeolocationPositionError code (or an unsupported environment) onto
// a message and whether a retry is worth offering.
export function describeLocationIssue(kind) {
  switch (kind) {
    case "denied":
      return {
        kind,
        message:
          "Location access was blocked, so we can't search near you. To use this, allow location for this site in your browser settings, then try again.",
        hint: FALLBACK_HINT,
        canRetry: true,
      };
    case "timeout":
      return {
        kind,
        message:
          "Finding your location took too long. Check that location services are on and you have a signal, then try again.",
        hint: FALLBACK_HINT,
        canRetry: true,
      };
    case "insecure":
      return {
        kind,
        message:
          "Your browser only shares location on a secure (https) connection, and this page isn't on one.",
        hint: FALLBACK_HINT,
        canRetry: false,
      };
    case "unsupported":
      return {
        kind,
        message: "This browser doesn't support finding your location.",
        hint: FALLBACK_HINT,
        canRetry: false,
      };
    default:
      return {
        kind: "unavailable",
        message:
          "Your location couldn't be determined right now. Check that location services are on, then try again.",
        hint: FALLBACK_HINT,
        canRetry: true,
      };
  }
}

// GeolocationPositionError.code: 1 = denied, 2 = unavailable, 3 = timeout.
export function issueKindFromError(error) {
  switch (error?.code) {
    case 1:
      return "denied";
    case 3:
      return "timeout";
    default:
      return "unavailable";
  }
}
