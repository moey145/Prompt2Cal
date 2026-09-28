// What each calendar can actually do, so the UI only offers real options.

export const isOutlook = (calendarProvider) => calendarProvider === "microsoft";

/** Graph has no per-event colour; it uses the mailbox's named categories. */
export const supportsEventColour = (calendarProvider) => !isOutlook(calendarProvider);

export const supportsCategories = (calendarProvider) => isOutlook(calendarProvider);

export const meetingLabels = (calendarProvider) =>
  isOutlook(calendarProvider)
    ? { field: "Teams meeting", checkbox: "Add Teams meeting link", generated: "Teams meeting link will be generated" }
    : { field: "Google Meet", checkbox: "Add Google Meet link", generated: "Google Meet link will be generated" };
