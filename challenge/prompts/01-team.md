# Team prompt 01: overview layout, signal map, oil and gas, historical comparison

Continue after milestone 3 as M4 to M6. Work in this folder (Junction-Vaasa-v2). Do not push and do not add or change git remotes.
The reference screenshot for the signal map is `challenge/assets/signal-map-reference.png` (Finnish UI, copy the structure, not the wording).

## Standing rules (unchanged, never weaken the existing gate checks, only add new ones)
- No invented numbers. Every number is SOURCE (named, dated, with URL), DEMODATA or ASSUMPTION.
- The LLM reads and classifies. Code computes every number.
- Recommendations stay conditional and qualitative: no quantities, order points or timing. Keep the guardrail in `llm.py`. The reference's "AI recommendation" box shows the layout only. Do not copy its wording (price clauses, hedging copper), reword it as a conditional analysis step.
- Counter-evidence on every signal. Structural and cyclical stay separate. The human decides.
- Vercel mode must keep working (VERCEL=1, read-only code, no API key, demo mode). Run `.hackforge/gate.sh` and a Vercel-mode check before finishing.

## My readings of the team's notes: list them at the decision checkpoint and wait for my answer before building
1. Overview order, top to bottom: major-signal banner, Current situation (short market review, at most 3 lines), sub-menu (segment, region, horizon), chart and Irma assistant side by side, Recommended move, then the full Market summary. Chart and assistant are both visible without scrolling at 1440x900 when the page opens.
2. "World situation 2: old data compared to the weight factors" means replacing the constructed downturn with a Historical data set (the 2021 to 2023 chip cycle) plus a panel that shows how the weight formula and scenario shares behave on that past cycle.
3. "Second new segment, oil and gas" means the segment filter becomes real with exactly two segments that have data: Data centres and Oil and gas. Remove the preview-only entries from the menu and list them in the docs as later work. Propose what "All segments" does (suggested: signals and map combined, scenario chart and recommendation ask for one segment).
4. "Several formulas and their average" already exists in `engine/weights.py` (the ensemble). Verify it, do not duplicate it. Show each formula's value and the average (the value used) on the signal page and in the map detail panel, and use the average as the map's weight axis.

## Changes
**A. Overview layout** as in reading 1. Check: headless screenshot at 1440x900 and 1280x720 shows chart and assistant inside the viewport on load.

**B. Recommended move, clearer language.** Short sentences, one action per line, plain words, no internal terms ("no_regret", "hedge", "kernel"). Rewrite the templates in `recommendations.json` in English and Finnish.

**C. Finnish and English text: simpler and more official.** Apply to all UI strings, scenario names and narratives, recommendation templates and notes. Finnish: virallinen yleiskieli, no slang, one term per concept (painoarvo, vaikutus, aikajänne, vastatodisteet). English: plain and formal. Add a gate check that the two I18N dictionaries have the same keys.

**D. Clean and minimalistic.** One accent colour (ABB red), neutral greys, fewer boxes and borders, more white space, secondary detail behind disclosures. Remove no information, only make it reachable in fewer steps.

**E. Signal market map on the Signals page** (reference screenshot).
- Filter row: Segment, Region, Signal type (source classes), Time horizon (1, 2, 3 years, default 3).
- SVG scatter. x = impact, -100 to +100, negative on the left. y = weight, 0 to 100 (weight x 100), small to large. Quadrants: Critical risks (high weight, negative), Strategic opportunities (high weight, positive), Risks to monitor (low weight, negative), Small opportunities (low weight, positive). Finnish labels: Kriittiset riskit, Strategiset mahdollisuudet, Seurattavat riskit, Pienet mahdollisuudet. Red dots negative, green dots positive, halo on the selected dot. The weight midline is the strong-signal threshold from Settings.
- Changing the horizon recomputes every signal's weight in the engine (the horizon weights that already exist), the dots move, and a note says so, as in the reference.
- Impact is a new code-computed field per signal, -100 to +100. Its sign is favourable or unfavourable for ABB relay demand and delivery in the selected segment. Its size comes from materiality and theme load. Document formula and label (ASSUMPTION) next to the weight assumptions. The LLM never sets it.
- Detail panel on click or keyboard: category, region, class, title, weight and impact badges, source (name, date, link), counter-evidence, a conditional "AI recommendation" box (from templates, guardrail applies), and buttons Approve / Edit / Reject (Hyväksy / Muokkaa / Hylkää). They map to the existing confirm / comment / dispute annotations, logged with name and reason, and the weight updates.
- Accessibility: markers are focusable with an aria-label (title, weight, impact), colour is not the only cue, and a table view shows the same data.
- Keep the existing strong, weak, changes and negative lists below the map, collapsed.

**F. Oil and gas segment.**
- 8 to 12 signal cards from real public sources (named, dated, URL, publisher grade), each with counter-evidence, region, update frequency and the six theme loadings. Use web search. If no source exists for a value, mark it DEMODATA on the card and in the UI.
- Its own pool of scenario archetypes with their own narratives, and its own recommendation templates. Do not reuse data-centre text.
- The segment filter selects signals, scenarios, chart and recommendation.

**G. Historical data (replaces world 2).**
- Sourced 2021 to 2023 points. Start with those in `docs/SOLUTION.md` section 1.3 (Broadcom lead times, SIA sales, ECIA, DRAM) and add more with sources.
- As-of snapshots (for example quarterly). Freshness and weights are computed as of each date and use only what was published by then (no hindsight).
- Comparison panel: weights and leading scenario per as-of date next to today's, and what happened next, with source. Label it "illustrative comparison, not validation and not a forecast".
- Button text "Historical data" / "Vanha data". Update world notes and tests.

**H. Docs and tests.** Update `docs/SOLUTION.md`, README, DEMO.md and `docs/how-irma-weighs-evidence.html` to match. Add tests for impact range and sign, horizon re-weighting, the oil and gas data labels and the historical as-of rule. Extend `gate.sh` with contract checks for all of it and set MILESTONE to 6.

## Process
Plan M4 (data and engine), M5 (frontend) and M6 (language, docs, gate) with runnable acceptance checks. Commit per milestone. Finish with screenshots of the overview and the map at 1440x900 in Finnish and English, the gate output and the Vercel-mode result. Do not push.
