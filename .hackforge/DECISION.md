# Decision — Option B: directives + consistency fixes (approved 2026-10-07)

## Why
The recommendation step is the single largest gap (fails R7/R10 and caps J1 at 6). Directives T1–T7 add about +1.0. The consistency fixes add about +0.6 more for under 3 h, and they remove the things a judge would catch in the demo.

## What gets built
1. **Recommended move (T2, T7):** a code-generated, scenario-conditional move per decision area (manufacturing / procurement / capacity / supply reliability), from templates in `data/` (bilingual, labelled ASSUMPTION). Each move has:
   - a no-regret vs contingent tag
   - the trigger signals and threshold that would change it
   - the cost of being wrong
   - the horizon
   - a revisit date
   - "the planner decides"
   It never includes quantities, order points or dates. The guardrail stays for quantity and order language. Narrow allow-phrases are added and the guardrail is tested.
2. **Overview 70/30 (T7):** "Current situation" at 70% and "Recommended move + next action" at 30%.
3. **Weight ensemble (T1):** five components, Credibility (Dempster–Shafer belief with corroboration) × Currency × Materiality (mean of LLM strength and z-score where SOURCE history exists) × Human, clamped to ≤ 1 (fixes the 1.5 bug). The single-source weight stays identical to today's. The aggregator range (product / min / geo-mean / mean) is shown as a sensitivity band and a waterfall breakdown on the signal page.
4. **Horizon (T4):** a lead-time kernel T(h) gives each card w₁₂ / w₂₄ / w₃₆. Horizon chips (1 y / 2 y / 3 y) re-rank signals and scenarios. The kernel width is an ASSUMPTION and its sensitivity is shown.
5. **Signals page (T3, T5, T6):** a "changed since last run" column (Δweight, new, direction flip). A negative-signals list (negative-direction cards + counter-evidence + negative contributions). A clearer layout that keeps all the information.
6. **Consistency:**
   - Re-key replay.json to the archetype ids.
   - Sync SOLUTION.md and README.
   - Normalise the priors.
   - Add 4–5 sourced negative cards (Energinet connection pause, Amsterdam moratorium, forecast critique, copper).
   - Add per-scenario import deltas.
   - Make the region filter real.
7. Tests for every engine change; replay mode works without a key (Vercel).

## Cut list
Segment filter stays preview. No video (option C) unless time is left. No new data sources beyond the 4–5 cards.

## Stack
Unchanged: FastAPI + vanilla JS + JSON data.
