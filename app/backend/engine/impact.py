"""Signed impact of a signal on ABB relay demand and delivery (contract C8).

Pure code, no language model. The weight (engine/weights.py) says how much to trust and
how current a signal is. The impact says which way it pushes ABB and how much of ABB's
business it can touch. The Signals map plots weight on one axis and impact on the other.

    impact = sign × size,   size = round(100 × materiality × theme_load)

    materiality  the card's M component from engine/weights.py (how big is the move)
    theme_load   min(1, Σ|axes| / A_ref) over the six theme loadings on the card
                 (demand, supply, policy, price, nordic, bullwhip): a signal that touches
                 several themes strongly can touch more of ABB's business than a single-theme one
    A_ref        ASSUMPTION, see ASSUMPTIONS: the summed absolute loading that counts as "fully loaded"

Sign rule (favourable + / unfavourable −, for ABB relay demand and delivery in the signal's segment)

    sign = sign(direction) × polarity(measures)

    direction  +1 the card's signal is growing, tightening, rising or supportive; -1 the opposite; 0 none recorded
    polarity   what a rising reading means for ABB:
                 end_demand, intermediary, policy   +1  more end demand, more orders, a more supportive
                                                        rule is favourable; falling demand, falling orders,
                                                        a connection pause or restrictive rule is unfavourable
                 supply_tightness, price            -1  tighter supply (longer lead times, scarcer parts)
                                                        and a rising component or commodity price are
                                                        unfavourable for delivery and cost; easing supply
                                                        and falling prices are favourable
    direction 0 means the card records no direction, so no effect is claimed: sign 0 and impact 0.
    A measure the rule does not know gets polarity +1 (direction read at face value).

The rule is the same for every segment, because the measures vocabulary is shared. It is a
reading of the card's own fields: the language model classifies `direction` and `measures`
when it writes the card, it never sets the sign or the number.
"""
from __future__ import annotations

from typing import Any

A_REF = 1.5                                         # ASSUMPTION: Σ|axes| at which a signal counts as fully loaded on the six themes
LABEL = "ASSUMPTION"
AXES = ("demand", "supply", "policy", "price", "nordic", "bullwhip")
POLARITY = {                                        # ASSUMPTION: what a rising reading means for ABB relay demand and delivery
    "end_demand": 1,
    "intermediary": 1,
    "policy": 1,
    "supply_tightness": -1,
    "price": -1,
}
FORMULA = "impact = sign × round(100 × materiality × min(1, Σ|axes| / A_ref))"
SIGN_RULE = {
    "en": ("Favourable (+) or unfavourable (−) for ABB relay demand and delivery. Sign = direction × polarity of the measure: "
           "end demand, orders and supportive policy count as favourable when rising; tighter supply and rising component or "
           "commodity prices count as unfavourable. A card with no direction has impact 0."),
    "fi": ("Suotuisa (+) tai epäsuotuisa (−) ABB:n suojareleiden kysynnälle ja toimituksille. Etumerkki = suunta × mittarin napaisuus: "
           "loppukysyntä, tilaukset ja tukeva sääntely ovat suotuisia noustessaan; tiukentuva saatavuus sekä nouseva komponentti- "
           "tai raaka-ainehinta ovat epäsuotuisia. Kortin vaikutus on 0, jos suuntaa ei ole kirjattu."),
}
ASSUMPTIONS: list[dict[str, Any]] = [
    {"name": "impact_a_ref", "value": A_REF, "label": LABEL,
     "why": "Summed absolute theme loading at which a signal touches ABB's business fully (theme_load = 1). No outcome data fits it; "
            "a card with one strong theme (0.9) gets 0.6, a card loaded on three themes gets 1."},
    {"name": "impact_polarity", "value": "end_demand +1, intermediary +1, policy +1, supply_tightness -1, price -1", "label": LABEL,
     "why": "A rising demand, order or supportive-policy reading helps ABB; tighter supply and higher component or commodity prices hurt delivery and cost."},
]


def _direction_sign(signal: dict[str, Any]) -> int:
    try:
        d = float(signal.get("direction", 0) or 0)
    except (TypeError, ValueError):
        return 0
    return 1 if d > 0 else (-1 if d < 0 else 0)


def impact_sign(signal: dict[str, Any]) -> int:
    """+1 favourable, -1 unfavourable, 0 when the card records no direction."""
    return _direction_sign(signal) * POLARITY.get(str(signal.get("measures") or ""), 1)


def theme_load(signal: dict[str, Any], a_ref: float = A_REF) -> float:
    axes = signal.get("axes") or {}
    total = 0.0
    for k in AXES:
        try:
            total += abs(float(axes.get(k, 0.0) or 0.0))
        except (TypeError, ValueError):
            continue
    return min(1.0, total / a_ref)


def compute_impact(signal: dict[str, Any], weight_entry: dict[str, Any]) -> dict[str, Any]:
    """Signed impact in [-100, 100] with its parts. `weight_entry` is the signal's entry from compute_weights."""
    materiality = float(((weight_entry or {}).get("components") or {}).get("materiality", 0.0) or 0.0)
    materiality = max(0.0, min(1.0, materiality))
    load = theme_load(signal)
    sign = impact_sign(signal)
    size = round(100 * materiality * load)
    value = max(-100, min(100, sign * size))
    return {"impact": int(value) + 0, "label": LABEL,
            "parts": {"sign": sign, "materiality": round(materiality, 4), "theme_load": round(load, 4)}}


def impact_meta() -> dict[str, Any]:
    return {"formula": FORMULA, "a_ref": A_REF, "label": LABEL, "sign_rule": dict(SIGN_RULE),
            "polarity": dict(POLARITY), "assumptions": [dict(a) for a in ASSUMPTIONS]}
