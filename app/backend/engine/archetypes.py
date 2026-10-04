"""Scenario generation per run.

The four scenarios shown are not fixed. A pool of candidate situations (archetypes) is
scored against the current weighted signals on six axes, and the four most likely are
selected for the run. Every number here is computed by code; a language model may
rewrite the texts, never the scores.

    axes               demand, supply, policy, price, nordic, bullwhip  (each in [-1, 1])
    signal.axes        how the observation loads on each axis (set on the card, visible)
    archetype.profile  what the situation would look like on each axis
    r(signal, arch)    sum_a axes_a * profile_a / sum_a |profile_a|, clamped to [-1, 1]
    L_arch             ln(prior) + k * sum_i w_i * r_i  (engine.scenarios.update_scenarios)
    selection          the four archetypes with the highest L; probabilities renormalised over the four
"""
from __future__ import annotations

import copy
import math
from typing import Any

from engine.scenarios import update_scenarios

AXES = ["demand", "supply", "policy", "price", "nordic", "bullwhip"]


def relevance(signal_axes: dict[str, float] | None, profile: dict[str, float]) -> float:
    if not signal_axes:
        return 0.0
    norm = sum(abs(float(profile.get(a, 0.0))) for a in AXES) or 1.0
    dot = sum(float(signal_axes.get(a, 0.0)) * float(profile.get(a, 0.0)) for a in AXES)
    return round(max(-1.0, min(1.0, dot / norm)), 4)


def attach_links(signals: list[dict[str, Any]], archetypes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return signal copies whose scenario_links are computed from axes against every archetype."""
    out = []
    for s in signals:
        c = dict(s)
        c["scenario_links"] = {a["id"]: relevance(s.get("axes"), a["profile"]) for a in archetypes}
        out.append(c)
    return out


def select_scenarios(archetypes: list[dict[str, Any]], signals: list[dict[str, Any]], weights: dict[str, Any], k: float = 1.0, n: int = 4) -> dict[str, Any]:
    linked = attach_links(signals, archetypes)
    full = update_scenarios(archetypes, linked, weights, k)
    ranked = sorted(full["scenarios"], key=lambda s: -s["log_odds"])
    chosen = ranked[:n]
    total = sum(s["probability"] for s in chosen) or 1.0
    for s in chosen:
        s["probability_all"] = s["probability"]
        s["probability"] = round(s["probability"] / total, 4)
        s["path"] = scenario_path(s)
    probs = [s["probability"] for s in chosen]
    entropy = -sum(p * math.log(p) for p in probs if p > 0) / math.log(len(probs)) if len(probs) > 1 else 0.0
    return {
        "scenarios": chosen,
        "candidates": [{"id": s["id"], "name": s["name"], "log_odds": s["log_odds"], "probability_all": s["probability"], "selected": s["id"] in {c["id"] for c in chosen}} for s in ranked],
        "entropy": round(entropy, 4),
        "k": k,
        "formula": full["formula"] + "; the four highest L are selected and renormalised",
    }


def scenario_path(arch: dict[str, Any], months: int = 36) -> dict[str, Any]:
    """Illustrative relative index paths (100 = today) for demand and deliverable supply. Not a forecast."""
    p = arch.get("path", {})
    dg = p.get("demand_yearly", [0.0, 0.0, 0.0])
    sg = p.get("supply_yearly", [0.0, 0.0, 0.0])
    band = float(p.get("band", 0.1))
    demand, supply, upper, lower = [], [], [], []
    d = s = 100.0
    for m in range(0, months + 1):
        if m > 0:
            year = min(2, (m - 1) // 12)
            d *= (1.0 + float(dg[year])) ** (1.0 / 12.0)
            s *= (1.0 + float(sg[year])) ** (1.0 / 12.0)
        spread = d * band * math.sqrt(m / 12.0)
        demand.append(round(d, 1)); supply.append(round(s, 1)); upper.append(round(d + spread, 1)); lower.append(round(max(0.0, d - spread), 1))
    return {"months": list(range(0, months + 1)), "demand": demand, "supply": supply, "upper": upper, "lower": lower,
            "label": "ASSUMPTION", "note": {"en": "Illustrative scenario path, index 100 = today. It depicts the scenario, it is not a forecast.",
                                              "fi": "Havainnollistava skenaariopolku, indeksi 100 = tänään. Kuvaa skenaarion, ei ole ennuste."}}


def axis_scores(signals: list[dict[str, Any]], weights: dict[str, Any]) -> dict[str, float]:
    tot = sum(weights.get(s["id"], {}).get("weight", 0.0) for s in signals) or 1.0
    return {a: round(sum(weights.get(s["id"], {}).get("weight", 0.0) * float((s.get("axes") or {}).get(a, 0.0)) for s in signals) / tot, 4) for a in AXES}


def plain_summary(selected: dict[str, Any], signals: list[dict[str, Any]], weights: dict[str, Any], lang: str) -> str:
    """Short, plain-language situation summary. No technical terms."""
    sc = axis_scores(signals, weights)
    lead = selected["scenarios"][0]
    by_id = {s["id"]: s for s in signals}
    watch = [c for c in lead["contributions"][:3]]
    names = [by_id[c["signal_id"]].get("short_fi" if lang == "fi" else "short", c["signal_name"]) for c in watch if c["signal_id"] in by_id][:2]
    d, s = sc["demand"], sc["supply"]
    if lang == "fi":
        demand_txt = "kasvaa edelleen" if d > 0.12 else ("laskee" if d < -0.12 else "pysyy tasaisena")
        supply_txt = "on edelleen vaikea saada" if s > 0.05 else ("on helpompi saada kuin aiemmin" if s < -0.05 else "saa kohtalaisesti")
        return (f"Datakeskusten sähkölaitteiden kysyntä Pohjoismaissa {demand_txt}. Piirejä ja muisteja {supply_txt}. "
                f"Todennäköisin kehitys seuraavien 1–3 vuoden aikana: {lead['name']['fi']} ({lead['probability']:.0%}). "
                + (f"Tärkeimmät seurattavat asiat juuri nyt: {' ja '.join(names)}." if names else ""))
    demand_txt = "is still growing" if d > 0.12 else ("is falling" if d < -0.12 else "is flat")
    supply_txt = "are still hard to get" if s > 0.05 else ("are easier to get than before" if s < -0.05 else "are moderately available")
    return (f"Demand for power equipment from data centres in the Nordics {demand_txt}. Chips and memory {supply_txt}. "
            f"The most likely path for the next 1–3 years: {lead['name']['en']} ({lead['probability']:.0%}). "
            + (f"The main things to watch right now: {' and '.join(names)}." if names else ""))
