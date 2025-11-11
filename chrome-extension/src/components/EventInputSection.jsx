// Event input section component
import React from "react";
import { Sparkles, Mic, Square } from "lucide-react";

export const EventInputSection = ({
  eventInput,
  setEventInput,
  onParse,
  isListening,
  onToggleVoice,
  loadingSingle,
  showSelectedText,
  selectedText,
  onUseSelectedText,
}) => {
  return (
    <>
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
            onClick={onToggleVoice}
          >
            {isListening ? <Square size={20} /> : <Mic size={22} />}
          </button>
        </div>
        <div className="action-buttons-main">
          <button
            id="parseEventButton"
            className="action-button action-single"
            onClick={() => onParse(null)}
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
            onClick={onUseSelectedText}
          >
            📝 Use Selected Text
          </button>
        </div>
      )}
    </>
  );
};

