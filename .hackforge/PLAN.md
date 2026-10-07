# Plan

Time budget: 10 h · Deadline: none · Team: 1 · Profile: standard · Stack: FastAPI + vanilla JS + JSON data (unchanged, existing entry)

## Milestones (vertical slices)
| M | Goal | Covers | Acceptance checks (runnable) | Time-box | Status |
|---|------|--------|------------------------------|----------|--------|
| M1 | Backend: ensemble weights + horizon, recommendation + next action, signal changes, negative list, data fixes | R7 R10 J1 J3 J5, T1 T2 T4 T5 T3(data) | `.hackforge/gate.sh` (pytest + contract checks) | 3 h | ✅ |
| M2 | Frontend: 70/30 overview with recommended move, horizon chips re-ranking, changes column, negative list, weight waterfall, real region filter, clearer UI | J6 J1, T2–T7 | gate.sh + `node --check` + served page check | 3 h | ⬜ |
| M3 | Docs and pitch sync: SOLUTION.md, README, explainer html match the app; DEMO.md | J2 J4 J5 D1–D5 | gate.sh doc-consistency checks | 2 h | ⬜ |
| — | Reserve: verify, mock judge, loop | | | 2 h | |

## Tasks per milestone
| M | Role | Task | Contract | Agent / model | Branch | Status |
|---|---|---|---|---|---|---|
| M1 | backend | A: weights ensemble, horizon kernel, scenarios_by_horizon | C1, C2 | builder / opus (escalated: hardest math) | hf/m1a-weights | ✅ |
| M1 | backend | B: recommendation engine + templates, guardrail, signal changes, negative list | C3, C4, C5, C6 | builder / sonnet | hf/m1b-reco | ✅ |
| M1 | data-ml | C: re-key replay.json, normalise priors, 4–5 sourced negative cards (world 1) | C7 | builder / sonnet | hf/m1c-data | ✅ |
| M2 | frontend | D: all UI changes in app.js / styles.css / index.html | C1–C6 | builder / sonnet | hf/m2-ui | ⬜ |
| M3 | pitch | E: docs sync + DEMO.md | all | builder / sonnet | hf/m3-docs | ⬜ |

## Non-code deliverables
| Asset | Raises | Spec | Tool | Status |
|---|---|---|---|---|
| (cut) refreshed demo video | J6 | — | HyperFrames | cut unless time left |

Polish & submission reserve: last 2 h
