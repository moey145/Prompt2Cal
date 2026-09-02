// Refactored Popup component using extracted components and hooks
import React, { useState, useEffect, useRef } from "react";
import { Sun, Moon, Settings } from "lucide-react";
import { useAuth } from "./hooks/useAuth";
import { useCalendars } from "./hooks/useCalendars";
import { useVoiceRecognition } from "./hooks/useVoiceRecognition";
import { makeApiCall } from "./utils/api";
import { normalizeEventPayload } from "./utils/eventNormalizers";
import { parseAttendeeInput, ensureUniqueEmails } from "./utils/emailUtils";
import { DEFAULT_COLOR, DEFAULT_REMINDER } from "./utils/constants";
import { SettingsDropdown } from "./components/SettingsDropdown";
import { AuthSection } from "./components/AuthSection";
import { EventInputSection } from "./components/EventInputSection";
import { SingleEventCard } from "./components/SingleEventCard";
import { BulkEventsCard } from "./components/BulkEventsCard";
import { EditEventModal } from "./components/EditEventModal";
import { ConflictWarning } from "./components/ConflictWarning";
import { ToastContainer } from "./components/Toast";

const Popup = () => {
  // Core state
  const [userId, setUserId] = useState(null);
  const [selectedText, setSelectedText] = useState("");
  const [showSelectedText, setShowSelectedText] = useState(false);
  const [parsedEvent, setParsedEvent] = useState(null);
  const [parsedEvents, setParsedEvents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loadingSingle, setLoadingSingle] = useState(false);
  const [showParsedEvent, setShowParsedEvent] = useState(false);
  const [showBulkEvents, setShowBulkEvents] = useState(false);
  const [toasts, setToasts] = useState([]);
  const [eventInput, setEventInput] = useState("");
  const [selectedColor, setSelectedColor] = useState(DEFAULT_COLOR);
  const [selectedReminder, setSelectedReminder] = useState(DEFAULT_REMINDER);
  const [darkMode, setDarkMode] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [authPending, setAuthPending] = useState(false);

  // Single event edit state
  const [singleAttendees, setSingleAttendees] = useState([]);
  const [singleAttendeeInput, setSingleAttendeeInput] = useState("");
  const [editedSingleEvent, setEditedSingleEvent] = useState(null);
  const [showEventEditForm, setShowEventEditForm] = useState(false);
  const [editingStart, setEditingStart] = useState(false);
  const [editingEnd, setEditingEnd] = useState(false);

  // Bulk event edit state
  const [editingEventIndex, setEditingEventIndex] = useState(null);
  const [editingEvent, setEditingEvent] = useState(null);
  const [editingAttendees, setEditingAttendees] = useState([]);
  const [editingAttendeeInput, setEditingAttendeeInput] = useState("");
  const [editingStartBulk, setEditingStartBulk] = useState(false);
  const [editingEndBulk, setEditingEndBulk] = useState(false);

  // Conflict detection state
  const [conflicts, setConflicts] = useState([]);
  const [checkingConflicts, setCheckingConflicts] = useState(false);
  const [bulkEventConflicts, setBulkEventConflicts] = useState({}); // Map of event index to conflicts

  // Custom hooks
  const {
    isAuthenticated,
    isCheckingAuth,
    loadingAuth,
    loadingMicrosoftAuth,
    calendarProvider,
    providers,
    checkAuthStatus,
    handleGoogleAuth: authGoogleAuth,
    handleMicrosoftAuth: authMicrosoftAuth,
    handleLogout: authLogout,
    switchProvider,
    setIsAuthenticated,
  } = useAuth(userId);

  const {
    calendars,
    selectedCalendarId,
    loadingCalendars,
    fetchCalendars,
    updateSelectedCalendar,
  } = useCalendars(userId, isAuthenticated, calendarProvider);

  const { isListening, toggleVoiceRecognition } = useVoiceRecognition();
  const eventInputHydrated = useRef(false);

  // Initialize on mount
  useEffect(() => {
    initializeUser();
    loadThemeFromStorage();
    loadDraftInput();
    // eslint-disable-next-line
  }, []);

  useEffect(() => {
    if (!eventInputHydrated.current) return;
    chrome.storage.local
      .set({ prompt2cal_event_input: eventInput })
      .catch(() => {});
  }, [eventInput]);

  // Close settings dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (showSettings && !event.target.closest(".settings-container")) {
        setShowSettings(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [showSettings]);

  const loadThemeFromStorage = async () => {
    const result = await chrome.storage.local.get(["darkMode"]);
    if (result.darkMode) {
      setDarkMode(result.darkMode);
      document.documentElement.classList.add("dark-mode");
    }
  };

  const loadDraftInput = async () => {
    try {
      const result = await chrome.storage.local.get(["prompt2cal_event_input"]);
      if (typeof result.prompt2cal_event_input === "string") {
        setEventInput(result.prompt2cal_event_input);
      }
    } catch (error) {
      console.error("Failed to restore draft input:", error);
    } finally {
      eventInputHydrated.current = true;
    }
  };

  const toggleTheme = async () => {
    const newDarkMode = !darkMode;
    setDarkMode(newDarkMode);
    document.documentElement.classList.toggle("dark-mode", newDarkMode);
    await chrome.storage.local.set({ darkMode: newDarkMode });
  };

  const initializeUser = async () => {
    try {
      const result = await chrome.storage.local.get(["prompt2cal_user_id"]);
      let userIdValue;

      if (result.prompt2cal_user_id) {
        userIdValue = result.prompt2cal_user_id;
      } else {
        userIdValue = "user_" + Math.random().toString(36).substr(2, 9);
        await chrome.storage.local.set({ prompt2cal_user_id: userIdValue });
      }

      setUserId(userIdValue);
      await checkForSelectedText();

      const authState = await chrome.storage.local.get(["waitingForAuth"]);
      if (authState.waitingForAuth) {
        setAuthPending(true);
        await chrome.storage.local.remove(["waitingForAuth"]);
        setTimeout(async () => {
          const authenticated = await checkAuthStatus(userIdValue);
          if (authenticated) {
            const stored = await chrome.storage.local.get(["calendar_provider"]);
            await fetchCalendars(
              userIdValue,
              stored.calendar_provider || "google"
            );
          }
          setAuthPending(false);
        }, 500);
      } else {
        const authenticated = await checkAuthStatus(userIdValue);
        if (authenticated) {
          const stored = await chrome.storage.local.get(["calendar_provider"]);
          await fetchCalendars(
            userIdValue,
            stored.calendar_provider || "google"
          );
        }
        setAuthPending(false);
      }
    } catch (error) {
      console.error("Error initializing user:", error);
      showMessage("Error initializing extension", "error");
    }
  };

  const checkForSelectedText = async () => {
    try {
      const [tab] = await chrome.tabs.query({
        active: true,
        currentWindow: true,
      });

      if (
        tab.url.startsWith("chrome://") ||
        tab.url.startsWith("chrome-extension://") ||
        tab.url.startsWith("moz-extension://")
      ) {
        return;
      }

      try {
        await chrome.scripting.executeScript({
          target: { tabId: tab.id },
          files: ["content.js"],
        });
        await new Promise((resolve) => setTimeout(resolve, 200));
      } catch (injectError) {
        // Script might already be loaded
      }

      const response = await chrome.tabs.sendMessage(tab.id, {
        action: "getSelectedText",
      });

      if (response && response.selectedText) {
        const text = response.selectedText.trim();
        if (text.length > 0) {
          setSelectedText(text);
          setShowSelectedText(true);
        }
      }
    } catch (error) {
      console.log("Error getting selected text:", error);
    }
  };

  const showMessage = (text, type = "info", link = null) => {
    const id = Date.now() + Math.random();
    setToasts((prev) => [...prev, { id, message: text, type, link }]);
  };

  const removeToast = (id) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  };

  const handleGoogleAuth = async () => {
    try {
      await authGoogleAuth();
    } catch (error) {
      showMessage(`Authentication error: ${error.message}`, "error");
    }
  };

  const handleMicrosoftAuth = async () => {
    try {
      await authMicrosoftAuth();
    } catch (error) {
      showMessage(`Microsoft authentication error: ${error.message}`, "error");
    }
  };

  const handleProviderChange = async (provider) => {
    try {
      const authenticated = await switchProvider(provider, userId);
      if (authenticated) {
        await fetchCalendars(userId, provider);
        showMessage(
          provider === "microsoft"
            ? "Using Microsoft Calendar"
            : "Using Google Calendar",
          "success"
        );
      } else {
        showMessage(
          `Connect ${
            provider === "microsoft" ? "Microsoft" : "Google"
          } Calendar first`,
          "error"
        );
      }
    } catch (error) {
      showMessage(`Could not switch calendar account: ${error.message}`, "error");
    }
  };

  const handleLogout = async () => {
    const providerLabel =
      calendarProvider === "microsoft" ? "Microsoft" : "Google";
    if (
      !confirm(
        `Are you sure you want to logout? You'll need to reconnect your ${providerLabel} Calendar.`
      )
    ) {
      return;
    }

    try {
      setLoading(true);
      const success = await authLogout();
      if (success) {
        showMessage(`Successfully logged out of ${providerLabel}`, "success");
        const stored = await chrome.storage.local.get([
          "prompt2cal_auth_status",
          "calendar_provider",
        ]);
        if (stored.prompt2cal_auth_status) {
          await fetchCalendars(userId, stored.calendar_provider || "google");
        } else {
          setShowSettings(false);
        }
      } else {
        showMessage("Logout failed", "error");
      }
    } catch (error) {
      showMessage(`Logout error: ${error.message}`, "error");
    } finally {
      setLoading(false);
    }
  };

  const handleParseEvent = async (forceMultiple = null) => {
    const text = eventInput.trim();
    if (!text) {
      showMessage("Please enter event description", "error");
      return;
    }

    if (loadingSingle) return;

    try {
      setLoadingSingle(true);
      setShowParsedEvent(false);
      setShowBulkEvents(false);

      const response = await makeApiCall("/create_event", {
        method: "POST",
        body: JSON.stringify({
          text: text,
          user_id: userId,
          timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
          force_multiple: forceMultiple,
        }),
      });

      if (response.success) {
        if (response.is_bulk && response.parsed_events) {
          const normalizedEvents = response.parsed_events
            .map((event) => normalizeEventPayload(event))
            .filter(Boolean);
          setParsedEvents(normalizedEvents);
          setSelectedColor(DEFAULT_COLOR);
          setSelectedReminder(DEFAULT_REMINDER);
          setShowBulkEvents(true);

          // Check for conflicts for all events if authenticated
          if (isAuthenticated) {
            await checkBulkEventConflicts(normalizedEvents);
          }
        } else if (response.parsed_event) {
          const normalizedEvent = normalizeEventPayload(response.parsed_event);
          setParsedEvent(normalizedEvent);
          setSelectedColor(normalizedEvent?.color || DEFAULT_COLOR);
          setSelectedReminder(normalizedEvent?.reminder ?? DEFAULT_REMINDER);
          setShowParsedEvent(true);

          // Check for conflicts if authenticated
          if (
            isAuthenticated &&
            normalizedEvent.start_time &&
            normalizedEvent.end_time
          ) {
            await checkEventConflicts(normalizedEvent);
          }
        } else {
          showMessage("Failed to parse event", "error");
        }
      } else {
        showMessage("Failed to parse event", "error");
      }
    } catch (error) {
      console.error("Parse error:", error);
      showMessage(`Failed to parse event: ${error.message}`, "error");
    } finally {
      setLoadingSingle(false);
    }
  };

  const handleCreateEvent = async () => {
    if (!parsedEvent || loading || loadingSingle) return;
    if (!isAuthenticated) {
      showMessage(
        "Please connect Google or Microsoft Calendar to create events",
        "error"
      );
      return;
    }

    try {
      setLoading(true);

      const clientTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
      const eventWithColor = {
        ...parsedEvent,
        color: selectedColor,
        reminder: selectedReminder,
        calendar_id: selectedCalendarId,
        calendar_provider: calendarProvider,
        timezone: parsedEvent.timezone || clientTimezone,
      };

      const response = await makeApiCall("/confirm_event", {
        method: "POST",
        params: { user_id: userId },
        body: JSON.stringify(eventWithColor),
      });

      showMessage(`Event created!`, "success", response.event_link);

      resetForm();
    } catch (error) {
      console.error("Create event error:", error);
      const errorMessage = error.message || "Failed to create event";
      // Check if it's a permission error
      if (
        errorMessage.toLowerCase().includes("write access") ||
        errorMessage.includes("requiredAccessLevel")
      ) {
        showMessage(
          "Permission error: You don't have write access to the selected calendar. Please select a calendar where you have writer or owner permissions in Settings.",
          "error"
        );
      } else {
        showMessage(`Failed to create event: ${errorMessage}`, "error");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleCreateAllEvents = async () => {
    if (
      !parsedEvents ||
      parsedEvents.length === 0 ||
      loading ||
      loadingSingle
    ) {
      showMessage("No events to create", "error");
      return;
    }
    if (!isAuthenticated) {
      showMessage(
        "Please connect Google or Microsoft Calendar to create events",
        "error"
      );
      return;
    }

    try {
      setLoading(true);

      const clientTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
      const eventsWithColor = parsedEvents.map((event) => ({
        ...event,
        color: event.color || selectedColor || DEFAULT_COLOR,
        reminder: selectedReminder,
        calendar_id: selectedCalendarId,
        calendar_provider: calendarProvider,
        timezone: event.timezone || clientTimezone,
      }));

      const response = await makeApiCall("/confirm_bulk_events", {
        method: "POST",
        params: { user_id: userId },
        body: JSON.stringify(eventsWithColor),
      });

      if (response.success) {
        showMessage(
          response.message ||
            `Created ${response.total_created || parsedEvents.length} events!`,
          "success"
        );
        setShowBulkEvents(false);
        setEventInput("");
      } else {
        showMessage(
          response.message ||
            "Failed to create events. Please check your calendar permissions.",
          "error"
        );
      }
    } catch (error) {
      const errorMessage = error.message || "Failed to create events";
      // Check if it's a permission error
      if (
        errorMessage.toLowerCase().includes("write access") ||
        errorMessage.includes("requiredAccessLevel")
      ) {
        showMessage(
          "Permission error: You don't have write access to the selected calendar. Please select a calendar where you have writer or owner permissions in Settings.",
          "error"
        );
      } else {
        showMessage(`Error: ${errorMessage}`, "error");
      }
    } finally {
      setLoading(false);
    }
  };

  const removeParsedEvent = (idx) => {
    setParsedEvents((prev) => prev.filter((_, i) => i !== idx));
  };

  const openEditModal = (index) => {
    const current = normalizeEventPayload(parsedEvents[index]);
    if (!current) return;

    const attendeeList = current.attendees || [];
    setEditingEventIndex(index);
    setEditingEvent({ ...current, attendees: attendeeList });
    setEditingAttendees(attendeeList);
    setEditingAttendeeInput("");
    setSelectedColor(current.color || DEFAULT_COLOR);
    setSelectedReminder(current.reminder ?? DEFAULT_REMINDER);
    setEditingStartBulk(false);
    setEditingEndBulk(false);
  };

  const closeEditModal = () => {
    setEditingEventIndex(null);
    setEditingEvent(null);
    setEditingAttendees([]);
    setEditingAttendeeInput("");
    setSelectedColor(DEFAULT_COLOR);
    setSelectedReminder(DEFAULT_REMINDER);
    setEditingStartBulk(false);
    setEditingEndBulk(false);
  };

  const saveEditedEvent = () => {
    if (editingEventIndex !== null && editingEvent) {
      const sanitizedAttendees = ensureUniqueEmails(editingAttendees);

      const sanitizedEvent = {
        ...editingEvent,
        attendees: sanitizedAttendees,
        add_conference: Boolean(editingEvent.add_conference),
      };

      const updatedEvents = parsedEvents.map((ev, i) =>
          i === editingEventIndex
            ? {
              ...sanitizedEvent,
                color: selectedColor,
                reminder: selectedReminder,
              }
            : ev
      );

      setParsedEvents(updatedEvents);
      closeEditModal();

      // Re-check conflicts for the updated event
      if (
        isAuthenticated &&
        sanitizedEvent.start_time &&
        sanitizedEvent.end_time
      ) {
        checkBulkEventConflicts(updatedEvents);
      }
    }
  };

  const handleAddEditingAttendee = () => {
    if (!editingEvent) return;
    const newEmails = parseAttendeeInput(editingAttendeeInput);
    if (!newEmails.length) {
      if (editingAttendeeInput.trim()) {
        showMessage("Please enter a valid email address", "error");
      }
      return;
    }

    const combined = ensureUniqueEmails([...editingAttendees, ...newEmails]);
    if (combined.length === editingAttendees.length) {
      showMessage("Guest already added", "info");
      setEditingAttendeeInput("");
      return;
    }

    setEditingAttendees(combined);
    setEditingEvent((prev) => (prev ? { ...prev, attendees: combined } : prev));
    setEditingAttendeeInput("");
  };

  const handleRemoveEditingAttendee = (email) => {
    const filtered = editingAttendees.filter((item) => item !== email);
    setEditingAttendees(filtered);
    setEditingEvent((prev) => (prev ? { ...prev, attendees: filtered } : prev));
  };

  const handleEditSingleEvent = () => {
    const normalized = normalizeEventPayload(parsedEvent);
    if (!normalized) return;

    const attendeeList = normalized.attendees || [];
    setSingleAttendees(attendeeList);
    setSingleAttendeeInput("");
    setSelectedColor(normalized.color || DEFAULT_COLOR);
    setSelectedReminder(normalized.reminder ?? DEFAULT_REMINDER);
    setEditedSingleEvent({ ...normalized });
    setEditingStart(false);
    setEditingEnd(false);
    setShowEventEditForm(true);
  };

  const handleSingleEventFormChange = (field, value) => {
    setEditedSingleEvent({ ...editedSingleEvent, [field]: value });
  };

  const handleAddSingleAttendee = () => {
    if (!editedSingleEvent) return;
    const newEmails = parseAttendeeInput(singleAttendeeInput);
    if (!newEmails.length) {
      if (singleAttendeeInput.trim()) {
        showMessage("Please enter a valid email address", "error");
      }
      return;
    }

    const combined = ensureUniqueEmails([...singleAttendees, ...newEmails]);
    if (combined.length === singleAttendees.length) {
      showMessage("Guest already added", "info");
      setSingleAttendeeInput("");
      return;
    }

    setSingleAttendees(combined);
    handleSingleEventFormChange("attendees", combined);
    setSingleAttendeeInput("");
  };

  const handleRemoveSingleAttendee = (email) => {
    const filtered = singleAttendees.filter((item) => item !== email);
    setSingleAttendees(filtered);
    handleSingleEventFormChange("attendees", filtered);
  };

  const handleSaveSingleEdit = () => {
    if (!editedSingleEvent) return;

    const sanitizedAttendees = ensureUniqueEmails(singleAttendees);

    const sanitizedEvent = {
      ...editedSingleEvent,
      attendees: sanitizedAttendees,
      add_conference: Boolean(editedSingleEvent.add_conference),
      color: selectedColor,
      reminder: selectedReminder,
    };

    setParsedEvent(sanitizedEvent);
    setSingleAttendees(sanitizedAttendees);
    setSelectedColor(sanitizedEvent.color || DEFAULT_COLOR);
    setSelectedReminder(sanitizedEvent.reminder ?? DEFAULT_REMINDER);
    setShowEventEditForm(false);
    setEditedSingleEvent(null);
    setSingleAttendeeInput("");

    // Re-check conflicts for the updated event
    if (
      isAuthenticated &&
      sanitizedEvent.start_time &&
      sanitizedEvent.end_time
    ) {
      checkEventConflicts(sanitizedEvent);
    }
  };

  const handleCancelSingleEdit = () => {
    setShowEventEditForm(false);
    setEditedSingleEvent(null);
    setSingleAttendees([]);
    setSingleAttendeeInput("");
    const normalized = normalizeEventPayload(parsedEvent);
    setSelectedColor(normalized?.color || DEFAULT_COLOR);
    setSelectedReminder(normalized?.reminder ?? DEFAULT_REMINDER);
    setEditingStart(false);
    setEditingEnd(false);
  };

  const handleToggleVoice = async () => {
    try {
      await toggleVoiceRecognition(eventInput, setEventInput);
    } catch (error) {
      showMessage(`${error.message}`, "error");
    }
  };

  const checkEventConflicts = async (event) => {
    if (!event || !event.start_time || !event.end_time || !isAuthenticated) {
      return;
    }

    try {
      setCheckingConflicts(true);
      const duration = event.duration_minutes || 60;

      // Check if event is recurring
      const isRecurring =
        event.recurrence_type && event.recurrence_type !== "none";

      const response = await makeApiCall("/check_conflicts", {
        method: "POST",
        body: JSON.stringify({
          user_id: userId,
          start_time: event.start_time,
          end_time: event.end_time,
          duration_minutes: duration,
          calendar_id: selectedCalendarId,
          calendar_provider: calendarProvider,
          buffer_minutes: 15,
          // Pass recurrence info for recurring events
          recurrence_type: isRecurring ? event.recurrence_type : null,
          recurrence_count: isRecurring ? event.recurrence_count : null,
          recurrence_interval: isRecurring ? event.recurrence_interval : null,
          end_date: isRecurring ? event.end_date : null,
        }),
      });

      if (response.success) {
        setConflicts(response.conflicts || []);
      }
    } catch (error) {
      console.error("Error checking conflicts:", error);
      // Don't show error to user - conflict checking is optional
    } finally {
      setCheckingConflicts(false);
    }
  };


  const checkBulkEventConflicts = async (events) => {
    if (!events || events.length === 0 || !isAuthenticated) {
      return;
    }

    const conflictsMap = {};

    // Check conflicts for each event
    for (let i = 0; i < events.length; i++) {
      const event = events[i];
      if (!event.start_time || !event.end_time) continue;

      try {
        const duration = event.duration_minutes || 60;

        // Check if event is recurring
        const isRecurring =
          event.recurrence_type && event.recurrence_type !== "none";

        const response = await makeApiCall("/check_conflicts", {
          method: "POST",
          body: JSON.stringify({
            user_id: userId,
            start_time: event.start_time,
            end_time: event.end_time,
            duration_minutes: duration,
            calendar_id: selectedCalendarId,
            calendar_provider: calendarProvider,
            buffer_minutes: 15,
            // Pass recurrence info for recurring events
            recurrence_type: isRecurring ? event.recurrence_type : null,
            recurrence_count: isRecurring ? event.recurrence_count : null,
            recurrence_interval: isRecurring ? event.recurrence_interval : null,
            end_date: isRecurring ? event.end_date : null,
          }),
        });

        if (response.success && response.has_conflicts) {
          conflictsMap[i] = {
            conflicts: response.conflicts || [],
          };
        }
      } catch (error) {
        console.error(`Error checking conflicts for event ${i}:`, error);
      }
    }

    setBulkEventConflicts(conflictsMap);
  };

  const resetForm = () => {
    setEventInput("");
    setParsedEvent(null);
    setParsedEvents([]);
    setShowParsedEvent(false);
    setShowBulkEvents(false);
    setShowSelectedText(false);
    setSelectedText("");
    setSingleAttendees([]);
    setSingleAttendeeInput("");
    setEditingAttendees([]);
    setEditingAttendeeInput("");
    setSelectedColor(DEFAULT_COLOR);
    setSelectedReminder(DEFAULT_REMINDER);
    setEditedSingleEvent(null);
    setShowEventEditForm(false);
    setEditingEvent(null);
    setEditingEventIndex(null);
    setEditingStart(false);
    setEditingEnd(false);
    setConflicts([]);
    setBulkEventConflicts({});
  };

  return (
    <div className="container">
      <div className="header">
        <div className="header-left">
          {isAuthenticated && (
            <div className="settings-container">
              <button
                className="settings-button"
                onClick={() => setShowSettings(!showSettings)}
                title="Settings"
              >
                <Settings size={18} />
              </button>
              <SettingsDropdown
                showSettings={showSettings}
                setShowSettings={setShowSettings}
                calendars={calendars}
                selectedCalendarId={selectedCalendarId}
                loadingCalendars={loadingCalendars}
                onCalendarChange={async (e) => {
                  await updateSelectedCalendar(e.target.value);
                }}
                onLogout={handleLogout}
                calendarProvider={calendarProvider}
                providers={providers}
                onProviderChange={handleProviderChange}
                onConnectGoogle={handleGoogleAuth}
                onConnectMicrosoft={handleMicrosoftAuth}
                loadingAuth={loadingAuth}
                loadingMicrosoftAuth={loadingMicrosoftAuth}
              />
            </div>
          )}
        </div>
        <button
          id="themeToggle"
          className="theme-toggle"
          onClick={toggleTheme}
          title={darkMode ? "Switch to light mode" : "Switch to dark mode"}
        >
          {darkMode ? <Moon size={20} /> : <Sun size={20} />}
        </button>
        <div className="hero">
          <div className="hero-icon">
            <span className="hero-glow" />
            <img
              src={chrome.runtime.getURL(
                darkMode ? "icons/DarkModeLogo.svg" : "icons/Logo.svg"
              )}
              alt="Prompt2Cal Logo"
              className="logo-image"
            />
          </div>
          <h1 className="logo">
            <span className="logo-black">Prompt2</span>
            <span className="logo-red">Cal</span>
          </h1>
          <div className="tagline">
            Turn natural language into calendar events instantly
          </div>
        </div>
      </div>

      {!isCheckingAuth && !isAuthenticated && !authPending && (
        <AuthSection
          onGoogleAuth={handleGoogleAuth}
          onMicrosoftAuth={handleMicrosoftAuth}
          loadingAuth={loadingAuth}
          loadingMicrosoftAuth={loadingMicrosoftAuth}
        />
      )}

      <div className="main-section" id="mainSection">
        <EventInputSection
          eventInput={eventInput}
          setEventInput={setEventInput}
          onParse={handleParseEvent}
          isListening={isListening}
          onToggleVoice={handleToggleVoice}
          loadingSingle={loadingSingle}
          showSelectedText={showSelectedText}
          selectedText={selectedText}
          onUseSelectedText={() => {
                setEventInput(selectedText);
                setShowSelectedText(false);
              }}
        />

        {showParsedEvent && parsedEvent && (
          <SingleEventCard
            parsedEvent={parsedEvent}
            onEdit={handleEditSingleEvent}
            onCreate={handleCreateEvent}
            onCancel={() => setShowParsedEvent(false)}
            loading={loading}
            loadingSingle={loadingSingle}
            conflicts={conflicts}
            checkingConflicts={checkingConflicts}
          />
        )}

        {showEventEditForm && editedSingleEvent && (
          <EditEventModal
            event={editedSingleEvent}
            attendees={singleAttendees}
            attendeeInput={singleAttendeeInput}
            setAttendeeInput={setSingleAttendeeInput}
            onAddAttendee={handleAddSingleAttendee}
            onRemoveAttendee={handleRemoveSingleAttendee}
            selectedColor={selectedColor}
            setSelectedColor={setSelectedColor}
            selectedReminder={selectedReminder}
            setSelectedReminder={setSelectedReminder}
            editingStart={editingStart}
            setEditingStart={setEditingStart}
            editingEnd={editingEnd}
            setEditingEnd={setEditingEnd}
            onFieldChange={handleSingleEventFormChange}
            onSave={handleSaveSingleEdit}
            onCancel={handleCancelSingleEdit}
            loading={loading}
          />
        )}

        {showBulkEvents && parsedEvents.length > 0 && (
          <BulkEventsCard
            parsedEvents={parsedEvents}
            onEdit={openEditModal}
            onRemove={removeParsedEvent}
            onCreateAll={handleCreateAllEvents}
            onCancel={() => setShowBulkEvents(false)}
            loading={loading}
            loadingSingle={loadingSingle}
            eventConflicts={bulkEventConflicts}
          />
        )}

        {editingEvent && editingEventIndex !== null && (
          <EditEventModal
            event={editingEvent}
            attendees={editingAttendees}
            attendeeInput={editingAttendeeInput}
            setAttendeeInput={setEditingAttendeeInput}
            onAddAttendee={handleAddEditingAttendee}
            onRemoveAttendee={handleRemoveEditingAttendee}
            selectedColor={selectedColor}
            setSelectedColor={setSelectedColor}
            selectedReminder={selectedReminder}
            setSelectedReminder={setSelectedReminder}
            editingStart={editingStartBulk}
            setEditingStart={setEditingStartBulk}
            editingEnd={editingEndBulk}
            setEditingEnd={setEditingEndBulk}
            onFieldChange={(field, value) => {
              setEditingEvent((prev) =>
                prev ? { ...prev, [field]: value } : prev
              );
            }}
            onSave={saveEditedEvent}
            onCancel={closeEditModal}
            loading={loading}
          />
        )}

        <ToastContainer toasts={toasts} onClose={removeToast} />
      </div>
    </div>
  );
};

export default Popup;
