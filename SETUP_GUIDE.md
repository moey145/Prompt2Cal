# Prompt2Cal Setup Guide

This guide will help you set up and run your natural-language calendar agent.

## Prerequisites

- Python 3.8+
- Node.js 16+
- OpenAI API key
- Google Cloud Project with Calendar API enabled

## Step 1: Backend Setup

### 1.1 Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 1.2 Environment Configuration

Create a `.env` file in the root directory (copy from `env.example`):

```bash
cp env.example .env
```

Edit `.env` and add your OpenAI API key:

```env
OPENAI_API_KEY=your_actual_openai_api_key_here
```

### 1.3 Google Calendar API Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Calendar API:

   - Go to "APIs & Services" > "Library"
   - Search for "Google Calendar API"
   - Click "Enable"

4. Create OAuth 2.0 credentials:

   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Choose "Web application"
   - Add authorized redirect URIs:
     - `http://localhost:8000/auth/callback`
   - Download the credentials file

5. Save the downloaded file as `credentials.json` in the `backend/` directory

### 1.4 Run the Backend

```bash
cd backend
python main.py
```

The API will be available at `http://localhost:8000`

## Step 2: Frontend Setup

### 2.1 Install Node.js Dependencies

```bash
cd frontend
npm install
```

### 2.2 Start the Development Server

```bash
npm start
```

The frontend will be available at `http://localhost:3000`

## Step 3: Testing

### 3.1 Test the API

Run the test script to verify everything is working:

```bash
python test_api.py
```

### 3.2 Test the Full Flow

1. Open `http://localhost:3000` in your browser
2. Click "Connect to Google Calendar"
3. Complete the OAuth flow
4. Enter a natural language event description like:
   - "Lunch with Sarah next Tuesday at 1pm"
   - "Team meeting tomorrow at 10am in conference room A"
   - "Doctor appointment on Friday at 2:30pm"
5. Review the parsed details
6. Confirm to create the event

## Troubleshooting

### Common Issues

1. **OpenAI API Key Error**

   - Make sure your API key is valid and has sufficient credits
   - Check that the `.env` file is in the root directory

2. **Google Calendar Authentication Issues**

   - Ensure `credentials.json` is in the `backend/` directory
   - Verify the redirect URI matches: `http://localhost:8000/auth/callback`
   - Check that the Google Calendar API is enabled

3. **CORS Issues**

   - The frontend is configured to proxy requests to the backend
   - Make sure both servers are running on the correct ports

4. **Date Parsing Issues**
   - The system uses dateparser with fallbacks for edge cases
   - Try more specific time descriptions if parsing fails

### Debugging

Check the console output for detailed error messages:

- Backend logs will show API call details
- Frontend console will show network errors
- Use the test script to verify individual endpoints

## API Endpoints

- `GET /health` - Health check
- `GET /auth/status` - Check authentication status
- `GET /auth/google` - Get Google OAuth URL
- `GET /auth/callback` - Handle OAuth callback
- `POST /create_event` - Parse natural language to event data
- `POST /confirm_event` - Create event in Google Calendar

## Example Usage

```bash
# Parse an event
curl -X POST "http://localhost:8000/create_event" \
  -H "Content-Type: application/json" \
  -d '{"text": "Lunch with Sarah next Tuesday at 1pm"}'
```

## Next Steps

Once everything is working:

1. Customize the UI in `frontend/src/App.css`
2. Add more sophisticated parsing rules in `backend/services/event_parser.py`
3. Extend the calendar service for additional features
4. Add user management and event history
5. Deploy to a cloud platform

## Support

If you encounter issues:

1. Check the logs for error messages
2. Verify all environment variables are set
3. Ensure all dependencies are installed
4. Test individual endpoints using the test script
