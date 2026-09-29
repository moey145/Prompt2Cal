// Edit event dialog (shared for single and bulk events)
import React, { useEffect, useRef } from "react";
import { Edit, X, Check } from "lucide-react";
import {
  EVENT_COLORS,
  EVENT_COLOR_NAMES,
  RECURRENCE_OPTIONS,
  REMINDER_OPTIONS,
} from "../utils/constants";
import {
  fieldsForEndMode,
  fieldsForRecurrenceType,
  intervalUnitLabel,
  isRecurring as isRecurringEvent,
  recurrenceEndMode,
} from "../utils/recurrence";
import {
  meetingLabels,
  supportsCategories,
} from "../utils/providerOptions";
import {
  fieldsForEnd,
  fieldsForStart,
  formatDuration,
  minutesBetween,
  toInputValue,
  validateEvent,
} from "../utils/eventEditing";

const FOCUSABLE =
  'button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

const Field = ({ label, htmlFor, error, hint, children }) => (
  <div className="edit-field">
    <label className="edit-label" htmlFor={htmlFor}>
      {label}
    </label>
    {children}
    {error ? (
      <div className="edit-error" role="alert">
        {error}
      </div>
    ) : hint ? (
      <div className="edit-hint">{hint}</div>
    ) : null}
  </div>
);

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
  onFieldChange,
  onSave,
  onCancel,
  loading,
  calendarProvider = "google",
  categories = [],
}) => {
  const dialogRef = useRef(null);
  const titleInputRef = useRef(null);
  // The parent passes new handler functions on every render; reading them
  // through refs lets the setup below run once instead of after each
  // keystroke, which used to pull focus back to the title.
  const onCancelRef = useRef(onCancel);
  const saveRef = useRef(null);
  onCancelRef.current = onCancel;

  const errors = event ? validateEvent(event) : {};
  const canSave = !loading && Object.keys(errors).length === 0;
  const save = () => {
    if (canSave) onSave();
  };
  saveRef.current = save;

  // Focus starts on the title with its text selected, Escape cancels,
  // Ctrl/Cmd+Enter saves, Tab stays inside the dialog, and focus returns to
  // whatever opened it.
  useEffect(() => {
    const opener = document.activeElement;
    titleInputRef.current?.focus();
    titleInputRef.current?.select();

    const handleKeyDown = (e) => {
      if (e.key === "Escape") {
        e.preventDefault();
        onCancelRef.current();
      } else if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        saveRef.current();
      } else if (e.key === "Tab" && dialogRef.current) {
        const items = [...dialogRef.current.querySelectorAll(FOCUSABLE)];
        if (!items.length) return;
        const first = items[0];
        const last = items[items.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      if (opener instanceof HTMLElement && document.contains(opener)) {
        opener.focus();
      }
    };
  }, []);

  if (!event) return null;

  const apply = (fields) => {
    if (!fields) return;
    Object.entries(fields).forEach(([field, value]) => onFieldChange(field, value));
  };

  // The two calendars do not offer the same options: Outlook creates Teams
  // meetings, and Microsoft Graph has no per-event colour (it uses named
  // categories instead), so the colour row is Google-only.
  const labels = meetingLabels(calendarProvider);
  const showCategories = supportsCategories(calendarProvider);

  const recurrenceType = event.recurrence_type || "none";
  const isRecurring = isRecurringEvent(event);
  const intervalUnit = intervalUnitLabel(recurrenceType);
  const endMode = recurrenceEndMode(event);
  const duration = formatDuration(minutesBetween(event.start_time, event.end_time));

  return (
    <div
      className="modal-overlay"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onCancel();
      }}
    >
      <div
        className="edit-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="edit-dialog-title"
        ref={dialogRef}
      >
        <div className="edit-dialog-header">
          <h3 id="edit-dialog-title">
            <Edit size={18} /> Edit event
          </h3>
          <button
            type="button"
            className="edit-dialog-close"
            aria-label="Close without saving"
            onClick={onCancel}
          >
            <X size={18} />
          </button>
        </div>

        <div className="edit-dialog-body">
          <Field label="Title" htmlFor="edit-title" error={errors.title}>
            <input
              id="edit-title"
              ref={titleInputRef}
              className="edit-input"
              type="text"
              placeholder="Add a title"
              value={event.title || ""}
              onChange={(e) => onFieldChange("title", e.target.value)}
            />
          </Field>

          <div className="edit-grid">
            <Field label="Starts" htmlFor="edit-start" error={errors.start_time}>
              <input
                id="edit-start"
                type="datetime-local"
                className="edit-input"
                value={toInputValue(event.start_time)}
                onChange={(e) => apply(fieldsForStart(event, e.target.value))}
              />
            </Field>
            <Field
              label="Ends"
              htmlFor="edit-end"
              error={errors.end_time}
              hint={duration && `Lasts ${duration}`}
            >
              <input
                id="edit-end"
                type="datetime-local"
                className="edit-input"
                value={toInputValue(event.end_time)}
                min={toInputValue(event.start_time) || undefined}
                onChange={(e) => apply(fieldsForEnd(event, e.target.value))}
              />
            </Field>
          </div>

          <Field label="Repeats" htmlFor="edit-repeats" error={errors.end_date}>
            <div className="edit-inline">
              <select
                id="edit-repeats"
                className="edit-input edit-input-auto"
                value={recurrenceType}
                onChange={(e) => apply(fieldsForRecurrenceType(e.target.value))}
              >
                {RECURRENCE_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>

              {isRecurring && (
                <>
                  <label className="edit-inline-text">
                    every
                    <input
                      type="number"
                      min="1"
                      max="30"
                      className="edit-input edit-number"
                      aria-label="Repeat interval"
                      value={event.recurrence_interval || 1}
                      onChange={(e) =>
                        onFieldChange(
                          "recurrence_interval",
                          Math.max(1, parseInt(e.target.value, 10) || 1)
                        )
                      }
                    />
                    {intervalUnit}
                  </label>

                  <select
                    className="edit-input edit-input-auto"
                    aria-label="When the series ends"
                    value={endMode}
                    onChange={(e) => apply(fieldsForEndMode(e.target.value, event))}
                  >
                    <option value="never">Never ends</option>
                    <option value="count">Ends after…</option>
                    <option value="date">Ends on…</option>
                  </select>

                  {endMode === "count" && (
                    <label className="edit-inline-text">
                      <input
                        type="number"
                        min="1"
                        max="365"
                        className="edit-input edit-number"
                        aria-label="Number of occurrences"
                        value={event.recurrence_count || 1}
                        onChange={(e) =>
                          onFieldChange(
                            "recurrence_count",
                            Math.max(1, parseInt(e.target.value, 10) || 1)
                          )
                        }
                      />
                      times
                    </label>
                  )}

                  {endMode === "date" && (
                    <input
                      type="date"
                      className="edit-input edit-input-auto"
                      aria-label="Last date of the series"
                      value={(event.end_date || "").slice(0, 10)}
                      min={toInputValue(event.start_time).slice(0, 10) || undefined}
                      onChange={(e) => onFieldChange("end_date", e.target.value)}
                    />
                  )}
                </>
              )}
            </div>
          </Field>

          <Field label="Location" htmlFor="edit-location">
            <input
              id="edit-location"
              className="edit-input"
              type="text"
              placeholder="Add a location"
              value={event.location || ""}
              onChange={(e) => onFieldChange("location", e.target.value)}
            />
          </Field>

          <Field label="Notes" htmlFor="edit-notes">
            <textarea
              id="edit-notes"
              className="edit-input edit-textarea"
              rows="2"
              placeholder="Add notes"
              value={event.notes || ""}
              onChange={(e) => onFieldChange("notes", e.target.value)}
            />
          </Field>

          <Field label="Guests" htmlFor="edit-guests">
            <div className="edit-inline edit-guest-row">
              <input
                id="edit-guests"
                type="email"
                className="edit-input"
                placeholder="name@example.com"
                value={attendeeInput}
                onChange={(e) => setAttendeeInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.ctrlKey && !e.metaKey) {
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
            <label className="edit-checkbox">
              <input
                type="checkbox"
                checked={Boolean(event.add_conference)}
                onChange={(e) => onFieldChange("add_conference", e.target.checked)}
              />
              {labels.checkbox}
            </label>
          </Field>

          <div className="edit-grid">
            {showCategories ? (
              <Field label="Category" htmlFor="edit-category">
                <select
                  id="edit-category"
                  className="edit-input"
                  value={event.category || ""}
                  onChange={(e) => onFieldChange("category", e.target.value || null)}
                  disabled={categories.length === 0}
                >
                  <option value="">
                    {categories.length === 0 ? "None in your mailbox" : "No category"}
                  </option>
                  {categories.map((category) => (
                    <option key={category.name} value={category.name}>
                      {category.name}
                    </option>
                  ))}
                </select>
              </Field>
            ) : (
              <Field label="Colour">
                <div className="edit-colours" role="radiogroup" aria-label="Event colour">
                  {EVENT_COLORS.map((colour) => (
                    <button
                      key={colour}
                      type="button"
                      role="radio"
                      aria-checked={selectedColor === colour}
                      aria-label={EVENT_COLOR_NAMES[colour] || colour}
                      title={EVENT_COLOR_NAMES[colour]}
                      className={`edit-colour ${selectedColor === colour ? "selected" : ""}`}
                      style={{ backgroundColor: colour }}
                      onClick={() => setSelectedColor(colour)}
                    />
                  ))}
                </div>
              </Field>
            )}
            <Field label="Reminder" htmlFor="edit-reminder">
              <select
                id="edit-reminder"
                className="edit-input"
                value={selectedReminder}
                onChange={(e) => setSelectedReminder(e.target.value)}
              >
                {REMINDER_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </Field>
          </div>
        </div>

        <div className="edit-dialog-footer">
          <button type="button" className="cancel-button" onClick={onCancel} disabled={loading}>
            Cancel
          </button>
          <button
            type="button"
            className="create-button"
            onClick={save}
            disabled={!canSave}
            title="Save (Ctrl+Enter)"
          >
            <Check size={16} /> Save changes
          </button>
        </div>
      </div>
    </div>
  );
};
