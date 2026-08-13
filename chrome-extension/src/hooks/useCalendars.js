// Calendar management hook
import { useState } from "react";
import { makeApiCall } from "../utils/api";

export const useCalendars = (userId, isAuthenticated, calendarProvider = "google") => {
  const [calendars, setCalendars] = useState([]);
  const [selectedCalendarId, setSelectedCalendarId] = useState(null);
  const [loadingCalendars, setLoadingCalendars] = useState(false);

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

        const storageKey =
          provider === "microsoft"
            ? "selectedMicrosoftCalendarId"
            : "selectedCalendarId";
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
      setCalendars([]);
      setSelectedCalendarId(null);
    } finally {
      setLoadingCalendars(false);
    }
  };

  const updateSelectedCalendar = async (calendarId) => {
    setSelectedCalendarId(calendarId);
    const storageKey =
      calendarProvider === "microsoft"
        ? "selectedMicrosoftCalendarId"
        : "selectedCalendarId";
    await chrome.storage.local.set({ [storageKey]: calendarId });
  };

  return {
    calendars,
    selectedCalendarId,
    loadingCalendars,
    fetchCalendars,
    updateSelectedCalendar,
  };
};
