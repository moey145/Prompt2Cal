// Timing checks shared by the confirm cards.

/**
 * True when a one-off event's start has already gone by.
 *
 * A bare weekday ("Dentist Thursday 10am") can resolve to earlier the same
 * day. A series is exempt: its first occurrence is often in the past by design.
 */
export const startsInThePast = (event, now = new Date()) => {
  if (!event || !event.start_time) return false;
  if (event.recurrence_type && event.recurrence_type !== "none") return false;
  const start = new Date(event.start_time);
  if (Number.isNaN(start.getTime())) return false;
  return start < now;
};
