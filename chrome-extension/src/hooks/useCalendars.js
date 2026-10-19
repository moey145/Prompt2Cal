// Calendar management hook
import { useEffect, useState } from "react";
import { makeApiCall } from "../utils/api";

// The last calendar list per provider, shown while a fresh one loads.
const savedListKey = (provider) => `prompt2cal_calendars_${provider || "google"}`;
const selectedKey = (provider) =>
  provider === "microsoft" ? "selectedMicrosoftCalendarId" : "selectedCalendarId";

export const useCalendars = (userId, isAuthenticated, calendarProvider = "google") => {
  const [calendars, setCalendars] = useState([]);
  const [selectedCalendarId, setSelectedCalendarId] = useState(null);
  const [loadingCalendars, setLoadingCalendars] = useState(false);

  useEffect(() => {
    if (!isAuthenticated) return undefined;
    let isMounted = true;
    const provider = calendarProvider || "google";
    chrome.storage.local
      .get([savedListKey(provider), selectedKey(provider)])
      .then((saved) => {
        const list = saved[savedListKey(provider)];
        if (!isMounted || !Array.isArray(list) || !list.length) return;
        // Only fill an empty list: a fresh one that arrived first is newer.
        setCalendars((current) => (current.length ? current : list));
        setSelectedCalendarId(
          (current) => current || saved[selectedKey(provider)] || list[0]?.id || null
        );
      })
      .catch(() => {});
    return () => {
      isMounted = false;
    };
  }, [isAuthenticated, calendarProvider]);

  const fetchCalendars = async (userIdValue, providerValue) => {
    try {
      setLoadingCalendars(true);
      const provider = providerValue || calendarProvider || "google";
      const response = await makeApiCall("/calendars", {
        method: "GET",
        params: {
          user_id: userIdValue || userId,
          provider,
        },
      });

      if (response.success && response.calendars) {
        setCalendars(response.calendars);
        chrome.storage.local
          .set({ [savedListKey(provider)]: response.calendars })
          .catch(() => {});

        const storageKey = selectedKey(provider);
        const saved = await chrome.storage.local.get([storageKey]);
        const savedId = saved[storageKey];

        if (savedId) {
          const exists = response.calendars.find((c) => c.id === savedId);
          if (exists) {
            setSelectedCalendarId(savedId);
          } else {
            const primary = response.calendars.find((c) => c.primary);
            const newCalendarId =
              primary ? primary.id : response.calendars[0]?.id || null;
            setSelectedCalendarId(newCalendarId);
            if (newCalendarId) {
              await chrome.storage.local.set({ [storageKey]: newCalendarId });
            }
          }
        } else {
          const primary = response.calendars.find((c) => c.primary);
          const defaultCalendarId =
            primary ? primary.id : response.calendars[0]?.id || null;
          setSelectedCalendarId(defaultCalendarId);
          if (defaultCalendarId) {
            await chrome.storage.local.set({ [storageKey]: defaultCalendarId });
          }
        }
      } else {
        setCalendars([]);
        setSelectedCalendarId(null);
      }
    } catch (error) {
      console.error("Failed to fetch calendars:", error);
      // With no reply at all, the saved list is still the best there is.
      if (!error.status) return;
      setCalendars([]);
      setSelectedCalendarId(null);
    } finally {
      setLoadingCalendars(false);
    }
  };

  const updateSelectedCalendar = async (calendarId) => {
    setSelectedCalendarId(calendarId);
    await chrome.storage.local.set({ [selectedKey(calendarProvider)]: calendarId });
  };

  return {
    calendars,
    selectedCalendarId,
    loadingCalendars,
    fetchCalendars,
    updateSelectedCalendar,
  };
};
