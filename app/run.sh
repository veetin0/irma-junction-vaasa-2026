#!/usr/bin/env bash
# Start Irma. Optional: export ANTHROPIC_API_KEY for live agents; DEMO_TODAY=YYYY-MM-DD to freeze the clock; PORT to change the port (default 8000).
cd "$(dirname "$0")/backend" && python3 -m uvicorn main:app --reload --port "${PORT:-8000}"
