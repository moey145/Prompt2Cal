// Prompt2Cal Chrome Extension - Content Script
// This script runs on all web pages to detect text selection

console.log("Prompt2Cal content script loaded on:", window.location.href);

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
      console.log("Content script: Received message:", request);
      if (request.action === "getSelectedText") {
        this.getSelectedText();
        console.log(
          "Content script: Sending selected text:",
          this.selectedText
        );
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

    console.log("Content script: Text selection changed:", {
      text,
      length: text.length,
      previousText: this.selectedText,
    });

    if (text && text !== this.selectedText && text.length > 5) {
      this.selectedText = text;
      console.log("Content script: Text selected:", text);
    } else if (!text) {
      this.selectedText = "";
      console.log("Content script: No text selected");
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
  console.log("Prompt2Cal content script initializing...");
  window.prompt2calContentScript = new Prompt2CalContentScript();
  console.log("Prompt2Cal content script initialized successfully");
} else {
  console.log("Prompt2Cal content script already initialized");
}
