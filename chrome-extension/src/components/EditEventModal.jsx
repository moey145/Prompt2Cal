// Edit event modal component (shared for single and bulk events)
import React from "react";
import { Edit, X, Check } from "lucide-react";
import { formatDateTime, toDateTimeLocal } from "../utils/dateFormatters";
import { EVENT_COLORS, REMINDER_OPTIONS } from "../utils/constants";
import { parseAttendeeInput, ensureUniqueEmails } from "../utils/emailUtils";

export const EditEventModal = ({
  event,
  attendees,
  attendeeInput,
  setAttendeeInput,
  onAddAttendee,
  onRemoveAttendee,
  selectedColor,
  setSelectedColor,
  selectedReminder,
  setSelectedReminder,
  editingStart,
  setEditingStart,
  editingEnd,
  setEditingEnd,
  onFieldChange,
  onSave,
  onCancel,
  loading,
}) => {
  if (!event) return null;

  return (
    <div className="modal-overlay" onClick={onCancel}>
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
                value={event.title || ""}
                onChange={(e) => onFieldChange("title", e.target.value)}
              />
            </div>
            <div className="detail-row editable-row">
              <strong>Start:</strong>
              {editingStart ? (
                <input
                  type="datetime-local"
                  className="datetime-input"
                  value={toDateTimeLocal(new Date(event.start_time))}
                  onChange={(e) => {
                    const d = new Date(e.target.value);
                    if (!isNaN(d.getTime())) {
                      const duration = event.duration_minutes || 60;
                      const endDate = new Date(d.getTime() + duration * 60000);
                      onFieldChange("start_time", d.toISOString());
                      onFieldChange("end_time", endDate.toISOString());
                    }
                  }}
                  onBlur={() => setEditingStart(false)}
                />
              ) : (
                <span
                  className="editable-field clickable"
                  onClick={() => setEditingStart(true)}
                >
                  {formatDateTime(event.start_time)}
                </span>
              )}
            </div>
            <div className="detail-row editable-row">
              <strong>End:</strong>
              {editingEnd ? (
                <input
                  type="datetime-local"
                  className="datetime-input"
                  value={toDateTimeLocal(new Date(event.end_time))}
                  onChange={(e) => {
                    const d = new Date(e.target.value);
                    if (!isNaN(d.getTime())) {
                      onFieldChange("end_time", d.toISOString());
                    }
                  }}
                  onBlur={() => setEditingEnd(false)}
                />
              ) : (
                <span
                  className="editable-field clickable"
                  onClick={() => setEditingEnd(true)}
                >
                  {formatDateTime(event.end_time)}
                </span>
              )}
            </div>
            <div className="detail-row editable-row">
              <strong>Location:</strong>
              <input
                className="text-input"
                type="text"
                value={event.location || ""}
                onChange={(e) => onFieldChange("location", e.target.value)}
              />
            </div>
            <div className="detail-row editable-row">
              <strong>Notes:</strong>
              <textarea
                className="text-input"
                rows="2"
                value={event.notes || ""}
                onChange={(e) => onFieldChange("notes", e.target.value)}
              />
            </div>
            <div className="detail-row editable-row">
              <strong>Guests:</strong>
              <div className="attendee-input-row">
                <input
                  type="email"
                  className="text-input"
                  placeholder="Add guest email"
                  value={attendeeInput}
                  onChange={(e) => setAttendeeInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      onAddAttendee();
                    }
                  }}
                />
                <button
                  type="button"
                  className="attendee-add-button"
                  onClick={onAddAttendee}
                  disabled={!attendeeInput.trim()}
                >
                  Add
                </button>
              </div>
              {attendees.length > 0 && (
                <div className="attendee-chip-list">
                  {attendees.map((email) => (
                    <span key={email} className="attendee-chip">
                      {email}
                      <button
                        type="button"
                        className="attendee-chip-remove"
                        aria-label={`Remove ${email}`}
                        onClick={() => onRemoveAttendee(email)}
                      >
                        <X size={12} />
                      </button>
                    </span>
                  ))}
                </div>
              )}
            </div>
            <div className="detail-row editable-row">
              <strong>Google Meet:</strong>
              <label className="checkbox-inline">
                <input
                  type="checkbox"
                  checked={Boolean(event.add_conference)}
                  onChange={(e) =>
                    onFieldChange("add_conference", e.target.checked)
                  }
                />
                <span>Add Google Meet link</span>
              </label>
            </div>
            <div className="detail-row">
              <strong>Color:</strong>
              <div className="color-presets">
                {EVENT_COLORS.map((c) => (
                  <div
                    key={c}
                    className={`color-preset ${selectedColor === c ? "selected" : ""}`}
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
                  {REMINDER_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          <div className="action-buttons">
            <button
              className="create-button"
              onClick={onSave}
              disabled={loading}
            >
              <Check size={16} className="inline-icon" /> Save Changes
            </button>
            <button
              className="cancel-button"
              onClick={onCancel}
              disabled={loading}
            >
              <X size={16} className="inline-icon" /> Cancel
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

