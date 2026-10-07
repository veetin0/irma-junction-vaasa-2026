"""Deterministic signal weighting: an ensemble of four conditions and a horizon fit.

Every number here is computed by code, never by a language model. The LLM agents read
and classify text into card fields (reliability grade, strength, direction, classification,
lead time, corroborating sources); this module turns those fields into a weight that the
user can inspect on the signal card.

    w   = min(1, Bel × F × M × H)            headline weight, then the unchallenged cap
    w_h = w × T(h)                           horizon weight for h in 12 / 24 / 36 months

Rule: multiply conditions that must all hold (true AND current AND material AND not
disputed), average estimators of the same quantity. Equal weights inside an average,
because there is no outcome data to fit them on (the forecast-combination puzzle).

    Bel  credibility   Dempster-Shafer belief that the claim is true, on the frame {true, false}.
                       support  s = 1 - (1 - R) × prod_j (1 - R_j) over the primary source and
                                every *independent* corroborating source (noisy-OR, which is
                                Dempster's rule on simple support functions; R from the A/B/C grade)
                       attack   c = min(0.8, 1 - prod over counter-evidence of (1 - R_ce × strength_ce))
                       Bel = s × (1 - c)   (Yager's rule: the conflict s × c goes to "unknown")
                       Pl  = 1 - c × (1 - s)   (upper bound, shown as a band)
                       With one source this is exactly the old R × (1 - C).
    F    currency      0.5 ** (age_days / half_life_days), half-life by update frequency
    M    materiality   mean of the available estimators of "how big is the move":
                         S    strength as classified on the card (always present)
                         S_z  min(1, |z_mod| / 3.5), robust z-score of the last move against the
                              earlier moves; only when history_label == "SOURCE" and there are
                              enough earlier moves, never from DEMODATA history
                       With no SOURCE history M = S, so the weight equals the old formula.
    H    human view    product of annotation multipliers (confirm 1.2, dispute 0.5), clamped [0.25, 1.5]
    T(h) horizon fit   log-normal kernel on lead_months L:  exp(-0.5 × (ln(h / L) / s)²)
                       before the effect arrives (h < L); once it has arrived a structural effect
                       persists (T = 1), a cyclical one fades with the kernel, a mixed one is halfway.

A signal never examined by the counter-evidence agent is capped at 0.6 so an unexamined
claim can never dominate a scenario. The cap is applied after the product, before the
horizon factor, so w_h <= w holds at every horizon.

Alongside the headline weight each card carries:
    band         the same four factors combined by product (= w), minimum, geometric and
                 arithmetic mean: the spread is the structural uncertainty of the aggregation
    attribution  share of the discount from 1.0 per component, ln(1/c_k) / sum ln(1/c_k)
                 (order-independent; a human boost above 1 shows as a negative share)
    assumptions  every ASSUMPTION constant that produced the number, with its justification
"""
from __future__ import annotations

import math
from datetime import date, datetime
from statistics import median
from typing import Any
from urllib.parse import urlparse

# ---- constants (all labelled; see ASSUMPTIONS below for the reasons) -------------------
RELIABILITY = {"A": 1.0, "B": 0.7, "C": 0.4}            # ASSUMPTION: no standard maps Admiralty letters to numbers
HALF_LIFE_DAYS = {                                     # ASSUMPTION: tied to how often the source publishes
    "daily": 14,
    "weekly": 30,
    "monthly": 60,
    "quarterly": 120,
    "annual": 240,
    "event": 90,
}
COUNTER_CAP = 0.8                                      # ASSUMPTION: one doubt never erases more than 80 % of belief
UNCHALLENGED_CAP = 0.6                                 # ASSUMPTION: an unexamined claim cannot dominate
HUMAN_MULTIPLIERS = {"confirm": 1.2, "dispute": 0.5, "comment": 1.0}   # ASSUMPTION
HUMAN_MIN, HUMAN_MAX = 0.25, 1.5                       # ASSUMPTION
WEIGHT_MAX = 1.0                                       # definition: a weight lives in [0, 1]

Z_CONSTANT = 0.6745                                    # SOURCE: Iglewicz and Hoaglin modified z-score (NIST e-Handbook 1.3.5.17)
Z_OUTLIER = 3.5                                        # SOURCE: same, published outlier threshold
Z_MIN_PRIOR_MOVES = 6                                  # ASSUMPTION: the MAD is unstable on shorter series

HORIZONS = (12, 24, 36)                                # months; the archetype paths have three yearly buckets
KERNEL_WIDTH = math.log(2)                             # ASSUMPTION: log-normal width s, see ASSUMPTIONS
PERSISTENCE = ("structural", "cyclical", "mixed")      # ASSUMPTION: rule below, see ASSUMPTIONS

FORMULA = "w = min(1, Bel × F × M × H); w_h = w × T(h)"
COMPONENTS = ("credibility", "currency", "materiality", "human")
LABEL_ORDER = {"SOURCE": 0, "DEMODATA": 1, "ASSUMPTION": 2}   # worst label wins

ASSUMPTIONS: list[dict[str, Any]] = [
    {"name": "reliability_grades", "value": "A=1.0, B=0.7, C=0.4", "label": "ASSUMPTION",
     "why": "Admiralty-style source grading; no standard assigns numbers to the letters, so a linear-ish map is used and shown."},
    {"name": "counter_cap", "value": COUNTER_CAP, "label": "ASSUMPTION",
     "why": "Counter-evidence keeps at least 20 % of the belief so that one doubt cannot erase a sourced signal."},
    {"name": "unchallenged_cap", "value": UNCHALLENGED_CAP, "label": "ASSUMPTION",
     "why": "A claim the counter-evidence agent has not examined cannot dominate a scenario."},
    {"name": "human_multipliers", "value": "confirm x1.2, dispute x0.5, clamp [0.25, 1.5]", "label": "ASSUMPTION",
     "why": "The planner's view moves the weight visibly but cannot replace the evidence."},
    {"name": "equal_estimator_weights", "value": "mean", "label": "ASSUMPTION",
     "why": "Several estimators of one quantity are averaged with equal weights: there is no outcome data to fit weights on (forecast-combination puzzle, Smith and Wallis 2009)."},
    {"name": "z_min_prior_moves", "value": float(Z_MIN_PRIOR_MOVES), "label": "ASSUMPTION",
     "why": "The robust z-score needs a stable median absolute deviation; with fewer earlier moves the estimator is skipped, not defaulted."},
    {"name": "corroboration_independence", "value": "different publisher domain and no derived_from", "label": "ASSUMPTION",
     "why": "Cheap proxy for circular reporting: syndicated copies of one release count as one source."},
    {"name": "horizon_kernel_width", "value": round(KERNEL_WIDTH, 4), "label": "ASSUMPTION",
     "why": "s = ln 2: the median high/low ratio of the eight lead-time ranges quoted on the cards is 2, and analysts' ranges are usually too narrow (Soll and Klayman 2004), so the kernel is not narrower than that. ln 1.5 and ln 3 are the sensitivity bounds; the 36-month leader is not robust to them."},
    {"name": "horizon_persistence", "value": "structural 1, cyclical T, mixed (1+T)/2 after arrival", "label": "ASSUMPTION",
     "why": "Once a structural effect has reached ABB demand or supply it stays; a cyclical one fades as the horizon moves past its lead time; mixed is halfway."},
    {"name": "horizon_missing_lead", "value": 1.0, "label": "ASSUMPTION",
     "why": "A card without a lead time carries no timing information, so it is horizon-neutral (T = 1) rather than guessed."},
]


# ---- helpers ------------------------------------------------------------------------------
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


def _domain(url: str | None) -> str | None:
    if not url:
        return None
    host = urlparse(url).netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    return host or None


def _worst(labels: list[str]) -> str:
    return max(labels, key=lambda lab: LABEL_ORDER.get(lab, 2)) if labels else "ASSUMPTION"


# ---- component 2: currency ----------------------------------------------------------------
def freshness(observed_at: str | None, today: date, update_frequency: str) -> float:
    """Exponential decay with a half-life tied to how often the source updates."""
    age = age_days(observed_at, today)
    if age is None:
        return 0.0
    half_life = HALF_LIFE_DAYS.get(update_frequency, 90)
    return round(0.5 ** (age / half_life), 4)


# ---- component 1: credibility --------------------------------------------------------------
def counter_penalty(signal: dict[str, Any], evidence_by_id: dict[str, dict[str, Any]]) -> float:
    """Noisy-OR over linked counter-evidence (Dempster combination of simple support functions)."""
    survive = 1.0
    for ce_id in signal.get("counter_evidence", []):
        ce = evidence_by_id.get(ce_id)
        if not ce:
            continue
        survive *= 1.0 - RELIABILITY.get(ce.get("reliability", "C"), 0.4) * float(ce.get("strength", 0.0))
    return round(min(COUNTER_CAP, 1.0 - survive), 4)


def independent_corroboration(signal: dict[str, Any]) -> list[dict[str, Any]]:
    """Corroborating sources that count: graded, with a URL on a new publisher domain, not derived from another."""
    seen = {d for d in [_domain((signal.get("source") or {}).get("url"))] if d}
    out = []
    for c in signal.get("corroboration") or []:
        grade = c.get("reliability")
        dom = _domain(c.get("url"))
        if grade not in RELIABILITY or dom is None or c.get("derived_from") or dom in seen:
            continue
        seen.add(dom)
        out.append({"name": c.get("name"), "url": c.get("url"), "reliability": grade, "r": RELIABILITY[grade]})
    return out


def credibility(signal: dict[str, Any], evidence_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Belief and plausibility that the card's claim is true."""
    r = RELIABILITY.get(signal.get("reliability", "C"), 0.4)
    corr = independent_corroboration(signal)
    if corr:
        miss = 1.0 - r
        for c in corr:
            miss *= 1.0 - c["r"]
        support = 1.0 - miss
    else:
        support = r                       # single source: exactly the old R
    c = counter_penalty(signal, evidence_by_id)
    return {
        "reliability": r,
        "support": support,
        "counter": c,
        "bel": support * (1.0 - c),
        "pl": 1.0 - c * (1.0 - support),
        "independent_sources": 1 + len(corr),
        "corroborating": [{k: v for k, v in x.items() if k != "r"} for x in corr],
    }


# ---- component 3: materiality ---------------------------------------------------------------
def z_materiality(signal: dict[str, Any]) -> float | None:
    """Robust z-score of the last move against earlier moves; None unless the history is SOURCE-labelled and long enough."""
    if signal.get("history_label") != "SOURCE":
        return None
    pts = []
    for p in signal.get("history") or []:
        try:
            pts.append((p.get("date") or "", float(p["value"])))
        except (KeyError, TypeError, ValueError):
            return None
    pts.sort(key=lambda x: x[0])
    moves = [b[1] - a[1] for a, b in zip(pts, pts[1:])]
    if len(moves) < Z_MIN_PRIOR_MOVES + 1:
        return None
    prior, last = moves[:-1], moves[-1]
    med = median(prior)
    mad = median(abs(m - med) for m in prior)
    if mad == 0:
        return None
    z = Z_CONSTANT * (last - med) / mad
    return min(1.0, abs(z) / Z_OUTLIER)


def materiality(signal: dict[str, Any]) -> dict[str, Any]:
    estimators = [{"name": "strength", "value": max(0.0, min(1.0, float(signal.get("strength", 0.0)))), "label": "ASSUMPTION"}]
    sz = z_materiality(signal)
    if sz is not None:
        estimators.append({"name": "z_score", "value": sz, "label": "SOURCE"})
    m = sum(e["value"] for e in estimators) / len(estimators)
    return {"value": m, "estimators": estimators}


# ---- component 4: human view ----------------------------------------------------------------
def human_factor(annotations: list[dict[str, Any]]) -> float:
    factor = 1.0
    for note in annotations or []:
        factor *= HUMAN_MULTIPLIERS.get(note.get("action", "comment"), 1.0)
    return round(max(HUMAN_MIN, min(HUMAN_MAX, factor)), 4)


# ---- horizon fit ------------------------------------------------------------------------------
def horizon_fit(signal: dict[str, Any], h: int, width: float = KERNEL_WIDTH) -> float:
    """T(h) in [0, 1]: how much the signal speaks about the state of the market h months out."""
    try:
        lead = float(signal.get("lead_months"))
    except (TypeError, ValueError):
        return 1.0
    if lead <= 0:
        return 1.0
    sym = math.exp(-0.5 * (math.log(h / lead) / width) ** 2)
    if h < lead:
        return sym                         # effect not arrived yet inside this horizon
    cls = signal.get("classification")
    if cls == "structural":
        return 1.0
    if cls == "cyclical":
        return sym
    return (1.0 + sym) / 2.0               # mixed, or unclassified treated as mixed


# ---- aggregation views ---------------------------------------------------------------------------
def _band(factors: list[float], weight: float, capped_fn) -> dict[str, Any]:
    n = len(factors)
    methods = {
        "product": weight,
        "minimum": capped_fn(min(factors)),
        "geometric": capped_fn(math.prod(factors) ** (1.0 / n)),
        "arithmetic": capped_fn(sum(factors) / n),
    }
    methods = {k: round(v, 4) for k, v in methods.items()}
    return {"min": min(methods.values()), "max": max(methods.values()), "methods": methods}


def _attribution(factors: dict[str, float], labels: dict[str, str], weight: float) -> list[dict[str, Any]]:
    """Log-share of the discount from 1.0 per component; shares sum to 1."""
    if weight >= WEIGHT_MAX:
        return []
    zeros = [k for k, v in factors.items() if v <= 0]
    if zeros:
        raw = {k: (1.0 / len(zeros) if k in zeros else 0.0) for k in factors}
    else:
        logs = {k: -math.log(v) for k, v in factors.items()}
        total = sum(logs.values())
        if total <= 0:
            return []                      # no discount in the product; only the unchallenged cap lowered w
        raw = {k: v / total for k, v in logs.items()}
    shares = {k: round(v, 4) + 0.0 for k, v in raw.items()}   # + 0.0 turns -0.0 into 0.0
    drift = round(1.0 - sum(shares.values()), 4)
    if drift:
        top = max(shares, key=lambda k: abs(shares[k]))
        shares[top] = round(shares[top] + drift, 4)
    return [{"component": k, "share": shares[k], "label": labels[k]} for k in COMPONENTS]


def _assumptions(update_frequency: str) -> list[dict[str, Any]]:
    hl = HALF_LIFE_DAYS.get(update_frequency, 90)
    return ASSUMPTIONS + [{
        "name": "half_life_days", "value": float(hl), "label": "ASSUMPTION",
        "why": f"Currency halves every {hl} days for a source updated '{update_frequency}', tied to its publication cadence.",
    }]


# ---- public API ------------------------------------------------------------------------------------
def signal_weight(
    signal: dict[str, Any],
    evidence_by_id: dict[str, dict[str, Any]],
    today: date,
) -> dict[str, Any]:
    cred = credibility(signal, evidence_by_id)
    upd = signal.get("update_frequency", "event")
    f = freshness(signal.get("observed_at"), today, upd)
    mat = materiality(signal)
    m = mat["value"]
    h = human_factor(signal.get("annotations", []))
    challenged = bool(signal.get("ce_searched", False))

    def bound(x: float) -> float:
        x = min(WEIGHT_MAX, max(0.0, x))
        return min(x, UNCHALLENGED_CAP) if not challenged else x

    # Same multiplication order as the old R × F × S × (1 − C) × H, so single-source cards match it to the bit.
    product = cred["support"] * f * m * (1.0 - cred["counter"]) * h
    clamped = min(WEIGHT_MAX, product)
    capped = not challenged and clamped > UNCHALLENGED_CAP
    weight = round(UNCHALLENGED_CAP if capped else clamped, 4)

    fits = {str(hz): round(horizon_fit(signal, hz), 4) for hz in HORIZONS}
    factors = {"credibility": cred["bel"], "currency": f, "materiality": m, "human": h}
    labels = {
        "credibility": _worst(["ASSUMPTION", "SOURCE"]),       # grade map and counter cap (ASSUMPTION) on a sourced card
        "currency": _worst(["ASSUMPTION", "SOURCE"]),          # half-life (ASSUMPTION) on a sourced date
        "materiality": _worst([e["label"] for e in mat["estimators"]]),
        "human": _worst(["ASSUMPTION"]),                       # annotation multipliers
    }
    return {
        "weight": weight,
        "components": {
            "reliability": cred["reliability"],
            "freshness": f,
            "strength": mat["estimators"][0]["value"],
            "counter_penalty": cred["counter"],
            "human": h,
            "credibility": round(cred["bel"], 4),
            "materiality": round(m, 4),
        },
        "age_days": age_days(signal.get("observed_at"), today),
        "unchallenged_cap_applied": capped,
        "formula": FORMULA,
        "horizon_fit": fits,
        "horizon": {k: round(weight * t, 4) for k, t in fits.items()},
        "band": _band(list(factors.values()), weight, bound),
        "attribution": _attribution(factors, labels, weight),
        "assumptions": _assumptions(upd),
        "detail": {
            "credibility": {"support": round(cred["support"], 4), "counter": cred["counter"], "bel": round(cred["bel"], 4),
                            "pl": round(cred["pl"], 4), "independent_sources": cred["independent_sources"],
                            "corroborating": cred["corroborating"]},
            "materiality": {"estimators": [{**e, "value": round(e["value"], 4)} for e in mat["estimators"]]},
        },
    }


def compute_weights(
    signals: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
    today: date,
) -> dict[str, dict[str, Any]]:
    evidence_by_id = {ce["id"]: ce for ce in evidence}
    return {sig["id"]: signal_weight(sig, evidence_by_id, today) for sig in signals}


def horizon_weights(weights: dict[str, dict[str, Any]], h: int) -> dict[str, dict[str, float]]:
    """Per-signal w_h for the scenario engine (same shape select_scenarios reads: {id: {"weight": w}})."""
    key = str(h)
    return {sid: {"weight": float(w.get("horizon", {}).get(key, 0.0))} for sid, w in weights.items()}
