// Whether to offer the free-slot search for the signed-in provider. The backend
// lists the providers it can search on /health. The last answer is kept in
// storage, so the button shows as the popup opens instead of after a slow
// first request; until any answer exists, the feature stays hidden.
import { useEffect, useState } from "react";
import { makeApiCall } from "../utils/api";
import { slotFinderSupported } from "../utils/slotFinder";

const HEALTH_KEY = "prompt2cal_slot_finder_providers";

export const useSlotFinder = (isAuthenticated, calendarProvider) => {
  const [health, setHealth] = useState(null);

  useEffect(() => {
    let isMounted = true;
    chrome.storage.local
      .get([HEALTH_KEY])
      .then((stored) => {
        const providers = stored[HEALTH_KEY];
        // A fresh answer that landed first wins over the saved one.
        if (isMounted && Array.isArray(providers)) {
          setHealth((current) => current || { slot_finder_providers: providers });
        }
      })
      .catch(() => {});
    // Asked straight away, not after sign-in is confirmed: it needs no
    // account, and it wakes the server while the popup reads its storage.
    makeApiCall("/health", { method: "GET" })
      .then((response) => {
        if (!isMounted) return;
        setHealth(response);
        chrome.storage.local
          .set({ [HEALTH_KEY]: response.slot_finder_providers || [] })
          .catch(() => {});
      })
      .catch((error) => console.error("Failed to check slot finder support:", error));
    return () => {
      isMounted = false;
    };
  }, []);

  return isAuthenticated && health !== null && slotFinderSupported(health, calendarProvider);
};
