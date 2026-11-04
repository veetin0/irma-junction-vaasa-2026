"""Impact (contract C8) and the weight ensemble relation (C9). Run from app/: python -m pytest tests -q"""
from __future__ import annotations

import math
import os
import sys
from pathlib import Path

os.environ.setdefault("DEMO_TODAY", "2026-10-03")
os.environ["AGENT_MODE"] = "replay"
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from fastapi.testclient import TestClient  # noqa: E402

import main  # noqa: E402
from engine import impact as imp  # noqa: E402
from engine.weights import UNCHALLENGED_CAP  # noqa: E402

client = TestClient(main.app)


def setup_function():
    client.post("/api/reset")


def _card(direction=1, measures="end_demand", axes=None, **kw):
    return {"id": "X-1", "direction": direction, "measures": measures,
            "axes": {"demand": 0.9, "supply": 0.0, "policy": 0.0, "price": 0.0, "nordic": 0.0, "bullwhip": 0.0} if axes is None else axes, **kw}


def _w(materiality):
    return {"components": {"materiality": materiality}}


# ---- sign rule ---------------------------------------------------------------------------------
def test_sign_rule_by_measure_and_direction():
    expect = {("end_demand", 1): 1, ("end_demand", -1): -1,
              ("intermediary", 1): 1, ("intermediary", -1): -1,
              ("policy", 1): 1, ("policy", -1): -1,
              ("supply_tightness", 1): -1, ("supply_tightness", -1): 1,    # tighter supply hurts delivery, easing helps
              ("price", 1): -1, ("price", -1): 1}                           # rising component or commodity price hurts
    for (measures, direction), sign in expect.items():
        out = imp.compute_impact(_card(direction, measures), _w(0.8))
        assert out["parts"]["sign"] == sign, (measures, direction)
        assert (out["impact"] > 0) == (sign > 0) and (out["impact"] < 0) == (sign < 0)


def test_no_direction_means_no_claimed_effect():
    out = imp.compute_impact(_card(0, "end_demand"), _w(0.9))
    assert out["impact"] == 0 and out["parts"]["sign"] == 0


def test_unknown_measure_reads_direction_at_face_value():
    assert imp.compute_impact(_card(-1, "something_new"), _w(0.5))["parts"]["sign"] == -1


# ---- size --------------------------------------------------------------------------------------
def test_size_formula_and_a_ref_cap():
    axes = {"demand": 0.6, "supply": -0.3, "policy": 0.0, "price": 0.0, "nordic": 0.0, "bullwhip": 0.0}
    out = imp.compute_impact(_card(1, "end_demand", axes), _w(0.5))
    load = (0.6 + 0.3) / imp.A_REF
    assert out["parts"]["theme_load"] == round(load, 4)
    assert out["impact"] == round(100 * 0.5 * load)
    heavy = {k: 1.0 for k in imp.AXES}                       # Σ|axes| = 6 > A_ref: theme_load saturates at 1
    top = imp.compute_impact(_card(-1, "end_demand", heavy), _w(1.0))
    assert top["parts"]["theme_load"] == 1.0 and top["impact"] == -100
    assert imp.compute_impact(_card(1, "end_demand", heavy), _w(1.0))["impact"] == 100


def test_impact_is_zero_without_axes_or_materiality():
    assert imp.compute_impact(_card(1, axes={}), _w(0.9))["impact"] == 0
    assert imp.compute_impact(_card(1), _w(0.0))["impact"] == 0
    assert imp.compute_impact(_card(1), {})["impact"] == 0


def test_a_ref_is_an_assumption_label():
    assert imp.A_REF == 1.5 and imp.LABEL == "ASSUMPTION"
    assert any(a["name"] == "impact_a_ref" and a["label"] == "ASSUMPTION" for a in imp.ASSUMPTIONS)


# ---- state ---------------------------------------------------------------------------------------
def _check_state(st):
    assert st["signals"]
    for s in st["signals"]:
        i = s["impact"]
        assert isinstance(i["impact"], int) and -100 <= i["impact"] <= 100, s["id"]
        assert i["label"] == "ASSUMPTION"
        assert set(i["parts"]) == {"sign", "materiality", "theme_load"}
        assert i["parts"]["sign"] in (-1, 0, 1) and 0 <= i["parts"]["theme_load"] <= 1 and 0 <= i["parts"]["materiality"] <= 1
        assert i["parts"]["materiality"] == s["computed"]["components"]["materiality"]
        assert i["impact"] == imp.compute_impact(s, s["computed"])["impact"]
        assert i["parts"]["sign"] == imp.impact_sign(s)
        if i["parts"]["sign"] == 0:
            assert i["impact"] == 0
        else:
            assert (i["impact"] >= 0) == (i["parts"]["sign"] > 0)


def test_every_state_signal_has_impact_in_range_in_both_worlds():
    _check_state(client.get("/api/state").json())
    _check_state(client.post("/api/world", json={"world": 2}).json()["state"])
    client.post("/api/world", json={"world": 1})


def test_state_meta_impact_documents_the_formula():
    m = client.get("/api/state").json()["meta"]["impact"]
    assert m["a_ref"] == imp.A_REF and m["label"] == "ASSUMPTION" and "Σ|axes| / A_ref" in m["formula"]
    assert m["sign_rule"]["en"] and m["sign_rule"]["fi"]
    assert client.get("/api/method").json()["impact"]["a_ref"] == imp.A_REF


def test_signal_endpoint_carries_impact_and_market():
    sig = client.get("/api/signals/SIG-007").json()
    assert sig["market"] == "datacenter" and sig["impact"]["parts"]["sign"] == -1       # DRAM price rising: unfavourable
    assert client.get("/api/signals/SIG-001").json()["impact"]["parts"]["sign"] == 1    # signed connection agreements: favourable


def test_known_cards_have_the_expected_sign():
    by_id = {s["id"]: s for s in client.get("/api/state").json()["signals"]}
    assert by_id["SIG-008"]["impact"]["parts"]["sign"] == -1       # MCU lead times lengthening
    assert by_id["SIG-005"]["impact"]["parts"]["sign"] == -1       # US delays and cancellations
    assert by_id["SIG-014"]["impact"]["parts"]["sign"] == -1       # connection priority rule change
    assert by_id["SIG-017"]["impact"]["impact"] == 0               # internal placeholder, no direction
    assert any(s["impact"]["impact"] > 0 for s in by_id.values()) and any(s["impact"]["impact"] < 0 for s in by_id.values())


# ---- ensemble relation (C9): the weight used is the documented combination of the four conditions ----------
def test_ensemble_weight_is_the_documented_combination_and_the_map_axis_uses_it():
    st = client.get("/api/state").json()
    for s in st["signals"]:
        c, comp = s["computed"], s["computed"]["components"]
        methods = c["band"]["methods"]
        assert set(methods) == {"product", "minimum", "geometric", "arithmetic"}
        assert c["weight"] == methods["product"], s["id"]                       # the weight used is the product estimator
        factors = [comp["credibility"], comp["freshness"], comp["materiality"], comp["human"]]
        capped = not s.get("ce_searched", False)

        def bound(x):
            x = min(1.0, max(0.0, x))
            return min(x, UNCHALLENGED_CAP) if capped else x

        assert math.isclose(c["weight"], bound(math.prod(factors)), abs_tol=2e-3), s["id"]
        assert math.isclose(methods["minimum"], bound(min(factors)), abs_tol=2e-3), s["id"]
        assert math.isclose(methods["geometric"], bound(math.prod(factors) ** 0.25), abs_tol=2e-3), s["id"]
        assert math.isclose(methods["arithmetic"], bound(sum(factors) / 4), abs_tol=2e-3), s["id"]
        assert c["band"]["min"] == min(methods.values()) and c["band"]["max"] == max(methods.values())
        # The map's y axis is weight (and weight × T(h) per horizon): never a different estimator.
        for h, wh in c["horizon"].items():
            assert wh <= c["weight"] + 1e-9
            assert math.isclose(wh, c["weight"] * c["horizon_fit"][h], abs_tol=2e-4)
        assert 0.0 <= c["weight"] <= 1.0
