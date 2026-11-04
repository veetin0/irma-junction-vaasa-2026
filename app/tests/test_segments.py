"""Segments (contract C9): POST /api/segment, meta.segments, per-segment data. Run from app/: python -m pytest tests -q

The oil and gas path is tested against a tiny fixture built in a temporary copy of the data folder,
so these tests do not depend on the real oil and gas files (they are built separately).
"""
from __future__ import annotations

import copy
import json
import os
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
REAL_DATA = APP / "backend" / "data"
N_FIXTURE = 6                                      # signals in the fixture


def setup_function():
    client.post("/api/reset")


def _read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=1, ensure_ascii=False), encoding="utf-8")


def _build_oilgas(data: Path) -> None:
    """A tiny oil and gas segment: data-centre cards and archetypes relabelled under oil and gas ids."""
    sigs = _read(REAL_DATA / "worlds" / "1" / "signals.json")[:N_FIXTURE]
    ev = _read(REAL_DATA / "worlds" / "1" / "evidence.json")
    sig_map = {s["id"]: s["id"].replace("SIG-", "OG-") for s in sigs}
    ce_map: dict[str, str] = {}
    og_sigs = []
    for s in sigs:
        c = copy.deepcopy(s)
        c.update(id=sig_map[s["id"]], market="oilgas", segment="oilgas", name="Oil and gas fixture: " + s["name"],
                 counter_evidence=[ce_map.setdefault(x, x.replace("CE-", "OG-CE-")) for x in s.get("counter_evidence", [])])
        og_sigs.append(c)
    og_ev = []
    for e in ev:
        if e["id"] in ce_map and e["against"] in sig_map:
            og_ev.append({**copy.deepcopy(e), "id": ce_map[e["id"]], "against": sig_map[e["against"]]})
    arch = _read(REAL_DATA / "scenario_archetypes.json")
    keep = arch["archetypes"][:6]
    total = sum(a["prior"] for a in keep)
    ids = {a["id"]: "og_" + a["id"] for a in keep}
    og_arch = []
    for a in keep:
        b = copy.deepcopy(a)
        b.update(id=ids[a["id"]], prior=a["prior"] / total, name={"en": "OG " + a["name"]["en"], "fi": "OG " + a["name"]["fi"]})
        b["signposts"] = [{**p, "signal_id": sig_map[p["signal_id"]]} for p in a.get("signposts", []) if p["signal_id"] in sig_map]
        og_arch.append(b)
    reco = copy.deepcopy(_read(REAL_DATA / "recommendations.json"))
    reco["archetypes"] = {ids[k]: v for k, v in reco["archetypes"].items() if k in ids}
    out = data / "segments" / "oilgas"
    _write(out / "signals.json", og_sigs)
    _write(out / "evidence.json", og_ev)
    _write(out / "scenario_archetypes.json", {**arch, "archetypes": og_arch})
    _write(out / "recommendations.json", reco)


@pytest.fixture
def data_with_oilgas(tmp_path, monkeypatch):
    data = tmp_path / "data"
    shutil.copytree(REAL_DATA, data, ignore=shutil.ignore_patterns("segments"))
    _build_oilgas(data)
    monkeypatch.setattr(main, "DATA", data)
    yield data
    monkeypatch.undo()
    client.post("/api/reset")


@pytest.fixture
def data_without_oilgas(tmp_path, monkeypatch):
    data = tmp_path / "data"
    shutil.copytree(REAL_DATA, data, ignore=shutil.ignore_patterns("segments"))
    monkeypatch.setattr(main, "DATA", data)
    yield data
    monkeypatch.undo()
    client.post("/api/reset")


# ---- meta and the endpoint ------------------------------------------------------------------------
def test_default_segment_and_meta_lists_exactly_datacenter_and_oilgas():
    m = client.get("/api/state").json()["meta"]
    assert m["segment"] == "datacenter" and m["scenario_segment_required"] is False
    assert [x["id"] for x in m["segments"]] == ["datacenter", "oilgas"]
    for x in m["segments"]:
        assert x["label"]["en"] and x["label"]["fi"] and isinstance(x["has_data"], bool)
    assert m["segments"][0]["has_data"] is True
    real = all((REAL_DATA / "segments" / "oilgas" / f).is_file() for f in main.SEGMENT_FILES["oilgas"])
    assert m["segments"][1]["has_data"] is real


def test_post_segment_datacenter_and_all_work_and_unknown_is_400():
    r = client.post("/api/segment", json={"segment": "datacenter"})
    assert r.status_code == 200 and r.json()["segment"] == "datacenter" and r.json()["state"]["meta"]["segment"] == "datacenter"
    r = client.post("/api/segment", json={"segment": "all"})
    assert r.status_code == 200 and r.json()["segment"] == "all"
    assert r.json()["state"]["meta"]["scenario_segment_required"] is True
    assert client.get("/api/state").json()["meta"]["segment"] == "all"
    for bad in ("nope", "", "Datacenter", "energy"):
        assert client.post("/api/segment", json={"segment": bad}).status_code == 400
    assert client.post("/api/segment", json={}).status_code == 422
    assert client.get("/api/state").json()["meta"]["segment"] == "all"        # a rejected request changes nothing


def test_reset_and_world_switch_return_to_the_default_segment():
    client.post("/api/segment", json={"segment": "all"})
    client.post("/api/reset")
    assert client.get("/api/state").json()["meta"]["segment"] == "datacenter"
    client.post("/api/segment", json={"segment": "all"})
    assert client.post("/api/world", json={"world": 2}).json()["state"]["meta"]["segment"] == "datacenter"
    client.post("/api/world", json={"world": 1})


def test_only_datacenter_segment_in_world_two():
    client.post("/api/world", json={"world": 2})
    assert client.post("/api/segment", json={"segment": "all"}).status_code == 400
    assert client.post("/api/segment", json={"segment": "oilgas"}).status_code == 400
    assert client.post("/api/segment", json={"segment": "datacenter"}).status_code == 200
    client.post("/api/world", json={"world": 1})


def test_datacenter_signals_are_marked_datacenter_and_unchanged_in_number():
    st = client.get("/api/state").json()
    shipped = _read(REAL_DATA / "worlds" / "1" / "signals.json")
    assert {s["market"] for s in st["signals"]} == {"datacenter"}
    assert {s["id"] for s in shipped} <= {s["id"] for s in st["signals"]}
    assert len(st["scenarios"]["scenarios"]) == 4


# ---- no oil and gas files ------------------------------------------------------------------------------
def test_oilgas_without_files_has_no_data_and_is_rejected(data_without_oilgas):
    client.post("/api/reset")
    st = client.get("/api/state").json()
    assert next(x for x in st["meta"]["segments"] if x["id"] == "oilgas")["has_data"] is False
    assert [x["id"] for x in st["meta"]["segments"]] == ["datacenter", "oilgas"]
    r = client.post("/api/segment", json={"segment": "oilgas"})
    assert r.status_code == 400
    assert client.get("/api/state").json()["meta"]["segment"] == "datacenter"


def test_a_partial_oilgas_folder_is_still_no_data(data_without_oilgas):
    _write(data_without_oilgas / "segments" / "oilgas" / "signals.json", [])
    client.post("/api/reset")
    assert client.get("/api/state").json()["meta"]["segments"][1]["has_data"] is False
    assert client.post("/api/segment", json={"segment": "oilgas"}).status_code == 400


def test_all_without_oilgas_files_shows_datacenter_signals(data_without_oilgas):
    client.post("/api/reset")
    dc = client.get("/api/state").json()
    st = client.post("/api/segment", json={"segment": "all"}).json()["state"]
    assert [s["id"] for s in st["signals"]] == [s["id"] for s in dc["signals"]]


# ---- the oil and gas path against the fixture ------------------------------------------------------------------
def test_oilgas_segment_uses_its_own_signals_scenarios_and_recommendation(data_with_oilgas):
    client.post("/api/reset")
    assert next(x for x in client.get("/api/state").json()["meta"]["segments"] if x["id"] == "oilgas")["has_data"] is True
    r = client.post("/api/segment", json={"segment": "oilgas"})
    assert r.status_code == 200
    st = r.json()["state"]
    assert st["meta"]["segment"] == "oilgas" and st["meta"]["scenario_segment_required"] is False
    ids = [s["id"] for s in st["signals"]]
    assert len(ids) == N_FIXTURE and all(i.startswith("OG-") for i in ids)
    assert {s["market"] for s in st["signals"]} == {"oilgas"}
    scen = st["scenarios"]["scenarios"]
    assert len(scen) == 4 and all(s["id"].startswith("og_") for s in scen)
    assert abs(sum(s["probability"] for s in scen) - 1) < 1e-3
    assert all(x["id"].startswith("og_") for v in st["scenarios_by_horizon"].values() for x in v["scenarios"])
    rec = st["recommendation"]
    assert rec["scenario_id"] == scen[0]["id"] and rec["scenario_id"].startswith("og_")
    assert all(set(m["trigger_signals"]) <= set(ids) for m in rec["moves"])
    assert {e["against"] for e in st["evidence"]} <= set(ids) and all(e["id"].startswith("OG-CE-") for e in st["evidence"])
    for s in st["signals"]:                                        # weights, horizons and impact work on the segment's cards
        assert 0 <= s["computed"]["weight"] <= 1 and set(s["computed"]["horizon"]) == {"12", "24", "36"}
        assert -100 <= s["impact"]["impact"] <= 100
    assert st["history"]["points"][-1]["leading"] == scen[0]["id"]
    assert all(set(p["probs"]) == {s["id"] for s in scen} for p in st["history"]["points"][-3:])


def test_oilgas_endpoints_keep_working(data_with_oilgas):
    client.post("/api/reset")
    client.post("/api/segment", json={"segment": "oilgas"})
    assert client.get("/api/signals/OG-001").json()["market"] == "oilgas"
    assert client.get("/api/signals/SIG-001").status_code == 404
    a = client.post("/api/ask", json={"question": "What should ABB do next", "lang": "en"})
    assert a.status_code == 200 and a.json()["answer"]
    assert client.get("/api/method").status_code == 200
    run = client.post("/api/run", json={"title": "Test item", "text": "A pipeline operator confirmed a new compressor station order.", "date": "2026-10-02",
                                        "source_name": "Test", "data_label": "DEMODATA"})
    assert run.status_code == 200
    new = [s for s in run.json()["state"]["signals"] if s["id"].startswith("SIG-")]
    assert new and new[0]["market"] == "oilgas"


def test_scout_is_datacenter_only(data_with_oilgas):
    client.post("/api/reset")
    assert client.get("/api/scout").json()["eligible"] is False                   # no API key in tests either way
    client.post("/api/segment", json={"segment": "oilgas"})
    sc = client.get("/api/scout").json()
    assert sc["eligible"] is False and sc["skip"]["en"] and sc["skip"]["fi"]
    assert main.STORE.scout_eligibility() == (False, "segment")
    assert client.post("/api/scout/run").json()["status"] == "skipped:segment"


def test_all_is_the_union_with_datacenter_scenarios_as_fallback(data_with_oilgas):
    client.post("/api/reset")
    dc = client.get("/api/state").json()
    st = client.post("/api/segment", json={"segment": "all"}).json()["state"]
    ids = {s["id"] for s in st["signals"]}
    assert {s["id"] for s in dc["signals"]} <= ids and {f"OG-00{i}" for i in range(1, N_FIXTURE + 1)} <= ids
    assert {s["market"] for s in st["signals"]} == {"datacenter", "oilgas"}
    assert st["meta"]["scenario_segment_required"] is True
    assert [s["id"] for s in st["scenarios"]["scenarios"]] == [s["id"] for s in dc["scenarios"]["scenarios"]]
    assert [s["probability"] for s in st["scenarios"]["scenarios"]] == [s["probability"] for s in dc["scenarios"]["scenarios"]]
    assert st["recommendation"]["scenario_id"] == dc["recommendation"]["scenario_id"]
    assert not any(i.startswith("og_") for i in {s["id"] for s in st["scenarios"]["scenarios"]})
    for s in st["signals"]:
        assert -100 <= s["impact"]["impact"] <= 100


def test_annotations_survive_a_segment_switch(data_with_oilgas):
    client.post("/api/reset")
    assert client.post("/api/signals/SIG-001/annotate", json={"action": "confirm", "note": "seen in the field", "author": "planner"}).status_code == 200
    before = client.get("/api/signals/SIG-001").json()["computed"]["weight"]
    client.post("/api/segment", json={"segment": "oilgas"})
    client.post("/api/segment", json={"segment": "all"})
    sig = client.get("/api/signals/SIG-001").json()
    assert [a["action"] for a in sig["annotations"]] == ["confirm"] and sig["computed"]["weight"] == before
    client.post("/api/reset")
    assert client.get("/api/signals/SIG-001").json()["annotations"] == []


# ---- Vercel mode ---------------------------------------------------------------------------------------------------
def test_vercel_mode_serves_segments(tmp_path):
    code = (
        "import sys, json\n"
        f"sys.path.insert(0, {str(APP / 'backend')!r})\n"
        "from fastapi.testclient import TestClient\n"
        "import main\n"
        "c = TestClient(main.app)\n"
        "assert c.get('/api/state').json()['meta']['segment'] == 'datacenter'\n"
        "assert c.post('/api/segment', json={'segment': 'all'}).status_code == 200\n"
        "assert c.post('/api/segment', json={'segment': 'nope'}).status_code == 400\n"
        "print(json.dumps(c.get('/api/state').json()['meta']['segments']))\n"
    )
    env = {**os.environ, "VERCEL": "1", "IRMA_RUNTIME_DIR": str(tmp_path / "rt"), "ANTHROPIC_API_KEY": "", "AGENT_MODE": "replay"}
    out = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True, timeout=120)
    assert out.returncode == 0, out.stderr[-800:]
    assert [x["id"] for x in json.loads(out.stdout.strip().splitlines()[-1])] == ["datacenter", "oilgas"]
