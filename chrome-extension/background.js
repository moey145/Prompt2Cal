// Prompt2Cal Chrome Extension - Background Service Worker

class Prompt2CalBackground {
  constructor() {
    this.setupEventListeners();
  }

  setupEventListeners() {
    // Handle extension installation
    chrome.runtime.onInstalled.addListener((details) => {
      this.handleInstallation(details);
    });

    // Handle messages from content scripts and popup
    chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
      this.handleMessage(request, sender, sendResponse);
      return true; // Keep message channel open for async responses
    });
  }

  handleInstallation(details) {
    if (details.reason === "install") {
      console.log("Prompt2Cal extension installed");

      // Set default settings
      chrome.storage.local.set({
        prompt2cal_settings: {
          api_base: "https://prompt2cal-backend-139801429107.us-central1.run.app",
          auto_parse_selected: true,
          show_hints: true,
        },
      });
    }
  }

  async handleMessage(request, sender, sendResponse) {
    try {
      switch (request.action) {
        case "checkBackendStatus":
          const status = await this.checkBackendStatus();
          sendResponse({ status });
          break;

        case "getSettings":
          const settings = await this.getSettings();
          sendResponse({ settings });
          break;

        case "updateSettings":
          await this.updateSettings(request.settings);
          sendResponse({ success: true });
          break;

        case "startOAuth":
          // Runs here rather than in the popup, which closes as soon as the
          // sign-in window takes focus.
          sendResponse({ started: true });
          await this.startOAuth(request);
          break;

        default:
          sendResponse({ error: "Unknown action" });
      }
    } catch (error) {
      console.error("Background script error:", error);
      sendResponse({ error: error.message });
    }
  }

  // Sign in to a calendar provider. The backend issues a new session when
  // sign-in completes and redirects to this extension's chrome.identity URL,
  // the only place the session is ever delivered.
  async startOAuth({ provider, apiBase, previousSession }) {
    try {
      const params = new URLSearchParams({
        redirect_uri: chrome.identity.getRedirectURL("oauth"),
      });
      if (previousSession) {
        params.set("user_id", previousSession);
      }
      const endpoint = provider === "microsoft" ? "/auth/microsoft" : "/auth/google";
      const response = await fetch(`${apiBase}${endpoint}?${params}`);
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data.detail || `HTTP ${response.status}`);
      }

      const finalUrl = await chrome.identity.launchWebAuthFlow({
        url: data.auth_url,
        interactive: true,
      });
      const result = new URLSearchParams(new URL(finalUrl).hash.slice(1));
      const session = result.get("session");
      if (!session) {
        throw new Error(
          result.get("error") === "access_denied"
            ? "Calendar access was not granted."
            : "Sign-in failed. Please try again."
        );
      }
      await chrome.storage.local.set({
        prompt2cal_user_id: session,
        calendar_provider: provider,
      });
    } catch (error) {
      console.error("Sign-in failed:", error);
      await chrome.storage.local.set({
        prompt2cal_auth_error: error.message || "Sign-in failed. Please try again.",
      });
    } finally {
      await chrome.storage.local.remove(["waitingForAuth"]);
    }
  }

  async checkBackendStatus() {
    try {
      const settings = await this.getSettings();
      const response = await fetch(`${settings.api_base}/`);

      if (response.ok) {
        const data = await response.json();
        return {
          online: true,
          message: data.message || "Backend is running",
        };
      } else {
        return {
          online: false,
          message: `Backend returned ${response.status}`,
        };
      }
    } catch (error) {
      return {
        online: false,
        message: "Backend is not accessible",
      };
    }
  }

  async getSettings() {
    const result = await chrome.storage.local.get(["prompt2cal_settings"]);
    return (
      result.prompt2cal_settings || {
        api_base: "https://prompt2cal-backend-139801429107.us-central1.run.app",
        auto_parse_selected: true,
        show_hints: true,
      }
    );
  }

  async updateSettings(newSettings) {
    const currentSettings = await this.getSettings();
    const updatedSettings = { ...currentSettings, ...newSettings };
    await chrome.storage.local.set({ prompt2cal_settings: updatedSettings });
  }
}

// Initialize background script
new Prompt2CalBackground();
