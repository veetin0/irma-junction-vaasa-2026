"""M6 contract checks (C14) at the level the interface sees them: the state and endpoint payloads.

Engine-level rules are tested elsewhere (test_impact, test_weights, test_historical, test_oilgas_cards). This file adds:
  - interface text: the node parity check (same keys in en and fi, no internal terms) and plain wording in the data text
  - impact range and sign in every segment (including oil and gas), as the map reads them
  - horizon re-weighting: the dots move when the horizon changes, in every segment
  - oil and gas labels as the interface receives them
  - the historical as-of rule as /api/historical reports it
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

os.environ.setdefault("DEMO_TODAY", "2026-10-03")
os.environ["AGENT_MODE"] = "replay"
APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP / "backend"))

from fastapi.testclient import TestClient  # noqa: E402

import main  # noqa: E402

client = TestClient(main.app)
DATA = APP / "backend" / "data"
LABELS = {"SOURCE", "DEMODATA", "ASSUMPTION"}


@pytest.fixture(autouse=True)
def _default_world_and_segment():
    client.post("/api/reset")
    yield
    client.post("/api/reset")


def _state(segment: str) -> dict:
    r = client.post("/api/segment", json={"segment": segment})
    assert r.status_code == 200, r.text
    return r.json()["state"]


# ---- interface text -----------------------------------------------------------------------------------------------
def test_i18n_parity_and_wording_check_passes_under_node():
    out = subprocess.run(["node", str(APP / "tests" / "i18n_parity.js")], capture_output=True, text=True, timeout=60)
    assert out.returncode == 0, out.stderr[-800:]
    assert "same keys in en and fi" in out.stdout


def test_i18n_check_fails_when_a_key_or_a_term_is_wrong(tmp_path):
    """The check must be able to fail: remove a Finnish key, then put an internal term into the English text."""
    work = tmp_path / "app"
    (work / "tests").mkdir(parents=True)
    shutil.copytree(APP / "frontend", work / "frontend")
    shutil.copy(APP / "tests" / "i18n_parity.js", work / "tests" / "i18n_parity.js")
    js = work / "frontend" / "app.js"
    src = js.read_text(encoding="utf-8")
    broken_key = src.replace('settings: "Asetukset", ', "", 1)
    assert broken_key != src
    js.write_text(broken_key, encoding="utf-8")
    out = subprocess.run(["node", str(work / "tests" / "i18n_parity.js")], capture_output=True, text=True, timeout=60)
    assert out.returncode == 1 and 'key "settings" is missing in fi' in out.stderr
    broken_term = src.replace('noRegret: "Do in any case"', 'noRegret: "A no-regret move"', 1)
    assert broken_term != src
    js.write_text(broken_term, encoding="utf-8")
    out = subprocess.run(["node", str(work / "tests" / "i18n_parity.js")], capture_output=True, text=True, timeout=60)
    assert out.returncode == 1 and "internal term" in out.stderr


INTERNAL_EN = re.compile(r"no[-_ ]regret|\bhedge\b|\bkernel\b|\bcontingent\b", re.I)
WRONG_FI = re.compile(r"vastanäyt|\bpaino\b|\bpainon\b|laukaisij|kakkonen|\bdata\b", re.I)


def _texts(node):
    if isinstance(node, dict):
        if isinstance(node.get("en"), str) and isinstance(node.get("fi"), str):
            yield node["en"], node["fi"]
        else:
            for v in node.values():
                yield from _texts(v)
    elif isinstance(node, list):
        for v in node:
            yield from _texts(v)


@pytest.mark.parametrize("path", ["scenario_archetypes.json", "segments/oilgas/scenario_archetypes.json"])
def test_scenario_names_and_narratives_use_plain_terms(path):
    pairs = list(_texts(json.loads((DATA / path).read_text(encoding="utf-8"))["archetypes"]))
    assert len(pairs) > 40
    for en, fi in pairs:
        assert not INTERNAL_EN.search(en), en
        assert not WRONG_FI.search(fi), fi
        assert en.strip() and fi.strip()


def test_suggested_prompts_name_no_segment_and_both_languages_match():
    sp = main.SUGGESTED_PROMPTS
    assert set(sp) == {"en", "fi"} and len(sp["en"]) == len(sp["fi"]) == 3
    for q in sp["en"] + sp["fi"]:
        assert not re.search(r"data[- ]?cent|datakesk|oil|gas|öljy|kaasu", q, re.I), q


def test_suggested_prompts_get_a_composed_answer_in_every_segment():
    for segment in ("datacenter", "oilgas"):
        _state(segment)
        for lang in ("en", "fi"):
            for q in main.SUGGESTED_PROMPTS[lang]:
                a = client.post("/api/ask", json={"question": q, "lang": lang}).json()
                assert a["mode"] == "composed" and a["citations"] and a["guardrail_removed"] == 0, (segment, q)
                ids = {c["signal_id"] for c in a["citations"]}
                prefix = "OG-" if segment == "oilgas" else "SIG-"
                assert all(i.startswith(prefix) for i in ids), (segment, q, ids)


# ---- impact range and sign, as the map reads it -----------------------------------------------------------------------
@pytest.mark.parametrize("segment", ["datacenter", "oilgas", "all"])
def test_impact_is_in_range_signed_and_labelled_in_every_segment(segment):
    st = _state(segment)
    assert st["signals"]
    for s in st["signals"]:
        i = s["impact"]
        assert isinstance(i["impact"], int) and -100 <= i["impact"] <= 100, s["id"]
        assert i["label"] == "ASSUMPTION" and i["parts"]["sign"] in (-1, 0, 1), s["id"]
        if i["impact"] != 0:
            assert (i["impact"] > 0) == (i["parts"]["sign"] > 0), s["id"]       # the sign of the number is the rule's sign
        assert abs(i["impact"]) <= 100 * i["parts"]["materiality"] * i["parts"]["theme_load"] + 0.5 + 1e-9
    assert any(s["impact"]["impact"] > 0 for s in st["signals"]) and any(s["impact"]["impact"] < 0 for s in st["signals"])
    assert st["meta"]["impact"]["label"] == "ASSUMPTION" and st["meta"]["impact"]["a_ref"] > 0


def test_oil_and_gas_impact_follows_direction_and_measure():
    cards = {s["id"]: s for s in _state("oilgas")["signals"]}
    polarity = main.impact_meta()["polarity"]
    for cid, s in cards.items():
        if not s.get("direction"):
            assert s["impact"]["impact"] == 0, cid
        else:
            assert s["impact"]["parts"]["sign"] == s["direction"] * polarity.get(s.get("measures"), 1), cid


# ---- horizon re-weighting ---------------------------------------------------------------------------------------------
@pytest.mark.parametrize("segment", ["datacenter", "oilgas", "all"])
def test_changing_the_horizon_moves_the_dots(segment):
    st = _state(segment)
    moved = 0
    for s in st["signals"]:
        c = s["computed"]
        h = c["horizon"]
        assert set(h) == {"12", "24", "36"}
        assert all(0 <= v <= c["weight"] + 1e-9 for v in h.values()), s["id"]
        assert abs(h["36"] * 100 - c["weight"] * 100 * c["horizon_fit"]["36"]) < 0.05
        if len({round(v, 4) for v in h.values()}) > 1:
            moved += 1
    assert moved >= len(st["signals"]) // 2          # most dots change place with the horizon (structural cards hold, cyclical ones fade)
    assert set(st["scenarios_by_horizon"]) == {"12", "24", "36"}


@pytest.mark.parametrize("segment", ["datacenter", "oilgas"])
def test_the_leading_situation_depends_on_the_horizon_and_each_is_normalised(segment):
    st = _state(segment)
    leaders = set()
    for h, block in st["scenarios_by_horizon"].items():
        probs = [x["probability"] for x in block["scenarios"]]
        assert abs(sum(probs) - 1) < 1e-3, h
        leaders.add(block["scenarios"][0]["id"])
    assert len(leaders) >= 2          # the horizon changes the reading, which is what the note on the map says


# ---- oil and gas labels as the interface receives them -------------------------------------------------------------------
def test_oil_and_gas_cards_carry_labels_and_sources_in_the_state():
    st = _state("oilgas")
    assert 8 <= len(st["signals"]) <= 12
    for s in st["signals"]:
        assert s["market"] == "oilgas" and s["id"].startswith("OG-")
        assert s["data_label"] in LABELS and s["history_label"] in LABELS | {"NONE"}, s["id"]
        if s["data_label"] == "SOURCE":
            assert s["source"]["url"].startswith("https://") and re.match(r"\d{4}-\d{2}-\d{2}$", s["source"]["date"] or ""), s["id"]
        assert s["reliability"] in {"A", "B", "C"} and s["update_frequency"] and s["region"]
        assert s["counter_evidence"], s["id"]
    assert st["meta"]["segment"] == "oilgas" and st["meta"]["scenario_segment_required"] is False
    assert all(x["id"].startswith("og_") for x in st["scenarios"]["scenarios"])


def test_oil_and_gas_text_names_no_data_centre_topics():
    st = _state("oilgas")
    blob = json.dumps([st["scenarios"], st["recommendation"], st["brief"]["text"]], ensure_ascii=False)
    assert not re.search(r"data[- ]?cent|datakesk|hyperscal|Fingrid", blob, re.I)


def test_all_segments_state_keeps_each_card_in_its_own_market():
    st = _state("all")
    markets = {s["market"] for s in st["signals"]}
    assert markets == {"datacenter", "oilgas"} and st["meta"]["scenario_segment_required"] is True
    assert all((s["id"].startswith("OG-")) == (s["market"] == "oilgas") for s in st["signals"])


# ---- the historical as-of rule, as /api/historical reports it ---------------------------------------------------------------
def test_historical_rows_use_only_what_was_published_by_each_date():
    hist = json.loads((DATA / "historical" / "chipcycle.json").read_text(encoding="utf-8"))
    published = {c["id"]: c["observed_at"] for c in hist["cards"]}
    out = client.get("/api/historical").json()
    assert out["label"]["en"] == "illustrative comparison, not validation and not a forecast"
    assert [r["as_of"] for r in out["rows"]] == hist["snapshots"]
    previous_n = 0
    for row in out["rows"]:
        known = [i for i, d in published.items() if d <= row["as_of"]]
        assert row["n_signals"] == len(known), row["as_of"]
        assert row["n_signals"] >= previous_n                       # knowledge only grows with the date
        previous_n = row["n_signals"]
        assert row["top_weights"] and all(published[t["id"]] <= row["as_of"] for t in row["top_weights"]), row["as_of"]
        assert abs(sum(row["probabilities"].values()) - 1) < 1e-3
        assert row["outcome"]["source"]["url"].startswith("http")
    assert len({r["leader"]["id"] for r in out["rows"]} | {tuple(t["id"] for t in r["top_weights"]) for r in out["rows"]}) > 1


def test_historical_today_column_only_for_the_data_centre_comparison():
    assert client.get("/api/historical").json()["today"]["leader"]["id"]
    _state("all")
    assert client.get("/api/historical").json()["today"]
    _state("oilgas")
    assert client.get("/api/historical").json()["today"] is None


def test_world_two_state_is_as_of_its_reference_date():
    st = client.post("/api/world", json={"world": 2}).json()["state"]
    ref = st["meta"]["today"]
    assert ref == "2023-07-01" and all(s["observed_at"] <= ref for s in st["signals"])
    assert all(s["impact"]["impact"] in range(-100, 101) for s in st["signals"])
