"""Signal scout: searches the web for new signals on every update cycle and admits only strict, recent, relevant ones.

Two gates, both enforced by code:

    pre-gate  (on the discovery answer, before any further cost)
        the link is one of the pages the search tools returned, and the page was actually read or cited;
        the publisher is graded A (or A/B, per settings); a publication date exists and is within the age limit;
        the item belongs to a defined theme and states its mechanism; the quoted sentence is found in the
        retrieved text; the link and the headline are not already known.

    post-gate (after the verification, classification and counter-evidence agents ran on a copy of the data)
        a primary source corroborates the item; the card's reliability meets the minimum; the item moves at
        least one scenario theme; its computed weight after counter-evidence and freshness clears the minimum;
        it is not the same fact as an existing card; an update must be newer than the existing observation.

If no candidate passes both gates, nothing is added. Every decision is logged with its reason.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from agents.web import (DEFAULT_SCOUT_SETTINGS, THEMES, clean_date, domain_grade, norm_url, page_date,
                        quote_supported, title_similarity, verify_url)

SCOUT_SYSTEM = """You are the signal scout for Irma, a market-scenario monitor used by ABB's protection-relay business
(medium-voltage protection relays; output is limited by semiconductors and memory ordered about 18 months ahead).
Search the web for NEW items that act as signals for relay demand from data centres and grids in Finland, the
Nordics and Europe, or for the supply of the electronic components the relays need.

An item qualifies only if all of the following hold:
1. It reports a concrete new fact: a number, a decision, an agreement, a price, an order, a forecast or a published
   study. Commentary, opinion and marketing do not qualify.
2. It was published inside the date window given, and the page shows its publication date.
3. It comes from a reliable publisher: preferably the primary source (grid operator, regulator, company release or
   filing, statistics office, research institute), otherwise reputable press.
4. It belongs to one of the themes listed and changes the outlook through a mechanism you can state in one sentence.
5. It is not one of the existing signals or already reviewed links listed.

Read the page before proposing it, and quote the supporting sentence verbatim from the page. Never invent a URL, a
date or a number. If nothing qualifies, return [] - returning nothing is the correct answer when there is no good source.
Return only a JSON array, no prose, of at most N_MAX objects with these keys:
"title" (short factual headline), "source_url" (exact retrieved URL), "source_name" (publisher),
"published_date" ("YYYY-MM-DD"), "theme" (one theme key), "region" ("FI", "NORDICS", "EU", "US" or "GLOBAL"),
"summary" (two or three factual sentences), "quote" (one verbatim sentence from the page),
"why_signal" (one sentence on how it moves relay demand or component supply)."""

REASONS: dict[str, dict[str, str]] = {
    "link_not_retrieved": {"en": "The link was not among the pages the search returned.", "fi": "Linkki ei ollut haun palauttamien sivujen joukossa."},
    "page_not_read": {"en": "The page appeared in search results but was never read or cited.", "fi": "Sivu näkyi hakutuloksissa, mutta sitä ei luettu eikä lainattu."},
    "publisher_grade": {"en": "Publisher graded {grade}; the minimum is {min}.", "fi": "Julkaisijan luokka {grade}; vähimmäistaso on {min}."},
    "no_date": {"en": "No verifiable publication date.", "fi": "Ei tarkistettavaa julkaisupäivää."},
    "too_old": {"en": "Published {age} days ago; the limit is {max} days.", "fi": "Julkaistu {age} päivää sitten; raja on {max} päivää."},
    "outside_themes": {"en": "Does not belong to any of the defined themes.", "fi": "Ei kuulu mihinkään määritellyistä teemoista."},
    "no_signal_mechanism": {"en": "No stated mechanism linking it to relay demand or component supply.", "fi": "Ei esitettyä mekanismia, joka yhdistäisi sen relekysyntään tai komponenttien saatavuuteen."},
    "quote_not_in_retrieved_text": {"en": "The quoted sentence was not found in the retrieved page text.", "fi": "Lainattua lausetta ei löytynyt haetun sivun tekstistä."},
    "already_known": {"en": "The link is already used by a signal or was reviewed earlier.", "fi": "Linkki on jo käytössä signaalissa tai tarkistettu aiemmin."},
    "duplicate": {"en": "Same headline as {sid}.", "fi": "Sama otsikko kuin {sid}."},
    "over_limit": {"en": "Run limit of {n} candidates reached; left for the next run.", "fi": "Ajon {n} ehdokkaan raja täyttyi; jää seuraavaan ajoon."},
    "not_corroborated": {"en": "Not corroborated by a primary source.", "fi": "Ensisijainen lähde ei vahvistanut tietoa."},
    "reliability": {"en": "Card reliability {grade} is below the minimum {min}.", "fi": "Kortin luotettavuus {grade} alittaa vähimmäistason {min}."},
    "no_theme_load": {"en": "Moves no scenario theme enough (largest load {load}, minimum {min}).", "fi": "Ei liikuta mitään skenaarioteemaa riittävästi (suurin {load}, vähintään {min})."},
    "weight_too_low": {"en": "Weight {w} after counter-evidence and freshness is below {min}.", "fi": "Paino {w} vastanäytön ja tuoreuden jälkeen alittaa rajan {min}."},
    "same_fact": {"en": "The primary source already backs {sid}.", "fi": "Ensisijainen lähde tukee jo signaalia {sid}."},
    "not_newer": {"en": "Not newer than the existing observation on {sid}.", "fi": "Ei uudempi kuin signaalin {sid} nykyinen havainto."},
    "pipeline_error": {"en": "The checking agents failed: {error}.", "fi": "Tarkistavat agentit epäonnistuivat: {error}."},
    "accepted": {"en": "Passed every check and was added.", "fi": "Läpäisi kaikki tarkistukset ja lisättiin."},
}
SKIP_REASONS: dict[str, dict[str, str]] = {
    "world": {"en": "Automatic search runs only in the current world situation.", "fi": "Automaattinen haku toimii vain nykyisessä maailmantilanteessa."},
    "no_key": {"en": "No API key: automatic search is off and nothing is added.", "fi": "Ei API-avainta: automaattinen haku ei ole käytössä eikä mitään lisätä."},
    "web_off": {"en": "Web search is switched off in Settings.", "fi": "Verkkohaku on kytketty pois Asetuksista."},
    "scout_off": {"en": "Automatic search for new signals is switched off in Settings.", "fi": "Uusien signaalien automaattinen haku on kytketty pois Asetuksista."},
}


def reason(code: str, **kw: Any) -> dict[str, str]:
    t = REASONS.get(code, {"en": code, "fi": code})
    return {"code": code, "en": t["en"].format(**kw), "fi": t["fi"].format(**kw)}


def scout_settings(web: dict[str, Any] | None) -> dict[str, Any]:
    return {**DEFAULT_SCOUT_SETTINGS, **((web or {}).get("scout") or {})}


def allowed_grades(cfg: dict[str, Any]) -> set[str]:
    return {"A"} if str(cfg.get("min_grade", "B")).upper() == "A" else {"A", "B"}


def build_prompt(today: date, cfg: dict[str, Any], signals: list[dict[str, Any]], seen: dict[str, Any]) -> tuple[str, str]:
    since = today - timedelta(days=int(cfg["max_age_days"]))
    system = SCOUT_SYSTEM.replace("N_MAX", str(int(cfg["max_candidates"]) + 2))
    lines = [f"TODAY: {today.isoformat()}", f"DATE WINDOW: published on or after {since.isoformat()}", "THEMES:"]
    lines += [f"- {k}: {v}" for k, v in THEMES.items()]
    recent = sorted(signals, key=lambda s: s.get("observed_at") or "", reverse=True)[:40]
    lines.append("EXISTING SIGNALS (do not repeat them; a newer observation of one of them is welcome):")
    lines += [f"- {s.get('short') or s.get('name')} (last observed {s.get('observed_at') or 'n/a'})" for s in recent]
    reviewed = list(seen.keys())[-30:]
    if reviewed:
        lines.append("ALREADY REVIEWED LINKS (skip them):")
        lines += [f"- {u}" for u in reviewed]
    return system, "\n".join(lines)


def known_urls(signals: list[dict[str, Any]], evidence: list[dict[str, Any]], seen: dict[str, Any]) -> dict[str, str]:
    """Normalised URL -> what already uses it (signal id, evidence id or 'reviewed')."""
    out: dict[str, str] = {}
    for s in signals:
        for u in [(s.get("source") or {}).get("url"), ((s.get("verification") or {}).get("primary") or {}).get("url")]:
            if u:
                out.setdefault(norm_url(u), s["id"])
    for e in evidence:
        u = (e.get("source") or {}).get("url")
        if u:
            out.setdefault(norm_url(u), e.get("id", "evidence"))
    for k in seen:
        out.setdefault(k, "reviewed")
    return out


def pre_gate(cand: dict[str, Any], evidence: dict[str, Any], today: date, cfg: dict[str, Any], web: dict[str, Any],
             known: dict[str, str], signals: list[dict[str, Any]]) -> tuple[bool, dict[str, str], dict[str, Any]]:
    info: dict[str, Any] = {"url": cand.get("source_url") or "", "grade": None, "date": None}
    src = verify_url(cand.get("source_url"), evidence)
    if not src:
        return False, reason("link_not_retrieved"), info
    info["url"] = src["url"]
    if not ({"citation", "fetch"} & set(src.get("via", []))):
        return False, reason("page_not_read"), info
    grade = domain_grade(src["url"], web)
    info["grade"] = grade
    if grade not in allowed_grades(cfg):
        return False, reason("publisher_grade", grade=grade, min=str(cfg.get("min_grade", "B")).upper()), info
    pub = page_date(src.get("page_age"), today) or clean_date(cand.get("published_date"), today)
    if not pub:
        return False, reason("no_date"), info
    info["date"] = pub
    age = (today - date.fromisoformat(pub)).days
    info["age_days"] = age
    if age > int(cfg["max_age_days"]):
        return False, reason("too_old", age=age, max=int(cfg["max_age_days"])), info
    if cand.get("theme") not in THEMES:
        return False, reason("outside_themes"), info
    if len(str(cand.get("why_signal") or "").strip()) < 20:
        return False, reason("no_signal_mechanism"), info
    if not quote_supported(cand.get("quote"), src):
        return False, reason("quote_not_in_retrieved_text"), info
    if norm_url(src["url"]) in known:
        return False, reason("already_known"), info
    best = max(((title_similarity(str(cand.get("title", "")), s.get("name", "")), s["id"]) for s in signals), default=(0.0, None))
    if best[0] >= 0.75:
        return False, reason("duplicate", sid=best[1]), info
    return True, reason("accepted"), info


def post_gate(ctx: Any, cfg: dict[str, Any], weights: dict[str, Any], today: date,
              live_signals: list[dict[str, Any]], known: dict[str, str]) -> tuple[bool, dict[str, str]]:
    card = ctx.new_signal or {}
    v = card.get("verification") or {}
    if not v.get("corroborated") or not v.get("primary"):
        return False, reason("not_corroborated")
    if card.get("reliability") not in allowed_grades(cfg):
        return False, reason("reliability", grade=card.get("reliability"), min=str(cfg.get("min_grade", "B")).upper())
    load = max([abs(float(x)) for x in (card.get("axes") or {}).values()] or [0.0])
    if load < float(cfg["min_axis_load"]):
        return False, reason("no_theme_load", load=f"{load:.2f}", min=cfg["min_axis_load"])
    w = float(weights.get(card.get("id"), {}).get("weight", 0.0))
    if w < float(cfg["min_weight"]):
        return False, reason("weight_too_low", w=f"{w:.2f}", min=cfg["min_weight"])
    obs = clean_date(card.get("observed_at"), today)
    if not obs:
        return False, reason("no_date")
    age = (today - date.fromisoformat(obs)).days
    if age > int(cfg["max_age_days"]):
        return False, reason("too_old", age=age, max=int(cfg["max_age_days"]))
    if ctx.is_update:
        live = next((s for s in live_signals if s["id"] == card.get("id")), None)
        if live and (live.get("observed_at") or "") >= obs:
            return False, reason("not_newer", sid=card.get("id"))
    else:
        owner = known.get(norm_url(v["primary"]["url"]))
        if owner and owner != "reviewed":
            return False, reason("same_fact", sid=owner)
    return True, reason("accepted")
