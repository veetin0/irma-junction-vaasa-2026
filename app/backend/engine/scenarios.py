"""Deterministic scenario probability update.

Log-odds accumulation over weighted signal relevance, normalised with a softmax:

    L_s = ln(prior_s) + k * sum_i ( w_i * r_{i,s} )
    p_s = exp(L_s) / sum_t exp(L_t)

    w_i      signal weight from engine.weights (0..1)
    r_{i,s}  oriented relevance of signal i to scenario s, in [-1, 1], set on the
             signal card and visible to the user (positive = supports, negative = contradicts)
    k        scaling constant from scenarios.json (an explicit assumption)

The update is not a calibrated Bayesian posterior: r is an analyst-set log-likelihood
direction, not a measured likelihood ratio. The point is traceability: every unit of
probability can be decomposed into the signals that produced it.
"""
from __future__ import annotations

import math
from typing import Any


def scenario_contributions(signal: dict[str, Any], weight: float) -> dict[str, float]:
    links = signal.get("scenario_links", {})
    return {s: round(weight * float(r), 4) for s, r in links.items()}


def normalised_entropy(probabilities: list[float]) -> float:
    """0 = one scenario certain, 1 = all scenarios equally likely."""
    n = len(probabilities)
    if n <= 1:
        return 0.0
    h = -sum(p * math.log(p) for p in probabilities if p > 0)
    return round(h / math.log(n), 4)


def update_scenarios(
    scenarios: list[dict[str, Any]],
    signals: list[dict[str, Any]],
    weights: dict[str, dict[str, Any]],
    k: float = 2.0,
) -> dict[str, Any]:
    ids = [s["id"] for s in scenarios]
    log_odds = {s["id"]: math.log(max(1e-6, float(s.get("prior", 1.0 / len(ids))))) for s in scenarios}
    contributions: dict[str, list[dict[str, Any]]] = {sid: [] for sid in ids}

    for sig in signals:
        w = weights.get(sig["id"], {}).get("weight", 0.0)
        if w <= 0:
            continue
        for sid, c in scenario_contributions(sig, w).items():
            if sid not in log_odds or c == 0:
                continue
            log_odds[sid] += k * c
            contributions[sid].append({
                "signal_id": sig["id"],
                "signal_name": sig.get("short") or sig.get("name"),
                "weight": w,
                "relevance": sig.get("scenario_links", {}).get(sid, 0.0),
                "contribution": round(k * c, 4),
                "data_label": sig.get("data_label", "SOURCE"),
            })

    max_l = max(log_odds.values())
    exp_l = {sid: math.exp(l - max_l) for sid, l in log_odds.items()}
    total = sum(exp_l.values())
    probabilities = {sid: exp_l[sid] / total for sid in ids}

    out = []
    for sc in scenarios:
        sid = sc["id"]
        contribs = sorted(contributions[sid], key=lambda c: -abs(c["contribution"]))
        evidence_for = round(sum(c["contribution"] for c in contribs if c["contribution"] > 0), 4)
        evidence_against = round(sum(c["contribution"] for c in contribs if c["contribution"] < 0), 4)
        out.append({
            **sc,
            "log_odds": round(log_odds[sid], 4),
            "probability": round(probabilities[sid], 4),
            "contributions": contribs,
            "evidence_for": evidence_for,
            "evidence_against": evidence_against,
            "net": round(evidence_for + evidence_against, 4),
        })

    return {
        "scenarios": out,
        "entropy": normalised_entropy([probabilities[s] for s in ids]),
        "k": k,
        "formula": "L_s = ln(prior_s) + k * sum_i(w_i * r_is); p_s = softmax(L)",
    }


def probability_delta(before: dict[str, Any] | None, after: dict[str, Any]) -> list[dict[str, Any]]:
    """Per-scenario change between two update results, for the pipeline trace."""
    prev = {s["id"]: s["probability"] for s in (before or {}).get("scenarios", [])}
    rows = []
    for s in after["scenarios"]:
        p0 = prev.get(s["id"])
        name = s["name"]["en"] if isinstance(s.get("name"), dict) else s.get("name")
        rows.append({
            "id": s["id"],
            "name": name,
            "before": p0,
            "after": s["probability"],
            "delta": None if p0 is None else round(s["probability"] - p0, 4),
        })
    return rows
