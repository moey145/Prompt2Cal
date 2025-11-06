# Prompt2Cal 📅

Convert natural language descriptions into Google Calendar events with AI-powered parsing and confirmation.

## 🎤 **NEW: Voice-Enabled Chrome Extension!**

This project now includes a **React-powered Chrome Extension with voice recognition**! Create calendar events by speaking naturally.

### Built with Modern Tech:

- ⚛️ **React + Vite** - Fast, modern component architecture
- 🎨 **Lucide React Icons** - Beautiful, consistent icons
- 🎤 **Voice Input** - Web Speech API integration
- 📅 **Google Calendar** - OAuth2 & event creation

👉 **[Get Started](chrome-extension/START-HERE.md)** | **[Quick Start](chrome-extension/QUICK-START.md)** | **[Voice Guide](VOICE_EXTENSION_GUIDE.md)**

## Features

- 🎤 **Voice Recognition**: Speak your events naturally (Chrome Extension)
- 🤖 **AI-Powered Parsing**: Uses OpenAI GPT to understand natural language
- 📅 **Google Calendar Integration**: Seamlessly creates events in your calendar
- ✅ **Confirmation System**: Review and confirm parsed event details before creation
- 🎨 **Modern UI**: Beautiful Chrome extension with responsive design
- 🔐 **OAuth2 Authentication**: Secure Google Calendar access
- 🌐 **Multi-User Support**: Each user gets their own authenticated session

## Example Usage

Input: `"Lunch with Sarah next Tuesday at 1pm"`

Output: Creates a calendar event with:

- Title: "Lunch with Sarah"
- Start: Next Tuesday at 1:00 PM
- End: Next Tuesday at 2:00 PM (1 hour duration)
- Location: (if specified)

## Quick Start

### Prerequisites

- Python 3.8+
- Node.js 16+
- OpenAI API key
- Google Cloud Project with Calendar API enabled

### Backend Setup

1. **Install Python dependencies:**

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

4. **Run the backend:**
   ```bash
   cd backend
   python main.py
   ```

The API will be available at `http://localhost:8000`

### Frontend Setup (Vite + React)

1. **Install Node.js dependencies:**

   ```bash
   cd frontend
   npm install
   ```

2. **Start the development server:**
   ```bash
   npm run dev
   ```

The frontend will be available at `http://localhost:3000`

Or use the convenience scripts:
- Windows: Double-click `frontend/run_frontend_vite.bat`
- Linux/Mac: Run `./frontend/run_frontend_vite.sh`

## API Endpoints

### `POST /create_event`

Parse natural language into structured event data.

**Request:**

```json
{
  "text": "Lunch with Sarah next Tuesday at 1pm"
}
```

**Response:**

```json
{
  "success": true,
  "parsed_event": {
    "title": "Lunch with Sarah",
    "start_time": "2024-01-16T13:00:00",
    "end_time": "2024-01-16T14:00:00",
    "location": null,
    "notes": null,
    "duration_minutes": 60
  },
  "message": "Event parsed successfully. Please confirm details.",
  "requires_confirmation": true
}
```

### `POST /confirm_event`

Create the confirmed event in Google Calendar.

**Request:**

```json
{
  "title": "Lunch with Sarah",
  "start_time": "2024-01-16T13:00:00",
  "end_time": "2024-01-16T14:00:00",
  "location": null,
  "notes": null,
  "duration_minutes": 60
}
```

**Response:**

```json
{
  "success": true,
  "message": "Event created successfully!",
  "event_link": "https://calendar.google.com/calendar/event?eid=...",
  "requires_confirmation": false
}
```

### `GET /auth/google`

Get Google OAuth2 authorization URL.

### `GET /auth/callback`

Handle Google OAuth2 callback.

## Project Structure

```
Prompt2Cal/
├── backend/
│   ├── main.py                 # FastAPI application
│   ├── models/
│   │   ├── __init__.py
│   │   └── event_models.py     # Pydantic models
│   └── services/
│       ├── __init__.py
│       ├── event_parser.py     # LLM parsing service
│       └── calendar_service.py # Google Calendar integration
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── App.js             # Main React component
│   │   ├── App.css            # Styling
│   │   ├── index.js           # React entry point
│   │   └── index.css          # Global styles
│   └── package.json
├── requirements.txt           # Python dependencies
├── env.example               # Environment variables template
└── README.md
```

## Configuration

### Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key for natural language processing
- `GOOGLE_APPLICATION_CREDENTIALS`: Path to Google credentials file
- `PORT`: Server port (default: 8000)

### Google Calendar Setup

1. Create a Google Cloud Project
2. Enable the Google Calendar API
3. Create OAuth 2.0 credentials
4. Set authorized redirect URIs:
   - `http://localhost:8000/auth/callback`
5. Download credentials and save as `backend/credentials.json`

## Development

### Running in Development Mode

**Backend:**

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**

```bash
cd frontend
npm start
```

### Testing

Test the API endpoints using curl or a tool like Postman:

```bash
# Parse an event
curl -X POST "http://localhost:8000/create_event" \
  -H "Content-Type: application/json" \
  -d '{"text": "Lunch with Sarah next Tuesday at 1pm"}'
```

## Troubleshooting

### Common Issues

1. **OpenAI API Key Error**: Make sure your API key is valid and has sufficient credits
2. **Google Calendar Authentication**: Ensure credentials.json is in the correct location
3. **CORS Issues**: The frontend is configured to proxy requests to the backend
4. **Date Parsing Issues**: The system uses dateparser with fallbacks for edge cases

### Logs

Check the console output for detailed error messages and debugging information.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenAI for the GPT API
- Google for the Calendar API
- FastAPI for the excellent Python web framework
- React for the frontend framework
