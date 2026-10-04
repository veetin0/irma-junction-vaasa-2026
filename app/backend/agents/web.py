"""Web search support for the agents (Anthropic server-side web_search / web_fetch tools).

The model searches and reads pages on Anthropic's servers. This module turns what came
back into checkable evidence:

    * collect_web_evidence  lists every page the tools actually returned (search results,
                            fetched pages, citations) and every query that was run
    * verify_url            accepts a URL from the model's answer only if it is one of those
                            retrieved pages; anything else is treated as unverified
    * domain_grade          reliability A/B/C from the publisher's domain (primary sources A,
                            reputable press and research B, everything else C)

Code decides which links survive and how reliable they are; the model only proposes.
"""
from __future__ import annotations

import json
import re
from datetime import date, datetime
from typing import Any
from urllib.parse import urlsplit

WEB_SEARCH_TOOL = "web_search_20260209"
WEB_FETCH_TOOL = "web_fetch_20260209"
FETCH_MAX_CONTENT_TOKENS = 8000

# Primary publishers of the facts the signals rest on (grid operators, regulators,
# statistics, company filings and releases, research institutes): reliability A.
PRIMARY_DOMAINS = [
    "fingrid.fi", "energiavirasto.fi", "tem.fi", "valtioneuvosto.fi", "stat.fi",
    "entsoe.eu", "europa.eu", "iea.org", "energy.gov", "lbl.gov", "eia.gov", "sec.gov",
    "energinet.dk", "statnett.no", "svk.se", "tennet.eu", "eirgrid.ie", "nordpoolgroup.com",
    "lme.com", "trendforce.com", "abb.com", "micron.com", "fortum.com", "microsoft.com",
    "blog.google", "ember-energy.org", "uptimeinstitute.com", "semiconductors.org", "ecianow.org",
]
# Reputable press, trade press and research: reliability B.
# ft.com, hs.fi, kauppalehti.fi and reuters.com are not accessible to Anthropic's search tool; the API rejects
# requests that list them, so they are left out (the agents also drop such domains automatically if the API reports them).
SECONDARY_DOMAINS = [
    "bloomberg.com", "cnbc.com", "fortune.com", "yle.fi",
    "datacenterdynamics.com", "datacenterknowledge.com", "computerweekly.com", "globalspec.com", "mining.com",
    "globenewswire.com", "businesswire.com", "mckinsey.com", "goldmansachs.com", "koomey.com", "gridlab.org",
    "lut.fi", "aalto.fi", "vtt.fi",
]
# Themes a scouted item must belong to: each moves relay demand or component supply.
THEMES = {
    "data_centre_projects": "Data-centre projects, sites, capacity and grid connection agreements",
    "hyperscaler_investment": "Hyperscaler and operator capital expenditure and site investment",
    "grid_and_connections": "Transmission and distribution grid capacity, connection queues and grid rules",
    "energy_policy": "Regulation and policy affecting data centres, grids or electrification",
    "components_supply": "Semiconductors, memory and microcontrollers: prices, lead times, allocation, capacity",
    "commodity_prices": "Copper, electricity and other prices that change project economics",
    "electrification_equipment": "Orders, capacity and lead times for switchgear, transformers and protection equipment",
    "research_outlook": "Institutional research on data-centre electricity demand or grid investment",
}
DEFAULT_SCOUT_SETTINGS: dict[str, Any] = {
    "enabled": True,            # search for new signals on every update cycle
    "max_candidates": 3,        # candidates taken forward per run; each one costs a verification and a counter search
    "max_searches": 4,          # web searches in the discovery step
    "max_age_days": 30,         # older items are rejected
    "min_grade": "B",           # A only, or A and B
    "min_weight": 0.15,         # computed weight after counter-evidence and freshness
    "min_axis_load": 0.3,       # the item must move at least one scenario theme this much
}
DEFAULT_WEB_SETTINGS: dict[str, Any] = {
    "enabled": True,
    "max_searches": 3,          # per agent call; each search costs USD 0.01 plus tokens
    "max_fetches": 2,           # per agent call; no fee, page text counts as input tokens
    "allowed_domains": PRIMARY_DOMAINS + SECONDARY_DOMAINS,
    "primary_domains": PRIMARY_DOMAINS,
    "blocked_domains": [],      # domains the API reported as not accessible to its search tool
    "scout": dict(DEFAULT_SCOUT_SETTINGS),
}


def host_of(url: str | None) -> str:
    if not url:
        return ""
    try:
        return urlsplit(url.strip()).netloc.lower().split(":")[0].removeprefix("www.")
    except ValueError:
        return ""


def norm_url(url: str | None) -> str:
    """Comparable form: host without www, path without trailing slash, no scheme, query or fragment."""
    if not url:
        return ""
    try:
        p = urlsplit(url.strip())
    except ValueError:
        return ""
    return f"{p.netloc.lower().removeprefix('www.')}{p.path.rstrip('/')}"


def _matches(host: str, domains: list[str]) -> bool:
    return any(host == d or host.endswith("." + d) for d in domains)


def domain_grade(url: str | None, web: dict[str, Any] | None) -> str:
    host = host_of(url)
    if not host:
        return "C"
    cfg = web or DEFAULT_WEB_SETTINGS
    if _matches(host, cfg.get("primary_domains") or PRIMARY_DOMAINS):
        return "A"
    if _matches(host, cfg.get("allowed_domains") or []):
        return "B"
    return "C"


def parse_blocked_domains(message: str) -> list[str]:
    """Domains listed in the API error 'The following domains are not accessible to our user agent: [...]'."""
    m = re.search(r"not accessible to our user agent:\s*\[([^\]]*)\]", message or "")
    return re.findall(r"['\"]([^'\"]+)['\"]", m.group(1)) if m else []


def allowed_after_exclusion(web: dict[str, Any], extra_domains: list[str] | None = None, exclude: set[str] | None = None) -> list[str]:
    blocked = set(exclude or ()) | set(web.get("blocked_domains") or [])
    return [d for d in dict.fromkeys([d for d in (web.get("allowed_domains") or []) + (extra_domains or []) if d]) if d not in blocked]


def build_tools(web: dict[str, Any], extra_domains: list[str] | None = None, exclude: set[str] | None = None) -> list[dict[str, Any]]:
    domains = allowed_after_exclusion(web, extra_domains, exclude)
    search: dict[str, Any] = {"type": WEB_SEARCH_TOOL, "name": "web_search", "max_uses": int(web.get("max_searches", 3))}
    tools = [search]
    if int(web.get("max_fetches", 0)) > 0:
        tools.append({"type": WEB_FETCH_TOOL, "name": "web_fetch", "max_uses": int(web["max_fetches"]), "max_content_tokens": FETCH_MAX_CONTENT_TOKENS})
    if domains:
        for t in tools:
            t["allowed_domains"] = domains
    return tools


def _as_dict(block: Any) -> dict[str, Any]:
    if isinstance(block, dict):
        return block
    if hasattr(block, "model_dump"):
        return block.model_dump()
    return dict(getattr(block, "__dict__", {}))


def response_text(blocks: list[Any]) -> str:
    return "".join(_as_dict(b).get("text", "") for b in blocks if _as_dict(b).get("type") == "text")


def collect_web_evidence(blocks: list[Any]) -> dict[str, Any]:
    queries: list[dict[str, str]] = []
    sources: dict[str, dict[str, Any]] = {}
    errors: list[str] = []

    def add(url: str, **fields: Any) -> dict[str, Any]:
        key = norm_url(url)
        entry = sources.setdefault(key, {"url": url, "title": "", "page_age": None, "retrieved_at": None, "via": [], "cited": [], "text": ""})
        for k, v in fields.items():
            if k == "via":
                if v not in entry["via"]:
                    entry["via"].append(v)
            elif v and not entry.get(k):
                entry[k] = v
        return entry

    for raw in blocks:
        b = _as_dict(raw)
        kind = b.get("type")
        if kind == "server_tool_use":
            inp = b.get("input") or {}
            if b.get("name") == "web_search":
                queries.append({"tool": "web_search", "query": str(inp.get("query", ""))})
            elif b.get("name") == "web_fetch":
                queries.append({"tool": "web_fetch", "url": str(inp.get("url", ""))})
        elif kind == "web_search_tool_result":
            content = b.get("content")
            if isinstance(content, list):
                for r in content:
                    r = _as_dict(r)
                    if r.get("type") == "web_search_result" and r.get("url"):
                        add(r["url"], title=r.get("title") or "", page_age=r.get("page_age"), via="search")
            elif isinstance(content, dict):
                errors.append(f"web_search: {content.get('error_code')}")
        elif kind == "web_fetch_tool_result":
            content = _as_dict(b.get("content") or {})
            if content.get("type") == "web_fetch_result" and content.get("url"):
                doc = _as_dict(content.get("content") or {})
                src = _as_dict(doc.get("source") or {})
                page_text = str(src.get("data") or "")[:40000] if src.get("type") == "text" else ""
                add(content["url"], title=doc.get("title") or "", retrieved_at=content.get("retrieved_at"), via="fetch", text=page_text)
            else:
                errors.append(f"web_fetch: {content.get('error_code')}")
        elif kind == "text":
            for cit in b.get("citations") or []:
                cit = _as_dict(cit)
                if cit.get("type") == "web_search_result_location" and cit.get("url"):
                    entry = add(cit["url"], title=cit.get("title") or "", via="citation")
                    if cit.get("cited_text"):
                        entry["cited"].append(str(cit["cited_text"])[:300])
    return {"queries": queries, "sources": list(sources.values()), "errors": errors}


def verify_url(url: str | None, evidence: dict[str, Any] | None) -> dict[str, Any] | None:
    """Return the retrieved source entry for this URL, or None if the tools never returned it."""
    if not url or not evidence:
        return None
    key = norm_url(url)
    return next((s for s in evidence.get("sources", []) if norm_url(s["url"]) == key), None)


def extract_json(text: str | None, kind: str = "array") -> Any:
    """Last well-formed JSON array (or object) in the text; None if there is none."""
    if not text:
        return None
    opener, closer = ("[", "]") if kind == "array" else ("{", "}")
    found = None
    starts = [m.start() for m in re.finditer(re.escape(opener), text)]
    for start in starts:
        depth, in_str, esc = 0, False, False
        for i in range(start, len(text)):
            ch = text[i]
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
                continue
            if ch == '"':
                in_str = True
            elif ch == opener:
                depth += 1
            elif ch == closer:
                depth -= 1
                if depth == 0:
                    try:
                        found = json.loads(text[start:i + 1])
                    except json.JSONDecodeError:
                        pass
                    break
    return found


def clean_date(value: Any, today: date) -> str:
    """YYYY-MM-DD not in the future, or ''. Accepts ISO dates and 'Month D, YYYY' page ages."""
    if not value:
        return ""
    s = str(value).strip()
    for fmt in ("%Y-%m-%d", "%B %d, %Y", "%b %d, %Y", "%d %B %Y"):
        try:
            d = datetime.strptime(s[:len(s) if fmt != "%Y-%m-%d" else 10], fmt).date()
            return d.isoformat() if d <= today else ""
        except ValueError:
            continue
    return ""


def clamp01(x: Any, default: float = 0.3) -> float:
    try:
        return max(0.0, min(1.0, float(x)))
    except (TypeError, ValueError):
        return default


_REL = re.compile(r"^(\d+)\s+(minute|hour|day|week|month|year)s?\s+ago$", re.IGNORECASE)


def page_date(value: Any, today: date) -> str:
    """Publication date from a search result's page_age: absolute dates or 'N days ago'."""
    if not value:
        return ""
    m = _REL.match(str(value).strip())
    if m:
        n, unit = int(m.group(1)), m.group(2).lower()
        days = {"minute": 0, "hour": 0, "day": n, "week": 7 * n, "month": 30 * n, "year": 365 * n}[unit]
        from datetime import timedelta
        return (today - timedelta(days=days)).isoformat()
    return clean_date(value, today)


def _norm_text(s: str) -> str:
    s = (s or "").lower().replace("\u2019", "'").replace("\u2018", "'").replace("\u201c", '"').replace("\u201d", '"')
    s = s.replace("\u2013", "-").replace("\u2014", "-")
    return re.sub(r"\s+", " ", s).strip()


def _tokens(s: str) -> list[str]:
    return re.findall(r"[a-z0-9\u00e4\u00f6\u00e5]{3,}", _norm_text(s))


def quote_supported(quote: str | None, source: dict[str, Any] | None) -> bool:
    """True if the quote is found in text the tools returned for this page (citations or fetched text)."""
    if not quote or not source:
        return False
    corpus = _norm_text(" ".join(source.get("cited", [])) + " " + (source.get("text") or ""))
    if not corpus.strip():
        return False
    q = _norm_text(quote)
    if len(q) >= 12 and q in corpus:
        return True
    qt = _tokens(q)
    if len(qt) < 4:
        return False
    ct = set(_tokens(corpus))
    return sum(1 for t in qt if t in ct) / len(qt) >= 0.8


def title_similarity(a: str, b: str) -> float:
    ta, tb = set(_tokens(a)), set(_tokens(b))
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)
