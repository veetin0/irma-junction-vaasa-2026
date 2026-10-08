# Rules & judging

Challenge: ABB Distribution Solutions, "From weak signals to proactive decisions" (Junction Vaasa 2026).
Sources read in full: `challenge/brief/ABB challenge Vaasa Hackathon 2026.pdf` (3 pages, cited as "Brief p.N §"), `challenge/data/1_Ecosystem...png`, `2_Challenge...png`, `3_Vision...png` (ABB slides, cited as Slide 1/2/3), `challenge/prompts/00-team.md` (team directives), `challenge/hackforge.yaml`, `challenge/README.md`. Extracted 2026-10-07.

Important: the brief contains NO explicit disqualification clauses, deadline, submission channel, team-size, licence or IP terms. The "hard rules" below are therefore the brief's mandatory-worded requirements ("needs to show", "should cover", "minimum requirement"). Anything the organiser has not written is listed under Open questions, not invented as a rule.

## Hard rules (break one = disqualified or not a valid entry)
| ID | Rule | Source (quote + location) | How we comply |
|----|------|---------------------------|---------------|
| R1 | Pick a market or phenomenon related to electrification | "Choose a market or phenomenon related to electrification." Brief p.1 §2 | Data-centre electrification demand and the component supply behind ABB protection relays; Nordics + Europe, US comparison (README.md, SOLUTION.md header) |
| R2 | Use public data and AI tools | "Use public data and AI tools to explore it." Brief p.1 §2; "grounded in business understanding, market knowledge, and public data" Brief p.3 outcome sentence | Public sources labelled SOURCE; DEMODATA/ASSUMPTION labelled. AI = Claude via Anthropic SDK (replay on Vercel) |
| R3 | Find key drivers and uncertainties, weak signals and possible turning points, and how they affect ABB demand, manufacturing or supply chain | "Find the key drivers and uncertainties, identify weak signals and possible turning points, and think about how these could affect ABB's demand, manufacturing, or supply chain." Brief p.1 §2 | SOLUTION.md §1.1-1.4, §2 |
| R4 | Define a specific decision problem relevant for ABB, then design an AI-based digital solution that detects changes earlier, explores alternative scenarios and supports human decision-making | "define a specific decision problem that is relevant for ABB. Then design an AI-based digital solution that helps detect changes earlier, explore alternative scenarios, and support human decision-making." Brief p.1 §2 | SOLUTION.md §3 (component procurement / S&OP planner), §4 |
| R5a | Show: public data sources and how to access them | "Which public data sources you can use and how to access them" Brief p.1-2 §2 "Your team needs to show" | SOLUTION.md §2.1 access column and access-methods paragraph |
| R5b | Show: reliability, up-to-dateness and forward-looking nature of signals | "How reliable, up-to-date, and forward-looking different signals are" Brief p.2 | Reliability A/B/C, freshness, lead months per card |
| R5c | Show: separate structural growth from short-term fluctuations and disruptions | "How to separate long-term structural growth from short-term fluctuations and temporary disruptions" Brief p.2 | SOLUTION.md §1.2, classification field |
| R5d | Show: balanced handling of growth-supporting and reversal-warning evidence | "How to handle both growth-supporting and reversal-warning evidence in a balanced way" Brief p.2 | Counter-evidence agent, noisy-OR penalty, 0.6 cap |
| R5e | Show: alternative market scenarios built from the signals | "What alternative market scenarios can be built from the signals" Brief p.2 | Four scenarios from nine archetypes, SOLUTION.md §4.5 |
| R5f | Show: manufacturing, procurement, capacity or supply chain decisions the findings could support | "What manufacturing, procurement, capacity, or supply chain decisions the findings could support" Brief p.2 | SOLUTION.md §1.5, §3 (analysis only; see GAP-1) |
| R5g | Show: why the AI solution fits the problem and how it works in practice | "Why the AI solution you propose fits the problem and how it would work in practice" Brief p.2 | SOLUTION.md §4, §5 |
| R6 | Final deliverable combines business understanding, data analysis, AI solution logic and a modern digital presentation, covering the six areas | "Your final deliverable should combine business understanding, data analysis, AI solution logic, and a modern digital presentation. It should cover these six areas:" Brief p.2 §3 | See D1-D6 |
| R7 | Prototype must implement the minimum chain | "Minimum requirement for your prototype: New data -> signal detection -> source and counter-evidence review -> scenario -> decision recommendation for ABB -> next action." Brief p.2 | Chain exists up to scenario; "decision recommendation for ABB" is conditional text only (GAP-1) |
| R8 | Do not aim at exact sales-figure prediction | "The goal is not to predict exact sales figures." Brief p.1 §1 | Scenario paths labelled "not a forecast"; no sales numbers |
| R9 | Human judgement must remain part of the solution | "support human decision-making" Brief p.1 §2; "the role of human judgment" Brief p.2 area 4; Slide 2 step "7. Human decision"; Slide 3 "Human in the loop" | Annotations, confirm/dispute, planner decides |
| R10 | Outcome must be scenarios AND recommended actions | "turns them into scenarios and recommended actions that support proactive decision-making at ABB." Brief p.3 "Hackathon Outcome" | Scenarios yes; recommended actions NOT yet (GAP-1) |
| R11 | Deliver an end-to-end example showing value to the user | "One end-to-end example that shows how the solution works and what value it delivers to the user." Brief p.2 area 5 | SOLUTION.md §5.2 walkthrough, Import data page |

## Deliverables
| ID | Artefact | Format / limits | Due |
|----|----------|-----------------|-----|
| D1 | Business & Market Insight | "Key market drivers, growth and slowdown signals, regional differences, uncertainties, and the connection to ABB." Brief p.2 area 1. No length limit given | Not stated |
| D2 | Data & Signal Portfolio | "Data sources, leading and lagging indicators, data quality, how current the data is, lead time, and any usage restrictions." Brief p.2 area 2 | Not stated |
| D3 | Decision Problem | "Who is the user, what decision they need to make, what change they need to detect, how much lead time is needed, and what happens if the signal is misread." Brief p.2 area 3 | Not stated |
| D4 | AI Solution Concept | "System architecture, agent roles, step-by-step process, how evidence is handled, scenarios, and the role of human judgment." Brief p.2 area 4 | Not stated |
| D5 | Demonstrable Prototype | "One end-to-end example that shows how the solution works and what value it delivers to the user." Brief p.2 area 5; must include the R7 chain | Not stated |
| D6 | Sixth area | The brief says "six areas" but the table lists only five (rows 1-5). The sixth is missing from the PDF text (see Q1). Conservative reading: the "modern digital presentation" (pitch/presentation layer) is the sixth | Not stated |
| D7 | Presentation form (optional ideas) | "Here are some ideas for your presentation, you don't need to do all of these": interactive signal radar or market map; filters by region, segment, time horizon; signal strength, direction, uncertainty views; scenario comparison and signal-based change paths; dashboard + chat; automatically generated executive briefing or situation overview; clickable prototype, lightweight live demo or recorded use case video. Brief p.2 | Not stated |

Prototype minimum chain, step by step (all mandatory, R7): (1) New data, (2) signal detection, (3) source and counter-evidence review, (4) scenario, (5) decision recommendation for ABB, (6) next action.

## Judging criteria
Source: Brief p.3 §5 "Teams will be evaluated on the following criteria". Weights are stated, sum 100 %.

| ID | Criterion | Weight | What a top score looks like (inference, not stated by ABB) |
|----|-----------|--------|-----------------------------|
| J1 | Business value and connection to ABB decisions | 20 % | Named ABB decisions (Slide 2 "What we must decide", Slide 3 decision areas), tied to lead time and time horizon, ending in a recommended action, not only insight |
| J2 | Understanding of the market and the phenomenon | 20 % | Demand-side AND supply-side ecosystem (Slide 1), interdependence, structural vs cyclical, regional differences |
| J3 | Quality of data sources and signal chain | 15 % | Public sources with access, quality, freshness, lead time, restrictions; leading vs lagging; chain global trend -> market data -> weak signal -> scenario -> business impact -> decision (Brief p.1) |
| J4 | Quality of problem definition | 15 % | Specific user, decision, change to detect, required lead time, cost of misreading |
| J5 | Logic and clarity of the AI solution | 20 % | Agent roles (Slide 3: market intelligence, supply chain, signal detection, scenario builder, impact assessment, recommendation), evidence handling, explainability, human in the loop |
| J6 | Prototype functionality and modern presentation | 10 % | Works end to end through the R7 chain; clear, modern UI |

## Implicit expectations
- ABB's own framing is an 8-step loop: "1. Detect signals, 2. Validate & filter, 3. Analyse impact, 4. Build scenarios, 5. Evaluate trade-offs, 6. Recommend actions, 7. Human decision, 8. Monitor & learn" (Slide 2). Steps 5 and 6 (trade-offs, recommend actions) are the ones Irma currently lacks.
- Slide 3 shows a "Recommendation Agent: Proposes actions & priorities" and an "Impact Assessment Agent: Estimates business impact & trade-offs". A reviewer comparing against the slides will look for both.
- Decisions ABB lists as theirs (Slide 2): when to buy components, how much inventory to hold, which capacity to secure or invest in, how to price, which customers/orders to prioritise, which products/alternatives to develop. Slide 3 decision areas: demand & sales, procurement, manufacturing, inventory & working capital, customer & order allocation, product & engineering, investment & strategy.
- Three time horizons (Slide 2): short 0-12 months, medium 1-3 years, long 3+ years; Slide 3 "Time Horizon View: Short, Medium, Long". Signals and actions should be tied to a horizon.
- Optimisation trade-off (Slide 2): short-term financial performance, customer continuity, future growth capability, business resilience; "Every decision has a cost".
- Both ecosystems matter: demand side (generation, transmission, distribution, consumption; data centres, e-mobility, etc.) and supply side (raw materials, OSAT, components, EMS, assembly) (Slide 1). The product at the core is the ABB protection relay.
- Outcomes ABB wants (Slide 2/3): better timing, lower cost/less waste, higher availability, stronger customer retention, higher margins/cash flow, long-term value.
- Slide 3 capabilities: early warning, scenario & what-if, demand-supply balancing, risk & opportunity assessment, time horizon view, explainability & transparency, alerts & dashboards.
- Tone line on p.3: "Business-led, data-grounded and AI-enabled foresight for resilient decisions." Business-led comes first.
- "proactive" is in the title: output should say what to do before the order book shows it ("before it shows up in actual orders", Brief p.1 §1).

## Team directives (challenge/prompts/00-team.md; followed unless they break an official rule; none do)
| ID | Directive (verbatim) | Note |
|----|----------------------|------|
| T1 | "Write better formula for weight calculation, maybe add many formulas and use all of them as a single result" | Supports J5; current single product formula in `engine/weights.py` |
| T2 | "Add a recomendation section header that shows ABB what they should do based on the program" | Directly required by R7/R10; conflicts with the project's earlier no-recommendation stance |
| T3 | "Show the latest signal changes in the signal list" | |
| T4 | "Make the signals connected to the time horizon" | Matches Slide 2/3 time horizons |
| T5 | "Add negative signals list in the Signal page" | Supports R5d balance |
| T6 | "Make the UI a little clearer while also displaying all the relevant info (the same as now)" | J6 |
| T7 | "Split the Current Situation overview 70/30 with the recomended move on the main page" | Requires a recommended move to exist |

## Open questions for the organisers (with the conservative reading to use meanwhile)
| ID | Question | Conservative reading |
|----|----------|----------------------|
| Q1 | The brief says "six areas" but the table shows five (Business & Market Insight, Data & Signal Portfolio, Decision Problem, AI Solution Concept, Demonstrable Prototype). What is the sixth? | Treat a short "modern digital presentation / pitch" as area 6 and also cover all 7 "team needs to show" bullets |
| Q2 | Deadline and time zone, submission channel, file formats, presentation length? None in the brief or hackforge.yaml (`deadline: ""`) | Ask on site; keep a runnable demo, a recorded fallback and a written document ready |
| Q3 | Team size, eligibility, pre-existing code rules, open-source licence, repository visibility, IP terms? Not stated | Assume all code written during the event; keep the repo clean of third-party proprietary data; keep licences of data (IEA CC BY 4.0 etc.) attributed |
| Q4 | May AI APIs/paid models be used and demoed live? Brief only says "public data and AI tools" | Allowed. Keep replay mode as fallback so the demo never depends on network or a key |
| Q5 | Does "decision recommendation for ABB" allow conditional, directional recommendations without quantities or order timing? ABB mentors (per project memory) warned that a recommendation from open data alone is false authority | Yes: give conditional, scenario-linked, directional actions with triggers, confidence and an explicit "human decides" label. No quantities, no order points |
| Q6 | Is DEMODATA acceptable in the prototype when public data is licensed or missing? | Acceptable if labelled (current practice); never present DEMODATA as a source |
| Q7 | The brief says "Choose a market"; are data centres the right market or must the team cover the whole protection-relay portfolio? | Data centres are a valid "market or phenomenon"; show the link to Slide 1 ecosystem |

## Compliance audit snapshot (2026-10-07; README.md, docs/SOLUTION.md, app/)
Audit of the existing project against the list above. Status: pass / fail / partial / unknown.

| ID | Status | Evidence | Fix |
|----|--------|----------|-----|
| R1, R2, R3 | pass | README.md header; SOLUTION.md §1-2; 32 signal cards in `app/backend/data/worlds/1/signals.json` | None. Note count inconsistency: SOLUTION.md §2.1 says 32 cards, but §3.4, §4.4 and §6 say "17 cards", self-score says "16 public cards"; fix before judges read it |
| R4 | pass | SOLUTION.md §3 (procurement/S&OP planner), §4 | Make the decision problem end in a recommended action |
| R5a-R5e, R5g | pass | SOLUTION.md §2.1, §1.2, §4.2-4.5 | None |
| R5f | partial | SOLUTION.md §1.5: "The system does not answer these questions" | Add recommended directional actions per decision area |
| R6 | partial | SOLUTION.md has sections 1-5 plus pitch; claims "six challenge areas" | Resolve Q1; label the pitch/presentation as area 6 |
| R7 | fail | SOLUTION.md §5.2 re-reads "decision recommendation for ABB" as "conditional impact statement, not a purchase instruction" and "next action" as "analysis action"; UI label is "Next analysis step" (`app/frontend/app.js:48`); no recommendation agent; `app/backend/agents/pipeline.py:1` "no recommendation agent" | Add a recommendation step (see GAP-1) |
| R8 | pass | Paths labelled "not a forecast" (SOLUTION.md §4.5) | None |
| R9 | pass | Annotations (confirm 1.2 / dispute 0.5), SOLUTION.md §4.6 | Keep, and make "human decides" label sit next to the recommendation |
| R10 | fail | Outcome sentence needs "recommended actions"; none produced. `app/backend/agents/llm.py:21-28` strips "ABB should order/buy..." and "we recommend" from all generated text; README principle 2 "No agent recommends" | See GAP-1 |
| R11 | pass | SOLUTION.md §5.2, Import data page | Ends at "next analysis step"; extend to recommended move |
| D1-D5 | pass | SOLUTION.md §1-§5 | D5 chain incomplete (R7) |
| D6 | unknown | Sixth area undefined in brief (Q1) | Confirm with ABB mentor |
| J1 | at risk | Self-score 4/5, but the document argues against recommending (SOLUTION.md §0, §3.6, §6.1 Q3, pitch "why no recommendations") while Brief p.3 requires "recommended actions" | Add recommendations; rewrite §3.6 and pitch lines |
| J5 | at risk | Slide 3 shows a Recommendation Agent and Slide 2 steps 5-6 (trade-offs, recommend); Irma has eight agents, none recommending (`app/frontend/app.js:42` "Agents (none of them recommends)") | Add a Recommendation agent and trade-off view |
| J6 | partial | Without key, LLM steps replayed; Vercel never uses a key (README); region/segment filters are label-only preview (SOLUTION.md §5.3) | State in the demo what is replayed; consider making filters functional or hiding them |
| T1 | fail | Single product formula `w = R x F x S x (1-C) x H` | Add an ensemble of formulas |
| T2, T7 | fail | No recommendation section; overview has no recommended-move panel | Build (GAP-1) |
| T3-T6 | unknown | Not confirmed by this audit (latest-change markers, horizon tags per signal, negative-signal list). Signals page has strong/weak lists, not positive/negative; horizon chips (6/12/36 months) change only the projection chart | Verify in UI after build |

### GAP-1: recommendation vs the current no-recommendation design
What the brief requires, verbatim: the prototype chain must contain "decision recommendation for ABB -> next action" (Brief p.2); the outcome is "scenarios and recommended actions that support proactive decision-making at ABB" (Brief p.3); ABB's slide chain includes "6. Recommend actions" then "7. Human decision" (Slide 2) and a "Recommendation Agent: Proposes actions & priorities" (Slide 3). Recommending and keeping a human decision are both required, not alternatives. The brief does not require purchase quantities, order points or timing of orders, and it states "The goal is not to predict exact sales figures."

The current design replaces the recommendation with a conditional impact statement and an "analysis action" (watch list, re-evaluation date, reviewers). That is a deliberate reinterpretation (SOLUTION.md §5.2) and likely reads as a missing step to a judge, while the guardrail in `agents/llm.py` would also delete any recommendation sentence a model or template wrote (pattern `you|abb should (order|buy|purchase|procure|stock)` and `we recommend`).

How a conditional, non-quantity recommendation can satisfy the brief:
- Output a "Recommended move" per leading scenario, built from the decision areas in Slide 3, in directional and reversible terms. Example forms: "If scenario A holds, prepare to extend the next component commitment window and start qualifying a second memory source", "If signals X and Y cross threshold Z by date, bring the S&OP review forward", "Hold the commitment decision until the Fingrid priority-rule outcome is known".
- Attach: the scenario and probability it depends on, the trigger signals and thresholds that would change it, no-regret moves (valid in most scenarios) vs contingent moves, the cost of being wrong in each direction (Slide 2 trade-offs), time horizon (0-12 months / 1-3 years / 3+ years), confidence, and an explicit "Human decides; Irma lacks contract, allocation and cash data" label.
- Never include quantities, order points, prices or order dates; keep those three pattern families in the guardrail.
- Implementation: generate the move in code from scenario state and archetype data (deterministic, testable), and run it through a separate path or an allow-list so the "should" phrasing is not stripped; keep the quantity/timing patterns. Add a Recommendation agent to the agent table and trace, so the chain reads detect -> review -> scenario -> recommend -> next action.
- Then update README principle 2, SOLUTION.md §0, §3.6, §5.2, §6 pitch and Q3 answer, the "none of them recommends" UI string, the assistant disclaimer (`app/backend/main.py:895`), and the tests in `app/tests/test_engine.py` (guardrail tests at lines 81-90).

## Compliance re-audit (2026-10-08, after M1–M3 and verifier run)
Supersedes the 2026-10-07 snapshot above for these items:
- R7 and R10 are now **compliant**. The Import chain ends in a code-generated "Recommended move" (4 moves, no-regret or contingent, trigger signal ids, cost if wrong, hedge) and a "Next action" with owner and due date. The move is also on the Overview (30% column) and in the run trace as "Recommendation agent (code)". There are no quantities or order timing; the guardrail is kept.
- The card counts in the docs now match the data: 37 in world 1 (36 + 1 scout addition), 24 in world 2.
- T1–T7 are compliant. The segment filter is still a labelled preview.
- Verifier (clean clone): R1–R11 compliant. R6/D6 partial by design (the sixth area is the pitch). D1–D5 present.
