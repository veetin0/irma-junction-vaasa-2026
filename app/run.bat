@echo off
REM Start Irma on Windows. Optional: set ANTHROPIC_API_KEY for live agents, DEMO_TODAY=YYYY-MM-DD to freeze the clock, PORT to change the port.
cd /d "%~dp0backend"
if "%PORT%"=="" set PORT=8000
python -m uvicorn main:app --port %PORT%
