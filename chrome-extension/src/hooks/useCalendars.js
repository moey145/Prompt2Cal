// Calendar management hook
import { useState, useEffect } from "react";
import { makeApiCall } from "../utils/api";

export const useCalendars = (userId, isAuthenticated) => {
  const [calendars, setCalendars] = useState([]);
  const [selectedCalendarId, setSelectedCalendarId] = useState(null);
  const [loadingCalendars, setLoadingCalendars] = useState(false);

  const fetchCalendars = async (userIdValue) => {
    try {
      setLoadingCalendars(true);
      const response = await makeApiCall("/calendars", {
        method: "GET",
        params: { user_id: userIdValue || userId },
      });

      if (response.success && response.calendars) {
        setCalendars(response.calendars);

        // Load saved calendar selection or default to primary
        // Note: Backend now only returns writable calendars, so we don't need to check accessRole here
        const saved = await chrome.storage.local.get(["selectedCalendarId"]);
        if (saved.selectedCalendarId) {
          const exists = response.calendars.find(
            (c) => c.id === saved.selectedCalendarId
          );
          if (exists) {
            setSelectedCalendarId(saved.selectedCalendarId);
          } else {
            // Saved calendar no longer exists, switch to primary or first available
            const primary = response.calendars.find((c) => c.primary);
            const newCalendarId = primary ? primary.id : response.calendars[0]?.id || null;
            setSelectedCalendarId(newCalendarId);
            if (newCalendarId) {
              await chrome.storage.local.set({ selectedCalendarId: newCalendarId });
            }
          }
        } else {
          // No saved calendar, default to primary or first available
          const primary = response.calendars.find((c) => c.primary);
          const defaultCalendarId = primary ? primary.id : response.calendars[0]?.id || null;
          setSelectedCalendarId(defaultCalendarId);
          if (defaultCalendarId) {
            await chrome.storage.local.set({ selectedCalendarId: defaultCalendarId });
          }
        }
      }
    } catch (error) {
      console.error("Failed to fetch calendars:", error);
    } finally {
      setLoadingCalendars(false);
    }
  };

  const updateSelectedCalendar = async (calendarId) => {
    setSelectedCalendarId(calendarId);
    await chrome.storage.local.set({ selectedCalendarId: calendarId });
  };

  // Note: fetchCalendars should be called explicitly from parent component
  // after authentication is confirmed to avoid dependency issues

  return {
    calendars,
    selectedCalendarId,
    loadingCalendars,
    fetchCalendars,
    updateSelectedCalendar,
  };
};

