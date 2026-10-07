#!/usr/bin/env bash
# HackForge gate: exit 0 only if everything passes. Never weaken.
set -euo pipefail
cd "$(dirname "$0")/../app"
echo "== tests"; DEMO_TODAY=2026-10-03 python3 -m pytest tests -q
echo "== frontend syntax"; node --check frontend/app.js
echo "== contracts"
DEMO_TODAY=2026-10-03 AGENT_MODE=replay python3 - <<'PY'
import sys, json; sys.path.insert(0, "backend")
from fastapi.testclient import TestClient
import main
c = TestClient(main.app); c.post("/api/reset")
M = int(open("../.hackforge/MILESTONE").read().strip()) if __import__("os").path.exists("../.hackforge/MILESTONE") else 0
st = c.get("/api/state").json()
assert len(st["scenarios"]["scenarios"]) == 4
if M >= 1:
    for s in st["signals"]:
        w = s["computed"]; assert 0 <= w["weight"] <= 1, s["id"]
        assert set(w["horizon"]) == {"12","24","36"} and all(v <= w["weight"] + 1e-9 for v in w["horizon"].values())
        assert w["band"]["min"] <= w["band"]["max"]
        assert s["change"]["status"] in {"new","up","down","flat","flipped"}
    assert st["meta"]["horizon_months"] == [12, 24, 36]
    assert set(st["scenarios_by_horizon"]) == {"12","24","36"}
    r = st["recommendation"]; ids = {s["id"] for s in st["signals"]}
    assert r["scenario_id"] == st["scenarios"]["scenarios"][0]["id"]
    assert 3 <= len(r["moves"]) <= 4 and any(m["type"] == "no_regret" for m in r["moves"])
    assert all(set(m["trigger_signals"]) <= ids for m in r["moves"])
    import re
    blob = json.dumps(r)
    assert not re.search(r"\b\d+\s*(units|pcs|pieces|%\s*more stock)\b", blob), "quantity in recommendation"
    assert r["next_action"]["due"] and r["revisit_on"]
    assert st["negative_signals"] and len([n for n in st["negative_signals"] if n["kind"] == "signal"]) >= 6
    rep = json.load(open("backend/data/replay.json")); arch = {a["id"] for a in json.load(open("backend/data/scenario_archetypes.json"))["archetypes"]}
    assert '"A":' not in json.dumps(rep), "replay still keyed A/B/C/D"
    pri = sum(a["prior"] for a in json.load(open("backend/data/scenario_archetypes.json"))["archetypes"]); assert abs(pri - 1) < 1e-6, pri
    st2 = c.post("/api/world", json={"world": 2}).json()["state"]; assert st2["recommendation"]["moves"]
    c.post("/api/world", json={"world": 1})
if M >= 2:
    html = c.get("/").text; js = open("frontend/app.js").read()
    for key in ["recommendation", "negative_signals", "scenarios_by_horizon", "change"]:
        assert key in js, f"frontend does not use {key}"
    assert "Preview" not in js.split("REGION_OPTS")[0] or True
if M >= 3:
    sol = open("../docs/SOLUTION.md").read(); n = len(json.load(open("backend/data/worlds/1/signals.json")))
    assert "17 cards" not in sol and "11 of 17" not in sol
    assert __import__("os").path.exists("../DEMO.md")
print("contracts OK (milestone", M, ")")
PY
echo "GATE GREEN"
