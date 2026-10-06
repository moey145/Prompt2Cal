// Prompt2Cal Chrome Extension - Background Service Worker

// Must match src/utils/parseJob.js.
const PARSE_JOB_KEY = "prompt2cal_parse_job";
// The popup records which backend it talks to, so a parse started from the
// right-click menu (with no popup open) goes to the same one.
const API_BASE_KEY = "prompt2cal_api_base";
const DEFAULT_API_BASE = "https://prompt2cal-backend-139801429107.us-central1.run.app";
const MENU_ID = "prompt2cal-add-selection";
// Must match MAX_EVENT_TEXT_CHARS in backend/models/event_models.py.
const MAX_TEXT_CHARS = 2000;

class Prompt2CalBackground {
  constructor() {
    this.setupEventListeners();
  }

  setupEventListeners() {
    // Handle extension installation
    chrome.runtime.onInstalled.addListener((details) => {
      this.handleInstallation(details);
    });

    // Right-click on selected text: "Add to calendar with Prompt2Cal".
    chrome.contextMenus.onClicked.addListener((info) => {
      this.handleContextMenu(info);
    });

    // Handle messages from content scripts and popup
    chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
      this.handleMessage(request, sender, sendResponse);
      return true; // Keep message channel open for async responses
    });
  }

  handleInstallation(details) {
    // Menus persist once created, so they are (re)made on install and update.
    this.createContextMenu();

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

        case "parseEvent":
          // Runs here so the parse finishes even if the popup is closed; the
          // popup picks the result up from storage whenever it next opens.
          await this.markParseStarted(request.jobId, request.payload?.text);
          sendResponse({ started: true });
          await this.runParseJob(request);
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
      // Clearing this releases the "Connecting..." state on the popup's button.
      await chrome.storage.local.remove(["waitingForAuth", "authStartedAt"]);
    }
  }

  createContextMenu() {
    chrome.contextMenus.removeAll(() => {
      chrome.contextMenus.create({
        id: MENU_ID,
        title: "Add to calendar with Prompt2Cal",
        contexts: ["selection"],
      });
    });
  }

  async handleContextMenu(info) {
    if (info.menuItemId !== MENU_ID) return;
    const text = (info.selectionText || "").trim();
    if (!text) return;

    // Open the popup while Chrome still counts this as the user's click; it
    // shows "Parsing..." and then the preview. Where Chrome does not allow
    // it, the badge says when the result is ready.
    if (chrome.action.openPopup) {
      chrome.action.openPopup().catch(() => {});
    }

    const jobId = crypto.randomUUID();
    await this.markParseStarted(jobId, text);
    const stored = await chrome.storage.local.get([API_BASE_KEY, "prompt2cal_user_id"]);
    await this.runParseJob({
      jobId,
      apiBase: stored[API_BASE_KEY] || DEFAULT_API_BASE,
      payload: {
        text,
        user_id: stored.prompt2cal_user_id || null,
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        force_multiple: null,
      },
    });
  }

  async markParseStarted(jobId, text) {
    await chrome.storage.local.set({
      // The text goes with the job so the popup can show what is being read.
      [PARSE_JOB_KEY]: { id: jobId, status: "pending", startedAt: Date.now(), text: text || "" },
    });
    await this.setBadge("…", "#6b7280");
  }

  async runParseJob({ jobId, apiBase, payload }) {
    if ((payload?.text || "").length > MAX_TEXT_CHARS) {
      await this.finishParseJob(jobId, {
        status: "error",
        error: `That text is too long. Use up to ${MAX_TEXT_CHARS.toLocaleString()} characters.`,
      });
      return;
    }
    try {
      const response = await fetch(`${apiBase}/create_event`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok || !data.success) {
        // Validation errors arrive as a list rather than a sentence.
        throw new Error(typeof data.detail === "string" ? data.detail : "");
      }
      await this.finishParseJob(jobId, { status: "done", response: data });
    } catch (error) {
      console.error("Background parse failed:", error);
      // The backend's messages are written for the user; a fetch that never
      // reached it throws a TypeError with nothing useful to show.
      const message =
        error instanceof TypeError
          ? "Couldn't reach Prompt2Cal. Check your connection and try again."
          : error.message || "Something went wrong reading that. Please try again.";
      await this.finishParseJob(jobId, { status: "error", error: message });
    }
  }

  async finishParseJob(jobId, fields) {
    const stored = await chrome.storage.local.get([PARSE_JOB_KEY]);
    const current = stored[PARSE_JOB_KEY];
    // A newer parse replaced this one; its result is no longer wanted.
    if (!current || current.id !== jobId) return;
    await chrome.storage.local.set({
      [PARSE_JOB_KEY]: { ...current, ...fields, finishedAt: Date.now() },
    });
    // The popup clears this as soon as it shows the result.
    if (fields.status === "done") {
      await this.setBadge("1", "#16a34a");
    } else {
      await this.setBadge("!", "#dc2626");
    }
  }

  async setBadge(text, colour) {
    try {
      await chrome.action.setBadgeBackgroundColor({ color: colour });
      await chrome.action.setBadgeText({ text });
    } catch (error) {
      console.error("Could not set the badge:", error);
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
