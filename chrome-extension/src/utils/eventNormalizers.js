// Event normalization utilities
import { ensureUniqueEmails, parseAttendeeInput } from "./emailUtils";

export const normalizeEventPayload = (event) => {
  if (!event) return null;
  const attendeesArray = Array.isArray(event.attendees)
    ? ensureUniqueEmails(event.attendees)
    : typeof event.attendees === "string"
    ? parseAttendeeInput(event.attendees)
    : [];

  const reminderValue =
    event.reminder === undefined || event.reminder === null
      ? "none"
      : String(event.reminder);

  return {
    ...event,
    attendees: attendeesArray,
    add_conference:
      typeof event.add_conference === "boolean"
        ? event.add_conference
        : Boolean(event.add_conference),
    reminder: reminderValue,
  };
};

