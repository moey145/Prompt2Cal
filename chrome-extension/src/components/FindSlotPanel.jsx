// Find a free slot in the next few days and start an event from it.
import React, { useEffect, useRef, useState } from "react";
import { CalendarSearch, Info, X } from "lucide-react";
import { SLOT_DURATION_OPTIONS } from "../utils/constants";
import { groupSlotsByDay } from "../utils/slotGroups";
import { SLOT_HOURS_KEY, formatHour, validSlotHours } from "../utils/slotFinder";

const START_HOURS = Array.from({ length: 24 }, (_, hour) => hour); // midnight to 11pm
const END_HOURS = Array.from({ length: 24 }, (_, i) => i + 1); // 1am to midnight

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
  const [includeWeekends, setIncludeWeekends] = useState(false);
  // null until the saved hours are read, so the first search uses them.
  const [hours, setHours] = useState(null);
  const [slots, setSlots] = useState(null);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState(null);
  const [showTip, setShowTip] = useState(false);
  const latestRequest = useRef(0);

  useEffect(() => {
    chrome.storage.local
      .get([SLOT_HOURS_KEY])
      .then((stored) => setHours(validSlotHours(stored[SLOT_HOURS_KEY])))
      .catch(() => setHours(validSlotHours(null)));
  }, []);

  const changeHours = (first, last) => {
    // Keep the end after the start, whichever one moved.
    const next = last > first ? [first, last] : [first, Math.min(first + 1, 24)];
    setHours(next);
    chrome.storage.local.set({ [SLOT_HOURS_KEY]: next }).catch(() => {});
  };

  // Search as soon as the panel opens and whenever a choice changes; only the
  // newest request may update the list.
  useEffect(() => {
    if (!hours) return;
    const request = ++latestRequest.current;
    setSearching(true);
    onFindSlots({ durationMinutes, days, includeWeekends, workingHours: hours })
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
  }, [durationMinutes, days, includeWeekends, hours]);

  const groups = slots ? groupSlotsByDay(slots) : [];
  const lengthLabel = SLOT_DURATION_OPTIONS.find((o) => o.value === durationMinutes)?.label;
  const hoursLabel = hours ? `between ${formatHour(hours[0])} and ${formatHour(hours[1])}` : "";

  return (
    <div className="event-card find-slot-panel">
      <div className="find-slot-header">
        <span className="input-label find-slot-title">
          <CalendarSearch size={18} className="inline-icon" /> Find a free time
          <button
            type="button"
            className={`find-slot-tip-button ${showTip ? "active" : ""}`}
            aria-label="What does this do?"
            aria-expanded={showTip}
            aria-controls="find-slot-tip"
            title="What does this do?"
            onClick={() => setShowTip(!showTip)}
          >
            <Info size={15} />
          </button>
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

      {showTip && (
        <div id="find-slot-tip" className="find-slot-tip">
          Looks through your calendar for gaps where an event of the chosen
          length fits, within the hours and days you pick. It keeps 15 minutes
          clear around your existing events. Click a time to start a new event
          there; nothing is added to your calendar until you create it.
        </div>
      )}

      <ChipGroup
        label="Length"
        options={SLOT_DURATION_OPTIONS}
        value={durationMinutes}
        onChange={setDurationMinutes}
      />
      <ChipGroup label="Within" options={RANGE_OPTIONS} value={days} onChange={setDays} />
      <div className="find-slot-row">
        <span className="find-slot-row-label">Hours</span>
        <div className="find-slot-hours">
          <select
            className="find-slot-select"
            aria-label="Earliest start"
            value={hours ? hours[0] : ""}
            disabled={!hours}
            onChange={(e) => changeHours(Number(e.target.value), hours[1])}
          >
            {START_HOURS.map((hour) => (
              <option key={hour} value={hour}>
                {formatHour(hour)}
              </option>
            ))}
          </select>
          <span>to</span>
          <select
            className="find-slot-select"
            aria-label="Latest finish"
            value={hours ? hours[1] : ""}
            disabled={!hours}
            onChange={(e) => changeHours(hours[0], Number(e.target.value))}
          >
            {END_HOURS.filter((hour) => !hours || hour > hours[0]).map((hour) => (
              <option key={hour} value={hour}>
                {formatHour(hour)}
              </option>
            ))}
          </select>
        </div>
      </div>
      <div className="find-slot-row">
        <span className="find-slot-row-label" />
        <label className="find-slot-toggle">
          <input
            type="checkbox"
            checked={includeWeekends}
            onChange={(e) => setIncludeWeekends(e.target.checked)}
          />
          Include weekends
        </label>
      </div>

      <div className={`find-slot-results ${searching ? "is-searching" : ""}`}>
        {searching && slots === null ? (
          <div className="find-slot-status">Checking your calendar…</div>
        ) : error ? (
          <div className="find-slot-status">{error}</div>
        ) : groups.length === 0 ? (
          <div className="find-slot-status">
            No times with {lengthLabel} free {hoursLabel}
            {includeWeekends ? "" : " on weekdays"}. Try a shorter length, wider
            hours or a longer range.
          </div>
        ) : (
          <>
          <div className="find-slot-summary">
            Times with {lengthLabel} free {hoursLabel}. Pick one to start an event.
          </div>
          {groups.map((group) => (
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
          ))}
          </>
        )}
      </div>
    </div>
  );
};
