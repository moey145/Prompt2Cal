// Backend Configuration for Chrome Extension
// This file contains the backend API configuration that the extension uses

const BACKEND_CONFIG = {
  // Default backend URL - change this if your backend runs on a different port/host
  API_BASE: "https://prompt2cal-backend-139801429107.us-central1.run.app",

  // API endpoints
  ENDPOINTS: {
    HEALTH: "/",
    CREATE_EVENT: "/create_event",
    CONFIRM_EVENT: "/confirm_event",
    AUTH_GOOGLE: "/auth/google",
    AUTH_CALLBACK: "/auth/callback",
    AUTH_STATUS: "/auth/status",
  },

  // Request timeout (milliseconds)
  TIMEOUT: 10000,

  // Retry configuration
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 1000,
};

// Export for use in other files
if (typeof module !== "undefined" && module.exports) {
  module.exports = BACKEND_CONFIG;
} else {
  window.BACKEND_CONFIG = BACKEND_CONFIG;
}
