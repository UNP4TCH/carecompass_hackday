import { useEffect, useRef } from "react";

// Moves keyboard/screen-reader focus to a view's heading when the view
// appears, so a change from intake -> assessment -> result is announced.
export function useFocusOnMount() {
  const ref = useRef(null);

  useEffect(() => {
    ref.current?.focus();
  }, []);

  return ref;
}
