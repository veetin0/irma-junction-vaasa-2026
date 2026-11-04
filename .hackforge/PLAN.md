# Plan

Time budget: 10 h · Deadline: none · Team: 1 · Profile: standard · Stack: FastAPI + vanilla JS + JSON data (unchanged, existing entry)

## Milestones (vertical slices)
| M | Goal | Covers | Acceptance checks (runnable) | Time-box | Status |
|---|------|--------|------------------------------|----------|--------|
| M1 | Backend: ensemble weights + horizon, recommendation + next action, signal changes, negative list, data fixes | R7 R10 J1 J3 J5, T1 T2 T4 T5 T3(data) | `.hackforge/gate.sh` (pytest + contract checks) | 3 h | ✅ |
| M2 | Frontend: 70/30 overview with recommended move, horizon chips re-ranking, changes column, negative list, weight waterfall, real region filter, clearer UI | J6 J1, T2–T7 | gate.sh + `node --check` + served page check | 3 h | ✅ |
| M3 | Docs and pitch sync: SOLUTION.md, README, explainer html match the app; DEMO.md | J2 J4 J5 D1–D5 | gate.sh doc-consistency checks | 2 h | ✅ |
| M4 | Data and engine: impact field, segments (Data centres, Oil and gas), oil-and-gas data, Historical data with as-of snapshots | R7 R10 J1 J3 J5, 01-team E/F/G | gate.sh (M4 contract checks) | 3 h | ⏳ |
| M5 | Frontend: overview order, Recommended move wording, signal market map, segment filter, historical panel, clean minimal UI | J6 J1, 01-team A B D E | gate.sh + `node --check` + 1440x900 and 1280x720 screenshots | 3 h | ⏳ |
| M6 | Language (FI/EN simplification, I18N key parity), docs, tests, gate to MILESTONE 6, Vercel-mode check | J2 J4 J5 D1–D5, 01-team C H | gate.sh + Vercel-mode check | 2 h | ⏳ |
| — | Reserve: verify, screenshots FI/EN, mock judge | | | 1 h | |

## Tasks per milestone
| M | Role | Task | Contract | Agent / model | Branch | Status |
|---|---|---|---|---|---|---|
| M1 | backend | A: weights ensemble, horizon kernel, scenarios_by_horizon | C1, C2 | builder / opus (escalated: hardest math) | hf/m1a-weights | ✅ |
| M1 | backend | B: recommendation engine + templates, guardrail, signal changes, negative list | C3, C4, C5, C6 | builder / sonnet | hf/m1b-reco | ✅ |
| M1 | data-ml | C: re-key replay.json, normalise priors, 4–5 sourced negative cards (world 1) | C7 | builder / sonnet | hf/m1c-data | ✅ |
| M2 | frontend | D: all UI changes in app.js / styles.css / index.html | C1–C6 | builder / sonnet | hf/m2-ui | ✅ |
| M3 | pitch | E: docs sync + DEMO.md | all | builder / sonnet | hf/m3-docs | ✅ |
| M4 | backend | M4.1: impact field, segment plumbing in main.py (Store.segment, /api/segment), map data, meta.impact_formula | C8, C9 | builder / sonnet | hf/m4-engine | ⏳ |
| M4 | data-ml | M4.2: oil-and-gas signals, evidence, archetypes, recommendation templates (web search, real sources) | C10 | builder / sonnet | hf/m4-oilgas | ⏳ |
| M4 | data-ml | M4.3: historical dataset 2021–2023 + engine/historical.py (as-of, no hindsight) | C11 | builder / sonnet | hf/m4-history | ⏳ |
| M4 | backend | M4.4: wire world 2 = Historical data and /api/historical into main.py (after M4.1–M4.3 merge) | C11 | builder / sonnet | hf/m4-wire | ⏳ |
| M5 | frontend | M5.1: app.js/index.html/styles.css: overview order, segment filter, historical panel, minimal UI | C12 | builder / sonnet | hf/m5-ui | ⏳ |
| M5 | frontend | M5.2: frontend/map.js + map.css: signal market map, detail panel, table view | C12 | builder / sonnet | hf/m5-map | ⏳ |
| M5 | backend | M5.3: recommendation templates in plain EN/FI (recommendations.json, both segments) | C13 | builder / sonnet | hf/m5-reco | ⏳ |
| M6 | full-stack | M6.1: FI/EN text pass, I18N parity check, docs, tests, gate | C14 | builder / sonnet | hf/m6-docs | ⏳ |

## Non-code deliverables
| Asset | Raises | Spec | Tool | Status |
|---|---|---|---|---|
| (cut) refreshed demo video | J6 | — | HyperFrames | cut unless time left |

Polish & submission reserve: last 2 h
