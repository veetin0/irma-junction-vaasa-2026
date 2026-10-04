"""Deterministic engine tests. Run from app/:  python -m pytest tests -q"""
from __future__ import annotations

import json
import os
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from engine.archetypes import plain_summary, relevance, select_scenarios  # noqa: E402
from engine.bullwhip import amplification_ratio, compute_bullwhip, momentum, spot_contract_spread  # noqa: E402
from engine.weights import compute_weights, freshness, signal_weight  # noqa: E402
from agents.llm import recommendation_filter  # noqa: E402

DATA = Path(__file__).resolve().parents[1] / "backend" / "data"
TODAY = date(2026, 10, 3)


def load(path):
    return json.loads((DATA / path).read_text(encoding="utf-8"))


def test_freshness_half_life():
    assert freshness("2026-10-03", TODAY, "quarterly") == 1.0
    assert abs(freshness("2026-06-05", TODAY, "quarterly") - 0.5) < 0.01
    assert freshness("", TODAY, "quarterly") == 0.0


def test_weight_components_and_caps():
    evidence = {"CE-X": {"id": "CE-X", "reliability": "A", "strength": 0.5}}
    sig = {"id": "S", "reliability": "A", "update_frequency": "quarterly", "observed_at": "2026-10-03",
           "strength": 1.0, "counter_evidence": ["CE-X"], "ce_searched": True, "annotations": []}
    assert signal_weight(sig, evidence, TODAY)["weight"] == 0.5
    assert signal_weight({**sig, "counter_evidence": [], "ce_searched": False}, evidence, TODAY)["weight"] == 0.6
    assert signal_weight({**sig, "annotations": [{"action": "dispute"}]}, evidence, TODAY)["weight"] == 0.25


def test_relevance_is_bounded_and_oriented():
    assert relevance({"demand": 1.0}, {"demand": 1.0, "supply": 1.0}) == 0.5
    assert relevance({"demand": -1.0}, {"demand": 1.0}) == -1.0
    assert relevance(None, {"demand": 1.0}) == 0.0


def test_world1_selects_four_and_sums_to_one():
    cfg = load("scenario_archetypes.json")
    signals, evidence = load("worlds/1/signals.json"), load("worlds/1/evidence.json")
    w = compute_weights(signals, evidence, TODAY)
    res = select_scenarios(cfg["archetypes"], signals, w, cfg["scaling_k"])
    assert len(res["scenarios"]) == 4 and abs(sum(s["probability"] for s in res["scenarios"]) - 1) < 1e-3
    assert res["scenarios"][0]["id"] in ("expansion_tight", "nordic_concentration")
    assert all(len(s["path"]["demand"]) == 37 for s in res["scenarios"])
    assert 0.0 <= res["entropy"] <= 1.0


def test_world2_selects_a_different_picture():
    cfg = load("scenario_archetypes.json")
    r1 = select_scenarios(cfg["archetypes"], load("worlds/1/signals.json"), compute_weights(load("worlds/1/signals.json"), load("worlds/1/evidence.json"), TODAY), cfg["scaling_k"])
    r2 = select_scenarios(cfg["archetypes"], load("worlds/2/signals.json"), compute_weights(load("worlds/2/signals.json"), load("worlds/2/evidence.json"), TODAY), cfg["scaling_k"])
    assert r1["scenarios"][0]["id"] != r2["scenarios"][0]["id"]
    assert r2["scenarios"][0]["id"] in ("contraction_surplus", "inventory_correction", "grid_baseline")
    s1 = plain_summary(r1, load("worlds/1/signals.json"), compute_weights(load("worlds/1/signals.json"), load("worlds/1/evidence.json"), TODAY), "en")
    s2 = plain_summary(r2, load("worlds/2/signals.json"), compute_weights(load("worlds/2/signals.json"), load("worlds/2/evidence.json"), TODAY), "fi")
    assert "growing" in s1 and "Todennäköisin" in s2


def test_placeholder_internal_signal_has_zero_weight():
    w = compute_weights(load("worlds/1/signals.json"), load("worlds/1/evidence.json"), TODAY)
    assert w["SIG-017"]["weight"] == 0.0


def test_bullwhip_metrics():
    assert amplification_ratio(1.10, 0.55, 1.3)["status"] == "hoarding_risk"
    assert momentum([25, 95.5, 60.5, 15.5], -20)["status"] == "hoarding_ending"
    assert spot_contract_spread([12, 28, 22, 14, 9, 6], 10)["status"] == "hoarding_ending"
    assert compute_bullwhip(load("worlds/1/bullwhip.json"))["overall"] == "mixed_turning"
    assert compute_bullwhip(load("worlds/2/bullwhip.json"))["overall"] == "real_demand"


def test_guardrail_keeps_disclaimers_and_leaves_no_marker():
    text = "I can't tell you whether you should buy busbars now. That decision belongs to you as planner.\n- You should order more relays now.\n- Copper is high [SIG-010]."
    clean, removed = recommendation_filter(text)
    assert removed == ["- You should order more relays now."]
    assert clean.startswith("I can't tell you whether you should buy busbars now.") and "removed by guardrail" not in clean
    assert clean.splitlines()[-1] == "- Copper is high [SIG-010]."


def test_guardrail_strips_recommendations():
    clean, removed = recommendation_filter("Demand is rising. We recommend ordering 5,000 additional units now. Supply is tight.")
    assert len(removed) == 1 and "5,000" not in clean and "Demand is rising." in clean


def test_pipeline_replay_run():
    os.environ["AGENT_MODE"] = "replay"
    from agents.llm import LLMClient, load_replay
    from agents.pipeline import Context, Pipeline
    signals, evidence, cfg, bw = load("worlds/1/signals.json"), load("worlds/1/evidence.json"), load("scenario_archetypes.json"), load("worlds/1/bullwhip.json")
    replay = load_replay(str(DATA / "replay.json"))
    ctx = Context(today=TODAY, signals=signals, evidence=evidence, scenario_config=cfg, bullwhip_config=bw, replay=replay, llm=LLMClient(), item=replay["demo_fingrid_q3"]["item"])
    Pipeline().run(ctx)
    assert ctx.trace[0].agent == "Collector & normaliser" and ctx.trace[-1].agent == "Explainer agent"
    assert ctx.new_signal["id"] == "SIG-001" and ctx.new_signal["value"]["number"] == 3.6 and ctx.new_signal["axes"]["nordic"] == 0.8
    assert ctx.after is not None and len(ctx.after["scenarios"]) == 4
    assert ctx.brief and "SIG-001" in ctx.brief["text"]
    assert all(t.status in ("ok", "degraded") for t in ctx.trace)
