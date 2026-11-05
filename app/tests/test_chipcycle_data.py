"""Historical chip-cycle dataset (contract C11, M4.3a): schema, sources, dates, as-of rule.

Pure data checks, no server. Run from app/: python -m pytest tests -q
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[1]
WORLD1 = APP / "backend" / "data" / "worlds" / "1" / "signals.json"
FILE = APP / "backend" / "data" / "historical" / "chipcycle.json"

DOC = json.loads(FILE.read_text(encoding="utf-8"))
CARDS = DOC["cards"]
EVIDENCE = DOC["evidence"]
OUTCOMES = DOC["outcomes"]
SNAPSHOTS = DOC["snapshots"]
INDEX = DOC["snapshot_index"]
BY_ID = {c["id"]: c for c in CARDS}

AXES = {"demand", "supply", "policy", "price", "nordic", "bullwhip"}
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
LABELS = {"SOURCE", "DEMODATA", "ASSUMPTION"}
WINDOW = ("2021-01-01", "2023-12-31")     # cards must belong to the 2021-2023 cycle


def world1_keys() -> set[str]:
    cards = json.loads(WORLD1.read_text(encoding="utf-8"))
    keys: set[str] = set()
    for c in cards:
        keys |= set(c)
    return keys


def test_card_count_and_ids():
    assert 12 <= len(CARDS) <= 18
    ids = [c["id"] for c in CARDS]
    assert len(ids) == len(set(ids))
    assert all(re.fullmatch(r"HS-\d{3}", i) for i in ids)
    assert ids == sorted(ids)


def test_schema_matches_world_one_cards():
    required = world1_keys()
    for c in CARDS:
        missing = required - set(c)
        assert not missing, (c["id"], missing)


def test_six_axes_in_range():
    for c in CARDS:
        assert set(c["axes"]) == AXES, c["id"]
        for k, v in c["axes"].items():
            assert -1.0 <= v <= 1.0, (c["id"], k)
        assert any(v != 0 for v in c["axes"].values()), c["id"]


def test_field_vocabulary():
    for c in CARDS:
        assert c["category"] in {"demand", "supply", "policy", "price", "bullwhip"}, c["id"]
        assert c["measures"] in {"end_demand", "intermediary", "supply_tightness", "policy", "price"}, c["id"]
        assert c["type"] in {"leading", "coincident", "lagging"}, c["id"]
        assert c["classification"] in {"structural", "cyclical", "mixed"}, c["id"]
        assert c["reliability"] in {"A", "B", "C"}, c["id"]
        assert c["direction"] in (-1, 0, 1), c["id"]
        assert 0.0 <= c["strength"] <= 1.0, c["id"]
        assert c["segment"] in {"datacenter", "components", "materials", "utility"}, c["id"]
        assert c["lead_months"] > 0 and c["lead_months_rationale"].startswith("[ASSUMPTION"), c["id"]
        assert c["short"] and c["short_fi"] and c["name"] and c["excerpt"], c["id"]
        assert c["excerpt_kind"] in {"quote", "paraphrase"}, c["id"]


def test_every_number_has_a_label_and_a_source_url():
    for c in CARDS:
        assert c["data_label"] in LABELS, c["id"]
        if c["data_label"] == "SOURCE":
            assert c["source"]["url"].startswith("https://"), c["id"]
            assert c["source"]["name"] and DATE.match(c["source"]["date"]), c["id"]
        assert isinstance(c["value"]["number"], (int, float)), c["id"]
        assert c["value"]["unit"] and c["value"]["label"], c["id"]
        assert c["history_label"] in LABELS | {"NONE"}, c["id"]
        if c["history"]:
            assert c["history_label"] in LABELS, c["id"]
            assert c["history_note"], c["id"]
        else:
            assert c["history_label"] == "NONE", c["id"]


def test_observed_at_is_the_source_date_and_inside_the_cycle():
    for c in CARDS:
        assert DATE.match(c["observed_at"]), c["id"]
        assert c["observed_at"] == c["source"]["date"], c["id"]
        assert WINDOW[0] <= c["observed_at"] <= WINDOW[1], c["id"]


def test_history_points_are_dated_and_not_later_than_the_card():
    for c in CARDS:
        dates = [p["date"] for p in c["history"]]
        assert dates == sorted(dates), c["id"]
        for p in c["history"]:
            assert DATE.match(p["date"]) and isinstance(p["value"], (int, float)), c["id"]
            assert p["date"] <= c["observed_at"], (c["id"], "history point after the card was published")


def test_snapshots_are_the_contract_range():
    assert 5 <= len(SNAPSHOTS) <= 6
    assert SNAPSHOTS == sorted(SNAPSHOTS)
    assert SNAPSHOTS[0] == "2021-07-01" and SNAPSHOTS[-1] == "2023-07-01"
    assert all(DATE.match(d) for d in SNAPSHOTS)
    assert [s["as_of"] for s in INDEX] == SNAPSHOTS


def test_no_card_in_a_snapshot_is_dated_after_the_snapshot():
    for s in INDEX:
        for cid in s["card_ids"]:
            assert cid in BY_ID, (s["as_of"], cid)
            assert BY_ID[cid]["observed_at"] <= s["as_of"], (s["as_of"], cid, "hindsight")


def test_snapshot_lists_are_exactly_the_cards_known_at_the_date():
    for s in INDEX:
        known = sorted(c["id"] for c in CARDS if c["observed_at"] <= s["as_of"])
        assert sorted(s["card_ids"]) == known, s["as_of"]


def test_snapshots_grow_and_each_one_adds_a_card_inside_its_window():
    prev: set[str] = set()
    prev_date = "0000-00-00"
    for s in INDEX:
        now = set(s["card_ids"])
        assert prev < now, (s["as_of"], "must add cards")
        for cid in now - prev:
            assert prev_date < BY_ID[cid]["observed_at"] <= s["as_of"], (s["as_of"], cid)
        prev, prev_date = now, s["as_of"]
    assert prev == set(BY_ID), "the last snapshot covers every card"
    assert len(INDEX[0]["card_ids"]) >= 3
    for s in INDEX:
        assert s["note"]["en"] and s["note"]["fi"]


def test_snapshots_differ_enough_to_show_the_cycle():
    """Early snapshots are supply-tight, later ones carry falling-price and falling-demand cards."""
    first = [BY_ID[i] for i in INDEX[0]["card_ids"]]
    last = [BY_ID[i] for i in INDEX[-1]["card_ids"]]
    assert sum(c["direction"] for c in first) > 0
    assert any(c["direction"] < 0 for c in last)
    assert sum(1 for c in last if c["axes"]["price"] < 0) >= 2


def test_evidence_schema_and_dates():
    ids = [e["id"] for e in EVIDENCE]
    assert len(ids) == len(set(ids))
    for e in EVIDENCE:
        assert e["against"] in BY_ID, e["id"]
        assert e["claim"] and e["data_label"] in LABELS and e["reliability"] in {"A", "B", "C"}, e["id"]
        assert 0.0 <= e["strength"] <= 1.0, e["id"]
        assert e["source"]["url"].startswith("https://") and DATE.match(e["source"]["date"]), e["id"]
        assert e["observed_at"] == e["source"]["date"], e["id"]


def test_card_counter_evidence_ids_resolve_and_point_back():
    by_ev = {e["id"]: e for e in EVIDENCE}
    for c in CARDS:
        for eid in c["counter_evidence"]:
            assert eid in by_ev, (c["id"], eid)
            assert by_ev[eid]["against"] == c["id"], (c["id"], eid)
    for e in EVIDENCE:
        assert e["id"] in BY_ID[e["against"]]["counter_evidence"], e["id"]
    # balanced: most cards carry counter-evidence, and the ones searched say so
    assert sum(1 for c in CARDS if c["counter_evidence"]) >= len(CARDS) // 2
    for c in CARDS:
        if c["counter_evidence"]:
            assert c["ce_searched"] is True, c["id"]


def test_snapshot_evidence_lists_have_no_hindsight():
    by_ev = {e["id"]: e for e in EVIDENCE}
    for s in INDEX:
        for eid in s["evidence_ids"]:
            assert by_ev[eid]["observed_at"] <= s["as_of"], (s["as_of"], eid)
            assert by_ev[eid]["against"] in s["card_ids"], (s["as_of"], eid)
        expect = sorted(e["id"] for e in EVIDENCE if e["observed_at"] <= s["as_of"] and e["against"] in s["card_ids"])
        assert sorted(s["evidence_ids"]) == expect, s["as_of"]


def test_outcomes_have_text_and_source_after_their_snapshot():
    assert len(OUTCOMES) == len(SNAPSHOTS)
    assert [o["after"] for o in OUTCOMES] == SNAPSHOTS
    for o in OUTCOMES:
        assert o["text"]["en"] and o["text"]["fi"], o["after"]
        src = o["source"]
        assert src["name"] and src["url"].startswith("https://") and DATE.match(src["date"]), o["after"]
        assert src["date"] > o["after"], (o["after"], "the outcome must come after the snapshot")


def test_each_outcome_is_not_already_on_a_card_of_its_own_snapshot():
    """What happened next must not be derivable from the cards the snapshot already holds."""
    for o in OUTCOMES:
        known_urls = {BY_ID[i]["source"]["url"] for s in INDEX if s["as_of"] == o["after"] for i in s["card_ids"]}
        assert o["source"]["url"] not in known_urls, o["after"]


def test_label_text_present():
    meta = DOC["meta"]
    assert meta["label"]["en"] == "Illustrative comparison, not validation and not a forecast."
    assert meta["label"]["fi"]
    assert meta["reference_date"] == SNAPSHOTS[-1]
    assert "ASSUMPTION" in meta["reference_date_label"]


def test_no_unsourced_numbers_and_no_demodata_slipped_in():
    for c in CARDS:
        assert c["data_label"] == "SOURCE", c["id"]
        assert "DEMODATA" not in json.dumps(c), c["id"]


@pytest.mark.parametrize("bad", ["we recommend", "you should buy", "order now"])
def test_no_recommendation_language(bad):
    text = json.dumps(DOC, ensure_ascii=False).lower()
    assert bad not in text
