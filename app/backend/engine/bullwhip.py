"""Deterministic bullwhip (demand-quality) metrics.

Each metric separates real end demand from intermediary hoarding. The inputs are
declared in data/bullwhip.json with a data label; the values below are computed
here. Status vocabulary:

    hoarding_risk   the metric is consistent with intermediaries ordering ahead of need
    real_demand     the metric is consistent with end demand driving orders
    hoarding_ending the metric shows urgency fading while supply is still tight
    inconclusive    the metric does not separate the two
    not_connected   inputs missing (internal data not yet plugged in)
"""
from __future__ import annotations

from typing import Any


def amplification_ratio(orders_growth: float, end_demand_growth: float, threshold: float) -> dict[str, Any]:
    ratio = (1.0 + orders_growth) / (1.0 + end_demand_growth)
    if ratio >= threshold:
        status, reading = "hoarding_risk", (
            f"Intermediary orders grew {orders_growth:+.0%} against end demand {end_demand_growth:+.0%}: "
            f"ratio {ratio:.2f} is above {threshold:.1f}. Orders are amplifying the signal."
        )
    elif ratio >= 1.05:
        status, reading = "inconclusive", f"Ratio {ratio:.2f}: mild amplification, within normal planning lead."
    else:
        status, reading = "real_demand", f"Ratio {ratio:.2f}: orders track end demand."
    return {"value": round(ratio, 2), "unit": "x", "status": status, "reading": reading}


def momentum(series: list[float], threshold: float) -> dict[str, Any]:
    if len(series) < 3:
        return {"value": None, "unit": "pp", "status": "inconclusive", "reading": "Fewer than three observations."}
    d1 = [series[i] - series[i - 1] for i in range(1, len(series))]
    second = d1[-1] - d1[-2]
    last_increment = series[-1]
    rising = last_increment > 0
    decelerating_twice = len(d1) >= 2 and d1[-1] < 0 and d1[-2] < 0
    if rising and decelerating_twice:
        status = "hoarding_ending"
        reading = (
            f"Prices still rising (+{last_increment:.0f}% QoQ) but the increment has shrunk two quarters in a row "
            f"(latest change {d1[-1]:+.0f} pp). This is the pre-peak shape seen before the 2022 memory correction."
        )
    elif rising:
        status = "hoarding_risk"
        reading = f"Prices rising (+{last_increment:.0f}% QoQ) with increments still growing; urgency is building."
    else:
        status = "real_demand"
        reading = f"Price increments negative ({last_increment:+.0f}% QoQ); the hoarding phase is over."
    return {"value": round(second, 1), "unit": "pp (2nd diff)", "status": status, "reading": reading}


def double_order_index(lead_time_change_pct: float, inventory_days_change_pct: float, threshold: float) -> dict[str, Any]:
    idx = min(lead_time_change_pct, inventory_days_change_pct)
    if lead_time_change_pct > threshold and inventory_days_change_pct > threshold:
        status = "hoarding_risk"
        reading = (
            f"Lead times +{lead_time_change_pct:.0%} and distributor inventory days +{inventory_days_change_pct:.0%} "
            "rose together: buyers are ordering ahead of need while stock accumulates downstream."
        )
    elif lead_time_change_pct > threshold and inventory_days_change_pct <= 0:
        status = "real_demand"
        reading = f"Lead times +{lead_time_change_pct:.0%} while inventory fell: genuine scarcity."
    else:
        status = "inconclusive"
        reading = "Lead time and inventory moves do not point the same way."
    return {"value": round(idx, 2), "unit": "min(dLT, dInv)", "status": status, "reading": reading}


def spot_contract_spread(spread_series: list[float], threshold: float) -> dict[str, Any]:
    if not spread_series:
        return {"value": None, "unit": "%", "status": "inconclusive", "reading": "No data."}
    latest = spread_series[-1]
    peak = max(spread_series)
    if latest < threshold and peak >= 2 * threshold:
        status = "hoarding_ending"
        reading = (
            f"Spot premium fell from {peak:.0f}% to {latest:.0f}%: urgency buyers have left the spot market "
            "while contract lead times are still long. Hoarding is ending before supply has loosened."
        )
    elif latest >= threshold:
        status = "hoarding_risk"
        reading = f"Spot premium {latest:.0f}%: buyers are paying up for immediate delivery."
    else:
        status = "real_demand"
        reading = f"Spot premium {latest:.0f}%: no urgency premium."
    return {"value": round(latest, 1), "unit": "% premium", "status": status, "reading": reading}


def cancellation_rate(cancelled_or_pushed: float | None, total: float | None, threshold: float) -> dict[str, Any]:
    if cancelled_or_pushed is None or not total:
        return {"value": None, "unit": "%", "status": "not_connected",
                "reading": "ABB order change history not connected. This is the earliest internal bullwhip signal."}
    rate = cancelled_or_pushed / total
    status = "hoarding_risk" if rate >= threshold else "real_demand"
    return {"value": round(rate * 100, 1), "unit": "%", "status": status,
            "reading": f"{rate:.0%} of frame-order quantity pushed out or cancelled in 90 days."}


METHODS = {
    "amplification_ratio": lambda i, t: amplification_ratio(i["orders_growth"], i["end_demand_growth"], t),
    "momentum": lambda i, t: momentum(i["series"], t),
    "double_order_index": lambda i, t: double_order_index(i["lead_time_change_pct"], i["inventory_days_change_pct"], t),
    "spot_contract_spread": lambda i, t: spot_contract_spread(i["spread_series"], t),
    "cancellation_rate": lambda i, t: cancellation_rate(i.get("cancelled_or_pushed"), i.get("total"), t),
}


def compute_bullwhip(config: dict[str, Any]) -> dict[str, Any]:
    results = []
    for m in config.get("metrics", []):
        fn = METHODS.get(m["method"])
        if fn is None:
            res = {"value": None, "unit": "", "status": "inconclusive", "reading": f"Unknown method {m['method']}"}
        else:
            res = fn(m.get("inputs", {}), m.get("threshold", 0))
        results.append({**m, **res})
    statuses = [r["status"] for r in results if r["status"] != "not_connected"]
    risk = sum(s in ("hoarding_risk",) for s in statuses)
    ending = sum(s == "hoarding_ending" for s in statuses)
    real = sum(s == "real_demand" for s in statuses)
    if ending >= 1 and risk >= 1:
        overall = "mixed_turning"
        summary = (
            "Hoarding indicators are still elevated but two urgency measures are already fading. "
            "Read as: the apparent demand surge contains a hoarding component that is starting to unwind "
            "while the structural end-demand signals are intact."
        )
    elif risk > real:
        overall = "hoarding_risk"
        summary = "Most metrics point to intermediaries ordering ahead of end demand."
    elif real > risk:
        overall = "real_demand"
        summary = "Most metrics are consistent with end demand driving orders."
    else:
        overall = "inconclusive"
        summary = "Metrics do not agree; more data needed."
    return {"metrics": results, "overall": overall, "summary": summary,
            "analog_2021_2023": config.get("analog_2021_2023", {})}
