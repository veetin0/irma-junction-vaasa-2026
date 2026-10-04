"""API-level tests for Irma. Run from app/: python -m pytest tests -q"""
from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("DEMO_TODAY", "2026-10-03")
os.environ["AGENT_MODE"] = "replay"
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from fastapi.testclient import TestClient  # noqa: E402

import main  # noqa: E402

client = TestClient(main.app)


def setup_function():
    client.post("/api/reset")


def test_state_shape_and_daily_history():
    st = client.get("/api/state").json()
    assert st["meta"]["app"] == "Irma" and st["meta"]["world"] == 1
    pts = st["history"]["points"]
    assert len(pts) >= 30 and pts[-1]["live"] is True and pts[-1]["date"] == "2026-10-03"
    assert all(abs(sum(p["probs"].values()) - 1) < 1e-3 for p in pts)
    assert len(st["scenarios"]["scenarios"]) == 4 and st["summary"]["en"] and st["summary"]["fi"]
    assert all(s["strength_class"] in ("strong", "weak", "inactive") for s in st["signals"])


def test_world_switch_changes_leading_scenario_and_summary():
    st1 = client.get("/api/state").json()
    st2 = client.post("/api/world", json={"world": 2}).json()["state"]
    assert st2["meta"]["world"] == 2
    assert st1["scenarios"]["scenarios"][0]["id"] != st2["scenarios"]["scenarios"][0]["id"]
    assert st1["summary"]["en"] != st2["summary"]["en"]
    client.post("/api/world", json={"world": 1})


def test_major_signals_notified_at_startup_bilingual():
    st = client.get("/api/state").json()
    majors = [n for n in st["notifications"] if n["kind"] == "major_signal"]
    assert majors and majors[0]["title_fi"].startswith("Merkittävä signaali")


def test_lock_halves_threshold_and_tracks():
    client.put("/api/settings", json={"notifications": {"price_change_pct": 5.0}})
    r = client.post("/api/signals/SIG-010/lock", json={"locked": True}).json()
    assert r["locked"] is True and r["tracking"]["checks"] >= 1
    after = client.get("/api/notifications").json()["notifications"]
    assert any(n["kind"] == "price_move" and n["signal_id"] == "SIG-010" for n in after)


def test_settings_persist_and_schedule():
    assert client.put("/api/settings", json={"run_interval_minutes": 30}).json()["run_interval_minutes"] == 30
    assert client.get("/api/state").json()["scheduler"]["interval_minutes"] == 30
    client.put("/api/settings", json={"run_interval_minutes": 60})


def test_run_updates_card_and_keeps_four_scenarios():
    r = client.post("/api/run", json={"preset": "demo_fingrid_q3"}).json()
    assert r["run"]["new_signal_id"] == "SIG-001" and r["state"]["notifications"][0]["kind"] == "new_information"
    assert len(r["run"]["scenarios_after"]["scenarios"]) == 4
    sig = client.get("/api/signals/SIG-001").json()
    assert sig["value"]["number"] == 3.6 and set(sig["scenario_names"]) == {s["id"] for s in r["state"]["scenarios"]["scenarios"]}


def test_ask_suggested_prompts_both_languages():
    for q in main.SUGGESTED_PROMPTS["en"]:
        a = client.post("/api/ask", json={"question": q, "lang": "en"}).json()
        assert a["mode"] == "composed" and a["citations"] and a["guardrail_removed"] == 0
    a = client.post("/api/ask", json={"question": main.SUGGESTED_PROMPTS["fi"][1], "lang": "fi"}).json()
    assert a["intent"] == "procurement" and "Irma ei suosittele" in a["answer"]


def test_live_answer_gets_the_full_catalogue_and_links_cited_cards():
    from types import SimpleNamespace
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import test_web as tw
    answer = SimpleNamespace(stop_reason="end_turn", model="claude-opus-5-5", usage=tw.usage(),
                             content=[SimpleNamespace(type="text", text="Copper is near its record at USD 14,319/t [SIG-010]. The decision is the planner's.\n- Memory stays tight SIG-018.")])

    class Capture:
        calls = []

        def create(self, **kw):
            self.calls.append(kw)
            return answer

    original = main.STORE.llm
    cap = Capture()
    main.STORE.llm = tw.live_client(cap)
    try:
        a = client.post("/api/ask", json={"question": "Should we buy copper busbars now?", "lang": "en"}).json()
    finally:
        main.STORE.llm = original
    prompt = cap.calls[0]["messages"][0]["content"]
    assert "SIGNAL CATALOGUE" in prompt and "[SIG-010] LME copper price" in prompt
    assert "plain text only" in cap.calls[0]["system"]
    assert a["mode"] == "live" and [c["signal_id"] for c in a["citations"]] == ["SIG-010", "SIG-018"]
    assert a["guardrail_removed"] == 0 and "removed by guardrail" not in a["answer"]
