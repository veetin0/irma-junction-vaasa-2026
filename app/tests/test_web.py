"""Web search for the agents, tested with a fake Anthropic client that returns the real block shapes.

Run from app/:  python -m pytest tests -q
"""
from __future__ import annotations

import copy
import json
import os
import sys
from datetime import date
from pathlib import Path
from types import SimpleNamespace

os.environ["AGENT_MODE"] = "replay"
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

import anthropic  # noqa: E402

from agents.llm import LLMClient, load_replay  # noqa: E402
from agents.pipeline import Context, Pipeline, SignalCardDraft  # noqa: E402
from agents.web import DEFAULT_WEB_SETTINGS, WEB_FETCH_TOOL, WEB_SEARCH_TOOL, domain_grade, extract_json, verify_url  # noqa: E402

DATA = Path(__file__).resolve().parents[1] / "backend" / "data"
TODAY = date(2026, 10, 3)
FINGRID = "https://www.fingrid.fi/en/news/2026/q3-interim/"
PRESS = "https://www.datacenterdynamics.com/en/news/finland-grid-queue-2026-10-02/"


def usage(searches=0, fetches=0):
    return SimpleNamespace(input_tokens=1200, output_tokens=400,
                           server_tool_use=SimpleNamespace(web_search_requests=searches, web_fetch_requests=fetches),
                           to_dict=lambda: {"input_tokens": 1200, "output_tokens": 400})


def search_blocks(query, urls):
    return [
        {"type": "server_tool_use", "id": "srvtoolu_1", "name": "web_search", "input": {"query": query}},
        {"type": "web_search_tool_result", "tool_use_id": "srvtoolu_1",
         "content": [{"type": "web_search_result", "url": u, "title": f"Page {i}", "page_age": "October 1, 2026", "encrypted_content": "x"} for i, u in enumerate(urls)]},
    ]


def text_block(text, cite_url=None):
    b = {"type": "text", "text": text, "citations": None}
    if cite_url:
        b["citations"] = [{"type": "web_search_result_location", "url": cite_url, "title": "Cited", "cited_text": "a quoted sentence", "encrypted_index": "x"}]
    return b


class FakeMessages:
    """Dispatches on the system prompt, like the agents' three kinds of call."""

    def __init__(self, verify=None, counter=None, verify_error=False, draft=None):
        self.calls = []
        self.verify, self.counter, self.verify_error = list(verify or []), list(counter or []), verify_error
        self.draft = draft

    def create(self, **kw):
        self.calls.append(kw)
        system = kw.get("system", "")
        if system.startswith("You verify"):
            if self.verify_error:
                raise anthropic.APIConnectionError(request=SimpleNamespace(method="POST", url="https://api.anthropic.com/v1/messages"))
            return self.verify.pop(0)
        if system.startswith("You are the counter-evidence agent for"):
            return self.counter.pop(0)
        # plain write() calls: interpretation, explainer, counter fallback without search
        return SimpleNamespace(stop_reason="end_turn", model="claude-opus-5-5", usage=usage(),
                               content=[SimpleNamespace(type="text", text='[{"claim": "Fallback claim", "source_hint": "regulator", "strength": 0.2}] Brief [SIG-001].')])

    def parse(self, **kw):
        self.calls.append(kw)
        return SimpleNamespace(stop_reason="end_turn", parsed_output=self.draft, usage=usage())


def live_client(messages):
    c = LLMClient()
    c.mode, c._client = "live", SimpleNamespace(messages=messages)
    return c


def draft(**over):
    base = dict(category="demand", measures="end_demand", region="FI", signal_type="leading", lead_months=30,
                lead_months_rationale="test", reliability="B", direction=1, strength=0.8, classification="structural",
                classification_rationale="test", value_number=3.6, value_unit="GW", value_label="signed DC capacity",
                excerpt="rose to 3.6 GW", axes={"demand": 0.8, "nordic": 0.8}, updates_signal_id=None)
    base.update(over)
    return SignalCardDraft(**base)


def run_pipeline(messages, web=True):
    ld = lambda p: json.loads((DATA / p).read_text(encoding="utf-8"))
    item = {"title": "Fingrid: signed data-centre agreements reach 3.6 GW", "text": "Signed capacity rose to 3.6 GW at the end of September.",
            "date": "2026-10-01", "source_name": "Example newsletter", "source_url": FINGRID, "data_label": "SOURCE"}
    wcfg = copy.deepcopy(DEFAULT_WEB_SETTINGS)
    wcfg["enabled"] = web
    ctx = Context(today=TODAY, signals=ld("worlds/1/signals.json"), evidence=ld("worlds/1/evidence.json"),
                  scenario_config=ld("scenario_archetypes.json"), bullwhip_config=ld("worlds/1/bullwhip.json"),
                  replay=load_replay(str(DATA / "replay.json")), llm=live_client(messages), item=item, web=wcfg)
    Pipeline().run(ctx)
    return ctx


# ---- helpers -----------------------------------------------------------------------------
def test_helpers():
    assert extract_json('Here: [{"a": 1}] and later [{"b": "x]y"}]', "array") == [{"b": "x]y"}]
    assert extract_json('noise {"corroborated": true} end', "object") == {"corroborated": True}
    assert extract_json("no json here", "array") is None
    ev = {"sources": [{"url": "https://www.fingrid.fi/en/news/2026/q3-interim"}]}
    assert verify_url("http://fingrid.fi/en/news/2026/q3-interim/", ev) is not None
    assert verify_url("https://fingrid.fi/en/news/other", ev) is None
    assert domain_grade(FINGRID, DEFAULT_WEB_SETTINGS) == "A"
    assert domain_grade(PRESS, DEFAULT_WEB_SETTINGS) == "B"
    assert domain_grade("https://random-blog.example/post", DEFAULT_WEB_SETTINGS) == "C"


# ---- research(): pause_turn continuation ---------------------------------------------------
def test_research_continues_after_pause_turn():
    first = SimpleNamespace(stop_reason="pause_turn", usage=usage(searches=1), content=search_blocks("fingrid data centre agreements", [FINGRID]))
    second = SimpleNamespace(stop_reason="end_turn", usage=usage(searches=1),
                             content=search_blocks("fingrid q3 2026", [PRESS]) + [text_block('{"corroborated": true}', cite_url=FINGRID)])
    msgs = FakeMessages(verify=[first, second])
    text, evidence, meta = live_client(msgs).research("You verify things", "item", DEFAULT_WEB_SETTINGS)
    assert len(msgs.calls) == 2
    resumed = msgs.calls[1]["messages"]
    assert [m["role"] for m in resumed] == ["user", "assistant"] and len(resumed[1]["content"]) == 2
    assert evidence["searches"] == 2 and len(evidence["sources"]) == 2 and len(evidence["queries"]) == 2
    assert any("citation" in s["via"] for s in evidence["sources"])
    tools = msgs.calls[0]["tools"]
    assert {t["type"] for t in tools} == {WEB_SEARCH_TOOL, WEB_FETCH_TOOL}
    assert all("fingrid.fi" in t["allowed_domains"] and t["max_uses"] >= 1 for t in tools)
    assert meta["mode"] == "live+web" and json.loads(text) == {"corroborated": True}


# ---- full pipeline -------------------------------------------------------------------------
def verify_ok():
    return SimpleNamespace(stop_reason="end_turn", usage=usage(searches=1, fetches=1),
                           content=search_blocks("Fingrid signed data centre agreements September 2026", [FINGRID])
                           + [text_block(json.dumps({"corroborated": True, "primary_source_url": FINGRID, "primary_source_name": "Fingrid, Q3 interim report",
                                                     "published_date": "2026-10-01", "quote": "rose to 3.6 GW", "notes": ""}))])


def counter_mixed():
    return SimpleNamespace(stop_reason="end_turn", usage=usage(searches=2),
                           content=search_blocks("Finland data centre connection delays", [PRESS])
                           + [text_block(json.dumps([
                               {"claim": "Southern Finland connection capacity is fully reserved until 2029.", "source_url": PRESS,
                                "source_name": "Reuters", "source_date": "2026-10-02", "quote": "capacity is fully reserved", "strength": 0.5},
                               {"claim": "An invented contradiction.", "source_url": "https://made-up.example.com/x",
                                "source_name": "Made-up site", "source_date": "2026-10-02", "quote": "", "strength": 0.9}]))])


def test_pipeline_with_web_verification_and_counter_search():
    msgs = FakeMessages(verify=[verify_ok()], counter=[counter_mixed()], draft=draft(reliability="B"))
    ctx = run_pipeline(msgs)
    card = ctx.new_signal
    assert card["verification"]["corroborated"] is True
    assert card["source"]["url"] == FINGRID and card["reliability"] == "A" and card["data_label"] == "SOURCE"
    assert card["source"]["date"] == "2026-10-01"
    created = ctx.new_evidence
    assert len(created) == 2
    good = next(c for c in created if c["web"]["verified"])
    bad = next(c for c in created if not c["web"]["verified"])
    assert good["source"]["url"] == PRESS and good["reliability"] == "B" and good["data_label"] == "SOURCE"
    assert bad["source"]["url"] == "" and bad["reliability"] == "C" and bad["strength"] <= 0.3 and bad["data_label"] == "ASSUMPTION"
    modes = {t.agent: t.mode for t in ctx.trace}
    assert modes["Demand signal agent"] == "live+web" and modes["Counter-evidence agent"] == "live+web"
    assert card["counter_search"]["searches"] == 2
    # the classifier saw the verification result
    parse_call = next(c for c in msgs.calls if "output_format" in c)
    assert "WEB VERIFICATION: corroborated=True" in parse_call["messages"][0]["content"]


def test_uncorroborated_item_is_downgraded_and_flagged():
    not_found = SimpleNamespace(stop_reason="end_turn", usage=usage(searches=1),
                                content=search_blocks("unknown claim", [PRESS]) + [text_block('{"corroborated": false, "primary_source_url": "", "notes": "No primary source found."}')])
    empty_counter = SimpleNamespace(stop_reason="end_turn", usage=usage(searches=1), content=[text_block("[]")])
    ctx = run_pipeline(FakeMessages(verify=[not_found], counter=[empty_counter], draft=draft(reliability="A")))
    card = ctx.new_signal
    assert card["reliability"] == "C" and card["needs_review"] is True and card["verification"]["corroborated"] is False
    # search ran and found nothing: no placeholder card, signal counts as challenged
    assert ctx.new_evidence == [] and card["ce_searched"] is True


def test_web_disabled_sends_no_tools():
    msgs = FakeMessages(draft=draft())
    ctx = run_pipeline(msgs, web=False)
    assert all("tools" not in c for c in msgs.calls)
    assert {t.agent: t.mode for t in ctx.trace}["Counter-evidence agent"] == "live"


def test_api_error_falls_back_without_breaking_the_run():
    msgs = FakeMessages(verify_error=True, counter=[counter_mixed()], draft=draft(reliability="B"))
    ctx = run_pipeline(msgs)
    step = next(t for t in ctx.trace if t.agent == "Demand signal agent")
    assert step.mode == "live" and any("Web verification unavailable" in n for n in step.notes)
    assert "verification" not in ctx.new_signal and ctx.new_signal["reliability"] == "B"
    assert len(ctx.trace) == 7
