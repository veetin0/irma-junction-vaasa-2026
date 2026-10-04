"""The agent layer: eight agents, one orchestrator, no recommendation agent.

Each agent has one responsibility, declared inputs and outputs, and a defined
failure behaviour. The LLM is used only to read and classify; all numbers come
from engine/*. When the LLM is unavailable the agent degrades to replayed or
heuristic output and says so in the trace.
"""
from __future__ import annotations

import hashlib
import re
import time
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any, Optional

from pydantic import BaseModel, Field

from engine.bullwhip import compute_bullwhip
from engine.archetypes import select_scenarios
from engine.scenarios import probability_delta
from engine.weights import compute_weights
from agents.llm import LLMClient, recommendation_filter
from agents.web import clamp01, clean_date, domain_grade, extract_json, host_of, verify_url


# ----------------------------------------------------------------------------------
# Structured output schema for the signal classifiers (LLM fills this; code computes)
# ----------------------------------------------------------------------------------
class Axes(BaseModel):
    """Explicit fields: a free-form dict becomes an empty object under the SDK's strict schema transform."""
    demand: float = Field(default=0.0, description="end demand accelerates (+) or contracts (-), in [-1, 1]")
    supply: float = Field(default=0.0, description="components tight (+) or loose (-), in [-1, 1]")
    policy: float = Field(default=0.0, description="rules favour (+) or restrict (-) projects, in [-1, 1]")
    price: float = Field(default=0.0, description="materials dearer (+) or cheaper (-), in [-1, 1]")
    nordic: float = Field(default=0.0, description="demand shifts toward (+) or away from (-) the Nordics, in [-1, 1]")
    bullwhip: float = Field(default=0.0, description="intermediaries hoarding (+) or unwinding (-), in [-1, 1]")


class SignalCardDraft(BaseModel):
    category: str = Field(description="demand | supply | bullwhip | price | policy")
    measures: str = Field(description="end_demand | supply_tightness | intermediary | price | policy")
    region: str = Field(description="FI | NORDICS | EU | US | GLOBAL")
    signal_type: str = Field(description="leading | coincident | lagging")
    lead_months: int
    lead_months_rationale: str
    reliability: str = Field(description="A | B | C")
    direction: int = Field(description="+1 toward demand acceleration / supply tightness, -1 opposite, 0 neutral")
    strength: float = Field(description="0..1 size of the move relative to the signal's own history")
    classification: str = Field(description="structural | cyclical | mixed")
    classification_rationale: str
    value_number: Optional[float] = None
    value_unit: Optional[str] = None
    value_label: Optional[str] = None
    excerpt: str = Field(description="verbatim quote from the source text that supports the card")
    axes: "Axes" = Field(default_factory=lambda: Axes(), description="how the observation loads on six axes, each in [-1, 1]")
    updates_signal_id: Optional[str] = Field(default=None, description="existing signal id if this is a new observation of it")


def next_id(items: list[dict[str, Any]], prefix: str) -> str:
    """Highest existing numeric id + 1 (safe with gaps and with ids reloaded from saved additions)."""
    nums = [int(m.group(1)) for x in items if (m := re.match(rf"^{prefix}-(\d+)$", str(x.get("id", ""))))]
    return f"{prefix}-{(max(nums) + 1 if nums else 1):03d}"


def _t(v: Any, lang: str = "en") -> str:
    """Pick a language from a bilingual dict, pass strings through."""
    if isinstance(v, dict):
        return str(v.get(lang) or v.get("en") or "")
    return "" if v is None else str(v)


@dataclass
class TraceStep:
    agent: str
    status: str  # ok | degraded | failed
    mode: str  # code | live | replay | heuristic
    summary: str
    output: Any = None
    duration_ms: int = 0
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "agent": self.agent, "status": self.status, "mode": self.mode, "summary": self.summary,
            "output": self.output, "duration_ms": self.duration_ms, "notes": self.notes,
        }


@dataclass
class Context:
    today: date
    signals: list[dict[str, Any]]
    evidence: list[dict[str, Any]]
    scenario_config: dict[str, Any]
    bullwhip_config: dict[str, Any]
    replay: dict[str, Any]
    llm: LLMClient
    item: dict[str, Any] | None = None
    web: dict[str, Any] | None = None
    normalized: dict[str, Any] | None = None
    new_signal: dict[str, Any] | None = None
    is_update: bool = False
    new_evidence: list[dict[str, Any]] = field(default_factory=list)
    before: dict[str, Any] | None = None
    after: dict[str, Any] | None = None
    weights: dict[str, Any] = field(default_factory=dict)
    bullwhip: dict[str, Any] | None = None
    interpretation: dict[str, Any] | None = None
    brief: dict[str, Any] | None = None
    trace: list[TraceStep] = field(default_factory=list)


def _timed(fn):
    def wrapper(self, ctx: Context) -> TraceStep:
        t0 = time.perf_counter()
        step = fn(self, ctx)
        step.duration_ms = int((time.perf_counter() - t0) * 1000)
        ctx.trace.append(step)
        return step
    return wrapper


# ----------------------------------------------------------------------------------
# 1. Collector & normaliser
# ----------------------------------------------------------------------------------
class CollectorAgent:
    name = "Collector & normaliser"
    responsibility = "Pulls raw items from configured sources and normalises date, units and provenance into one record."

    @_timed
    def run(self, ctx: Context) -> TraceStep:
        item = ctx.item or {}
        text = (item.get("text") or "").strip()
        title = (item.get("title") or text[:80] or "Untitled item").strip()
        raw_date = (item.get("date") or "").strip()
        iso = raw_date[:10] if re.match(r"^\d{4}-\d{2}-\d{2}", raw_date) else None
        notes = []
        if iso is None:
            notes.append("Date missing or unparsable: freshness will be 0 until corrected.")
        digest = hashlib.sha1(f"{title}|{text}|{item.get('source_url','')}".encode()).hexdigest()[:10]
        ctx.normalized = {
            "id": f"RAW-{digest}",
            "title": title,
            "text": text,
            "date": iso,
            "source": {
                "name": item.get("source_name") or "Unspecified source",
                "url": item.get("source_url") or "",
                "access": item.get("access") or "manual entry",
                "date": iso or "",
            },
            "data_label": item.get("data_label") or "DEMODATA",
        }
        status = "degraded" if notes else "ok"
        return TraceStep(self.name, status, "code", f"Normalised 1 item ({ctx.normalized['id']}), dated {iso or 'unknown'}.", ctx.normalized, notes=notes)


# ----------------------------------------------------------------------------------
# 2/3. Demand and supply signal agents (same mechanics, different prompts)
# ----------------------------------------------------------------------------------
CLASSIFIER_SYSTEM = """You read one market item about electrification / data centres / electronic components and
fill a signal card for ABB Distribution Solutions' protection-relay business. Rules:
- Only state what the text supports; quote the supporting sentence verbatim in `excerpt`.
- Never invent a number. If the text has no number, leave value_number null.
- reliability: A = primary source (TSO, regulator, company filing, IEA), B = reputable secondary, C = blog/unverified.
- direction: +1 if the item points toward demand acceleration (demand items) or supply tightness (supply items); -1 if the opposite; 0 if neutral.
- strength 0..1: how large the move is relative to the signal's own history.
- classification: structural (multi-year, contract-backed, regulated), cyclical (sentiment, prices, lead times, timing), mixed.
- axes: how this observation loads on six axes, each in [-1, 1]: demand (end demand accelerates +, contracts -), supply (components tight +, loose -), policy (rules favour projects +, restrict -), price (materials dearer +), nordic (demand shifts toward the Nordics +), bullwhip (intermediaries hoarding +, unwinding -).
- You do not make recommendations. You classify."""


def _source_class(category: str, title: str, text: str) -> str:
    t = f"{title} {text}".lower()
    if category in ("supply", "price") or any(k in t for k in ["price", "lead time", "lead-time", "contract price"]):
        return "price"
    if category == "policy":
        return "policy"
    if any(k in t for k in ["agreement", "contract", "signed", "ppa", "purchase order", "land purchase"]):
        return "contract"
    return "news"


def _heuristic_draft(text: str, title: str, kind: str) -> SignalCardDraft:
    """Deterministic keyword classifier used when no LLM is available. Labelled as heuristic."""
    t = f"{title} {text}".lower()
    region = "FI" if any(k in t for k in ["finland", "fingrid", "vaasa", "finnish"]) else \
        "NORDICS" if any(k in t for k in ["nordic", "sweden", "norway", "denmark"]) else \
        "US" if any(k in t for k in ["united states", " us ", "u.s.", "virginia", "texas"]) else \
        "EU" if any(k in t for k in ["europe", "eu ", "germany", "amsterdam", "ireland"]) else "GLOBAL"
    negative = any(k in t for k in ["cancel", "delay", "pause", "moratorium", "cut", "fall", "decline", "down", "lower"])
    direction = -1 if negative else 1
    num = re.search(r"(\d+(?:[\.,]\d+)?)\s*(gw|mw|twh|%|weeks|usd|eur|bn|billion)", t)
    value_number = float(num.group(1).replace(",", ".")) if num else None
    value_unit = num.group(2).upper() if num else None
    if kind == "supply":
        links = {}
        return SignalCardDraft(axes={"supply": 0.7 * direction, "price": 0.3 * direction}, category="supply", measures="supply_tightness", region=region, signal_type="coincident",
                               lead_months=4, lead_months_rationale="[heuristic default for supply items]",
                               reliability="C", direction=direction, strength=0.5, classification="cyclical",
                               classification_rationale="Heuristic: lead-time and price items default to cyclical.",
                               value_number=value_number, value_unit=value_unit, value_label=title,
                               excerpt=text[:240], updates_signal_id=None)
    links = {}
    nordic = 0.5 * direction if region in ("FI", "NORDICS") else 0.0
    structural = any(k in t for k in ["agreement", "contract", "signed", "22-year", "investment", "committed"])
    return SignalCardDraft(axes={"demand": 0.6 * direction, "nordic": nordic}, category="demand", measures="end_demand", region=region, signal_type="leading",
                           lead_months=18, lead_months_rationale="[heuristic default for demand items]",
                           reliability="C", direction=direction, strength=0.5,
                           classification="structural" if structural else "cyclical",
                           classification_rationale="Heuristic: contract/agreement language marks structural; otherwise cyclical.",
                           value_number=value_number, value_unit=value_unit, value_label=title,
                           excerpt=text[:240], updates_signal_id=None)


VERIFY_SYSTEM = """You verify one market news item before it becomes a signal card for a market-scenario monitor
used by ABB's protection-relay business. If the item has a URL, fetch it. Search for the primary source (the grid
operator, regulator, company or institute that published the fact) and for independent corroboration.
Use only pages you actually retrieved with your tools; never invent a URL, a date or a number.
Return only a JSON object, no prose: {"corroborated": true or false, "primary_source_url": exact retrieved URL or "",
"primary_source_name": publisher and title or "", "published_date": "YYYY-MM-DD" or "", "quote": one short verbatim
sentence from the primary source supporting the item or "", "notes": one sentence on any discrepancy (different number,
older date, retraction) or ""}."""


def web_on(ctx: "Context") -> bool:
    return bool(ctx.web and ctx.web.get("enabled")) and ctx.llm.mode == "live"


def _verify_item(ctx: "Context", n: dict[str, Any]) -> tuple[dict[str, Any] | None, list[str]]:
    """Web verification of an incoming item. Code keeps only URLs the tools actually returned."""
    notes: list[str] = []
    prompt = (f"TITLE: {n['title']}\nDATE GIVEN: {n['date'] or 'none'}\nSOURCE GIVEN: {n['source']['name']}\n"
              f"URL GIVEN: {n['source'].get('url') or 'none'}\nTEXT:\n{n['text'][:4000]}")
    extra = [host_of(n["source"].get("url"))] if n["source"].get("url") else []
    text, evidence, meta = ctx.llm.research(VERIFY_SYSTEM, prompt, ctx.web, extra_domains=extra)
    if text is None:
        notes.append(f"Web verification unavailable ({meta.get('error')}); card classified without it.")
        return None, notes
    result = extract_json(text, "object") or {}
    primary = verify_url(result.get("primary_source_url"), evidence)
    if result.get("primary_source_url") and primary is None:
        notes.append("The primary-source link proposed by the model was not among the retrieved pages and was dropped.")
    corroborated = bool(result.get("corroborated")) and primary is not None
    verification = {
        "ran": True, "corroborated": corroborated,
        "primary": ({"url": primary["url"], "name": result.get("primary_source_name") or primary.get("title") or host_of(primary["url"]),
                     "date": clean_date(result.get("published_date"), ctx.today) or clean_date(primary.get("page_age"), ctx.today),
                     "grade": domain_grade(primary["url"], ctx.web)} if primary else None),
        "quote": str(result.get("quote") or "")[:300], "notes": str(result.get("notes") or "")[:300],
        "queries": evidence["queries"], "searches": evidence["searches"], "fetches": evidence["fetches"],
        "sources": [{"url": x["url"], "title": x["title"], "grade": domain_grade(x["url"], ctx.web)} for x in evidence["sources"][:8]],
        "errors": evidence["errors"], "usage": meta.get("usage"),
    }
    notes.append(f"Web verification: {evidence['searches']} search(es), {evidence['fetches']} fetch(es), "
                 f"{len(evidence['sources'])} page(s) retrieved; corroborated = {corroborated}.")
    return verification, notes


def _apply_verification(card: dict[str, Any], v: dict[str, Any] | None, is_new: bool) -> list[str]:
    """Deterministic consequences of web verification for the card's source and reliability."""
    if not v:
        return []
    card["verification"] = v
    rank = {"A": 3, "B": 2, "C": 1}
    if v["corroborated"] and v["primary"]:
        p = v["primary"]
        card["source"] = {**card.get("source", {}), "name": p["name"], "url": p["url"], "date": p["date"] or card.get("source", {}).get("date", "")}
        if not card.get("observed_at") and p["date"]:
            card["observed_at"] = p["date"]
        old = card.get("reliability", "C")
        card["reliability"] = p["grade"] if is_new else (p["grade"] if rank[p["grade"]] > rank.get(old, 1) else old)
        card["data_label"] = "SOURCE"
        return [f"Source replaced by the verified primary source ({p['grade']}-grade domain)."]
    card["needs_review"] = True
    if is_new:
        card["reliability"] = "C"
        return ["Not corroborated by web search: reliability set to C and the card flagged for review."]
    return ["New observation not corroborated by web search: card flagged for review; reliability unchanged."]


class SignalAgent:
    def __init__(self, kind: str) -> None:
        self.kind = kind
        self.name = "Demand signal agent" if kind == "demand" else "Supply signal agent"
        self.responsibility = (
            "Verifies each end-demand item against its primary source on the web, then classifies it into a signal card."
            if kind == "demand" else
            "Verifies each component item (prices, lead times, allocation) against its primary source on the web, then classifies it into a signal card."
        )

    def applies(self, ctx: Context) -> bool:
        t = f"{ctx.normalized['title']} {ctx.normalized['text']}".lower()
        supply_words = ["dram", "memory", "mcu", "lead time", "lead-time", "allocation", "wafer", "semiconductor", "contract price", "distributor"]
        is_supply = any(w in t for w in supply_words)
        return is_supply if self.kind == "supply" else not is_supply

    @_timed
    def run(self, ctx: Context) -> TraceStep:
        n = ctx.normalized
        assert n is not None
        notes: list[str] = []
        replay_key = (ctx.item or {}).get("replay_key")
        replayed = ctx.replay.get(replay_key, {}).get("classify") if replay_key else None
        mode = "live"
        draft: SignalCardDraft | None = None
        verification = None
        if web_on(ctx):
            verification, vnotes = _verify_item(ctx, n)
            notes.extend(vnotes)
        if ctx.llm.mode == "live":
            vtxt = ""
            if verification:
                pr = verification["primary"] or {}
                vtxt = (f"\nWEB VERIFICATION: corroborated={verification['corroborated']}; primary source={pr.get('name', 'none')} "
                        f"({pr.get('url', '')}, {pr.get('date', '')}); quote: {verification['quote']}; notes: {verification['notes']}")
            draft, meta = ctx.llm.classify(CLASSIFIER_SYSTEM, f"TITLE: {n['title']}\nDATE: {n['date']}\nSOURCE: {n['source']['name']}\nTEXT:\n{n['text']}{vtxt}", SignalCardDraft)
            if draft is None:
                notes.append(f"LLM classification failed ({meta.get('error')}); falling back.")
        if draft is None and replayed:
            draft, mode = SignalCardDraft(**replayed), "replay"
        if draft is None:
            draft, mode = _heuristic_draft(n["text"], n["title"], self.kind), "heuristic"
            notes.append("Keyword heuristic used: reliability forced to C and strength 0.5 until a human reviews the card.")

        existing = next((s for s in ctx.signals if s["id"] == draft.updates_signal_id), None) if draft.updates_signal_id else None
        if existing is not None:
            # New observation of an existing signal: append to history, refresh the card.
            existing["observed_at"] = n["date"] or existing["observed_at"]
            existing["direction"] = draft.direction
            existing["strength"] = draft.strength
            existing["excerpt"] = draft.excerpt
            existing["source"] = {**existing["source"], **n["source"]}
            existing["data_label"] = n["data_label"]
            if any(draft.axes.model_dump().values()):
                existing["axes"] = draft.axes.model_dump()
            if draft.value_number is not None:
                existing["value"] = {"number": draft.value_number, "unit": draft.value_unit or existing["value"].get("unit"), "label": draft.value_label or existing["value"].get("label")}
                existing.setdefault("history", []).append({"date": n["date"], "value": draft.value_number})
            existing["ce_searched"] = False
            notes.extend(_apply_verification(existing, verification, is_new=False))
            ctx.new_signal = existing
            ctx.is_update = True
            summary = f"Updated {existing['id']} ({existing['short']}) with a new observation dated {n['date']}."
        else:
            new_id = next_id(ctx.signals, "SIG")
            card = {
                "id": new_id, "name": n["title"], "short": n["title"][:40],
                "category": draft.category, "measures": draft.measures, "region": draft.region, "segment": "datacenter",
                "type": draft.signal_type, "lead_months": draft.lead_months, "lead_months_rationale": draft.lead_months_rationale,
                "update_frequency": "event", "source": n["source"], "reliability": draft.reliability,
                "direction": draft.direction, "strength": draft.strength, "observed_at": n["date"] or "",
                "classification": draft.classification, "classification_rationale": draft.classification_rationale,
                "value": {"number": draft.value_number, "unit": draft.value_unit, "label": draft.value_label},
                "data_label": n["data_label"], "excerpt": draft.excerpt,
                "history": [{"date": n["date"], "value": draft.value_number}] if draft.value_number is not None else [],
                "history_label": n["data_label"], "history_note": "Single observation.",
                "axes": draft.axes.model_dump(), "usage_restrictions": "", "counter_evidence": [],
                "ce_searched": False, "annotations": [], "needs_review": mode != "live",
                "source_class": _source_class(draft.category, n["title"], n["text"]), "locked": False,
                "tracking": {"checks": 0, "last_checked": None},
            }
            notes.extend(_apply_verification(card, verification, is_new=True))
            ctx.signals.append(card)
            ctx.new_signal = card
            summary = f"Created {new_id}: {draft.category}/{draft.measures}, {draft.region}, direction {draft.direction:+d}, strength {draft.strength:.1f}, {draft.classification}."
        status = "ok" if mode == "live" else "degraded"
        if verification and mode == "live":
            mode = "live+web"
        return TraceStep(self.name, status, mode, summary, {"draft": draft.model_dump(), "signal_id": ctx.new_signal["id"], "verification": verification}, notes=notes)


# ----------------------------------------------------------------------------------
# 4. Bullwhip / demand-quality agent
# ----------------------------------------------------------------------------------
class BullwhipAgent:
    name = "Demand-quality (bullwhip) agent"
    responsibility = "Computes the bullwhip metrics and labels whether apparent demand looks like end use or hoarding."

    @_timed
    def run(self, ctx: Context) -> TraceStep:
        result = compute_bullwhip(ctx.bullwhip_config)
        ctx.bullwhip = result
        connected = [m for m in result["metrics"] if m["status"] != "not_connected"]
        summary = f"{result['overall'].replace('_', ' ')}: {len(connected)}/{len(result['metrics'])} metrics connected. {result['summary']}"
        return TraceStep(self.name, "ok", "code", summary, {"overall": result["overall"], "metrics": [{"id": m["id"], "name": m["name"], "value": m["value"], "status": m["status"]} for m in result["metrics"]]})


# ----------------------------------------------------------------------------------
# 5. Counter-evidence agent
# ----------------------------------------------------------------------------------
COUNTER_SYSTEM = """You are the counter-evidence agent. Given a signal card, write up to three specific claims that would
weaken or reverse the signal's reading. Each claim must be checkable, name the kind of source that would settle it,
and must not invent numbers. Output JSON list of {claim, source_hint, strength 0..1}. You do not recommend actions."""


COUNTER_WEB_SYSTEM = """You are the counter-evidence agent for a market-scenario monitor used by ABB's protection-relay
business. Search the web for evidence that contradicts, weakens or delays the signal you are given. Prefer primary sources
(grid operators, regulators, company filings, statistical agencies, research institutes). Use only pages you actually
retrieved with your tools; never invent a URL, a date or a number.
Return only a JSON array, no prose, of at most 3 objects: {"claim": one or two sentences, "source_url": exact retrieved URL,
"source_name": publisher and title, "source_date": "YYYY-MM-DD" or "", "quote": one short verbatim sentence from the
source, "strength": number 0..1 for how much it weakens the signal}. Return [] if nothing you found contradicts the
signal. You do not recommend actions."""


def _counter_prompt(sig: dict[str, Any]) -> str:
    return (f"SIGNAL: {sig.get('name')}\nREGION: {sig.get('region')}\nOBSERVED: {sig.get('observed_at')}\n"
            f"VALUE: {(sig.get('value') or {}).get('label')}\nCLASSIFIED AS: {sig.get('classification')}, direction {sig.get('direction')}\n"
            f"SOURCE: {(sig.get('source') or {}).get('name')} {(sig.get('source') or {}).get('url', '')}\nEXCERPT: {sig.get('excerpt')}")


class CounterEvidenceAgent:
    name = "Counter-evidence agent"
    responsibility = "Searches the web for evidence that contradicts every new signal and links only sources it actually retrieved."

    @_timed
    def run(self, ctx: Context) -> TraceStep:
        sig = ctx.new_signal
        if sig is None:
            return TraceStep(self.name, "failed", "code", "No new signal to challenge.")
        replay_key = (ctx.item or {}).get("replay_key")
        replayed = ctx.replay.get(replay_key, {}).get("counter") if replay_key else None
        notes: list[str] = []
        created: list[dict[str, Any]] = []
        mode = "replay" if replayed else "heuristic"
        searched_empty = False
        web_meta: dict[str, Any] | None = None
        if web_on(ctx):
            text, evidence, meta = ctx.llm.research(COUNTER_WEB_SYSTEM, _counter_prompt(sig), ctx.web)
            items = extract_json(text, "array") if text is not None else None
            if text is None:
                notes.append(f"Web search unavailable ({meta.get('error')}); falling back to the model without search.")
            elif items is None:
                notes.append("Web search answer had no JSON list; falling back to the model without search.")
            else:
                mode = "live+web"
                web_meta = {"queries": evidence["queries"], "searches": evidence["searches"], "fetches": evidence["fetches"], "usage": meta.get("usage")}
                replayed = []
                for it in [x for x in items if isinstance(x, dict) and x.get("claim")][:3]:
                    hit = verify_url(it.get("source_url"), evidence)
                    strength = clamp01(it.get("strength"))
                    if hit:
                        replayed.append({"claim": str(it["claim"])[:600],
                                         "source": {"name": str(it.get("source_name") or hit["title"] or host_of(hit["url"]))[:200], "url": hit["url"],
                                                    "date": clean_date(it.get("source_date"), ctx.today) or clean_date(hit.get("page_age"), ctx.today)},
                                         "reliability": domain_grade(hit["url"], ctx.web), "strength": strength, "data_label": "SOURCE",
                                         "web": {"verified": True, "quote": str(it.get("quote") or "")[:300]}})
                    else:
                        replayed.append({"claim": str(it["claim"])[:600],
                                         "source": {"name": f"[unverified] {str(it.get('source_name') or 'source not retrieved')[:160]}", "url": "", "date": ""},
                                         "reliability": "C", "strength": min(strength, 0.3), "data_label": "ASSUMPTION",
                                         "web": {"verified": False, "note": "The link was not among the retrieved pages and was removed."}})
                        notes.append("One proposed source was not among the retrieved pages: link removed, graded C, strength capped at 0.3.")
                searched_empty = not replayed
                notes.append(f"Web: {evidence['searches']} search(es), {evidence['fetches']} fetch(es); "
                             + "; ".join(q.get("query") or q.get("url", "") for q in evidence["queries"][:4]))
        if mode != "live+web" and ctx.llm.mode == "live":
            text, meta = ctx.llm.write(COUNTER_SYSTEM, f"SIGNAL CARD:\n{sig}")
            if text:
                payload = extract_json(text, "array")
                if isinstance(payload, list):
                    replayed = [{"claim": str(p["claim"])[:600], "source": {"name": str(p.get("source_hint") or "to be sourced")[:200], "url": "", "date": ctx.today.isoformat()},
                                 "reliability": "C", "strength": clamp01(p.get("strength")), "data_label": "ASSUMPTION"}
                                for p in payload if isinstance(p, dict) and p.get("claim")]
                    mode = "live"
                else:
                    notes.append("Model answer had no JSON list; falling back.")
        if not replayed and not searched_empty:
            replayed = [{
                "claim": f"No counter-evidence has been sourced yet for '{sig.get('short')}'. Until a human or the agent links a contradicting source, the card is marked unchallenged and its weight is capped at 0.6.",
                "source": {"name": "[ASSUMPTION] unchallenged placeholder", "url": "", "date": ctx.today.isoformat()},
                "reliability": "C", "strength": 0.0, "data_label": "ASSUMPTION",
            }]
            notes.append("Unchallenged: weight cap 0.6 applied by the engine.")
        for i, ce in enumerate(replayed):
            ce_id = next_id(ctx.evidence, "CE")
            card = {"id": ce_id, "against": sig["id"], **ce}
            ctx.evidence.append(card)
            sig.setdefault("counter_evidence", []).append(ce_id)
            created.append(card)
        sig["ce_searched"] = searched_empty or any(c["strength"] > 0 for c in created)
        if web_meta is not None:
            sig["counter_search"] = {"at": ctx.today.isoformat(), "found": len(created), **web_meta}
        ctx.new_evidence = created
        if searched_empty:
            notes.append("Web search found nothing that contradicts this signal; the card counts as challenged.")
        summary = f"Linked {len(created)} counter-evidence card(s) to {sig['id']}; searched = {sig['ce_searched']}."
        return TraceStep(self.name, "ok" if mode != "heuristic" else "degraded", mode, summary, created, notes=notes)


# ----------------------------------------------------------------------------------
# 6. Scenario agent
# ----------------------------------------------------------------------------------
class ScenarioAgent:
    name = "Scenario agent"
    responsibility = "Maintains the four scenarios and recomputes their probabilities from the weighted signals."

    @_timed
    def run(self, ctx: Context) -> TraceStep:
        k = float(ctx.scenario_config.get("scaling_k", 1.5))
        ctx.weights = compute_weights(ctx.signals, ctx.evidence, ctx.today)
        ctx.after = select_scenarios(ctx.scenario_config["archetypes"], ctx.signals, ctx.weights, k)
        deltas = probability_delta(ctx.before, ctx.after)
        moved = sorted(deltas, key=lambda d: -abs(d["delta"] or 0))
        top = moved[0] if moved and moved[0]["delta"] is not None else None
        names = ", ".join(_t(x["name"]) for x in ctx.after["scenarios"])
        summary = (
            f"Selected the 4 most likely of {len(ctx.scenario_config['archetypes'])} candidate situations: {names}. Entropy {ctx.after['entropy']:.2f}. "
            + (f"Largest move: {top['name']} {top['before']:.0%} -> {top['after']:.0%}." if (top and top['before'] is not None) else "")
        )
        return TraceStep(self.name, "ok", "code", summary, {"deltas": deltas, "entropy": ctx.after["entropy"], "k": k, "candidates": ctx.after["candidates"]})


# ----------------------------------------------------------------------------------
# 7. Interpretation agent (ABB translation, conditional only)
# ----------------------------------------------------------------------------------
INTERPRET_SYSTEM = """You translate a scenario update into ABB Distribution Solutions' language, in CONDITIONAL form only
("if this scenario holds, ..."). Cover demand, delivery capability and component need. Never tell ABB what to
order, buy, stock or decide; the user decides. Keep to 120 words per scenario."""


class InterpretationAgent:
    name = "Interpretation agent"
    responsibility = "Writes what each scenario would mean for ABB demand, delivery capability and component need, conditionally."

    @_timed
    def run(self, ctx: Context) -> TraceStep:
        assert ctx.after is not None
        replay_key = (ctx.item or {}).get("replay_key")
        replayed = ctx.replay.get(replay_key, {}).get("interpretation") if replay_key else None
        notes: list[str] = []
        mode = "replay" if replayed else "code"
        text_by_id: dict[str, str] = {}
        if ctx.llm.mode == "live":
            text, meta = ctx.llm.write(INTERPRET_SYSTEM, f"NEW SIGNAL: {ctx.new_signal}\nSCENARIOS: {[{'id': s['id'], 'name': _t(s['name']), 'probability': s['probability'], 'narrative': _t(s['narrative'])} for s in ctx.after['scenarios']]}")
            if text:
                clean, removed = recommendation_filter(text)
                if removed:
                    notes.append(f"Guardrail removed {len(removed)} sentence(s) with recommendation language.")
                text_by_id = {"ALL": clean}
                mode = "live"
        if not text_by_id and replayed:
            text_by_id = replayed
        if not text_by_id:
            sig = ctx.new_signal or {}
            for s in ctx.after["scenarios"]:
                base = s["abb_interpretation"]
                text_by_id[s["id"]] = (
                    f"If '{_t(s['name'])}' holds (now {s['probability']:.0%}): {_t(base['demand'])} {_t(base['components'])} "
                    f"The new item ({sig.get('id')}) contributed {next((c['contribution'] for c in s['contributions'] if c['signal_id'] == sig.get('id')), 0):+.2f} to this scenario's log-odds."
                )
        for sid, txt in list(text_by_id.items()):
            clean, removed = recommendation_filter(txt)
            text_by_id[sid] = clean
            if removed:
                notes.append(f"Guardrail removed recommendation language from scenario {sid}.")
        ctx.interpretation = text_by_id
        return TraceStep(self.name, "ok", mode, "Conditional interpretation written for each scenario; guardrail applied.", text_by_id, notes=notes)


# ----------------------------------------------------------------------------------
# 8. Explainer agent
# ----------------------------------------------------------------------------------
EXPLAIN_SYSTEM = """You write a short situation brief for a procurement/S&OP planner at ABB Distribution Solutions.
Cite signal ids in brackets like [SIG-001]. State uncertainty explicitly. End with 'Next analysis step' listing:
which signals to watch, when to re-evaluate, and who to review with. Never recommend purchases or quantities."""


def _next_analysis_step(ctx: Context) -> dict[str, Any]:
    """Deterministic next-step builder: top contributors with the oldest data, plus scheduled source updates."""
    assert ctx.after is not None
    contribs: dict[str, float] = {}
    for s in ctx.after["scenarios"]:
        for c in s["contributions"]:
            contribs[c["signal_id"]] = contribs.get(c["signal_id"], 0) + abs(c["contribution"])
    by_id = {s["id"]: s for s in ctx.signals}
    ranked = sorted(contribs.items(), key=lambda kv: -kv[1])[:5]
    watch = []
    for sid, _ in ranked:
        s = by_id[sid]
        w = ctx.weights.get(sid, {})
        watch.append({
            "signal_id": sid, "short": s.get("short"), "freshness": w.get("components", {}).get("freshness"),
            "update_frequency": s.get("update_frequency"),
            "why": "largest contribution to the current picture" + (", freshness below 0.5" if (w.get("components", {}).get("freshness") or 1) < 0.5 else ""),
        })
    reeval = ctx.today + timedelta(days=28)
    return {
        "watch": watch,
        "reevaluate_on": reeval.isoformat(),
        "reevaluate_reason": "[ASSUMPTION: monthly cadence; next TrendForce quarterly release and Fingrid Q3 report both fall inside this window]",
        "review_with": ["S&OP owner (demand review)", "Component procurement lead (memory, MCU allocation)", "Segment manager, data centres"],
        "open_questions": [
            "Which signals does the planner dispute? Disputes halve the weight and are logged.",
            "Does ABB's frame-order coverage (SIG-017) agree with the public end-demand signals once connected?",
        ],
    }


class ExplainerAgent:
    name = "Explainer agent"
    responsibility = "Writes the situation brief with citations and answers questions about the evidence."

    @_timed
    def run(self, ctx: Context) -> TraceStep:
        assert ctx.after is not None
        replay_key = (ctx.item or {}).get("replay_key")
        replayed = ctx.replay.get(replay_key, {}).get("brief") if replay_key else None
        notes: list[str] = []
        next_step = _next_analysis_step(ctx)
        text: str | None = None
        mode = "code"
        if ctx.llm.mode == "live":
            text, meta = ctx.llm.write(EXPLAIN_SYSTEM, f"NEW SIGNAL: {ctx.new_signal}\nSCENARIOS: {[{'id': s['id'], 'name': _t(s['name']), 'probability': s['probability'], 'for': s['evidence_for'], 'against': s['evidence_against']} for s in ctx.after['scenarios']]}\nBULLWHIP: {ctx.bullwhip and ctx.bullwhip['summary']}")
            if text:
                mode = "live"
        if text is None and replayed:
            text, mode = replayed, "replay"
        if text is None:
            text = build_brief(ctx)
        clean, removed = recommendation_filter(text)
        if removed:
            notes.append(f"Guardrail removed {len(removed)} sentence(s) with recommendation language.")
        ctx.brief = {"text": clean, "next_step": next_step, "generated_on": ctx.today.isoformat(), "mode": mode}
        return TraceStep(self.name, "ok", mode, "Situation brief and next analysis step produced; guardrail applied.", ctx.brief, notes=notes)


def build_brief(ctx: Context) -> str:
    """Template brief composed from computed numbers only (used when no LLM output exists)."""
    assert ctx.after is not None
    sc = sorted(ctx.after["scenarios"], key=lambda s: -s["probability"])
    lead = sc[0]
    second = sc[1]
    sig = ctx.new_signal
    parts = [
        f"Situation as of {ctx.today.isoformat()}. The most likely picture is '{_t(lead['name'])}' at {lead['probability']:.0%}, "
        f"followed by '{_t(second['name'])}' at {second['probability']:.0%}; spread across the four selected scenarios (entropy {ctx.after['entropy']:.2f}) "
        "means no scenario can be treated as settled.",
    ]
    if sig:
        parts.append(f"Latest input [{sig['id']}] ({sig.get('short')}) is classified {sig.get('classification')} with reliability {sig.get('reliability')}; "
                     f"its weight is {ctx.weights.get(sig['id'], {}).get('weight', 0):.2f} after counter-evidence and freshness.")
    if ctx.bullwhip:
        parts.append(f"Demand quality: {ctx.bullwhip['summary']}")
    top_for = lead["contributions"][:3]
    if top_for:
        parts.append("Strongest support for the leading scenario: " + "; ".join(f"[{c['signal_id']}] {c['signal_name']} ({c['contribution']:+.2f})" for c in top_for) + ".")
    against = [c for c in lead["contributions"] if c["contribution"] < 0][:2]
    if against:
        parts.append("Evidence against it: " + "; ".join(f"[{c['signal_id']}] {c['signal_name']} ({c['contribution']:+.2f})" for c in against) + ".")
    parts.append("The planner decides what this means for orders; the system shows the evidence and the alternatives.")
    return " ".join(parts)


# ----------------------------------------------------------------------------------
# Orchestrator
# ----------------------------------------------------------------------------------
class Pipeline:
    def __init__(self) -> None:
        self.collector = CollectorAgent()
        self.demand = SignalAgent("demand")
        self.supply = SignalAgent("supply")
        self.bullwhip = BullwhipAgent()
        self.counter = CounterEvidenceAgent()
        self.scenario = ScenarioAgent()
        self.interpret = InterpretationAgent()
        self.explain = ExplainerAgent()

    def describe(self) -> list[dict[str, str]]:
        return [{"name": a.name, "responsibility": a.responsibility} for a in
                (self.collector, self.demand, self.supply, self.bullwhip, self.counter, self.scenario, self.interpret, self.explain)]

    def run(self, ctx: Context, full: bool = True) -> Context:
        """full=False skips the interpretation and explainer agents (used for scouted items)."""
        k = float(ctx.scenario_config.get("scaling_k", 1.5))
        ctx.before = select_scenarios(ctx.scenario_config["archetypes"], ctx.signals, compute_weights(ctx.signals, ctx.evidence, ctx.today), k)
        self.collector.run(ctx)
        agent = self.supply if self.supply.applies(ctx) else self.demand
        agent.run(ctx)
        self.counter.run(ctx)
        self.bullwhip.run(ctx)
        self.scenario.run(ctx)
        if full:
            self.interpret.run(ctx)
            self.explain.run(ctx)
        return ctx
