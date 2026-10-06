// Prompt2Cal Chrome Extension - Content Script
// This script runs on all web pages to detect text selection


class Prompt2CalContentScript {
  constructor() {
    this.selectedText = "";
    // Remove any existing hints from previous versions
    const existingHint = document.getElementById("prompt2cal-hint");
    if (existingHint) {
      existingHint.remove();
    }
    this.setupEventListeners();
  }

  setupEventListeners() {
    // Listen for messages from popup
    chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
      if (request.action === "getSelectedText") {
        this.getSelectedText();
        sendResponse({ selectedText: this.selectedText });
        return true; // Indicate that we will send a response
      }
    });

    // Listen for text selection changes
    document.addEventListener("mouseup", () => {
      setTimeout(() => this.handleTextSelection(), 100);
    });

    document.addEventListener("keyup", () => {
      setTimeout(() => this.handleTextSelection(), 100);
    });
  }

  handleTextSelection() {
    const selection = window.getSelection();
    const text = selection.toString().trim();


    if (text && text !== this.selectedText && text.length > 5) {
      this.selectedText = text;
    } else if (!text) {
      this.selectedText = "";
    }
  }

  getSelectedText() {
    const selection = window.getSelection();
    this.selectedText = selection.toString().trim();
    return this.selectedText;
  }
}

// Initialize content script only if not already initialized
if (!window.prompt2calContentScript) {
  window.prompt2calContentScript = new Prompt2CalContentScript();
} else {
}
