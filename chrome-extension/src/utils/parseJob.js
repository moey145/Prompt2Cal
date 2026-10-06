// A parse runs in the background worker so it survives the popup closing.
// The worker records the job in storage; the popup reads it when it opens,
// and keeps the resulting preview until the user creates or cancels it.

export const PARSE_JOB_KEY = "prompt2cal_parse_job";
export const PREVIEW_KEY = "prompt2cal_preview";

// A job still "pending" after this was cut off (the worker was stopped).
export const PARSE_TIMEOUT_MS = 2 * 60 * 1000;
// Relative dates such as "tomorrow" go stale, so an old preview is dropped.
export const PREVIEW_MAX_AGE_MS = 12 * 60 * 60 * 1000;

/** "none", "pending", "stalled", "done" or "error". */
export const parseJobState = (job, now = Date.now()) => {
  if (!job || typeof job !== "object") return "none";
  if (job.status === "pending") {
    return now - (job.startedAt || 0) > PARSE_TIMEOUT_MS ? "stalled" : "pending";
  }
  if (job.status === "done" && job.response) return "done";
  if (job.status === "error") return "error";
  return "none";
};

/** What to save for the preview on screen, or null when there is none. */
export const previewToSave = ({ showParsedEvent, parsedEvent, showBulkEvents, parsedEvents }, now = Date.now()) => {
  if (showParsedEvent && parsedEvent) {
    return { kind: "single", event: parsedEvent, savedAt: now };
  }
  if (showBulkEvents && parsedEvents && parsedEvents.length) {
    return { kind: "bulk", events: parsedEvents, savedAt: now };
  }
  return null;
};

/** A saved preview worth showing again, or null. */
export const previewToRestore = (saved, now = Date.now()) => {
  if (!saved || now - (saved.savedAt || 0) > PREVIEW_MAX_AGE_MS) return null;
  if (saved.kind === "single" && saved.event) return saved;
  if (saved.kind === "bulk" && Array.isArray(saved.events) && saved.events.length) return saved;
  return null;
};
