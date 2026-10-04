"""Deterministic signal weighting.

Every number here is computed by code, never by a language model. The LLM agents
read and classify text into the card fields (reliability, strength, direction,
classification); this module turns those fields into a weight with a formula the
user can inspect on the signal card.

    w = R * F * S * (1 - C) * H

    R  reliability grade        A = 1.0, B = 0.7, C = 0.4
    F  freshness                0.5 ** (age_days / half_life_days), half-life by update frequency
    S  strength                 0..1 as classified (size of the move relative to its own history)
    C  counter-evidence penalty min(0.8, 1 - prod over linked counter-evidence of (1 - R_ce * strength_ce))
                                (noisy-OR: two counter-claims making the same point do not stack linearly)
    H  human factor             product of annotation multipliers, clamped to [0.25, 1.5]

A signal that has never been challenged by the counter-evidence agent is capped at
0.6 so that an unexamined claim can never dominate a scenario.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Any

RELIABILITY = {"A": 1.0, "B": 0.7, "C": 0.4}
HALF_LIFE_DAYS = {
    "daily": 14,
    "weekly": 30,
    "monthly": 60,
    "quarterly": 120,
    "annual": 240,
    "event": 90,
}
COUNTER_CAP = 0.8
UNCHALLENGED_CAP = 0.6
HUMAN_MULTIPLIERS = {"confirm": 1.2, "dispute": 0.5, "comment": 1.0}
HUMAN_MIN, HUMAN_MAX = 0.25, 1.5


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.strptime(value[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def age_days(observed_at: str | None, today: date) -> int | None:
    observed = parse_date(observed_at)
    if observed is None:
        return None
    return max(0, (today - observed).days)


def freshness(observed_at: str | None, today: date, update_frequency: str) -> float:
    """Exponential decay with a half-life tied to how often the source updates."""
    age = age_days(observed_at, today)
    if age is None:
        return 0.0
    half_life = HALF_LIFE_DAYS.get(update_frequency, 90)
    return round(0.5 ** (age / half_life), 4)


def counter_penalty(signal: dict[str, Any], evidence_by_id: dict[str, dict[str, Any]]) -> float:
    survive = 1.0
    for ce_id in signal.get("counter_evidence", []):
        ce = evidence_by_id.get(ce_id)
        if not ce:
            continue
        survive *= 1.0 - RELIABILITY.get(ce.get("reliability", "C"), 0.4) * float(ce.get("strength", 0.0))
    return round(min(COUNTER_CAP, 1.0 - survive), 4)


def human_factor(annotations: list[dict[str, Any]]) -> float:
    factor = 1.0
    for note in annotations or []:
        factor *= HUMAN_MULTIPLIERS.get(note.get("action", "comment"), 1.0)
    return round(max(HUMAN_MIN, min(HUMAN_MAX, factor)), 4)


def signal_weight(
    signal: dict[str, Any],
    evidence_by_id: dict[str, dict[str, Any]],
    today: date,
) -> dict[str, Any]:
    r = RELIABILITY.get(signal.get("reliability", "C"), 0.4)
    f = freshness(signal.get("observed_at"), today, signal.get("update_frequency", "event"))
    s = max(0.0, min(1.0, float(signal.get("strength", 0.0))))
    c = counter_penalty(signal, evidence_by_id)
    h = human_factor(signal.get("annotations", []))
    raw = r * f * s * (1.0 - c) * h
    capped = False
    if not signal.get("ce_searched", False) and raw > UNCHALLENGED_CAP:
        raw = UNCHALLENGED_CAP
        capped = True
    return {
        "weight": round(raw, 4),
        "components": {
            "reliability": r,
            "freshness": f,
            "strength": s,
            "counter_penalty": c,
            "human": h,
        },
        "age_days": age_days(signal.get("observed_at"), today),
        "unchallenged_cap_applied": capped,
        "formula": "w = R * F * S * (1 - C) * H",
    }


def compute_weights(
    signals: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
    today: date,
) -> dict[str, dict[str, Any]]:
    evidence_by_id = {ce["id"]: ce for ce in evidence}
    return {sig["id"]: signal_weight(sig, evidence_by_id, today) for sig in signals}
