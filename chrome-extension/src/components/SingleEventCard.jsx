// Single event confirmation card component
import React from "react";
import {
  Calendar1,
  CalendarSync,
  Clock,
  MapPin,
  FileText,
  Users,
  Video,
  SquarePen,
  Check,
  X,
  AlertTriangle,
} from "lucide-react";
import { formatDateTimeShort, formatTimeShort, formatDateOnly } from "../utils/dateFormatters";
import { getRecurrenceDescription } from "../utils/recurrenceDescription";
import { ConflictWarning } from "./ConflictWarning";

export const SingleEventCard = ({
  parsedEvent,
  onEdit,
  onCreate,
  onCancel,
  loading,
  loadingSingle,
  conflicts,
  checkingConflicts,
}) => {
  if (!parsedEvent) return null;

  const isRecurring =
    parsedEvent.recurrence_type &&
    parsedEvent.recurrence_type !== "none";
  const recurrenceEndLabel = parsedEvent.end_date
    ? formatDateOnly(parsedEvent.end_date)
    : null;

  // Source-grounding confidence computed by the backend verifier:
  // fields marked "ungrounded" were not found in the user's input text.
  const confidence = parsedEvent.field_confidence || {};
  const isUngrounded = (field) => confidence[field] === "ungrounded";
  const fieldClass = (field) =>
    isUngrounded(field) ? " field-ungrounded-confirm" : "";
  const hasUngrounded = Object.values(confidence).includes("ungrounded");

  return (
    <div className="event-card-confirm">
      <div className="event-card-header-confirm">
        <div className="event-card-header-left-confirm">
          {isRecurring ? (
            <CalendarSync className="event-card-icon-confirm" />
          ) : (
            <Calendar1 className="event-card-icon-confirm" />
          )}
          {isRecurring ? (
            <h3>Confirm Recurring Event</h3>
          ) : (
            <h3>Confirm Event</h3>
          )}
        </div>
      </div>
      <div className="event-card-content-confirm">
        <div className="event-title-row-confirm">
          <div className={"event-title-confirm" + fieldClass("title")}>
            {parsedEvent.title}
          </div>
          <button
            className="edit-button-confirm"
            onClick={onEdit}
            title="Edit event"
          >
            <SquarePen size={18} />
          </button>
        </div>
        {isRecurring ? (
          <div className="event-time-row-confirm">
            <Clock className="event-time-icon-confirm" />
            <div className="event-time-info-confirm">
              <div className="event-start-label-confirm">Starting from</div>
              <div className={"event-date-confirm" + fieldClass("start_time")}>
                {formatDateTimeShort(parsedEvent.start_time)}
              </div>
              <div className="event-time-range-confirm">
                <span className={fieldClass("start_time").trim()}>
                  {formatTimeShort(parsedEvent.start_time)}
                </span>{" "}
                -{" "}
                <span className={fieldClass("end_time").trim()}>
                  {formatTimeShort(parsedEvent.end_time)}
                </span>
                {parsedEvent.end_time_assumed && (
                  <span className="assumed-label-confirm">assumed</span>
                )}
              </div>
              <div
                className={
                  "recurrence-text-confirm" + fieldClass("recurrence_type")
                }
              >
                {getRecurrenceDescription(parsedEvent) ||
                  parsedEvent.recurrence_type.charAt(0).toUpperCase() +
                    parsedEvent.recurrence_type.slice(1)}
              </div>
              {recurrenceEndLabel && (
                <div className="event-until-confirm">
                  Until {recurrenceEndLabel}
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="event-time-row-confirm">
            <Clock className="event-time-icon-confirm" />
            <div className="event-time-info-confirm">
              <div className={"event-date-confirm" + fieldClass("start_time")}>
                {formatDateTimeShort(parsedEvent.start_time)}
              </div>
              <div className="event-time-range-confirm">
                <span className={fieldClass("start_time").trim()}>
                  {formatTimeShort(parsedEvent.start_time)}
                </span>{" "}
                -{" "}
                <span className={fieldClass("end_time").trim()}>
                  {formatTimeShort(parsedEvent.end_time)}
                </span>
                {parsedEvent.end_time_assumed && (
                  <span className="assumed-label-confirm">assumed</span>
                )}
              </div>
            </div>
          </div>
        )}
        {parsedEvent.location ? (
          <div className="event-time-row-confirm">
            <MapPin className="event-time-icon-confirm" />
            <div
              className={
                "event-location-info-confirm" + fieldClass("location")
              }
            >
              {parsedEvent.location}
            </div>
          </div>
        ) : (
          <div className="event-time-row-confirm field-empty-confirm">
            <MapPin className="event-time-icon-confirm" />
            <div className="event-location-info-confirm">
              No location specified
            </div>
          </div>
        )}
        {parsedEvent.notes && (
          <div className="event-time-row-confirm">
            <FileText className="event-time-icon-confirm" />
            <div
              className={"event-location-info-confirm" + fieldClass("notes")}
            >
              {parsedEvent.notes}
            </div>
          </div>
        )}
        {parsedEvent.attendees && parsedEvent.attendees.length > 0 && (
          <div className="event-time-row-confirm">
            <Users className="event-time-icon-confirm" />
            <div className="event-location-info-confirm">
              {parsedEvent.attendees.join(", ")}
            </div>
          </div>
        )}
        {parsedEvent.add_conference && (
          <div className="event-time-row-confirm">
            <Video className="event-time-icon-confirm" />
            <div className="event-location-info-confirm">
              Google Meet link will be generated
            </div>
          </div>
        )}
        {hasUngrounded && (
          <div className="confidence-hint-confirm">
            <AlertTriangle size={14} className="confidence-hint-icon-confirm" />
            <span>
              Highlighted details were not found in your text. Please check
              them before creating the event.
            </span>
          </div>
        )}
        {!checkingConflicts && conflicts && conflicts.length > 0 && (
          <ConflictWarning
            conflicts={conflicts}
            eventStartTime={parsedEvent.start_time}
            eventEndTime={parsedEvent.end_time}
          />
        )}
      </div>
      <div className="action-buttons">
        <button
          className="create-button"
          onClick={onCreate}
          disabled={loading || loadingSingle}
        >
          <Check size={16} className="inline-icon" /> Create Event
        </button>
        <button
          className="cancel-button"
          onClick={onCancel}
          disabled={loading || loadingSingle}
        >
          <X size={16} className="inline-icon" /> Cancel
        </button>
      </div>
    </div>
  );
};
