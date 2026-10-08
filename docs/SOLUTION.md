# Irma — from weak signals to scenarios for ABB Distribution Solutions

Segment: **data centres**. Region: **Nordics + Europe**, with the US as comparison. Horizon: **12–36 months**. Prototype: `app/` (Irma: a market-terminal style interface in ABB red and white on a deterministic engine with eight agents plus a code-only recommendation agent that also appears as a step in the run trace, scheduled updates, notifications, signal tracking and a cited assistant). This document covers the six challenge areas, scores itself, and lists what must be verified with ABB. A 3-minute demo script, a 30-second version and the likely judge questions are in `DEMO.md`.

**Labelling convention used throughout.** Every number is one of: **[SOURCE]** named public source with date (the signal cards carry the URL), **[DEMODATA]** illustrative value in the prototype, or **[ASSUMPTION: reason]** (Finnish brief: OLETUS). Statements from ABB Distribution Solutions are marked **[ABB]**. Unlabelled numbers do not appear. Figures that describe the running prototype are computed with `DEMO_TODAY=2026-10-03` in replay mode (no model key), which is also how the public Vercel deployment runs.

### The six areas at a glance

The brief lists five areas and says "six"; we treat the modern digital presentation (pitch and demo) as the sixth and cover every "your team needs to show" item.

| Area | Where | What is delivered | Honest gap |
|---|---|---|---|
| 1. Business and market insight | §1 | Seven-link chain from capex to relay order with lead times; structural vs cyclical drivers; the bullwhip mechanism; regional timing; the ABB decisions the picture informs | The lead-time links are assumptions until validated against ABB order data; US delay figures rest on C-grade sources |
| 2. Data and signal portfolio | §2 | 37 signal cards (35 SOURCE, 1 DEMODATA placeholder, 1 internal placeholder) with access, reliability, freshness, lead time and restrictions; 7 negative-direction cards; five bullwhip metrics | Three of five bullwhip metrics take DEMODATA inputs; BW-5 and SIG-017 need ABB's SAP data |
| 3. Decision problem | §3 | User, decision, change to detect, required lead time, both misreadings and their cost; ends in a recommended move for the planner | The persona is inferred, not interviewed |
| 4. AI solution concept | §4 | Eight agents plus a code-only recommendation step; an ensemble signal weight with a horizon fit; counter-evidence on every strong card; scenario update; the human's role | Relevance values and priors are analyst-set, so probabilities are traceable but not calibrated; the corroboration and z-score estimators are built and tested but no current card uses them |
| 5. Demonstrable prototype | §5 | The full chain (new data, detection, source and counter-evidence review, scenario update, recommended move, next action) in one click path; 83 tests | LLM steps are replayed without a key; the daily history before today is simulated |
| 6. Presentation | §6, `DEMO.md` | 7-minute pitch, 3-minute demo script, 30-second version, judge Q and A | The pitch has not been timed against ABB's slot, which the brief does not state |

## What this system is, and what it is not

**It is** an AI system that follows weak signals from open sources about data-centre end demand and about the component supply that limits ABB's protection-relay output, and keeps four alternative scenarios of how the market can develop. Every scenario is argued, traceable to sources, and shown with evidence for and against. From the leading scenario it composes a **recommended move**: three to four conditional, qualitative moves across procurement, manufacturing, capacity and supply reliability, each marked no-regret or contingent and carrying the signals that would trigger or change it, its cost if wrong and its horizon; a hedge for the runner-up scenario; a **next action** with an owner and a due date; and a revisit date.

**It is not** a purchasing system or a sales forecast. The recommended move contains no quantities, no order points and no order dates, and the system does not claim to know which scenario will happen. The move is written by code from labelled templates (ASSUMPTION), not by the language model.

**Why the move is qualitative and conditional.** The order book lags the market by 18 months or more (ABB's 18-month component window against a 10-week order view; the 18–30 month lag is the arithmetic of section 1.1). A purchasing decision at ABB depends on frame contracts, supplier allocation agreements, cash position, internal priorities between ABB units and customer promises. None of that is visible in open data. A quantity or an order date computed from the market half of the picture would be false authority in a decision owned by the person holding the other half. The system therefore says what to prepare, review, watch and discuss, under which conditions and with what it costs if wrong, delivers the market half earlier and more completely than the order book can, and leaves quantity and timing where the missing information sits. **The human is the interpreter and the decision-maker; the words "The planner decides" are on the recommendation itself.**

---

## 1. Business & market insight

### 1.1 The signal chain: from a data-centre decision to an ABB relay order

ABB's unit makes protection relays: a small computer in an enclosure with 3–4 million lines of code [ABB]. The growth bottleneck is electronics, specifically semiconductors and memory, which must be ordered about 18 months ahead [ABB]. Customer delivery time has stretched from about 2 weeks to 8–10 weeks [ABB]. The chain below shows what happens before an order reaches ABB, and how far ahead of that order each link is visible.

| Link | Observable event | Months before relay order reaches ABB DS | Evidence of the lag |
|---|---|---|---|
| 1 | Hyperscaler capex guidance raised (earnings call) | 24–30 | [ASSUMPTION: guidance precedes site-level construction spend by 1–3 quarters; the electrical fit-out follows construction start by 12–18 months] |
| 2 | Land purchase or grid connection inquiry filed (e.g. Microsoft 470 acres at Vaasa, June 2026 [SOURCE: Computer Weekly]) | 24–36 | [ASSUMPTION: inquiries precede signed agreements by 6–18 months; most never convert] |
| 3 | Transmission connection agreement signed (Fingrid: >3 GW signed by June 2026 [SOURCE: Fingrid H1 2026 report, 2026-07-23]) | 18–30 | [ASSUMPTION: agreement to energisation 2–4 years; relay specification 12–18 months before energisation] |
| 4 | Permit granted, construction starts | 12–18 | [ASSUMPTION: electrical rooms are built after civil works] |
| 5 | MV substation design frozen, switchgear tender issued | 6–12 | [ASSUMPTION: the relay type is fixed at tender; verify with ABB] |
| 6 | Switchgear factory (often another ABB unit) places relay order or frame call-off on ABB DS | 0 | Order book. ABB sees this with 8–10 weeks delivery time [ABB] |
| 7 | ABB DS must have ordered memory and MCUs | **−18 (i.e. 18 months before link 6)** | [ABB] |

The arithmetic of the table is the whole problem. ABB's component order (link 7) must be placed roughly at the time of links 1–3, when the only visible evidence is capex guidance, land and connection agreements. By the time the switchgear tender exists, the component window has closed. This is why ABB "did not see in early 2025 that demand would double in mid-2026" [ABB]: the order book is a lagging indicator by 18–30 months relative to the decision it should inform.

**ABB's question, "what affects electrification market growth?":** for this segment the answer in order of lead time is (1) AI capex decisions, (2) grid connection capacity and its allocation rules, (3) electricity price differentials between regions, (4) permitting regimes, and (5) the electrical supply chain itself (transformers, switchgear) whose lead times delay projects. Items 2–5 explain *where and when*, item 1 explains *whether*.

### 1.2 Structural drivers vs cyclical factors

| Driver | Type | How to recognise it in data | Current evidence |
|---|---|---|---|
| Data-centre electricity demand doubling 2024→2030 | Structural | Multi-year institutional projection with alternative cases; slope uncertain, sign not | IEA base case 415 → ~945 TWh [SOURCE: IEA Energy and AI, April 2025] |
| Long-dated energy contracts behind sites | Structural | Contract length ≥ 10 years; nuclear or hydro PPA | Google–Fortum 22-year Loviisa agreement within EUR 13 bn programme [SOURCE: announcement 2026-09-09] |
| Signed grid connection agreements | Structural (timing uncertain) | Financially committed; counted by TSO | Fingrid >3 GW signed [SOURCE: 2026-07-23] |
| EU grid investment need | Structural | Regulated utility capex | EUR 584 bn this decade, distribution EUR 375–425 bn [SOURCE: COM(2023) 757] |
| Nordic vs continental power price gap | Structural | Persists across years, driven by generation mix | FI 40.5 vs DE 89.3 EUR/MWh in 2025 [SOURCE: Nord Pool via Fortum] |
| Hyperscaler capex pace | Mixed | Revised quarterly; investor-sensitive | USD 720–745 bn guided for 2026, +78% [SOURCE: Axios 2026-02-11] |
| Memory contract prices and lead times | Cyclical | Second derivative turns before the level does | DRAM +93–98% (1Q26), +58–63% (2Q26), +13–18% (3Q26) [SOURCE: TrendForce] |
| Distributor sentiment and queue sizes | Cyclical | Record readings mark the hoarding phase | ECIA memory index 180 [SOURCE: Feb 2026]; Fingrid inquiries ~24 GW [SOURCE: Aug 2026] |
| Project delays from permitting and transformer shortages | Cyclical (timing) | Shifts dates, not totals | 30–50% of US 2026 projects delayed or cancelled [SOURCE, reliability C] |
| Copper price | Mixed | Level = structural demand; spikes and retraces = positioning | ATH USD 14,858/t on 2026-09-09, USD 14,347 on 2026-10-02 [SOURCE: LME via Benchmark / Metalcharts] |

Rule used by the system: a signal is structural when it is contract-backed, regulated or institutional and multi-year; cyclical when it measures prices, sentiment, lead times, queues or timing; mixed when a structural trend is delivered through a cyclical mechanism (capex, copper). The classification is on every card with its rationale, and the user can dispute it.

### 1.3 The bullwhip mechanism in this value chain

ABB expects a pumping motion: the market is high now, and the question is where the first braking signal appears and how hard it brakes [ABB]. Step by step in this chain:

1. **End demand rises** (data-centre connection agreements, capex). Real, structural.
2. **Switchgear factories bid tenders.** Several factories, including several ABB units, bid for the same substation. Each forecasts the relays it would need. The same end project appears in several forecasts. [ASSUMPTION: multiple bidding per tender; verify how ABB consolidates internal forecasts.]
3. **ABB DS sees frame orders and forecasts** that exceed end demand, and cannot deliver all of it (8–10 weeks). Allocation begins [ABB].
4. **ABB orders components 18 months ahead with a safety margin**, because allocation at suppliers rewards early and large orders. Rational for ABB, amplifying for the chain.
5. **Memory and MCU makers see demand from PCs, AI servers and industrial buyers** at once; prices and lead times rise (DRAM +93–98% QoQ in 1Q26, MCU lead times 52–55 weeks [SOURCE]).
6. **Longer lead times cause more advance ordering** by everyone. This is the positive feedback loop. Distributor sentiment hits records (ECIA 180 [SOURCE]).
7. **The turn.** Grid connection limits and transformer shortages delay energisation dates (US: 30–50% delayed [SOURCE, C]; Finland: priority rules under consultation [SOURCE]). Switchgear factories push out or cancel relay orders. ABB's 18-month component orders arrive anyway.
8. **The overhang.** Inventory accumulates at every tier, spot prices fall below contract, lead times collapse. Everyone who double-ordered sits on stock.

**2021–2023 as analogy, not forecast.** Semiconductor lead times rose from 12.2 weeks (Feb 2020) to 22.2 weeks (Apr 2021) at Broadcom [SOURCE: Wikipedia summary of industry data]; global sales reached USD 573.5 bn in 2022 and were already falling 4.4% month on month by December 2022; smartphones, PCs and memory corrected first and rebounded first [SOURCE: SIA data via Nomad Semi]. The relevant lesson for ABB is the **order of events**: distributor sentiment and spot premiums turned a quarter or two before shipments did, and memory moved first. The bullwhip metrics in section 2 are built to watch exactly that order.

**Where the 2026 cycle differs.** The demand driver is concentrated in a handful of hyperscalers with published capex plans, which makes the end-demand signal more observable than in 2021, and the supply constraint is memory makers' deliberate reallocation to AI servers rather than fab outages. Both differences argue for watching capex guidance and memory allocation statements directly rather than only distributor behaviour.

### 1.4 Regional differences: same megatrend, different timing

| Factor | US | FLAP-D core (Frankfurt, London, Amsterdam, Paris, Dublin) | Nordics (Finland focus) |
|---|---|---|---|
| Grid connection capacity | Binding; transformer lead times 3–5 years, switchgear sold out through 2028 [SOURCE, C] | Moratoria: Amsterdam until at least 2030 (Apr 2025); Dublin reopened with on-site generation conditions; Energinet paused new connections March 2026 with queue >60 GW [SOURCE: EUDCA/EnkiAI, DCD] | Fingrid: >3 GW signed, ~24 GW inquiries; constraint is southern connection capacity, 70% of generation in west and north [SOURCE: Fingrid] |
| Electricity price | Varies by state; not sourced here | Germany 89.3 EUR/MWh 2025 [SOURCE] | Finland 40.5 EUR/MWh 2025 [SOURCE] |
| Permitting | Local opposition now a structural deal-breaker [SOURCE, C] | Long and tightening (EU energy efficiency reporting, PUE rules) | Comparatively fast, but new connection-priority rules under consultation (Aug 2026) could re-sequence data centres [SOURCE] |
| Tariffs and trade | Tariff regimes change the landed cost of imported switchgear and favour local assembly [ASSUMPTION: no sourced figure in this document] | Intra-EU neutral | Intra-EU neutral; exposure through component imports |
| Resulting timing | Demand strongest but delivery dates slipping: an "air pocket" risk | Demand deferred or displaced: 63% of new European capacity now outside FLAP-D [SOURCE: TNW] | Demand arriving: Google EUR 13 bn 2027–28, Microsoft Vaasa land [SOURCE]; timing hinges on connection rules |

Consequence: the same global signal (hyperscaler capex) reaches the Nordics 1–2 years later than the US and with a policy filter in between. A Nordic picture must therefore combine global capex signals with local connection data; neither alone is sufficient. For the rest of Europe, utility grid investment (EUR 584 bn) is the floor under relay demand regardless of data centres [SOURCE: COM(2023) 757].

### 1.5 What follows for ABB: which questions a better market picture changes

The system does not set quantities or order dates for these decisions; it changes the evidence available when ABB decides, and it proposes a conditional move for each decision area (procurement, manufacturing, capacity, supply reliability) under the scenario it currently finds most likely (section 4.10).

- **Component commitment timing and size** (18-month orders placed now for 2028 delivery [ABB]): which scenario is the order being placed into, and what evidence would change that view before the next order window. Under the leading scenario the proposed moves are preparatory, for example to prepare a second-source qualification for memory-dependent relay boards, so that the commitment window can be extended if the tight-supply reading holds. The size and timing of the order stay with the planner.
- **Allocation between internal switchgear factories and external customers** when demand exceeds supply [ABB]: which segment's demand is structural and which is amplified. The proposed move is to agree the sharing rule before a demand peak turns it into a dispute, activated when ABB's own order signals and Nordic site announcements rise together.
- **Capacity investment in assembly and test**: only relevant in scenarios where the component constraint loosens while demand continues ("Growth continues, components become easier to get"). The recommendation template for that scenario carries a contingent capacity move next to a no-regret procurement one.
- **Price and timing risk in frame orders** (new to the unit [ABB]): copper and memory price scenarios attached to delivery dates a year out, as another ABB business already does with copper indexation [ABB].
- **When to escalate to S&OP**: the next action names the item for the agenda, an owner and a due date, which is an action for the planner, not a purchase action.

---

## 2. Data & signal portfolio

### 2.1 Signal table (37 cards in the current world situation: 35 sourced public cards, 1 [DEMODATA] placeholder (SIG-015) and 1 internal placeholder (SIG-017); SIG-018 to SIG-025 from the news of 21 September to 3 October 2026, SIG-026 to SIG-032 from research institutions with Koomey and GridLab's 2026 forecast critique as counter-evidence, SIG-033 found by the automatic scout, SIG-034 to SIG-037 four sourced negative-direction cards with counter-evidence CE-033 to CE-036; the constructed downturn world has 24 cards)

Type: L = leading, C = coincident, G = lagging. Reliability: A primary (TSO, regulator, filing, IEA), B reputable secondary, C blog or unverified. Lead months are per-card assumptions, stated on the card.

| ID | Signal | Type | Lead (mo) | Update | Source and access | Rel. | Restrictions |
|---|---|---|---|---|---|---|---|
| SIG-001 | Fingrid signed DC connection agreements (>3 GW, June 2026) | L | 30 | Quarterly | Fingrid half-year report, public PDF | A | Project-level data not disclosed |
| SIG-002 | Fingrid DC connection inquiries (~24 GW) | L | 36 | Event | Borenius legal alert, DCD; public web | B | Secondary reporting of Fingrid data |
| SIG-003 | Google EUR 13 bn Finland programme 2027–28 | L | 20 | Event | Company announcement via press | A | Site MW not disclosed |
| SIG-004 | Hyperscaler 2026 capex guidance (USD 720–745 bn) | L | 15 | Quarterly | Earnings calls, SEC filings; Axios compilation | A | US-weighted, no EU split |
| SIG-005 | US 2026 DC projects delayed/cancelled (30–50%) | C | 6 | Quarterly | Secondary blogs citing brokerage data | C | Primary report paywalled; do not quote externally |
| SIG-006 | IEA DC electricity 415 → 945 TWh (2024→2030) | G | 48 | Annual | IEA report, CC BY 4.0 | A | Attribution required |
| SIG-007 | TrendForce DRAM contract price QoQ | C | 4 | Quarterly | Press releases public; series paid | A | Licence for full series |
| SIG-008 | Industrial 32-bit MCU lead times (52–55 weeks) | C | 3 | Monthly | Distributor intelligence (J2, Welllink) | B | Verify with ABB supplier confirmations |
| SIG-009 | ECIA memory IC sentiment index (180) | L | 6 | Monthly | ECIA survey via Electronics360 | B | Index, not volume |
| SIG-010 | LME copper 3-month (USD 14,347/t, 2026-10-02) | C | 3 | Daily | LME via Benchmark/Investing News; delayed quotes public | A | Real-time data licensed |
| SIG-011 | FI vs DE power price gap (40.5 vs 89.3 EUR/MWh, 2025) | L | 24 | Annual | Nord Pool via Fortum | A | Granular series licensed |
| SIG-012 | EU core-market moratoria and queues | L | 18 | Event | EUDCA/EnkiAI, DCD, TNW; TSO decisions primary | B | Public |
| SIG-013 | EU grid investment need (EUR 584 bn) | G | 36 | Annual | European Commission COM(2023) 757, EUR-Lex | A | Public |
| SIG-014 | Finland connection-priority rule change (proposed) | L | 12 | Event | DCD; ministry consultation primary | B | Outcome pending |
| SIG-015 | DRAM spot-to-contract spread | L | 3 | Weekly | **[DEMODATA]** placeholder for DRAMeXchange | C | Paid subscription |
| SIG-016 | Microsoft 470-acre land purchase, Vaasa/Mustasaari | L | 36 | Event | Computer Weekly | B | Public |
| SIG-017 | ABB frame purchase order coverage | L | 12 | Monthly | **ABB SAP ERP, not connected** | — | Internal, confidential |
| SIG-018 | Micron: memory demand to exceed supply through 2028 (2026-10-01) | L | 12 | Event | WinBuzzer reporting Micron's results call | B | Primary is the earnings call |
| SIG-019 | EU data-centre rating scheme; capacity to triple (2026-09-21) | L | 24 | Event | European Commission IP/26/1667, public | A | Public |
| SIG-020 | ABB Q2 2026 record orders, data-centre orders at triple-digit growth | C | 6 | Quarterly | ABB Q2 2026 results via Finimize | B | Public company results |
| SIG-021 | Enetron Park 250 MW Pyhäjoki, contested planning (early Oct 2026) | L | 36 | Event | DCD | B | Date assumed, early October |
| SIG-022 | Fingrid KJV2026 grid code submission Oct–Nov 2026 | L | 12 | Event | Fingrid draft page | B | Public |
| SIG-023 | Big-tech commitments to Finland > USD 30 bn (2026-09-10) | L | 24 | Event | Fortune | A | Overlaps SIG-003/016 |
| SIG-024 | atNorth 30 MW Stockholm (Q4 2027) and 350 MW Norway | L | 18 | Event | DCD | B | Month-level date |
| SIG-025 | Hyperscaler 2026 capex projection ~USD 780 bn incl. Oracle (2026-10-03) | L | 15 | Weekly | Secondary newsletter | C | Do not quote externally |
| SIG-026 | Ember: European DC demand 96 → 168 TWh by 2030, Nordics tripling (June 2025) | G | 36 | Annual | Ember report, public | A | Public |
| SIG-027 | LBNL/DOE: US DC electricity 176 TWh (2023) → 325–580 TWh (2028) | G | 36 | Annual | LBNL report for US DOE | A | Public |
| SIG-028 | Uptime Institute 2026 survey: power availability concerns 64%, power behind 56% of worst outages | C | 12 | Annual | Uptime Institute | A | Full report for members |
| SIG-029 | Goldman Sachs Research: DC power demand +165% by 2030, 55 → 92 GW by 2027 | G | 36 | Annual | GS Research | A | Public summary |
| SIG-030 | McKinsey: European DC power 62 → >150 TWh by 2030, IT load 10 → 35 GW | G | 36 | Annual | McKinsey | A | Public |
| SIG-031 | IEA Electricity Mid-Year Update 2026: DC demand +17% in 2025, AI DCs +50% | G | 24 | Annual | IEA, CC BY 4.0 | A | Attribution |
| SIG-032 | Finnish Government: committed DCs add 8–10 TWh; AFRY price study | G | 30 | Annual | valtioneuvosto.fi; Yle | A | Public |
| SIG-033 | Valorem plans a 30–50 MW data centre in Savonlinna from 2028, over 100 MW by 2032 (2026-09-14) | L | 18 | Event | Yle Uutiset; public web; saved by the scout | B | Planning stage; the land reservation is non-binding (CE-032) |
| SIG-034 | Energinet (Denmark): no new large grid connection agreements before autumn 2026 (2026-05-27) | L | 18 | Event | Energinet press release via Ritzau; public | A | Public; overlaps with the Energinet reference in SIG-012 |
| SIG-035 | EirGrid (Ireland): data-centre applications in constrained network areas cannot progress (2026-05-20) | L | 18 | Event | EirGrid policy PDF (DCCOPP v3); public | A | Public |
| SIG-036 | Netherlands: court rules TenneT need not connect a 70 MW data centre on an overloaded grid (2026-04-30) | C | 12 | Event | W.Media citing NU.nl; public trade press | B | Secondary; the ruling itself was not read |
| SIG-037 | Wood Mackenzie: US grid operators expected to commit to about 28% of 1,066 GW of requests (2026-08-12) | L | 12 | Event | Energy Central summary, first reported by Bloomberg | C | Secondary; do not quote externally without the primary report |

**Cards that point the other way.** Seven cards carry direction −1: SIG-005 (US delays), SIG-014 (Finnish priority-rule change), SIG-015 ([DEMODATA] spread), and the four added ones, SIG-034 to SIG-037 (grid-connection limits in Denmark, Ireland and the Netherlands, and the share of US requests utilities expect to serve). Together they subtract 0.17 from the log-odds of the leading scenario (section 4.4). The Signals page lists them in a **negative-signals list** together with the counter-evidence cards attached to growth-supporting cards (38 entries today: 7 signals and 31 counter-evidence cards), signals ordered by weight and counter-evidence by reliability times strength, so that the reversal-warning side of the picture is as easy to read as the growth side.

Research anchors (SIG-026 to SIG-032) are annual publications with a low freshness weight; they bound the structural trend and are each challenged by the Koomey and GridLab (2026) finding that data-centre load forecasts are biased toward overestimation, so no research projection can dominate the picture on its own.

Access methods in production: TSO reports (PDF, quarterly, scrape or manual), company filings (SEC EDGAR API, free), TrendForce and DRAMeXchange (licence), LME delayed quotes (free, delayed), Nord Pool (API for members, annual averages free), ECIA (member survey), EUR-Lex (free), news sources (RSS). The collector agent normalises all of them into the same card schema.

### 2.2 Signals that measure end demand (not intermediary behaviour)

SIG-001 (signed agreements), SIG-003 (committed investment with a 22-year PPA), SIG-004 (capex guidance), SIG-006 (consumption projection), SIG-011 (price differential driving site selection), SIG-013 (regulated grid capex), SIG-016 (land). These are what data-centre operators and utilities commit to, independent of what anyone orders from ABB.

### 2.3 Signals that measure supply tightness

SIG-007 (contract prices), SIG-008 (lead times), SIG-015 (spot spread), plus CE cards on capacity reallocation. In production: supplier allocation letters, EMS partner confirmations, memory maker capex announcements.

### 2.4 Five bullwhip metrics: real demand vs hoarding

All five are computed by code (`engine/bullwhip.py`); thresholds are stated and adjustable.

| Metric | Definition | Reading that signals hoarding | Prototype status (2026-10-03) |
|---|---|---|---|
| BW-1 Order amplification ratio | (1+g_orders)/(1+g_end-demand) over 12 months, orders = switchgear-OEM relay orders, end demand = energised DC MW | ≥ 1.3 | 1.35, hoarding risk **[DEMODATA inputs]** |
| BW-2 Memory price momentum | Latest change of the QoQ contract price increment (pp); the second difference is kept alongside | Increment shrinking two quarters in a row while still positive = pre-peak | Prices still rising (+12% QoQ) but the increment has shrunk two quarters in a row (latest change −3 pp), hoarding ending [SOURCE: TrendForce 1Q–4Q26, the 4Q26 point is TrendForce's forecast; the 4Q25 base is DEMODATA] |
| BW-3 Double-ordering index | Lead times and distributor inventory days rising together | Both > +15% | 0.22, hoarding risk **[DEMODATA inventory input]** |
| BW-4 Spot-to-contract spread | Spot premium over contract DRAM | Premium collapsing while lead times still long = hoarding ending | 6% from 28% peak, hoarding ending **[DEMODATA]** |
| BW-5 Push-out / cancellation rate | Share of frame-order quantity rescheduled out or cancelled in 90 days | ≥ 10% | not connected (ABB SAP schedule-line history) |

Combined reading in the prototype: **mixed, turning**: hoarding indicators elevated, two urgency measures already fading, structural end-demand signals intact. This is ABB's braking signal, expressed as five numbers with their inputs labelled.

### 2.5 The role of copper

Copper is priced by the electrification demand of the whole world at once: grids, data centres, vehicles, and speculative positioning. In this chain it does three things. First, it is a **fast coincident cross-check**: if the end-demand cards say acceleration and copper is falling for a quarter, one of them is wrong. Second, it is a **cost-side risk** for ABB's customers (switchgear is copper-heavy) that feeds back into project economics and therefore timing. Third, it is the **mechanism ABB already uses** for price risk: another ABB business indexes offers to copper because delivery is a year out [ABB]. What copper does not do is lead: a record on 2026-09-09 followed by a retrace within days [SOURCE] shows how much positioning sits in the level. The card therefore carries lead time 3 months, type coincident, and the Goldman Sachs decline forecast as counter-evidence [SOURCE].

### 2.6 Where ABB's internal data plugs in later

| Field | System | What it adds |
|---|---|---|
| Frame PO / scheduling agreement coverage by customer segment and region (months of forward demand) | SAP ERP: purchasing and sales documents (EKKO/EKPO, VBAK/VBAP or equivalent); S&OP export | SIG-017: compares committed customer intent with public end-demand signals; a widening gap is a bullwhip warning |
| Schedule-line change history (push-outs, cancellations) | SAP sales order change log (VBEP) | BW-5: the earliest internal braking signal |
| Quote pipeline by segment, win rate, tender count | CRM / tender database | Detects multiple bidding on the same end project (step 2 of the bullwhip) |
| Supplier allocation and confirmed lead times per critical part | SAP MM purchase order confirmations; supplier portals | Replaces distributor blogs (SIG-008) with A-grade data |
| Internal ABB switchgear factories' own forecasts | Inter-company planning | Removes double counting between ABB units |

Each becomes a signal card with the same fields, reliability A, and the same counter-evidence treatment. The engine does not change.

---

## 3. The analysis problem and the user

### 3.1 Who the user is and what they do with the information

The user is the **component procurement lead or S&OP planner** at ABB Distribution Solutions who prepares the 18-month component commitments and the demand review. Rhythm: a monthly S&OP cycle, a quarterly commitment window for critical components, and ad-hoc checks when a supplier changes allocation. They read the scenarios, the evidence and the recommended move with its next action, decide which cards they trust, and bring the picture into the S&OP meeting. The system records their confirmations and disputes and shows the effect on weights; it does not act on them beyond that.

### 3.2 What they cannot see today

Their information source is the order book and customers' frame orders, which are indications, not commitments, and carry price risk [ABB]. "The best forecast has been history" worked while the business was flat [ABB]. The order book turns 18–30 months after the market event that drives it (section 1.1), which is after the component window. Internal forecasts can also double-count the same project through several bidding units [ASSUMPTION]. The planner is therefore deciding 2028 component volumes with 2026 order data and no view of the hoarding component inside it.

### 3.3 The change that must be detected

- **Turning point**: end demand stops accelerating while orders still rise (bullwhip peak).
- **Acceleration**: signed connection agreements and capex guidance rise together, as in 2026.
- **Deceleration**: capex guidance cut, connection agreements stall, spot premiums collapse.
- **Regional shift**: demand moving from FLAP-D to the Nordics, or from Finland to Sweden/Norway if Finnish queue rules change.

### 3.4 Required lead time

Critical components are ordered 18 months ahead [ABB]. A signal that is only visible at the switchgear tender (6–12 months before the ABB order) arrives 24–30 months after the component decision it should have informed. The picture must therefore reach **at least 24 months** [ABB], which is why the portfolio is weighted toward links 1–3 of the chain (capex, land, connection agreements) and why every card states its lead-month assumption. The prototype shows the maximum horizon covered (48 months, from the IEA card) and how many cards reach 18 months or more (21 of 37).

### 3.5 Misreading the signal, in both directions

- **False acceleration** (reading hoarding as demand): ABB places ten-fold component orders that are never consumed [ABB's own risk statement]. Cost: inventory at peak prices, write-downs, and cash tied up while the price falls (the scenarios "Investment slows down, stock piles up" and "Duplicate orders unwind, stock is released").
- **False deceleration** (reading a timing air pocket as a turn): ABB under-orders, delivery times stretch past 10 weeks, allocation disputes with internal customers, lost structural growth. This is the risk of reading the scenario "Projects slip, components stay scarce" as the truth when the projects are only delayed.

How the system protects against false certainty:

1. **Uncertainty is displayed**, not hidden: four probabilities and their entropy (0.77 today, where 1.0 is "no idea"), and the recommended move carries a confidence level (medium today, from the margin to the runner-up and the entropy).
2. **Counter-evidence is mandatory**: every strong signal is challenged by an agent whose only job is to find the opposite case; an unchallenged card is capped at weight 0.6.
3. **Scenarios are parallel**: the least likely of the four shown ("Projects slip, components stay scarce", 3%) is shown with the same detail as the leading one, including the early signs that would raise it, and the recommendation names a hedge for the runner-up.
4. **Data provenance is on every number**: SOURCE, DEMODATA or ASSUMPTION, with date and URL.
5. **The human can dispute**: a dispute halves the weight and is logged with a name and reason; the next reader sees it.
6. **Every move states what would change it and what it costs if wrong**: the trigger signals, the cost if wrong, a revisit date and "The planner decides" are part of the recommendation, not a footnote.

### 3.6 Why the recommended move is qualitative and conditional

The brief asks for a decision recommendation and a next action, and ABB asked for insight and scenarios on which ABB can think its own decisions through, "never black and white" [ABB]. Both are met by a move that says what to prepare, review, watch or agree, under which condition, and what it costs if the reading is wrong. Three reasons keep it from going further, to a quantity or an order date.

1. **The order book lags the market by 18 months or more**, and the component window closes before the order book shows demand (section 1.1). The only evidence available at decision time is the open market picture, which says where the market is heading but not what ABB's contracts, allocations and customer commitments already cover.
2. **The information that decides a purchase is not in open data**: frame contracts, supplier allocation agreements, cash position, internal priorities, and the customer relationships ABB chooses to protect [ABB]. A quantity computed from the market half would be false authority in a decision owned by the person who holds the other half.
3. **The probabilities are traceable, not calibrated** (section 4.4). A move conditional on a scenario at 50% is honest about that; an order size derived from it would not be.

What the planner gets is therefore the earliest possible conditional direction (for example, to prepare a second-source qualification for memory-dependent relay boards so that the next commitment window can be extended if the tight-supply reading holds), the signals that activate or retire each move, a hedge if the runner-up scenario overtakes, one next action with an owner and a due date, and a revisit date. The boundary is enforced in code in two places: the recommendation is composed from templates that contain no quantities, order points or order dates (a test checks every move text), and a deterministic guardrail (`agents/llm.py`) removes purchase, quantity and order-timing language from any text a language model writes. The planner decides.

---

## 4. AI solution concept

### 4.1 Architecture

**Data sources → integration layer → agent layer → evidence store → scenario layer → user interface.**

- **Data sources**: TSO reports, company filings, price services, policy documents, news; later ABB ERP and CRM exports.
- **Integration layer**: scheduled collectors (RSS, APIs, PDF parsing), unit and date normalisation, deduplication by content hash, provenance stamp (source, URL, retrieval time, licence).
- **Agent layer**: eight agents (4.2). Language models read and classify; code computes. Rationale: a model that produces numbers can hallucinate them; a model that quotes a sentence and assigns a grade can be checked against the quote. Every numeric field on a card is either copied from a source excerpt or computed by `engine/`.
- **Evidence store**: signal cards, counter-evidence cards, annotations, run traces. Append-only; every weight is recomputable from stored inputs.
- **Scenario layer**: the 2×2 framework with log-odds accumulation (4.4), probability history, signposts and falsifiers.
- **User interface**: a minimal interface in the style of consumer finance applications (section 5): one most-likely scenario on the front page, daily probability tracking, strong and weak signal lists, notifications, and everything secondary behind a click.

### 4.2 The agents

| # | Agent | Responsibility (one sentence) | Input | Output | On failure |
|---|---|---|---|---|---|
| 1 | Collector & normaliser | Pulls raw items and normalises date, units and provenance into one record. | Source feeds, pasted items | Normalised item with hash and label | Undated items get freshness 0 and a note; nothing is fabricated |
| 2 | Demand signal agent | Verifies each end-demand item against its primary source on the web, then classifies it into a signal card. | Normalised item; web search and fetch | Card draft with theme scores, reliability, quote; web verification record (corroborated, primary source, queries, pages retrieved) | No web: classifies without verification. No model: replayed or keyword heuristic output, reliability C, flagged for review |
| 3 | Supply signal agent | Same as 2 for component availability items (prices, lead times, allocation). | Normalised item; web search and fetch | Same card schema and verification record | Same as 2 |
| 4 | Demand-quality (bullwhip) agent | Computes the five bullwhip metrics and labels apparent demand as end use or hoarding. | Metric inputs | Metric values, statuses, combined reading | Missing inputs are reported as "not connected", never estimated |
| 5 | Counter-evidence agent | Searches the web for evidence that contradicts every new signal and links only sources it actually retrieved. | New or strong card; web search and fetch | Counter-evidence cards with source link, date, quote, domain-graded reliability | Link not among retrieved pages: removed, graded C, strength capped at 0.3. Search finds nothing: no placeholder, card counts as challenged. Web unavailable: model without search, then placeholder with the 0.6 weight cap |
| 6 | Scenario agent | Recomputes weights and the four scenario probabilities, at the headline and at the 12, 24 and 36 month horizons, and records the change. | All cards and evidence | Probabilities, contributions per signal, entropy, deltas, ranking per horizon | Pure code; if inputs are missing the previous state is kept and marked stale |
| 7 | Interpretation agent | Writes what each scenario would mean for ABB demand, delivery capability and component need, in conditional form. | Scenario state, new card | Conditional text per scenario | Falls back to the scenario's stored interpretation plus the computed contribution; guardrail strips any recommendation language |
| 8 | Explainer agent | Writes the cited situation brief and answers questions about the evidence. | Scenario state, bullwhip reading, cards | Brief with [SIG-xxx] citations; next analysis step (watch list, re-evaluation date, reviewers) | Falls back to a template brief composed from computed numbers; retrieval-based answers with citations |
| 9 | Recommendation (code, no model) | Composes the recommended move for the leading scenario: conditional moves per decision area, trigger signals, cost if wrong, a hedge for the runner-up, a next action and a revisit date. | Scenario state, weights, signal cards, templates in `data/recommendations.json` | `state.recommendation` | Unknown scenario id: no move is shown rather than a wrong one; the guardrail still applies to any model text |

No language model writes the recommendation. It is assembled by code (`engine/recommend.py`, shown as the "Recommendation agent (code)" step in the run trace right after the scenario agent) from labelled templates and the computed scenario state, and its trigger ids are matched to real cards in the current world by card fields, never hard-coded; section 4.10 describes it. The "next analysis step" of the brief is built by code from the largest contributions and their freshness; it names signals, a date and reviewers. The agents that do use a model (2, 3, 5, 7, 8) read, classify, challenge and explain; none of them is allowed to recommend, and the guardrail removes purchase, quantity and order-timing language from their text.

Model and SDK: Claude via the Anthropic SDK (`claude-opus-5-5` by default), structured outputs for card drafts (`messages.parse` with a Pydantic schema), server-side refusal fallback enabled for free-text calls. Without credentials the agents run in replay/heuristic mode and say so in every trace step.

### 4.3 Signal card data model

| Field | Meaning | Who sets it |
|---|---|---|
| `id`, `name`, `short` | Identity | Collector |
| `source {name, url, access, date}` | Provenance; URL opens from the card | Collector |
| `observed_at` | Date of the observation (drives freshness) | Collector |
| `direction` (+1 / 0 / −1) | Toward demand acceleration or supply tightness, or the opposite | Classifier (LLM or human) |
| `strength` (0–1) | Size of the move relative to the signal's own history | Classifier; the z-score estimator from SOURCE history is averaged in by code when it exists |
| `reliability` (A/B/C) | Source grade | Classifier, overridable by human |
| `freshness` (0–1) | 0.5^(age/half-life), half-life by update frequency | Code |
| `lead_months` + rationale | How far ahead of the ABB order the signal is visible | Classifier, assumption stated |
| `classification` (structural/cyclical/mixed) + rationale | Section 1.2 rule | Classifier |
| `measures` (end_demand / supply_tightness / intermediary / price / policy) | What the signal actually measures | Classifier |
| `value {number, unit, label}`, `excerpt` | The quoted fact and the sentence it comes from | Classifier copies; never computes |
| `history[]` + `history_label` | Series for sparkline, labelled SOURCE/DEMODATA | Collector |
| `axes {demand, supply, policy, price, nordic, bullwhip}` ∈ [−1, 1] | Loading on six themes; relevance to each of the nine candidate situations is computed from it (4.5) | Classifier; visible and disputable |
| `region`, `segment` | Where the signal applies (Finland, Nordics, EU, US, global) and which market; drives the region filter | Collector |
| `corroboration[]` (optional) | Further sources of the same fact: name, URL, grade, `derived_from` | Collector; only independent publishers count |
| `counter_evidence[]`, `ce_searched` | Linked counter-evidence cards; whether the search ran | Counter-evidence agent |
| `annotations[]` | confirm / dispute / comment with author, time, note | Human |
| `data_label` | SOURCE / DEMODATA / ASSUMPTION | Collector |
| `computed {weight, components, band, attribution, horizon_fit, horizon, assumptions}` | The formula result with its factors, the aggregation band, the attribution of the discount, the fit and weight at 12, 24 and 36 months, and every assumption used | Code |
| `change {status, weight_prev, delta, since}` | Change since the previous update cycle: new, up, down, flat, flipped | Code |

### 4.4 Weight, horizon and probability: the formulas

**Signal weight** (code, `engine/weights.py`). The weight is an ensemble of four conditions that must all hold: the claim is credible, it is current, the move is material, and the planner does not dispute it. The rule behind the design is to **multiply conditions that are different things, and average estimators of the same thing**. Equal weights inside an average, because there is no outcome data to fit them on.

```
w   = min(1, Bel × F × M × H)            headline weight, 0..1
      if the card was never examined by the counter-evidence search: w = min(w, 0.6)
w_h = w × T(h)                            weight at horizon h = 12, 24, 36 months

Bel  credibility   Dempster–Shafer belief that the claim is true, on the frame {true, false}
       s  = 1 − (1 − R) × Π_j (1 − R_j)                     support from the primary source and every independent corroborating source
       c  = min(0.8, 1 − Π_ce (1 − R_ce × strength_ce))     attack from counter-evidence (noisy-OR: duplicate doubts do not stack)
       Bel = s × (1 − c),   plausibility Pl = 1 − c × (1 − s)
       R: A = 1.0, B = 0.7, C = 0.4 [ASSUMPTION]
F    currency      0.5^(age_days / half_life), half-life by update frequency: daily 14 d, weekly 30, monthly 60, quarterly 120, annual 240, event 90 [ASSUMPTION]
M    materiality   mean of the available estimators of "how big is the move":
                     strength on the card (always); and, only when the card's history is SOURCE-labelled and has at least 6 earlier moves,
                     min(1, |z|/3.5) from the robust z-score of the last move (Iglewicz and Hoaglin). DEMODATA history never drives a weight.
H    human view    Π annotation multipliers (confirm 1.2, dispute 0.5), clamped to [0.25, 1.5] [ASSUMPTION]
T(h) horizon fit   log-normal kernel on the card's lead_months L: exp(−½ (ln(h / L) / s)²), s = ln 2 [ASSUMPTION], for h < L.
                   Once the effect has arrived (h ≥ L): structural cards keep T = 1, cyclical cards fade with the kernel, mixed cards sit halfway.
```

What each part buys:

- **Credibility with corroboration.** With one source and one counter-claim this is exactly the earlier R × (1 − C). A second independent source (a different publisher domain, not derived from the first) raises support: two B sources give 1 − 0.3 × 0.3 = 0.91, not 0.7. Syndicated copies of one release count once. This estimator is in the engine and tested; **no card in the current data carries a corroboration list yet**, so today every card has one source.
- **Materiality from several estimators.** The z-score estimator needs a SOURCE-labelled history with enough earlier moves; **no current card qualifies**, so today M equals the card's strength. A single-source card without such history therefore receives exactly the weight the earlier formula gave it (a test checks this to four decimals for every card in both worlds).
- **The clamp.** The product used to be able to leave [0, 1]: a fresh A-grade card at full strength with two "confirm" annotations multiplied to 1.44. The weight is now clamped to 1, and the horizon weight never exceeds it (`w_h ≤ w`, tested).
- **The band.** The same four factors can be combined other ways. Each card carries the weight under four aggregators, product (the headline), minimum, geometric mean and arithmetic mean, and the interface shows the spread as a band. The band is the structural uncertainty of the aggregation choice: the product is the strictest as long as no factor exceeds 1, because a single failing condition pulls it down, and the others show how much the answer would rise if conditions were allowed to compensate for each other.
- **The attribution waterfall.** For each card, the discount from 1.0 is shared among the four conditions as ln(1/c_k) / Σ ln(1/c_k), which is order-independent and sums to 1. It answers "why is this weight not higher": the answer is credibility (doubt), currency (age), materiality (small move) or the planner.
- **The horizon fit.** Every card states how many months ahead of the ABB order it becomes visible. The kernel turns that into a weight per horizon: a card whose effect has not arrived yet inside a horizon counts for less there, and a structural card whose effect has arrived keeps its full weight. The kernel width is an assumption: ln 2, because the median high-to-low ratio of the eight lead-time ranges quoted on the cards is 2.

**Worked example 1: a strong card (SIG-003, Google programme, 2026-10-03).** R 1.0 (grade A), F 0.83 (24 days old, event half-life 90 d), M = 0.90 (strength on the card), one B-grade counter-card at strength 0.3 so that c = 0.21 and Bel = 0.79, H 1.0, so w = 1.0 × 0.83 × 0.90 × 0.79 = **0.59**, the highest of the 37 cards. The band is 0.59 (product) to 0.88 (arithmetic mean). The discount from 1.0 is shared 45% credibility, 35% currency, 20% materiality, 0% human. Its lead time is 20 months and it is structural, so T(12) = 0.76 and T(24) = T(36) = 1.00: w₁₂ = 0.45, w₂₄ = w₃₆ = 0.59.

**Worked example 2: a doubted card (SIG-001, Fingrid signed agreements).** R 1.0, three counter-cards (A at 0.4, B at 0.3, A at 0.4) so that c = 1 − 0.6 × 0.79 × 0.6 = 0.72 and Bel = 0.28, F 0.66 (72 days old, quarterly half-life 120 d), M = 0.80, so w = 0.28 × 0.66 × 0.80 = **0.15**. The band is 0.15 to 0.69, and 66% of the discount is credibility: the doubts, not the age, are why a grade-A card counts little. Lead time 30 months, structural: T(12) = 0.42, T(24) = 0.95, T(36) = 1.00, so w₁₂ = 0.06, w₂₄ = 0.14, w₃₆ = 0.15. For contrast, SIG-007 (DRAM contract prices, cyclical, lead 4 months) has w = 0.33 and w₁₂ = 0.10, w₂₄ = 0.01, w₃₆ = 0.00: a price card speaks about the next year, not about 2028.

**Scenario probability.** The scenario layer is described in 4.5. It takes the weight w (or w_h at a horizon) as the strength of each card's vote.

The weights, the factor maps and the kernel width are assumptions, listed on every card under "assumptions" with their reasons. They are shown, not fitted: the update is **traceable, not a calibrated posterior** (r below is an analyst-set direction), and that is the honest description.

### 4.5 Scenario generation: the four most likely situations per run

The scenarios shown are not fixed. A pool of nine candidate situations (archetypes) is kept in `scenario_archetypes.json`, each with a profile on six axes (demand, supply, policy, price, Nordic shift, bullwhip), a prior, bilingual texts (name, narrative, confirming signposts, refuting indications, conditional implications for ABB) and an illustrative path. Every signal card carries loadings on the same six axes. On each update cycle:

```
r_is  = Σ_a axes_ia × profile_sa / Σ_a |profile_sa|           relevance of signal i to candidate s, in [−1, 1]
L_s   = ln(prior_s) + k × Σ_i w_i × r_is                      k = 1.5 [ASSUMPTION]
shown = the four candidates with the highest L_s;  p_s = softmax over the four
```

The priors are assumptions and sum to 1 (0.18 for "Growth continues, components stay scarce", 0.12 for three candidates and 0.09 for the other five, normalised proportionally so the ranking did not change). k = 1.5 means that one fresh grade-A card at full strength and relevance 0.5 shifts a candidate's log-odds by 0.75, which multiplies its odds by about 2.1; no single source can settle the picture.

**Worked example (2026-10-03).** SIG-003 has weight 0.59 and relevance +0.45 to "Growth continues, components stay scarce" (its themes are demand +0.9 and Nordic shift +0.9, the scenario's profile is demand +1.0 and Nordic +0.3 among other themes, and the sum of the profile's absolute values is 2.6, so r = (0.9 × 1.0 + 0.9 × 0.3) / 2.6 = 0.45). Its push is k × w × r = 1.5 × 0.59 × 0.45 = **+0.40** to that scenario's log-odds, and −0.15 to "Projects slip, components stay scarce" (r = −0.17). Across all 37 cards the leading scenario's score is built from the starting score ln(0.18) = −1.70, plus 28 positive pushes totalling +2.41 and 7 negative pushes totalling −0.17, which gives +0.54. The runner-up scores +0.23, so the leader is 0.30 ahead and about 1.4 times as likely. The result is:

| Scenario shown | Probability |
|---|---|
| Growth continues, components stay scarce | 50% |
| Investment concentrates in the Nordics | 37% |
| Growth continues, components become easier to get | 10% |
| Projects slip, components stay scarce | 3% |

Uncertainty (normalised entropy) is 0.77. With the constructed downturn dataset (world situation 2, 24 cards) the selection changes to "Duplicate orders unwind, stock is released" (36%), "Investment slows down, stock piles up" (35%), "Grid upgrades carry demand while data centres pause" (15%) and "Grid rules delay data centres" (14%), with uncertainty 0.93: a near tie that the recommendation reports as low confidence. A language model, when connected, rewrites the texts; the selection and the probabilities are always computed by code, and the full candidate ranking is visible in the method page.

**Horizon view (12, 24, 36 months).** The same update is run again with each card's horizon weight w_h instead of w, which gives a ranking per horizon (`scenarios_by_horizon`). In the current world situation the leader is "Growth continues, components stay scarce" at 12 months (47%, against 31% for the Nordics); at 24 months it is a near tie (41% against 40%); at 36 months "Investment concentrates in the Nordics" leads (42% against 39%). The reading is that the Nordic picture strengthens as the horizon lengthens, but the later gaps are small and depend on the kernel width: with s = ln 1.5 the 24-month leader flips to the Nordics, and with s = ln 3 the 36-month leader flips back to "Growth continues, components stay scarce" [ASSUMPTION: s = ln 2]. The 24 and 36 month rankings are therefore to be read as ranges, not verdicts, and the card's assumption list says so. The four scenarios shown at a horizon can differ from the headline four; in the downturn world they do.

**Scenario paths (1, 2 and 3 years).** Each candidate carries yearly growth parameters for two indices, demand and deliverable supply (100 = today), from which the interface draws a 36-month path with a widening band. The path depicts the scenario; it is labelled as an assumption and is not a forecast.

**Plain-language summary.** The first element on the page is a three-sentence summary composed from the axis scores and the leading scenario (demand growing, flat or falling; chips and memory hard or easier to get; the most likely path with its probability; the two signals to watch), in English and Finnish.

**Two mock worlds.** A small switch loads either the public October 2026 dataset (the current world situation) or a constructed stress dataset labelled DEMODATA throughout (world situation 2: investment cuts, cancellations, falling memory and copper prices, easing lead times, Finnish priority rules adopted). The switch exists to show how the selection, the summary, the notifications and the assistant react to a different world.

### 4.6 The human's role

The user **marks** cards as confirmed or disputed (weight ×1.2 or ×0.5, logged with name, time and reason), **comments** without changing weight, and **contests** classifications and lead-month assumptions (a comment on the card; a change of the field is an edit with the same log). Disputes are visible to every later reader, so the evidence base carries institutional memory rather than one analyst's opinion. The product of annotation multipliers is clamped to [0.25, 1.5] and the weight itself to 1, so repeated confirmations cannot lift a card above full weight. The system uses the annotations only through the H factor; it never suppresses a card or hides a scenario because of them. Over time, confirmations and disputes against realised outcomes become the data for calibrating r and the reliability grades, which is the first step from a traceable update toward a measured one.

### 4.7 Operations: scheduled updates, notifications and tracking

- **Update cycle.** The backend runs an update cycle every 60 minutes by default (configurable from 15 minutes to once a day in Settings, persisted to `settings.json`). Each cycle recomputes freshness, weights and scenario probabilities, writes the day's point into the daily history (hourly runs overwrite the same day's point, so the chart shows one probability per day), and checks the notification rules. In production the cycle also triggers the collectors; in the prototype the collectors run on demand.
- **Daily history.** Each point is the probability computed on that day. The 120 days before the prototype's start date are simulated and labelled DEMODATA in the interface; from the first live day onward the history is real.
- **Notifications.** Four rules, thresholds set by the user: a scenario's probability moves by at least N percentage points in a day (default 3); a signal's computed weight reaches the major-signal threshold (default 0.4); a price signal moves by at least N% between its two latest observations (default 5); the most likely scenario changes. The newest unread major notification is shown as a banner at the top of every page.
- **Tracking (lock).** Locking a signal marks it for close tracking: it is re-checked at every cycle, its check count and last check time are shown, and its notification thresholds are halved. Locking never changes the signal's weight, so a user's attention does not bias the probabilities.
- **Strong and weak signals.** A signal is listed as strong when its computed weight is at or above the strong-signal threshold (default 0.25), otherwise as weak. Weak signals are shown with the same calculation trail so that early indications remain visible rather than filtered out.


### 4.8 Web search for the agents

When an API key is configured, two agents use Anthropic's server-side web search and web fetch tools (`web_search_20260209`, `web_fetch_20260209`). The searches and page reads run on Anthropic's servers; code decides what survives.

- **Verification before classification.** The demand or supply agent fetches the item's own URL and searches for the primary source and independent corroboration. If a primary source is found among the pages actually retrieved, the card takes that source's name, link and date, and its reliability comes from the publisher's domain: grid operators, regulators, statistics, company releases and research institutes are A, reputable press and research are B, everything else C. An item that cannot be corroborated becomes a C-grade card flagged for review; a new observation of an existing card only raises the flag.
- **Counter-evidence from the web.** The counter-evidence agent searches for evidence that contradicts, weakens or delays the signal. Each proposed source is accepted only if its URL is one of the pages the tools returned in that turn. A fabricated or unretrieved link is removed and the claim is kept as a C-grade assumption with strength capped at 0.3. If the search finds nothing, no placeholder is added and the card counts as challenged.
- **Limits and settings.** Search and fetch are restricted to an allowlist of 47 domains (29 of them graded A), editable in Settings together with the number of searches (default 3) and page fetches (default 2) per agent call. Fetched pages are capped at 8,000 tokens. A paused server turn is resumed at most twice.
- **Failure behaviour.** Any API error, refusal or unparsable answer falls back to the previous behaviour without breaking the run, and the trace records why. Each card shows the queries that were run and the pages that were retrieved.
- **Cost.** Web search costs USD 10 per 1,000 searches plus tokens; web fetch has no fee beyond the tokens of the fetched text. With the defaults, one imported item adds up to six searches and four page fetches. [ASSUMPTION: 15,000–50,000 extra input tokens and 1,000–4,000 extra output tokens per item] This raises the cost per item from about USD 0.09–0.22 to about USD 0.20–0.55 and the running time to about 1.5–4 minutes. The hourly update cycle still makes no model calls.
- **Testing.** Without an API key the path is tested with a fake client returning the real response block types (search results, fetched pages, citations, a paused turn, a fabricated link and an API error); the six tests cover verification, link removal, domain grading, continuation and fallback.


### 4.9 Automatic search for new signals (scout)

On every update cycle (hourly by default), on "Run update now" and at start-up, a scout agent searches the trusted domains for new items on eight themes: data-centre projects, hyperscaler investment, grids and connections, energy policy, component supply, commodity prices, electrification equipment and research outlooks. It runs in the background, works only in the current world situation and only with an API key, and never adds anything that fails a check.

**First checks, by code, on the scout's answer:**

1. The link is one of the pages the search tools returned in that turn, and the page was actually read or cited, not merely listed.
2. The publisher is graded A or B (configurable to A only).
3. The page shows a publication date no older than the limit (default 30 days).
4. The item belongs to a defined theme and states how it moves relay demand or component supply.
5. The quoted supporting sentence is found in the text the tools retrieved.
6. The link and the headline are new.

**Full check, on a copy of the data:** the verification, classification and counter-evidence agents run on the candidate. It is added only if a primary source corroborates it, the card's reliability meets the minimum, it moves at least one scenario theme by the minimum load (default 0.3), its computed weight after counter-evidence and freshness reaches the minimum (default 0.15), and it is not the same fact as an existing card. An update to an existing card must be newer than the current observation.

**If nothing passes, nothing is added.** Every candidate is logged with its decision and reason, in English and Finnish, on the Signals page. Rejected links are remembered for the age window so they are not paid for again. Accepted signals are saved and reload after a restart, and can be removed from Settings. Each accepted signal raises a notification and is labelled "found automatically", with the reason it counts as a signal.

**Cost (estimate):** about USD 0.10–0.30 per run for discovery (up to four searches plus tokens), plus about USD 0.20–0.55 for each candidate that reaches the full check (at most three per run by default). With hourly updates, discovery alone comes to about USD 2.40–7.20 a day; the update interval in Settings controls this. Each run records its searches, tokens and an estimated cost.

**Testing:** without an API key the scout is tested with a fake client. One test answer contains six candidates, each built to fail a different first check except one that qualifies. Further tests cover an empty answer, an uncorroborated candidate (live data stays unchanged), a weak candidate rejected on weight, saving and reloading, and the background run.


### 4.10 Recommended move and next action

The recommendation is the step the brief asks for between the scenario and the next action. It is written by code (`engine/recommend.py`, templates in `data/recommendations.json`, every template and threshold labelled ASSUMPTION), not by a language model, so that it can be tested and so that no model can slip a quantity into it.

1. **Leading scenario and confidence.** The leading scenario and the runner-up come from the scenario layer. Confidence is *low*, *medium* or *high* from the probability margin to the runner-up and the normalised entropy (high needs a margin of at least 0.20 and entropy at most 0.70; medium a margin of at least 0.08 and entropy at most 0.90 [ASSUMPTION: untested thresholds, to tune with ABB]). Today the margin is 0.13 and the entropy 0.77, so confidence is **medium**; in the downturn world it is low.
2. **Moves.** Each of the nine candidate situations has a template with three or four moves across the decision areas *procurement*, *manufacturing*, *capacity* and *supply reliability*. A move is **no-regret** (it is worth doing under every plausible scenario, or costs little if the reading is wrong) or **contingent** (it applies only while its trigger holds). Each carries a trigger text, the **trigger signals** (real card ids), its **cost if wrong** and a **horizon** of 12, 24 or 36 months.
3. **Trigger signals are matched, not hard-coded.** A template names signal themes (for example "memory contract prices and microcontroller lead times"). The engine maps each theme to cards of the current world by their fields (category, what they measure, region, source class), strongest weight first, so the same templates work in the downturn world and for a card the scout adds.
4. **Hedge.** What changes if the runner-up overtakes the leader.
5. **Next action.** One action with an **owner** and a **due date** (today + 14 days [ASSUMPTION]), and a **revisit date** (today + 28 days, the monthly S&OP cycle [ASSUMPTION]).
6. **The boundary.** Every recommendation ends with "The planner decides. Irma has no contract, allocation or cash data, so this gives conditional moves only: no quantities and no order timing." Tests check that every template is covered, that every trigger id exists, that no move text contains a quantity, an order point or a date, and that the texts pass the guardrail unchanged.

**The current world situation (2026-10-03).** Leading scenario "Growth continues, components stay scarce" (50%), runner-up "Investment concentrates in the Nordics" (37%), confidence medium. Headline: *prepare a second-source qualification for memory-dependent relay boards so the next commitment window can be extended if the tight-supply reading holds.*

| Area | Type | Horizon | Move | Trigger signals |
|---|---|---|---|---|
| Procurement | No-regret | 12 months | Prepare a second-source qualification for memory-dependent relay boards, so the next commitment window can be extended if the tight-supply reading holds. | SIG-007, SIG-018, SIG-015, SIG-009 |
| Manufacturing | Contingent | 12 months | Identify which relay variants carry the longest-lead components and protect assembly slots for those variants first, if data-centre project conversion continues. | SIG-007, SIG-018, SIG-003, SIG-033 |
| Capacity | Contingent | 24 months | Agree with the internal switchgear factories how scarce relay supply is shared between internal and external customers, before a demand peak turns it into a dispute. | SIG-020, SIG-017, SIG-023, SIG-024 |
| Supply reliability | No-regret | 12 months | Ask the main memory and microcontroller suppliers for a written allocation and lead-time status at every review, and log each change next to the signal cards. | SIG-007, SIG-018 |

*Hedge:* if "Investment concentrates in the Nordics" overtakes the leader, capacity and delivery priority for Nordic projects would come first, with variant standardisation following; the no-regret moves stay and the contingent ones are read again. *Next action:* put the second-source qualification on the agenda of the next S&OP review and agree which signals decide whether the commitment window is extended; owner: the component procurement lead with the S&OP owner; due 2026-10-17; revisit 2026-10-31. Three moves have a 12-month horizon and the capacity move 24 months.

What the recommendation does not contain is as deliberate as what it does: no unit counts, no safety-stock levels, no order dates, no price levels. Those need ABB's contracts, allocations and cash position (section 3.6).

### 4.11 Changes since the last cycle and the negative list

- **Signal changes.** Each card carries a change against the previous update cycle: *new* (not in the baseline), *up*, *down*, *flat* (|Δ| < 0.01 [ASSUMPTION]) or *flipped* (direction changed), with the weight before and the delta. On a first start the baseline is the weights as they were seven days earlier [ASSUMPTION], and cards observed since then are *new*. The change list leaves out flat cards, puts new cards first and orders the rest by the size of the change. In the current world situation 6 cards are new and 9 have weakened by 0.01 or more as they aged, SIG-003 the most (−0.03). After the Fingrid demonstration item is imported, SIG-001 is the only change: up by 0.02 (0.15 to 0.17).
- **Negative list.** The Signals page lists the cards with direction −1 and the counter-evidence cards against growth-supporting cards (section 2.1). Importing the demonstration item adds its two counter-evidence cards to the list (38 to 40 entries).

---

## 5. Demonstrable prototype

Location: `app/`. Backend: FastAPI with a deterministic engine, eight agents plus a code-only recommendation agent that also appears as a step in the run trace, a scheduled update cycle (hourly by default, configurable), persisted settings, notifications and daily probability history (`python3 -m uvicorn main:app`). Front end: minimal single-page application named Irma. Tests: `pytest` on the ensemble weights (single-source equivalence with the earlier formula, the clamp, band, attribution, horizon fit, corroboration, z-score), scenario update, bullwhip metrics, the recommendation (coverage of all nine situations, real trigger ids, no quantities, guardrail), signal changes, the negative list, the scout, web verification, the replayed pipeline run and the API (83 tests, all passing).

### 5.1 Views (Irma)

The interface follows the layout of a market terminal. The top bar has Overview, Signals, Scenarios and Settings, a search field, the FI/EN switch and the notification bell; "Import data" is a button on the Signals page. Below a 70/30 top row, the Overview has a signal list on the left, the scenario in focus in the centre, and an assistant on the right. ABB red and white, black top bar with the IRMA logo.

| View | What is shown | What the user does | Question it answers |
|---|---|---|---|
| **Overview** | A 70/30 top row. On the left (70%), "Current situation": the plain-language summary with the world-situation switch, a region filter and a (preview) segment filter, horizon chips and a line naming the leader at the chosen horizon, then the four most likely situations: one large chart of the selected situation on the left (projection of demand and deliverable supply for 1, 2 or 3 years, or the daily probability history) and three smaller charts below it that swap into the large one when clicked; under them the selected situation's narrative, the signals and sources used, confirming and refuting indications and the conditional implications for ABB. The horizon chips (1 y, 2 y, 3 y) re-rank the signal list by weight at 12, 24 or 36 months and show the scenario leader at that horizon, and whether it differs from the headline. On the right (30%), a compact **recommended move** card: the leading scenario and its probability, confidence and the ASSUMPTION label, the lead move in bold, the four moves with their area and no-regret or contingent tag (trigger signals, horizon and cost if wrong behind one disclosure), the next action with owner, due date and revisit date, and the hedge for the runner-up behind a disclosure. The Irma assistant, with three suggested prompts and a chat bar, stays in the right-hand column below. | Switches situations, changes the horizon, switches world, reads and follows the recommended move, asks the assistant | What is the situation in plain words, what are the four most likely paths, what evidence is behind each, and what should the planner prepare, watch or review as a result? |
| **Signals** | Strong signals and weak signals as two bullet lists, filtered by source class (contracts and commitments, component and commodity prices, market news, policy and institutional) and by the top-bar search. Each bullet states where the value is calculated from: source, date, reliability, freshness, strength, counter-evidence count and weight. A lock on each signal starts close tracking. A **Latest changes** box lists the biggest changes since the last cycle, and each card shows its change (new, up or down with the delta). A **Negative signals and counter-evidence** box lists the cards that point against growth and the counter-evidence behind growth-supporting cards. The region filter (all regions, Finland, Nordics, Europe, North America, global) filters the cards, and the horizon chips switch the weight shown. "Import data" opens the import page. | Filters by source class and region, searches, opens a signal, locks it, imports data | Which evidence carries the picture, what changed since I last looked, what speaks against it, and which early indications deserve attention? |
| **Signal** | Observed value and history, the weight with its band and its weight at 12, 24 and 36 months, source quote and link, and sections: classification rationale, "How the weight is calculated" (the formula, the attribution of the discount, the band across four methods, the horizon fit table, belief to plausibility, and every assumption used), counter-evidence, contribution to scenarios, assessment (confirm / dispute / comment) | Checks the source, disputes or confirms, locks | Where does this come from and what speaks against it? |
| **Scenarios** | Ranking of the four scenarios with probabilities and daily change; the selected scenario in detail: narrative, confirming signposts, refuting indications, implications for ABB (conditional), evidence for and against; the daily probability chart; the demand-quality check | Switches between scenarios; opens evidence; follows a cited signal | How could the market develop and what would each path mean for ABB? |
| **Import data** | New item (demonstration or pasted text), the resulting probability changes per scenario with a sentence on which signal moved each, side by side with the recommended move card computed after the import, then the signals to watch (weight, freshness, date) with the re-evaluation date and reviewers, the situation brief, implications by scenario, and the processing steps behind a disclosure | Runs the chain on new data | What happens when new information arrives, and why did the picture move? |
| **Notifications** | Major signals, large daily changes, changes of the most likely scenario, moves in tracked or price signals | Reads, opens the related signal or scenario, marks as read | What needs attention since I last looked? |
| **Settings** | Update frequency (15 minutes to once a day), thresholds for large changes, major signals and price moves, the strong-signal threshold, run-now and reset, and the method (formulas, agents, data labels, sources) behind disclosures | Adjusts cadence and thresholds; audits the method | How often does it run, and what counts as a large change for me? |

**The assistant.** The three suggested prompts are answered from the computed state with citations: the summary from scenario deltas, the newest evidence and open notifications; the procurement question with the next analysis step (signals to follow, re-evaluation date, reviewers) and the conditional component reading of the leading scenario, prefaced by the statement that order quantities and timing depend on contracts, allocation agreements and cash position that are not in the data, as the recommended move on the Overview also states; the component question from the supply-side cards and the five demand-quality indicators. With a model key the same composed context is passed to the model; the recommendation guardrail runs on every answer.

Daily and weekly readers get the same overview: the chart's 7-day and 30-day ranges show what moved since their last visit, and the notification list keeps what crossed a threshold.

### 5.2 Walkthrough: new data → signal detection → source and counter-evidence review → scenario → recommended move → next action

The challenge's chain ends in "decision recommendation for ABB → next action". The prototype implements both links: the **recommended move** is a conditional, qualitative move per decision area with its trigger signals, cost if wrong and horizon (section 4.10), and the **next action** is one action with an owner and a due date, plus a revisit date. Neither contains a quantity or an order date, for the reasons in section 3.6.

All figures below are the prototype's actual computed output with `DEMO_TODAY=2026-10-03` in replay mode (no model key); the new item is **[DEMODATA]**. The click path is in `DEMO.md`.

1. **New data.** The planner clicks the demonstration item (or pastes text): "[DEMODATA] Fingrid reports that the planned total capacity of data centre projects with signed connection agreements rose to 3.6 GW by the end of September 2026, up from just over 3 GW at the end of June … Fingrid repeats that connection capacity in Southern Finland remains the limiting factor and that the government's proposed connection priority rules are still under consultation." Dated 2026-10-01.
2. **Collector** normalises it: id RAW-3d0cf06757, date 2026-10-01, label DEMODATA, source stored.
3. **Signal detection.** The demand agent recognises a new observation of SIG-001, quotes the sentence, sets direction +1, strength 0.85, classification structural ("the committed pipeline is growing even as speculative applications are discouraged"), lead 30 months, and appends 3.6 GW to the card's history. In this environment the output is replayed (no model key), and the trace says so: `Demand signal agent [replay/degraded]`.
4. **Source and counter-evidence review.** The counter-evidence agent links two cards, CE-037 (the same release says southern capacity is the limit, so signed agreements may not be energised on schedule; B, strength 0.3 [DEMODATA]) and CE-038 (GW is not relay count: relays scale with feeders, not MW [ASSUMPTION, C, 0.2]). SIG-001 now has five counter-cards; its counter-evidence attack rises from 0.72 to 0.79 (noisy-OR), so its credibility falls from 0.28 to 0.21, while its freshness rises from 0.66 to 0.99 and its strength from 0.80 to 0.85. The weight moves from **0.15 to 0.17**: a fresher, stronger observation gains weight, but the attached doubts keep the gain small. After the import the weight band is 0.17 to 0.76 and 90% of the discount from 1.0 is credibility, which is the planner's cue to read the counter-cards. The two new counter-cards also appear in the negative list (38 to 40 entries), and SIG-001 is the one change in the changes column (up 0.02).
5. **Demand quality.** The bullwhip agent reports *mixed, turning*: amplification 1.35 and double-ordering 0.22 still elevated [DEMODATA inputs], memory price increments shrinking two quarters in a row [SOURCE] and the spot premium down to 6% from 28% [DEMODATA] already fading, push-out rate not connected.
6. **Scenario update.** Probabilities before → after: "Growth continues, components stay scarce" 49.8% → 49.7% (−0.1 pp), "Investment concentrates in the Nordics" 36.7% → 36.9% (+0.2 pp), "Growth continues, components become easier to get" 10.1% → 10.1%, "Projects slip, components stay scarce" 3.4% → 3.3%. Uncertainty 0.766 → 0.765. One quarterly data point moves the picture by a fraction of a point, and moves the Nordic scenario most because SIG-001 loads on the Nordic theme more strongly (relevance +0.61) than on the leader (+0.40). Each scenario row says which signal moved it and why, for example: "[SIG-001] FI signed DC connection agreements raised its log-odds by 0.022 (weight 0.15 to 0.17); the card supports this scenario (relevance +0.61). It loads on the Nordic share, which this scenario shares."
7. **Recommended move.** The leading scenario is still "Growth continues, components stay scarce" at 50%, runner-up "Investment concentrates in the Nordics" at 37%, confidence **medium** (margin 0.13, entropy 0.76). The headline reads: prepare a second-source qualification for memory-dependent relay boards so the next commitment window can be extended if the tight-supply reading holds. Four moves follow (two no-regret, two contingent; section 4.10), each with trigger signals and the cost if wrong, and a hedge for the case where the Nordic scenario overtakes. The move did not change: the recommendation is stable against one data point, which is the intent. The conditional reading of the scenario is shown with it, for example: "If 'Growth continues, components stay scarce' holds, the committed Finnish pipeline would convert into substation projects through 2027–2028 while memory and microcontroller supply remains on allocation … the component orders placed 18 months ahead would be the binding constraint, and under-ordering would be the main exposure." For "Projects slip, components stay scarce": "… frame orders from switchgear factories would be rescheduled 6–12 months before public data shows it." The guardrail scans every model-written text; nothing is phrased as an instruction.
8. **Next action.** Put the second-source qualification of memory-dependent relay boards on the agenda of the next S&OP review and agree which signals decide whether the commitment window is extended. Owner: component procurement lead with the S&OP owner. Due 2026-10-17, revisit 2026-10-31 [ASSUMPTION: two weeks and the monthly S&OP cycle]. Alongside it, the next analysis step from the explainer lists what to watch, from the largest contributions and their freshness: SIG-003 (Google programme, freshness 0.83), SIG-023 (big-tech commitments, 0.84), SIG-007 (TrendForce, 0.98), SIG-018 (Micron, 0.98) and SIG-024 (atNorth, 0.87), to be reviewed with the S&OP owner, the component procurement lead and the data-centre segment manager. Open questions logged for the planner: which cards they dispute, and whether SIG-017 (frame coverage) agrees with the public signals once connected.
9. **The planner** opens SIG-001, reads the five counter-cards and the attribution, and disputes the card with a reason (for example, that GW does not map to relays in their product mix). The weight halves from 0.17 to 0.09, the probabilities become 50.0%, 36.2%, 10.2% and 3.6%, the dispute is logged with name and reason, and the recommended move stays the same at medium confidence. The decision on what the picture means for the next component commitment, and in what quantity and when, is theirs and is taken in the S&OP meeting, not in the tool.

### 5.3 Technical scoping for 48 hours: what is real, what is pre-recorded, and why that is honest

**Built and running:** the signal and counter-evidence data model; the ensemble weight (credibility with corroboration, currency, materiality, human view) with its clamp, band, attribution and per-horizon fit; the scenario update with contributions and entropy, at the headline and at 12, 24 and 36 months; the code-generated recommended move, hedge and next action; signal changes since the last cycle and the negative list; the five bullwhip metrics; the eight-agent orchestration with trace, failure modes and the guardrail that strips purchase, quantity and order-timing language from model text; the Claude SDK integration with structured outputs; the full UI with filters (including a region filter that filters the cards), object pages, charts and annotations; the API; 83 tests.

**Preview only:** the segment filter (data centres, energy clusters, utility grids, renewable generation, industry, e-mobility, hydrogen, buildings) on the overview and Signals pages changes its label but not the data; it shows where filtering by segment will sit once the portfolio covers more than data centres (30 of the 37 cards are tagged data centre, 5 components, 1 materials and 1 utility). The region filter is real: every card carries a region (Finland, Nordics, EU, US, global).

**Built and tested but dormant on today's data:** the corroboration estimator (no card carries a list of independent sources yet) and the z-score materiality estimator (no card has a SOURCE-labelled history long enough). With them dormant, every weight equals what the single-source formula gives, and a test checks that. They switch on when the scout or a human adds a second independent source, or when licensed series arrive.

**Pre-recorded or demo:** the LLM outputs for the demo item (classification, counter-evidence, interpretation, brief) are replayed when no API key is present, and labelled "replay" in the trace; pasted items fall back to a keyword heuristic that forces reliability C and flags the card for review. The recommended move is not pre-recorded: it is composed live by code from templates, so it works without a key. Time series behind sparklines are DEMODATA except the sourced anchor points. Bullwhip inputs for BW-1, BW-3 and BW-4 are DEMODATA; BW-5 is not connected. The probability history before today is DEMODATA.

**Why this is the honest cut:** the value of the system is the evidence discipline (sources, counter-evidence, labelled provenance, traceable arithmetic), and that part is fully built and tested. The parts that need licences (TrendForce series, LME real-time, Nord Pool granular) or ABB data (order history) are shown as labelled placeholders rather than invented series. Every replayed output is visibly marked, so the jury sees exactly which boxes a live model would fill.

---

## 6. Pitch (7 minutes)

A 3-minute demo script ordered by judging weight, a 30-second version and the likely judge questions are in `DEMO.md`.

| Minute | Content | Criterion |
|---|---|---|
| 0:00–0:30 | Hook (below) | Problem definition |
| 0:30–1:30 | The user and the gap: 18-month component orders, 10-week order book, "the best forecast was history" stopped working; both misreadings and their cost | Problem definition 15% |
| 1:30–3:00 | The chain and the mechanism: seven links with lead times; structural vs cyclical; the bullwhip in this chain with 2021–2023 as the order of events; regional timing differences (Fingrid vs FLAP-D vs US) | Market understanding 20% |
| 3:00–4:00 | The evidence: 37 cards, what each measures, reliability, freshness, lead time and horizon fit, counter-evidence on every strong one, seven cards that point the other way; the five bullwhip metrics; copper's real role; where ABB's SAP data plugs in | Data and signal chain 15% |
| 4:00–5:30 | Live demo: import the Fingrid item, watch the agents, see the weight and the probabilities move by a fraction, open the card and its attribution, read the recommended move and the next action, dispute a card and see the move hold; formulas on screen | AI solution logic 20%, prototype 10% |
| 5:30–6:30 | What it changes for ABB: the component commitment window, allocation, price indexation, S&OP escalation; the recommended move and why it is conditional and qualitative (one sentence) | Business value 20% |
| 6:30–7:00 | Close (below) | — |

**Opening hook (30 seconds).** "In early 2025, ABB's relay team had to decide the chips for mid-2026. Demand doubled; they could not see it, and they missed the order. Today they are placing orders for deliveries at the end of 2028, and their most reliable information is an order book that shows the next ten weeks. Eighteen months of blindness against ten weeks of sight. We built the instrument that looks eighteen months ahead, tells you how much to doubt it, and proposes what to prepare."

**One sentence on why the recommendation is conditional and has no quantities, and why that is strength.** "The order book lags the market by eighteen months and the data we can see is the market, not ABB's contracts, cash and customer promises, so a quantity from open data would be false authority; we recommend what to prepare, review and watch, the signals that would change it and what it costs if we are wrong, and leave the quantity and the date with the person who holds the other half."

**Closing line.** "The best forecast used to be history. We give ABB the next best thing: the earliest evidence, with its doubts attached, two years before the order book knows."

### 6.1 Nine hardest jury questions

1. **How do you validate that a signal leads ABB's demand?** Each card states its lead-month assumption. Validation is a back-test against ABB's own order history: lag correlation between the card series and relay order intake by segment. The prototype is built so the test is one export away (SIG-017 and BW-5 fields). Until then the lead months are labelled assumptions, and the list of questions for ABB at the end of this document asks for the two facts that calibrate them.
2. **What if the LLM hallucinates?** It cannot hallucinate a number into the arithmetic: the model only quotes a source sentence and assigns grades; every weight and probability is computed by tested code from stored fields. A card with a mis-quoted excerpt is visible on the object page next to its source link, and a dispute halves it. Structured outputs enforce the schema; the guardrail removes recommendation language.
3. **Why no quantities? Isn't the work half done?** The recommendation is there: a leading scenario with its confidence, three to four conditional moves per decision area with trigger signals, cost if wrong and horizon, a hedge, and a next action with an owner and a due date. The half we do not give is the half the data cannot see: quantities and order dates depend on frame contracts, allocations and cash, which are not in open data, and the order book that would show them lags the market by 18 months or more. The challenge text says "support human decision-making" and ABB asked for "insight and scenarios", "never black and white".
4. **How does this integrate with ABB's systems?** The cards are a flat schema; SAP exports (purchasing documents, sales schedule lines, change logs) become cards with reliability A through the same collector. The interface is a static single-page application that can be embedded in an intranet portal or an S/4HANA launchpad tile. Nothing in the engine changes when internal data arrives.
5. **Why not do this in Excel?** Excel can hold the weights. It cannot read 40 sources a week, quote the supporting sentence, search for the counter-case on every strong card, and keep an audit trail of who disputed what. The arithmetic is deliberately simple enough for Excel so that the planner can check it; the reading and challenging is the part Excel does not do.
6. **Your probabilities are not calibrated.** Correct, and the method page says so: the update is a traceable log-odds accumulation with analyst-set relevance, not a measured posterior. Calibration needs outcomes; the annotation log and the probability history are the data for it. Today the value is that every point of probability can be opened to its sources.
7. **Most of your time series are demo data.** Yes, and each is labelled. The sourced anchor points are real and dated; the licences for the full series (TrendForce, LME, Nord Pool) are listed. The system is designed so that replacing a DEMODATA series changes nothing except the label.
8. **The scenarios look obvious; what is new?** The scenarios are deliberately plain so that the evidence is the product. What is new is the mandatory counter-evidence per signal, the bullwhip metrics separating hoarding from demand, the lead-time accounting per card that re-ranks the scenarios at 12, 24 and 36 months, and the fact that one new data point moves the picture by a fraction of a point with the reason on screen.
9. **Is the recommendation just a template?** It is assembled from templates, and says so: every template and threshold is labelled ASSUMPTION. What is computed is which template applies (the leading scenario), the confidence (margin and entropy), the trigger signals (matched to real cards by their fields and ranked by computed weight) and the dates. Writing it in code, not with a model, is the point: it can be tested, it cannot invent a quantity, and it is the same in replay mode as with a key. The templates are what ABB's planners should rewrite first; the engine does not change when they do.

---

## Self-assessment against the criteria (1–5)

Scored by us, against the weights in the brief. The scale is whole numbers; no criterion gets a 5 because each has a gap named in its reason.

| Criterion | Score | One-sentence reason |
|---|---|---|
| Business value and connection to ABB decisions (20%) | 4 | The decisions are named, tied to the 18-month window and the 12, 24 and 36 month horizons, and the chain now ends in a recommended move and a next action with owner and date; the move is qualitative by design, the templates are our assumptions, and the lead-time links are unvalidated against ABB order data. |
| Understanding of the market and the phenomenon (20%) | 4 | Chain, bullwhip, regional timing and the 2026-vs-2021 differences are argued with dated sources, and seven negative-direction cards balance the growth evidence; US delay figures rely on C-grade sources. |
| Quality of data sources and signal chain (15%) | 4 | 35 sourced public cards with access, reliability, lead time and restrictions, five bullwhip metrics, a changes column and a negative list; three metrics and most time series run on DEMODATA, and BW-5 and SIG-017 need ABB's data. |
| Quality of problem definition (15%) | 4 | User, rhythm, gap, change to detect, lead time and both misreadings are explicit, and the recommendation names its trigger and its cost if wrong; the user persona is inferred, not interviewed. |
| Logic and clarity of the AI solution (20%) | 4 | The ensemble weight, horizon fit, scenario update and recommendation step are explicit, labelled and covered by 83 tests, and every weight can be opened to its factors; relevance values and priors are hand-set, and the corroboration and z-score estimators are dormant on today's cards. |
| Prototype functionality and modern presentation (10%) | 4 | The whole minimum chain runs in replay mode with no key, with a 70/30 overview, horizon view, changes, negative list and attribution; LLM steps are replayed without a key, the segment filter is a preview and the daily history before today is simulated. |

**Weakest points.** (1) Lead-month assumptions per link are unvalidated; a back-test against ABB order intake is the single most valuable next step. (2) Scenario relevance values and priors are analyst-set; the probabilities are traceable, not calibrated, and the 24 and 36 month rankings change with the kernel width. (3) Three of five bullwhip metrics and most time series run on DEMODATA; the method is real, the inputs are placeholders until licences and ABB exports arrive. (4) The recommendation templates, the confidence thresholds and the due and revisit days are assumptions that no ABB planner has reviewed.

## Claims to verify with ABB, and what to ask

| Claim in this document | Question for ABB |
|---|---|
| Relays are specified at the switchgear tender, 6–12 months before the ABB order, and 12–18 months before energisation | At what project phase is the relay type and quantity fixed, and how long after that does the order reach you? |
| A signed transmission connection agreement precedes energisation by 2–4 years | Which TSO or customer milestone has historically been the first reliable predictor of your order intake? |
| The same end project is forecast by several bidding units, including several ABB units | How are inter-company forecasts consolidated, and do you see duplicated demand for the same substation? |
| Relay count scales with feeders, not MW | Roughly how many relays does a typical data-centre MV substation take, and does that differ from a utility substation? |
| The 18-month component order is placed with a safety margin to secure allocation | How is the order quantity set today, and has it ever been cut after placement? |
| Frame purchase orders carry price risk and are indications only | What share of frame-order quantity has historically been called off, and with what timing slippage? |
| Memory is the critical path; MCUs secondary | Which three part families gate your output today, and which suppliers confirm lead times above 40 weeks? |
| Internal data lives in SAP purchasing and sales documents with change logs | Which system holds order change history, and can a monthly export be provided for a back-test? |
| Copper matters more as a cost-side risk than as a leading indicator for relays | Which of your products or offers are copper-indexed, and do you watch copper for demand or for price? |
| Priors for the nine candidate situations: 0.18 for "Growth continues, components stay scarce", 0.12 for three, 0.09 for five | Does the current state feel like "Growth continues, components stay scarce", and which situation do you fear most? |
| The recommended moves per decision area (second-source qualification, protected assembly slots, a sharing rule between internal and external customers, written allocation status) are the right preparatory moves | Which of these would your planners already do, which are missing, and which would they never consider? |
| Confidence from the margin to the runner-up and the entropy; next action due in two weeks, revisit in four | What thresholds and what cadence match your monthly S&OP cycle? |
| The horizon kernel width (the median high-to-low ratio of the lead-time ranges is 2) | How wide is the real spread between a signal and the order it leads to, for the two or three signals you trust most? |

## Final check

The document and the prototype were reviewed for any quantity or order instruction. Sentences of the form "ABB should order", "increase stock", "buy now" do not appear; the recommended moves are conditional and qualitative ("prepare", "agree", "identify", "if this holds, …"), the next action names an owner and a due date, the interpretation texts are conditional, and the code guardrail (`agents/llm.py`, `recommendation_filter`) removes such sentences from any generated text, with a test covering it.
