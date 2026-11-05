"""Oil and gas signal cards and counter-evidence (contract C10, M4.2a). Run from app/: python -m pytest tests -q

Checks the shape, the sourcing rule (every figure has a SOURCE with URL, or is labelled DEMODATA / ASSUMPTION),
counter-evidence on every card, and the six theme axes. The files are plain data; no network access is used.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP / "backend"))

from engine.weights import compute_weights  # noqa: E402

DATA = APP / "backend" / "data"
OG = DATA / "segments" / "oilgas"
AXES = ("demand", "supply", "policy", "price", "nordic", "bullwhip")
LABELS = {"SOURCE", "DEMODATA", "ASSUMPTION"}
REGIONS = {"FI", "NORDICS", "EU", "US", "GLOBAL"}
CLASSES = {"structural", "cyclical", "mixed"}
SOURCE_CLASSES = {"news", "policy", "research", "price", "contract"}
MEASURES = {"end_demand", "intermediary", "policy", "supply_tightness", "price"}
FREQUENCIES = {"event", "daily", "weekly", "monthly", "quarterly", "annual"}
CATEGORIES = {"demand", "supply", "policy", "price", "bullwhip"}
# the key set every world 1 card carries (cards here must match it so the engine and UI treat them alike)
SCHEMA = {"id", "name", "short", "short_fi", "category", "measures", "region", "segment", "market", "type", "lead_months",
          "lead_months_rationale", "update_frequency", "source", "reliability", "direction", "strength", "observed_at",
          "classification", "classification_rationale", "value", "data_label", "excerpt", "history", "history_label",
          "history_note", "usage_restrictions", "counter_evidence", "ce_searched", "annotations", "source_class", "locked",
          "tracking", "axes"}
DC_PHRASES = ("data centre", "data center", "hyperscal", "fingrid", "datacentre")

SIGNALS = json.loads((OG / "signals.json").read_text(encoding="utf-8"))
EVIDENCE = json.loads((OG / "evidence.json").read_text(encoding="utf-8"))
EVIDENCE_BY_ID = {e["id"]: e for e in EVIDENCE}


def _is_date(s: str) -> bool:
    try:
        date.fromisoformat(s)
        return True
    except (TypeError, ValueError):
        return False


def test_card_count_and_unique_ids():
    assert 8 <= len(SIGNALS) <= 12
    ids = [s["id"] for s in SIGNALS]
    assert len(set(ids)) == len(ids)
    assert all(re.fullmatch(r"OG-\d{3}", i) for i in ids)
    ce_ids = [e["id"] for e in EVIDENCE]
    assert len(set(ce_ids)) == len(ce_ids)
    assert all(re.fullmatch(r"OG-CE-\d{3}", i) for i in ce_ids)
    assert not set(ids) & {s["id"] for s in json.loads((DATA / "worlds" / "1" / "signals.json").read_text(encoding="utf-8"))}


@pytest.mark.parametrize("card", SIGNALS, ids=lambda c: c["id"])
def test_schema(card):
    assert set(card) == SCHEMA, f"{card['id']}: extra {set(card) - SCHEMA}, missing {SCHEMA - set(card)}"
    assert card["market"] == "oilgas" and card["segment"] == "oilgas"
    assert card["category"] in CATEGORIES
    assert card["measures"] in MEASURES
    assert card["region"] in REGIONS
    assert card["classification"] in CLASSES
    assert card["source_class"] in SOURCE_CLASSES
    assert card["update_frequency"] in FREQUENCIES
    assert card["reliability"] in {"A", "B", "C"}
    assert card["direction"] in (-1, 0, 1)
    assert 0.0 <= card["strength"] <= 1.0
    assert card["type"] in {"leading", "lagging", "coincident"}
    assert isinstance(card["lead_months"], (int, float)) and card["lead_months"] > 0
    assert card["lead_months_rationale"].startswith("[ASSUMPTION")
    assert card["classification_rationale"].strip()
    assert card["name"].strip() and card["short"].strip() and card["short_fi"].strip()
    assert isinstance(card["value"].get("number"), (int, float)) and card["value"]["unit"] and card["value"]["label"]
    assert _is_date(card["observed_at"])
    assert card["observed_at"] == card["source"]["date"]


@pytest.mark.parametrize("card", SIGNALS, ids=lambda c: c["id"])
def test_six_axes(card):
    assert tuple(card["axes"]) == AXES
    assert all(isinstance(v, (int, float)) and -1.0 <= v <= 1.0 for v in card["axes"].values())
    assert any(v != 0 for v in card["axes"].values()), "a card with no axis loading cannot be placed on any theme"


def test_every_axis_is_used_by_some_card():
    for axis in AXES:
        assert any(abs(c["axes"][axis]) > 0 for c in SIGNALS), f"no card loads the {axis} axis"


@pytest.mark.parametrize("card", SIGNALS, ids=lambda c: c["id"])
def test_sources(card):
    """Every figure carries SOURCE (name, https URL, date) or an explicit DEMODATA / ASSUMPTION label."""
    assert card["data_label"] in LABELS
    assert card["history_label"] in LABELS | {"NONE"}
    src = card["source"]
    assert src["name"].strip() and _is_date(src["date"])
    if card["data_label"] == "SOURCE":
        assert re.match(r"https://[^\s/]+\.[^\s]+", src["url"]), f"{card['id']}: SOURCE card needs an https URL"
        assert len(card["excerpt"].strip()) >= 40, "excerpt is quoted from the page"
    if card["history"]:
        assert card["history_label"] != "NONE"
        assert all(_is_date(p["date"]) for p in card["history"])
    else:
        assert card["history_label"] == "NONE"


@pytest.mark.parametrize("card", SIGNALS, ids=lambda c: c["id"])
def test_counter_evidence(card):
    assert card["ce_searched"] is True
    assert card["counter_evidence"], f"{card['id']} has no counter-evidence"
    for ce_id in card["counter_evidence"]:
        assert ce_id in EVIDENCE_BY_ID, f"{card['id']} cites unknown {ce_id}"
        assert EVIDENCE_BY_ID[ce_id]["against"] == card["id"]


def test_evidence_schema_and_sources():
    ids = {s["id"] for s in SIGNALS}
    for e in EVIDENCE:
        assert set(e) == {"id", "against", "claim", "source", "reliability", "strength", "data_label"}
        assert e["against"] in ids, f"{e['id']} is against an unknown card"
        assert len(e["claim"].strip()) >= 40
        assert e["reliability"] in {"A", "B", "C"}
        assert 0.0 < e["strength"] <= 1.0
        assert e["data_label"] in LABELS
        assert e["source"]["name"].strip() and _is_date(e["source"]["date"])
        if e["data_label"] == "SOURCE":
            assert e["source"]["url"].startswith("https://")
    # nothing in the evidence file is orphaned: every item is listed on the card it is against
    for e in EVIDENCE:
        card = next(s for s in SIGNALS if s["id"] == e["against"])
        assert e["id"] in card["counter_evidence"]


def test_balance_of_directions():
    """The pool carries both favourable and unfavourable readings, so the segment is not one-sided."""
    directions = {c["direction"] for c in SIGNALS}
    assert 1 in directions and -1 in directions
    assert {"structural", "cyclical"} <= {c["classification"] for c in SIGNALS}


def test_no_data_centre_text():
    for c in SIGNALS:
        text = " ".join(str(c[k]) for k in ("name", "short", "short_fi", "classification_rationale", "lead_months_rationale")).lower()
        assert not any(p in text for p in DC_PHRASES), f"{c['id']} reads like a data-centre card"


def test_engine_weights_load():
    """The shared engine computes a weight in [0, 1] for every card with its counter-evidence."""
    w = compute_weights(SIGNALS, EVIDENCE, date(2026, 10, 3))
    assert set(w) == {c["id"] for c in SIGNALS}
    assert all(0.0 <= v["weight"] <= 1.0 for v in w.values())
