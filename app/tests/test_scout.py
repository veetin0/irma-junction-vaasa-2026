"""The signal scout: strict gates, nothing added without a qualifying source, persistence.

Uses a fake Anthropic client that returns the real block shapes. Run from app/:  python -m pytest tests -q
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("DEMO_TODAY", "2026-10-03")
os.environ["AGENT_MODE"] = "replay"
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pytest  # noqa: E402

import main  # noqa: E402
import test_web as tw  # noqa: E402
from agents.llm import LLMClient  # noqa: E402
from agents.pipeline import next_id  # noqa: E402

GOOD = "https://www.fingrid.fi/en/news/2026/data-centre-agreements-3-6-gw/"
OLD = "https://www.iea.org/reports/data-centre-outlook-march-2026"
BLOG = "https://random-blog.example/post/data-centres"
HIT_ONLY = "https://www.reuters.com/business/energy/nordic-grid-2026-10-02/"
KNOWN = "https://www.trendforce.com/presscenter/news/20260930-13258.html"
BAD_QUOTE = "https://energy.ec.europa.eu/news/data-centre-package-2026-09-29"
GOOD_QUOTE = "Fingrid has signed connection agreements for data centres totalling 3.6 GW"


def results(pairs):
    return {"type": "web_search_tool_result", "tool_use_id": "srvtoolu_s",
            "content": [{"type": "web_search_result", "url": u, "title": f"Title {i}", "page_age": age, "encrypted_content": "x"} for i, (u, age) in enumerate(pairs)]}


def fetched(url, text):
    return [{"type": "server_tool_use", "id": "srvtoolu_f", "name": "web_fetch", "input": {"url": url}},
            {"type": "web_fetch_tool_result", "tool_use_id": "srvtoolu_f",
             "content": {"type": "web_fetch_result", "url": url, "retrieved_at": "2026-10-03T08:00:00Z",
                         "content": {"type": "document", "title": "Fingrid news", "source": {"type": "text", "media_type": "text/plain", "data": text}}}}]


def cited(url, cited_text):
    return {"type": "text", "text": "Noted. ", "citations": [{"type": "web_search_result_location", "url": url, "title": "t", "cited_text": cited_text, "encrypted_index": "x"}]}


def cand(url, title, date, theme, quote, why="Signed transmission agreements precede substation projects that specify protection relays 12–18 months ahead."):
    return {"title": title, "source_url": url, "source_name": "Publisher", "published_date": date, "theme": theme, "region": "FI",
            "summary": "A factual summary of the item.", "quote": quote, "why_signal": why}


def discovery(cands, extra_blocks=None):
    blocks = [{"type": "server_tool_use", "id": "srvtoolu_s", "name": "web_search", "input": {"query": "Finland data centre grid connection October 2026"}},
              results([(GOOD, "2 days ago"), (OLD, "March 1, 2026"), (BLOG, "1 day ago"), (HIT_ONLY, "1 day ago"), (KNOWN, "3 days ago"), (BAD_QUOTE, "4 days ago")])]
    blocks += extra_blocks or []
    blocks.append({"type": "text", "text": json.dumps(cands), "citations": None})
    return SimpleNamespace(stop_reason="end_turn", usage=tw.usage(searches=2, fetches=1), content=blocks)


MIXED = discovery(
    [cand(GOOD, "Fingrid signs further data-centre connection agreements, 3.6 GW in total", "2026-10-01", "grid_and_connections", GOOD_QUOTE),
     cand(OLD, "IEA outlook on data-centre demand", "2026-03-01", "research_outlook", "Data centre demand will keep rising."),
     cand(BLOG, "Blog says Finland is the new hub", "2026-10-02", "data_centre_projects", "Finland is the new hub for data centres."),
     cand(HIT_ONLY, "Reuters: Nordic grid queues lengthen", "2026-10-02", "grid_and_connections", "Queues lengthen across the Nordics."),
     cand(KNOWN, "AI server demand sustains memory contract prices in 4Q26", "2026-09-30", "components_supply", "Conventional DRAM contract prices are projected to grow 10-15% QoQ in 4Q26."),
     cand(BAD_QUOTE, "EU bans new data centres", "2026-09-29", "energy_policy", "The European Union banned new data centres from 2027 onward.")],
    extra_blocks=fetched(GOOD, f"Helsinki, 1 October 2026. {GOOD_QUOTE}, up from just over 3 GW in June.")
    + [cited(OLD, "Data centre demand will keep rising."), cited(BLOG, "Finland is the new hub for data centres."),
       cited(KNOWN, "Conventional DRAM contract prices are projected to grow 10-15% QoQ in 4Q26."),
       cited(BAD_QUOTE, "The Commission proposed a rating scheme for data centres.")])


def verify(corroborated=True):
    return SimpleNamespace(stop_reason="end_turn", usage=tw.usage(searches=1),
                           content=tw.search_blocks("Fingrid data centre agreements 3.6 GW", [GOOD])
                           + [tw.text_block(json.dumps({"corroborated": corroborated, "primary_source_url": GOOD if corroborated else "",
                                                        "primary_source_name": "Fingrid", "published_date": "2026-10-01", "quote": GOOD_QUOTE, "notes": ""}))])


def nothing_against():
    return SimpleNamespace(stop_reason="end_turn", usage=tw.usage(searches=1), content=[tw.text_block("[]")])


class ScoutFake(tw.FakeMessages):
    def __init__(self, discoveries, **kw):
        super().__init__(**kw)
        self.discoveries = list(discoveries)

    def create(self, **kw):
        if kw.get("system", "").startswith("You are the signal scout"):
            self.calls.append(kw)
            return self.discoveries.pop(0)
        return super().create(**kw)


@pytest.fixture()
def store(tmp_path):
    s = main.STORE
    original_path, original_llm = s.additions_path, s.llm
    s.additions_path = tmp_path / "additions.json"
    s.scout_state["runs"] = []
    s.reset(1)
    yield s
    s.additions_path, s.llm = original_path, original_llm
    s.scout_state["runs"] = []
    s.reset(1)


def use(store, fake):
    store.llm = tw.live_client(fake)
    return fake


def test_next_id_uses_the_highest_number():
    assert next_id([{"id": "SIG-001"}, {"id": "SIG-034"}, {"id": "SIG-002"}], "SIG") == "SIG-035"
    assert next_id([], "CE") == "CE-001"


def test_strict_gates_admit_only_the_qualifying_source(store):
    before = len(store.signals)
    use(store, ScoutFake([MIXED], verify=[verify()], counter=[nothing_against()], draft=tw.draft(reliability="B")))
    rec = store.run_scout("manual")
    assert rec["status"] == "done" and rec["accepted"] == 1 and rec["rejected"] == 5
    codes = {c["reason"]["code"] for c in rec["candidates"] if c["decision"] == "rejected"}
    assert codes == {"too_old", "publisher_grade", "page_not_read", "already_known", "quote_not_in_retrieved_text"}
    accepted = next(c for c in rec["candidates"] if c["decision"] == "accepted")
    card = next(s for s in store.signals if s["id"] == accepted["signal_id"])
    assert len(store.signals) == before + 1 and card["origin"] == "scout" and card["theme"] == "grid_and_connections"
    assert card["source"]["url"] == GOOD and card["reliability"] == "A" and card["verification"]["corroborated"] is True
    assert card["ce_searched"] is True
    assert store.notifications[0]["kind"] == "new_signal_found"
    saved = json.loads(store.additions_path.read_text())
    assert [s["id"] for s in saved["signals"]] == [card["id"]] and len(saved["seen"]) == 6 and saved["runs"][-1]["id"] == rec["id"]
    assert rec["est_cost_usd"] > 0 and rec["searches"] >= 3


def test_nothing_is_added_when_no_source_qualifies(store):
    before_s, before_e = len(store.signals), len(store.evidence)
    use(store, ScoutFake([SimpleNamespace(stop_reason="end_turn", usage=tw.usage(searches=4), content=[tw.text_block("[]")])]))
    rec = store.run_scout("scheduled")
    assert rec["status"] == "done" and rec["accepted"] == 0 and rec["candidates"] == []
    assert rec["note"]["en"].startswith("No source met the criteria")
    assert len(store.signals) == before_s and len(store.evidence) == before_e
    assert not any(n["kind"] == "new_signal_found" for n in store.notifications)


def test_uncorroborated_candidate_leaves_live_data_untouched(store):
    before_s, before_e = len(store.signals), len(store.evidence)
    only_good = discovery([cand(GOOD, "Fingrid signs further data-centre connection agreements, 3.6 GW in total", "2026-10-01", "grid_and_connections", GOOD_QUOTE)],
                          extra_blocks=fetched(GOOD, GOOD_QUOTE))
    use(store, ScoutFake([only_good], verify=[verify(corroborated=False)], counter=[tw.counter_mixed()], draft=tw.draft(reliability="A")))
    rec = store.run_scout("manual")
    assert rec["accepted"] == 0 and rec["candidates"][0]["reason"]["code"] == "not_corroborated"
    assert len(store.signals) == before_s and len(store.evidence) == before_e   # counter-evidence built on the copy did not leak


def test_weak_candidate_is_rejected_on_weight(store):
    only_good = discovery([cand(GOOD, "Fingrid signs further data-centre connection agreements, 3.6 GW in total", "2026-10-01", "grid_and_connections", GOOD_QUOTE)],
                          extra_blocks=fetched(GOOD, GOOD_QUOTE))
    use(store, ScoutFake([only_good], verify=[verify()], counter=[nothing_against()], draft=tw.draft(strength=0.05)))
    rec = store.run_scout("manual")
    assert rec["accepted"] == 0 and rec["candidates"][0]["reason"]["code"] == "weight_too_low"


def test_saved_signals_reload_and_are_not_added_twice(store):
    use(store, ScoutFake([MIXED, MIXED], verify=[verify()], counter=[nothing_against()], draft=tw.draft(reliability="B")))
    first = store.run_scout("manual")
    sid = next(c["signal_id"] for c in first["candidates"] if c["decision"] == "accepted")
    store.reset(1)
    assert any(s["id"] == sid and s.get("origin") == "scout" for s in store.signals)
    second = store.run_scout("scheduled")
    assert second["accepted"] == 0
    assert next(c for c in second["candidates"] if c["url"] == GOOD)["reason"]["code"] == "already_known"


def test_scout_is_skipped_without_a_key_or_in_the_mock_world(store):
    store.llm = LLMClient()
    assert store.start_scout("scheduled") == "skipped:no_key"
    assert store.scout_public()["skip"]["en"].startswith("No API key")
    store.llm = tw.live_client(ScoutFake([]))
    store.reset(2)
    assert store.start_scout("scheduled") == "skipped:world"


def test_background_run_completes(store):
    use(store, ScoutFake([SimpleNamespace(stop_reason="end_turn", usage=tw.usage(searches=1), content=[tw.text_block("[]")])]))
    assert store.start_scout("manual") == "started"
    for _ in range(50):
        if not store.scout_state["running"]:
            break
        time.sleep(0.05)
    assert store.scout_state["running"] is False and store.scout_state["runs"][-1]["status"] == "done"


def test_blocked_domains_are_removed_from_saved_settings(store, tmp_path, monkeypatch):
    monkeypatch.setattr(main, "SETTINGS_PATH", tmp_path / "settings.json")
    store.settings["web_search"]["allowed_domains"] = store.settings["web_search"]["allowed_domains"] + ["ft.com"]
    ok = SimpleNamespace(stop_reason="end_turn", usage=tw.usage(searches=1), content=[tw.text_block("[]")])

    class Blocking(ScoutFake):
        def create(self, **kw):
            if kw.get("system", "").startswith("You are the signal scout") and not self.calls:
                self.calls.append(kw)
                import anthropic, httpx
                raise anthropic.BadRequestError("Error code: 400 - The following domains are not accessible to our user agent: ['ft.com']. Read more",
                                                response=httpx.Response(400, request=httpx.Request("POST", "https://api.anthropic.com/v1/messages")), body=None)
            return super().create(**kw)

    use(store, Blocking([ok]))
    rec = store.run_scout("scheduled")
    assert rec["status"] == "done" and rec["domains_removed"] == ["ft.com"]
    saved = json.loads((tmp_path / "settings.json").read_text())["web_search"]
    assert "ft.com" in saved["blocked_domains"] and "ft.com" not in saved["allowed_domains"]
    store.settings["web_search"]["blocked_domains"] = []
