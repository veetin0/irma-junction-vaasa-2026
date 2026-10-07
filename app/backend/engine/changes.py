"""Signal changes since the previous update cycle (C4) and the negative-evidence list (C5).

All computed from weights, never invented.

Baseline
    The weights recorded at the previous update cycle. On the first start there is none, so the
    baseline is compute_weights as of (today - BASELINE_DAYS); cards observed after that date did not
    exist yet and are marked "new". [ASSUMPTION: seven days is the look-back window for the first start.]

Status
    new      the card is not in the baseline
    flipped  the card's direction (+1 / -1) differs from the baseline
    up/down  weight moved by at least FLAT_EPS
    flat     |delta| < FLAT_EPS  [ASSUMPTION: 0.01]
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from engine.weights import RELIABILITY, compute_weights

BASELINE_DAYS = 7
FLAT_EPS = 0.01


def _parse(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def snapshot(signals: list[dict[str, Any]], weights: dict[str, Any], on: date, ids: set[str] | None = None) -> dict[str, Any]:
    """Record the weights and directions of a cycle. `ids` restricts the snapshot to cards that existed then."""
    keep = [s for s in signals if ids is None or s["id"] in ids]
    return {"date": on.isoformat(),
            "weights": {s["id"]: float(weights.get(s["id"], {}).get("weight", 0.0)) for s in keep},
            "direction": {s["id"]: int(s.get("direction", 0)) for s in keep}}


def initial_baseline(signals: list[dict[str, Any]], evidence: list[dict[str, Any]], today: date, days: int = BASELINE_DAYS) -> dict[str, Any]:
    """First start: weights as they would have been `days` days ago, for the cards that existed then."""
    then = today - timedelta(days=days)
    existed = {s["id"] for s in signals if (d := _parse(s.get("observed_at"))) is None or d <= then}
    return snapshot(signals, compute_weights(signals, evidence, then), then, existed)


def compute_changes(signals: list[dict[str, Any]], weights: dict[str, Any], baseline: dict[str, Any] | None, today: date) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    since = (baseline or {}).get("date") or today.isoformat()
    for s in signals:
        sid = s["id"]
        now_w = float(weights.get(sid, {}).get("weight", 0.0))
        if baseline is None or sid not in baseline["weights"]:
            obs = _parse(s.get("observed_at"))
            out[sid] = {"status": "new", "weight_prev": None, "delta": None, "since": (obs or today).isoformat()}
            continue
        prev = baseline["weights"][sid]
        delta = round(now_w - prev, 4)
        if int(s.get("direction", 0)) != baseline["direction"].get(sid, int(s.get("direction", 0))):
            status = "flipped"
        elif abs(delta) < FLAT_EPS:
            status = "flat"
        else:
            status = "up" if delta > 0 else "down"
        out[sid] = {"status": status, "weight_prev": round(prev, 4), "delta": delta, "since": since}
    return out


def signal_changes(signals: list[dict[str, Any]], changes: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """Non-flat changes: new cards first (newest first), then flipped and moved cards by |delta| descending."""
    obs = {s["id"]: s.get("observed_at") or "" for s in signals}
    rows = [{"signal_id": sid, "status": c["status"], "delta": c["delta"]} for sid, c in changes.items() if c["status"] != "flat"]
    new = sorted((r for r in rows if r["status"] == "new"), key=lambda r: (obs[r["signal_id"]], r["signal_id"]), reverse=True)
    rest = sorted((r for r in rows if r["status"] != "new"), key=lambda r: (-abs(r["delta"] or 0.0), r["signal_id"]))
    return new + rest


# ---------------------------------------------------------------------------------
# C5: negative evidence
# ---------------------------------------------------------------------------------
def _against_for_signal(sig: dict[str, Any], signals: list[dict[str, Any]], weights: dict[str, Any], limit: int = 3) -> list[str]:
    """Growth-supporting cards this card contradicts: positive direction, opposite sign on at least one shared axis."""
    ax = sig.get("axes") or {}
    scored = []
    for o in signals:
        if o["id"] == sig["id"] or int(o.get("direction", 0)) <= 0:
            continue
        oax = o.get("axes") or {}
        clash = sum(min(abs(float(ax.get(a, 0.0))), abs(float(oax.get(a, 0.0)))) for a in ax
                    if float(ax.get(a, 0.0)) * float(oax.get(a, 0.0)) < 0)
        if clash > 0:
            scored.append((clash * float(weights.get(o["id"], {}).get("weight", 0.0)), o["id"]))
    scored.sort(key=lambda t: (-t[0], t[1]))
    return [sid for _, sid in scored[:limit]]


def negative_signals(signals: list[dict[str, Any]], evidence: list[dict[str, Any]], weights: dict[str, Any]) -> list[dict[str, Any]]:
    """direction<0 cards (by weight), then counter-evidence cards against growth-supporting cards (by R x strength)."""
    rows: list[dict[str, Any]] = []
    by_id = {s["id"]: s for s in signals}
    for s in signals:
        if int(s.get("direction", 0)) >= 0:
            continue
        w = float(weights.get(s["id"], {}).get("weight", 0.0))
        rows.append({"kind": "signal", "id": s["id"], "name": s.get("name"), "short": s.get("short"), "short_fi": s.get("short_fi", s.get("short")),
                     "region": s.get("region"), "weight": w, "strength": float(s.get("strength", 0.0)), "reliability": s.get("reliability"),
                     "source": {"name": (s.get("source") or {}).get("name"), "date": (s.get("source") or {}).get("date"), "url": (s.get("source") or {}).get("url")},
                     "against": _against_for_signal(s, signals, weights), "data_label": s.get("data_label"), "score": w})
    for ce in evidence:
        target = by_id.get(ce.get("against"))
        if target is None or int(target.get("direction", 0)) < 0:
            continue
        r = RELIABILITY.get(ce.get("reliability", "C"), 0.4)
        claim = str(ce.get("claim", ""))
        first = claim.split(". ")[0].rstrip(".") + "."
        src = ce.get("source") or {}
        rows.append({"kind": "counter_evidence", "id": ce["id"], "name": first if len(first) <= 160 else first[:157] + "...",
                     "short": src.get("name") or ce["id"], "short_fi": src.get("name") or ce["id"],
                     "region": target.get("region"), "weight": None, "strength": float(ce.get("strength", 0.0)), "reliability": ce.get("reliability"),
                     "source": {"name": src.get("name"), "date": src.get("date"), "url": src.get("url")},
                     "against": [target["id"]], "data_label": ce.get("data_label"), "score": round(r * float(ce.get("strength", 0.0)), 4)})
    # Cards first (by computed weight), then counter-evidence cards (by reliability x strength).
    rows.sort(key=lambda r: (r["kind"] != "signal", -r["score"], r["id"]))
    return rows
