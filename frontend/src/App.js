import React, { useState, useEffect } from "react";
import axios from "axios";
import {
  Calendar,
  CalendarCheck,
  CheckCircle,
  Lock,
  Mic,
  StopCircle,
  Sparkles,
  CalendarDays,
  FileText,
  FolderOpen,
  X,
  PartyPopper,
  MapPin,
  Lightbulb,
  Hourglass,
  ClipboardList,
  Pencil,
  Clock,
  Moon,
  Sun,
} from "lucide-react";
import "./App.css";

function App() {
  const [inputText, setInputText] = useState("");
  const [parsedEvent, setParsedEvent] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [eventLink, setEventLink] = useState("");
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [speechSupported, setSpeechSupported] = useState(false);
  const [bulkEvents, setBulkEvents] = useState([]);
  const [showBulkSection, setShowBulkSection] = useState(false);
  const [fileImportMode, setFileImportMode] = useState(false);
  const [showEditForm, setShowEditForm] = useState(false);
  const [editedEvent, setEditedEvent] = useState(null);
  const [darkMode, setDarkMode] = useState(() => {
    const saved = localStorage.getItem("darkMode");
    return saved ? JSON.parse(saved) : false;
  });

  // Check authentication status on component mount
  useEffect(() => {
    checkAuthStatus();
    handleAuthCallback();
    checkSpeechSupport();
    // Initialize dark mode on mount
    const savedDarkMode = localStorage.getItem("darkMode");
    const isDarkMode = savedDarkMode ? JSON.parse(savedDarkMode) : false;
    if (isDarkMode) {
      document.documentElement.classList.add("dark-mode");
    } else {
      document.documentElement.classList.remove("dark-mode");
    }
  }, []);

  // Apply dark mode to document when it changes
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add("dark-mode");
    } else {
      document.documentElement.classList.remove("dark-mode");
    }
    localStorage.setItem("darkMode", JSON.stringify(darkMode));
  }, [darkMode]);

  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
  };

  const checkSpeechSupport = () => {
    if ("webkitSpeechRecognition" in window || "SpeechRecognition" in window) {
      setSpeechSupported(true);
    }
  };

  const handleAuthCallback = () => {
    // Check for authentication callback parameters in URL
    const urlParams = new URLSearchParams(window.location.search);
    const authStatus = urlParams.get("auth");
    const message = urlParams.get("message");

    if (authStatus === "success") {
      setMessage(decodeURIComponent(message || "Authentication successful!"));
      setIsAuthenticated(true);
      // Clean up URL parameters
      window.history.replaceState({}, document.title, window.location.pathname);
    } else if (authStatus === "error") {
      setMessage(decodeURIComponent(message || "Authentication failed!"));
      setIsAuthenticated(false);
      // Clean up URL parameters
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  };

  const checkAuthStatus = async () => {
    try {
      const response = await axios.get("/auth/status");
      setIsAuthenticated(response.data.authenticated);
    } catch (error) {
      console.error("Error checking auth status:", error);
      setIsAuthenticated(false);
    }
  };

  const handleInputChange = (e) => {
    setInputText(e.target.value);
  };

  const startVoiceInput = () => {
    if (!speechSupported) {
      setMessage("Voice input is not supported in this browser");
      return;
    }

    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();

    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = "en-US";

    recognition.onstart = () => {
      setIsListening(true);
      setMessage("Listening... Speak now!");
    };

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      setInputText(transcript);
      setMessage("Voice input received!");
    };

    recognition.onerror = (event) => {
      setMessage(`Voice input error: ${event.error}`);
      setIsListening(false);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognition.start();
  };

  const stopVoiceInput = () => {
    setIsListening(false);
    setMessage("");
  };

  const handleBulkEventParse = async () => {
    if (!inputText.trim()) {
      setMessage("Please enter some text to parse");
      return;
    }

    setLoading(true);
    setMessage("");
    setBulkEvents([]);

    try {
      const response = await axios.post("/create_bulk_events", {
        text: inputText,
      });

      if (response.data.success) {
        setBulkEvents(response.data.parsed_events);
        setMessage(response.data.message);
        setShowBulkSection(true);
      } else {
        setMessage("Failed to parse bulk events");
      }
    } catch (error) {
      setMessage(`Error: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleBulkEventConfirm = async () => {
    if (!bulkEvents.length) return;

    setLoading(true);
    setMessage("");

    try {
      const response = await axios.post("/confirm_bulk_events", bulkEvents);

      if (response.data.success) {
        setMessage(response.data.message);
        setBulkEvents([]);
        setShowBulkSection(false);
        setInputText("");
      } else {
        setMessage("Failed to create bulk events");
      }
    } catch (error) {
      setMessage(`Error: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleFileImport = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = async (e) => {
      const content = e.target.result;
      const fileType = file.name.split(".").pop().toLowerCase();

      setLoading(true);
      setMessage("");

      try {
        const response = await axios.post("/import_events", {
          file_content: content,
          file_type: fileType,
        });

        if (response.data.success) {
          setBulkEvents(response.data.parsed_events);
          setMessage(response.data.message);
          setShowBulkSection(true);
          setFileImportMode(false);
        } else {
          setMessage("Failed to import events from file");
        }
      } catch (error) {
        setMessage(`Error: ${error.response?.data?.detail || error.message}`);
      } finally {
        setLoading(false);
      }
    };

    reader.readAsText(file);
  };

  const handleParseEvent = async () => {
    if (!inputText.trim()) {
      setMessage("Please enter some text to parse");
      return;
    }

    setLoading(true);
    setMessage("");
    setParsedEvent(null);
    setEventLink("");

    try {
      const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
      const response = await axios.post("/create_event", {
        text: inputText,
        timezone,
      });

      if (response.data.success) {
        setParsedEvent(response.data.parsed_event);
        setMessage(response.data.message);
      } else {
        setMessage("Failed to parse event");
      }
    } catch (error) {
      setMessage(`Error: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmEvent = async () => {
    if (!parsedEvent) return;

    setLoading(true);
    setMessage("");

    try {
      const timezone =
        parsedEvent.timezone ||
        Intl.DateTimeFormat().resolvedOptions().timeZone;
      const response = await axios.post("/confirm_event", {
        ...parsedEvent,
        timezone,
      });

      if (response.data.success) {
        setMessage(response.data.message);
        setEventLink(response.data.event_link);
        setParsedEvent(null);
        setInputText("");
      } else {
        setMessage("Failed to create event");
      }
    } catch (error) {
      setMessage(`Error: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleAuth = async () => {
    try {
      const response = await axios.get("/auth/google");
      window.location.href = response.data.auth_url;
    } catch (error) {
      setMessage(
        `Authentication error: ${error.response?.data?.detail || error.message}`
      );
    }
  };

  const formatDateTime = (isoString) => {
    if (!isoString) return "";
    const date = new Date(isoString);
    return date.toLocaleString();
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

  const handleEditEvent = () => {
    setShowEditForm(true);
    setEditedEvent({ ...parsedEvent });
  };

  const handleEditFormChange = (field, value) => {
    setEditedEvent({ ...editedEvent, [field]: value });
  };

  const handleSaveEdit = () => {
    setParsedEvent(editedEvent);
    setShowEditForm(false);
    setEditedEvent(null);
  };

  const formatDateTimeLocal = (isoString) => {
    if (!isoString) return "";
    const date = new Date(isoString);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    const hours = String(date.getHours()).padStart(2, "0");
    const minutes = String(date.getMinutes()).padStart(2, "0");
    return `${year}-${month}-${day}T${hours}:${minutes}`;
  };

  const handleCancelEdit = () => {
    setShowEditForm(false);
    setEditedEvent(null);
  };

  return (
    <div className="App">
      <div className="container">
        <header className="header">
          <div className="header-content">
            <div>
              <h1>
                <Calendar className="header-icon" /> Prompt2Cal
              </h1>
              <p>Convert natural language to calendar events</p>
            </div>
            <button
              className="theme-toggle"
              onClick={toggleDarkMode}
              title={darkMode ? "Switch to light mode" : "Switch to dark mode"}
            >
              {darkMode ? <Sun size={24} /> : <Moon size={24} />}
            </button>
          </div>
        </header>

        <div className="auth-section">
          {isAuthenticated ? (
            <div className="auth-status">
              <span className="auth-success">
                <CheckCircle className="inline-icon" /> Connected to Google
                Calendar
              </span>
            </div>
          ) : (
            <div className="auth-prompt">
              <p>Please connect to Google Calendar to create events:</p>
              <button className="auth-button" onClick={handleGoogleAuth}>
                <Lock className="inline-icon" /> Connect to Google Calendar
              </button>
            </div>
          )}
        </div>

        <div className="input-section">
          <div className="input-group">
            <label htmlFor="event-input">Describe your event:</label>
            <div className="input-container">
              <textarea
                id="event-input"
                value={inputText}
                onChange={handleInputChange}
                placeholder="e.g., Lunch with Sarah next Tuesday at 1pm"
                rows={3}
                disabled={loading}
              />
              {speechSupported && (
                <button
                  className={`voice-button ${isListening ? "listening" : ""}`}
                  onClick={isListening ? stopVoiceInput : startVoiceInput}
                  disabled={loading}
                  title={isListening ? "Stop listening" : "Start voice input"}
                >
                  {isListening ? (
                    <StopCircle className="icon" />
                  ) : (
                    <Mic className="icon" />
                  )}
                </button>
              )}
            </div>
          </div>
          <div className="button-group">
            <button
              className="parse-button"
              onClick={handleParseEvent}
              disabled={loading || !inputText.trim()}
            >
              {loading ? (
                <>
                  <Hourglass className="inline-icon spinning" /> Parsing...
                </>
              ) : (
                <>
                  <Sparkles className="inline-icon" /> Parse Event
                </>
              )}
            </button>

            <button
              className="bulk-button"
              onClick={handleBulkEventParse}
              disabled={loading || !inputText.trim()}
            >
              {loading ? (
                <>
                  <Hourglass className="inline-icon spinning" /> Parsing...
                </>
              ) : (
                <>
                  <CalendarDays className="inline-icon" /> Parse Bulk Events
                </>
              )}
            </button>

            <button
              className="import-button"
              onClick={() => setFileImportMode(!fileImportMode)}
              disabled={loading}
            >
              <FolderOpen className="inline-icon" /> Import from File
            </button>
          </div>
        </div>

        {fileImportMode && (
          <div className="file-import-section">
            <h3>
              <FolderOpen className="inline-icon" /> Import Events from File
            </h3>
            <p>Upload a CSV or text file with events:</p>
            <input
              type="file"
              accept=".csv,.txt"
              onChange={handleFileImport}
              className="file-input"
            />
            <div className="file-format-info">
              <p>
                <strong>CSV Format:</strong> Title,Start Time,End
                Time,Location,Notes
              </p>
              <p>
                <strong>Text Format:</strong> One event description per line
              </p>
            </div>
          </div>
        )}

        {message && (
          <div
            className={`message ${
              message.includes("Error") ? "error" : "success"
            }`}
          >
            {message}
          </div>
        )}

        {parsedEvent && !showEditForm && (
          <div className="event-card">
            <div className="event-card-header">
              <div className="event-card-header-left">
                <Calendar className="event-card-icon" />
                <h3>Confirm Event</h3>
              </div>
            </div>
            <div className="event-card-content">
              <div className="event-title-row">
                <div className="event-title">{parsedEvent.title}</div>
                <button
                  className="edit-button"
                  onClick={handleEditEvent}
                  title="Edit event"
                >
                  <Pencil size={18} />
                </button>
              </div>
              <div className="event-time-row">
                <Clock className="event-time-icon" />
                <div className="event-time-info">
                  <div className="event-date">
                    {formatDateTimeShort(parsedEvent.start_time)}
                  </div>
                  <div className="event-time-range">
                    {formatTimeShort(parsedEvent.start_time)} -{" "}
                    {formatTimeShort(parsedEvent.end_time)}
                  </div>
                </div>
              </div>
            </div>
            <div className="confirmation-buttons">
              <button
                className="confirm-button"
                onClick={handleConfirmEvent}
                disabled={loading}
              >
                {loading ? (
                  <>
                    <Hourglass className="inline-icon spinning" /> Creating...
                  </>
                ) : (
                  <>
                    <CheckCircle className="inline-icon" /> Create Event
                  </>
                )}
              </button>
              <button
                className="cancel-button"
                onClick={() => setParsedEvent(null)}
                disabled={loading}
              >
                <X className="inline-icon" /> Cancel
              </button>
            </div>
          </div>
        )}

        {showEditForm && editedEvent && (
          <div className="event-edit-form">
            <h3>Event Details</h3>
            <div className="edit-form-group">
              <label>Title:</label>
              <input
                type="text"
                value={editedEvent.title}
                onChange={(e) => handleEditFormChange("title", e.target.value)}
                className="edit-input"
              />
            </div>
            <div className="edit-form-group">
              <label>Start:</label>
              <input
                type="datetime-local"
                value={formatDateTimeLocal(editedEvent.start_time)}
                onChange={(e) => {
                  const date = new Date(e.target.value);
                  handleEditFormChange("start_time", date.toISOString());
                }}
                className="edit-input"
              />
            </div>
            <div className="edit-form-group">
              <label>End:</label>
              <input
                type="datetime-local"
                value={formatDateTimeLocal(editedEvent.end_time)}
                onChange={(e) => {
                  const date = new Date(e.target.value);
                  handleEditFormChange("end_time", date.toISOString());
                }}
                className="edit-input"
              />
            </div>
            <div className="edit-form-group">
              <label>Color:</label>
              <select
                value={editedEvent.color || "#3f51b5"}
                onChange={(e) => handleEditFormChange("color", e.target.value)}
                className="edit-input"
              >
                <option value="#d50000">Tomato</option>
                <option value="#e67c73">Flamingo</option>
                <option value="#f4511e">Tangerine</option>
                <option value="#f6bf26">Banana</option>
                <option value="#33b679">Sage</option>
                <option value="#0b8043">Basil</option>
                <option value="#039be5">Peacock</option>
                <option value="#3f51b5">Blueberry</option>
                <option value="#7986cb">Lavender</option>
                <option value="#8e24aa">Grape</option>
                <option value="#616161">Graphite</option>
              </select>
            </div>
            <div className="edit-form-group">
              <label>Reminders:</label>
              <select
                value={editedEvent.reminder || "none"}
                onChange={(e) =>
                  handleEditFormChange("reminder", e.target.value)
                }
                className="edit-input"
              >
                <option value="none">None</option>
                <option value="5">5 minutes before</option>
                <option value="10">10 minutes before</option>
                <option value="15">15 minutes before</option>
                <option value="30">30 minutes before</option>
                <option value="60">1 hour before</option>
                <option value="1440">1 day before</option>
              </select>
            </div>
            <div className="confirmation-buttons">
              <button
                className="confirm-button"
                onClick={handleSaveEdit}
                disabled={loading}
              >
                <CheckCircle className="inline-icon" /> Create Event
              </button>
              <button
                className="cancel-button"
                onClick={handleCancelEdit}
                disabled={loading}
              >
                <X className="inline-icon" /> Cancel
              </button>
            </div>
          </div>
        )}

        {showBulkSection && bulkEvents.length > 0 && (
          <div className="bulk-confirmation-section">
            <h3>
              <CalendarDays className="inline-icon" /> Confirm Bulk Events (
              {bulkEvents.length} events)
            </h3>
            <div className="bulk-events-list">
              {bulkEvents.slice(0, 5).map((event, index) => (
                <div key={index} className="bulk-event-item">
                  <div className="bulk-event-title">{event.title}</div>
                  <div className="bulk-event-time">
                    {formatDateTime(event.start_time)} -{" "}
                    {formatDateTime(event.end_time)}
                  </div>
                  {event.location && (
                    <div className="bulk-event-location">
                      <MapPin className="inline-icon" /> {event.location}
                    </div>
                  )}
                </div>
              ))}
              {bulkEvents.length > 5 && (
                <div className="bulk-event-more">
                  ... and {bulkEvents.length - 5} more events
                </div>
              )}
            </div>
            <div className="confirmation-buttons">
              <button
                className="confirm-button"
                onClick={handleBulkEventConfirm}
                disabled={loading}
              >
                {loading ? (
                  <>
                    <Hourglass className="inline-icon spinning" /> Creating...
                  </>
                ) : (
                  <>
                    <CheckCircle className="inline-icon" /> Create{" "}
                    {bulkEvents.length} Events
                  </>
                )}
              </button>
              <button
                className="cancel-button"
                onClick={() => {
                  setShowBulkSection(false);
                  setBulkEvents([]);
                }}
                disabled={loading}
              >
                <X className="inline-icon" /> Cancel
              </button>
            </div>
          </div>
        )}

        {eventLink && (
          <div className="success-section">
            <h3>
              <PartyPopper className="inline-icon" /> Event Created
              Successfully!
            </h3>
            <a
              href={eventLink}
              target="_blank"
              rel="noopener noreferrer"
              className="event-link"
            >
              <CalendarCheck className="inline-icon" /> View in Google Calendar
            </a>
          </div>
        )}

        <div className="examples">
          <h3>
            <Lightbulb className="inline-icon" /> Example inputs:
          </h3>
          <ul>
            <li>"Lunch with Sarah next Tuesday at 1pm"</li>
            <li>"Team meeting tomorrow at 10am in conference room A"</li>
            <li>"Doctor appointment on Friday at 2:30pm"</li>
            <li>"Birthday party next Saturday at 7pm at my house"</li>
            <li>
              <strong>Recurring:</strong> "Weekly team standup every Monday at
              9am"
            </li>
            <li>
              <strong>Duration:</strong> "2-hour project meeting tomorrow at
              2pm"
            </li>
            <li>
              <strong>Relative time:</strong> "Call in 30 minutes"
            </li>
            <li>
              <strong>Voice input:</strong> Click{" "}
              <Mic className="inline-icon" /> to speak your event!
            </li>
            <li>
              <strong>Bulk creation:</strong> "Create 5 meetings every day this
              week at 2pm"
            </li>
            <li>
              <strong>File import:</strong> Upload CSV or text files with events
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}

export default App;
