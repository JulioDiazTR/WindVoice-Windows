@echo off
echo Starting WindVoice-Windows...
echo.

REM Check if executable exists
if not exist "C:\Users\6113618\Github\WindVoice-Windows\dist\WindVoice-Windows.exe" (
    echo ERROR: WindVoice-Windows.exe not found!
    echo Please run build.py first to create the executable.
    pause
    exit /b 1
)

REM Start WindVoice
echo Launching WindVoice-Windows...
start "" "C:\Users\6113618\Github\WindVoice-Windows\dist\WindVoice-Windows.exe"

REM Optional: Keep window open for debugging
REM echo WindVoice started. Check system tray.
REM pause
