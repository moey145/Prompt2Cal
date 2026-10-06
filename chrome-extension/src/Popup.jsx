// Refactored Popup component using extracted components and hooks
import React, { useState, useEffect, useRef } from "react";
import { Sun, Moon, Settings, CalendarSearch } from "lucide-react";
import { useAuth } from "./hooks/useAuth";
import { useCalendars } from "./hooks/useCalendars";
import { useCategories } from "./hooks/useCategories";
import { useVoiceRecognition } from "./hooks/useVoiceRecognition";
import { makeApiCall } from "./utils/api";
import { normalizeEventPayload } from "./utils/eventNormalizers";
import { parseAttendeeInput, ensureUniqueEmails } from "./utils/emailUtils";
import { API_BASE, DEFAULT_COLOR, DEFAULT_REMINDER } from "./utils/constants";
import {
  PARSE_JOB_KEY,
  PREVIEW_KEY,
  parseJobState,
  previewToRestore,
  previewToSave,
} from "./utils/parseJob";
import { isIssuedSession } from "./utils/signInState";
import { SettingsDropdown } from "./components/SettingsDropdown";
import { AuthSection } from "./components/AuthSection";
import { EventInputSection } from "./components/EventInputSection";
import { SingleEventCard } from "./components/SingleEventCard";
import { BulkEventsCard } from "./components/BulkEventsCard";
import { EditEventModal } from "./components/EditEventModal";
import { ConflictWarning } from "./components/ConflictWarning";
import { FindSlotPanel } from "./components/FindSlotPanel";
import { useSlotFinder } from "./hooks/useSlotFinder";
import { slotSearchErrorMessage } from "./utils/slotFinder";
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

  // Single event edit state
  const [singleAttendees, setSingleAttendees] = useState([]);
  const [singleAttendeeInput, setSingleAttendeeInput] = useState("");
  const [editedSingleEvent, setEditedSingleEvent] = useState(null);
  const [showEventEditForm, setShowEventEditForm] = useState(false);

  // Bulk event edit state
  const [editingEventIndex, setEditingEventIndex] = useState(null);
  const [editingEvent, setEditingEvent] = useState(null);
  const [editingAttendees, setEditingAttendees] = useState([]);
  const [editingAttendeeInput, setEditingAttendeeInput] = useState("");

  // Conflict detection state
  const [conflicts, setConflicts] = useState([]);
  const [checkingConflicts, setCheckingConflicts] = useState(false);
  const [alternatives, setAlternatives] = useState([]);
  const [loadingAlternatives, setLoadingAlternatives] = useState(false);
  const [showFindSlot, setShowFindSlot] = useState(false);
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

  const { categories } = useCategories(userId, isAuthenticated, calendarProvider);
  const slotFinderAvailable = useSlotFinder(isAuthenticated, calendarProvider);

  // Close the slot finder if the provider changes to one it cannot search.
  useEffect(() => {
    if (!slotFinderAvailable) setShowFindSlot(false);
  }, [slotFinderAvailable]);

  const { isListening, toggleVoiceRecognition } = useVoiceRecognition();
  const eventInputHydrated = useRef(false);
  // Set once the saved preview has been read, so an empty first render does
  // not wipe it from storage before it is restored.
  const previewHydrated = useRef(false);
  // A result that arrived before sign-in status was known still needs its
  // clash check; the effect below runs it once the popup knows.
  const needsConflictCheck = useRef(false);

  // Initialize on mount
  useEffect(() => {
    initializeUser();
    loadThemeFromStorage();
    loadDraftInput();
    loadSavedWork();
    // eslint-disable-next-line
  }, []);

  // Sign-in finishes in the background worker; pick up its result if this
  // popup is open when it lands.
  useEffect(() => {
    const handleStorageChange = async (changes, area) => {
      if (area !== "local") return;
      const session = changes.prompt2cal_user_id?.newValue;
      if (isIssuedSession(session)) {
        setUserId(session);
        const authenticated = await checkAuthStatus(session);
        if (authenticated) {
          const stored = await chrome.storage.local.get(["calendar_provider"]);
          await fetchCalendars(session, stored.calendar_provider || "google");
        }
      }
      // A parse started earlier finished in the background worker.
      if (changes[PARSE_JOB_KEY]?.newValue) {
        consumeParseJob(changes[PARSE_JOB_KEY].newValue);
      }
      const authError = changes.prompt2cal_auth_error?.newValue;
      if (authError) {
        showMessage(authError, "error");
        await chrome.storage.local.remove(["prompt2cal_auth_error"]);
      }
    };
    chrome.storage.onChanged.addListener(handleStorageChange);
    return () => chrome.storage.onChanged.removeListener(handleStorageChange);
    // eslint-disable-next-line
  }, []);

  useEffect(() => {
    if (!eventInputHydrated.current) return;
    chrome.storage.local
      .set({ prompt2cal_event_input: eventInput })
      .catch(() => {});
  }, [eventInput]);

  // Keep the preview on screen in storage, so closing the popup does not lose
  // it (or the edits made to it) before the event is created or cancelled.
  useEffect(() => {
    if (!previewHydrated.current) return;
    const saved = previewToSave({ showParsedEvent, parsedEvent, showBulkEvents, parsedEvents });
    (saved
      ? chrome.storage.local.set({ [PREVIEW_KEY]: saved })
      : chrome.storage.local.remove([PREVIEW_KEY])
    ).catch(() => {});
  }, [showParsedEvent, parsedEvent, showBulkEvents, parsedEvents]);

  useEffect(() => {
    if (!isAuthenticated || !needsConflictCheck.current) return;
    needsConflictCheck.current = false;
    if (showParsedEvent && parsedEvent?.start_time && parsedEvent?.end_time) {
      checkEventConflicts(parsedEvent);
    } else if (showBulkEvents && parsedEvents.length) {
      checkBulkEventConflicts(parsedEvents);
    }
    // eslint-disable-next-line
  }, [isAuthenticated, showParsedEvent, parsedEvent, showBulkEvents, parsedEvents]);

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

  // Bring back a preview left open last time, then pick up a parse that ran
  // (or is still running) while the popup was closed.
  const loadSavedWork = async () => {
    try {
      const stored = await chrome.storage.local.get([PREVIEW_KEY, PARSE_JOB_KEY]);
      const preview = previewToRestore(stored[PREVIEW_KEY]);
      if (preview?.kind === "single") {
        setParsedEvent(preview.event);
        setSelectedColor(preview.event.color || DEFAULT_COLOR);
        setSelectedReminder(preview.event.reminder ?? DEFAULT_REMINDER);
        setShowParsedEvent(true);
        needsConflictCheck.current = true;
      } else if (preview?.kind === "bulk") {
        setParsedEvents(preview.events);
        setShowBulkEvents(true);
        needsConflictCheck.current = true;
      }
      previewHydrated.current = true;
      if (stored[PARSE_JOB_KEY]) {
        await consumeParseJob(stored[PARSE_JOB_KEY]);
      }
    } catch (error) {
      previewHydrated.current = true;
      console.error("Failed to restore saved work:", error);
    }
  };

  const clearParseJob = async () => {
    try {
      await chrome.storage.local.remove([PARSE_JOB_KEY]);
      await chrome.action.setBadgeText({ text: "" });
    } catch (error) {
      console.error("Failed to clear the finished parse:", error);
    }
  };

  const consumeParseJob = async (job) => {
    const state = parseJobState(job);
    if (state === "pending") {
      setLoadingSingle(true);
      setShowParsedEvent(false);
      setShowBulkEvents(false);
      return;
    }
    if (state === "none") return;
    setLoadingSingle(false);
    await clearParseJob();
    if (state === "done") {
      applyParseResponse(job.response);
    } else if (state === "stalled") {
      showMessage("Parsing was interrupted. Please try again.", "error");
    } else {
      showMessage(job.error || "Something went wrong reading that. Please try again.", "error");
    }
  };

  const applyParseResponse = (response) => {
    if (response?.is_bulk && response.parsed_events) {
      const normalizedEvents = response.parsed_events
        .map((event) => normalizeEventPayload(event))
        .filter(Boolean);
      setParsedEvents(normalizedEvents);
      setSelectedColor(DEFAULT_COLOR);
      setSelectedReminder(DEFAULT_REMINDER);
      setShowParsedEvent(false);
      setShowBulkEvents(true);
    } else if (response?.parsed_event) {
      const normalizedEvent = normalizeEventPayload(response.parsed_event);
      setParsedEvent(normalizedEvent);
      setSelectedColor(normalizedEvent?.color || DEFAULT_COLOR);
      setSelectedReminder(normalizedEvent?.reminder ?? DEFAULT_REMINDER);
      setShowBulkEvents(false);
      setShowParsedEvent(true);
    } else {
      showMessage("Failed to parse event", "error");
      return;
    }
    setConflicts([]);
    setBulkEventConflicts({});
    needsConflictCheck.current = true;
  };

  const toggleTheme = async () => {
    const newDarkMode = !darkMode;
    setDarkMode(newDarkMode);
    document.documentElement.classList.toggle("dark-mode", newDarkMode);
    await chrome.storage.local.set({ darkMode: newDarkMode });
  };

  const initializeUser = async () => {
    try {
      const result = await chrome.storage.local.get([
        "prompt2cal_user_id",
        "prompt2cal_auth_error",
      ]);
      // Only the backend issues sessions, at sign-in. IDs made up by older
      // versions of the extension are no longer accepted, so those users
      // connect their calendar again.
      let userIdValue = null;
      if (isIssuedSession(result.prompt2cal_user_id)) {
        userIdValue = result.prompt2cal_user_id;
      } else if (result.prompt2cal_user_id) {
        await chrome.storage.local.remove(["prompt2cal_user_id"]);
      }
      if (result.prompt2cal_auth_error) {
        showMessage(result.prompt2cal_auth_error, "error");
        await chrome.storage.local.remove(["prompt2cal_auth_error"]);
      }

      setUserId(userIdValue);
      await checkForSelectedText();

      // A sign-in still in progress keeps its button on "Connecting...", so the
      // connect buttons stay on screen rather than being hidden while waiting.
      const authenticated = await checkAuthStatus(userIdValue);
      if (authenticated) {
        const stored = await chrome.storage.local.get(["calendar_provider"]);
        await fetchCalendars(userIdValue, stored.calendar_provider || "google");
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

      // The background worker sends the request, so it keeps going if the
      // popup closes; the result comes back through storage.
      const reply = await chrome.runtime.sendMessage({
        action: "parseEvent",
        jobId: crypto.randomUUID(),
        apiBase: API_BASE,
        payload: {
          text,
          user_id: userId,
          timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
          force_multiple: forceMultiple,
        },
      });
      if (!reply?.started) {
        throw new Error(reply?.error || "Could not start parsing");
      }
    } catch (error) {
      console.error("Parse error:", error);
      showMessage(`Failed to parse event: ${error.message}`, "error");
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
  };

  const closeEditModal = () => {
    setEditingEventIndex(null);
    setEditingEvent(null);
    setEditingAttendees([]);
    setEditingAttendeeInput("");
    setSelectedColor(DEFAULT_COLOR);
    setSelectedReminder(DEFAULT_REMINDER);
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

  const handleEditSingleEvent = () => openSingleEditor(parsedEvent);

  const openSingleEditor = (source) => {
    const normalized = normalizeEventPayload(source);
    if (!normalized) return;

    const attendeeList = normalized.attendees || [];
    setSingleAttendees(attendeeList);
    setSingleAttendeeInput("");
    setSelectedColor(normalized.color || DEFAULT_COLOR);
    setSelectedReminder(normalized.reminder ?? DEFAULT_REMINDER);
    setEditedSingleEvent({ ...normalized });
    setShowEventEditForm(true);
  };

  // Functional update: the dialog changes several fields in one go (start and
  // end together), and each call must build on the one before it.
  const handleSingleEventFormChange = (field, value) => {
    setEditedSingleEvent((prev) => (prev ? { ...prev, [field]: value } : prev));
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
        const foundConflicts = response.conflicts || [];
        setConflicts(foundConflicts);
        if (foundConflicts.length > 0) {
          loadAlternatives(event);
        } else {
          setAlternatives([]);
        }
      }
    } catch (error) {
      console.error("Error checking conflicts:", error);
      // Don't show error to user - conflict checking is optional
    } finally {
      setCheckingConflicts(false);
    }
  };

  // When something clashes, offer the nearest free times rather than only
  // reporting the problem.
  const loadAlternatives = async (event) => {
    try {
      setLoadingAlternatives(true);
      setAlternatives([]);
      const response = await makeApiCall("/suggest_alternatives", {
        method: "POST",
        body: JSON.stringify({
          user_id: userId,
          start_time: event.start_time,
          end_time: event.end_time,
          duration_minutes: event.duration_minutes || 60,
          calendar_id: selectedCalendarId,
          calendar_provider: calendarProvider,
        }),
      });
      if (response.success) {
        setAlternatives(response.alternatives || []);
      }
    } catch (error) {
      console.error("Error loading alternatives:", error);
    } finally {
      setLoadingAlternatives(false);
    }
  };

  const handlePickAlternative = (slot) => {
    if (!parsedEvent) return;
    const moved = {
      ...parsedEvent,
      start_time: slot.start,
      end_time: slot.end,
      end_time_assumed: parsedEvent.end_time_assumed,
    };
    setParsedEvent(moved);
    setAlternatives([]);
    showMessage(`Moved to ${slot.formatted_time}`, "success");
    checkEventConflicts(moved);
  };

  const handleFindSlots = async ({ durationMinutes, days, includeWeekends, workingHours }) => {
    const now = new Date();
    // Midnight at the end of the last day, so "Today" stops at midnight
    // rather than running into tomorrow morning.
    const end = new Date(now);
    end.setHours(0, 0, 0, 0);
    end.setDate(end.getDate() + days);
    try {
      const response = await makeApiCall("/find_meeting_slots", {
        method: "POST",
        body: JSON.stringify({
          user_id: userId,
          start_date: now.toISOString(),
          end_date: end.toISOString(),
          duration_minutes: durationMinutes,
          working_hours: workingHours,
          buffer_minutes: 15,
          // Working hours are the user's, so the server needs their zone.
          timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
          include_weekends: Boolean(includeWeekends),
          calendar_id: selectedCalendarId,
          calendar_provider: calendarProvider,
        }),
      });
      if (!response.success) throw new Error("Slot search did not succeed");
      return response.available_slots || [];
    } catch (error) {
      console.error("Free slot search failed:", error);
      throw new Error(slotSearchErrorMessage(error, calendarProvider));
    }
  };

  const handlePickSlot = (slot) => {
    const draft = {
      title: "New event",
      start_time: slot.start,
      end_time: slot.end,
      duration_minutes: slot.duration_minutes,
      recurrence_type: "none",
      attendees: [],
      calendar_provider: calendarProvider,
    };
    setShowFindSlot(false);
    setParsedEvents([]);
    setShowBulkEvents(false);
    setParsedEvent(draft);
    setShowParsedEvent(true);
    setConflicts([]);
    setAlternatives([]);
    openSingleEditor(draft);
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
          {slotFinderAvailable && (
            <button
              type="button"
              className={`settings-button ${showFindSlot ? "active" : ""}`}
              onClick={() => setShowFindSlot(!showFindSlot)}
              title="Find a free time"
              aria-label="Find a free time"
              aria-pressed={showFindSlot}
            >
              <CalendarSearch size={18} />
            </button>
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

      {!isCheckingAuth && !isAuthenticated && (
        <AuthSection
          onGoogleAuth={handleGoogleAuth}
          onMicrosoftAuth={handleMicrosoftAuth}
          loadingAuth={loadingAuth}
          loadingMicrosoftAuth={loadingMicrosoftAuth}
        />
      )}

      <div className="main-section" id="mainSection">
        {showFindSlot ? (
          <FindSlotPanel
            onFindSlots={handleFindSlots}
            onPickSlot={handlePickSlot}
            onClose={() => setShowFindSlot(false)}
          />
        ) : (
        <>
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
            calendarProvider={calendarProvider}
            alternatives={alternatives}
            loadingAlternatives={loadingAlternatives}
            onPickAlternative={handlePickAlternative}
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
            onFieldChange={handleSingleEventFormChange}
            onSave={handleSaveSingleEdit}
            onCancel={handleCancelSingleEdit}
            loading={loading}
            calendarProvider={calendarProvider}
            categories={categories}
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
            calendarProvider={calendarProvider}
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
            onFieldChange={(field, value) => {
              setEditingEvent((prev) =>
                prev ? { ...prev, [field]: value } : prev
              );
            }}
            onSave={saveEditedEvent}
            onCancel={closeEditModal}
            loading={loading}
            calendarProvider={calendarProvider}
            categories={categories}
          />
        )}
        </>
        )}

        <ToastContainer toasts={toasts} onClose={removeToast} />
      </div>
    </div>
  );
};

export default Popup;
