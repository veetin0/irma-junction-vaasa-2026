"""Vercel entrypoint. Loads the Irma FastAPI app from app/backend.

Local development does not use this file: run ./app/run.sh (or app\\run.bat on Windows).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "app" / "backend"))

from main import app  # noqa: E402,F401
