// Find a free slot in the next few days and start an event from it.
import React, { useEffect, useRef, useState } from "react";
import { CalendarSearch, Info, X } from "lucide-react";
import { SLOT_DURATION_OPTIONS } from "../utils/constants";
import { groupSlotsByDay } from "../utils/slotGroups";
import {
  DAY_LIMITS,
  LENGTH_LIMITS,
  SLOT_HOURS_KEY,
  SLOT_PREFS_KEY,
  clampDays,
  clampLength,
  formatHour,
  lengthWords,
  rangeWords,
  validSlotHours,
  validSlotPrefs,
} from "../utils/slotFinder";

const START_HOURS = Array.from({ length: 24 }, (_, hour) => hour); // midnight to 11pm
const END_HOURS = Array.from({ length: 24 }, (_, i) => i + 1); // 1am to midnight

const RANGE_OPTIONS = [
  { value: 1, label: "Today" },
  { value: 3, label: "3 days" },
  { value: 7, label: "7 days" },
];

// A number box that searches once typing pauses (or on Enter / leaving the
// box), not on every keystroke, and shows the clamped value it settled on.
const NumberField = ({ model, toModel, fromModel, onCommit, ...inputProps }) => {
  const shown = String(fromModel(model));
  const [draft, setDraft] = useState(shown);

  useEffect(() => setDraft(shown), [shown]);

  const commit = (text, final) => {
    const number = Number(text);
    if (text.trim() === "" || !Number.isFinite(number) || number <= 0) {
      if (final) setDraft(shown);
      return;
    }
    const next = toModel(number);
    if (next !== model) onCommit(next);
    if (final) setDraft(String(fromModel(next)));
  };

  useEffect(() => {
    if (draft === shown) return undefined;
    const timer = setTimeout(() => commit(draft, false), 600);
    return () => clearTimeout(timer);
    // eslint-disable-next-line
  }, [draft]);

  return (
    <input
      type="number"
      className="find-slot-number"
      value={draft}
      onChange={(e) => setDraft(e.target.value)}
      onBlur={() => commit(draft, true)}
      onKeyDown={(e) => {
        if (e.key === "Enter") e.currentTarget.blur();
      }}
      {...inputProps}
    />
  );
};

// Preset chips plus "Custom", which opens a box for any other value. A saved
// value that is not a preset opens the box on its own.
const ChipGroup = ({ label, options, value, onChange, renderCustom }) => {
  const [customOpen, setCustomOpen] = useState(false);
  const isPreset = options.some((option) => option.value === value);
  const showCustom = customOpen || !isPreset;

  return (
    <div className="find-slot-row">
      <span className="find-slot-row-label">{label}</span>
      <div className="find-slot-chips" role="radiogroup" aria-label={label}>
        {options.map((option) => {
          const selected = !showCustom && value === option.value;
          return (
            <button
              key={option.value}
              type="button"
              role="radio"
              aria-checked={selected}
              className={`find-slot-chip ${selected ? "selected" : ""}`}
              onClick={() => {
                setCustomOpen(false);
                onChange(option.value);
              }}
            >
              {option.short || option.label}
            </button>
          );
        })}
        <button
          type="button"
          role="radio"
          aria-checked={showCustom}
          className={`find-slot-chip ${showCustom ? "selected" : ""}`}
          onClick={() => setCustomOpen(true)}
        >
          Custom
        </button>
        {showCustom && <span className="find-slot-custom">{renderCustom()}</span>}
      </div>
    </div>
  );
};

export const FindSlotPanel = ({ onFindSlots, onPickSlot, onClose }) => {
  // null until the saved choices are read, so the first search uses them.
  const [prefs, setPrefs] = useState(null);
  const [hours, setHours] = useState(null);
  const [lengthUnit, setLengthUnit] = useState("min");
  const [slots, setSlots] = useState(null);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState(null);
  const [showTip, setShowTip] = useState(false);
  const latestRequest = useRef(0);

  useEffect(() => {
    chrome.storage.local
      .get([SLOT_HOURS_KEY, SLOT_PREFS_KEY])
      .catch(() => ({}))
      .then((stored) => {
        const saved = validSlotPrefs(stored[SLOT_PREFS_KEY]);
        setPrefs(saved);
        setLengthUnit(saved.durationMinutes % 60 === 0 ? "hours" : "min");
        setHours(validSlotHours(stored[SLOT_HOURS_KEY]));
      });
  }, []);

  const updatePrefs = (changes) => {
    const next = { ...prefs, ...changes };
    setPrefs(next);
    chrome.storage.local.set({ [SLOT_PREFS_KEY]: next }).catch(() => {});
  };

  const changeHours = (first, last) => {
    // Keep the end after the start, whichever one moved.
    const next = last > first ? [first, last] : [first, Math.min(first + 1, 24)];
    setHours(next);
    chrome.storage.local.set({ [SLOT_HOURS_KEY]: next }).catch(() => {});
  };

  // Search as soon as the panel opens and whenever a choice changes; only the
  // newest request may update the list.
  useEffect(() => {
    if (!prefs || !hours) return;
    const request = ++latestRequest.current;
    setSearching(true);
    onFindSlots({ ...prefs, workingHours: hours })
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
  }, [prefs, hours]);

  const groups = slots ? groupSlotsByDay(slots) : [];
  const ready = prefs && hours;
  const searchedFor = ready
    ? `${lengthWords(prefs.durationMinutes)} free between ${formatHour(hours[0])} and ${formatHour(
        hours[1]
      )} ${rangeWords(prefs.days)}`
    : "";

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

      {!ready ? (
        <div className="find-slot-status">Loading…</div>
      ) : (
        <>
          <ChipGroup
            label="Length"
            options={SLOT_DURATION_OPTIONS}
            value={prefs.durationMinutes}
            onChange={(durationMinutes) => updatePrefs({ durationMinutes })}
            renderCustom={() => (
              <>
                <NumberField
                  aria-label="Custom length"
                  min={lengthUnit === "hours" ? 0.25 : LENGTH_LIMITS.min}
                  max={lengthUnit === "hours" ? LENGTH_LIMITS.max / 60 : LENGTH_LIMITS.max}
                  step={lengthUnit === "hours" ? 0.5 : 5}
                  model={prefs.durationMinutes}
                  fromModel={(minutes) =>
                    lengthUnit === "hours" ? Math.round((minutes / 60) * 100) / 100 : minutes
                  }
                  toModel={(n) => clampLength(lengthUnit === "hours" ? n * 60 : n)}
                  onCommit={(durationMinutes) => updatePrefs({ durationMinutes })}
                />
                <select
                  className="find-slot-select"
                  aria-label="Length unit"
                  value={lengthUnit}
                  onChange={(e) => setLengthUnit(e.target.value)}
                >
                  <option value="min">min</option>
                  <option value="hours">hours</option>
                </select>
              </>
            )}
          />
          <ChipGroup
            label="Within"
            options={RANGE_OPTIONS}
            value={prefs.days}
            onChange={(days) => updatePrefs({ days })}
            renderCustom={() => (
              <>
                <NumberField
                  aria-label="Custom number of days"
                  min={DAY_LIMITS.min}
                  max={DAY_LIMITS.max}
                  step={1}
                  model={prefs.days}
                  fromModel={(days) => days}
                  toModel={clampDays}
                  onCommit={(days) => updatePrefs({ days })}
                />
                <span>days</span>
              </>
            )}
          />
          <div className="find-slot-row">
            <span className="find-slot-row-label">Hours</span>
            <div className="find-slot-hours">
              <select
                className="find-slot-select"
                aria-label="Earliest start"
                value={hours[0]}
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
                value={hours[1]}
                onChange={(e) => changeHours(hours[0], Number(e.target.value))}
              >
                {END_HOURS.filter((hour) => hour > hours[0]).map((hour) => (
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
                checked={prefs.includeWeekends}
                onChange={(e) => updatePrefs({ includeWeekends: e.target.checked })}
              />
              Include weekends
            </label>
          </div>
        </>
      )}

      {ready && (
        <div className={`find-slot-results ${searching ? "is-searching" : ""}`}>
          {searching && slots === null ? (
            <div className="find-slot-status">Checking your calendar…</div>
          ) : error ? (
            <div className="find-slot-status">{error}</div>
          ) : groups.length === 0 ? (
            <div className="find-slot-status">
              No times with {searchedFor}
              {prefs.includeWeekends ? "" : " on weekdays"}. Try a shorter length,
              wider hours or a longer range.
            </div>
          ) : (
            <>
              <div className="find-slot-summary">
                Times with {searchedFor}. Pick one to start an event.
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
      )}
    </div>
  );
};
