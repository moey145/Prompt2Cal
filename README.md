# Prompt2Cal 📅

**Turn natural language into Google Calendar events instantly.**

Create calendar events by simply typing or speaking in plain English. No more clicking through multiple fields—just describe your event and let AI do the rest.

## 🚀 Get Started

**[Install from Chrome Web Store →](https://chrome.google.com/webstore)** (Search for "Prompt2Cal")

1. Click the extension icon in your browser
2. Connect your Google Calendar (one-time setup, stays connected for 14 days)
3. Start creating events with natural language!

## ✨ Key Features

### 🎤 **Voice Input**

Speak your events naturally—just click the microphone and talk. Perfect for hands-free event creation.

### 🤖 **AI-Powered Parsing**

Advanced AI understands natural language, so you can say things like:

- "Lunch with Sarah next Tuesday at 1pm"
- "Team meeting every Monday at 9am for the next month"
- "Doctor appointment tomorrow at 3:30pm"
- "Conference call with John on Friday at 2pm"

### ⚠️ **Smart Conflict Detection**

Automatically checks your calendar for scheduling conflicts before creating events, so you never double-book.

### 🔍 **Confidence Highlighting**

Before you create an event, fields the AI filled in that **weren't found in your text** are highlighted on the confirm screen — so you can catch hallucinated dates, times, or locations before they land on your calendar. End times inferred from a default duration (rather than something you stated) are labelled as **assumed**.

### 📋 **Selected Text**

Select text from any webpage and the extension will automatically detect it—perfect for quickly adding events from emails or web pages.

### 📅 **Bulk Event Creation**

Parse multiple events at once from a single text block. Great for importing schedules or meeting notes.

### 🔄 **Recurring Events**

Create repeating events with natural language:

- "Daily standup at 9am"
- "Weekly team meeting every Monday"
- "Monthly review on the first Friday"

### 🎨 **Fully Customizable**

- Choose event colors (Google Calendar palette)
- Set reminder notifications
- Add locations and attendees
- Select which calendar to use
- Connect **Google Calendar** or **Microsoft Outlook**
- Beautiful dark mode support

## 🎯 How It Works

1. **Type or speak** your event in natural language
2. **AI parses** your text into structured event data (Claude Sonnet 4.6)
3. **Review and confirm** the parsed details — ungrounded fields are highlighted
4. **Event is created** in your Google or Outlook calendar instantly

## 📖 Example Usage

**Input:** `"Lunch with Sarah next Tuesday at 1pm"`

**Output:** Creates a calendar event with:

- Title: "Lunch with Sarah"
- Date: Next Tuesday at 1:00 PM
- Duration: 1 hour (default)
- Automatically added to your selected Google Calendar

## 🔒 Privacy & Security

- Your data is processed securely through our backend API
- Google Calendar authentication uses OAuth2 (industry standard)
- No data is stored permanently—only processed to create your events
- Full privacy policy available at: [https://moey145.github.io/Prompt2Cal/privacy-policy.html](https://moey145.github.io/Prompt2Cal/privacy-policy.html)

## 🛠️ Technical Architecture

This project consists of:

### Chrome Extension (Frontend)

- **Tech Stack:** React + Vite, Lucide React Icons
- **Features:** Voice recognition, conflict detection, bulk parsing
- **Location:** `chrome-extension/`

### Backend API

- **Tech Stack:** FastAPI (Python), Claude Sonnet 4.6 (live parser), Google Calendar API, Microsoft Graph
- **Deployment:** Google Cloud Run
- **Features:** Natural language parsing, source-grounding confidence, event creation, OAuth2 handling
- **Location:** `backend/`

### Key Services

- **Rules Parser:** Deterministic parsing for common patterns
- **Intelligent Parser:** Claude-powered parsing for complex natural language
- **Confidence layer:** Source-grounding verifier applied to every live extraction
- **Calendar Service:** Google Calendar and Microsoft Outlook integration with conflict detection

### Research evaluation

The capstone benchmark, evaluation harness, verifier scoring, and reproduction commands are documented separately in **[RESEARCH.md](RESEARCH.md)** (not required to use the extension).

## 📁 Project Structure

```
Prompt2Cal/
├── chrome-extension/          # Chrome extension (React + Vite)
│   ├── src/                   # React components
│   ├── manifest.json          # Extension manifest
│   └── dist/                  # Built extension
├── backend/                   # FastAPI backend
│   ├── main.py                # API endpoints
│   ├── services/              # Parsing & calendar services
│   └── models/                # Data models
├── docs/                      # Documentation & website
│   ├── index.html             # Homepage
│   └── privacy-policy.html    # Privacy policy
├── benchmark/                 # Research benchmark dataset & artefacts
├── scripts/                   # Evaluation & analysis CLI scripts
├── RESEARCH.md                # Benchmark reproduction guide (capstone)
└── README.md                  # This file
```

## 🔧 Development

### Prerequisites

- Python 3.8+
- Node.js 16+
- Anthropic API key (live parser) and/or OpenAI API key (research harness)
- Google Cloud Project with Calendar API enabled (optional: Azure app for Outlook)

### Backend Setup

1. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**

   ```bash
   cp env.example .env
   # Edit .env: ANTHROPIC_API_KEY (live parser), GOOGLE_* / MS_* (calendar OAuth)
   ```

3. **Set up Google Calendar API:**

   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Enable the Google Calendar API
   - Create OAuth 2.0 credentials
   - Download the `credentials.json` file
   - Place `credentials.json` in the `backend/` directory

4. **Run locally:**
   ```bash
   cd backend
   python main.py
   ```

### Chrome Extension Setup

1. **Install dependencies:**

   ```bash
   cd chrome-extension
   npm install
   ```

2. **Build the extension:**

   ```bash
   npm run build
   ```

3. **Load in Chrome:**
   - Open `chrome://extensions/`
   - Enable "Developer mode"
   - Click "Load unpacked"
   - Select the `chrome-extension/dist` folder

### Deploying the Backend (Cloud Run)

Calendar tokens are stored in a Cloud Storage bucket mounted into the service, so sign-ins survive restarts and are shared across instances. Create the bucket once and let the service's runtime service account use it:

```bash
gcloud storage buckets create gs://PROJECT_ID-prompt2cal-tokens \
  --location=us-central1 --uniform-bucket-level-access --public-access-prevention
gcloud storage buckets add-iam-policy-binding gs://PROJECT_ID-prompt2cal-tokens \
  --member=serviceAccount:RUNTIME_SERVICE_ACCOUNT --role=roles/storage.objectUser
gcloud builds submit --config cloudbuild.yaml
```

Set `CHROME_EXTENSION_ID` on the service to the published extension's ID so only that extension can complete a sign-in.

## 📝 API Endpoints

### `POST /create_event`

Parse natural language into structured event data for confirmation.

### `POST /confirm_event`, `POST /confirm_bulk_events`

Create the confirmed event(s) in Google Calendar or Outlook.

### `GET /calendars`

Get the user's writable calendars.

### `POST /check_conflicts`

Check for scheduling conflicts.

### `GET /auth/google`, `GET /auth/microsoft`

Start a calendar sign-in from the extension. When it completes, the backend issues a session and hands it only to the extension's `chrome.identity` redirect URL. Calendar endpoints take that session as `user_id` and reject anything else.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔗 Links

- **Chrome Web Store:** [Install Prompt2Cal](https://chrome.google.com/webstore)
- **Homepage:** [https://moey145.github.io/Prompt2Cal/](https://moey145.github.io/Prompt2Cal/)
- **Privacy Policy:** [https://moey145.github.io/Prompt2Cal/privacy-policy.html](https://moey145.github.io/Prompt2Cal/privacy-policy.html)

## 🙏 Acknowledgments

- Anthropic for the Claude API (live parser)
- OpenAI for GPT API (research benchmark)
- Google for the Calendar API
- Microsoft for the Graph Calendar API
- FastAPI for the excellent Python web framework
- React for the frontend framework

---

**Made with ❤️ for easier calendar management**
