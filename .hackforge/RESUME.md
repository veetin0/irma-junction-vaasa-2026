# HackForge resume pack (auto-generated — read this instead of the whole history)

_Updated 2026-11-06T08:58:59+00:00_

## Goal and decision

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
4. **Horizon (T4):** a lead-time kernel T(h) gives e

## State

# State
- Phase: build M4–M6 (directive 11) in progress. M4.1 merged on main (c869321). Rate limit hit 2026-11-05 ~12:50, resets 13:50; the 4 data/engine builders (M4.2a oil and gas cards, M4.2b oil and gas scenarios, M4.3a chip-cycle data, M4.3b historical engine) wrote nothing and must be relaunched, then M4.4 wiring, M5, M6
M4 done and merged (gate green, 216 tests, MILESTONE 4). Next: M5 (M5.1 UI, M5.2 map, M5.3 reco wording), then M6.
- Profile: standard (auto: 10 h, team of 1, existing entry being improved) · Models: research sonnet / architect opus / judge opus / build sonnet / craft sonnet / verify sonnet
- Deadline: none set · Time budget 10 h
- Current milestone / wave: —
- Done: init, inventory, directives, brief, RULES.md, baseline judge 7.2, weighting research, OPTIONS, DECISION (pending)
- Next: user review; optional items in LOOP.md
- Best metric vs baseline: tests 33/33 · Latest mock score: 8.1 (7.2 before build)
- Escalations / de-escalations: kickoff scaled down. There is an existing entry and concrete directives, so the improvement options are designed inline instead of by 3 architect agents.; builder A on opus (hardest math)
- Risks & open questions: recommendat

## Team directives

# Team directives
Directives override HackForge defaults, never an official rule.

| # | Directive | Source |
|---|---|---|
| 1 | Write a better formula for weight calculation; maybe several formulas combined into a single result | prompts/00-team.md |
| 2 | Add a recommendation section that shows ABB what they should do, based on the program | prompts/00-team.md |
| 3 | Show the latest signal changes in the signal list | prompts/00-team.md |
| 4 | Connect the signals to the time horizon | prompts/00-team.md |
| 5 | Add a negative-signals list on the Signals page | prompts/00-team.md |
| 6 | Make the UI a little clearer while still showing all the relevant info | prompts/00-team.md |
| 7 | Split the Current Situation overview 70/30, with the recommended move on the main page | prompts/00-team.md |
| 8 | Modalities: suggest (propose at the decision checkpoint) | hackforge.yaml |
| 9 | Standing project constraints (from memory of the original build): no invented numbers (SOURCE / DEMODAT

## Loop

not running

## Last iterations (LOOP.md)

- clear world-1 notifications on a world switch
- label "weight at 1 y" vs headline weight in "Signals and sources used"
- the blank area under the Overview left column
- shorter assistant move answer
- grade the illustrative SIG-001 import below A (it would change the demo numbers and docs)

## Latest verdict

no verify.json yet



## Recent gate results

—

## Advisor

no consultations

## Integrity

not locked

## Rules

Hard rules: .hackforge/RULES.md. Contracts: .hackforge/contracts/. Never weaken gate.sh, tests, configs or thresholds.
