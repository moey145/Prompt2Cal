// Find a free slot in the next few days and start an event from it.
import React, { useState } from "react";
import { CalendarSearch, Clock, X } from "lucide-react";
import { SLOT_DURATION_OPTIONS } from "../utils/constants";

const RANGE_OPTIONS = [
  { value: 1, label: "Today" },
  { value: 3, label: "Next 3 days" },
  { value: 7, label: "Next 7 days" },
];

export const FindSlotPanel = ({ onFindSlots, onPickSlot, onClose }) => {
  const [durationMinutes, setDurationMinutes] = useState(60);
  const [days, setDays] = useState(3);
  const [slots, setSlots] = useState(null);
  const [searching, setSearching] = useState(false);

  const search = async () => {
    setSearching(true);
    try {
      setSlots(await onFindSlots({ durationMinutes, days }));
    } finally {
      setSearching(false);
    }
  };

  return (
    <div className="event-card find-slot-panel">
      <div className="find-slot-header">
        <span className="input-label">
          <CalendarSearch size={18} className="inline-icon" /> Find a free slot
        </span>
        <button
          type="button"
          className="attendee-chip-remove"
          aria-label="Close free slot search"
          onClick={onClose}
        >
          <X size={14} />
        </button>
      </div>

      <div className="find-slot-controls">
        <select
          className="reminder-select"
          value={durationMinutes}
          onChange={(e) => setDurationMinutes(Number(e.target.value))}
          aria-label="Meeting length"
        >
          {SLOT_DURATION_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        <select
          className="reminder-select"
          value={days}
          onChange={(e) => setDays(Number(e.target.value))}
          aria-label="Search range"
        >
          {RANGE_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        <button
          type="button"
          className="action-button action-single"
          onClick={search}
          disabled={searching}
        >
          {searching ? "Searching…" : "Search"}
        </button>
      </div>

      {slots !== null && !searching && (
        <div className="find-slot-results">
          {slots.length === 0 ? (
            <div className="find-slot-empty">
              No free slots in working hours for that length. Try a shorter
              meeting or a wider range.
            </div>
          ) : (
            slots.map((slot) => (
              <button
                key={slot.start}
                type="button"
                className="conflict-alternative-button"
                onClick={() => onPickSlot(slot)}
                title="Start an event at this time"
              >
                <Clock size={14} />
                {slot.formatted_start}
              </button>
            ))
          )}
        </div>
      )}
    </div>
  );
};
