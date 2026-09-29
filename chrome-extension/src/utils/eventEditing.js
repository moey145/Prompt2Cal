// Rules for the edit dialog's fields, kept out of the component so they are
// testable on their own.

const DEFAULT_MINUTES = 60;

const toDate = (value) => {
  if (!value) return null;
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? null : date;
};

/** The value a datetime-local input expects, or "" for a missing time. */
export const toInputValue = (iso) => {
  const date = toDate(iso);
  if (!date) return "";
  const pad = (n) => String(n).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(
    date.getHours()
  )}:${pad(date.getMinutes())}`;
};

/** Minutes between start and end, or null when either is missing. */
export const minutesBetween = (startIso, endIso) => {
  const start = toDate(startIso);
  const end = toDate(endIso);
  if (!start || !end) return null;
  return Math.round((end - start) / 60000);
};

/**
 * Fields to change when the start moves: the end moves with it, keeping the
 * length the event had, so editing the start never leaves the end behind it.
 */
export const fieldsForStart = (event, inputValue) => {
  const start = toDate(inputValue);
  if (!start) return null;
  const current = minutesBetween(event?.start_time, event?.end_time);
  const minutes = current && current > 0 ? current : event?.duration_minutes || DEFAULT_MINUTES;
  return {
    start_time: start.toISOString(),
    end_time: new Date(start.getTime() + minutes * 60000).toISOString(),
    duration_minutes: minutes,
  };
};

/** Fields to change when the end moves; the length follows it. */
export const fieldsForEnd = (event, inputValue) => {
  const end = toDate(inputValue);
  if (!end) return null;
  const minutes = minutesBetween(event?.start_time, end.toISOString());
  return {
    end_time: end.toISOString(),
    ...(minutes && minutes > 0 ? { duration_minutes: minutes } : {}),
  };
};

/** "45 min", "1 hr", "1 hr 30 min", "2 days". */
export const formatDuration = (minutes) => {
  if (!minutes || minutes <= 0) return "";
  if (minutes % 1440 === 0) {
    const days = minutes / 1440;
    return `${days} day${days === 1 ? "" : "s"}`;
  }
  const hours = Math.floor(minutes / 60);
  const rest = minutes % 60;
  if (!hours) return `${rest} min`;
  return rest ? `${hours} hr ${rest} min` : `${hours} hr`;
};

/** Problems that must be fixed before saving, by field; empty when valid. */
export const validateEvent = (event) => {
  const errors = {};
  if (!event?.title || !event.title.trim()) {
    errors.title = "Add a title.";
  }
  const start = toDate(event?.start_time);
  const end = toDate(event?.end_time);
  if (!start) {
    errors.start_time = "Add a start time.";
  } else if (end && end <= start) {
    errors.end_time = "The end must be after the start.";
  }
  if (start && event?.end_date) {
    const seriesEnd = toDate(`${String(event.end_date).slice(0, 10)}T23:59:59`);
    if (seriesEnd && seriesEnd < start) {
      errors.end_date = "The series can't end before it starts.";
    }
  }
  return errors;
};
