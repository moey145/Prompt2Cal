// Find a free slot in the next few days and start an event from it.
import React, { useEffect, useRef, useState } from "react";
import { CalendarSearch, X } from "lucide-react";
import { SLOT_DURATION_OPTIONS } from "../utils/constants";
import { groupSlotsByDay } from "../utils/slotGroups";

const RANGE_OPTIONS = [
  { value: 1, label: "Today" },
  { value: 3, label: "3 days" },
  { value: 7, label: "7 days" },
];

const ChipGroup = ({ label, options, value, onChange }) => (
  <div className="find-slot-row">
    <span className="find-slot-row-label">{label}</span>
    <div className="find-slot-chips" role="radiogroup" aria-label={label}>
      {options.map((option) => (
        <button
          key={option.value}
          type="button"
          role="radio"
          aria-checked={value === option.value}
          className={`find-slot-chip ${value === option.value ? "selected" : ""}`}
          onClick={() => onChange(option.value)}
        >
          {option.short || option.label}
        </button>
      ))}
    </div>
  </div>
);

export const FindSlotPanel = ({ onFindSlots, onPickSlot, onClose }) => {
  const [durationMinutes, setDurationMinutes] = useState(60);
  const [days, setDays] = useState(3);
  const [slots, setSlots] = useState(null);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState(null);
  const latestRequest = useRef(0);

  // Search as soon as the panel opens and whenever a choice changes; only the
  // newest request may update the list.
  useEffect(() => {
    const request = ++latestRequest.current;
    setSearching(true);
    onFindSlots({ durationMinutes, days })
      .then((found) => {
        if (request !== latestRequest.current) return;
        setSlots(found);
        setError(null);
      })
      .catch((failure) => {
        if (request !== latestRequest.current) return;
        setSlots(null);
        setError(failure.message);
      })
      .finally(() => {
        if (request === latestRequest.current) setSearching(false);
      });
  }, [durationMinutes, days]);

  const groups = slots ? groupSlotsByDay(slots) : [];

  return (
    <div className="event-card find-slot-panel">
      <div className="find-slot-header">
        <span className="input-label find-slot-title">
          <CalendarSearch size={18} className="inline-icon" /> Find a free time
        </span>
        <button
          type="button"
          className="find-slot-close"
          aria-label="Close free slot search"
          onClick={onClose}
        >
          <X size={16} />
        </button>
      </div>

      <ChipGroup
        label="Length"
        options={SLOT_DURATION_OPTIONS}
        value={durationMinutes}
        onChange={setDurationMinutes}
      />
      <ChipGroup label="Within" options={RANGE_OPTIONS} value={days} onChange={setDays} />

      <div className={`find-slot-results ${searching ? "is-searching" : ""}`}>
        {searching && slots === null ? (
          <div className="find-slot-status">Checking your calendar…</div>
        ) : error ? (
          <div className="find-slot-status">{error}</div>
        ) : groups.length === 0 ? (
          <div className="find-slot-status">
            No free time between 9am and 5pm for that length. Try a shorter
            length or a longer range.
          </div>
        ) : (
          groups.map((group) => (
            <div key={group.label} className="find-slot-day">
              <div className="find-slot-day-label">{group.label}</div>
              <div className="find-slot-times">
                {group.slots.map((slot) => (
                  <button
                    key={slot.start}
                    type="button"
                    className="find-slot-time"
                    onClick={() => onPickSlot(slot)}
                    title={`Start an event at ${slot.formatted_start}`}
                  >
                    {slot.time}
                  </button>
                ))}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
