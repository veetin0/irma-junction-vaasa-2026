"""Vercel mode (C14): VERCEL=1, no API key, read-only code. Every route in main.py is called once, in a fresh process.

The table below must list every route the app defines, so a new endpoint cannot be added without being checked here.
Nothing may be written under backend/data (on Vercel only /tmp is writable): the data folder is hashed before and after.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

APP = Path(__file__).resolve().parents[1]

PROBE = r'''
import sys, json
sys.path.insert(0, {backend!r})
from fastapi.testclient import TestClient
import main
c = TestClient(main.app)
out = {{"mode": main.STORE.llm.mode, "background": main.BACKGROUND, "runtime": str(main.RUNTIME_DIR), "calls": {{}}, "routes": []}}
for r in main.app.routes:
    for m in getattr(r, "methods", None) or ():
        if r.path == "/" or r.path.startswith("/api"):
            out["routes"].append(m + " " + r.path)
def call(key, method, path, **kw):
    r = c.request(method, path, **kw)
    out["calls"][key] = r.status_code
    return r
st = call("GET /", "GET", "/").status_code
state = call("GET /api/state", "GET", "/api/state").json()
sid = state["signals"][0]["id"]
call("POST /api/world", "POST", "/api/world", json={{"world": 2}})
out["historical_world2_rows"] = len(call("GET /api/historical", "GET", "/api/historical").json()["rows"])
call("POST /api/world (back)", "POST", "/api/world", json={{"world": 1}})
out["historical_rows"] = len(c.get("/api/historical").json()["rows"])
for seg in ("oilgas", "all", "datacenter", "nope"):
    call("POST /api/segment " + seg, "POST", "/api/segment", json={{"segment": seg}})
call("GET /api/signals/{{signal_id}}", "GET", "/api/signals/" + sid)
call("POST /api/signals/{{signal_id}}/annotate", "POST", "/api/signals/" + sid + "/annotate", json={{"action": "comment", "note": "vercel check", "author": "test"}})
call("POST /api/signals/{{signal_id}}/lock", "POST", "/api/signals/" + sid + "/lock", json={{"locked": True}})
preset = next(k for k, v in main.STORE.replay.items() if isinstance(v, dict) and "item" in v)
run = call("POST /api/run", "POST", "/api/run", json={{"preset": preset}})
call("GET /api/runs/{{run_id}}", "GET", "/api/runs/" + run.json()["run"]["id"])
call("POST /api/cycle", "POST", "/api/cycle")
call("GET /api/scout", "GET", "/api/scout")
call("POST /api/scout/run", "POST", "/api/scout/run")
call("POST /api/scout/clear", "POST", "/api/scout/clear")
settings = call("GET /api/settings", "GET", "/api/settings").json()
call("PUT /api/settings", "PUT", "/api/settings", json=settings)
notes = call("GET /api/notifications", "GET", "/api/notifications").json()["notifications"]
call("POST /api/notifications/{{note_id}}/read", "POST", "/api/notifications/" + (notes[0]["id"] if notes else "N-0000") + "/read")
call("POST /api/notifications/read-all", "POST", "/api/notifications/read-all")
for lang in ("en", "fi"):
    a = call("POST /api/ask " + lang, "POST", "/api/ask", json={{"question": "Summarize the key changes in the selected segment", "lang": lang}})
    out["ask_" + lang] = a.json().get("mode")
call("GET /api/method", "GET", "/api/method")
call("POST /api/reset", "POST", "/api/reset")
print("PROBE " + json.dumps(out))
'''

# Expected status per call. Everything answers 200 except the one deliberately invalid segment.
OK = 200
EXPECTED = {
    "GET /": OK, "GET /api/state": OK, "POST /api/world": OK, "GET /api/historical": OK, "POST /api/world (back)": OK,
    "POST /api/segment oilgas": OK, "POST /api/segment all": OK, "POST /api/segment datacenter": OK, "POST /api/segment nope": 400,
    "GET /api/signals/{signal_id}": OK, "POST /api/signals/{signal_id}/annotate": OK, "POST /api/signals/{signal_id}/lock": OK,
    "POST /api/run": OK, "GET /api/runs/{run_id}": OK, "POST /api/cycle": OK,
    "GET /api/scout": OK, "POST /api/scout/run": OK, "POST /api/scout/clear": OK,
    "GET /api/settings": OK, "PUT /api/settings": OK,
    "GET /api/notifications": OK, "POST /api/notifications/{note_id}/read": OK, "POST /api/notifications/read-all": OK,
    "POST /api/ask en": OK, "POST /api/ask fi": OK, "GET /api/method": OK, "POST /api/reset": OK,
}
ROUTE_NAMES = {  # route as FastAPI lists it -> key in EXPECTED
    "GET /": "GET /", "GET /api/state": "GET /api/state", "POST /api/world": "POST /api/world", "GET /api/historical": "GET /api/historical",
    "POST /api/segment": "POST /api/segment oilgas", "GET /api/signals/{signal_id}": "GET /api/signals/{signal_id}",
    "POST /api/signals/{signal_id}/annotate": "POST /api/signals/{signal_id}/annotate", "POST /api/signals/{signal_id}/lock": "POST /api/signals/{signal_id}/lock",
    "POST /api/run": "POST /api/run", "GET /api/runs/{run_id}": "GET /api/runs/{run_id}", "POST /api/cycle": "POST /api/cycle",
    "GET /api/scout": "GET /api/scout", "POST /api/scout/run": "POST /api/scout/run", "POST /api/scout/clear": "POST /api/scout/clear",
    "GET /api/settings": "GET /api/settings", "PUT /api/settings": "PUT /api/settings", "GET /api/notifications": "GET /api/notifications",
    "POST /api/notifications/{note_id}/read": "POST /api/notifications/{note_id}/read", "POST /api/notifications/read-all": "POST /api/notifications/read-all",
    "POST /api/ask": "POST /api/ask en", "POST /api/reset": "POST /api/reset", "GET /api/method": "GET /api/method",
}


def _digest(folder: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(folder.rglob("*")):
        if p.is_file():
            h.update(str(p.relative_to(folder)).encode())
            h.update(p.read_bytes())
    return h.hexdigest()


def _run_vercel_probe(tmp_path: Path) -> dict:
    env = {**os.environ, "VERCEL": "1", "ANTHROPIC_API_KEY": "", "AGENT_MODE": "replay", "DEMO_TODAY": "2026-10-03",
           "IRMA_RUNTIME_DIR": str(tmp_path / "rt")}
    env.pop("IRMA_BACKGROUND", None)
    out = subprocess.run([sys.executable, "-c", PROBE.format(backend=str(APP / "backend"))], env=env, capture_output=True, text=True, timeout=300, cwd=APP)
    assert out.returncode == 0, out.stderr[-1500:]
    line = [x for x in out.stdout.splitlines() if x.startswith("PROBE ")][-1]
    return json.loads(line[len("PROBE "):])


def test_every_endpoint_answers_in_vercel_mode_without_a_key(tmp_path):
    before = _digest(APP / "backend" / "data")
    result = _run_vercel_probe(tmp_path)
    assert result["mode"] == "replay" and result["background"] is False        # no key: replay; no background scheduler on Vercel
    # Every route the app defines has an entry in the table.
    defined = {x for x in result["routes"] if not x.startswith("HEAD") and not x.startswith("OPTIONS")}
    assert defined <= set(ROUTE_NAMES), sorted(defined - set(ROUTE_NAMES))
    assert set(ROUTE_NAMES.values()) <= set(EXPECTED)
    assert result["calls"] == EXPECTED, {k: (v, EXPECTED.get(k)) for k, v in result["calls"].items() if EXPECTED.get(k) != v}
    # The two newest endpoints return real content, not just a status.
    assert result["historical_rows"] == 5 and result["historical_world2_rows"] == 5
    assert result["ask_en"] == "composed" and result["ask_fi"] == "composed"
    # Writes went to the runtime folder, never to the read-only code.
    assert _digest(APP / "backend" / "data") == before
    assert (tmp_path / "rt").exists()
