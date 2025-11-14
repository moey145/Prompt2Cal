# Chrome Web Store Privacy & Permissions Form

## Single Purpose Description

**Copy this (under 1000 characters):**

```
Prompt2Cal converts natural language text into Google Calendar events. Users type or speak event descriptions (e.g., "Meeting tomorrow at 2pm"), and the extension parses the text, extracts event details, and creates calendar entries in the user's Google Calendar. The extension's sole purpose is to simplify calendar event creation through natural language processing.
```

## Permission Justifications

### activeTab Justification

**Copy this:**

```
The activeTab permission allows Prompt2Cal to access the currently active browser tab when users select text on a webpage to create calendar events. This enables the "Use Selected Text" feature, where users can highlight event descriptions on any webpage and convert them to calendar events. The extension only accesses the tab when the user explicitly clicks the extension icon or uses the selected text feature.
```

### storage Justification

**Copy this:**

```
The storage permission is required to save user preferences and settings locally, including the selected Google Calendar ID, authentication state, theme preferences (dark/light mode), and user ID for session management. All data is stored locally in the browser and never transmitted to third parties.
```

### identity Justification

**Copy this:**

```
The identity permission is used to generate a unique user ID for each extension installation. This user ID is necessary to associate Google Calendar OAuth tokens with the correct user session when connecting to the backend API. The identity API provides a stable, privacy-preserving identifier that doesn't reveal personal information.
```

### scripting Justification

**Copy this:**

```
The scripting permission is required to inject content scripts that detect and highlight selectable text on web pages. This enables users to select event descriptions from any webpage and create calendar events from them. The extension only injects scripts when the user explicitly interacts with the extension.
```

### Host Permission Justification

**Copy this:**

```
Host permissions are required for the following purposes:

1. https://prompt2cal-backend-139801429107.us-central1.run.app/* - This is the backend API endpoint that processes natural language text and creates calendar events. All event parsing and Google Calendar API interactions occur through this secure backend service.

2. https://accounts.google.com/* and https://www.googleapis.com/* - These permissions are required for Google Calendar OAuth authentication. The extension needs to authenticate users with Google Calendar to create events on their behalf. This follows Google's OAuth 2.0 standard flow for calendar access.

The extension does not access any other websites or domains beyond these specified endpoints.
```

## Remote Code

**Select: "Yes, I am using Remote code"**

**Justification:**

```
The extension communicates with a remote backend API (prompt2cal-backend-139801429107.us-central1.run.app) to process natural language text and interact with Google Calendar. The backend service handles:
- Natural language processing using AI models
- Google Calendar API authentication and event creation
- Date/time parsing and event conflict detection

All API calls are made to our own secure backend service. No third-party scripts or external code is loaded into the extension.
```

## Data Usage

**Select the following checkboxes:**

- ✅ **Personally identifiable information** - User's Google account email (for calendar authentication)
- ✅ **User activity** - Text input for event descriptions (only when user explicitly types or selects text)
- ✅ **Website content** - Selected text from web pages (only when user explicitly selects text to create events)

**Do NOT select:**
- ❌ Health information
- ❌ Financial and payment information
- ❌ Authentication information (we don't store passwords)
- ❌ Personal communications
- ❌ Location
- ❌ Web history

**Certifications - Check all three:**

- ✅ I do not sell or transfer user data to third parties, apart from the approved use cases
- ✅ I do not use or transfer user data for purposes that are unrelated to my item's single purpose
- ✅ I do not use or transfer user data to determine creditworthiness or for lending purposes

## Privacy Policy URL

**Enter this:**

```
https://moey145.github.io/Prompt2Cal/privacy-policy.html
```

---

## Summary

- **Single Purpose**: Convert natural language to calendar events
- **Permissions**: All justified for core functionality
- **Remote Code**: Yes (backend API)
- **Data Collected**: Google account email, user input text, selected webpage text
- **Privacy Policy**: https://moey145.github.io/Prompt2Cal/privacy-policy.html


