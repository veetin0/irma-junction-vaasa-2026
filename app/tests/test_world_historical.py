"""M4.4: world 2 is the historical dataset, as known on its reference date; /api/historical compares the snapshots."""
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def _back_to_world_one():
    client.post("/api/world", json={"world": 1})


def test_world_two_is_historical_and_pinned_to_its_date():
    try:
        st = client.post("/api/world", json={"world": 2}).json()["state"]
        labels = {w["id"]: w["label"] for w in st["meta"]["worlds"]}
        assert labels[2] == {"en": "Historical data", "fi": "Vanha data"}
        assert st["meta"]["today"] == "2023-07-01"
        assert st["signals"] and all(s["id"].startswith("HS-") for s in st["signals"])
        assert all(s["observed_at"] <= "2023-07-01" for s in st["signals"])   # no hindsight
    finally:
        _back_to_world_one()
    assert client.get("/api/state").json()["meta"]["today"] != "2023-07-01"


def test_segments_other_than_datacenter_are_refused_in_world_two():
    try:
        client.post("/api/world", json={"world": 2})
        assert client.post("/api/segment", json={"segment": "oilgas"}).status_code == 400
        assert client.post("/api/segment", json={"segment": "all"}).status_code == 400
        assert client.post("/api/segment", json={"segment": "datacenter"}).status_code == 200
    finally:
        _back_to_world_one()


def test_api_historical_rows_label_and_outcomes():
    r = client.get("/api/historical").json()
    assert r["label"]["en"] == "illustrative comparison, not validation and not a forecast"
    assert len(r["rows"]) == 5 and r["reference_date"] == "2023-07-01"
    assert [x["as_of"] for x in r["rows"]] == sorted(x["as_of"] for x in r["rows"])
    assert all(x["leader"] and x["top_weights"] and x["outcome"] for x in r["rows"])
    assert r["today"] and r["today"]["leader"]["id"] and r["today"]["top_weights"]


def test_oilgas_segment_has_its_own_pool():
    try:
        st = client.post("/api/segment", json={"segment": "oilgas"}).json()["state"]
        assert st["meta"]["segment"] == "oilgas"
        assert st["recommendation"]["scenario_id"].startswith("og_")
        assert all(s["id"].startswith("OG-") for s in st["signals"])
    finally:
        client.post("/api/segment", json={"segment": "datacenter"})
