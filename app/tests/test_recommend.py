"""Recommended move, next action, signal changes, negative list and per-scenario explanations (contracts C3 to C6).

Run from app/:  DEMO_TODAY=2026-10-03 python -m pytest tests -q
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import date, timedelta
from pathlib import Path

os.environ.setdefault("DEMO_TODAY", "2026-10-03")
os.environ["AGENT_MODE"] = "replay"
BACKEND = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND))

from fastapi.testclient import TestClient  # noqa: E402

import main  # noqa: E402
from agents.llm import recommendation_filter  # noqa: E402
from engine.changes import FLAT_EPS, compute_changes, signal_changes  # noqa: E402
from engine.recommend import build_recommendation, confidence, load_templates, template_texts  # noqa: E402

client = TestClient(main.app)
TEMPLATES = load_templates(BACKEND / "data" / "recommendations.json")
ARCHETYPES = json.loads((BACKEND / "data" / "scenario_archetypes.json").read_text(encoding="utf-8"))["archetypes"]
AREAS = {"procurement", "manufacturing", "capacity", "supply_reliability"}
# A digit followed by a unit, a share or a quantity word. Move texts must contain none.
QUANTITY = re.compile(r"\d+([.,]\d+)?\s*(%|per cent|percent|units?|pcs|pieces|relays?|boards?|weeks?|months?|days?|years?|tonnes?|gw|mw|twh|eur|usd|k\b|m\b|bn\b)", re.IGNORECASE)
ORDER_WORDS = re.compile(r"\b(reorder point|order point|safety stock of|order quantity|re-order|reorder)\b", re.IGNORECASE)


def setup_function():
    client.post("/api/reset")


def _both_worlds():
    for world in (1, 2):
        yield world, client.post("/api/world", json={"world": world}).json()["state"]
    client.post("/api/world", json={"world": 1})


def _move_text(r: dict) -> list[str]:
    """The free text of the moves, the next action and the disclaimer, apart from the trigger's bracketed signal ids."""
    out = []
    for m in r["moves"]:
        for key in ("text", "trigger", "cost_if_wrong"):
            out += [re.sub(r"\[SIG-[0-9, SIG-]*\]", "", v) for v in m[key].values()]
    out += list(r["next_action"]["text"].values()) + list(r["next_action"]["owner"].values()) + list(r["disclaimer"].values())
    return out


def _framing_text(r: dict) -> list[str]:
    """Headline and hedge with the quoted scenario names and their probabilities masked.

    Both quote an archetype name verbatim and a scenario probability (a share between scenarios, not a quantity of
    anything to buy). The archetype named "Duplicate orders unwind" trips the guardrail's "double ... orders" pattern
    by name alone, so the names are data, not wording, and are masked here.
    """
    names = [r["scenario_name"], r["runner_up"]["name"]]
    out = []
    for t in list(r["headline"].values()) + list(r["hedge"].values()):
        for n in names:
            for v in n.values():
                t = t.replace(v, "NAME")
        out.append(re.sub(r"\d+\s?%", "P", t))
    return out


# ---------------------------------------------------------------- C3: templates ---------
def test_templates_cover_all_nine_archetypes_with_three_or_four_moves():
    ids = {a["id"] for a in ARCHETYPES}
    assert len(ids) == 9 and set(TEMPLATES["archetypes"]) == ids
    for sid, t in TEMPLATES["archetypes"].items():
        moves = t["moves"]
        assert 3 <= len(moves) <= 4, sid
        assert any(m["type"] == "no_regret" for m in moves), sid
        assert all(m["area"] in AREAS and m["type"] in ("no_regret", "contingent") and m["horizon_months"] in (12, 24, 36) for m in moves), sid
        assert all(k in TEMPLATES["themes"] for m in moves for k in m["themes"]), sid
        for key in ("headline_move", "if_leading"):
            assert t[key]["en"] and t[key]["fi"], (sid, key)
        for m in moves:
            for key in ("text", "trigger", "cost_if_wrong"):
                assert m[key]["en"].strip() and m[key]["fi"].strip(), (sid, key)
                assert m[key]["en"] != m[key]["fi"], (sid, key)
        assert t["next_action"]["text"]["fi"] and t["next_action"]["owner"]["fi"] and t["next_action"]["due_days"] > 0


def test_thresholds_and_day_counts_are_labelled_assumption():
    assert TEMPLATES["confidence_rules"]["label"] == "ASSUMPTION" and "ASSUMPTION" in TEMPLATES["confidence_rules"]["note"]
    assert TEMPLATES["defaults"]["label"] == "ASSUMPTION" and "ASSUMPTION" in TEMPLATES["defaults"]["note"]


def test_confidence_rule():
    rules = TEMPLATES["confidence_rules"]
    assert confidence(0.30, 0.50, rules) == "high"
    assert confidence(0.30, 0.95, rules) == "low"       # a wide margin does not help when the spread is wide
    assert confidence(0.12, 0.76, rules) == "medium"
    assert confidence(0.01, 0.93, rules) == "low"
    assert confidence(0.12, 0.76, rules) != confidence(0.01, 0.76, rules)


def test_both_worlds_give_a_grounded_recommendation():
    today = date.fromisoformat(os.environ["DEMO_TODAY"])
    heads = {}
    for world, st in _both_worlds():
        r = st["recommendation"]
        ids = {s["id"] for s in st["signals"]}
        lead, runner = sorted(st["scenarios"]["scenarios"], key=lambda s: -s["probability"])[:2]
        assert r["scenario_id"] == lead["id"] and r["runner_up"]["id"] == runner["id"]
        assert r["scenario_name"]["en"] and r["scenario_name"]["fi"] and r["runner_up"]["name"]["fi"]
        assert 3 <= len(r["moves"]) <= 4 and any(m["type"] == "no_regret" for m in r["moves"]), world
        assert r["confidence"] in ("low", "medium", "high") and r["label"] == "ASSUMPTION" and r["generated_by"] == "code"
        for m in r["moves"]:
            assert m["area"] in AREAS and m["horizon_months"] in (12, 24, 36) and m["label"] == "ASSUMPTION"
            assert m["trigger_signals"] and set(m["trigger_signals"]) <= ids, (world, m["trigger_signals"])
            assert all(sid in m["trigger"]["en"] and sid in m["trigger"]["fi"] for sid in m["trigger_signals"][:1])
            assert m["text"]["en"] and m["text"]["fi"] and m["cost_if_wrong"]["en"] and m["cost_if_wrong"]["fi"]
        assert runner["name"]["en"] in r["hedge"]["en"] and r["hedge"]["fi"]
        na = r["next_action"]
        assert na["due"] > today.isoformat() and na["owner"]["en"] and na["text"]["fi"]
        assert date.fromisoformat(na["due"]) - today == timedelta(days=TEMPLATES["archetypes"][lead["id"]]["next_action"]["due_days"])
        assert r["revisit_on"] == (today + timedelta(days=TEMPLATES["defaults"]["revisit_days"])).isoformat()
        assert "planner decides" in r["disclaimer"]["en"].lower() and "päätöksen tekee" in r["disclaimer"]["fi"].lower()
        assert r["headline"]["en"].startswith("Recommended move") and r["headline"]["fi"].startswith("Suositeltu siirto")
        heads[world] = r["headline"]
    assert heads[1] != heads[2]


def test_every_archetype_builds_a_recommendation_with_real_trigger_ids():
    """Run each archetype as the leader in each world, so templates for archetypes not leading today are exercised too."""
    for world, st in _both_worlds():
        ids = {s["id"] for s in st["signals"]}
        weights = {s["id"]: s["computed"] for s in st["signals"]}
        signals = [{k: v for k, v in s.items() if k not in ("computed", "change")} for s in st["signals"]]
        for a in ARCHETYPES:
            others = [x for x in ARCHETYPES if x["id"] != a["id"]]
            fake = {"scenarios": [{"id": a["id"], "name": a["name"], "probability": 0.4},
                                  {"id": others[0]["id"], "name": others[0]["name"], "probability": 0.3},
                                  {"id": others[1]["id"], "name": others[1]["name"], "probability": 0.2},
                                  {"id": others[2]["id"], "name": others[2]["name"], "probability": 0.1}], "entropy": 0.8}
            r = build_recommendation(fake, signals, weights, date(2026, 10, 3), TEMPLATES)
            assert r and r["scenario_id"] == a["id"], (world, a["id"])
            assert 3 <= len(r["moves"]) <= 4 and any(m["type"] == "no_regret" for m in r["moves"])
            assert all(m["trigger_signals"] and set(m["trigger_signals"]) <= ids for m in r["moves"]), (world, a["id"])


def test_unknown_leading_archetype_gives_no_recommendation_instead_of_failing():
    fake = {"scenarios": [{"id": "not_a_scenario", "name": {"en": "x", "fi": "x"}, "probability": 1.0}], "entropy": 0.0}
    assert build_recommendation(fake, [], {}, date(2026, 10, 3), TEMPLATES) is None


# ---------------------------------------------------------------- guardrail --------------
def test_every_template_text_passes_the_guardrail_unchanged():
    texts = template_texts(TEMPLATES)
    assert len(texts) > 150
    for t in texts:
        clean, removed = recommendation_filter(t)
        assert removed == [] and clean == t.strip(), t


def test_built_recommendations_pass_the_guardrail_in_both_worlds():
    for world, st in _both_worlds():
        r = st["recommendation"]
        for t in _move_text(r) + _framing_text(r):
            clean, removed = recommendation_filter(t)
            assert removed == [] and clean == t.strip(), (world, t)


def test_guardrail_still_strips_quantities_and_order_language():
    for bad in ["ABB should order 5000 relays now.", "We recommend placing an order for memory.", "Increase the order volume for DRAM.",
                "The reorder point of the relay boards is reached.", "You should buy more memory."]:
        clean, removed = recommendation_filter(bad)
        assert removed and clean == "", bad


def test_no_quantities_order_points_or_dates_in_move_texts():
    for _, st in _both_worlds():
        for t in _move_text(st["recommendation"]) + _framing_text(st["recommendation"]):
            assert not QUANTITY.search(t), t
            assert not ORDER_WORDS.search(t), t
            assert not re.search(r"\d{4}-\d{2}-\d{2}", t), t
            assert not re.search(r"\d", t), t   # stricter: the moves carry no digits at all
    for t in template_texts(TEMPLATES):
        stripped = re.sub(r"\{[a-z_]+\}", "", t)
        assert not QUANTITY.search(stripped) and not ORDER_WORDS.search(stripped), t


def test_agent_descriptions_say_what_is_true_now():
    st = client.get("/api/state").json()
    names = [a["name"] for a in st["meta"]["agents"]]
    reco = next(a for a in st["meta"]["agents"] if a["name"].startswith("Recommendation agent"))
    assert "code" in reco["responsibility"] and "planner decides" in reco["responsibility"].lower() and "no quantities" in reco["responsibility"].lower()
    assert len(names) == len(set(names)) == 9
    principle = client.get("/api/method").json()["principle"]
    assert "No agent produces a purchase recommendation" not in principle
    assert "recommended move" in principle and "planner decides" in principle and "no quantities or order timing" in principle


# ---------------------------------------------------------------- C4: signal changes -----
def test_change_baseline_marks_recent_signals_new():
    st = client.get("/api/state").json()
    today = date.fromisoformat(st["meta"]["today"])
    cutoff = (today - timedelta(days=7)).isoformat()
    for s in st["signals"]:
        ch = s["change"]
        assert ch["status"] in ("new", "up", "down", "flat", "flipped") and set(ch) == {"status", "weight_prev", "delta", "since"}
        if s["observed_at"] and s["observed_at"] > cutoff:
            assert ch["status"] == "new" and ch["weight_prev"] is None and ch["delta"] is None, s["id"]
            assert ch["since"] == s["observed_at"]
        else:
            assert ch["status"] != "new" and ch["weight_prev"] is not None and ch["delta"] is not None, s["id"]
            assert ch["since"] == cutoff
            assert (ch["status"] == "flat") == (abs(ch["delta"]) < FLAT_EPS)
            assert ch["status"] == ("flat" if abs(ch["delta"]) < FLAT_EPS else "up" if ch["delta"] > 0 else "down")
    new_ids = {s["id"] for s in st["signals"] if s["change"]["status"] == "new"}
    assert {"SIG-007", "SIG-010", "SIG-018"} <= new_ids          # observed 30 Sep, 2 Oct and 1 Oct 2026
    assert "SIG-001" not in new_ids


def test_signal_changes_list_is_sorted_and_skips_flat():
    st = client.get("/api/state").json()
    rows = st["signal_changes"]
    assert rows and all(set(r) == {"signal_id", "status", "delta"} and r["status"] != "flat" for r in rows)
    ids = [r["signal_id"] for r in rows]
    assert len(ids) == len(set(ids))
    obs = {s["id"]: s["observed_at"] for s in st["signals"]}
    new = [r for r in rows if r["status"] == "new"]
    rest = [r for r in rows if r["status"] != "new"]
    assert rows[: len(new)] == new                                   # new cards first
    assert [obs[r["signal_id"]] for r in new] == sorted((obs[r["signal_id"]] for r in new), reverse=True)   # newest first
    mags = [abs(r["delta"]) for r in rest]
    assert mags == sorted(mags, reverse=True)


def test_change_statuses_up_down_flat_flipped_new_from_a_stored_baseline():
    today = date(2026, 10, 3)
    sigs = [{"id": f"S{i}", "direction": 1, "observed_at": "2026-09-01"} for i in range(6)]
    weights = {"S0": {"weight": 0.50}, "S1": {"weight": 0.30}, "S2": {"weight": 0.2005}, "S3": {"weight": 0.40}, "S4": {"weight": 0.10}, "S5": {"weight": 0.2}}
    sigs[3]["direction"] = -1
    sigs.append({"id": "S6", "direction": 1, "observed_at": "2026-10-02"})
    weights["S6"] = {"weight": 0.2}
    base = {"date": "2026-09-30", "weights": {"S0": 0.40, "S1": 0.40, "S2": 0.20, "S3": 0.40, "S4": 0.10, "S5": 0.2}, "direction": {f"S{i}": 1 for i in range(6)}}
    ch = compute_changes(sigs, weights, base, today)
    assert ch["S0"]["status"] == "up" and ch["S0"]["delta"] == 0.1 and ch["S0"]["since"] == "2026-09-30"
    assert ch["S1"]["status"] == "down" and ch["S2"]["status"] == "flat" and ch["S4"]["status"] == "flat"
    assert ch["S3"]["status"] == "flipped" and ch["S6"] == {"status": "new", "weight_prev": None, "delta": None, "since": "2026-10-02"}
    rows = signal_changes(sigs, ch)
    assert [r["signal_id"] for r in rows] == ["S6", "S0", "S1", "S3"]      # new first, then by |delta|; flat S2 and S4 left out


def test_new_information_moves_the_baseline_and_shows_the_change():
    r = client.post("/api/run", json={"preset": "demo_fingrid_q3"}).json()
    ch = next(s for s in r["state"]["signals"] if s["id"] == "SIG-001")["change"]
    assert ch["status"] == "up" and ch["delta"] > FLAT_EPS and ch["weight_prev"] < next(s for s in r["state"]["signals"] if s["id"] == "SIG-001")["computed"]["weight"]
    assert any(x["signal_id"] == "SIG-001" and x["status"] == "up" for x in r["state"]["signal_changes"])
    # An hourly cycle on the same day must not erase the change.
    again = client.post("/api/cycle").json()["state"]
    assert next(s for s in again["signals"] if s["id"] == "SIG-001")["change"]["status"] == "up"


# ---------------------------------------------------------------- C5: negative list ------
def test_negative_signals_list():
    for world, st in _both_worlds():
        rows = st["negative_signals"]
        by_id = {s["id"]: s for s in st["signals"]}
        ce_ids = {c["id"]: c for c in st["evidence"]}
        sig_rows = [r for r in rows if r["kind"] == "signal"]
        assert {r["id"] for r in sig_rows} == {s["id"] for s in st["signals"] if s["direction"] < 0}, world
        keys = {"kind", "id", "name", "short", "region", "weight", "strength", "reliability", "source", "against", "data_label"}
        for r in rows:
            assert keys <= set(r) and set(r["source"]) == {"name", "date", "url"} and r["reliability"] in ("A", "B", "C")
            assert r["against"] and all(a in by_id for a in r["against"]), (world, r["id"])
            if r["kind"] == "signal":
                assert r["weight"] == by_id[r["id"]]["computed"]["weight"] and by_id[r["id"]]["direction"] < 0
                assert all(by_id[a]["direction"] > 0 for a in r["against"])
            else:
                assert r["weight"] is None and r["id"] in ce_ids and 0 <= r["strength"] <= 1
                assert by_id[r["against"][0]]["direction"] >= 0           # counter-evidence to growth cards only
        weights = [r["weight"] for r in sig_rows]
        assert weights == sorted(weights, reverse=True)
        kinds = [r["kind"] for r in rows]
        assert kinds == sorted(kinds, key=lambda k: k != "signal")        # cards first, then counter-evidence
        scores = [r["score"] for r in rows if r["kind"] == "counter_evidence"]
        assert scores == sorted(scores, reverse=True)


def test_negative_list_world_one_holds_the_known_reversal_cards():
    ids = {r["id"] for r in client.get("/api/state").json()["negative_signals"] if r["kind"] == "signal"}
    assert {"SIG-005", "SIG-014", "SIG-015"} <= ids


# ---------------------------------------------------------------- C6: import result -------
def test_run_result_delta_rows_use_current_archetype_ids_and_explain_themselves():
    r = client.post("/api/run", json={"preset": "demo_fingrid_q3"}).json()
    arch = {a["id"]: a for a in ARCHETYPES}
    rows = r["run"]["scenario_deltas"]
    assert rows == next(t["output"]["deltas"] for t in r["run"]["trace"] if t["agent"] == "Scenario agent")
    assert len(rows) == 4 and {x["id"] for x in rows} == {s["id"] for s in r["state"]["scenarios"]["scenarios"]}
    for row in rows:
        assert row["id"] in arch and row["id"] not in ("A", "B", "C", "D")
        assert row["name"] == arch[row["id"]]["name"]["en"] and row["name_fi"] == arch[row["id"]]["name"]["fi"]
        ps = row["per_scenario"]
        assert ps["en"].strip() and ps["fi"].strip() and ps["en"] != ps["fi"]
        assert "[SIG-" in ps["en"] and "[SIG-" in ps["fi"]
        for sid in re.findall(r"SIG-\d+", ps["en"]):
            assert sid in {s["id"] for s in r["state"]["signals"]}
    # The explanation names the signal that was imported, and says whether it supports or counts against the scenario.
    assert all("[SIG-001]" in row["per_scenario"]["en"] for row in rows)
    assert any("supports this scenario" in row["per_scenario"]["en"] for row in rows)
    assert any("counts against this scenario" in row["per_scenario"]["en"] for row in rows)
    for row in rows:
        clean, removed = recommendation_filter(row["per_scenario"]["en"])
        assert removed == []


def test_run_state_still_carries_the_recommendation():
    r = client.post("/api/run", json={"preset": "demo_fingrid_q3"}).json()
    assert r["state"]["recommendation"]["moves"] and r["state"]["negative_signals"] and "signal_changes" in r["state"]


def test_import_run_returns_recommended_move_and_next_action():
    from fastapi.testclient import TestClient
    import main
    c = TestClient(main.app)
    c.post("/api/reset")
    r = c.post("/api/run", json={"preset": "demo_fingrid_q3"}).json()
    rec = r.get("recommendation") or r.get("run", {}).get("recommendation")
    assert rec and rec["moves"] and rec["next_action"]["due"]
    assert c.get("/api/method").json()["weight_formula"].startswith("w = min(1,")
