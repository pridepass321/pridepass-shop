@echo off
cd /d "%~dp0"
echo.
echo  LGBTIQASB+ Community Access Cards
echo  =================================
echo.

where python >nul 2>&1
if %ERRORLEVEL%==0 (
    echo [1/3] Stopping any old server on port 8765...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8765 ^| findstr LISTENING') do taskkill /F /PID %%a >nul 2>&1
    echo [2/3] Building templates and syncing identities...
    python scripts\build.py
    echo.
    echo [3/3] Starting server...
    start http://localhost:8765
    python server.py
    goto :end
)

where node >nul 2>&1
if %ERRORLEVEL%==0 (
    echo Python not found — using Node.js server (no Python batch API).
    start http://localhost:8765
    node server.js
    goto :end
)

echo No Python or Node found. Open index.html directly.
start index.html

:end
pause