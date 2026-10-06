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
