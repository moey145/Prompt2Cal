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

    // Handle tab updates (for auth callback)
    chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
      this.handleTabUpdate(tabId, changeInfo, tab);
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

        default:
          sendResponse({ error: "Unknown action" });
      }
    } catch (error) {
      console.error("Background script error:", error);
      sendResponse({ error: error.message });
    }
  }

  handleTabUpdate(tabId, changeInfo, tab) {
    // Handle OAuth callback
    if (changeInfo.status === "complete" && tab.url) {
      if (tab.url.includes("/auth/callback")) {
        // Auth callback detected, close the tab after a short delay
        // This gives time for the success/error page to load and show
        setTimeout(() => {
          chrome.tabs.remove(tabId).catch(() => {
            // Tab might already be closed
          });
        }, 3000); // Increased to 3 seconds to show the success message
      }
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
