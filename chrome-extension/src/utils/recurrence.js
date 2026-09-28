// Repeat settings for the edit dialog, kept out of the component so the rules
// are testable on their own.

export const INTERVAL_UNITS = {
  daily: "day(s)",
  weekly: "week(s)",
  monthly: "month(s)",
  yearly: "year(s)",
};

export const isRecurring = (event) =>
  Boolean(event && event.recurrence_type && event.recurrence_type !== "none");

export const intervalUnitLabel = (recurrenceType) => INTERVAL_UNITS[recurrenceType];

/** Which ending the event currently describes: never, after N, or on a date. */
export const recurrenceEndMode = (event) => {
  if (!event) return "never";
  if (event.recurrence_count) return "count";
  if (event.end_date) return "date";
  return "never";
};

/** Three months out, so "Ends: on…" starts somewhere sensible. */
export const defaultRecurrenceEndDate = (startTime) => {
  const start = startTime ? new Date(startTime) : new Date();
  const base = Number.isNaN(start.getTime()) ? new Date() : start;
  const end = new Date(base);
  end.setMonth(end.getMonth() + 3);
  return end.toISOString().slice(0, 10);
};

/** The fields to change when the repeat pattern changes. */
export const fieldsForRecurrenceType = (recurrenceType) => {
  if (recurrenceType === "none") {
    // Settings that only make sense for a series.
    return {
      recurrence_type: "none",
      recurrence_count: null,
      end_date: null,
      recurrence_interval: 1,
    };
  }
  return { recurrence_type: recurrenceType };
};

/** The fields to change when the ending changes. */
export const fieldsForEndMode = (mode, event) => {
  if (mode === "count") {
    return { end_date: null, recurrence_count: (event && event.recurrence_count) || 5 };
  }
  if (mode === "date") {
    return {
      recurrence_count: null,
      end_date: (event && event.end_date) || defaultRecurrenceEndDate(event && event.start_time),
    };
  }
  return { recurrence_count: null, end_date: null };
};
