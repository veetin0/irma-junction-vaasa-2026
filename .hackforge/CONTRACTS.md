# Contracts (frozen for M1–M2)

All numbers are computed in Python. Every constant is labelled SOURCE / DEMODATA / ASSUMPTION. Existing response keys are **kept** (additive changes only), so the current UI and tests keep working. Everything must work in replay mode (no API key, Vercel).

## C1 — `engine/weights.py` (task A)
`compute_weights(signals, evidence, today) -> {signal_id: W}` (same signature). `W` keeps every current key and adds:
```
W = {
  "weight": float,                    # headline, now min(1, ·); unchallenged cap 0.6 still applied
  "components": {                     # existing keys kept: reliability, freshness, strength, counter_penalty, human
     ..., "credibility": float,       # Bel: Dempster–Shafer belief incl. corroboration; equals R*(1-C) for single-source cards
     "materiality": float             # mean of available estimators (LLM strength; z-score only when history is SOURCE-labelled)
  },
  "horizon_fit": {"12": float, "24": float, "36": float},   # T(h) in [0,1], log-normal kernel on lead_months, structural persistence
  "horizon":     {"12": float, "24": float, "36": float},   # w_h = weight * T(h)  (<= weight)
  "band": {"min": float, "max": float,
           "methods": {"product": float, "minimum": float, "geometric": float, "arithmetic": float}},
  "attribution": [{"component": "credibility|currency|materiality|human", "share": float, "label": "SOURCE|ASSUMPTION|DEMODATA"}],  # log-share of the discount from 1.0, shares sum to 1 (or [] when weight==1)
  "formula": "w = min(1, Bel × F × M × H); w_h = w × T(h)",
  "assumptions": [{"name": str, "value": float|str, "label": "ASSUMPTION", "why": str}]
}
```
Invariant tests: single-source card with no SOURCE history → `weight` equals the old formula's value to 4 dp; `weight <= 1` even with two "confirm" annotations; `horizon[h] <= weight`; unchallenged cap holds.
Also add `horizon_weights(weights, h:int) -> {id: {"weight": w_h}}` for the scenario engine.

## C2 — `/api/state` horizon view (task A, edits `main.py _state`)
- `meta.horizon_months = [12, 24, 36]`
- `scenarios_by_horizon = {"12": H, "24": H, "36": H}`, `H = {"scenarios": [{"id", "name", "probability", "rank"}], "entropy": float, "leader": id}`, computed with `select_scenarios` on `horizon_weights(w, h)`. The four shown at each horizon may differ from the headline four.
- `scenarios` (headline) is unchanged.

## C3 — `engine/recommend.py` + `data/recommendations.json` (task B)
`build_recommendation(scenarios_result, signals, weights, today, templates) -> R`, exposed as `state["recommendation"]`:
```
R = {
  "scenario_id": str, "scenario_name": {en,fi}, "probability": float,
  "runner_up": {"id", "name": {en,fi}, "probability": float},
  "confidence": "low|medium|high",            # code rule from margin to runner-up and entropy; thresholds ASSUMPTION
  "headline": {en,fi},                         # one sentence: the recommended move
  "moves": [{
     "area": "procurement|manufacturing|capacity|supply_reliability",
     "type": "no_regret|contingent",
     "text": {en,fi},                          # qualitative, conditional; NO quantities, order points or order dates
     "trigger": {en,fi},                       # what would change or activate it
     "trigger_signals": ["SIG-…"],             # real ids present in the current world
     "cost_if_wrong": {en,fi},
     "horizon_months": 12|24|36,
     "label": "ASSUMPTION"
  }],                                          # 3–4 moves, at least one no_regret
  "hedge": {en,fi},                            # what changes if the runner-up wins
  "next_action": {"text": {en,fi}, "owner": {en,fi}, "due": "YYYY-MM-DD"},   # due = today + N days, N ASSUMPTION in templates
  "revisit_on": "YYYY-MM-DD",
  "disclaimer": {en,fi},                       # "The planner decides. No quantities or order timing."
  "label": "ASSUMPTION", "generated_by": "code"
}
```
Templates are keyed by all 9 archetype ids, so every world works. The texts must pass `agents/llm.py` guardrail unchanged in meaning. Narrow the guardrail only if necessary, and keep stripping quantities and order language (with tests). Update the UI-facing strings that say "none of them recommends" only in backend data; the frontend is task D.

## C4 — signal changes (task B)
Each `state.signals[i].change = {"status": "new|up|down|flat|flipped", "weight_prev": float|null, "delta": float|null, "since": "YYYY-MM-DD"}`.
Baseline: the weights recorded at the previous update cycle. On first start, the baseline is `compute_weights` with `today - 7 days` and signals with `observed_at` after that date marked "new". Computed, not invented. flat = |delta| < 0.01 (ASSUMPTION).
`state.signal_changes = [{"signal_id", "status", "delta"}]` sorted by |delta| desc, newest first for "new".

## C5 — negative evidence list (task B)
`state.negative_signals = [{"kind": "signal|counter_evidence", "id", "name", "short", "region", "weight": float|null, "strength": float|null, "reliability": "A|B|C", "source": {"name","date","url"}, "against": ["SIG-…"], "data_label"}]`: direction<0 signals (by weight) + counter-evidence cards (by R×strength), weight-ordered.

## C6 — import result (task B, pipeline)
The `/api/run` result's scenario delta rows use current archetype ids and names (no "A/B/C/D"). Add `per_scenario` explanation text {en,fi} per row: which signal moved it and why.

## C7 — data (task C)
- `data/replay.json`: re-key every scenario-keyed field to current archetype ids; names from `scenario_archetypes.json`.
- `scenario_archetypes.json`: priors normalised to sum 1.0 (proportional, so the ranking is unchanged); `prior_note` says so.
- `data/worlds/1/signals.json` (+ `evidence.json` if needed): 4–5 new **negative-direction** cards with real, checked public sources (URL, date, excerpt quoted from the page), full card schema like SIG-001, `data_label: SOURCE`, ids continuing the sequence. If a source can't be verified, don't add it.

## Env
Unchanged: `ANTHROPIC_API_KEY` (optional), `AGENT_MODE`, `DEMO_TODAY`, `PORT`, `IRMA_BACKGROUND`.
