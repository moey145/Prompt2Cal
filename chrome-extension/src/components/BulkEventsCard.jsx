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
} from "lucide-react";
import { formatDateTimeShort, formatTimeShort } from "../utils/dateFormatters";
import { getRecurrenceDescription } from "../utils/recurrenceDescription";

export const BulkEventsCard = ({
  parsedEvents,
  onEdit,
  onRemove,
  onCreateAll,
  onCancel,
  loading,
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

          return (
            <div key={index} className="event-item-confirm">
              <div className="event-title-row-confirm">
                <div className="event-title-confirm">{event.title}</div>
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
                    <div className="event-date-confirm">
                      {formatDateTimeShort(event.start_time)}
                    </div>
                    <div className="event-time-range-confirm">
                      {formatTimeShort(event.start_time)} -{" "}
                      {formatTimeShort(event.end_time)}
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
                    <div className="event-date-confirm">
                      {formatDateTimeShort(event.start_time)}
                    </div>
                    <div className="event-time-range-confirm">
                      {formatTimeShort(event.start_time)} -{" "}
                      {formatTimeShort(event.end_time)}
                    </div>
                  </div>
                </div>
              )}
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
            </div>
          );
        })}
      </div>

      <div className="action-buttons">
        <button
          className="create-button"
          onClick={onCreateAll}
          disabled={loading}
        >
          <Check size={16} className="inline-icon" /> Create All Events
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
  );
};

