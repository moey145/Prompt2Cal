// Whether to offer the free-slot search for the signed-in provider. The backend
// lists the providers it can search on /health; until that answers, or if it
// fails, the feature stays hidden rather than erroring when used.
import { useEffect, useState } from "react";
import { makeApiCall } from "../utils/api";
import { slotFinderSupported } from "../utils/slotFinder";

export const useSlotFinder = (isAuthenticated, calendarProvider) => {
  const [health, setHealth] = useState(null);

  useEffect(() => {
    if (!isAuthenticated || health) return undefined;
    let isMounted = true;
    makeApiCall("/health", { method: "GET" })
      .then((response) => {
        if (isMounted) setHealth(response);
      })
      .catch((error) => console.error("Failed to check slot finder support:", error));
    return () => {
      isMounted = false;
    };
  }, [isAuthenticated, health]);

  return isAuthenticated && health !== null && slotFinderSupported(health, calendarProvider);
};
