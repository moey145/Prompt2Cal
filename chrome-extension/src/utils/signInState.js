// Sign-in state the popup reads back from storage.
//
// The sign-in runs in the background worker and outlives the popup, so these
// rules decide what the reopened popup should show.
import { SESSION_PATTERN } from "./constants.js";

// A sign-in left open this long is treated as abandoned, so a button cannot
// stay stuck on "Connecting...".
export const SIGN_IN_TIMEOUT_MS = 5 * 60 * 1000;

/** Only sessions the backend issued at sign-in are usable. */
export const isIssuedSession = (value) =>
  typeof value === "string" && SESSION_PATTERN.test(value);

/**
 * Which provider's button should still show "Connecting...", if any.
 * Returns "google", "microsoft", or null when nothing is pending or it is stale.
 */
export const pendingSignInProvider = (stored, now = Date.now()) => {
  if (!stored || !stored.waitingForAuth) return null;
  const startedAt = stored.authStartedAt;
  if (!startedAt || now - startedAt > SIGN_IN_TIMEOUT_MS) return null;
  return stored.waitingForAuth === "microsoft" ? "microsoft" : "google";
};
