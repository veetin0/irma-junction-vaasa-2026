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

---
# Contracts M4–M6 (from challenge/prompts/01-team.md, readings 1–4 approved by the user, directive 11)

Standing rules unchanged: no invented numbers (SOURCE / DEMODATA / ASSUMPTION), LLM never sets a number, recommendations conditional and qualitative, guardrail in `llm.py` kept, counter-evidence on every signal, Vercel mode works, never weaken gate checks, do not push or change remotes.

## C8 — impact (M4.1) `engine/impact.py`
`compute_impact(signal, weight_entry) -> {"impact": int in [-100, 100], "label": "ASSUMPTION", "parts": {"sign": ±1, "materiality": float, "theme_load": float}}`.
- sign: favourable (+) or unfavourable (−) for ABB relay demand and delivery in the signal's segment. Derive it from `direction` and `measures` and document the rule (for example a supply-tight signal is unfavourable for delivery, a demand-up signal is favourable). Pure code, the LLM never sets it.
- size = round(100 × materiality × theme_load). materiality = `weights[id]["components"]["materiality"]`; theme_load = min(1, Σ|axes| / A_ref) over the six theme loadings (`axes`), A_ref ASSUMPTION (start at 1.5).
- Every `state.signals[i]` gets `impact` (the dict above); `state.meta.impact = {"formula": str, "a_ref": float, "label": "ASSUMPTION", "sign_rule": {en,fi}}`. Document the formula next to the weight assumptions in `engine/weights.py` ASSUMPTIONS list or `/api/method`.

## C9 — segments (M4.1) `main.py`
- `Store.segment in {"datacenter","oilgas","all"}`, default `"datacenter"`. `POST /api/segment {"segment": ...}` → `{"segment", "state"}`; unknown → 400. `GET /api/state` includes `meta.segment`, `meta.segments = [{"id","label":{en,fi},"has_data":bool}]` (exactly datacenter and oilgas; preview-only entries are not in the API), and `meta.scenario_segment_required: bool` (true only for `all`).
- Signals: world 1 `signals.json` signals are `market: "datacenter"` (default when the field is missing). Oil and gas signals live in `data/segments/oilgas/signals.json` (+ `evidence.json`, `bullwhip.json` optional), each with `"market": "oilgas"`. segment `datacenter` → datacenter signals only; `oilgas` → oilgas only; `all` → union (state.signals carries `market`).
- Scenarios and recommendation use the segment's own pool: `data/scenario_archetypes.json` (datacenter, unchanged) and `data/segments/oilgas/scenario_archetypes.json`; templates `data/recommendations.json` and `data/segments/oilgas/recommendations.json`. For `all`, scenarios/recommendation are computed for datacenter as a fallback and `meta.scenario_segment_required` is true (the UI asks for one segment). Missing oilgas files → segment has_data false, the endpoint rejects it with 400 (until M4.2 merges).
- Scout/additions stay datacenter-only (`_load_additions` unchanged). Segment resets to default on `POST /api/reset`.
- Horizons: `state.signals[i].computed.horizon` already holds w_h for 12/24/36; the map uses it (no new compute).
- The ensemble in `engine/weights.py` is verified, not duplicated: `computed.band.methods` holds each formula's value and `computed.weight` the value used. Add a test that asserts this relation (weight equals the documented combination and the map axis uses `weight`).

## C10 — oil and gas data (M4.2) `data/segments/oilgas/`
- `signals.json`: 8 to 12 cards, same schema as `data/worlds/1/signals.json` cards (id `OG-001`…, `market: "oilgas"`, `segment: "oilgas"`, `region`, `source{name,url,date}`, `reliability` A/B/C, `update_frequency`, `axes` with the six theme loadings `demand, supply, policy, price, nordic, bullwhip`, `classification` structural/cyclical, `counter_evidence` ids, `excerpt` quoted from the page, `short_fi`, `data_label`). Real public sources found with web search; open the page and quote the excerpt. A value without a source is `DEMODATA` on the card (`data_label`, and `history_label`). If a source cannot be verified, do not add the card.
- `evidence.json`: counter-evidence cards (ids `OG-CE-001`…) so every signal has at least one, with source.
- `scenario_archetypes.json`: its own pool (at least 6 archetypes, priors sum to exactly 1.0, `prior_note`, `profile` over the same six axes, `narrative` en/fi, `signposts` referencing `OG-…` ids, `path`). No data-centre text reused.
- `recommendations.json`: same structure as `data/recommendations.json`, keyed by the oilgas archetype ids, own themes/moves (`select` rules match oilgas signals). Passes the guardrail (no quantities, no order timing).
- `bullwhip.json` optional (copy structure of world 1; labelled DEMODATA).
- Tests: `tests/test_oilgas.py` (ids unique, schema keys, six axes, labels, every signal has counter-evidence, priors sum 1, templates cover every archetype, no data-centre phrases).

## C11 — historical data (M4.3, M4.4) replaces world 2
- `data/historical/chipcycle.json`: sourced 2021–2023 points (start with `docs/SOLUTION.md` section 1.3: Broadcom lead times, SIA sales, ECIA, DRAM; add more with URL, date, excerpt). Each point is a full signal card (same schema) with `observed_at` = publication date. Values without a source are DEMODATA. Also `snapshots: ["2021-07-01", "2022-01-01", "2022-07-01", "2023-01-01", "2023-07-01"]` (quarterly or half-yearly, builder chooses and justifies) and `outcomes: [{"after": date, "text":{en,fi}, "source":{name,url,date}}]` (what happened next, with source), and `counter_evidence` cards as `evidence`.
- `engine/historical.py`: `signals_as_of(cards, d)` keeps only cards with `observed_at <= d` and truncates `history` to `<= d` (no hindsight); `snapshot(cards, evidence, archetypes, d)` computes weights with `compute_weights(..., today=d)` and the scenario ranking; `compare(cards, evidence, archetypes, snapshots, current_state)` returns `{"label":{en,fi}: "illustrative comparison, not validation and not a forecast", "rows":[{"as_of","n_signals","top_weights":[{"id","short","weight"}],"leader":{id,name,probability},"probabilities":{...},"outcome":{text,source}}], "today":{"as_of","top_weights","leader"}}`.
- World 2 = "Historical data" / "Vanha data" (`WORLDS[2]` label and note updated). `main.today()` returns the world's reference date while world 2 is active (the latest snapshot date, ASSUMPTION) so the whole state is as-of that date; DEMO_TODAY applies to world 1 only. `GET /api/historical` → the `compare` result, always available (computed from the historical dataset and the current world-1 datacenter state). The segment in world 2 is datacenter only (oilgas → 400 in world 2).
- Delete the constructed world-2 stress data (`data/worlds/2/*`) only after the new dataset loads through the same `signals.json/evidence.json/bullwhip.json` layout (keep that layout: the Store reads world 2 from `data/worlds/2/` so no loader changes; `chipcycle.json` is the master and `worlds/2/signals.json` is generated from it by `scripts` or committed beside it with a test that they agree).
- Tests: `tests/test_historical.py` (as-of rule: no card with observed_at after the snapshot is used, history truncated, weights at an early snapshot differ from the later one, every point has a source or DEMODATA label, outcomes carry a source, label text present).

## C12 — frontend (M5)
- Overview order top to bottom: major-signal banner, Current situation (short market review, ≤ 3 lines), sub-menu (segment, region, horizon), chart and Irma assistant side by side, Recommended move, full Market summary. At 1440×900 and 1280×720 the chart and the assistant are visible without scrolling on load.
- Segment filter shows exactly Data centres and Oil and gas (and All segments); the preview-only entries are removed. It calls `POST /api/segment`. In `all` the chart and the recommendation are replaced by a short card asking the user to pick one segment (two buttons).
- `frontend/map.js` exposes `window.renderSignalMap(root, ctx)` with `ctx = {state, lang, t, api, reload}`; `index.html` loads it and `frontend/map.css` (M5.1 adds the tags, M5.2 creates the files; before M5.2 merges `renderSignalMap` may be missing, so M5.1 guards with `window.renderSignalMap?.`).
- Signals page map: filter row (Segment, Region, Signal type = `source_class`, Time horizon 1/2/3 years default 3 → `computed.horizon["12"|"24"|"36"]`), SVG scatter x = `impact.impact` (−100…+100), y = weight×100 (0…100). Quadrants: Critical risks (high weight, negative), Strategic opportunities (high weight, positive), Risks to monitor (low weight, negative), Small opportunities (low weight, positive); FI: Kriittiset riskit, Strategiset mahdollisuudet, Seurattavat riskit, Pienet mahdollisuudet. Midline = `settings.strong_signal_weight`×100. Red dot negative, green positive, halo on selected, shape or label cue besides colour, focusable markers with aria-label (title, weight, impact), table view of the same data, note that the horizon recomputes weights.
- Detail panel: category, region, class, title, weight and impact badges, source (name, date, link), counter-evidence, "AI recommendation" box worded as a conditional analysis step from templates (guardrail applies; no price clauses), buttons Approve/Edit/Reject (Hyväksy/Muokkaa/Hylkää) → existing `confirm`/`comment`/`dispute` annotations with name and reason, then `reload()`. Show each formula's value (`computed.band.methods`) and the average used (`computed.weight`) in the panel and on the signal page.
- Existing strong/weak/changes/negative lists stay below the map, collapsed.
- Historical data panel (button "Historical data" / "Vanha data"): weights and leading scenario per as-of date next to today's, what happened next with source, label "illustrative comparison, not validation and not a forecast", from `GET /api/historical`.
- Design: one accent colour (ABB red), neutral greys, fewer boxes and borders, more white space, secondary detail behind disclosures. No information removed.

## C13 — recommendation language (M5.3)
Rewrite the texts in `data/recommendations.json` and `data/segments/oilgas/recommendations.json` (the oil and gas file arrives from M4.2; M5.3 starts after M4 merged) in plain EN and FI: short sentences, one action per line, plain words, no internal terms ("no_regret", "hedge", "kernel", "no-regret"). Keys and structure unchanged, guardrail and existing recommend tests green.

## C14 — language, docs, gate (M6)
- Finnish: virallinen yleiskieli, no slang, one term per concept (painoarvo, vaikutus, aikajänne, vastatodisteet); English plain and formal. Applies to I18N strings, scenario names and narratives, templates and notes.
- Gate: I18N key parity check (EN and FI dictionaries in `app.js` have identical keys; run with node), new contract checks for C8–C13, MILESTONE=6. Docs updated: `docs/SOLUTION.md`, README, DEMO.md, `docs/how-irma-weighs-evidence.html`. Tests for impact range/sign, horizon re-weighting, oil-and-gas labels, historical as-of rule. Vercel-mode check (`VERCEL=1`, no API key) on all endpoints incl. `/api/segment` and `/api/historical`.
