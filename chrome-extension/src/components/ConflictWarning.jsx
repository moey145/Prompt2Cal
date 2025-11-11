// Conflict warning component
import React from "react";
import { AlertTriangle, Clock, Calendar } from "lucide-react";
import { formatDateTimeShort, formatTimeShort } from "../utils/dateFormatters";

// Helper to format conflict time
const formatConflictTime = (isoString) => {
  if (!isoString) return "";
  try {
    const date = new Date(isoString);
    return date.toLocaleString("en-US", {
      weekday: "short",
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
      hour12: true,
    });
  } catch (e) {
    return isoString;
  }
};

// Helper to format recurring event pattern (day and time)
const formatRecurringPattern = (isoString) => {
  if (!isoString) return "";
  try {
    const date = new Date(isoString);
    const weekday = date.toLocaleString("en-US", { weekday: "long" });
    const time = date.toLocaleString("en-US", {
      hour: "numeric",
      minute: "2-digit",
      hour12: true,
    });
    return `${weekday}s at ${time}`;
  } catch (e) {
    return isoString;
  }
};

export const ConflictWarning = ({
  conflicts,
  alternatives,
  onSelectAlternative,
  eventStartTime,
  eventEndTime,
}) => {
  if (!conflicts || conflicts.length === 0) {
    return null;
  }

  return (
    <div className="conflict-warning">
      <div className="conflict-header">
        <AlertTriangle size={18} className="conflict-icon" />
        <strong>Schedule Conflict Detected</strong>
      </div>
      <div className="conflict-message">
        This event conflicts with {conflicts.length} existing event
        {conflicts.length > 1 ? "s" : ""}:
      </div>
      <div className="conflicts-list">
        {conflicts.map((conflict, index) => (
          <div key={index} className="conflict-item">
            <div className="conflict-title">
              {conflict.title}
              {conflict.is_recurring && (
                <span className="conflict-recurring-badge">
                  {" "}
                  (Recurring Event)
                </span>
              )}
            </div>
            {conflict.is_recurring ? (
              <div className="conflict-time">
                <Clock size={14} />
                {formatRecurringPattern(conflict.start)}
              </div>
            ) : (
              <div className="conflict-time">
                <Clock size={14} />
                {formatConflictTime(conflict.start)} -{" "}
                {formatTimeShort(conflict.end)}
              </div>
            )}
            {conflict.location && (
              <div className="conflict-location">{conflict.location}</div>
            )}
          </div>
        ))}
      </div>

      {alternatives && alternatives.length > 0 && (
        <div className="alternatives-section">
          <div className="alternatives-header">
            <strong>Suggested Alternative Times:</strong>
          </div>
          <div className="alternatives-list">
            {alternatives.map((alt, index) => (
              <button
                key={index}
                className="alternative-time-button"
                onClick={() => onSelectAlternative(alt)}
                title={`Select ${alt.formatted_start}`}
              >
                <div className="alternative-time-main">
                  {alt.formatted_start}
                </div>
                <div className="alternative-time-range">
                  {alt.formatted_time}
                </div>
                {alt.minutes_from_proposed !== 0 && (
                  <div className="alternative-time-offset">
                    {(() => {
                      const minutes = Math.abs(alt.minutes_from_proposed);
                      const hours = Math.floor(minutes / 60);
                      const remainingMinutes = minutes % 60;

                      const isEarlier = alt.minutes_from_proposed < 0;

                      if (hours > 0 && remainingMinutes === 0) {
                        return `${hours} ${hours === 1 ? "hour" : "hours"} ${
                          isEarlier ? "earlier" : "later"
                        }`;
                      } else if (hours > 0) {
                        return `${hours}h ${remainingMinutes}m ${
                          isEarlier ? "earlier" : "later"
                        }`;
                      } else {
                        return `${minutes} min ${
                          isEarlier ? "earlier" : "later"
                        }`;
                      }
                    })()}
                  </div>
                )}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
