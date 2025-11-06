# Prompt2Cal Frontend (Vite + React)

This is the frontend application for Prompt2Cal, built with Vite and React.

## Features

- ⚡️ Lightning fast development with Vite
- ⚛️ React 18
- 🎨 Modern UI with responsive design
- 🎤 Voice input support
- 📅 Google Calendar integration
- 📋 Bulk event creation
- 📁 File import (CSV/TXT)

## Prerequisites

- Node.js 16+ installed
- Backend server running on http://localhost:8000

## Installation

```bash
npm install
```

## Development

Start the development server:

```bash
npm run dev
```

The app will be available at http://localhost:3000

## Build for Production

```bash
npm run build
```

The build output will be in the `dist/` folder.

## Preview Production Build

```bash
npm run preview
```

## Project Structure

```
frontend/
├── public/          # Static assets
├── src/
│   ├── App.js      # Main application component
│   ├── App.css     # Application styles
│   ├── main.jsx    # Application entry point
│   └── index.css   # Global styles
├── index.html      # HTML template
├── vite.config.js  # Vite configuration
└── package.json    # Dependencies and scripts
```

## API Proxy

The development server proxies API calls to the backend at http://localhost:8000. Make sure the backend is running before starting the frontend.

## Browser Support

- Chrome/Edge (latest 2 versions)
- Firefox (latest 2 versions)
- Safari (latest 2 versions)

