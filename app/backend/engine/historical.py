"""Historical comparison: what the formulas would have shown at past dates, next to what happened.

Everything here is the same code that runs on today's data. Nothing is tuned to the past.

    signals_as_of(dataset, d)   only what had been published on or before d (no hindsight):
                                cards with observed_at <= d, history points <= d, counter-evidence,
                                corroboration and annotations dated <= d. Undated items are excluded.
    snapshot(dataset, d)        weights (engine.weights ensemble, today=d) and the scenario shares
                                (engine.archetypes.select_scenarios) for that date.
    compare(dataset)            one row per snapshot date: weights and shares next to the recorded
                                outcome. Outcomes are shown, never used in the computation.

The comparison is illustrative. It is not a validation of the method and it is not a forecast:
a handful of snapshot dates in one cycle cannot establish accuracy, and the scenario pool was
written after the fact by people who know the outcome.

Dataset layout (data/historical/chipcycle.json):
    signals | points | cards   list of signal cards (observed_at = publication date)
    evidence | counter_evidence list of counter-evidence cards (source.date)
    snapshots                   list of ISO dates
    outcomes                    [{"after": date, "text": {en, fi}, "source": {name, url, date}}]
    archetypes, scaling_k       optional; default to data/scenario_archetypes.json
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from engine.archetypes import select_scenarios
from engine.weights import compute_weights, parse_date

LABEL = {
    "en": "illustrative comparison, not validation and not a forecast",
    "fi": "havainnollistava vertailu, ei validointi eikä ennuste",
}
TOP_N = 5
_DEFAULT_ARCHETYPES = Path(__file__).resolve().parents[1] / "data" / "scenario_archetypes.json"


def _as_date(d: date | str) -> date:
    if isinstance(d, date):
        return d
    parsed = parse_date(d)
    if parsed is None:
        raise ValueError(f"not an ISO date: {d!r}")
    return parsed


def _cards(dataset: dict[str, Any]) -> list[dict[str, Any]]:
    for key in ("signals", "points", "cards"):
        if dataset.get(key):
            return dataset[key]
    return []


def _evidence(dataset: dict[str, Any]) -> list[dict[str, Any]]:
    return dataset.get("evidence") or dataset.get("counter_evidence") or []


def _known_by(item_dates: list[str | None], d: date) -> bool:
    """True when every date is a real date on or before d. An undated item cannot be shown to pre-date d."""
    parsed = [parse_date(x) for x in item_dates]
    return bool(parsed) and all(p is not None and p <= d for p in parsed)


def _card_known(card: dict[str, Any], d: date) -> bool:
    dates = [card.get("observed_at")]
    src_date = (card.get("source") or {}).get("date")
    if src_date:
        dates.append(src_date)
    return _known_by(dates, d)


def signals_as_of(dataset: dict[str, Any], as_of: date | str) -> dict[str, Any]:
    """The state of knowledge at `as_of`: {"as_of", "signals", "evidence"}. Copies; the dataset is untouched."""
    d = _as_date(as_of)
    evidence = [dict(ce) for ce in _evidence(dataset) if _known_by([(ce.get("source") or {}).get("date")], d)]
    kept_ce = {ce["id"] for ce in evidence}
    signals = []
    for card in _cards(dataset):
        if not _card_known(card, d):
            continue
        c = dict(card)
        c["history"] = [p for p in card.get("history") or [] if _known_by([p.get("date")], d)]
        c["counter_evidence"] = [i for i in card.get("counter_evidence") or [] if i in kept_ce]
        if "corroboration" in card:
            c["corroboration"] = [x for x in card["corroboration"] or [] if _known_by([x.get("date")], d)]
        c["annotations"] = [a for a in card.get("annotations") or [] if _known_by([a.get("at") or a.get("date")], d)]
        signals.append(c)
    return {"as_of": d.isoformat(), "signals": signals, "evidence": evidence}


def _archetypes(dataset: dict[str, Any]) -> tuple[list[dict[str, Any]], float]:
    if dataset.get("archetypes"):
        return dataset["archetypes"], float(dataset.get("scaling_k", 1.5))
    cfg = json.loads(_DEFAULT_ARCHETYPES.read_text(encoding="utf-8"))
    return cfg["archetypes"], float(dataset.get("scaling_k", cfg.get("scaling_k", 1.5)))


def _top_weights(signals: list[dict[str, Any]], weights: dict[str, Any], n: int = TOP_N) -> list[dict[str, Any]]:
    ranked = sorted(signals, key=lambda s: (-weights[s["id"]]["weight"], s["id"]))
    return [{"id": s["id"], "short": s.get("short") or s.get("name"), "weight": round(weights[s["id"]]["weight"], 4)}
            for s in ranked[:n] if weights[s["id"]]["weight"] > 0]


def snapshot(dataset: dict[str, Any], as_of: date | str) -> dict[str, Any]:
    """Weights and scenario shares computed only from what was known at `as_of`."""
    d = _as_date(as_of)
    known = signals_as_of(dataset, d)
    signals, evidence = known["signals"], known["evidence"]
    weights = compute_weights(signals, evidence, d)
    probabilities: dict[str, float] = {}
    leader = None
    if signals:
        archetypes, k = _archetypes(dataset)
        sc = select_scenarios(archetypes, signals, weights, k)
        ranked = sorted(sc["scenarios"], key=lambda s: -s["probability"])
        probabilities = {s["id"]: s["probability"] for s in ranked}
        leader = {"id": ranked[0]["id"], "name": ranked[0]["name"], "probability": ranked[0]["probability"]}
    return {"as_of": d.isoformat(), "n_signals": len(signals), "n_evidence": len(evidence),
            "top_weights": _top_weights(signals, weights), "leader": leader, "probabilities": probabilities}


def outcome_for(dataset: dict[str, Any], as_of: date | str) -> dict[str, Any] | None:
    """What happened next: the outcome recorded for this date, else the latest one recorded for an earlier date."""
    d = _as_date(as_of)
    dated = [(parse_date(o.get("after")), o) for o in dataset.get("outcomes") or []]
    dated = [(a, o) for a, o in dated if a is not None and a <= d]
    if not dated:
        return None
    o = max(dated, key=lambda x: x[0])[1]
    return {"after": o.get("after"), "text": o.get("text"), "source": o.get("source")}


def compare(dataset: dict[str, Any], current: dict[str, Any] | None = None) -> dict[str, Any]:
    """Per snapshot date: weights and scenario shares from the formulas, and the recorded outcome.

    `current` is an optional {"as_of", "top_weights", "leader"} for today's state, supplied by the caller.
    """
    rows = []
    for s in dataset.get("snapshots") or []:
        snap = snapshot(dataset, s)
        snap["outcome"] = outcome_for(dataset, s)
        rows.append(snap)
    return {"label": dict(LABEL), "rows": rows, "today": current}


def validate(dataset: dict[str, Any]) -> list[str]:
    """Problems that break the no-hindsight rule or the labelling rule. Empty list = fine."""
    problems = []
    for c in _cards(dataset):
        cid = c.get("id", "?")
        if parse_date(c.get("observed_at")) is None:
            problems.append(f"{cid}: observed_at missing or not a date")
        if not (c.get("source") or {}).get("url") and c.get("data_label") != "DEMODATA":
            problems.append(f"{cid}: no source URL and not labelled DEMODATA")
    for ce in _evidence(dataset):
        if parse_date((ce.get("source") or {}).get("date")) is None:
            problems.append(f"{ce.get('id', '?')}: evidence has no source date")
    for o in dataset.get("outcomes") or []:
        if not (o.get("source") or {}).get("url"):
            problems.append(f"outcome after {o.get('after')}: no source")
    return problems
