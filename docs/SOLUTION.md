# Irma — from weak signals to scenarios for ABB Distribution Solutions

Segment: **data centres**. Region: **Nordics + Europe**, with the US as comparison. Horizon: **12–36 months**. Prototype: `app/` (Irma: a market-terminal style interface in ABB red and white on a deterministic engine with eight agents, scheduled updates, notifications, signal tracking and a cited assistant). This document covers the six challenge areas, scores itself, and lists what must be verified with ABB.

**Labelling convention used throughout.** Every number is one of: **[SOURCE]** named public source with date (the signal cards carry the URL), **[DEMODATA]** illustrative value in the prototype, or **[ASSUMPTION: reason]** (Finnish brief: OLETUS). Statements from ABB Distribution Solutions are marked **[ABB]**. Unlabelled numbers do not appear.

## What this system is, and what it is not

**It is** an AI system that follows weak signals from open sources about data-centre end demand and about the component supply that limits ABB's protection-relay output, and keeps four alternative scenarios of how the market can develop. Every scenario is argued, traceable to sources, and shown with evidence for and against.

**It is not** a purchasing system, a recommendation engine or a sales forecast. It gives no quantities, no order points and no "order now". It does not claim to know which scenario will happen.

**Why the boundary is deliberate.** A purchasing decision at ABB depends on frame contracts, supplier allocation agreements, cash position, internal priorities between ABB units and customer promises. None of that is visible in open data. A recommendation computed from the market half of the picture would carry false authority into a decision owned by the person holding the other half. The system therefore delivers the market half earlier and more completely than the order book can, and leaves the judgement where the missing information sits. **The human is the interpreter and the decision-maker; this is written into every view of the prototype.**

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

The system does not answer these questions; it changes the evidence available when ABB answers them.

- **Component commitment timing and size** (18-month orders placed now for 2028 delivery [ABB]): which scenario is the order being placed into, and what evidence would change that view before the next order window.
- **Allocation between internal switchgear factories and external customers** when demand exceeds supply [ABB]: which segment's demand is structural and which is amplified.
- **Capacity investment in assembly and test**: only relevant in scenarios where the component constraint loosens while demand continues (scenario B).
- **Price and timing risk in frame orders** (new to the unit [ABB]): copper and memory price scenarios attached to delivery dates a year out, as another ABB business already does with copper indexation [ABB].
- **When to escalate to S&OP**: the system's "next analysis step" names the signal, the date and the people, which is an analysis action, not a purchase action.

---

## 2. Data & signal portfolio

### 2.1 Signal table (32 cards in the current world situation; 31 public, 1 internal placeholder; SIG-018 to SIG-025 from the news of 21 September to 3 October 2026, SIG-026 to SIG-032 from research institutions with Koomey and GridLab's 2026 forecast critique as counter-evidence)

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
| BW-2 Memory price momentum | Second difference of QoQ contract price increments | Increment shrinking two quarters in a row while still positive = pre-peak | −10 pp, hoarding ending [SOURCE: TrendForce 1Q–3Q26] |
| BW-3 Double-ordering index | Lead times and distributor inventory days rising together | Both > +15% | 0.22, hoarding risk **[DEMODATA inventory input]** |
| BW-4 Spot-to-contract spread | Spot premium over contract DRAM | Premium collapsing while lead times still long = hoarding ending | 6% from 28% peak, hoarding ending **[DEMODATA]** |
| BW-5 Push-out / cancellation rate | Share of frame-order quantity rescheduled out or cancelled in 90 days | ≥ 10% | not connected (ABB SAP schedule-line history) |

Combined reading in the prototype: **mixed, turning**: hoarding indicators elevated, two urgency measures already fading, structural end-demand signals intact. This is ABB' braking signal, expressed as five numbers with their inputs labelled.

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

The user is the **component procurement lead or S&OP planner** at ABB Distribution Solutions who prepares the 18-month component commitments and the demand review. Rhythm: a monthly S&OP cycle, a quarterly commitment window for critical components, and ad-hoc checks when a supplier changes allocation. They read the scenarios and the evidence, decide which cards they trust, and bring the picture into the S&OP meeting. The system records their confirmations and disputes and shows the effect on weights; it does not act on them beyond that.

### 3.2 What they cannot see today

Their information source is the order book and customers' frame orders, which are indications, not commitments, and carry price risk [ABB]. "The best forecast has been history" worked while the business was flat [ABB]. The order book turns 18–30 months after the market event that drives it (section 1.1), which is after the component window. Internal forecasts can also double-count the same project through several bidding units [ASSUMPTION]. The planner is therefore deciding 2028 component volumes with 2026 order data and no view of the hoarding component inside it.

### 3.3 The change that must be detected

- **Turning point**: end demand stops accelerating while orders still rise (bullwhip peak).
- **Acceleration**: signed connection agreements and capex guidance rise together, as in 2026.
- **Deceleration**: capex guidance cut, connection agreements stall, spot premiums collapse.
- **Regional shift**: demand moving from FLAP-D to the Nordics, or from Finland to Sweden/Norway if Finnish queue rules change.

### 3.4 Required lead time

Critical components are ordered 18 months ahead [ABB]. A signal that is only visible at the switchgear tender (6–12 months before the ABB order) arrives 24–30 months after the component decision it should have informed. The picture must therefore reach **at least 24 months** [ABB], which is why the portfolio is weighted toward links 1–3 of the chain (capex, land, connection agreements) and why every card states its lead-month assumption. The prototype shows the maximum horizon covered (48 months, from the IEA card) and how many cards reach 18 months or more (11 of 17).

### 3.5 Misreading the signal, in both directions

- **False acceleration** (reading hoarding as demand): ABB places ten-fold component orders that are never consumed [ABB's own risk statement]. Cost: inventory at peak prices, write-downs, and cash tied up while the price falls (scenario D).
- **False deceleration** (reading a timing air pocket as a turn): ABB under-orders, delivery times stretch past 10 weeks, allocation disputes with internal customers, lost structural growth (scenario A).

How the system protects against false certainty:

1. **Uncertainty is displayed**, not hidden: four probabilities and their entropy (0.76 today, where 1.0 is "no idea").
2. **Counter-evidence is mandatory**: every strong signal is challenged by an agent whose only job is to find the opposite case; an unchallenged card is capped at weight 0.6.
3. **Scenarios are parallel**: the least likely scenario (D, 5%) is shown with the same detail as the leading one, including the early signs that would raise it.
4. **Data provenance is on every number**: SOURCE, DEMODATA or ASSUMPTION, with date and URL.
5. **The human can dispute**: a dispute halves the weight and is logged with a name and reason; the next reader sees it.

### 3.6 Why the system gives no recommendations

The information that decides a purchase (contracts, allocation agreements, cash, internal priorities, customer relationships ABB chooses to protect [ABB]) is not in open data and often not in any system. A recommendation would present a half-informed computation as an answer. ABB asked for insight and possible scenarios on which ABB can think its own decisions through, "never black and white" [ABB]. The boundary is enforced in code: no agent has a recommendation role, and a deterministic guardrail removes purchase language from any generated text.

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
| 6 | Scenario agent | Recomputes weights and the four scenario probabilities and records the change. | All cards and evidence | Probabilities, contributions per signal, entropy, deltas | Pure code; if inputs are missing the previous state is kept and marked stale |
| 7 | Interpretation agent | Writes what each scenario would mean for ABB demand, delivery capability and component need, in conditional form. | Scenario state, new card | Conditional text per scenario | Falls back to the scenario's stored interpretation plus the computed contribution; guardrail strips any recommendation language |
| 8 | Explainer agent | Writes the cited situation brief and answers questions about the evidence. | Scenario state, bullwhip reading, cards | Brief with [SIG-xxx] citations; next analysis step (watch list, re-evaluation date, reviewers) | Falls back to a template brief composed from computed numbers; retrieval-based answers with citations |

No agent recommends. The "next analysis step" is built by code from the largest contributions and their freshness; it names signals, a date and reviewers.

Model and SDK: Claude via the Anthropic SDK (`claude-opus-5-5` by default), structured outputs for card drafts (`messages.parse` with a Pydantic schema), server-side refusal fallback enabled for free-text calls. Without credentials the agents run in replay/heuristic mode and say so in every trace step.

### 4.3 Signal card data model

| Field | Meaning | Who sets it |
|---|---|---|
| `id`, `name`, `short` | Identity | Collector |
| `source {name, url, access, date}` | Provenance; URL opens from the card | Collector |
| `observed_at` | Date of the observation (drives freshness) | Collector |
| `direction` (+1 / 0 / −1) | Toward demand acceleration or supply tightness, or the opposite | Classifier (LLM or human) |
| `strength` (0–1) | Size of the move relative to the signal's own history | Classifier; later computed from history by code |
| `reliability` (A/B/C) | Source grade | Classifier, overridable by human |
| `freshness` (0–1) | 0.5^(age/half-life), half-life by update frequency | Code |
| `lead_months` + rationale | How far ahead of the ABB order the signal is visible | Classifier, assumption stated |
| `classification` (structural/cyclical/mixed) + rationale | Section 1.2 rule | Classifier |
| `measures` (end_demand / supply_tightness / intermediary / price / policy) | What the signal actually measures | Classifier |
| `value {number, unit, label}`, `excerpt` | The quoted fact and the sentence it comes from | Classifier copies; never computes |
| `history[]` + `history_label` | Series for sparkline, labelled SOURCE/DEMODATA | Collector |
| `scenario_links {A,B,C,D}` ∈ [−1, 1] | Oriented relevance to each scenario | Classifier; visible and disputable |
| `counter_evidence[]`, `ce_searched` | Linked counter-evidence cards; whether the search ran | Counter-evidence agent |
| `annotations[]` | confirm / dispute / comment with author, time, note | Human |
| `data_label` | SOURCE / DEMODATA / ASSUMPTION | Collector |
| `computed {weight, components}` | The formula result, shown with its factors | Code |

### 4.4 Weight and probability update, as formulas

Signal weight (code, `engine/weights.py`):

```
w_i = R_i × F_i × S_i × (1 − C_i) × H_i

R  reliability   A = 1.0, B = 0.7, C = 0.4
F  freshness     0.5^(age_days / half_life), half-life: daily 14 d, weekly 30, monthly 60, quarterly 120, annual 240, event 90
S  strength      0..1 from the card
C  counter-evidence penalty = min(0.8, 1 − Π_ce (1 − R_ce × strength_ce))   (noisy-OR: duplicate counter-claims do not stack)
H  human factor  Π annotation multipliers (confirm 1.2, dispute 0.5), clamped to [0.25, 1.5]
Unchallenged cards (no counter-evidence search): w_i = min(w_i, 0.6)
```

Scenario probability (code, `engine/scenarios.py`):

```
L_s = ln(prior_s) + k × Σ_i w_i × r_{i,s}        r_{i,s} ∈ [−1, 1] from the card, k = 1.0 [ASSUMPTION]
p_s = exp(L_s) / Σ_t exp(L_t)
uncertainty = −Σ p_s ln p_s / ln 4                 (0 = certain, 1 = uniform)
```

Worked example from the prototype (2026-10-03): SIG-003 (Google programme) has R 1.0, F 0.83 (24 days old, event half-life 90 d), S 0.9, C 0.21 (one B-grade counter-card at 0.3), H 1.0 → w = 0.59. With r = +0.6 for scenario A its contribution is +0.35 to A's log-odds and −0.30 to D's. Across all 17 cards the result is A 60%, B 23%, C 12%, D 5%, uncertainty 0.76. The choice k = 1.0 means one fresh A-grade card at full strength and relevance 0.6 multiplies a scenario's odds by about 1.8; no single source can settle the picture. The update is traceable, not a calibrated posterior: r is an analyst-set direction, shown on the card, and that is the honest description.

### 4.5 Scenario generation: the four most likely situations per run

The scenarios shown are not fixed. A pool of nine candidate situations (archetypes) is kept in `scenario_archetypes.json`, each with a profile on six axes (demand, supply, policy, price, Nordic shift, bullwhip), a prior, bilingual texts (name, narrative, confirming signposts, refuting indications, conditional implications for ABB) and an illustrative path. Every signal card carries loadings on the same six axes. On each update cycle:

```
r_is  = Σ_a axes_ia × profile_sa / Σ_a |profile_sa|           relevance of signal i to candidate s, in [−1, 1]
L_s   = ln(prior_s) + k × Σ_i w_i × r_is                      k = 1.5 [ASSUMPTION]
shown = the four candidates with the highest L_s;  p_s = softmax over the four
```

With the October 2026 data (the current world situation) the four shown are "Growth continues, components stay scarce" (42%), "Investment concentrates in the Nordics" (32%), "Growth continues, components become easier to get" (17%) and "Projects slip, components stay scarce" (9%). With the constructed downturn dataset (world situation 2) the selection changes to "Investment slows down, stock piles up" (39%), "Double orders unwind, stock is released" (35%), "Grid upgrades carry demand while data centres pause" (16%) and "Grid rules delay data centres" (11%). A language model, when connected, rewrites the texts; the selection and the probabilities are always computed by code, and the full candidate ranking is visible in the method page.

**Scenario paths (1, 2 and 3 years).** Each candidate carries yearly growth parameters for two indices, demand and deliverable supply (100 = today), from which the interface draws a 36-month path with a widening band. The path depicts the scenario; it is labelled as an assumption and is not a forecast.

**Plain-language summary.** The first element on the page is a three-sentence summary composed from the axis scores and the leading scenario (demand growing, flat or falling; chips and memory hard or easier to get; the most likely path with its probability; the two signals to watch), in English and Finnish.

**Two mock worlds.** A small switch loads either the public October 2026 dataset (the current world situation) or a constructed stress dataset labelled DEMODATA throughout (world situation 2: investment cuts, cancellations, falling memory and copper prices, easing lead times, Finnish priority rules adopted). The switch exists to show how the selection, the summary, the notifications and the assistant react to a different world.

### 4.6 The human's role

The user **marks** cards as confirmed or disputed (weight ×1.2 or ×0.5, logged with name, time and reason), **comments** without changing weight, and **contests** classifications and lead-month assumptions (a comment on the card; a change of the field is an edit with the same log). Disputes are visible to every later reader, so the evidence base carries institutional memory rather than one analyst's opinion. The system uses the annotations only through the H factor; it never suppresses a card or hides a scenario because of them. Over time, confirmations and disputes against realised outcomes become the data for calibrating r and the reliability grades, which is the first step from a traceable update toward a measured one.

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
- **Limits and settings.** Search and fetch are restricted to an allowlist of 51 domains (29 of them graded A), editable in Settings together with the number of searches (default 3) and page fetches (default 2) per agent call. Fetched pages are capped at 8,000 tokens. A paused server turn is resumed at most twice.
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

---

## 5. Demonstrable prototype

Location: `app/`. Backend: FastAPI with a deterministic engine, eight agents, a scheduled update cycle (hourly by default, configurable), persisted settings, notifications and daily probability history (`python3 -m uvicorn main:app`). Front end: minimal single-page application named Irma. Tests: `pytest` on weights, scenario update, bullwhip metrics, guardrail, the replayed pipeline run and the API (13 tests).

### 5.1 Views (Irma)

The interface follows the layout of a market terminal: a signal list on the left, the scenario in focus in the centre, and an assistant on the right. ABB red and white, black top bar with the IRMA logo.

| View | What is shown | What the user does | Question it answers |
|---|---|---|---|
| **Overview** | First: the plain-language summary of the current situation, with the world-situation switch. Then the four most likely situations: one large chart of the selected situation on the left (projection of demand and deliverable supply for 1, 2 or 3 years, or the daily probability history) and three smaller charts below it that swap into the large one when clicked; under them the selected situation's narrative, the signals and sources used, confirming and refuting indications and the conditional implications for ABB. Left: the signal list. Right: the Irma assistant with three suggested prompts and a chat bar. A FI/EN switch is in the top bar. | Switches situations, changes the horizon, switches world, asks the assistant | What is the situation in plain words, what are the four most likely paths, and what evidence is behind each? |
| **Signals** | Strong signals and weak signals as two bullet lists, filtered by source class (contracts and commitments, component and commodity prices, market news, policy and institutional) and by the top-bar search. Each bullet states where the value is calculated from: source, date, reliability, freshness, strength, counter-evidence count and weight. A lock on each signal starts close tracking. "Import data" opens the import page. | Filters, searches, opens a signal, locks it, imports data | Which evidence carries the picture, and which early indications deserve attention? |
| **Signal** | Observed value and history, weight, source quote and link, and collapsed sections: classification rationale, weight calculation, counter-evidence, contribution to scenarios, assessment (confirm / dispute / comment) | Checks the source, disputes or confirms, locks | Where does this come from and what speaks against it? |
| **Scenarios** | Ranking of the four scenarios with probabilities and daily change; the selected scenario in detail: narrative, confirming signposts, refuting indications, implications for ABB (conditional), evidence for and against; the daily probability chart; the demand-quality check | Switches between scenarios; opens evidence; follows a cited signal | How could the market develop and what would each path mean for ABB? |
| **Import data** | New item (demonstration or pasted text), the resulting probability changes, next analysis step, situation brief, implications by scenario, and the processing steps behind a disclosure | Runs the chain on new data | What happens when new information arrives, and why did the picture move? |
| **Notifications** | Major signals, large daily changes, changes of the most likely scenario, moves in tracked or price signals | Reads, opens the related signal or scenario, marks as read | What needs attention since I last looked? |
| **Settings** | Update frequency (15 minutes to once a day), thresholds for large changes, major signals and price moves, the strong-signal threshold, run-now and reset, and the method (formulas, agents, data labels, sources) behind disclosures | Adjusts cadence and thresholds; audits the method | How often does it run, and what counts as a large change for me? |

**The assistant.** The three suggested prompts are answered from the computed state with citations: the summary from scenario deltas, the newest evidence and open notifications; the procurement question with the next analysis step (signals to follow, re-evaluation date, reviewers) and the conditional component reading of the leading scenario, prefaced by the statement that Irma does not recommend quantities or timing; the component question from the supply-side cards and the five demand-quality indicators. With a model key the same composed context is passed to the model; the recommendation guardrail runs on every answer.

Daily and weekly readers get the same overview: the chart's 7-day and 30-day ranges show what moved since their last visit, and the notification list keeps what crossed a threshold.

### 5.2 Walkthrough: new data → signal detection → source and counter-evidence review → scenario → what this means for ABB → next action

The challenge's chain ends in "decision recommendation for ABB → next action". This solution reads those two links as: **"what this means for ABB" = conditional impact statement, not a purchase instruction**, and **"next action" = analysis action: which signal to watch, when to re-evaluate, with whom to review**. Both are rendered exactly that way in the prototype.

All figures below are the prototype's actual computed output with `DEMO_TODAY=2026-10-03`; the new item is **[DEMODATA]**.

1. **New data.** The planner pastes (or clicks the demo item): "[DEMODATA] Fingrid Q3 2026 interim: signed data-centre connection agreements rose to 3.6 GW by end of September, up from just over 3 GW in June; southern connection capacity remains the limiting factor; priority rules still under consultation." Dated 2026-10-01.
2. **Collector** normalises it: id RAW-3d0cf06757, date 2026-10-01, label DEMODATA, source stored.
3. **Signal detection.** The demand agent recognises a new observation of SIG-001, quotes the sentence, sets direction +1, strength 0.85, classification structural ("committed pipeline growing while speculative applications are discouraged"), lead 30 months, and appends 3.6 GW to the card's history. In this environment the output is replayed (no model key), and the trace says so: `Demand signal agent [replay/degraded]`.
4. **Source and counter-evidence review.** The counter-evidence agent links two cards: (a) southern connection capacity and the proposed priority rules could delay energisation of what was signed (B, strength 0.3 [DEMODATA]); (b) GW is not relay count: a few large campuses add 0.6 GW with a handful of MV substations, and relays scale with feeders [ASSUMPTION, C, 0.2]. SIG-001 now has four counter-cards; its penalty is 0.66 (noisy-OR), its freshness 0.99, and its weight moves from 0.25 to 0.29. A fresher, stronger observation gains weight, but the attached doubts keep the gain modest.
5. **Demand quality.** The bullwhip agent reports *mixed, turning*: amplification 1.35 and double-ordering 0.22 still elevated [DEMODATA inputs], memory momentum −10 pp and spot spread 6% already fading [SOURCE / DEMODATA], push-out rate not connected.
6. **Scenario.** Probabilities before → after: A 59.8% → 60.2% (+0.4 pp), B 23.2% → 23.4%, C 11.8% → 11.4%, D 5.3% → 5.1%. Uncertainty 0.76 → 0.75. One quarterly data point moves the picture a fraction of a point; the trace shows exactly which contribution did it.
7. **What this means for ABB (conditional).** Per scenario, e.g. for A: "If 'Sustained expansion, constrained supply' holds, the committed Finnish pipeline would be converting into substation projects through 2027–2028 while memory and MCU supply stays on allocation … the component orders placed 18 months ahead would be the binding constraint." For C: "… frame orders would be pushed out 6–12 months before public data shows it." The guardrail scans the text; nothing is phrased as an instruction.
8. **Next analysis step.** Watch list from the largest contributions: SIG-003 (Google programme, freshness 0.83), SIG-001 (now 0.99), SIG-007 (TrendForce, 0.61), SIG-010 (copper, 0.95), SIG-004 (capex guidance, freshness 0.26, flagged below 0.5). Re-evaluate on 2026-10-31 [ASSUMPTION: monthly cadence; next TrendForce quarterly release and hyperscaler Q3 earnings fall inside the window]. Review with the S&OP owner, the component procurement lead and the data-centre segment manager. Open questions logged for the planner: which cards they dispute, and whether SIG-017 (frame coverage) agrees with the public signals once connected.
9. **The planner** opens SIG-001, reads the four counter-cards, disputes card (b) as irrelevant for their product mix with a reason, and the weight is recomputed and logged. The decision on what the picture means for the next component commitment is theirs and is taken in the S&OP meeting, not in the tool.

### 5.3 Technical scoping for 48 hours: what is real, what is pre-recorded, and why that is honest

**Built and running:** the signal and counter-evidence data model; the weight formula with freshness, counter-evidence and human factors; the scenario update with contributions and entropy; the five bullwhip metrics; the eight-agent orchestration with trace, failure modes and the recommendation guardrail; the Claude SDK integration with structured outputs; the full UI with filters, object pages, charts and annotations; the API; the tests.

**Preview only:** the region filter (all continents, the Nordics and Finland) and the segment filter (data centres, energy clusters, utility grids, renewable generation, industry, e-mobility, hydrogen, buildings) on the overview and Signals pages change their label but not the data; they show where signal filtering by region and segment will sit once cards carry those tags.

**Pre-recorded or demo:** the LLM outputs for the demo item (classification, counter-evidence, interpretation, brief) are replayed when no API key is present, and labelled "replay" in the trace; pasted items fall back to a keyword heuristic that forces reliability C and flags the card for review. Time series behind sparklines are DEMODATA except the sourced anchor points. Bullwhip inputs for BW-1, BW-3 and BW-4 are DEMODATA; BW-5 is not connected. The probability history before today is DEMODATA.

**Why this is the honest cut:** the value of the system is the evidence discipline (sources, counter-evidence, labelled provenance, traceable arithmetic), and that part is fully built and tested. The parts that need licences (TrendForce series, LME real-time, Nord Pool granular) or ABB data (order history) are shown as labelled placeholders rather than invented series. Every replayed output is visibly marked, so the jury sees exactly which boxes a live model would fill.

---

## 6. Pitch (7 minutes)

| Minute | Content | Criterion |
|---|---|---|
| 0:00–0:30 | Hook (below) | Problem definition |
| 0:30–1:30 | The user and the gap: 18-month component orders, 10-week order book, "the best forecast was history" stopped working; both misreadings and their cost | Problem definition 15% |
| 1:30–3:00 | The chain and the mechanism: seven links with lead times; structural vs cyclical; the bullwhip in this chain with 2021–2023 as the order of events; regional timing differences (Fingrid vs FLAP-D vs US) | Market understanding 20% |
| 3:00–4:00 | The evidence: 17 cards, what each measures, reliability, freshness, counter-evidence on every strong one; the five bullwhip metrics; copper's real role; where ABB's SAP data plugs in | Data and signal chain 15% |
| 4:00–5:30 | Live demo: paste the Fingrid item, watch eight agents, see weight and probabilities move by a fraction, open the card, dispute a counter-claim; formulas on screen | AI solution logic 20%, prototype 10% |
| 5:30–6:30 | What it changes for ABB: the component commitment window, allocation, price indexation, S&OP escalation; why it does not recommend (one sentence) | Business value 20% |
| 6:30–7:00 | Close (below) | — |

**Opening hook (30 seconds).** "In early 2025, ABB's relay team had to decide the chips for mid-2026. Demand doubled; they could not see it, and they missed the order. Today they are placing orders for deliveries at the end of 2028, and their most reliable information is an order book that shows the next ten weeks. Eighteen months of blindness against ten weeks of sight. We built the instrument that looks eighteen months ahead, and tells you how much to doubt it."

**One sentence on why no recommendations, and why that is strength.** "It does not recommend because the data it can see is the market, not ABB's contracts, cash and customer promises; a recommendation from half the picture would be false authority, so we deliver the market half early, traceable and with its counter-evidence attached, and leave the decision with the person who holds the other half."

**Closing line.** "The best forecast used to be history. We give ABB the next best thing: the earliest evidence, with its doubts attached, two years before the order book knows."

### 6.1 Eight hardest jury questions

1. **How do you validate that a signal leads ABB's demand?** Each card states its lead-month assumption. Validation is a back-test against ABB's own order history: lag correlation between the card series and relay order intake by segment. The prototype is built so the test is one export away (SIG-017 and BW-5 fields). Until then the lead months are labelled assumptions, and the list of questions for ABB at the end of this document asks for the two facts that calibrate them.
2. **What if the LLM hallucinates?** It cannot hallucinate a number into the arithmetic: the model only quotes a source sentence and assigns grades; every weight and probability is computed by tested code from stored fields. A card with a mis-quoted excerpt is visible on the object page next to its source link, and a dispute halves it. Structured outputs enforce the schema; the guardrail removes recommendation language.
3. **Why no recommendation? Isn't the work half done?** The half we do not do is the half the data cannot see. The challenge text says "support human decision-making" and ABB asked for "insight and scenarios", "never black and white". The next-action link is an analysis action with a date and names, which is the part that is actually missing in ABB's current process.
4. **How does this integrate with ABB's systems?** The cards are a flat schema; SAP exports (purchasing documents, sales schedule lines, change logs) become cards with reliability A through the same collector. The interface is a static single-page application that can be embedded in an intranet portal or an S/4HANA launchpad tile. Nothing in the engine changes when internal data arrives.
5. **Why not do this in Excel?** Excel can hold the weights. It cannot read 40 sources a week, quote the supporting sentence, search for the counter-case on every strong card, and keep an audit trail of who disputed what. The arithmetic is deliberately simple enough for Excel so that the planner can check it; the reading and challenging is the part Excel does not do.
6. **Your probabilities are not calibrated.** Correct, and the method page says so: the update is a traceable log-odds accumulation with analyst-set relevance, not a measured posterior. Calibration needs outcomes; the annotation log and the probability history are the data for it. Today the value is that every point of probability can be opened to its sources.
7. **Most of your time series are demo data.** Yes, and each is labelled. The sourced anchor points are real and dated; the licences for the full series (TrendForce, LME, Nord Pool) are listed. The system is designed so that replacing a DEMODATA series changes nothing except the label.
8. **The scenarios look obvious; what is new?** The scenarios are deliberately plain so that the evidence is the product. What is new is the mandatory counter-evidence per signal, the bullwhip metrics separating hoarding from demand, the lead-time accounting per card, and the fact that one new data point moves the picture by a fraction of a point with the reason on screen.

---

## Self-assessment against the criteria (1–5)

| Criterion | Score | One-sentence reason |
|---|---|---|
| Business value and connection to ABB decisions (20%) | 4 | The decision questions are named and tied to the 18-month window, but the lead-time links are assumptions until validated against ABB order data. |
| Understanding of the market and the phenomenon (20%) | 4 | Chain, bullwhip, regional timing and the 2026-vs-2021 differences are argued with dated sources; US delay figures rely on C-grade sources. |
| Quality of data sources and signal chain (15%) | 4 | 16 public cards with access, reliability and restrictions, five bullwhip metrics; three metrics and most series run on DEMODATA. |
| Quality of problem definition (15%) | 4 | User, rhythm, gap, change to detect, lead time and both misreadings are explicit; the user persona is inferred, not interviewed. |
| Logic and clarity of the AI solution (20%) | 4 | Formulas, agents, failure modes and guardrail are explicit and tested; relevance values r are hand-set. |
| Prototype functionality and modern presentation (10%) | 4 | All views, the full chain, scheduled updates, notifications and tracking work; LLM steps are replayed without a key and the daily history before today is simulated. |

**Three weakest points.** (1) Lead-month assumptions per link are unvalidated; a back-test against ABB order intake is the single most valuable next step. (2) Scenario relevance values and priors are analyst-set; the probabilities are traceable, not calibrated. (3) Three of five bullwhip metrics and most time series run on DEMODATA; the method is real, the inputs are placeholders until licences and ABB exports arrive.

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
| Priors A 0.35 / B 0.20 / C 0.25 / D 0.20 | Does the current state feel like scenario A, and which scenario do you fear most? |

## Final check

The document and the prototype were reviewed for any instruction to the user. Sentences of the form "ABB should order", "increase stock", "buy now" do not appear; the interpretation texts are conditional ("if this holds, …"), the next-step texts name signals, dates and reviewers, and the code guardrail (`agents/llm.py`, `recommendation_filter`) removes such sentences from any generated text, with a test covering it.
