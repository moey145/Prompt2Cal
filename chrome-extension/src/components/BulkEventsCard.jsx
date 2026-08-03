// Bulk events confirmation card component
import React from "react";
import {
  CalendarSync,
  CalendarDays,
  Clock,
  MapPin,
  FileText,
  Users,
  Video,
  SquarePen,
  X,
  Check,
  AlertTriangle,
} from "lucide-react";
import { formatDateTimeShort, formatTimeShort } from "../utils/dateFormatters";
import { getRecurrenceDescription } from "../utils/recurrenceDescription";
import { ConflictWarning } from "./ConflictWarning";

export const BulkEventsCard = ({
  parsedEvents,
  onEdit,
  onRemove,
  onCreateAll,
  onCancel,
  loading,
  loadingSingle,
  eventConflicts,
}) => {
  if (!parsedEvents || parsedEvents.length === 0) return null;

  const recurringCount = parsedEvents.filter(
    (e) => e.recurrence_type && e.recurrence_type !== "none"
  ).length;

  const getHeaderIcon = () => {
    return recurringCount > 0 ? (
      <CalendarSync className="event-card-icon-confirm" />
    ) : (
      <CalendarDays className="event-card-icon-confirm" />
    );
  };

  const getHeaderTitle = () => {
    if (recurringCount === parsedEvents.length && recurringCount > 0) {
      return <h3>Confirm {parsedEvents.length} Recurring Events</h3>;
    } else if (recurringCount > 0) {
      return (
        <h3>
          Confirm {parsedEvents.length} Events ({recurringCount} Recurring)
        </h3>
      );
    } else {
      return <h3>Confirm {parsedEvents.length} Events</h3>;
    }
  };

  return (
    <div className="event-card-confirm">
      <div className="event-card-header-confirm">
        <div className="event-card-header-left-confirm">
          {getHeaderIcon()}
          {getHeaderTitle()}
        </div>
      </div>
      <div className="events-list-confirm">
        {parsedEvents.map((event, index) => {
          const isRecurring =
            event.recurrence_type && event.recurrence_type !== "none";
          const confidence = event.field_confidence || {};
          const fieldClass = (field) =>
            confidence[field] === "ungrounded"
              ? " field-ungrounded-confirm"
              : "";
          const hasUngrounded =
            Object.values(confidence).includes("ungrounded");

          return (
            <div key={index} className="event-item-confirm">
              <div className="event-title-row-confirm">
                <div className={"event-title-confirm" + fieldClass("title")}>
                  {event.title}
                  {hasUngrounded && (
                    <AlertTriangle
                      size={14}
                      className="confidence-flag-confirm"
                      title="Some details were not found in your text"
                    />
                  )}
                </div>
                <div className="event-item-controls-confirm">
                  <button
                    className="edit-button-confirm"
                    title="Edit"
                    onClick={(e) => {
                      e.stopPropagation();
                      onEdit(index);
                    }}
                  >
                    <SquarePen size={18} />
                  </button>
                  <button
                    className="remove-event-confirm"
                    title="Remove"
                    onClick={() => onRemove(index)}
                  >
                    <X size={18} />
                  </button>
                </div>
              </div>
              {isRecurring ? (
                <div className="event-time-row-confirm">
                  <Clock className="event-time-icon-confirm" />
                  <div className="event-time-info-confirm">
                    <div className="event-start-label-confirm">
                      Starting from
                    </div>
                    <div
                      className={"event-date-confirm" + fieldClass("start_time")}
                    >
                      {formatDateTimeShort(event.start_time)}
                    </div>
                    <div className="event-time-range-confirm">
                      <span className={fieldClass("start_time").trim()}>
                        {formatTimeShort(event.start_time)}
                      </span>{" "}
                      -{" "}
                      <span className={fieldClass("end_time").trim()}>
                        {formatTimeShort(event.end_time)}
                      </span>
                      {event.end_time_assumed && (
                        <span className="assumed-label-confirm">assumed</span>
                      )}
                    </div>
                    <div className="recurrence-text-confirm">
                      {getRecurrenceDescription(event) ||
                        event.recurrence_type.charAt(0).toUpperCase() +
                          event.recurrence_type.slice(1)}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="event-time-row-confirm">
                  <Clock className="event-time-icon-confirm" />
                  <div className="event-time-info-confirm">
                    <div
                      className={"event-date-confirm" + fieldClass("start_time")}
                    >
                      {formatDateTimeShort(event.start_time)}
                    </div>
                    <div className="event-time-range-confirm">
                      <span className={fieldClass("start_time").trim()}>
                        {formatTimeShort(event.start_time)}
                      </span>{" "}
                      -{" "}
                      <span className={fieldClass("end_time").trim()}>
                        {formatTimeShort(event.end_time)}
                      </span>
                      {event.end_time_assumed && (
                        <span className="assumed-label-confirm">assumed</span>
                      )}
                    </div>
                  </div>
                </div>
              )}
              {event.location && (
                <div className="event-time-row-confirm">
                  <MapPin className="event-time-icon-confirm" />
                  <div
                    className={
                      "event-location-info-confirm" + fieldClass("location")
                    }
                  >
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
              {event.attendees && event.attendees.length > 0 && (
                <div className="event-time-row-confirm">
                  <Users className="event-time-icon-confirm" />
                  <div className="event-location-info-confirm">
                    {event.attendees.join(", ")}
                  </div>
                </div>
              )}
              {event.add_conference && (
                <div className="event-time-row-confirm">
                  <Video className="event-time-icon-confirm" />
                  <div className="event-location-info-confirm">
                    Google Meet link will be generated
                  </div>
                </div>
              )}
              {eventConflicts && eventConflicts[index] && eventConflicts[index].conflicts && eventConflicts[index].conflicts.length > 0 && (
                <div style={{ marginTop: "12px" }}>
                  <ConflictWarning
                    conflicts={eventConflicts[index].conflicts}
                    eventStartTime={event.start_time}
                    eventEndTime={event.end_time}
                  />
                </div>
              )}
            </div>
          );
        })}
      </div>

      <div className="action-buttons">
        <button
          className="create-button"
          onClick={onCreateAll}
          disabled={loading || loadingSingle}
        >
          <Check size={16} className="inline-icon" /> Create All Events
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

