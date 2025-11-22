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

- Choose event colors
- Set reminder notifications
- Add locations and attendees
- Select which calendar to use
- Beautiful dark mode support

## 🎯 How It Works

1. **Type or speak** your event in natural language
2. **AI parses** your text into structured event data
3. **Review and confirm** the parsed details
4. **Event is created** in your Google Calendar instantly

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

- **Tech Stack:** FastAPI (Python), OpenAI GPT, Google Calendar API
- **Deployment:** Google Cloud Run
- **Features:** Natural language parsing, event creation, OAuth2 handling
- **Location:** `backend/`

### Key Services

- **Rules Parser:** Deterministic parsing for common patterns
- **Intelligent Parser:** AI-powered parsing for complex natural language
- **Calendar Service:** Google Calendar integration with conflict detection

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
└── README.md                  # This file
```

## 🔧 Development

### Prerequisites

- Python 3.8+
- Node.js 16+
- OpenAI API key
- Google Cloud Project with Calendar API enabled

### Backend Setup

1. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**

   ```bash
   cp env.example .env
   # Edit .env and add your OpenAI API key
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

## 📝 API Endpoints

### `POST /parse_event`

Parse natural language into structured event data.

### `POST /confirm_event`

Create the confirmed event in Google Calendar.

### `GET /calendars`

Get user's available Google Calendars.

### `GET /check_conflicts`

Check for scheduling conflicts.

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

- OpenAI for the GPT API
- Google for the Calendar API
- FastAPI for the excellent Python web framework
- React for the frontend framework

---

**Made with ❤️ for easier calendar management**
