"""Tests for engine.historical (contract C11): the no-hindsight rule, snapshots and the labelled comparison.

Uses a small fixture, not the real dataset (data/historical/chipcycle.json is written separately).
Run from app/:  python -m pytest tests/test_historical.py -q
"""
from __future__ import annotations

import copy
import os
import sys
from datetime import date
from pathlib import Path

os.environ["AGENT_MODE"] = "replay"
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

import pytest  # noqa: E402

from engine import historical  # noqa: E402
from engine.historical import LABEL, compare, outcome_for, signals_as_of, snapshot, validate  # noqa: E402

SRC = {"name": "Test source", "url": "https://example.com/a", "date": "2021-02-01"}


def card(cid, observed, axes, *, short=None, ce=(), history=(), strength=0.8, **extra):
    return {
        "id": cid, "name": f"Signal {cid}", "short": short or cid, "category": "demand", "measures": "end_demand",
        "region": "GLOBAL", "segment": "datacenter", "type": "leading", "lead_months": 6,
        "update_frequency": "quarterly", "source": {**SRC, "date": observed}, "reliability": "A", "direction": 1,
        "strength": strength, "observed_at": observed, "classification": "cyclical", "data_label": "SOURCE",
        "history": [{"date": d, "value": v} for d, v in history], "history_label": "SOURCE",
        "counter_evidence": list(ce), "ce_searched": True, "annotations": [], "axes": axes, **extra,
    }


def ce(cid, against, date_):
    return {"id": cid, "against": against, "claim": "counter", "source": {**SRC, "date": date_},
            "reliability": "B", "strength": 0.7, "data_label": "SOURCE"}


TIGHT = {"demand": 0.2, "supply": 1.0, "policy": 0.0, "price": 0.8, "nordic": 0.0, "bullwhip": 0.6}
LOOSE = {"demand": -0.6, "supply": -0.9, "policy": 0.0, "price": -0.7, "nordic": 0.0, "bullwhip": 0.4}

ARCHETYPES = [
    {"id": "tight", "name": {"en": "Tight supply", "fi": "Tiukka tarjonta"}, "prior": 0.5,
     "profile": {"demand": 0.2, "supply": 1.0, "policy": 0.0, "price": 0.8, "nordic": 0.0, "bullwhip": 0.6}},
    {"id": "loose", "name": {"en": "Loose supply", "fi": "Löysä tarjonta"}, "prior": 0.5,
     "profile": {"demand": -0.6, "supply": -0.9, "policy": 0.0, "price": -0.7, "nordic": 0.0, "bullwhip": 0.4}},
]


@pytest.fixture()
def dataset():
    return {
        "archetypes": ARCHETYPES, "scaling_k": 1.5,
        "signals": [
            card("H-1", "2021-03-01", TIGHT, short="Lead times long",
                 history=[("2020-12-01", 20), ("2021-03-01", 26), ("2021-09-01", 30)], ce=["HC-1", "HC-2"]),
            card("H-2", "2021-10-15", TIGHT, short="Sales up"),
            card("H-3", "2022-08-01", LOOSE, short="Inventories rise", ce=["HC-3"]),
            card("H-4", "2023-02-01", LOOSE, short="Orders cancelled"),
        ],
        "evidence": [ce("HC-1", "H-1", "2021-04-01"), ce("HC-2", "H-1", "2022-09-01"), ce("HC-3", "H-3", "2022-12-01")],
        "snapshots": ["2021-07-01", "2022-01-01", "2023-01-01", "2023-07-01"],
        "outcomes": [
            {"after": "2021-07-01", "text": {"en": "Shortage deepened", "fi": "Pula syveni"}, "source": {**SRC, "date": "2022-03-01"}},
            {"after": "2023-01-01", "text": {"en": "Inventory glut", "fi": "Varastoähky"}, "source": {**SRC, "date": "2023-09-01"}},
        ],
    }


# ---- as-of rule ------------------------------------------------------------------
def test_only_cards_published_on_or_before_the_date(dataset):
    ids = lambda d: {s["id"] for s in signals_as_of(dataset, d)["signals"]}  # noqa: E731
    assert ids("2021-02-28") == set()
    assert ids("2021-03-01") == {"H-1"}                       # on the date counts
    assert ids("2022-01-01") == {"H-1", "H-2"}
    assert ids(date(2023, 7, 1)) == {"H-1", "H-2", "H-3", "H-4"}


def test_later_evidence_excluded_and_unlinked(dataset):
    k = signals_as_of(dataset, "2021-07-01")
    assert [c["id"] for c in k["evidence"]] == ["HC-1"]       # HC-2 (2022-09) and HC-3 (2022-12) are hindsight
    assert k["signals"][0]["counter_evidence"] == ["HC-1"]
    later = signals_as_of(dataset, "2023-01-01")
    assert {c["id"] for c in later["evidence"]} == {"HC-1", "HC-2", "HC-3"}


def test_history_truncated_to_the_date(dataset):
    k = signals_as_of(dataset, "2021-07-01")
    assert [p["date"] for p in k["signals"][0]["history"]] == ["2020-12-01", "2021-03-01"]
    assert len(signals_as_of(dataset, "2022-01-01")["signals"][0]["history"]) == 3


def test_nothing_in_the_result_postdates_the_snapshot(dataset):
    for d in dataset["snapshots"]:
        k = signals_as_of(dataset, d)
        for s in k["signals"]:
            assert s["observed_at"] <= d and s["source"]["date"] <= d
            assert all(p["date"] <= d for p in s["history"])
        assert all(c["source"]["date"] <= d for c in k["evidence"])


def test_corroboration_and_annotations_are_dated_too(dataset):
    dataset["signals"][0]["corroboration"] = [
        {"name": "Early", "url": "https://a.example.org/x", "reliability": "A", "date": "2021-05-01"},
        {"name": "Late", "url": "https://b.example.org/y", "reliability": "A", "date": "2022-05-01"}]
    dataset["signals"][0]["annotations"] = [{"type": "confirm", "at": "2021-06-01"}, {"type": "dispute", "at": "2022-06-01"}]
    s = signals_as_of(dataset, "2021-07-01")["signals"][0]
    assert [c["name"] for c in s["corroboration"]] == ["Early"]
    assert [a["at"] for a in s["annotations"]] == ["2021-06-01"]


def test_undated_items_are_excluded(dataset):
    dataset["signals"].append({**card("H-X", "2021-01-01", TIGHT), "observed_at": None, "source": {"name": "n", "url": "u"}})
    assert "H-X" not in {s["id"] for s in signals_as_of(dataset, "2023-07-01")["signals"]}


def test_dataset_is_not_mutated(dataset):
    before = copy.deepcopy(dataset)
    snapshot(dataset, "2021-07-01")
    compare(dataset)
    assert dataset == before


def test_bad_date_raises(dataset):
    with pytest.raises(ValueError):
        signals_as_of(dataset, "last spring")


# ---- snapshot --------------------------------------------------------------------
def test_snapshot_shape_and_probabilities(dataset):
    s = snapshot(dataset, "2022-01-01")
    assert s["as_of"] == "2022-01-01" and s["n_signals"] == 2
    assert abs(sum(s["probabilities"].values()) - 1.0) < 0.01
    assert s["leader"]["id"] == max(s["probabilities"], key=s["probabilities"].get)
    assert set(s["leader"]) == {"id", "name", "probability"}
    assert all(set(t) == {"id", "short", "weight"} for t in s["top_weights"])
    assert [t["weight"] for t in s["top_weights"]] == sorted((t["weight"] for t in s["top_weights"]), reverse=True)


def test_early_and_late_snapshots_differ(dataset):
    early, late = snapshot(dataset, "2021-07-01"), snapshot(dataset, "2023-07-01")
    assert early["leader"]["id"] == "tight"
    assert late["leader"]["id"] == "loose"
    assert early["probabilities"] != late["probabilities"]
    assert early["top_weights"] != late["top_weights"]


def test_weights_use_the_snapshot_date_not_today(dataset):
    # Same card, older as-of date: it is fresher then, so its weight is higher than it would be years later.
    only = {**dataset, "signals": dataset["signals"][:1], "evidence": []}
    only["signals"][0]["counter_evidence"] = []
    w_early = snapshot(only, "2021-03-02")["top_weights"][0]["weight"]
    w_late = snapshot(only, "2022-06-01")["top_weights"][0]["weight"]
    assert w_early > w_late


def test_hindsight_counter_evidence_changes_nothing_before_it_existed(dataset):
    base = snapshot(dataset, "2021-07-01")
    dataset["evidence"].append(ce("HC-9", "H-1", "2030-01-01"))
    dataset["signals"][0]["counter_evidence"].append("HC-9")
    assert snapshot(dataset, "2021-07-01") == base


def test_empty_snapshot_before_any_card(dataset):
    s = snapshot(dataset, "2020-01-01")
    assert s["n_signals"] == 0 and s["leader"] is None and s["probabilities"] == {} and s["top_weights"] == []


def test_default_archetypes_load_when_dataset_has_none(dataset):
    del dataset["archetypes"]
    s = snapshot(dataset, "2022-01-01")
    assert s["leader"] is not None and len(s["probabilities"]) == 4


# ---- compare ---------------------------------------------------------------------
def test_compare_rows_labels_and_outcomes(dataset):
    out = compare(dataset)
    assert out["label"]["en"] == "illustrative comparison, not validation and not a forecast"
    assert out["label"]["fi"] and out["label"] == LABEL
    assert [r["as_of"] for r in out["rows"]] == dataset["snapshots"]
    for r in out["rows"]:
        assert {"as_of", "n_signals", "top_weights", "leader", "probabilities", "outcome"} <= set(r)
    first = out["rows"][0]
    assert first["outcome"]["text"]["en"] == "Shortage deepened" and first["outcome"]["source"]["url"]
    assert out["today"] is None
    assert compare(dataset, {"as_of": "2026-10-03"})["today"] == {"as_of": "2026-10-03"}


def test_outcome_is_displayed_but_not_used_in_the_computation(dataset):
    base = compare(dataset)
    for o in dataset["outcomes"]:
        o["text"] = {"en": "changed", "fi": "muutettu"}
    changed = compare(dataset)
    for a, b in zip(base["rows"], changed["rows"]):
        assert {k: v for k, v in a.items() if k != "outcome"} == {k: v for k, v in b.items() if k != "outcome"}


def test_outcome_for_picks_latest_recorded_on_or_before(dataset):
    assert outcome_for(dataset, "2021-06-01") is None
    assert outcome_for(dataset, "2022-01-01")["after"] == "2021-07-01"
    assert outcome_for(dataset, "2023-07-01")["after"] == "2023-01-01"


# ---- labelling checks the real dataset must also pass ------------------------------
def test_validate_accepts_the_fixture_and_flags_problems(dataset):
    assert validate(dataset) == []
    bad = copy.deepcopy(dataset)
    bad["signals"][0]["source"] = {"name": "n"}
    bad["signals"][1]["observed_at"] = "soon"
    bad["evidence"][0]["source"]["date"] = None
    bad["outcomes"][0]["source"] = {}
    problems = validate(bad)
    assert len(problems) == 4
    bad["signals"][0]["data_label"] = "DEMODATA"
    assert len(validate(bad)) == 3


def test_module_label_text_present():
    assert "not validation" in historical.LABEL["en"] and "not a forecast" in historical.LABEL["en"]
