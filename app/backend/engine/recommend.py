"""Recommended move, next action and hedge, composed in code from templates (contract C3).

The recommendation is not written by a language model. It is assembled from
data/recommendations.json (qualitative, conditional decision moves for the S&OP /
component procurement planner, one block per scenario archetype) and the current
scenario state:

    leading scenario, runner-up      from engine.archetypes.select_scenarios
    confidence                       margin to the runner-up and normalised entropy, thresholds labelled ASSUMPTION
    trigger signals                  each move names signal themes; a theme is mapped here to real signal ids in
                                     the current world by matching card fields (category, measures, region,
                                     source_class, direction), ranked by computed weight. No id is hard-coded.
    next action, revisit date        today + N days, N from the templates (ASSUMPTION)

Boundary (directive 2 vs 9): moves say what to prepare, review, watch or discuss, conditionally.
They never contain quantities, order points, prices or order dates. The planner decides.
"""
from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any

AREAS = ("procurement", "manufacturing", "capacity", "supply_reliability")
MAX_PER_THEME = 2
MAX_TRIGGER_SIGNALS = 4


def load_templates(path: str | Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _name(a: dict[str, Any]) -> dict[str, str]:
    n = a.get("name")
    if isinstance(n, dict):
        return {"en": str(n.get("en", "")), "fi": str(n.get("fi") or n.get("en", ""))}
    return {"en": str(n or a.get("id", "")), "fi": str(n or a.get("id", ""))}


def _pct(p: float, lang: str) -> str:
    return f"{p * 100:.0f} %" if lang == "fi" else f"{p * 100:.0f}%"


def confidence(margin: float, entropy: float, rules: dict[str, Any]) -> str:
    """low | medium | high from the probability margin to the runner-up and the normalised entropy."""
    hi, mid = rules["high"], rules["medium"]
    if margin >= float(hi["min_margin"]) and entropy <= float(hi["max_entropy"]):
        return "high"
    if margin >= float(mid["min_margin"]) and entropy <= float(mid["max_entropy"]):
        return "medium"
    return "low"


def _matches(sig: dict[str, Any], select: dict[str, list[Any]]) -> bool:
    for key, allowed in select.items():
        value = sig.get(key)
        if value not in allowed:
            return False
    return True


def match_theme(theme: dict[str, Any], signals: list[dict[str, Any]], weights: dict[str, Any]) -> list[str]:
    """Real signal ids in the current world that carry a theme, strongest computed weight first."""
    def w(s: dict[str, Any]) -> float:
        return float(weights.get(s["id"], {}).get("weight", 0.0))

    hits = [s for s in signals if _matches(s, theme.get("select", {}))]
    if not theme.get("allow_inactive"):
        hits = [s for s in hits if w(s) > 0]
    hits.sort(key=lambda s: (-w(s), s["id"]))
    if hits:
        return [s["id"] for s in hits[:MAX_PER_THEME]]
    axis = theme.get("fallback_axis")
    if axis:
        near = [s for s in signals if w(s) > 0 and abs(float((s.get("axes") or {}).get(axis, 0.0))) >= 0.3]
        near.sort(key=lambda s: (-w(s) * abs(float(s["axes"].get(axis, 0.0))), s["id"]))
        return [s["id"] for s in near[:MAX_PER_THEME]]
    return []


def _trigger_text(move: dict[str, Any], themes: dict[str, Any], by_theme: dict[str, list[str]], lang: str) -> str:
    parts = []
    for key in move["themes"]:
        label = themes[key]["label"][lang]
        ids = by_theme.get(key, [])
        parts.append(f"{label} [{', '.join(ids)}]" if ids else label)
    return move["trigger"][lang].replace("{themes}", "; ".join(parts))


def build_recommendation(
    scenarios_result: dict[str, Any],
    signals: list[dict[str, Any]],
    weights: dict[str, Any],
    today: date,
    templates: dict[str, Any],
) -> dict[str, Any] | None:
    """Return the recommendation object R of contract C3, or None when the templates lack the leading archetype."""
    ranked = sorted(scenarios_result["scenarios"], key=lambda s: -s["probability"])
    if not ranked:
        return None
    lead = ranked[0]
    runner = ranked[1] if len(ranked) > 1 else None
    tpl = templates["archetypes"].get(lead["id"])
    if tpl is None:
        return None
    themes = templates["themes"]
    entropy = float(scenarios_result.get("entropy", 1.0))
    margin = lead["probability"] - (runner["probability"] if runner else 0.0)
    conf = confidence(margin, entropy, templates["confidence_rules"])
    lead_name = _name(lead)

    by_theme: dict[str, list[str]] = {}
    moves = []
    for m in tpl["moves"]:
        for key in m["themes"]:
            if key not in by_theme:
                by_theme[key] = match_theme(themes[key], signals, weights)
        trigger_ids: list[str] = []
        for key in m["themes"]:
            for sid in by_theme[key]:
                if sid not in trigger_ids:
                    trigger_ids.append(sid)
        moves.append({
            "area": m["area"], "type": m["type"],
            "text": dict(m["text"]),
            "trigger": {lang: _trigger_text(m, themes, by_theme, lang) for lang in ("en", "fi")},
            "trigger_signals": trigger_ids[:MAX_TRIGGER_SIGNALS],
            "cost_if_wrong": dict(m["cost_if_wrong"]),
            "horizon_months": int(m["horizon_months"]),
            "label": "ASSUMPTION",
        })

    headline = {
        lang: templates["headline_template"][lang].format(
            confidence=templates["confidence_labels"][conf][lang], name=lead_name[lang],
            probability=_pct(lead["probability"], lang), move=tpl["headline_move"][lang])
        for lang in ("en", "fi")
    }

    runner_out = None
    hedge = {"en": "", "fi": ""}
    if runner is not None:
        rn = _name(runner)
        runner_out = {"id": runner["id"], "name": rn, "probability": runner["probability"]}
        shift = templates["archetypes"].get(runner["id"], {}).get("if_leading")
        for lang in ("en", "fi"):
            hedge[lang] = templates["hedge_template"][lang].format(
                runner=rn[lang], runner_p=_pct(runner["probability"], lang), lead=lead_name[lang],
                shift=(shift or {}).get(lang, "the emphasis of the plan would be re-read." if lang == "en" else "suunnitelman painopiste arvioitaisiin uudelleen."))

    defaults = templates["defaults"]
    due_days = int(tpl["next_action"].get("due_days", defaults["due_days"]))
    na = tpl["next_action"]
    return {
        "scenario_id": lead["id"], "scenario_name": lead_name, "probability": lead["probability"],
        "runner_up": runner_out,
        "confidence": conf,
        "confidence_basis": {"margin": round(margin, 4), "entropy": round(entropy, 4), "label": "ASSUMPTION",
                             "rule": templates["confidence_rules"]["note"]},
        "headline": headline,
        "moves": moves,
        "hedge": hedge,
        "next_action": {"text": dict(na["text"]), "owner": dict(na["owner"]), "due": (today + timedelta(days=due_days)).isoformat()},
        "revisit_on": (today + timedelta(days=int(defaults["revisit_days"]))).isoformat(),
        "disclaimer": dict(templates["disclaimer"]),
        "label": "ASSUMPTION", "generated_by": "code",
    }


def template_texts(templates: dict[str, Any]) -> list[str]:
    """Every free-text string in the templates (used by the guardrail test)."""
    out: list[str] = []

    def walk(v: Any) -> None:
        if isinstance(v, dict):
            if set(v) == {"en", "fi"} and all(isinstance(x, str) for x in v.values()):
                out.extend(v.values())
            else:
                for x in v.values():
                    walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)

    walk({k: v for k, v in templates.items() if not k.startswith("_")})
    return out
