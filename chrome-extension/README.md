# Prompt2Cal Chrome Extension (React + Vite)

⚛️ **React-powered Chrome Extension** with voice input, AI parsing, and Google Calendar integration.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
npm install
```

### 2. Build the Extension

```bash
npm run build
```

### 3. Load in Chrome

1. Open Chrome → `chrome://extensions/`
2. Enable "Developer mode" (toggle top-right)
3. Click "Load unpacked"
4. Select the `dist/` folder
5. Done! 🎉

## 🎯 Features

✅ **Voice Input** - Speak your events naturally  
✅ **AI Parsing** - GPT-powered natural language understanding  
✅ **React + Vite** - Modern, fast, component-based  
✅ **Lucide React Icons** - Beautiful, consistent icons  
✅ **Google Calendar** - OAuth2 authentication & event creation  
✅ **Bulk Events** - Parse and create multiple events at once  
✅ **Color Picker** - Customize event colors  
✅ **Reminders** - Set reminder notifications

## 📁 Project Structure

```
chrome-extension/
├── src/
│   ├── Popup.jsx          # Main React component
│   ├── main.jsx           # React entry point
│   └── index.css          # Styles
├── dist/                  # Built extension (load this in Chrome!)
│   ├── manifest.json
│   ├── popup-react.html
│   ├── assets/
│   │   ├── popup.js       # Bundled React app
│   │   └── popup.css
│   └── [static files]
├── popup-react.html       # HTML template
├── background.js          # Service worker
├── content.js             # Content script
├── vite.config.js         # Vite configuration
├── package.json           # Dependencies
└── build.js               # Post-build script
```

## 🛠️ Development

### Build Commands

```bash
npm run build        # Production build
npm run dev          # Development watch mode
npm run copy-files   # Copy static files only
```

### Development Workflow

1. Edit `src/Popup.jsx` or other files
2. Run `npm run dev` for auto-rebuild
3. Reload extension in `chrome://extensions/`
4. Test changes

### Helper Scripts

- **Windows**: `run_extension_dev.bat`
- **Unix/Mac**: `run_extension_dev.sh`

## 🎨 Tech Stack

- **React 18** - UI library
- **Vite** - Build tool & bundler
- **Lucide React** - Icon library
- **Web Speech API** - Voice recognition
- **Chrome Extension APIs** - Browser integration
- **Google Calendar API** - Calendar integration

## 📦 Dependencies

```json
{
  "react": "^18.2.0",
  "react-dom": "^18.2.0",
  "lucide-react": "^0.292.0"
}
```

## 🔧 Backend Setup

The extension requires a backend server running on `http://localhost:8000`.

From the project root:

```bash
python run_backend.py
```

See the main project README for backend setup instructions.

## 🎨 Using Lucide React Icons

Import and use icons as React components:

```jsx
import { Calendar, Sparkles, Mic } from 'lucide-react';

<Calendar size={20} />
<Sparkles size={16} className="inline-icon" />
<Mic size={20} />
```

[Browse all icons →](https://lucide.dev/icons/)

## 📚 Documentation

- **[START-HERE.md](START-HERE.md)** - Getting started guide
- **[QUICK-START.md](QUICK-START.md)** - Quick start guide
- **[BUILD-INSTRUCTIONS.txt](BUILD-INSTRUCTIONS.txt)** - Build instructions
- **[EXTENSION-STRUCTURE.md](EXTENSION-STRUCTURE.md)** - File structure
- **[REACT-CONVERSION-SUMMARY.md](REACT-CONVERSION-SUMMARY.md)** - Technical details

## 🎯 How It Works

1. **User Input**: Type or speak event description
2. **AI Parsing**: Backend uses GPT to parse natural language
3. **Confirmation**: Review parsed event details
4. **Creation**: Event created in Google Calendar via OAuth2

### Example Flow

```
Input: "Lunch with Sarah next Tuesday at 1pm"
   ↓
Parse with GPT
   ↓
Extract:
  - Title: "Lunch with Sarah"
  - Date: Next Tuesday
  - Time: 1:00 PM - 2:00 PM
   ↓
Create in Google Calendar
```

## 🔑 Features in Detail

### Voice Recognition

- Click microphone icon to start
- Speak naturally
- Auto-stops after 2 seconds of silence
- Appends to existing text

### Single vs Multiple Events

- **Single**: Parse one event description
- **Multiple**: Extract multiple events from one text block

### Selected Text Detection

- Automatically detects text selected on webpage
- Option to use selected text as input

### Event Customization

- Custom colors
- Reminder notifications
- Location and notes support

## 🐛 Troubleshooting

**Extension not loading?**

- Make sure you ran `npm run build`
- Load the `dist/` folder (not the root)
- Check for build errors

**Build errors?**

- Delete `node_modules/` and run `npm install`
- Ensure Node.js 16+ is installed

**Backend errors?**

- Start backend: `python run_backend.py`
- Backend must run on `http://localhost:8000`
- Check backend logs for API errors

**Icons not showing?**

- Check browser console (F12) for errors
- Ensure lucide-react is installed
- Try rebuilding: `npm run build`

**Voice not working?**

- Allow microphone permissions in Chrome
- Check microphone settings in OS
- Only works on HTTPS or localhost

## 📊 Build Output

```
dist/
├── manifest.json          # Extension manifest
├── popup-react.html       # Popup HTML
├── assets/
│   ├── popup.js          # ~157 KB bundled React app
│   └── popup.css         # ~13 KB bundled styles
├── background.js         # Service worker
├── content.js            # Content script
├── content.css           # Content styles
└── icons/                # Extension icons
```

## 🚀 Deployment

For production use:

1. Build: `npm run build`
2. Test the `dist/` folder locally
3. Zip the `dist/` folder
4. Upload to Chrome Web Store

## 🤝 Contributing

The extension is part of the Prompt2Cal project. See the main repository README for contribution guidelines.

## 📝 License

See LICENSE file in project root.

## 🎉 You're Ready!

Your React Chrome extension is ready to go. Build it and start creating calendar events with voice and natural language! 🚀

**Next Steps:**

1. `npm install` - Install dependencies
2. `npm run build` - Build the extension
3. Load `dist/` in Chrome
4. Start backend: `python run_backend.py`
5. Create events! 🎉
