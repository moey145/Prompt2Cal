// Constants
// Backend URL - set via environment variable VITE_API_BASE or default to Cloud Run for production
// Local backend while developing Microsoft Calendar + confidence features.
// For production/store builds, set VITE_API_BASE to your Cloud Run URL.
const viteEnv = typeof import.meta.env === "object" ? import.meta.env : {};
export const API_BASE = viteEnv.VITE_API_BASE || "http://localhost:8000";

// Sessions are issued by the backend when a calendar sign-in completes.
export const SESSION_PATTERN = /^s_[A-Za-z0-9_-]{43}$/;

export const RECURRENCE_OPTIONS = [
  { value: "none", label: "Does not repeat" },
  { value: "daily", label: "Daily" },
  { value: "weekly", label: "Weekly" },
  { value: "monthly", label: "Monthly" },
  { value: "yearly", label: "Yearly" },
];

export const SLOT_DURATION_OPTIONS = [
  { value: 30, label: "30 minutes", short: "30m" },
  { value: 45, label: "45 minutes", short: "45m" },
  { value: 60, label: "1 hour", short: "1h" },
  { value: 90, label: "1.5 hours", short: "1.5h" },
  { value: 120, label: "2 hours", short: "2h" },
];

export const EVENT_COLORS = [
  "#d50000", // Tomato (11)
  "#e67c73", // Flamingo (4)
  "#f4511e", // Tangerine (6)
  "#f6bf26", // Banana (5)
  "#33b679", // Sage (2)
  "#0b8043", // Basil (10)
  "#039be5", // Peacock (7)
  "#3f51b5", // Blueberry (9)
  "#7986cb", // Lavender (1)
  "#8e24aa", // Grape (3)
  "#616161", // Graphite (8)
];

// Google Calendar's names for the colours above, in the same order.
export const EVENT_COLOR_NAMES = {
  "#d50000": "Tomato",
  "#e67c73": "Flamingo",
  "#f4511e": "Tangerine",
  "#f6bf26": "Banana",
  "#33b679": "Sage",
  "#0b8043": "Basil",
  "#039be5": "Peacock",
  "#3f51b5": "Blueberry",
  "#7986cb": "Lavender",
  "#8e24aa": "Grape",
  "#616161": "Graphite",
};

export const REMINDER_OPTIONS = [
  { value: "none", label: "No reminder" },
  { value: "5", label: "5 minutes before" },
  { value: "10", label: "10 minutes before" },
  { value: "15", label: "15 minutes before" },
  { value: "30", label: "30 minutes before" },
  { value: "60", label: "1 hour before" },
  { value: "120", label: "2 hours before" },
  { value: "1440", label: "1 day before" },
  { value: "2880", label: "2 days before" },
];

export const DEFAULT_COLOR = "#3f51b5";
export const DEFAULT_REMINDER = "none";

