@echo off
echo Starting TestGen AI Frontend...
echo.
cd /d "%~dp0frontend"
echo Installing dependencies...
npm install -q
echo.
echo Starting Vite dev server on http://localhost:5173
npm run dev
