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
        const saved = await chrome.storage.local.get(["selectedCalendarId"]);
        if (saved.selectedCalendarId) {
          const exists = response.calendars.find(
            (c) => c.id === saved.selectedCalendarId
          );
          if (exists) {
            setSelectedCalendarId(saved.selectedCalendarId);
          } else {
            const primary = response.calendars.find((c) => c.primary);
            setSelectedCalendarId(
              primary ? primary.id : response.calendars[0]?.id || null
            );
          }
        } else {
          const primary = response.calendars.find((c) => c.primary);
          setSelectedCalendarId(
            primary ? primary.id : response.calendars[0]?.id || null
          );
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

