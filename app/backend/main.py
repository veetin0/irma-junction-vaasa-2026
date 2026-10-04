"""Irma API: scenario monitor for ABB (data-centre segment).

Signals, generated scenarios (the four most likely situations per run), daily history,
notifications, settings, two switchable mock worlds, a plain-language summary, and the
agent pipeline for new information. Scheduled update cycle (default hourly).

Run from app/backend:  uvicorn main:app --port 8000
"""
from __future__ import annotations

import asyncio
import copy
import json
import os
import random
import re
import threading
import time
from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from agents.llm import LLMClient, load_replay, recommendation_filter
from agents.pipeline import Context, Pipeline, _next_analysis_step, _t, build_brief, next_id
from agents.scout import SKIP_REASONS, build_prompt, known_urls, post_gate, pre_gate, reason as scout_reason, scout_settings
from engine.archetypes import axis_scores, plain_summary, select_scenarios
from engine.bullwhip import compute_bullwhip
from engine.weights import compute_weights
from agents.web import DEFAULT_SCOUT_SETTINGS, DEFAULT_WEB_SETTINGS, THEMES, extract_json, host_of, norm_url

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
FRONTEND = BASE.parent / "frontend"
SETTINGS_PATH = DATA / "settings.json"

DEFAULT_SETTINGS: dict[str, Any] = {
    "run_interval_minutes": 60,
    "notifications": {"probability_change_pp": 3.0, "major_signal_weight": 0.4, "price_change_pct": 5.0, "leader_change": True},
    "strong_signal_weight": 0.25,
    "history_days": 120,
    "web_search": copy.deepcopy(DEFAULT_WEB_SETTINGS),
}
SOURCE_CLASSES = {
    "contract": {"en": "Contracts and commitments", "fi": "Sopimukset ja sitoumukset"},
    "price": {"en": "Component and commodity prices", "fi": "Komponenttien ja raaka-aineiden hinnat"},
    "news": {"en": "Market news", "fi": "Markkinauutiset"},
    "policy": {"en": "Policy and institutional", "fi": "Sääntely ja instituutiot"},
    "research": {"en": "Research and institutions", "fi": "Tutkimus ja instituutiot"},
}
WORLDS = {
    1: {"id": 1, "label": {"en": "Current world situation", "fi": "Nykyinen maailmantilanne"},
        "note": {"en": "Public signals as of October 2026: growth with scarce components.", "fi": "Julkiset signaalit lokakuussa 2026: kasvua ja niukkoja komponentteja."}},
    2: {"id": 2, "label": {"en": "World situation 2", "fi": "Maailmantilanne 2"},
        "note": {"en": "Constructed stress dataset (DEMODATA): investment cuts, cancellations, falling prices and easing supply.", "fi": "Rakennettu stressiaineisto (DEMODATA): investointileikkauksia, peruutuksia, laskevia hintoja ja helpottuvaa saatavuutta."}},
}
SUGGESTED_PROMPTS = {
    "en": ["Summarize key changes in the data-centre segment", "What is the logical next move for procurement", "Tell about the situation of components in our products"],
    "fi": ["Tiivistä datakeskussegmentin keskeiset muutokset", "Mikä on hankinnan looginen seuraava askel", "Kerro komponenttien tilanteesta tuotteissamme"],
}


def today() -> date:
    override = os.environ.get("DEMO_TODAY")
    return datetime.strptime(override, "%Y-%m-%d").date() if override else date.today()


def now() -> datetime:
    return datetime.combine(today(), datetime.now().time())


def _load(path: Path) -> Any:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(base)
    for k, v in (override or {}).items():
        out[k] = _merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


class Store:
    def __init__(self) -> None:
        self.llm = LLMClient()
        self.pipeline = Pipeline()
        self.replay = load_replay(str(DATA / "replay.json"))
        self.settings = self.load_settings()
        self.world = 1
        self.llm.blocked_domains = set((self.settings.get("web_search") or {}).get("blocked_domains") or [])
        self.lock = threading.RLock()
        self.scout_state: dict[str, Any] = {"running": False, "runs": [], "started_at": None}
        self.additions_path = Path(os.environ.get("IRMA_ADDITIONS", str(DATA / "worlds" / "1" / "additions.json")))
        self.additions: dict[str, dict[str, Any]] = {"signals": {}, "evidence": {}}
        self.seen: dict[str, Any] = {}
        self.reset()

    # ---- settings -------------------------------------------------------------
    def load_settings(self) -> dict[str, Any]:
        if SETTINGS_PATH.exists():
            try:
                return _merge(DEFAULT_SETTINGS, json.loads(SETTINGS_PATH.read_text(encoding="utf-8")))
            except json.JSONDecodeError:
                pass
        return copy.deepcopy(DEFAULT_SETTINGS)

    def save_settings(self, patch: dict[str, Any]) -> dict[str, Any]:
        self.settings = _merge(self.settings, patch)
        self.settings["run_interval_minutes"] = max(5, int(self.settings["run_interval_minutes"]))
        ws = self.settings.setdefault("web_search", copy.deepcopy(DEFAULT_WEB_SETTINGS))
        ws["max_searches"] = max(1, min(10, int(ws.get("max_searches", 3))))
        ws["max_fetches"] = max(0, min(10, int(ws.get("max_fetches", 2))))
        ws["allowed_domains"] = [d.strip().lower().removeprefix("https://").removeprefix("http://").removeprefix("www.").strip("/") for d in ws.get("allowed_domains", []) if d and d.strip()][:100]
        ws["primary_domains"] = [d.strip().lower().removeprefix("www.").strip("/") for d in ws.get("primary_domains", []) if d and d.strip()][:100]
        ws["blocked_domains"] = sorted({d.strip().lower() for d in ws.get("blocked_domains", []) if d and d.strip()})
        ws["allowed_domains"] = [d for d in ws["allowed_domains"] if d not in ws["blocked_domains"]]
        self.llm.blocked_domains = set(ws["blocked_domains"])
        sc = {**DEFAULT_SCOUT_SETTINGS, **(ws.get("scout") or {})}
        sc["enabled"] = bool(sc["enabled"])
        sc["max_candidates"] = max(1, min(5, int(sc["max_candidates"])))
        sc["max_searches"] = max(1, min(10, int(sc["max_searches"])))
        sc["max_age_days"] = max(1, min(180, int(sc["max_age_days"])))
        sc["min_grade"] = "A" if str(sc["min_grade"]).upper() == "A" else "B"
        sc["min_weight"] = max(0.0, min(1.0, float(sc["min_weight"])))
        sc["min_axis_load"] = max(0.0, min(1.0, float(sc["min_axis_load"])))
        ws["scout"] = sc
        SETTINGS_PATH.write_text(json.dumps(self.settings, indent=2), encoding="utf-8")
        self.next_run = now() + timedelta(minutes=self.settings["run_interval_minutes"])
        return self.settings

    # ---- state ----------------------------------------------------------------
    def reset(self, world: int | None = None) -> None:
        with self.lock:
            self._reset(world)

    def _reset(self, world: int | None = None) -> None:
        if world is not None:
            self.world = int(world)
        wdir = DATA / "worlds" / str(self.world)
        self.scenario_config: dict[str, Any] = _load(DATA / "scenario_archetypes.json")
        self.signals: list[dict[str, Any]] = _load(wdir / "signals.json")
        self.evidence: list[dict[str, Any]] = _load(wdir / "evidence.json")
        self.bullwhip_config: dict[str, Any] = _load(wdir / "bullwhip.json")
        self._load_additions()
        self.runs: list[dict[str, Any]] = []
        self.brief: dict[str, Any] | None = None
        self.notifications: list[dict[str, Any]] = []
        self.notified: set[tuple] = set()
        self.last_run: datetime | None = None
        self.runs_completed = 0
        self.next_run = now() + timedelta(minutes=self.settings["run_interval_minutes"])
        self.history: list[dict[str, Any]] = self.seed_history()
        self.cycle("startup")

    def weights(self) -> dict[str, Any]:
        return compute_weights(self.signals, self.evidence, today())

    def scenarios(self, weights: dict[str, Any] | None = None) -> dict[str, Any]:
        w = weights or self.weights()
        return select_scenarios(self.scenario_config["archetypes"], self.signals, w, float(self.scenario_config.get("scaling_k", 1.5)))

    def _context(self, item: dict[str, Any] | None = None) -> Context:
        return Context(today=today(), signals=self.signals, evidence=self.evidence, scenario_config=self.scenario_config,
                       bullwhip_config=self.bullwhip_config, replay=self.replay, llm=self.llm, item=item,
                       web=self.settings.get("web_search"))

    # ---- daily history (keyed by scenario id) -------------------------------------
    def seed_history(self) -> list[dict[str, Any]]:
        sc = self.scenarios()
        ids = [s["id"] for s in sc["scenarios"]]
        rng = random.Random(7 + self.world)
        days = int(self.settings.get("history_days", 120))
        p = {s["id"]: s["probability"] for s in sc["scenarios"]}
        points: list[dict[str, Any]] = []
        for i in range(1, days + 1):
            d = today() - timedelta(days=i)
            drift = {sid: max(0.02, p[sid] + rng.gauss(0, 0.006)) for sid in ids}
            total = sum(drift.values())
            p = {sid: v / total for sid, v in drift.items()}
            points.append({"date": d.isoformat(), "probs": {sid: round(p[sid], 4) for sid in ids}, "leading": max(ids, key=lambda s: p[s]), "live": False, "label": "DEMODATA"})
        points.reverse()
        return points

    def snapshot_today(self, sc: dict[str, Any]) -> dict[str, Any]:
        point = {"date": today().isoformat(), "probs": {s["id"]: s["probability"] for s in sc["scenarios"]},
                 "leading": max(sc["scenarios"], key=lambda s: s["probability"])["id"], "live": True, "label": "LIVE",
                 "entropy": sc["entropy"], "updated_at": now().isoformat(timespec="minutes")}
        if self.history and self.history[-1]["date"] == point["date"]:
            self.history[-1] = point
        else:
            self.history.append(point)
        return point

    def previous_day(self) -> dict[str, Any] | None:
        t = today().isoformat()
        prev = [h for h in self.history if h["date"] < t]
        return prev[-1] if prev else None

    # ---- update cycle ---------------------------------------------------------------
    def cycle(self, reason: str) -> list[dict[str, Any]]:
        with self.lock:
            return self._cycle(reason)

    def _cycle(self, reason: str) -> list[dict[str, Any]]:
        w = self.weights()
        sc = self.scenarios(w)
        prev = self.previous_day()
        point = self.snapshot_today(sc)
        created: list[dict[str, Any]] = []
        n = self.settings["notifications"]
        by_id = {s["id"]: s for s in sc["scenarios"]}

        def push(key: tuple, kind: str, severity: str, title: dict[str, str], text: dict[str, str], signal_id: str | None = None, scenario_id: str | None = None) -> None:
            if key in self.notified:
                return
            self.notified.add(key)
            note = {"id": f"N-{len(self.notifications) + 1:04d}", "time": now().isoformat(timespec="minutes"), "kind": kind, "severity": severity,
                    "title": title["en"], "text": text["en"], "title_fi": title["fi"], "text_fi": text["fi"],
                    "signal_id": signal_id, "scenario_id": scenario_id, "read": False, "reason": reason}
            self.notifications.insert(0, note)
            created.append(note)

        if prev is not None:
            if n.get("leader_change") and prev["leading"] != point["leading"] and point["leading"] in by_id:
                new = by_id[point["leading"]]
                prev_name = next((_t(a["name"], "en") for a in self.scenario_config["archetypes"] if a["id"] == prev["leading"]), prev["leading"])
                prev_name_fi = next((_t(a["name"], "fi") for a in self.scenario_config["archetypes"] if a["id"] == prev["leading"]), prev["leading"])
                push(("leader", point["date"], point["leading"]), "leader_change", "high",
                     {"en": f"Most likely scenario changed to '{_t(new['name'])}'", "fi": f"Todennäköisin skenaario vaihtui: '{_t(new['name'], 'fi')}'"},
                     {"en": f"{_t(new['name'])} is now at {new['probability']:.0%}; previously the leading scenario was '{prev_name}'.",
                      "fi": f"{_t(new['name'], 'fi')} on nyt {new['probability']:.0%}; aiemmin johtava skenaario oli '{prev_name_fi}'."}, scenario_id=new["id"])
            for s in sc["scenarios"]:
                p0 = prev["probs"].get(s["id"])
                if p0 is None:
                    continue
                delta_pp = (s["probability"] - p0) * 100
                if abs(delta_pp) >= float(n["probability_change_pp"]):
                    push(("change", point["date"], s["id"]), "large_change", "high",
                         {"en": f"Large change: {_t(s['name'])} {delta_pp:+.1f} pp since {prev['date']}", "fi": f"Suuri muutos: {_t(s['name'], 'fi')} {delta_pp:+.1f} %-yks. ({prev['date']})"},
                         {"en": f"Probability moved from {p0:.0%} to {s['probability']:.0%}. Open the scenario to see which signals contributed.",
                          "fi": f"Todennäköisyys muuttui {p0:.0%} → {s['probability']:.0%}. Avaa skenaario nähdäksesi vaikuttaneet signaalit."}, scenario_id=s["id"])

        for s in self.signals:
            weight = w[s["id"]]["weight"]
            thr = float(n["major_signal_weight"]) * (0.5 if s.get("locked") else 1.0)
            if weight >= thr and weight > 0:
                f = w[s["id"]]["components"]["freshness"]
                push(("major", s["id"], round(weight, 2)), "major_signal", "high" if not s.get("locked") else "medium",
                     {"en": f"Major signal: {s.get('short')}", "fi": f"Merkittävä signaali: {s.get('short_fi', s.get('short'))}"},
                     {"en": f"Computed weight {weight:.2f} (reliability {s.get('reliability')}, freshness {f:.2f}). Source: {s['source'].get('name')} ({s['source'].get('date') or 'undated'}).",
                      "fi": f"Laskettu paino {weight:.2f} (luotettavuus {s.get('reliability')}, tuoreus {f:.2f}). Lähde: {s['source'].get('name')} ({s['source'].get('date') or 'ei päivää'})."}, signal_id=s["id"])

        for s in self.signals:
            if s.get("measures") != "price" or len(s.get("history", [])) < 2:
                continue
            a, b = s["history"][-2]["value"], s["history"][-1]["value"]
            if not a:
                continue
            pctm = (b - a) / abs(a) * 100
            thr = float(n["price_change_pct"]) * (0.5 if s.get("locked") else 1.0)
            if abs(pctm) >= thr:
                kind_en = "Tracked signal" if s.get("locked") else "Price signal"
                kind_fi = "Seurattu signaali" if s.get("locked") else "Hintasignaali"
                push(("price", s["id"], s["history"][-1]["date"]), "price_move", "medium",
                     {"en": f"{kind_en} moved: {s.get('short')} {pctm:+.1f}%", "fi": f"{kind_fi} liikkui: {s.get('short_fi', s.get('short'))} {pctm:+.1f} %"},
                     {"en": f"From {a:,.0f} to {b:,.0f} {s['value'].get('unit', '')} between {s['history'][-2]['date']} and {s['history'][-1]['date']}.",
                      "fi": f"{a:,.0f} → {b:,.0f} {s['value'].get('unit', '')} välillä {s['history'][-2]['date']} – {s['history'][-1]['date']}."}, signal_id=s["id"])

        for s in self.signals:
            if s.get("locked"):
                tr = s.setdefault("tracking", {"checks": 0, "last_checked": None})
                tr["checks"] = int(tr.get("checks", 0)) + 1
                tr["last_checked"] = now().isoformat(timespec="minutes")

        self.last_run = now()
        self.runs_completed += 1
        self.next_run = now() + timedelta(minutes=self.settings["run_interval_minutes"])
        return created

    # ---- full state ---------------------------------------------------------------
    def state(self) -> dict[str, Any]:
        with self.lock:
            return self._state()

    def _state(self) -> dict[str, Any]:
        w = self.weights()
        sc = self.scenarios(w)
        strong = float(self.settings.get("strong_signal_weight", 0.25))
        signals = []
        for s in self.signals:
            weight = w[s["id"]]["weight"]
            cls = "inactive" if weight <= 0 else ("strong" if weight >= strong else "weak")
            signals.append({**s, "computed": w[s["id"]], "strength_class": cls, "source_class_label": SOURCE_CLASSES.get(s.get("source_class", "news"), SOURCE_CLASSES["news"])})
        if self.brief is None:
            ctx = self._context(); ctx.weights, ctx.after = w, sc
            ctx.bullwhip = compute_bullwhip(self.bullwhip_config)
            self.brief = {"text": build_brief(ctx), "next_step": _next_analysis_step(ctx), "generated_on": today().isoformat(), "mode": "code"}
        prev = self.previous_day()
        for s in sc["scenarios"]:
            p0 = prev["probs"].get(s["id"]) if prev else None
            s["delta_pp"] = round((s["probability"] - p0) * 100, 2) if p0 is not None else None
        return {
            "meta": {"app": "Irma", "today": today().isoformat(), "llm_mode": self.llm.mode, "model": os.environ.get("ABB_MODEL", "claude-opus-5-5"),
                     "horizon_months": [12, 36], "agents": self.pipeline.describe(), "source_classes": SOURCE_CLASSES,
                     "suggested_prompts": SUGGESTED_PROMPTS, "world": self.world, "worlds": list(WORLDS.values()), "languages": ["en", "fi"]},
            "scheduler": {"interval_minutes": self.settings["run_interval_minutes"], "last_run": self.last_run.isoformat(timespec="minutes") if self.last_run else None,
                          "next_run": self.next_run.isoformat(timespec="minutes") if self.next_run else None, "runs_completed": self.runs_completed},
            "settings": self.settings,
            "summary": {"en": plain_summary(sc, self.signals, w, "en"), "fi": plain_summary(sc, self.signals, w, "fi")},
            "axis_scores": axis_scores(self.signals, w),
            "signals": signals,
            "evidence": self.evidence,
            "scenarios": sc,
            "scaling_note": self.scenario_config.get("scaling_note"),
            "history": {"points": self.history, "note": {"en": f"Points before {today().isoformat()} are simulated demonstration data (DEMODATA); today's point is computed live.",
                                                           "fi": f"Pisteet ennen {today().isoformat()} ovat simuloitua esittelydataa (DEMODATA); tämän päivän piste lasketaan reaaliaikaisesti."}},
            "bullwhip": compute_bullwhip(self.bullwhip_config),
            "brief": self.brief,
            "notifications": self.notifications[:50],
            "unread": sum(1 for x in self.notifications if not x["read"]),
            "runs": [{"id": r["id"], "title": r["title"], "ran_at": r["ran_at"]} for r in self.runs],
            "scout": self.scout_public(),
        }


    # ---- saved additions (signals found by the scout, current world only) ---------------
    def _load_additions(self) -> None:
        self.additions = {"signals": {}, "evidence": {}}
        self.seen = {}
        if self.world != 1 or not self.additions_path.exists():
            return
        try:
            data = json.loads(self.additions_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return
        for card in data.get("signals", []):
            idx = next((i for i, s in enumerate(self.signals) if s["id"] == card["id"]), None)
            if idx is None:
                self.signals.append(card)
            else:
                self.signals[idx] = card
            self.additions["signals"][card["id"]] = card
        have = {e["id"] for e in self.evidence}
        for ce in data.get("evidence", []):
            if ce["id"] not in have:
                self.evidence.append(ce)
            self.additions["evidence"][ce["id"]] = ce
        max_age = int(scout_settings(self.settings.get("web_search")).get("max_age_days", 30))
        cutoff = (today() - timedelta(days=max_age)).isoformat()
        self.seen = {k: v for k, v in (data.get("seen") or {}).items() if str(v.get("at", "")) >= cutoff}
        if not self.scout_state["runs"]:
            self.scout_state["runs"] = list(data.get("runs") or [])[-20:]

    def _save_additions(self) -> None:
        if self.world != 1:
            return
        self.additions_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"note": "Signals and counter-evidence added by the automatic web search (scout). Delete this file to remove them.",
                   "signals": list(self.additions["signals"].values()), "evidence": list(self.additions["evidence"].values()),
                   "seen": self.seen, "runs": self.scout_state["runs"][-20:]}
        self.additions_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    def clear_additions(self) -> None:
        with self.lock:
            if self.additions_path.exists():
                self.additions_path.unlink()
            self.scout_state["runs"] = []
            self._reset(self.world)

    def _sync_blocked_domains(self) -> list[str]:
        """Persist domains the API reported as inaccessible and drop them from the allowlist. Caller holds the lock."""
        ws = self.settings.get("web_search") or {}
        new = sorted(set(self.llm.blocked_domains) - set(ws.get("blocked_domains") or []))
        if new:
            self.save_settings({"web_search": {"blocked_domains": sorted(set(ws.get("blocked_domains") or []) | set(new))}})
        return new

    # ---- notifications outside the cycle ------------------------------------------------
    def notify(self, kind: str, severity: str, title: dict[str, str], text: dict[str, str], signal_id: str | None = None) -> None:
        self.notifications.insert(0, {"id": f"N-{len(self.notifications) + 1:04d}", "time": now().isoformat(timespec="minutes"), "kind": kind,
                                      "severity": severity, "title": title["en"], "text": text["en"], "title_fi": title["fi"], "text_fi": text["fi"],
                                      "signal_id": signal_id, "scenario_id": None, "read": False, "reason": kind})

    # ---- run the pipeline on a copy, commit the result ------------------------------------
    def _work_context(self, item: dict[str, Any], replay: dict[str, Any] | None = None) -> Context:
        with self.lock:
            return Context(today=today(), signals=copy.deepcopy(self.signals), evidence=copy.deepcopy(self.evidence),
                           scenario_config=self.scenario_config, bullwhip_config=self.bullwhip_config,
                           replay=self.replay if replay is None else replay, llm=self.llm, item=item,
                           web=copy.deepcopy(self.settings.get("web_search")))

    def _commit(self, ctx: Context, origin: str, extra: dict[str, Any] | None = None) -> tuple[str, str]:
        """Merge the pipeline result (built on copies) into live state. Caller holds the lock."""
        sig = copy.deepcopy(ctx.new_signal)
        old_id = sig["id"]
        ce_map: dict[str, str] = {}
        new_ces = []
        for ce in ctx.new_evidence:
            nid = next_id(self.evidence, "CE")
            ce_map[ce["id"]] = nid
            c2 = {**copy.deepcopy(ce), "id": nid}
            self.evidence.append(c2)
            new_ces.append(c2)
        sig["counter_evidence"] = [ce_map.get(x, x) for x in sig.get("counter_evidence", [])]
        if extra:
            sig.update(extra)
        live = next((s for s in self.signals if s["id"] == old_id), None) if ctx.is_update else None
        if live is not None:
            for k in ("annotations", "locked", "tracking"):
                sig[k] = live.get(k, sig.get(k))
            self.signals[self.signals.index(live)] = sig
            final_id = old_id
        else:
            final_id = next_id(self.signals, "SIG")
            sig["id"] = final_id
            for c in new_ces:
                c["against"] = final_id
            self.signals.append(sig)
        if origin == "scout" and self.world == 1:
            self.additions["signals"][final_id] = sig
            for c in new_ces:
                self.additions["evidence"][c["id"]] = c
        return final_id, old_id

    def process_item(self, item: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        """Manual import: full pipeline on a copy, then always committed."""
        ctx = self._work_context(item)
        self.pipeline.run(ctx)
        with self.lock:
            final_id, old_id = self._commit(ctx, "import") if ctx.new_signal else (None, None)
            brief = copy.deepcopy(ctx.brief)
            if brief and final_id and final_id != old_id:
                brief["text"] = brief["text"].replace(f"[{old_id}]", f"[{final_id}]")
            self.brief = brief
            run_id = f"RUN-{len(self.runs) + 1:03d}"
            record = {"id": run_id, "title": item.get("title"), "ran_at": now().isoformat(timespec="seconds"), "trace": [t.as_dict() for t in ctx.trace],
                      "new_signal_id": final_id, "scenarios_before": ctx.before, "scenarios_after": ctx.after,
                      "interpretation": ctx.interpretation, "brief": brief, "bullwhip": ctx.bullwhip}
            self.runs.append(record)
            self._sync_blocked_domains()
            created = self._cycle("new_information")
            if final_id:
                card = next(s for s in self.signals if s["id"] == final_id)
                wgt = self.weights()[final_id]["weight"]
                self.notified.add(("info", run_id))
                self.notify("new_information", "low",
                            {"en": f"New information processed: {card.get('short')}", "fi": f"Uusi tieto käsitelty: {card.get('short_fi', card.get('short'))}"},
                            {"en": f"Card {final_id} updated; computed weight {wgt:.2f}.", "fi": f"Kortti {final_id} päivitetty; laskettu paino {wgt:.2f}."}, final_id)
            return record, created

    # ---- the scout -------------------------------------------------------------------------
    def scout_eligibility(self) -> tuple[bool, str]:
        ws = self.settings.get("web_search") or {}
        if self.world != 1:
            return False, "world"
        if self.llm.mode != "live":
            return False, "no_key"
        if not ws.get("enabled"):
            return False, "web_off"
        if not scout_settings(ws).get("enabled"):
            return False, "scout_off"
        return True, ""

    def scout_public(self) -> dict[str, Any]:
        ok, why = self.scout_eligibility()
        return {"running": self.scout_state["running"], "started_at": self.scout_state["started_at"], "eligible": ok,
                "skip": SKIP_REASONS.get(why) if not ok else None, "runs": list(reversed(self.scout_state["runs"][-10:])),
                "found": len(self.additions["signals"]), "settings": scout_settings(self.settings.get("web_search")), "themes": THEMES}

    def start_scout(self, why: str) -> str:
        ok, skip = self.scout_eligibility()
        if not ok:
            return f"skipped:{skip}"
        with self.lock:
            if self.scout_state["running"]:
                return "already_running"
            self.scout_state["running"] = True
            self.scout_state["started_at"] = now().isoformat(timespec="seconds")
        threading.Thread(target=self._scout_thread, args=(why,), daemon=True).start()
        return "started"

    def _scout_thread(self, why: str) -> None:
        try:
            self.run_scout(why)
        except Exception as exc:  # pragma: no cover - keep the server alive
            with self.lock:
                self.scout_state["runs"].append({"id": next_id(self.scout_state["runs"], "SCOUT"), "at": now().isoformat(timespec="seconds"),
                                                 "reason": why, "status": "failed", "error": str(exc), "candidates": [], "accepted": 0, "rejected": 0})
        finally:
            self.scout_state["running"] = False

    def run_scout(self, why: str) -> dict[str, Any]:
        """Discovery, pre-gate, full check on a copy, post-gate, commit. Nothing is added unless every check passes."""
        t0 = time.time()
        with self.lock:
            world = self.world
            web = copy.deepcopy(self.settings.get("web_search") or DEFAULT_WEB_SETTINGS)
            cfg = scout_settings(web)
            snapshot = copy.deepcopy(self.signals)
            known = known_urls(self.signals, self.evidence, self.seen)
            seen = dict(self.seen)
            run_id = next_id(self.scout_state["runs"], "SCOUT")
        record: dict[str, Any] = {"id": run_id, "at": now().isoformat(timespec="seconds"), "reason": why, "status": "running",
                                  "candidates": [], "accepted": 0, "rejected": 0, "searches": 0, "queries": [],
                                  "usage": {"input_tokens": 0, "output_tokens": 0}}

        def add_usage(u: dict[str, Any] | None) -> None:
            for k in ("input_tokens", "output_tokens"):
                record["usage"][k] += int((u or {}).get(k, 0) or 0)

        system, prompt = build_prompt(today(), cfg, snapshot, seen)
        text, evidence, meta = self.llm.research(system, prompt, {**web, "max_searches": cfg["max_searches"]})
        add_usage(meta.get("usage"))
        if text is None:
            record.update(status="failed", error=meta.get("error") or "web search unavailable")
            return self._finish_scout(record, t0)
        record["searches"] += evidence["searches"]
        record["queries"] = [q.get("query") or q.get("url", "") for q in evidence["queries"]]
        items = extract_json(text, "array")
        if not isinstance(items, list):
            record.update(status="failed", error="the search answer contained no JSON list")
            return self._finish_scout(record, t0)
        taken = 0
        for cand in [x for x in items if isinstance(x, dict)]:
            ok, rsn, info = pre_gate(cand, evidence, today(), cfg, web, known, snapshot)
            entry = {"title": str(cand.get("title") or "")[:200], "url": info.get("url") or "", "source_name": str(cand.get("source_name") or "")[:120],
                     "date": info.get("date"), "grade": info.get("grade"), "theme": cand.get("theme"), "why_signal": str(cand.get("why_signal") or "")[:300]}
            if ok and taken >= int(cfg["max_candidates"]):
                ok, rsn = False, scout_reason("over_limit", n=cfg["max_candidates"])
            elif ok:
                taken += 1
                ok, rsn, extra = self._check_candidate(cand, info, world, known, record)
                entry.update(extra)
            entry.update(decision="accepted" if ok else "rejected", reason=rsn)
            record["candidates"].append(entry)
            if entry["url"] and rsn["code"] != "over_limit":
                self.seen[norm_url(entry["url"])] = {"at": today().isoformat(), "code": rsn["code"]}
        record["accepted"] = sum(1 for c in record["candidates"] if c["decision"] == "accepted")
        record["rejected"] = len(record["candidates"]) - record["accepted"]
        record["status"] = "done"
        if not record["candidates"]:
            record["note"] = {"en": "No source met the criteria; nothing was added.", "fi": "Yksikään lähde ei täyttänyt ehtoja; mitään ei lisätty."}
        elif not record["accepted"]:
            record["note"] = {"en": "Candidates were found but none passed every check; nothing was added.", "fi": "Ehdokkaita löytyi, mutta yksikään ei läpäissyt kaikkia tarkistuksia; mitään ei lisätty."}
        return self._finish_scout(record, t0)

    def _check_candidate(self, cand: dict[str, Any], info: dict[str, Any], world: int, known: dict[str, str],
                         record: dict[str, Any]) -> tuple[bool, dict[str, str], dict[str, Any]]:
        item = {"title": str(cand.get("title") or "")[:200], "text": f"{cand.get('summary') or ''}\n\nQuote from the source: {cand.get('quote') or ''}",
                "date": info["date"], "source_name": str(cand.get("source_name") or host_of(info["url"]))[:120],
                "source_url": info["url"], "data_label": "SOURCE"}
        ctx = self._work_context(item, replay={})
        try:
            self.pipeline.run(ctx, full=False)
        except Exception as exc:  # pragma: no cover
            return False, scout_reason("pipeline_error", error=str(exc)[:120]), {}
        v = (ctx.new_signal or {}).get("verification") or {}
        cs = (ctx.new_signal or {}).get("counter_search") or {}
        record["searches"] += int(v.get("searches", 0) or 0) + int(cs.get("searches", 0) or 0)
        for u in (v.get("usage"), cs.get("usage")):
            for k in ("input_tokens", "output_tokens"):
                record["usage"][k] += int((u or {}).get(k, 0) or 0)
        weights = compute_weights(ctx.signals, ctx.evidence, today())
        with self.lock:
            live = copy.deepcopy(self.signals)
        ok, rsn = post_gate(ctx, scout_settings(ctx.web), weights, today(), live, known)
        extra = {"weight": round(float(weights.get(ctx.new_signal["id"], {}).get("weight", 0.0)), 3) if ctx.new_signal else None,
                 "reliability": (ctx.new_signal or {}).get("reliability"), "corroborated": bool(v.get("corroborated"))}
        if not ok:
            return False, rsn, extra
        with self.lock:
            if self.world != world:
                return False, scout_reason("pipeline_error", error="world situation changed during the run"), extra
            final_id, _ = self._commit(ctx, "scout", {"origin": "scout", "theme": cand.get("theme"), "why_signal": str(cand.get("why_signal") or "")[:300],
                                                      "found_at": now().isoformat(timespec="minutes")})
            self.brief = None
            self._cycle("scout")
            card = next(s for s in self.signals if s["id"] == final_id)
            wgt = self.weights()[final_id]["weight"]
            self.notify("new_signal_found", "medium",
                        {"en": f"New signal found on the web: {card.get('short')}", "fi": f"Uusi signaali löytyi verkosta: {card.get('short_fi', card.get('short'))}"},
                        {"en": f"{card['source'].get('name')}, {card['source'].get('date') or card.get('observed_at')}. Verified against a primary source and challenged by a counter-evidence search; weight {wgt:.2f}.",
                         "fi": f"{card['source'].get('name')}, {card['source'].get('date') or card.get('observed_at')}. Tarkistettu ensisijaisesta lähteestä ja haastettu vastanäytön haulla; paino {wgt:.2f}."}, final_id)
        extra["signal_id"] = final_id
        return True, rsn, extra

    def _finish_scout(self, record: dict[str, Any], t0: float) -> dict[str, Any]:
        record["duration_s"] = round(time.time() - t0, 1)
        u = record["usage"]
        record["est_cost_usd"] = round(record["searches"] * 0.01 + u["input_tokens"] * 4e-6 + u["output_tokens"] * 20e-6, 3)
        record["cost_note"] = "Searches at USD 0.01 plus Claude Opus 5.5 tokens for discovery, verification and counter-evidence; the classifier's own tokens are not included."
        with self.lock:
            removed = self._sync_blocked_domains()
            if removed:
                record["domains_removed"] = removed
            self.scout_state["runs"].append(record)
            self.scout_state["runs"] = self.scout_state["runs"][-20:]
            self._save_additions()
        return record


STORE = Store()


async def scheduler_loop() -> None:
    while True:
        await asyncio.sleep(20)
        try:
            if STORE.next_run and now() >= STORE.next_run:
                STORE.cycle("scheduled")
                STORE.start_scout("scheduled")
        except Exception:  # pragma: no cover
            pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(scheduler_loop())
    STORE.start_scout("startup")
    try:
        yield
    finally:
        task.cancel()


app = FastAPI(title="Irma API", version="0.3.0", lifespan=lifespan)


class AnnotateBody(BaseModel):
    action: str
    note: Optional[str] = ""
    author: Optional[str] = "planner"


class LockBody(BaseModel):
    locked: bool


class WorldBody(BaseModel):
    world: int


class RunBody(BaseModel):
    preset: Optional[str] = None
    title: Optional[str] = None
    text: Optional[str] = None
    date: Optional[str] = None
    source_name: Optional[str] = None
    source_url: Optional[str] = None
    data_label: Optional[str] = "DEMODATA"


class AskBody(BaseModel):
    question: str
    lang: Optional[str] = "en"


class SettingsBody(BaseModel):
    run_interval_minutes: Optional[int] = None
    notifications: Optional[dict[str, Any]] = None
    strong_signal_weight: Optional[float] = None
    web_search: Optional[dict[str, Any]] = None


@app.get("/api/state")
def get_state() -> dict[str, Any]:
    return STORE.state()


@app.post("/api/world")
def set_world(body: WorldBody) -> dict[str, Any]:
    if body.world not in WORLDS:
        raise HTTPException(400, "unknown world")
    STORE.reset(body.world)
    return {"world": STORE.world, "state": STORE.state()}


@app.get("/api/signals/{signal_id}")
def get_signal(signal_id: str) -> dict[str, Any]:
    with STORE.lock:
        return _get_signal(signal_id)


def _get_signal(signal_id: str) -> dict[str, Any]:
    sig = next((s for s in STORE.signals if s["id"] == signal_id), None)
    if sig is None:
        raise HTTPException(404, "signal not found")
    w = STORE.weights()
    sc = STORE.scenarios(w)
    strong = float(STORE.settings.get("strong_signal_weight", 0.25))
    weight = w[signal_id]["weight"]
    contributions = {s["id"]: next((c for c in s["contributions"] if c["signal_id"] == signal_id), None) for s in sc["scenarios"]}
    return {**sig, "computed": w[signal_id], "strength_class": "inactive" if weight <= 0 else ("strong" if weight >= strong else "weak"),
            "source_class_label": SOURCE_CLASSES.get(sig.get("source_class", "news"), SOURCE_CLASSES["news"]),
            "counter_cards": [e for e in STORE.evidence if e["against"] == signal_id], "contributions": contributions,
            "scenario_names": {s["id"]: s["name"] for s in sc["scenarios"]}}


@app.post("/api/signals/{signal_id}/annotate")
def annotate(signal_id: str, body: AnnotateBody) -> dict[str, Any]:
    sig = next((s for s in STORE.signals if s["id"] == signal_id), None)
    if sig is None:
        raise HTTPException(404, "signal not found")
    if body.action not in ("confirm", "dispute", "comment"):
        raise HTTPException(400, "action must be confirm, dispute or comment")
    with STORE.lock:
        sig.setdefault("annotations", []).append({"action": body.action, "note": body.note or "", "author": body.author, "at": now().isoformat(timespec="seconds")})
        if sig["id"] in STORE.additions["signals"]:
            STORE._save_additions()
        STORE.brief = None
        STORE.cycle("annotation")
    return get_signal(signal_id)


@app.post("/api/signals/{signal_id}/lock")
def lock(signal_id: str, body: LockBody) -> dict[str, Any]:
    sig = next((s for s in STORE.signals if s["id"] == signal_id), None)
    if sig is None:
        raise HTTPException(404, "signal not found")
    with STORE.lock:
        sig["locked"] = bool(body.locked)
        tr = sig.setdefault("tracking", {"checks": 0, "last_checked": None})
        tr["locked_at"] = now().isoformat(timespec="minutes") if body.locked else None
        STORE.cycle("lock")
    return get_signal(signal_id)


@app.post("/api/run")
def run_pipeline(body: RunBody) -> dict[str, Any]:
    if body.preset:
        preset = STORE.replay.get(body.preset)
        if not preset:
            raise HTTPException(404, "unknown preset")
        item = dict(preset["item"])
    else:
        if not body.text:
            raise HTTPException(400, "text is required")
        item = {"title": body.title or "", "text": body.text, "date": body.date or "", "source_name": body.source_name or "",
                "source_url": body.source_url or "", "data_label": body.data_label or "DEMODATA"}
    record, created = STORE.process_item(item)
    return {"run": record, "state": STORE.state(), "notifications_created": created}


@app.get("/api/runs/{run_id}")
def get_run(run_id: str) -> dict[str, Any]:
    r = next((r for r in STORE.runs if r["id"] == run_id), None)
    if r is None:
        raise HTTPException(404, "run not found")
    return r


@app.post("/api/cycle")
def run_cycle() -> dict[str, Any]:
    created = STORE.cycle("manual")
    scout = STORE.start_scout("manual")
    return {"notifications_created": created, "scout": scout, "state": STORE.state()}


@app.get("/api/scout")
def get_scout() -> dict[str, Any]:
    with STORE.lock:
        return STORE.scout_public()


@app.post("/api/scout/run")
def run_scout_now() -> dict[str, Any]:
    status = STORE.start_scout("manual")
    with STORE.lock:
        return {"status": status, "scout": STORE.scout_public()}


@app.post("/api/scout/clear")
def clear_scouted() -> dict[str, Any]:
    STORE.clear_additions()
    return {"ok": True, "state": STORE.state()}


@app.get("/api/settings")
def get_settings() -> dict[str, Any]:
    return STORE.settings


@app.put("/api/settings")
def put_settings(body: SettingsBody) -> dict[str, Any]:
    with STORE.lock:
        return STORE.save_settings({k: v for k, v in body.model_dump().items() if v is not None})


@app.get("/api/notifications")
def get_notifications() -> dict[str, Any]:
    return {"notifications": STORE.notifications, "unread": sum(1 for x in STORE.notifications if not x["read"])}


@app.post("/api/notifications/{note_id}/read")
def read_notification(note_id: str) -> dict[str, Any]:
    for x in STORE.notifications:
        if x["id"] == note_id:
            x["read"] = True
    return get_notifications()


@app.post("/api/notifications/read-all")
def read_all() -> dict[str, Any]:
    for x in STORE.notifications:
        x["read"] = True
    return get_notifications()


# ---- assistant --------------------------------------------------------------------
def _intent(q: str) -> str:
    ql = q.lower()
    if any(k in ql for k in ("summar", "key change", "what changed", "changes", "overview", "happened", "tiivist", "muutok", "yhteenveto")):
        return "summary"
    if any(k in ql for k in ("procure", "next move", "next step", "purchas", "buy", "order", "hankin", "seuraava", "tilau", "osta")):
        return "procurement"
    if any(k in ql for k in ("component", "supply", "parts", "memory", "dram", "mcu", "lead time", "lead-time", "semiconductor", "komponent", "saatavuu", "muisti", "toimitusai")):
        return "components"
    return "general"


def _compose(intent: str, sc: dict[str, Any], w: dict[str, Any], lang: str) -> tuple[str, list[dict[str, Any]]]:
    lead = sc["scenarios"][0]
    by_id = {s["id"]: s for s in STORE.signals}
    prev = STORE.previous_day()
    fi = lang == "fi"
    short = lambda s: s.get("short_fi", s.get("short")) if fi else s.get("short")

    def cite(ids: list[str]) -> list[dict[str, Any]]:
        return [{"signal_id": i, "short": short(by_id[i]), "weight": w[i]["weight"], "source": by_id[i]["source"], "data_label": by_id[i]["data_label"]} for i in ids if i in by_id]

    if intent == "summary":
        moves = sorted(sc["scenarios"], key=lambda s: -abs(s.get("delta_pp") or 0))
        recent = sorted([s for s in STORE.signals if s.get("observed_at")], key=lambda s: s["observed_at"], reverse=True)[:3]
        notes = STORE.notifications[:4]
        p0 = prev["probs"].get(lead["id"]) if prev else None
        if fi:
            text = (f"Todennäköisin skenaario: '{_t(lead['name'], 'fi')}' ({lead['probability']:.0%}" + (f", {(lead['probability'] - p0) * 100:+.1f} %-yks. edellisestä päivästä)." if p0 is not None else ").")
                    + f" Epävarmuus neljän skenaarion välillä on {sc['entropy']:.2f}. Suurimmat päivämuutokset: " + "; ".join(f"{_t(m['name'], 'fi')} {m.get('delta_pp') or 0:+.1f} %-yks." for m in moves[:2]) + ". "
                    + "Tuoreimmat havainnot: " + "; ".join(f"[{s['id']}] {short(s)} ({s['observed_at']}, paino {w[s['id']]['weight']:.2f})" for s in recent) + ". "
                    + (("Avoimet ilmoitukset: " + "; ".join(n.get('title_fi', n['title']) for n in notes) + ". ") if notes else "")
                    + f"Kysynnän laatu: {compute_bullwhip(STORE.bullwhip_config)['summary']}")
        else:
            text = (f"Most likely scenario: '{_t(lead['name'])}' at {lead['probability']:.0%}" + (f" ({(lead['probability'] - p0) * 100:+.1f} pp since {prev['date']})." if p0 is not None else ".")
                    + f" Uncertainty across the four scenarios is {sc['entropy']:.2f}. Largest daily moves: " + "; ".join(f"{_t(m['name'])} {m.get('delta_pp') or 0:+.1f} pp" for m in moves[:2]) + ". "
                    + "Most recent evidence: " + "; ".join(f"[{s['id']}] {short(s)} ({s['observed_at']}, weight {w[s['id']]['weight']:.2f})" for s in recent) + ". "
                    + (("Open notifications: " + "; ".join(n['title'] for n in notes) + ". ") if notes else "")
                    + f"Demand quality: {compute_bullwhip(STORE.bullwhip_config)['summary']}")
        return text, cite([s["id"] for s in recent])

    if intent == "procurement":
        ctx = STORE._context(); ctx.weights, ctx.after = w, sc
        ns = _next_analysis_step(ctx)
        comp = _t(lead["abb_interpretation"]["components"], lang)
        watch = "; ".join(f"[{x['signal_id']}] {short(by_id[x['signal_id']])}" for x in ns["watch"][:4] if x["signal_id"] in by_id)
        refute = "; ".join(f"{_t(f['text'], lang)} [{f['signal_id']}]" for f in lead["falsifiers"][:2])
        if fi:
            text = ("Irma ei suosittele tilausmääriä tai ajoitusta; ne riippuvat sopimuksista, allokaatiosopimuksista ja kassatilanteesta, jotka eivät ole datassa. "
                    f"Seuraava analyyttinen askel, jota Irma tukee: (1) seuraa nykyistä kuvaa kantavia signaaleja: {watch}; (2) arvioi uudelleen {ns['reevaluate_on']} yhdessä: {', '.join(ns['review_with'])}; "
                    f"(3) testaa johtavaa skenaariota sen kumoavilla merkeillä: {refute}. Johtavan skenaarion ehdollinen tulkinta komponenteista: {comp}")
        else:
            text = ("Irma does not recommend order quantities or timing; those depend on contracts, allocation agreements and cash position that are not in the data. "
                    f"The next analytical move it supports: (1) follow the signals carrying the current picture: {watch}; (2) re-evaluate on {ns['reevaluate_on']} with the {', '.join(ns['review_with'])}; "
                    f"(3) test the leading scenario against its refuting indications: {refute}. Conditional reading of the leading scenario for components: {comp}")
        return text, cite([x["signal_id"] for x in ns["watch"][:4]])

    if intent == "components":
        supply = sorted([s for s in STORE.signals if s.get("source_class") == "price" or s.get("category") in ("supply", "bullwhip")], key=lambda s: -w[s["id"]]["weight"])[:4]
        bw = compute_bullwhip(STORE.bullwhip_config)
        ev = "; ".join(f"[{s['id']}] {short(s)}: {s['value'].get('label') or ''} ({s['source'].get('name')}, {s['source'].get('date') or '—'})" for s in supply)
        metrics = "; ".join(f"{m['name']} = {m['value'] if m['value'] is not None else '—'} ({m['status'].replace('_', ' ')})" for m in bw["metrics"])
        if fi:
            text = (f"Releiden komponenttien saatavuus on johtavassa skenaariossa '{_t(lead['supply'], 'fi')}'. Näyttö: {ev}. Kysynnän laadun tarkistus: {bw['summary']} Mittarit: {metrics}. "
                    "Sisäinen osatason näkymä (toimittajavahvistukset, allokaatiokirjeet) ei ole vielä kytketty; katso paikkamerkkikortti [SIG-017].")
        else:
            text = (f"Component supply for the relays is read as '{_t(lead['supply'])}' in the leading scenario. Evidence: {ev}. Demand quality check: {bw['summary']} Metrics: {metrics}. "
                    "The internal part-level view (supplier confirmations, allocation letters) is not connected yet; see the placeholder card [SIG-017].")
        return text, cite([s["id"] for s in supply])
    return "", []


ASK_SYSTEM = """You are Irma, the assistant in a market-scenario monitor for ABB's protection-relay business. Answer in LANGUAGE.
Format: plain text only, no Markdown: no asterisks, no headings, no bold or italics. At most 120 words. Use short sentences;
if you list items, put each on its own line starting with "- ", at most four items.
Content: answer the question directly from the evidence given. Cite every signal you use by its id in square brackets, for
example [SIG-010]. Check the signal catalogue before saying a topic is not covered; if it really is not covered, say so in
one sentence and name the closest card. State the main uncertainty in one sentence.
Boundary: do not recommend purchases, quantities or the timing of orders. If the question asks for that, say once, in one
sentence, that the decision is the planner's, and then give the evidence."""

# Words in questions mapped to the terms the signal cards use.
ASK_SYNONYMS = {
    "busbar": "copper", "busbars": "copper", "kisko": "copper", "kiskot": "copper", "kupari": "copper", "cable": "copper", "kaapeli": "copper",
    "chip": "semiconductor", "chips": "semiconductor", "siru": "semiconductor", "sirut": "semiconductor", "muisti": "memory dram", "puolijohde": "semiconductor",
    "datakeskus": "data centre", "datakeskukset": "data centre", "verkko": "grid", "sähköverkko": "grid", "liittymä": "connection", "hinta": "price",
}


@app.post("/api/ask")
def ask(body: AskBody) -> dict[str, Any]:
    q = body.question.strip()
    if not q:
        raise HTTPException(400, "question is required")
    lang = "fi" if (body.lang or "en").lower().startswith("fi") else "en"
    w = STORE.weights()
    sc = STORE.scenarios(w)
    prev = STORE.previous_day()
    for s in sc["scenarios"]:
        p0 = prev["probs"].get(s["id"]) if prev else None
        s["delta_pp"] = round((s["probability"] - p0) * 100, 2) if p0 is not None else None
    intent = _intent(q)
    composed, citations = _compose(intent, sc, w, lang)
    words = {t for t in re.findall(r"[a-z0-9äöå]+", q.lower()) if len(t) > 3}
    words |= {x for t in list(words) for x in ASK_SYNONYMS.get(t, "").split() if len(x) > 3}

    def score(s: dict[str, Any]) -> int:
        hay = f"{s['name']} {s['short']} {s.get('short_fi', '')} {s['excerpt']} {s['classification_rationale']} {s['category']} {s['region']}".lower()
        return sum(1 for t in words if t in hay)

    candidates = [s for s in STORE.signals if w[s["id"]]["weight"] > 0]
    ranked = sorted(candidates, key=lambda s: (-score(s), -w[s["id"]]["weight"]))
    hits = [s for s in ranked if score(s) > 0][:4]
    if not citations:
        citations = [{"signal_id": s["id"], "short": s.get("short_fi", s["short"]) if lang == "fi" else s["short"], "weight": w[s["id"]]["weight"], "source": s["source"], "data_label": s["data_label"]} for s in hits]
    answer: str | None = None
    mode = "composed" if composed else "retrieval"
    if STORE.llm.mode == "live":
        by_id = {x["id"]: x for x in STORE.signals}
        relevant = "\n".join(f"[{h['id']}] {h['short']}: {(h.get('value') or {}).get('label') or ''} | {h['source'].get('name')}, {h['source'].get('date') or h.get('observed_at') or 'undated'} | weight {w[h['id']]['weight']:.2f}" for h in hits)
        catalogue = "\n".join(f"[{x['id']}] {x['short']} | {(x.get('value') or {}).get('label') or ''} | observed {x.get('observed_at') or 'n/a'} | weight {w[x['id']]['weight']:.2f} | reliability {x.get('reliability')}"
                               for x in sorted(candidates, key=lambda x: -w[x["id"]]["weight"]))
        scen = "\n".join(f"- {_t(x['name'])}: {x['probability']:.0%} (demand {_t(x['demand'])}, components {_t(x['supply'])})" for x in sc["scenarios"])
        prompt = (f"QUESTION: {q}\n\nFOUR MOST LIKELY SCENARIOS:\n{scen}\n\n"
                  + (f"PREPARED ANALYSIS:\n{composed}\n\n" if composed else "")
                  + (f"MOST RELEVANT CARDS:\n{relevant}\n\n" if relevant else "")
                  + f"SIGNAL CATALOGUE (every active card, highest weight first):\n{catalogue}")
        text, meta = STORE.llm.write(ASK_SYSTEM.replace("LANGUAGE", "Finnish" if lang == "fi" else "English"), prompt)
        if text:
            answer, mode = text, "live"
            used = list(dict.fromkeys(re.findall(r"SIG-\d{3}", text)))
            if used:
                citations = [{"signal_id": i, "short": by_id[i].get("short_fi", by_id[i]["short"]) if lang == "fi" else by_id[i]["short"], "weight": w[i]["weight"],
                              "source": by_id[i]["source"], "data_label": by_id[i]["data_label"]} for i in used if i in by_id and i in w]
    if answer is None and composed:
        answer = composed
    if answer is None:
        lead = sc["scenarios"][0]
        if citations:
            answer = (("Kysymykseen liittyvä näyttö: " if lang == "fi" else "Evidence most related to the question: ") + "; ".join(
                f"[{c['signal_id']}] {c['short']} ({c['data_label']}, {'paino' if lang == 'fi' else 'weight'} {c['weight']:.2f}, {c['source']['name']}, {c['source']['date'] or '—'})" for c in citations)
                + (f". Todennäköisin skenaario on '{_t(lead['name'], 'fi')}' ({lead['probability']:.0%}), epävarmuus {sc['entropy']:.2f}. Päätös tilauksista on suunnittelijan." if lang == "fi" else
                   f". The most likely scenario is '{_t(lead['name'])}' at {lead['probability']:.0%}, with uncertainty {sc['entropy']:.2f} across the four. The judgement on what this means for orders rests with the planner."))
        else:
            answer = ("Yksikään signaalikortti ei vastaa hakusanoja. Kokeile alueita (Suomi, Pohjoismaat, USA), lähteitä (Fingrid, TrendForce, IEA) tai teemoja (kupari, DRAM, toimitusaika, liittymäsopimukset)." if lang == "fi" else
                      "No signal card matches those terms. Region names (Finland, Nordics, US), sources (Fingrid, TrendForce, IEA) or themes (copper, DRAM, lead time, connection agreements) can be used.")
    clean, removed = recommendation_filter(answer)
    return {"question": q, "answer": clean, "citations": citations, "mode": mode, "intent": intent, "lang": lang, "guardrail_removed": len(removed)}


@app.post("/api/reset")
def reset() -> dict[str, Any]:
    STORE.reset()
    return {"ok": True, "state": STORE.state()}


@app.get("/api/method")
def method() -> dict[str, Any]:
    from engine.weights import COUNTER_CAP, HALF_LIFE_DAYS, HUMAN_MULTIPLIERS, RELIABILITY, UNCHALLENGED_CAP
    return {
        "weight_formula": "w = R × F × S × (1 − C) × H",
        "reliability": RELIABILITY, "half_life_days": HALF_LIFE_DAYS, "counter_cap": COUNTER_CAP, "unchallenged_cap": UNCHALLENGED_CAP, "human_multipliers": HUMAN_MULTIPLIERS,
        "scenario_formula": "r = Σ_a axes_a × profile_a / Σ_a |profile_a|;  L_s = ln(prior_s) + k × Σ_i (w_i × r_is);  the 4 highest L are shown, p = softmax over the 4",
        "k": STORE.scenario_config.get("scaling_k"), "k_note": STORE.scenario_config.get("scaling_note"),
        "candidates": [{"id": a["id"], "name": a["name"], "profile": a["profile"], "prior": a["prior"]} for a in STORE.scenario_config["archetypes"]],
        "llm_mode": STORE.llm.mode, "model": os.environ.get("ABB_MODEL", "claude-opus-5-5"), "agents": STORE.pipeline.describe(),
        "web_search": {**STORE.settings.get("web_search", {}), "pricing": "Web search USD 10 per 1,000 searches plus tokens; web fetch has no fee, fetched page text counts as input tokens (capped at 8,000 tokens per page)."},
        "principle": "Language models read and classify; code computes every number. The four scenarios shown are the most likely of nine candidate situations given the current signals. No agent produces a purchase recommendation; a deterministic guardrail removes recommendation language from generated text.",
    }


if FRONTEND.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND)), name="static")

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(str(FRONTEND / "index.html"))
