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
