// Constants
// Backend URL - set via environment variable VITE_API_BASE or default to Cloud Run for production
export const API_BASE = import.meta.env.VITE_API_BASE || "https://prompt2cal-backend-139801429107.us-central1.run.app";

export const EVENT_COLORS = [
  "#4285f4",
  "#ea4335",
  "#fbbc04",
  "#34a853",
  "#9c27b0",
  "#ff9800",
  "#795548",
  "#607d8b",
];

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

export const DEFAULT_COLOR = "#4285f4";
export const DEFAULT_REMINDER = "none";

