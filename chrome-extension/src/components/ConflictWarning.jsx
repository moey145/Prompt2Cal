// Conflict warning component
import React from "react";
import { AlertTriangle, Clock } from "lucide-react";
import { formatTimeShort } from "../utils/dateFormatters";

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
    </div>
  );
};
