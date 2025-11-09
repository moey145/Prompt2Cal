import React, { useState, useEffect, useRef } from "react";
import {
  Calendar,
  Sun,
  Moon,
  LogOut,
  Sparkles,
  Mic,
  Square,
  Check,
  X,
  List,
  Edit,
  SquarePen,
  Clock,
  MapPin,
  FileText,
  Repeat,
} from "lucide-react";

const API_BASE = "http://localhost:8000";

const Popup = () => {
  // State
  const [userId, setUserId] = useState(null);
  const [selectedText, setSelectedText] = useState("");
  const [parsedEvent, setParsedEvent] = useState(null);
  const [parsedEvents, setParsedEvents] = useState([]);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);
  const [isListening, setIsListening] = useState(false);
  const [message, setMessage] = useState("");
  const [messageType, setMessageType] = useState("info");
  const [eventInput, setEventInput] = useState("");
  const [selectedColor, setSelectedColor] = useState("#4285f4");
  const [selectedReminder, setSelectedReminder] = useState("none");
  const [editingStart, setEditingStart] = useState(false);
  const [editingEnd, setEditingEnd] = useState(false);
  const [showParsedEvent, setShowParsedEvent] = useState(false);
  const [showBulkEvents, setShowBulkEvents] = useState(false);
  const [showSelectedText, setShowSelectedText] = useState(false);
  const [loading, setLoading] = useState(false);
  const [loadingSingle, setLoadingSingle] = useState(false);
  const [loadingAuth, setLoadingAuth] = useState(false);
  const [editingEventIndex, setEditingEventIndex] = useState(null);
  const [editingEvent, setEditingEvent] = useState(null);
  const [showEventEditForm, setShowEventEditForm] = useState(false);
  const [editedSingleEvent, setEditedSingleEvent] = useState(null);
  const [darkMode, setDarkMode] = useState(false);

  // Refs
  const recognitionRef = useRef(null);
  const originalTextRef = useRef("");
  const silenceTimeoutRef = useRef(null);

  // Initialize on mount
  useEffect(() => {
    initializeUser();
    loadThemeFromStorage();
    // eslint-disable-next-line
  }, []);

  const loadThemeFromStorage = async () => {
    const result = await chrome.storage.local.get(["darkMode"]);
    if (result.darkMode) {
      setDarkMode(result.darkMode);
      document.documentElement.classList.add("dark-mode");
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
      // Generate or get existing user ID
      const result = await chrome.storage.local.get(["prompt2cal_user_id"]);
      let userIdValue;

      if (result.prompt2cal_user_id) {
        userIdValue = result.prompt2cal_user_id;
      } else {
        userIdValue = "user_" + Math.random().toString(36).substr(2, 9);
        await chrome.storage.local.set({ prompt2cal_user_id: userIdValue });
      }

      setUserId(userIdValue);

      // Check for selected text from content script
      await checkForSelectedText();

      // Check if we were waiting for auth completion
      const authState = await chrome.storage.local.get(["waitingForAuth"]);
      if (authState.waitingForAuth) {
        await chrome.storage.local.remove(["waitingForAuth"]);
        setTimeout(async () => {
          await checkAuthStatus(userIdValue);
        }, 500);
      } else {
        await checkAuthStatus(userIdValue);
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
      // Content script might not be loaded, that's ok
      console.log("Error getting selected text:", error);
    }
  };

  const checkAuthStatus = async (userIdValue) => {
    try {
      const response = await makeApiCall("/auth/status", {
        method: "GET",
        params: { user_id: userIdValue || userId },
      });

      setIsAuthenticated(response.authenticated);
    } catch (error) {
      console.error("Auth check failed:", error);
      setIsAuthenticated(false);
      showMessage(
        "Backend server not running. Please start the backend first.",
        "error"
      );
    } finally {
      setIsCheckingAuth(false);
    }
  };

  const handleGoogleAuth = async () => {
    if (loadingAuth) return;

    try {
      setLoadingAuth(true);

      const response = await makeApiCall("/auth/google", {
        method: "GET",
        params: { user_id: userId },
      });

      await chrome.storage.local.set({ waitingForAuth: true });
      await chrome.tabs.create({ url: response.auth_url });
      window.close();
    } catch (error) {
      console.error("Auth error:", error);
      showMessage(`Authentication error: ${error.message}`, "error");
    } finally {
      setLoadingAuth(false);
    }
  };

  const handleLogout = async () => {
    if (loading) return;

    if (
      !confirm(
        "Are you sure you want to logout? You'll need to reconnect your Google Calendar."
      )
    ) {
      return;
    }

    try {
      setLoading(true);

      const response = await makeApiCall("/auth/logout", {
        method: "POST",
        params: { user_id: userId },
      });

      if (response.success) {
        showMessage("Successfully logged out", "success");
        setIsAuthenticated(false);
      } else {
        showMessage("Logout failed: " + response.message, "error");
      }
    } catch (error) {
      console.error("Logout error:", error);
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
      // Use a single loading state
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
          setParsedEvents(response.parsed_events);
          setShowBulkEvents(true);
          showMessage(response.message, "success");
        } else {
          setParsedEvent(response.parsed_event);
          setShowParsedEvent(true);
          showMessage(response.message, "success");
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
    if (!parsedEvent || loading) return;
    if (!isAuthenticated) {
      showMessage(
        "Please connect your Google Calendar to create events",
        "error"
      );
      return;
    }

    try {
      setLoading(true);

      const eventWithColor = {
        ...parsedEvent,
        color: selectedColor,
        reminder: selectedReminder,
      };

      const response = await makeApiCall("/confirm_event", {
        method: "POST",
        params: { user_id: userId },
        body: JSON.stringify(eventWithColor),
      });

      showMessage(
        `✅ Event created! ${
          response.event_link ? `View: ${response.event_link}` : ""
        }`,
        "success"
      );

      resetForm();
    } catch (error) {
      console.error("Create event error:", error);
      showMessage(`Failed to create event: ${error.message}`, "error");
    } finally {
      setLoading(false);
    }
  };

  const handleCreateAllEvents = async () => {
    if (!parsedEvents || parsedEvents.length === 0 || loading) {
      showMessage("No events to create", "error");
      return;
    }
    if (!isAuthenticated) {
      showMessage(
        "Please connect your Google Calendar to create events",
        "error"
      );
      return;
    }

    try {
      setLoading(true);

      const eventsWithColor = parsedEvents.map((event) => ({
        ...event,
        color: event.color || "#4285f4",
        reminder: selectedReminder,
      }));

      const response = await makeApiCall("/confirm_bulk_events", {
        method: "POST",
        params: { user_id: userId },
        body: JSON.stringify(eventsWithColor),
      });

      if (response.success) {
        showMessage(
          `✅ Created ${response.total_created || parsedEvents.length} events!`,
          "success"
        );
        setShowBulkEvents(false);
        setEventInput("");
      } else {
        showMessage("Failed to create events", "error");
      }
    } catch (error) {
      showMessage(`Error: ${error.message}`, "error");
    } finally {
      setLoading(false);
    }
  };

  const removeParsedEvent = (idx) => {
    setParsedEvents((prev) => prev.filter((_, i) => i !== idx));
  };

  const openEditModal = (index) => {
    setEditingEventIndex(index);
    setEditingEvent({ ...parsedEvents[index] });
    setSelectedColor(parsedEvents[index].color || "#4285f4");
    setSelectedReminder("none");
    setEditingStart(false);
    setEditingEnd(false);
  };

  const closeEditModal = () => {
    setEditingEventIndex(null);
    setEditingEvent(null);
    setSelectedColor("#4285f4");
    setSelectedReminder("none");
  };

  const saveEditedEvent = () => {
    if (editingEventIndex !== null && editingEvent) {
      setParsedEvents((prev) =>
        prev.map((ev, i) =>
          i === editingEventIndex
            ? {
                ...editingEvent,
                color: selectedColor,
                reminder: selectedReminder,
              }
            : ev
        )
      );
      closeEditModal();
    }
  };

  const resetForm = () => {
    setEventInput("");
    setParsedEvent(null);
    setParsedEvents([]);
    setShowParsedEvent(false);
    setShowBulkEvents(false);
    setShowSelectedText(false);
    setSelectedText("");
    setMessage("");
  };

  const toggleVoiceRecognition = async () => {
    if (
      !("webkitSpeechRecognition" in window || "SpeechRecognition" in window)
    ) {
      showMessage("❌ Voice recognition not supported", "error");
      return;
    }

    if (isListening) {
      stopVoiceRecognition();
    } else {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          audio: true,
        });
        stream.getTracks().forEach((track) => track.stop());

        startVoiceRecognition();
      } catch (error) {
        console.error("Microphone permission error:", error);
        showMessage(
          "❌ Microphone permission denied. Please allow microphone access in your browser settings.",
          "error"
        );
      }
    }
  };

  const startVoiceRecognition = () => {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();

    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = "en-US";
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
      setIsListening(true);
      originalTextRef.current = eventInput;
    };

    recognition.onresult = (event) => {
      let interimTranscript = "";
      let finalTranscript = "";

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          finalTranscript += transcript;
        } else {
          interimTranscript += transcript;
        }
      }

      if (finalTranscript) {
        const newText =
          originalTextRef.current +
          (originalTextRef.current ? " " : "") +
          finalTranscript.trim();
        setEventInput(newText);
        originalTextRef.current = newText;

        // After getting final transcript, stop listening after 2 seconds of silence
        if (silenceTimeoutRef.current) {
          clearTimeout(silenceTimeoutRef.current);
        }
        silenceTimeoutRef.current = setTimeout(() => {
          stopVoiceRecognition();
        }, 2000);
      } else if (interimTranscript) {
        const newText =
          originalTextRef.current +
          (originalTextRef.current ? " " : "") +
          interimTranscript.trim();
        setEventInput(newText);

        // Reset silence timeout on interim transcript - extend it
        if (silenceTimeoutRef.current) {
          clearTimeout(silenceTimeoutRef.current);
        }
        silenceTimeoutRef.current = setTimeout(() => {
          stopVoiceRecognition();
        }, 2000);
      }
    };

    recognition.onend = () => {
      setIsListening(false);
      if (silenceTimeoutRef.current) {
        clearTimeout(silenceTimeoutRef.current);
      }
      // Don't automatically restart - user can click button again
      if (eventInput.trim()) {
        setMessage("");
      }
    };

    recognition.onerror = (event) => {
      setIsListening(false);
      if (silenceTimeoutRef.current) {
        clearTimeout(silenceTimeoutRef.current);
      }

      let errorMessage = "Voice recognition error";
      switch (event.error) {
        case "no-speech":
          errorMessage = "No speech detected. Please try again.";
          break;
        case "audio-capture":
          errorMessage = "No microphone found. Please check your microphone.";
          break;
        case "not-allowed":
          errorMessage =
            "Microphone permission denied. Please allow microphone access.";
          break;
        case "network":
          errorMessage = "Network error. Please check your connection.";
          break;
        case "aborted":
          return;
        default:
          errorMessage = `Voice recognition error: ${event.error}`;
      }

      showMessage(`❌ ${errorMessage}`, "error");
    };

    recognition.start();
    recognitionRef.current = recognition;
  };

  const stopVoiceRecognition = () => {
    if (recognitionRef.current) {
      if (silenceTimeoutRef.current) {
        clearTimeout(silenceTimeoutRef.current);
      }
      try {
        recognitionRef.current.stop();
      } catch (e) {
        // Recognition might already be stopped
      }
      setIsListening(false);
    }
  };

  const makeApiCall = async (endpoint, options = {}) => {
    const url = `${API_BASE}${endpoint}`;

    const defaultOptions = {
      headers: {
        "Content-Type": "application/json",
      },
    };

    const finalOptions = { ...defaultOptions, ...options };

    if (finalOptions.params) {
      const params = new URLSearchParams(finalOptions.params);
      const paramString = params.toString();
      const fullUrl = paramString ? `${url}?${paramString}` : url;
      delete finalOptions.params;

      const response = await fetch(fullUrl, finalOptions);
      return await handleResponse(response);
    }

    const response = await fetch(url, finalOptions);
    return await handleResponse(response);
  };

  const handleResponse = async (response) => {
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(
        errorData.detail || `HTTP ${response.status}: ${response.statusText}`
      );
    }

    return await response.json();
  };

  const showMessage = (text, type = "info") => {
    setMessage(text);
    setMessageType(type);

    setTimeout(() => {
      setMessage("");
    }, 5000);
  };

  const formatDateTime = (dateTimeString) => {
    if (!dateTimeString) return "Not specified";

    try {
      const date = new Date(dateTimeString);
      return date.toLocaleString("en-US", {
        weekday: "short",
        month: "short",
        day: "numeric",
        hour: "numeric",
        minute: "2-digit",
        hour12: true,
      });
    } catch (error) {
      return dateTimeString;
    }
  };

  const toDateTimeLocal = (date) => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    const hours = String(date.getHours()).padStart(2, "0");
    const minutes = String(date.getMinutes()).padStart(2, "0");
    return `${year}-${month}-${day}T${hours}:${minutes}`;
  };

  const formatDateTimeShort = (isoString) => {
    if (!isoString) return "";
    const date = new Date(isoString);
    const options = {
      weekday: "short",
      month: "short",
      day: "numeric",
      year: "numeric",
    };
    return date.toLocaleString("en-US", options);
  };

  const formatTimeShort = (isoString) => {
    if (!isoString) return "";
    const date = new Date(isoString);
    const options = { hour: "numeric", minute: "2-digit" };
    return date.toLocaleString("en-US", options);
  };

  const getRecurrenceDescription = (event) => {
    if (!event || !event.recurrence_type || event.recurrence_type === "none") {
      return null;
    }

    const recurrenceType = event.recurrence_type.toLowerCase();
    const interval = event.recurrence_interval || 1;
    const count = event.recurrence_count;
    const startTime = event.start_time;

    // Get day of week if it's a weekly event
    let dayOfWeek = null;
    if (recurrenceType === "weekly" && startTime) {
      try {
        const date = new Date(startTime);
        const days = [
          "Sunday",
          "Monday",
          "Tuesday",
          "Wednesday",
          "Thursday",
          "Friday",
          "Saturday",
        ];
        dayOfWeek = days[date.getDay()];
      } catch (e) {
        // Ignore parsing errors
      }
    }

    // Build the description
    let description = "";

    // Handle interval
    if (interval > 1) {
      if (recurrenceType === "weekly") {
        description = `Every ${interval === 2 ? "other" : interval} week`;
      } else if (recurrenceType === "daily") {
        description = `Every ${interval === 2 ? "other" : interval} day`;
      } else if (recurrenceType === "monthly") {
        description = `Every ${interval === 2 ? "other" : interval} month`;
      } else if (recurrenceType === "yearly") {
        description = `Every ${interval === 2 ? "other" : interval} year`;
      }
    } else {
      // Standard recurrence
      if (recurrenceType === "daily") {
        description = "Daily";
      } else if (recurrenceType === "weekly") {
        description = "Weekly";
      } else if (recurrenceType === "monthly") {
        description = "Monthly";
      } else if (recurrenceType === "yearly") {
        description = "Yearly";
      }
    }

    // Add event title
    if (event.title) {
      description += ` ${event.title.toLowerCase()}`;
    }

    // Add day of week for weekly events (after title for natural flow)
    if (dayOfWeek && recurrenceType === "weekly") {
      description += ` on ${dayOfWeek}`;
    }

    return description;
  };

  const handleEditSingleEvent = () => {
    setShowEventEditForm(true);
    setEditedSingleEvent({ ...parsedEvent });
  };

  const handleSingleEventFormChange = (field, value) => {
    setEditedSingleEvent({ ...editedSingleEvent, [field]: value });
  };

  const handleSaveSingleEdit = () => {
    setParsedEvent(editedSingleEvent);
    setShowEventEditForm(false);
    setEditedSingleEvent(null);
  };

  const handleCancelSingleEdit = () => {
    setShowEventEditForm(false);
    setEditedSingleEvent(null);
  };

  return (
    <div className="container">
      <div className="header">
        <button
          id="themeToggle"
          className="theme-toggle"
          onClick={toggleTheme}
          title={darkMode ? "Switch to light mode" : "Switch to dark mode"}
        >
          {darkMode ? <Moon size={20} /> : <Sun size={20} />}
        </button>
        {isAuthenticated && (
          <button
            id="logoutButton"
            className="logout-button"
            onClick={handleLogout}
            title="Logout"
          >
            Logout
          </button>
        )}
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
        <div className="auth-section" id="authSection">
          <button
            id="authButton"
            className="auth-button"
            onClick={handleGoogleAuth}
            disabled={loadingAuth}
          >
            {loadingAuth ? (
              <>
                <div className="dots-spinner">
                  <div></div>
                  <div></div>
                  <div></div>
                  <div></div>
                </div>{" "}
                Connecting...
              </>
            ) : (
              <>
                <Calendar size={18} /> Connect Google Calendar
              </>
            )}
          </button>
        </div>
      )}

      <div className="main-section" id="mainSection">
        <div className="event-card">
          <label htmlFor="eventInput" className="input-label">
            <Sparkles size={18} className="inline-icon" /> Describe your event:
          </label>
          <div className="input-container">
            <textarea
              id="eventInput"
              placeholder="Type your event in plain language..."
              rows="5"
              value={eventInput}
              onChange={(e) => setEventInput(e.target.value)}
            />
            <button
              id="voiceButton"
              className={`voice-button ${isListening ? "listening" : ""}`}
              title={isListening ? "Stop listening" : "Click to speak"}
              onClick={toggleVoiceRecognition}
            >
              {isListening ? <Square size={20} /> : <Mic size={22} />}
            </button>
          </div>
          <div className="action-buttons-main">
            <button
              id="parseEventButton"
              className="action-button action-single"
              onClick={() => handleParseEvent(null)}
              disabled={loadingSingle || !eventInput.trim()}
              title="Parse event (auto-detects single or multiple)"
            >
              {loadingSingle ? (
                <>
                  <div className="dots-spinner">
                    <div></div>
                    <div></div>
                    <div></div>
                    <div></div>
                  </div>{" "}
                  Parsing...
                </>
              ) : (
                <>
                  <Sparkles size={18} className="inline-icon" /> Parse Event
                </>
              )}
            </button>
          </div>
        </div>

        {showSelectedText && (
          <div className="selected-text-section">
            <div className="selected-text-label">Selected text:</div>
            <div className="selected-text">{selectedText}</div>
            <button
              className="use-selected-button"
              onClick={() => {
                setEventInput(selectedText);
                setShowSelectedText(false);
              }}
            >
              📝 Use Selected Text
            </button>
          </div>
        )}

        {showParsedEvent && parsedEvent && (
          <div className="event-card-confirm">
            <div className="event-card-header-confirm">
              <div className="event-card-header-left-confirm">
                <Calendar className="event-card-icon-confirm" />
                {parsedEvent.recurrence_type &&
                parsedEvent.recurrence_type !== "none" ? (
                  <h3>Confirm Recurring Event</h3>
                ) : (
                  <h3>Confirm Event</h3>
                )}
              </div>
            </div>
            <div className="event-card-content-confirm">
              <div className="event-title-row-confirm">
                <div className="event-title-confirm">{parsedEvent.title}</div>
                <button
                  className="edit-button-confirm"
                  onClick={handleEditSingleEvent}
                  title="Edit event"
                >
                  <SquarePen size={18} />
                </button>
              </div>
              {parsedEvent.recurrence_type &&
                parsedEvent.recurrence_type !== "none" && (
                  <div className="recurrence-badge">
                    <Repeat size={14} />
                    <span>
                      {parsedEvent.recurrence_type.charAt(0).toUpperCase() +
                        parsedEvent.recurrence_type.slice(1)}
                      {parsedEvent.recurrence_count
                        ? ` (${parsedEvent.recurrence_count}x)`
                        : ""}
                    </span>
                  </div>
                )}
              <div className="event-time-row-confirm">
                <Clock className="event-time-icon-confirm" />
                <div className="event-time-info-confirm">
                  <div className="event-date-confirm">
                    {parsedEvent.recurrence_type &&
                    parsedEvent.recurrence_type !== "none" ? (
                      <>
                        <span style={{ fontSize: "0.85em", opacity: 0.8, marginRight: "4px" }}>
                          Starting from:{" "}
                        </span>
                        {formatDateTimeShort(parsedEvent.start_time)}
                      </>
                    ) : (
                      formatDateTimeShort(parsedEvent.start_time)
                    )}
                  </div>
                  <div className="event-time-range-confirm">
                    {formatTimeShort(parsedEvent.start_time)} -{" "}
                    {formatTimeShort(parsedEvent.end_time)}
                  </div>
                </div>
              </div>
              {parsedEvent.location && (
                <div className="event-time-row-confirm">
                  <MapPin className="event-time-icon-confirm" />
                  <div className="event-location-info-confirm">
                    {parsedEvent.location}
                  </div>
                </div>
              )}
              {parsedEvent.notes && (
                <div className="event-time-row-confirm">
                  <FileText className="event-time-icon-confirm" />
                  <div className="event-location-info-confirm">
                    {parsedEvent.notes}
                  </div>
                </div>
              )}
            </div>
            <div className="action-buttons">
              <button
                className="create-button"
                onClick={handleCreateEvent}
                disabled={loading}
              >
                <Check size={16} className="inline-icon" /> Create Event
              </button>
              <button
                className="cancel-button"
                onClick={() => setShowParsedEvent(false)}
                disabled={loading}
              >
                <X size={16} className="inline-icon" /> Cancel
              </button>
            </div>
          </div>
        )}

        {showEventEditForm && editedSingleEvent && (
          <div className="modal-overlay" onClick={handleCancelSingleEdit}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <div className="parsed-event">
                <div className="event-details">
                  <h3>
                    <Edit size={20} className="inline-icon" /> Edit Event
                  </h3>
                  <div className="detail-row editable-row">
                    <strong>Title:</strong>
                    <input
                      className="text-input"
                      type="text"
                      value={editedSingleEvent.title || ""}
                      onChange={(e) =>
                        handleSingleEventFormChange("title", e.target.value)
                      }
                    />
                  </div>
                  <div className="detail-row editable-row">
                    <strong>Start:</strong>
                    {editingStart ? (
                      <input
                        type="datetime-local"
                        className="datetime-input"
                        value={toDateTimeLocal(
                          new Date(editedSingleEvent.start_time)
                        )}
                        onChange={(e) => {
                          const d = new Date(e.target.value);
                          if (!isNaN(d.getTime())) {
                            const duration =
                              editedSingleEvent.duration_minutes || 60;
                            const endDate = new Date(
                              d.getTime() + duration * 60000
                            );
                            handleSingleEventFormChange(
                              "start_time",
                              d.toISOString()
                            );
                            handleSingleEventFormChange(
                              "end_time",
                              endDate.toISOString()
                            );
                          }
                        }}
                        onBlur={() => setEditingStart(false)}
                      />
                    ) : (
                      <span
                        className="editable-field clickable"
                        onClick={() => setEditingStart(true)}
                      >
                        {formatDateTime(editedSingleEvent.start_time)}
                      </span>
                    )}
                  </div>
                  <div className="detail-row editable-row">
                    <strong>End:</strong>
                    {editingEnd ? (
                      <input
                        type="datetime-local"
                        className="datetime-input"
                        value={toDateTimeLocal(
                          new Date(editedSingleEvent.end_time)
                        )}
                        onChange={(e) => {
                          const d = new Date(e.target.value);
                          if (!isNaN(d.getTime())) {
                            handleSingleEventFormChange(
                              "end_time",
                              d.toISOString()
                            );
                          }
                        }}
                        onBlur={() => setEditingEnd(false)}
                      />
                    ) : (
                      <span
                        className="editable-field clickable"
                        onClick={() => setEditingEnd(true)}
                      >
                        {formatDateTime(editedSingleEvent.end_time)}
                      </span>
                    )}
                  </div>
                  <div className="detail-row editable-row">
                    <strong>Location:</strong>
                    <input
                      className="text-input"
                      type="text"
                      value={editedSingleEvent.location || ""}
                      onChange={(e) =>
                        handleSingleEventFormChange("location", e.target.value)
                      }
                    />
                  </div>
                  <div className="detail-row editable-row">
                    <strong>Notes:</strong>
                    <textarea
                      className="text-input"
                      rows="2"
                      value={editedSingleEvent.notes || ""}
                      onChange={(e) =>
                        handleSingleEventFormChange("notes", e.target.value)
                      }
                    />
                  </div>
                  <div className="detail-row">
                    <strong>Color:</strong>
                    <div className="color-presets">
                      {[
                        "#4285f4",
                        "#ea4335",
                        "#fbbc04",
                        "#34a853",
                        "#9c27b0",
                        "#ff9800",
                        "#795548",
                        "#607d8b",
                      ].map((c) => (
                        <div
                          key={c}
                          className={`color-preset ${
                            selectedColor === c ? "selected" : ""
                          }`}
                          style={{ backgroundColor: c }}
                          onClick={() => setSelectedColor(c)}
                        />
                      ))}
                    </div>
                  </div>
                  <div className="detail-row">
                    <strong>Reminders:</strong>
                    <div className="reminder-controls">
                      <select
                        className="reminder-select"
                        value={selectedReminder}
                        onChange={(e) => setSelectedReminder(e.target.value)}
                      >
                        <option value="none">No reminder</option>
                        <option value="5">5 minutes before</option>
                        <option value="10">10 minutes before</option>
                        <option value="15">15 minutes before</option>
                        <option value="30">30 minutes before</option>
                        <option value="60">1 hour before</option>
                        <option value="120">2 hours before</option>
                        <option value="1440">1 day before</option>
                        <option value="2880">2 days before</option>
                      </select>
                    </div>
                  </div>
                </div>

                <div className="action-buttons">
                  <button
                    className="create-button"
                    onClick={handleSaveSingleEdit}
                    disabled={loading}
                  >
                    <Check size={16} className="inline-icon" /> Save Changes
                  </button>
                  <button
                    className="cancel-button"
                    onClick={handleCancelSingleEdit}
                    disabled={loading}
                  >
                    <X size={16} className="inline-icon" /> Cancel
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {showBulkEvents && parsedEvents.length > 0 && (
          <div className="event-card-confirm">
            <div className="event-card-header-confirm">
              <div className="event-card-header-left-confirm">
                <Calendar className="event-card-icon-confirm" />
                {(() => {
                  const recurringCount = parsedEvents.filter(
                    (e) => e.recurrence_type && e.recurrence_type !== "none"
                  ).length;
                  if (
                    recurringCount === parsedEvents.length &&
                    recurringCount > 0
                  ) {
                    return (
                      <h3>Confirm {parsedEvents.length} Recurring Events</h3>
                    );
                  } else if (recurringCount > 0) {
                    return (
                      <h3>
                        Confirm {parsedEvents.length} Events ({recurringCount}{" "}
                        Recurring)
                      </h3>
                    );
                  } else {
                    return <h3>Confirm {parsedEvents.length} Events</h3>;
                  }
                })()}
              </div>
            </div>
            <div className="events-list-confirm">
              {parsedEvents.map((event, index) => (
                <div key={index} className="event-item-confirm">
                  <div className="event-title-row-confirm">
                    <div className="event-title-confirm">{event.title}</div>
                    <div className="event-item-controls-confirm">
                      <button
                        className="edit-button-confirm"
                        title="Edit"
                        onClick={(e) => {
                          e.stopPropagation();
                          openEditModal(index);
                        }}
                      >
                        <SquarePen size={18} />
                      </button>
                      <button
                        className="remove-event-confirm"
                        title="Remove"
                        onClick={() => removeParsedEvent(index)}
                      >
                        <X size={18} />
                      </button>
                    </div>
                  </div>
                  {event.recurrence_type &&
                    event.recurrence_type !== "none" && (
                      <div className="recurrence-badge">
                        <Repeat size={14} />
                        <span>
                          {event.recurrence_type.charAt(0).toUpperCase() +
                            event.recurrence_type.slice(1)}
                          {event.recurrence_count
                            ? ` (${event.recurrence_count}x)`
                            : ""}
                        </span>
                      </div>
                    )}
                  <div className="event-time-row-confirm">
                    <Clock className="event-time-icon-confirm" />
                    <div className="event-time-info-confirm">
                      <div className="event-date-confirm">
                        {event.recurrence_type &&
                        event.recurrence_type !== "none" ? (
                          <>
                            <span style={{ fontSize: "0.85em", opacity: 0.8, marginRight: "4px" }}>
                              Starting from:{" "}
                            </span>
                            {formatDateTimeShort(event.start_time)}
                          </>
                        ) : (
                          formatDateTimeShort(event.start_time)
                        )}
                      </div>
                      <div className="event-time-range-confirm">
                        {formatTimeShort(event.start_time)} -{" "}
                        {formatTimeShort(event.end_time)}
                      </div>
                    </div>
                  </div>
                  {event.location && (
                    <div className="event-time-row-confirm">
                      <MapPin className="event-time-icon-confirm" />
                      <div className="event-location-info-confirm">
                        {event.location}
                      </div>
                    </div>
                  )}
                  {event.notes && (
                    <div className="event-time-row-confirm">
                      <FileText className="event-time-icon-confirm" />
                      <div className="event-location-info-confirm">
                        {event.notes}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>

            <div className="action-buttons">
              <button
                className="create-button"
                onClick={handleCreateAllEvents}
                disabled={loading}
              >
                <Check size={16} className="inline-icon" /> Create All Events
              </button>
              <button
                className="cancel-button"
                onClick={() => setShowBulkEvents(false)}
                disabled={loading}
              >
                <X size={16} className="inline-icon" /> Cancel
              </button>
            </div>
          </div>
        )}

        {editingEvent && editingEventIndex !== null && (
          <div className="modal-overlay" onClick={closeEditModal}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <div className="parsed-event">
                <div className="event-details">
                  <h3>
                    <Edit size={20} className="inline-icon" /> Edit Event
                  </h3>
                  <div className="detail-row editable-row">
                    <strong>Title:</strong>
                    <input
                      className="text-input"
                      type="text"
                      value={editingEvent.title || ""}
                      onChange={(e) =>
                        setEditingEvent({
                          ...editingEvent,
                          title: e.target.value,
                        })
                      }
                    />
                  </div>
                  <div className="detail-row editable-row">
                    <strong>Start:</strong>
                    {editingStart ? (
                      <input
                        type="datetime-local"
                        className="datetime-input"
                        value={toDateTimeLocal(
                          new Date(editingEvent.start_time)
                        )}
                        onChange={(e) => {
                          const d = new Date(e.target.value);
                          if (!isNaN(d.getTime())) {
                            const duration =
                              editingEvent.duration_minutes || 60;
                            const endDate = new Date(
                              d.getTime() + duration * 60000
                            );
                            setEditingEvent({
                              ...editingEvent,
                              start_time: d.toISOString(),
                              end_time: endDate.toISOString(),
                            });
                          }
                        }}
                        onBlur={() => setEditingStart(false)}
                      />
                    ) : (
                      <span
                        className="editable-field clickable"
                        onClick={() => setEditingStart(true)}
                      >
                        {formatDateTime(editingEvent.start_time)}
                      </span>
                    )}
                  </div>
                  <div className="detail-row editable-row">
                    <strong>End:</strong>
                    {editingEnd ? (
                      <input
                        type="datetime-local"
                        className="datetime-input"
                        value={toDateTimeLocal(new Date(editingEvent.end_time))}
                        onChange={(e) => {
                          const d = new Date(e.target.value);
                          if (!isNaN(d.getTime())) {
                            setEditingEvent({
                              ...editingEvent,
                              end_time: d.toISOString(),
                            });
                          }
                        }}
                        onBlur={() => setEditingEnd(false)}
                      />
                    ) : (
                      <span
                        className="editable-field clickable"
                        onClick={() => setEditingEnd(true)}
                      >
                        {formatDateTime(editingEvent.end_time)}
                      </span>
                    )}
                  </div>
                  <div className="detail-row editable-row">
                    <strong>Location:</strong>
                    <input
                      className="text-input"
                      type="text"
                      value={editingEvent.location || ""}
                      onChange={(e) =>
                        setEditingEvent({
                          ...editingEvent,
                          location: e.target.value,
                        })
                      }
                    />
                  </div>
                  <div className="detail-row editable-row">
                    <strong>Notes:</strong>
                    <textarea
                      className="text-input"
                      rows="2"
                      value={editingEvent.notes || ""}
                      onChange={(e) =>
                        setEditingEvent({
                          ...editingEvent,
                          notes: e.target.value,
                        })
                      }
                    />
                  </div>
                  <div className="detail-row">
                    <strong>Color:</strong>
                    <div className="color-presets">
                      {[
                        "#4285f4",
                        "#ea4335",
                        "#fbbc04",
                        "#34a853",
                        "#9c27b0",
                        "#ff9800",
                        "#795548",
                        "#607d8b",
                      ].map((c) => (
                        <div
                          key={c}
                          className={`color-preset ${
                            selectedColor === c ? "selected" : ""
                          }`}
                          style={{ backgroundColor: c }}
                          onClick={() => setSelectedColor(c)}
                        />
                      ))}
                    </div>
                  </div>
                  <div className="detail-row">
                    <strong>Reminders:</strong>
                    <div className="reminder-controls">
                      <select
                        className="reminder-select"
                        value={selectedReminder}
                        onChange={(e) => setSelectedReminder(e.target.value)}
                      >
                        <option value="none">No reminder</option>
                        <option value="5">5 minutes before</option>
                        <option value="10">10 minutes before</option>
                        <option value="15">15 minutes before</option>
                        <option value="30">30 minutes before</option>
                        <option value="60">1 hour before</option>
                        <option value="120">2 hours before</option>
                        <option value="1440">1 day before</option>
                        <option value="2880">2 days before</option>
                      </select>
                    </div>
                  </div>
                </div>

                <div className="action-buttons">
                  <button className="create-button" onClick={saveEditedEvent}>
                    <Check size={16} className="inline-icon" /> Save Changes
                  </button>
                  <button className="cancel-button" onClick={closeEditModal}>
                    <X size={16} className="inline-icon" /> Cancel
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {message && <div className={`message ${messageType}`}>{message}</div>}
      </div>
    </div>
  );
};

export default Popup;
