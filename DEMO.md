# Irma demo script

Three minutes, ordered by judging weight: business value 20, market understanding 20, AI logic 20, data and signal chain 15, problem definition 15, prototype 10. It covers the full minimum chain of the brief: **new data → signal detection → source and counter-evidence review → scenario update → recommended move → next action**.

Every number below was read from the running app (`DEMO_TODAY=2026-10-03`, replay mode, no model key; the same as the public Vercel deployment). If a number on your screen differs, the clock or the world is wrong: fix that before you start.

## Before you go on

1. Start in replay mode with the frozen clock: `DEMO_TODAY=2026-10-03 AGENT_MODE=replay PORT=8765 ./app/run.sh`, then open http://localhost:8765 (or the Vercel link).
2. Settings → **Reset demonstration state**. Make sure the world is the public one (Overview shows "Public signals as of October 2026: growth with scarce components.") and the language is EN.
3. Overview must read: leading situation **Growth continues, components stay scarce, 50%**, runner-up **Investment concentrates in the Nordics, 37%**, recommended move confidence **medium**. Do not import the demonstration item before the demo: a second import would add the item again and the numbers below would no longer match.
4. Keep a second tab on `docs/how-irma-weighs-evidence.html` in case a judge asks how a weight is made.

## The 3-minute script

### 0:00–0:50 Business value: the recommended move (20%)

*Screen: Overview, right-hand column.*

1. Say: "ABB orders memory and microcontrollers 18 months ahead but sees orders ten weeks ahead. Irma reads open signals and ends in a move for the planner."
2. Point at the **Recommended move** card (30% of the top row). Read the bold lead move: "Prepare a second-source qualification for memory-dependent relay boards, so the next commitment window can be extended if the tight-supply reading holds."
3. Point at the pills: **medium** confidence and the **ASSUMPTION** label. Say: "It is conditional and it says how sure it is."
4. Open the disclosure **Trigger · cost if wrong** on the first move. Read the trigger signals (SIG-007, SIG-018, SIG-015, SIG-009) and the cost if wrong: "If supply eases instead, the qualification effort has little short-term use, but a second source stays in the portfolio at modest cost."
5. Point at **Next action**: put it on the next S&OP agenda; owner the component procurement lead with the S&OP owner; due **2026-10-17**; revisit **2026-10-31**.
6. Open **If the runner-up wins**: "A hedge: what changes if the Nordic situation overtakes."
7. Say: "No quantities and no order dates. The order book lags the market by 18 months or more and ABB's contracts and cash are not in open data, so a quantity from here would be false authority. The planner decides."

### 0:50–1:20 Market understanding: horizon, regions, the other side (20%)

*Screen: Overview, left-hand column; then Signals.*

1. Click the horizon chips **1 y → 2 y → 3 y**. The "Leader at this horizon" line changes: 12 months Growth continues (47%), 24 months a near tie (41% against 40%), 36 months **Investment concentrates in the Nordics** (42%) with a "differs from headline" pill. Say: "Capex reaches the Nordics one to two years after the US, and the picture shifts toward Finland as the horizon lengthens. The later horizons are near ties and depend on one assumption, the timing width; we show that, we do not hide it."
2. Open the **Region** filter and pick **Finland**, then **North America**: the signal list changes with it. Say: "Same megatrend, different timing: Finnish connection agreements against US projects slipping."
3. Click **Signals**. Point at **Negative signals and counter-evidence**: "Seven cards point against growth, from Denmark, Ireland, the Netherlands and the US grid queue, plus the counter-evidence behind the growth cards. Growth and reversal evidence side by side."
4. Click **Scenarios**, scroll to **Demand quality**: "The bullwhip check reads mixed, turning: hoarding indicators still elevated, two urgency measures already fading."

### 1:20–2:15 AI solution logic: the full chain on new data (20%, prototype 10%)

*Screen: Signals → Import data.*

1. Click **Signals**, then **Import data**, then **Import demonstration item** (a DEMODATA Fingrid Q3 note: signed connections rose to 3.6 GW from just over 3 GW). Say: "New data."
2. Results appear. Open **Processing steps**: the collector normalises it, the demand agent recognises a new observation of **SIG-001** (marked `replay`, because there is no key), the counter-evidence agent links two new doubts. Say: "Signal detection, then source and counter-evidence review. Models read and classify; code computes every number."
3. Point at the scenario rows: probabilities move by **tenths of a point** (Growth continues 49.8% → 49.7%, Nordics 36.7% → 36.9%), each with a sentence on which signal moved it and why. Say: "One quarterly data point barely moves the picture, and we show why."
4. Point at the **Recommended move** card in the result: the same move, medium confidence, next action due 2026-10-17. Say: "Scenario update, recommended move, next action. The move did not flip on one data point, which is what we want."
5. Click the **SIG-001** link at the top of the result. Open **How the weight is calculated**: the weight went **0.15 → 0.17**; read the **band** (0.17 to 0.76) and the **attribution**: "90% of the discount is credibility, because there are now five counter-claims. The formula is credibility × currency × materiality × the planner's view, capped at 1, and every constant is labelled."
6. Point at the horizon table in the same section: "And it speaks differently at 12, 24 and 36 months."

### 2:15–2:35 Data and signal chain (15%)

*Screen: SIG-001 page, then SIG-003.*

1. On SIG-001, point at **Earlier versions of this card**: the demonstration import replaced the source with a DEMODATA item, and the card says so and keeps the original grade-A Fingrid half-year report underneath. Then open **SIG-003** (Google FI investment) and point at the source quote and link, reliability grade A, the lead time and the label pills. Say: "Every card has a named source, a dated quote, a grade, a lead time and a label: SOURCE, DEMODATA or ASSUMPTION. 37 cards, 35 sourced before the demonstration import. Where data is licensed or ABB's own, such as SAP order history, we show a labelled placeholder rather than an invented series."
2. Back on **Signals**, point at the **Latest changes** box: "SIG-001 is up 0.02 since the last cycle."

### 2:35–2:55 Problem definition and the human (15%)

*Screen: SIG-001 page, then Overview.*

1. Scroll to **Your assessment**, type "GW is not relays for our mix", click **Dispute**. The weight halves (**0.17 → 0.09**) and the dispute is logged with name and reason.
2. Click **Overview**: the probabilities move again (50.0%, 36.2%, 10.2%, 3.6%) and the recommended move holds. Say: "The user is the component procurement lead preparing the 18-month commitment. Misread hoarding as demand and ABB carries inventory at peak prices; misread a delay as a turn and it under-orders. Both costs are on the screen next to the move."
3. Under **Evidence set**, click **World situation 2** (a constructed downturn, labelled DEMODATA). The recommended move changes to "Compare the frame-order book with end-customer consumption before any further commitment is extended", now at low confidence. Say: "Different evidence, a different move, and Irma says how sure it is." Click **Current world situation** to switch back.

### 2:55–3:00 Close

"The best forecast used to be history. Irma gives ABB the earliest evidence with its doubts attached, and a conditional move to prepare, before the order book knows. 84 tests pass, and it runs without a key."

## Timing notes

- Practise the import step (1:20–2:15) most: it carries the minimum chain. If time is short, skip the horizon table and the Latest changes box.
- If the import has already been done, Settings → **Reset demonstration state** restores the start.
- Nothing in the script needs the network. The links on cards open the real sources, so avoid clicking them live unless asked.

## The 30-second version

"ABB orders chips 18 months ahead but sees orders ten weeks ahead. Irma follows 37 open signals, each with its source, its doubts and its lead time, and keeps four scenarios in parallel: today Growth continues, components stay scarce at 50%. It ends in a recommended move, conditional, with trigger signals, cost if wrong and an owner and due date, and no quantities, because open data cannot see ABB's contracts. Import one new Fingrid item and you watch the chain run: detection, counter-evidence, the scenario moves by a tenth of a point, the move holds. Every number is computed by code, every assumption is labelled, and the planner decides."

## Likely judge questions, with honest answers

**Is the recommendation just a template?** It is assembled from templates, and every template and threshold is labelled ASSUMPTION. What is computed is which template applies (the leading scenario), the confidence (probability margin and entropy), the trigger signals (matched to real cards by their fields and ranked by computed weight) and the dates. We wrote it in code on purpose: it can be tested, it cannot invent a quantity, and it behaves the same without a key. ABB's planners should rewrite the templates first; the engine does not change when they do.

**Why no quantities or order dates?** Three reasons. The order book lags the market by 18 months or more. The information that decides a purchase (frame contracts, allocation agreements, cash, customer priorities) is not in open data. And our probabilities are traceable, not calibrated, so an order size derived from them would be false precision. We give the earliest conditional direction and leave quantity and timing with the person who holds the other half. If the organisers want quantified moves, that needs ABB data first.

**Are your probabilities real probabilities?** No. They are a transparent ranking of today's evidence: log-odds accumulation with analyst-set relevance and priors. Nobody has yet checked how often a situation shown at 50% happens. The path to calibration is stored: one probability point per day, plus the annotation log, compared with ABB's order intake after 6 to 18 months.

**How do you know the lead times are right?** We do not. Each card states its lead-month assumption and the reason. The validation is a back-test against ABB's own order history: lag correlation between card series and relay order intake. That is the single most valuable next step, and the structure (SIG-017 and the BW-5 push-out metric) is in place for it.

**What stops the language model from hallucinating?** It never produces a number that enters the arithmetic. It quotes a sentence and assigns grades; weights, probabilities and the recommendation are computed by tested code from stored fields. Each card shows its quote beside its source link, a dispute halves a card's weight, and a regex guardrail removes purchase, quantity and order-timing language from any model-written text, with a test.

**What is real and what is replayed?** Real: all arithmetic, the weights, the scenario update, the recommendation, the changes and the negative list, and the 84 tests. Replayed without a key: the language-model steps for the demonstration item (classification, counter-evidence, interpretation, brief), marked `replay` in the trace. Simulated: the daily probability history before today, labelled DEMODATA. The public Vercel deployment never uses a key.

**How much of the data is demo data?** 35 of 37 cards are sourced public items. One is a DEMODATA placeholder (the memory spot spread) and one is an internal placeholder for ABB's SAP frame-order coverage. But three of the five bullwhip indicators take DEMODATA inputs, the push-out metric is not connected, and most card time series are DEMODATA except the sourced anchor points. Every one is labelled; replacing one changes the label, not the engine.

**You say the weights are better. Better than what?** Than a single product of five numbers. The new weight separates credibility (with further independent sources and counter-evidence), currency, materiality and the planner's view, never exceeds 1 (two confirmations used to give 1.44), shows a band across four ways of combining them, and says which condition costs the most. Two parts are built and tested but not yet used by any card: corroboration by a second independent source, and the statistical z-score for sourced histories. So today every weight equals what the single-source formula gives, and a test checks that.

**The 24 and 36 month rankings are near ties. Why show them?** Because the lead times differ and ABB's three horizons matter. We say it is a near tie and what flips it: a narrower timing width flips the 24-month leader to the Nordic situation, a wider one flips the 36-month leader back. The 12-month ranking is stable.

**What is the business value in numbers?** We do not claim a saving. The value case is timing: an 18-month window against a 10-week view, a move prepared before the order book shows it, and a stated cost of misreading in both directions. A figure would need ABB's order history and cost of capital, and we will not invent it.

**Who is the user, and did you talk to them?** The component procurement lead or S&OP planner preparing the 18-month commitment and the monthly demand review. The persona is inferred from ABB's briefing and the mentors, not interviewed. The questions we would ask ABB are listed at the end of `docs/SOLUTION.md`.

**How would this plug into ABB's systems?** Cards are a flat schema. SAP exports (frame order coverage, schedule-line changes, supplier confirmations) become cards with grade A through the same collector, and the engine does not change. The interface is a static single-page app that could sit in an intranet portal.

**Why not do this in Excel?** Excel can hold the weights. It cannot read dozens of sources, quote the supporting sentence, search for the counter-case on every strong card, and keep an audit trail of who disputed what. The arithmetic is kept simple enough for Excel so that the planner can check it.

**Is there anything in the app that does not add up?** One known thing: the segment filter is a labelled preview and does not filter yet; the region filter does.
