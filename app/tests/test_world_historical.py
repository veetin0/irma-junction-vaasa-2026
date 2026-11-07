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


def test_oilgas_next_step_names_no_data_centre_topics():
    try:
        st = client.post("/api/segment", json={"segment": "oilgas"}).json()["state"]
        ns = str(st["brief"]["next_step"])
        for word in ("TrendForce", "Fingrid", "data centres", "SIG-017", "DRAM"):
            assert word not in ns, word
        ask = client.post("/api/ask", json={"question": "Tell about the situation of components in our products", "lang": "en"}).json()
        assert "SIG-017" not in str(ask)
    finally:
        client.post("/api/segment", json={"segment": "datacenter"})


def test_historical_brief_support_lists_only_positive_contributions():
    """Support and 'evidence against' must not list the same card (ABB first-look finding 5)."""
    import re
    from fastapi.testclient import TestClient
    from backend.main import app
    c = TestClient(app)
    c.post("/api/world", json={"world": 2})
    text = c.get("/api/state").json()["brief"]["text"]
    sup = re.search(r"Strongest support[^:]*: (.*?)\. (?:Evidence against|The planner)", text)
    ag = re.search(r"Evidence against it: (.*?)\. The planner", text)
    if sup and ag:
        assert not set(re.findall(r"HS-\d+", sup.group(1))) & set(re.findall(r"HS-\d+", ag.group(1)))
    c.post("/api/world", json={"world": 1})


def test_brief_has_finnish_twin_with_same_signal_ids():
    import re
    from fastapi.testclient import TestClient
    from backend.main import app
    b = TestClient(app).get("/api/state").json()["brief"]
    assert b["text_fi"] and "entropy" not in b["text"]
    assert set(re.findall(r"SIG-\d+", b["text"])) == set(re.findall(r"SIG-\d+", b["text_fi"]))


def test_ask_answers_in_the_language_of_the_question():
    from fastapi.testclient import TestClient
    from backend.main import app
    a = TestClient(app).post("/api/ask", json={"question": "Mikä on nykyinen tilanne?", "lang": "en"}).json()["answer"]
    assert "the" not in a.lower().split()[:6] or any(ch in a for ch in "äö")
