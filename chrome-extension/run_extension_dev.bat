@echo off
cd /d "%~dp0"
echo Starting React extension development mode...
echo.
echo This will watch for changes and rebuild automatically.
echo After changes, reload the extension in chrome://extensions/
echo.
npm run dev

