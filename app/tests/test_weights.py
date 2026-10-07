"""Invariant tests for the ensemble signal weight and horizon fit (contract C1, C2).

Run from app/:  DEMO_TODAY=2026-10-03 python -m pytest tests -q
"""
from __future__ import annotations

import json
import math
import os
import sys
from datetime import date, datetime
from pathlib import Path

os.environ.setdefault("DEMO_TODAY", "2026-10-03")
os.environ["AGENT_MODE"] = "replay"
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

import pytest  # noqa: E402

from engine.weights import (  # noqa: E402
    FORMULA, UNCHALLENGED_CAP, compute_weights, horizon_fit, horizon_weights, signal_weight,
)

DATA = Path(__file__).resolve().parents[1] / "backend" / "data"
TODAY = date(2026, 10, 3)
WORLDS = ("1", "2")


def load(path):
    return json.loads((DATA / path).read_text(encoding="utf-8"))


def old_weight(sig, evidence_by_id, today):
    """The pre-M1 formula, written out independently: w = R * F * S * (1 - C) * H, unchallenged cap, no clamp."""
    grade = {"A": 1.0, "B": 0.7, "C": 0.4}
    half = {"daily": 14, "weekly": 30, "monthly": 60, "quarterly": 120, "annual": 240, "event": 90}
    r = grade.get(sig.get("reliability", "C"), 0.4)
    obs = sig.get("observed_at")
    if obs:
        age = max(0, (today - datetime.strptime(obs[:10], "%Y-%m-%d").date()).days)
        f = round(0.5 ** (age / half.get(sig.get("update_frequency", "event"), 90)), 4)
    else:
        f = 0.0
    s = max(0.0, min(1.0, float(sig.get("strength", 0.0))))
    survive = 1.0
    for ce_id in sig.get("counter_evidence", []):
        ce = evidence_by_id.get(ce_id)
        if ce:
            survive *= 1.0 - grade.get(ce.get("reliability", "C"), 0.4) * float(ce.get("strength", 0.0))
    c = round(min(0.8, 1.0 - survive), 4)
    hf = 1.0
    for a in sig.get("annotations", []) or []:
        hf *= {"confirm": 1.2, "dispute": 0.5, "comment": 1.0}.get(a.get("action", "comment"), 1.0)
    hf = round(max(0.25, min(1.5, hf)), 4)
    raw = r * f * s * (1.0 - c) * hf
    if not sig.get("ce_searched", False) and raw > 0.6:
        raw = 0.6
    return round(raw, 4)


def base_card(**kw):
    card = {"id": "S", "reliability": "A", "update_frequency": "quarterly", "observed_at": "2026-10-03",
            "strength": 1.0, "counter_evidence": [], "ce_searched": True, "annotations": [],
            "source": {"name": "Primary", "url": "https://www.example.org/report"},
            "lead_months": 12, "classification": "structural"}
    card.update(kw)
    return card


def world(n):
    signals, evidence = load(f"worlds/{n}/signals.json"), load(f"worlds/{n}/evidence.json")
    return signals, evidence, compute_weights(signals, evidence, TODAY)


# ---- C1: regression against the old formula -----------------------------------------------------
@pytest.mark.parametrize("n", WORLDS)
def test_single_source_equals_old_formula_to_4dp(n):
    signals, evidence, w = world(n)
    by_id = {ce["id"]: ce for ce in evidence}
    for sig in signals:
        assert not sig.get("corroboration"), "fixture assumption: shipped cards are single-source"
        assert w[sig["id"]]["detail"]["materiality"]["estimators"][0]["name"] == "strength"
        # no shipped card has a SOURCE history long enough for the z-score, so M = S everywhere
        assert len(w[sig["id"]]["detail"]["materiality"]["estimators"]) == 1
        assert w[sig["id"]]["weight"] == old_weight(sig, by_id, TODAY), sig["id"]


@pytest.mark.parametrize("n", WORLDS)
def test_credibility_equals_r_times_one_minus_c_for_single_source(n):
    _, _, w = world(n)
    for sid, x in w.items():
        c = x["components"]
        assert abs(c["credibility"] - c["reliability"] * (1 - c["counter_penalty"])) < 1e-4, sid
        assert c["materiality"] == c["strength"], sid


def test_existing_keys_kept_and_new_keys_present():
    _, _, w = world("1")
    for x in w.values():
        assert {"weight", "components", "age_days", "unchallenged_cap_applied", "formula",
                "horizon_fit", "horizon", "band", "attribution", "assumptions"} <= set(x)
        assert {"reliability", "freshness", "strength", "counter_penalty", "human",
                "credibility", "materiality"} <= set(x["components"])
        assert x["formula"] == FORMULA
        assert x["assumptions"] and all(a["label"] == "ASSUMPTION" and a["why"] and isinstance(a["value"], (float, str))
                                        for a in x["assumptions"])
    names = {a["name"] for a in w["SIG-001"]["assumptions"]}
    assert "horizon_kernel_width" in names and "half_life_days" in names


# ---- C1: clamp and cap ---------------------------------------------------------------------------
def test_two_confirms_cannot_push_weight_above_one():
    sig = base_card(annotations=[{"action": "confirm"}, {"action": "confirm"}])
    assert old_weight(sig, {}, TODAY) == 1.44          # the old formula's hole
    out = signal_weight(sig, {}, TODAY)
    assert out["weight"] == 1.0 and out["components"]["human"] == 1.44
    assert all(v <= 1.0 for v in out["horizon"].values())
    assert out["band"]["max"] <= 1.0 and out["attribution"] == []


def test_unchallenged_cap_holds_even_with_confirms():
    sig = base_card(ce_searched=False, annotations=[{"action": "confirm"}, {"action": "confirm"}])
    out = signal_weight(sig, {}, TODAY)
    assert out["weight"] == UNCHALLENGED_CAP and out["unchallenged_cap_applied"] is True
    assert all(v <= UNCHALLENGED_CAP for v in out["horizon"].values())
    assert out["band"]["max"] <= UNCHALLENGED_CAP


@pytest.mark.parametrize("n", WORLDS)
def test_world_weights_bounded_and_capped(n):
    signals, _, w = world(n)
    for sig in signals:
        x = w[sig["id"]]
        assert 0.0 <= x["weight"] <= 1.0
        if not sig.get("ce_searched", False):
            assert x["weight"] <= UNCHALLENGED_CAP and all(v <= UNCHALLENGED_CAP for v in x["horizon"].values())


def test_dispute_halves_the_weight():
    sig = base_card(strength=0.6, reliability="B")
    w0 = signal_weight(sig, {}, TODAY)["weight"]
    w1 = signal_weight({**sig, "annotations": [{"action": "dispute"}]}, {}, TODAY)["weight"]
    assert abs(w1 - 0.5 * w0) < 1e-4


# ---- C1: horizon -----------------------------------------------------------------------------------
@pytest.mark.parametrize("n", WORLDS)
def test_horizon_weight_never_exceeds_weight(n):
    _, _, w = world(n)
    for sid, x in w.items():
        assert set(x["horizon"]) == {"12", "24", "36"} == set(x["horizon_fit"])
        for h in ("12", "24", "36"):
            assert 0.0 <= x["horizon_fit"][h] <= 1.0
            assert x["horizon"][h] <= x["weight"] + 1e-12, (sid, h)
            assert abs(x["horizon"][h] - round(x["weight"] * x["horizon_fit"][h], 4)) < 1e-9


def test_structural_persists_cyclical_fades_after_arrival():
    for lead in (4, 6, 12):
        st = [horizon_fit(base_card(lead_months=lead, classification="structural"), h) for h in (12, 24, 36)]
        cy = [horizon_fit(base_card(lead_months=lead, classification="cyclical"), h) for h in (12, 24, 36)]
        mx = [horizon_fit(base_card(lead_months=lead, classification="mixed"), h) for h in (12, 24, 36)]
        assert st == [1.0, 1.0, 1.0]
        assert cy[0] > cy[1] > cy[2] and cy[2] < 0.5
        assert all(c <= m <= s for c, m, s in zip(cy, mx, st))


def test_effect_not_arrived_is_discounted_the_same_for_every_class():
    fits = {cls: horizon_fit(base_card(lead_months=30, classification=cls), 12) for cls in ("structural", "cyclical", "mixed")}
    assert len(set(fits.values())) == 1
    expected = math.exp(-0.5 * (math.log(12 / 30) / math.log(2)) ** 2)
    assert abs(fits["structural"] - expected) < 1e-12
    st = [horizon_fit(base_card(lead_months=30, classification="structural"), h) for h in (12, 24, 36)]
    assert st[0] < st[1] < st[2] == 1.0          # a structural signal speaks most to the later years


def test_world1_real_cards_follow_lead_and_class():
    _, _, w = world("1")
    dram, fingrid = w["SIG-007"]["horizon_fit"], w["SIG-001"]["horizon_fit"]   # cyclical L=4, structural L=30
    assert dram["12"] > dram["24"] > dram["36"]
    assert fingrid["12"] < fingrid["24"] < fingrid["36"] == 1.0


def test_missing_lead_is_horizon_neutral():
    sig = base_card()
    sig.pop("lead_months")
    assert [horizon_fit(sig, h) for h in (12, 24, 36)] == [1.0, 1.0, 1.0]


def test_horizon_weights_shape():
    _, _, w = world("1")
    hw = horizon_weights(w, 24)
    assert set(hw) == set(w)
    assert all(set(v) == {"weight"} and v["weight"] == w[k]["horizon"]["24"] for k, v in hw.items())


# ---- C1: band and attribution -----------------------------------------------------------------------
@pytest.mark.parametrize("n", WORLDS)
def test_band_contains_weight_and_is_ordered(n):
    _, _, w = world(n)
    for sid, x in w.items():
        b, m = x["band"], x["band"]["methods"]
        assert set(m) == {"product", "minimum", "geometric", "arithmetic"}
        assert b["min"] == min(m.values()) and b["max"] == max(m.values())
        assert b["min"] <= x["weight"] <= b["max"] and m["product"] == x["weight"]
        if x["components"]["human"] <= 1.0:
            # factors in [0, 1]: product <= weakest link <= geometric mean <= arithmetic mean
            assert m["product"] <= m["minimum"] <= m["geometric"] <= m["arithmetic"], sid


@pytest.mark.parametrize("n", WORLDS)
def test_attribution_shares_sum_to_one(n):
    _, _, w = world(n)
    for sid, x in w.items():
        att = x["attribution"]
        if x["weight"] >= 1.0:
            assert att == []
            continue
        assert [a["component"] for a in att] == ["credibility", "currency", "materiality", "human"]
        assert abs(sum(a["share"] for a in att) - 1.0) < 1e-9, sid
        assert all(a["label"] in ("SOURCE", "ASSUMPTION", "DEMODATA") for a in att)


def test_attribution_matches_log_shares_and_zero_factors():
    out = signal_weight(base_card(reliability="B", strength=0.5), {}, TODAY)    # Bel 0.7, F 1, M 0.5, H 1
    shares = {a["component"]: a["share"] for a in out["attribution"]}
    total = math.log(1 / 0.7) + math.log(1 / 0.5)
    assert abs(shares["credibility"] - math.log(1 / 0.7) / total) < 1e-4
    assert shares["currency"] == 0.0 and shares["human"] == 0.0
    zero = signal_weight(base_card(strength=0.0), {}, TODAY)
    assert {a["component"]: a["share"] for a in zero["attribution"]}["materiality"] == 1.0


# ---- C1: corroboration and the z-score estimator ----------------------------------------------------
def test_independent_corroboration_raises_credibility_only_when_independent():
    sig = base_card(reliability="B", strength=0.5)
    single = signal_weight(sig, {}, TODAY)
    indep = signal_weight({**sig, "corroboration": [{"name": "Other", "url": "https://news.other.com/x", "reliability": "B"}]}, {}, TODAY)
    assert abs(indep["components"]["credibility"] - (1 - 0.3 * 0.3)) < 1e-4       # noisy-OR: 1 - (1-0.7)(1-0.7)
    assert indep["weight"] > single["weight"]
    assert indep["detail"]["credibility"]["independent_sources"] == 2
    for dup in ({"name": "Copy", "url": "https://example.org/copy", "reliability": "A"},            # same publisher
                {"name": "Wire", "url": "https://wire.net/x", "reliability": "A", "derived_from": "Primary"},
                {"name": "No URL", "reliability": "A"},
                {"name": "Ungraded", "url": "https://third.net/x"}):
        out = signal_weight({**sig, "corroboration": [dup]}, {}, TODAY)
        assert out["weight"] == single["weight"], dup["name"]


def test_corroboration_and_counter_evidence_combine_as_belief():
    ev = {"CE-1": {"id": "CE-1", "reliability": "A", "strength": 0.5}}
    sig = base_card(reliability="C", counter_evidence=["CE-1"],
                    corroboration=[{"name": "Other", "url": "https://other.com/x", "reliability": "C"}])
    d = signal_weight(sig, ev, TODAY)["detail"]["credibility"]
    s = 1 - 0.6 * 0.6
    assert abs(d["bel"] - s * 0.5) < 1e-4 and abs(d["pl"] - (1 - 0.5 * (1 - s))) < 1e-4 and d["bel"] <= d["pl"]


def _history(values, label):
    return {"history": [{"date": f"2026-{i + 1:02d}-01", "value": v} for i, v in enumerate(values)], "history_label": label}


def test_z_score_only_from_source_history():
    values = [10, 11, 10, 12, 11, 12, 13, 25]          # 7 moves: 6 earlier ones plus a large last move
    src = signal_weight(base_card(strength=0.4, **_history(values, "SOURCE")), {}, TODAY)
    demo = signal_weight(base_card(strength=0.4, **_history(values, "DEMODATA")), {}, TODAY)
    short = signal_weight(base_card(strength=0.4, **_history(values[-5:], "SOURCE")), {}, TODAY)
    assert [e["name"] for e in src["detail"]["materiality"]["estimators"]] == ["strength", "z_score"]
    assert src["detail"]["materiality"]["estimators"][1]["value"] == 1.0           # |z| well above 3.5
    assert src["components"]["materiality"] == 0.7                                   # mean(0.4, 1.0)
    assert demo["components"]["materiality"] == 0.4 and short["components"]["materiality"] == 0.4


# ---- C2: /api/state horizon view -------------------------------------------------------------------------
def test_scenarios_by_horizon_shape_via_api():
    from fastapi.testclient import TestClient
    import main

    client = TestClient(main.app)
    client.post("/api/reset")
    st = client.get("/api/state").json()
    assert st["meta"]["horizon_months"] == [12, 24, 36]
    sbh = st["scenarios_by_horizon"]
    assert set(sbh) == {"12", "24", "36"}
    arche = {a["id"] for a in main.STORE.scenario_config["archetypes"]}
    for h, view in sbh.items():
        assert set(view) == {"scenarios", "entropy", "leader"}
        rows = view["scenarios"]
        assert len(rows) == 4 and all(set(r) == {"id", "name", "probability", "rank"} for r in rows)
        assert [r["rank"] for r in rows] == [1, 2, 3, 4]
        assert all(rows[i]["probability"] >= rows[i + 1]["probability"] for i in range(3))
        assert abs(sum(r["probability"] for r in rows) - 1) < 1e-3
        assert view["leader"] == rows[0]["id"] and {r["id"] for r in rows} <= arche
        assert 0.0 <= view["entropy"] <= 1.0
    assert len(st["scenarios"]["scenarios"]) == 4 and "contributions" in st["scenarios"]["scenarios"][0]   # headline unchanged
    for s in st["signals"]:
        assert set(s["computed"]["horizon"]) == {"12", "24", "36"}
