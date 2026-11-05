"""Oil and gas scenario pool, recommendation templates and bullwhip inputs (contract C10, M4.2b).

Covers data/segments/oilgas/{scenario_archetypes,recommendations,bullwhip}.json. The signals and evidence files are
built separately and are only read here for a cross-check when they exist.
Run from app/:  python -m pytest tests -q
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import date
from pathlib import Path

os.environ.setdefault("DEMO_TODAY", "2026-10-03")
BACKEND = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND))

from agents.llm import recommendation_filter  # noqa: E402
from engine.archetypes import AXES, select_scenarios  # noqa: E402
from engine.bullwhip import METHODS, compute_bullwhip  # noqa: E402
from engine.recommend import build_recommendation, template_texts  # noqa: E402

DATA = BACKEND / "data"
OG = DATA / "segments" / "oilgas"
AREAS = {"procurement", "manufacturing", "capacity", "supply_reliability"}
QUANTITY = re.compile(r"\d+([.,]\d+)?\s*(%|per cent|percent|units?|pcs|pieces|relays?|boards?|weeks?|months?|days?|years?|tonnes?|gw|mw|twh|eur|usd|k\b|m\b|bn\b)", re.IGNORECASE)
ORDER_WORDS = re.compile(r"\b(reorder point|order point|safety stock of|order quantity|re-order|reorder)\b", re.IGNORECASE)
INTERNAL_TERMS = re.compile(r"no[_ -]regret|hedge|kernel", re.IGNORECASE)
DATACENTRE = re.compile(r"data[- ]?centre|data[- ]?center|hyperscal|datakeskus", re.IGNORECASE)


def _read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


ARCH = _read(OG / "scenario_archetypes.json")
DC_ARCH = _read(DATA / "scenario_archetypes.json")
TPL = _read(OG / "recommendations.json")
DC_TPL = _read(DATA / "recommendations.json")
BW = _read(OG / "bullwhip.json")
DC_BW = _read(DATA / "worlds" / "1" / "bullwhip.json")
ARCHETYPES = ARCH["archetypes"]
IDS = [a["id"] for a in ARCHETYPES]


def _pairs(node):
    """Every {en, fi} text pair inside a structure."""
    if isinstance(node, dict):
        if set(node) == {"en", "fi"} and all(isinstance(v, str) for v in node.values()):
            yield node
        else:
            for v in node.values():
                yield from _pairs(v)
    elif isinstance(node, list):
        for v in node:
            yield from _pairs(v)


# ----------------------------------------------------------------- archetypes -------------
def test_at_least_six_archetypes_with_og_ids_and_priors_summing_to_one():
    assert len(ARCHETYPES) >= 6
    assert len(set(IDS)) == len(IDS)
    assert all(re.fullmatch(r"og_[a-z0-9_]+", i) for i in IDS)
    assert not set(IDS) & {a["id"] for a in DC_ARCH["archetypes"]}
    assert sum(a["prior"] for a in ARCHETYPES) == 1.0
    assert all(0 < a["prior"] < 1 for a in ARCHETYPES)


def test_archetype_schema_matches_the_datacenter_file():
    assert set(ARCH) == set(DC_ARCH)
    assert ARCH["scaling_k"] == DC_ARCH["scaling_k"] and "ASSUMPTION" in ARCH["scaling_note"]
    keys = set(DC_ARCH["archetypes"][0])
    for a in ARCHETYPES:
        assert set(a) == keys, a["id"]
        assert list(a["profile"]) == AXES and set(a["profile"]) == set(DC_ARCH["archetypes"][0]["profile"])
        assert all(-1.0 <= v <= 1.0 for v in a["profile"].values()), a["id"]
        assert set(a["path"]) == {"demand_yearly", "supply_yearly", "band"}
        assert len(a["path"]["demand_yearly"]) == len(a["path"]["supply_yearly"]) == 3
        assert set(a["abb_interpretation"]) == {"demand", "delivery", "components"}
        assert a["signposts"] and a["falsifiers"]
        for item in a["signposts"] + a["falsifiers"]:
            assert set(item) == {"text", "signal_id"}


def test_every_number_in_the_pool_is_labelled():
    for a in ARCHETYPES:
        note = a["prior_note"]
        assert note.startswith("[ASSUMPTION"), a["id"]          # priors and path rates are hand-set
        if re.search(r"USD|%|\d{4}", note.replace("the eight priors", "").replace("2022-2023", "")):
            assert "[SOURCE]" in note, a["id"]               # a quoted figure carries its label
    assert "ASSUMPTION" in ARCH["scaling_note"]


def test_en_fi_parity_in_the_archetypes():
    pairs = list(_pairs(ARCHETYPES))
    assert len(pairs) >= 10 * len(ARCHETYPES)
    for p in pairs:
        assert p["en"].strip() and p["fi"].strip(), p
        assert p["en"] != p["fi"], p
    for a in ARCHETYPES:
        assert len(a["narrative"]["en"]) > 80 and len(a["narrative"]["fi"]) > 80


def test_signpost_ids_are_og_ids_and_exist_when_the_signals_file_is_present():
    ids = {i["signal_id"] for a in ARCHETYPES for i in a["signposts"] + a["falsifiers"]}
    assert all(re.fullmatch(r"OG-\d{3}", i) for i in ids), ids
    sig_path = OG / "signals.json"
    if sig_path.is_file():
        known = {s["id"] for s in _read(sig_path)}
        assert ids <= known, sorted(ids - known)


def test_no_datacenter_text_in_the_oilgas_files():
    for node in (ARCH, TPL, BW):
        blob = json.dumps(node, ensure_ascii=False)
        assert not DATACENTRE.search(blob), DATACENTRE.search(blob).group(0)


def test_archetypes_rank_through_the_engine():
    """The pool works with select_scenarios: a signal that loads on supply and bullwhip lifts the rush archetype."""
    sig = {"id": "OG-T1", "axes": {"demand": 0.3, "supply": 0.8, "policy": 0.0, "price": 1.0, "nordic": 0.0, "bullwhip": 1.0}}
    flat = {"id": "OG-T2", "axes": {a: 0.0 for a in AXES}}
    weights = {"OG-T1": {"weight": 0.9}, "OG-T2": {"weight": 0.9}}
    res = select_scenarios(ARCHETYPES, [sig, flat], weights, k=ARCH["scaling_k"])
    assert len(res["scenarios"]) == 4 and abs(sum(s["probability"] for s in res["scenarios"]) - 1.0) < 1e-3
    assert res["scenarios"][0]["id"] == "og_shock_rush"


# ------------------------------------------------------------------ templates -------------
def test_templates_cover_every_archetype_and_nothing_else():
    assert set(TPL["archetypes"]) == set(IDS)


def test_template_schema_matches_the_datacenter_file():
    assert set(TPL) == set(DC_TPL)
    for key in ("confidence_rules", "defaults", "confidence_labels", "headline_template", "disclaimer"):
        assert TPL[key] == DC_TPL[key], key
    assert set(TPL["hedge_template"]) == {"en", "fi"}
    for key in ("{runner}", "{runner_p}", "{lead}", "{shift}"):
        assert key in TPL["hedge_template"]["en"] and key in TPL["hedge_template"]["fi"], key
    dc_a = next(iter(DC_TPL["archetypes"].values()))
    dc_move = dc_a["moves"][0]
    for sid, t in TPL["archetypes"].items():
        assert set(t) == set(dc_a), sid
        assert set(t["next_action"]) == set(dc_a["next_action"]), sid
        for m in t["moves"]:
            assert set(m) == set(dc_move), sid
    for key, th in TPL["themes"].items():
        dc_th = DC_TPL["themes"]["memory_supply"]
        assert {"label", "select", "fallback_axis"} <= set(th) <= set(dc_th) | set(DC_TPL["themes"]["abb_order_book"]), key
        assert th["fallback_axis"] in AXES, key


def test_each_archetype_has_three_or_four_moves_with_a_move_that_pays_off_anyway():
    for sid, t in TPL["archetypes"].items():
        moves = t["moves"]
        assert 3 <= len(moves) <= 4, sid
        assert any(m["type"] == "no_regret" for m in moves), sid
        assert all(m["area"] in AREAS and m["type"] in ("no_regret", "contingent") and m["horizon_months"] in (12, 24, 36) for m in moves), sid
        assert len({m["area"] for m in moves}) == len(moves), sid          # one move per area
        assert all(k in TPL["themes"] for m in moves for k in m["themes"]), sid
        assert t["next_action"]["due_days"] > 0 and t["next_action"]["owner"]["en"]
        for m in moves:
            assert "{themes}" in m["trigger"]["en"] and "{themes}" in m["trigger"]["fi"], sid
    used = {k for t in TPL["archetypes"].values() for m in t["moves"] for k in m["themes"]}
    assert used == set(TPL["themes"])                                       # no unused theme


def test_en_fi_parity_in_the_templates():
    pairs = list(_pairs({k: v for k, v in TPL.items() if not k.startswith("_")}))
    assert len(pairs) > 120
    for p in pairs:
        assert p["en"].strip() and p["fi"].strip(), p
        if p["en"] not in ("low", "medium", "high"):
            assert p["en"] != p["fi"], p
    for sid, t in TPL["archetypes"].items():
        assert t["headline_move"]["en"] and t["headline_move"]["fi"] and t["if_leading"]["fi"], sid


def test_template_texts_pass_the_guardrail_and_carry_no_numbers_or_internal_terms():
    texts = template_texts(TPL)
    assert len(texts) > 120
    for t in texts:
        clean, removed = recommendation_filter(t)
        assert removed == [] and clean == t.strip(), t
        stripped = re.sub(r"\{[a-z_]+\}", "", t)
        assert not QUANTITY.search(stripped) and not ORDER_WORDS.search(stripped), t
        assert not INTERNAL_TERMS.search(t), t
    for sid, tpl in TPL["archetypes"].items():
        for m in tpl["moves"]:
            for key in ("text", "trigger", "cost_if_wrong"):
                for v in m[key].values():
                    assert not re.search(r"\d", v), (sid, v)
        for key in ("headline_move", "if_leading"):
            for v in tpl[key].values():
                assert not re.search(r"\d", v), (sid, v)
    assert "planner decides" in TPL["disclaimer"]["en"].lower() and "päätöksen tekee" in TPL["disclaimer"]["fi"].lower()


def _signals_fixture():
    """A small oil and gas signal set, with the fields the theme rules read."""
    def sig(i, cat, meas, region, cls, axes):
        return {"id": f"OG-{i:03d}", "category": cat, "measures": meas, "region": region, "source_class": cls, "direction": 1,
                "axes": {**{a: 0.0 for a in AXES}, **axes}}
    sigs = [
        sig(1, "price", "price", "GLOBAL", "price", {"price": 0.8}),
        sig(2, "demand", "end_demand", "GLOBAL", "research", {"demand": -0.5}),
        sig(3, "demand", "end_demand", "EU", "news", {"demand": 0.7}),
        sig(4, "demand", "end_demand", "NO", "news", {"nordic": 0.6, "demand": 0.2}),
        sig(5, "policy", "policy", "EU", "policy", {"policy": 0.7}),
        sig(6, "policy", "policy", "NO", "policy", {"policy": 0.8, "nordic": 0.5}),
        sig(7, "supply", "supply_tightness", "GLOBAL", "news", {"supply": 0.7}),
        sig(8, "bullwhip", "intermediary", "GLOBAL", "research", {"bullwhip": 0.8}),
        sig(9, "demand", "intermediary", "NORDICS", "contract", {"demand": 0.5}),
    ]
    weights = {s["id"]: {"weight": 0.5 + 0.01 * i} for i, s in enumerate(sigs)}
    return sigs, weights


def test_every_archetype_builds_a_recommendation_with_real_trigger_ids():
    sigs, weights = _signals_fixture()
    ids = {s["id"] for s in sigs}
    for a in ARCHETYPES:
        others = [x for x in ARCHETYPES if x["id"] != a["id"]]
        fake = {"scenarios": [{"id": a["id"], "name": a["name"], "probability": 0.4},
                              {"id": others[0]["id"], "name": others[0]["name"], "probability": 0.3},
                              {"id": others[1]["id"], "name": others[1]["name"], "probability": 0.2},
                              {"id": others[2]["id"], "name": others[2]["name"], "probability": 0.1}], "entropy": 0.8}
        r = build_recommendation(fake, sigs, weights, date(2026, 10, 3), TPL)
        assert r and r["scenario_id"] == a["id"], a["id"]
        assert 3 <= len(r["moves"]) <= 4 and any(m["type"] == "no_regret" for m in r["moves"])
        assert all(m["trigger_signals"] and set(m["trigger_signals"]) <= ids for m in r["moves"]), a["id"]
        assert r["runner_up"]["name"]["en"] in r["hedge"]["en"] and r["hedge"]["fi"]
        assert r["headline"]["en"].startswith("Recommended move") and r["headline"]["fi"].startswith("Suositeltu siirto")
        assert "planner decides" in r["disclaimer"]["en"].lower()
        for text in [v for m in r["moves"] for k in ("text", "cost_if_wrong") for v in m[k].values()]:
            clean, removed = recommendation_filter(text)
            assert removed == [] and clean == text.strip(), text


# ------------------------------------------------------------------- bullwhip -------------
def test_bullwhip_inputs_match_the_datacenter_structure_and_are_labelled():
    assert set(BW) == set(DC_BW)
    assert [m["id"] for m in BW["metrics"]] == [m["id"] for m in DC_BW["metrics"]]
    for m, dc in zip(BW["metrics"], DC_BW["metrics"]):
        assert set(m) == set(dc), m["id"]
        assert m["method"] == dc["method"] and m["method"] in METHODS
        assert set(m["inputs"]) == set(dc["inputs"]), m["id"]
        assert m["inputs_label"] in ("SOURCE", "DEMODATA", "ASSUMPTION"), m["id"]
        assert m["inputs_label"] in m["inputs_note"] or m["inputs_label"] == "SOURCE" and "[SOURCE]" in m["inputs_note"], m["id"]
        assert m["sources"] and all("name" in s and "url" in s for s in m["sources"])
    sourced = [m for m in BW["metrics"] if m["inputs_label"] == "SOURCE"]
    assert sourced and all(s["url"].startswith("https://") for m in sourced for s in m["sources"])


def test_bullwhip_engine_computes_from_the_oilgas_inputs():
    res = compute_bullwhip(BW)
    assert len(res["metrics"]) == 5 and res["overall"] in ("hoarding_risk", "real_demand", "mixed_turning", "inconclusive")
    by_id = {m["id"]: m for m in res["metrics"]}
    assert by_id["BW-5"]["status"] == "not_connected"
    assert by_id["BW-1"]["value"] == round((1 + 0.35) / (1 + 0.10), 2)
    # BW-2 recomputes from the quoted EIA quarterly averages, so the stored series cannot drift from its source.
    q = [68.01, 69.00, 63.63, 81.11, 102.93, 95.95]
    series = [round((b / a - 1) * 100, 1) for a, b in zip(q, q[1:])]
    assert BW["metrics"][1]["inputs"]["series"] == series
