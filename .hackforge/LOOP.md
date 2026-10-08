# Improvement loop
| # | change | gate | compliance | score | kept |
|---|---|---|---|---|---|
| 0 | baseline after M1–M3 | green | R7 R10 fixed | 7.8 | — |
| 1 | import chain wording, Recommendation trace step, replay text matching live state, assistant cites the move, horizon hedge hint, strong/weak at horizon, years, httpx in requirements, DEMO world-flip beat, RULES re-audit | green (83 tests) | PASS (verifier) | 8.1 | kept | 
| 2 | card provenance kept on update (earlier versions), DEMO data step on SIG-003, one watch list, import rows to 1 dp, hedge auto-opens at differing horizon, fuzzy lead-move match (world 2), month labels, assistant wording | green (84 tests) | PASS | 8.1 | kept |
| 3 | assistant routes "what do you recommend" to the move, hedge prefix, axis "Oct 2026" + round ticks, "signals to watch" wording, DEMO world-switch note | green (85 tests) | PASS | 8.1 | kept |

Stopped: plateau. Iterations 1–3 each scored 8.1 (start 7.8 after build; 7.2 before the build). The judges agree the remaining gap to 9.0 is mostly structural: DEMODATA series, no back-test of lead times against ABB order intake, uncalibrated probabilities, no quantified value case without SAP and cost data. Those cap J1 and J3 at about 8.5.
Remaining cheap items (not done):
- world-2 demand-quality reading vs its "Duplicate orders unwind" leader
- clear world-1 notifications on a world switch
- label "weight at 1 y" vs headline weight in "Signals and sources used"
- the blank area under the Overview left column
- shorter assistant move answer
- grade the illustrative SIG-001 import below A (it would change the demo numbers and docs)
