// Whether the free-slot search can run, and what to tell the user when it fails.

// A backend that predates the capability list only searched Google calendars.
const LEGACY_PROVIDERS = ["google"];

export const slotFinderProviders = (health) =>
  Array.isArray(health?.slot_finder_providers) ? health.slot_finder_providers : LEGACY_PROVIDERS;

export const slotFinderSupported = (health, provider) =>
  Boolean(provider) && slotFinderProviders(health).includes(provider);

export const providerName = (provider) => (provider === "microsoft" ? "Outlook" : "Google");

// The backend's 409 detail is already written for the user; anything else is
// technical, so it is replaced rather than shown.
export const slotSearchErrorMessage = (error, provider) => {
  if (error?.status === 409 && error.message) return error.message;
  if (error?.status === 401) return `Connect ${providerName(provider)} Calendar in Settings to find free slots.`;
  return "Couldn't check your calendar. Try again in a moment.";
};

// The hours to search between, remembered between visits; 24 means midnight.
export const SLOT_HOURS_KEY = "prompt2cal_slot_hours";
export const DEFAULT_SLOT_HOURS = [9, 17];

/** "midnight", "9am", "noon", "5pm". */
export const formatHour = (hour) => {
  if (hour === 0 || hour === 24) return "midnight";
  if (hour === 12) return "noon";
  return hour < 12 ? `${hour}am` : `${hour - 12}pm`;
};

/** Saved hours if they still make sense, otherwise 9am to 5pm. */
export const validSlotHours = (value) =>
  Array.isArray(value) &&
  value.length === 2 &&
  Number.isInteger(value[0]) &&
  Number.isInteger(value[1]) &&
  value[0] >= 0 &&
  value[0] < value[1] &&
  value[1] <= 24
    ? value
    : DEFAULT_SLOT_HOURS;

// Length, range and weekend choice, remembered between visits.
export const SLOT_PREFS_KEY = "prompt2cal_slot_prefs";
export const LENGTH_LIMITS = { min: 5, max: 720 }; // minutes: 5 minutes to 12 hours
export const DAY_LIMITS = { min: 1, max: 30 };
export const DEFAULT_SLOT_PREFS = { durationMinutes: 60, days: 3, includeWeekends: false };

const clampWhole = (value, { min, max }, fallback) => {
  const number = Math.round(Number(value));
  return Number.isFinite(number) ? Math.min(max, Math.max(min, number)) : fallback;
};

export const clampLength = (minutes) =>
  clampWhole(minutes, LENGTH_LIMITS, DEFAULT_SLOT_PREFS.durationMinutes);

export const clampDays = (days) => clampWhole(days, DAY_LIMITS, DEFAULT_SLOT_PREFS.days);

export const validSlotPrefs = (saved) => ({
  durationMinutes: clampLength(saved?.durationMinutes ?? DEFAULT_SLOT_PREFS.durationMinutes),
  days: clampDays(saved?.days ?? DEFAULT_SLOT_PREFS.days),
  includeWeekends: Boolean(saved?.includeWeekends),
});

/** "45 minutes", "1 hour", "2 hours 30 minutes". */
export const lengthWords = (minutes) => {
  const hours = Math.floor(minutes / 60);
  const rest = minutes % 60;
  const parts = [];
  if (hours) parts.push(`${hours} hour${hours === 1 ? "" : "s"}`);
  if (rest) parts.push(`${rest} minute${rest === 1 ? "" : "s"}`);
  return parts.join(" ");
};

/** "today", "in the next 10 days". */
export const rangeWords = (days) => (days === 1 ? "today" : `in the next ${days} days`);
