# Irma demo script

About seven minutes, ordered by judging weight: business value 20, market understanding 20, AI logic 20, data and signal chain 15, problem definition 15, prototype 10. It covers the full minimum chain of the brief: **new data → signal detection → source and counter-evidence review → scenario update → recommended move → next action**, and the newer parts: two real segments, the signal market map with a signed impact, and the Historical data comparison.

Every number below was read from the running app (`DEMO_TODAY=2026-10-03`, replay mode, no model key; the same as the public Vercel deployment). If a number on your screen differs, the clock or the data set is wrong: fix that before you start.

## Before you go on

1. Start in replay mode with the frozen clock: `DEMO_TODAY=2026-10-03 AGENT_MODE=replay PORT=8765 ./app/run.sh`, then open http://localhost:8765 (or the Vercel link). Use a 1440×900 window, language EN.
2. Settings → **Reset demonstration state**. Check that the Overview shows the evidence set **Current world situation**, the segment **Data centres**, and the date 2026-10-03.
3. Overview must read: leading situation **Growth continues, components stay scarce, 50%**, then **Investment concentrates in the Nordics, 37%**, **Growth continues, components become easier to get, 10%**, **Projects slip, components stay scarce, 3%**. The Recommended move shows **medium confidence**. Do not import the demonstration item before the demo: a second import adds it again and the numbers below no longer match.
4. Keep a second tab on `docs/how-irma-weighs-evidence.html` for the question "how is a weight made".

## The script

### 0:00–1:15 Business value: the Overview and the recommended move (20%)

*Screen: Overview, top to bottom.*

1. Say: "ABB orders memory and microcontrollers 18 months ahead but sees orders ten weeks ahead. Irma reads open signals and ends in a move for the planner." Scroll slowly down the page once: "The page reads in the order a planner thinks. First, whether anything major happened." Point at the **major-signal banner** (Uptime Institute 2026 survey: power is the constraint). "Then the situation in three lines. Then the filters: segment, region, horizon. Then the chart of the four most likely situations next to the Irma assistant. Then the move."
2. Point at **Current situation**: leading situation 50%, with Google's EUR 13 bn Finland programme and the big-tech commitments as the things to watch.
3. Point at the **Recommended move** card. Read the first move: "Test and approve a second supplier for relay boards that depend on memory chips. Then the next commitment window can be extended if supply stays tight." Point at the labels: **medium confidence**, **ASSUMPTION**, and on the move **Do in any case**. Say: "It is conditional, and it says how sure it is."
4. Open **Trigger · cost if wrong** on that move. Read the trigger signals (SIG-007, SIG-018, SIG-015, SIG-009) and the cost if wrong: "If supply eases, the work has little short-term use. A second supplier still stays available at a small cost."
5. Point at **Next action**: put the approval of a second supplier on the agenda of the next S&OP review; owner the component procurement lead with the S&OP owner; due **2026-10-17**; revisit **2026-10-31**. Open **If the runner-up wins**.
6. Say: "No quantities and no order dates. The order book lags the market by 18 months or more and ABB's contracts and cash are not in open data, so a quantity from here would be false authority. The planner decides."

### 1:15–2:00 Market understanding: horizon and region (20%)

*Screen: Overview, sub-menu.*

1. Click the horizon chips **1 y → 2 y → 3 y**. The line "Leader at this horizon" in the Recommended move card changes: 12 months Growth continues (47%), 24 months a near tie (41% against 40%), 36 months **Investment concentrates in the Nordics** (42%). Say: "Capex reaches the Nordics one to two years after the US. The later horizons are near ties and depend on one assumption, the timing width. We show that, we do not hide it." Return to 1 y.
2. Open **Region**, pick **Finland**, then **North America**: the signals change with it. Say: "Same megatrend, different timing: Finnish connection agreements against US projects slipping." Reset to All regions.

### 2:00–3:00 Two real segments (problem definition 15%, data 15%)

*Screen: Overview, Segment menu.*

1. Open **Segment**: three entries, **All segments**, **Data centres**, **Oil and gas**. Say: "Earlier there were eight entries, six of them empty previews. We removed them: a menu item that does nothing is a claim we cannot support. Two segments have data. The rest is later work."
2. Choose **Oil and gas**. The four situations change to the segment's own pool: **Gas and LNG spending rises, components stay scarce 30%**, **Spending stays flat, maintenance and replacement carry demand 24%**, **Supply shock sets off rush ordering 24%**, **Platforms and terminals move to grid power, protection work grows 22%**. The Recommended move now reads **low confidence**: ask the key suppliers for a written delivery status on oil and gas relay parts. Say: "Different evidence, different move, and Irma says it is less sure: the four are close. These are ten sourced cards, from EIA, IEA, Baker Hughes, ABB's own Q2 report and trade press, each with its counter-evidence. Two of them are second-hand reports and we say so in the documents."
3. Choose **All segments**. The chart and the move are replaced by the card **Pick one segment** with two buttons. Say: "The signals of both segments live together, 47 cards, on the Signals page. A scenario and a move only make sense for one segment, so Irma asks."
4. Choose **Data centres** again.

### 3:00–4:30 The signal market map: weight against impact (AI logic 20%)

*Screen: Signals.*

1. The map is the first thing on the page. Say: "Each dot is a signal. Across: impact, from minus 100 to plus 100, whether it is unfavourable or favourable for ABB relay demand and delivery. Up: weight, how much to trust it and how current it is." Point at the four corners: **Critical risks**, **Strategic opportunities**, **Risks to monitor**, **Small opportunities**, and at the line "Strong-signal threshold 25" from Settings. Point at the shapes: minus in red, plus in green, one grey dot for a card with no direction. "Colour is not the only cue, every dot works with the keyboard, and there is a table view."
2. The Google programme (SIG-003) is selected: **Weight 59, Impact +90**. Say: "Impact is code, never the model: sign from the card's direction and what it measures, size from materiality and how many of the six themes it loads. A rule with one assumption, A_ref 1.5, labelled."
3. Change **Time horizon** to **1 year**. The dots move and the note says the weights are recomputed. SIG-003 becomes **Weight 45**. Two dots now sit in **Critical risks**: Micron's memory shortage through 2028 (SIG-018, impact −80) and the Finnish connection-priority proposal (SIG-014, impact −43). Say: "In a year, tight memory is the threat. In three years its weight fades, because a price card speaks about the next year, not about 2028." Return to **3 years**.
4. Click the dot for DRAM contract prices (SIG-007): impact **−85** although its direction is "rising". Say: "Rising memory prices are unfavourable for delivery. The sign rule reads direction times what the card measures."
5. In the detail panel, open **How the weight is calculated**. Point at the four formulas: product, minimum, geometric mean, arithmetic mean, with the product marked **used**. Say: "Four ways to combine the same four factors. The product is the one we use; the others show how much the choice matters. The average is one of four, it is not the headline."
6. Point at the **Suggested follow-up** box and the buttons **Approve**, **Edit**, **Reject**. Say: "The text comes from the templates, worded as an analysis step, no quantities. The buttons log a confirm, a comment or a dispute with a name and a reason."

### 4:30–5:45 The full chain on new data (AI logic, prototype 10%)

*Screen: Signals → Import data.*

1. Click **Import data**, then **Import demonstration item** (a DEMODATA Fingrid Q3 note: signed connections rose to 3.6 GW from just over 3 GW). Say: "New data."
2. Open **Processing steps**: the collector normalises it, the demand agent recognises a new observation of **SIG-001** (marked `replay`, because there is no key), the counter-evidence agent links two new doubts. Say: "Signal detection, then source and counter-evidence review. Models read and classify; code computes every number."
3. Point at the scenario rows: probabilities move by **tenths of a point** (Growth continues 49.8% → 49.7%, Nordics 36.7% → 36.9%), each with a sentence on which signal moved it and why. Point at the recommended move in the result: the same move, medium confidence, next action due 2026-10-17. Say: "Scenario update, recommended move, next action. The move did not flip on one data point, which is what we want."
4. Click the **SIG-001** link in the result and open **How the weight is calculated**: the weight went **0.15 → 0.17**. Read the four formulas (product 0.17 used, minimum 0.21, geometric 0.65, arithmetic 0.76) and the attribution: "90% of the discount is credibility, because there are now five counter-claims."
5. Go to **Signals**, set **Time horizon** to **3 years**, switch the map to **Table**, and pick the row "Fingrid: signed data-centre connection agreements" (a **Demo data** badge shows, because the import replaced its source): **Weight 17, Impact +85**. Click **Reject**, enter your name and the reason "GW is not relays for our mix", and click **Save rejection**. The weight halves (**17 → 9**), the dot drops, the **impact stays +85**, the dispute is logged with name and reason, and the Overview probabilities move again (50.0%, 36.2%, 10.2%, 3.6%) with the move holding. Say: "The planner is the interpreter. Impact says which way it points; weight says how much we believe it. They are separate on purpose."

### 5:45–6:40 Historical data: the same formulas on a past cycle (AI logic, honesty)

*Screen: Overview → Historical data panel (bottom of the page).*

1. Reset first if you want clean numbers later (Settings → Reset demonstration state). On the Overview scroll to **Historical data** and open it. Point at the label: **illustrative comparison, not validation and not a forecast**.
2. Read the table: five dates from 2021-07-01 to 2023-07-01, built only from what had been published by each date (4 cards at the first date, 18 at the last). The strongest signal by weight moves from chip sales (2021) to memory prices (DRAM prices down in 3Q22 at 0.56, in 2022-07; DRAM prices −18 to −23% at 0.45, in 2023-01). In the last column, what happened next, with its source: for example Micron cutting wafer starts by about 20% on 2022-11-16, and 2023 sales of USD 526.8 bn, 8.2% below 2022.
3. Say plainly: "Do not read this as a track record. The leading situation is the same at four of the five dates, and the last three leaders are separated from the runner-up by 1.5 to 4.6 points. The tool shows which evidence carried weight on each date. It does not show that it would have warned in time. Of the 18 cards, only nine have counter-evidence attached, most excerpts are paraphrases, and six dates were not checked at the original page. It is in the data README." Optional: click **Historical data** next to **Current world situation** to see the whole app as of 1 July 2023: the move comes with low confidence (31%).
4. If you used the switch, click **Current world situation** to switch back (switching resets the demonstration state).

### 6:40–7:00 Close

"The best forecast used to be history. Irma gives ABB the earliest evidence with its doubts attached, and a conditional move to prepare, before the order book knows. Two segments, every number labelled source, demo data or assumption, 223 tests, and it runs without a key."

## Timing notes

- Practise the map and the import (3:00–5:45) most: they carry the AI logic. If time is short, drop the region filter, the DRAM click and the optional world switch.
- If the import has already been done, Settings → **Reset demonstration state** restores the start. A segment switch keeps your annotations; a reset clears them.
- Nothing in the script needs the network. The links on cards open the real sources, so avoid clicking them live unless asked.
- Finnish: the same screens work with the FI switch; the map quadrants read Kriittiset riskit, Strategiset mahdollisuudet, Seurattavat riskit and Pienet mahdollisuudet, and the buttons Hyväksy, Muokkaa, Hylkää.

## The 30-second version

"ABB orders chips 18 months ahead but sees orders ten weeks ahead. Irma follows open signals in two segments, data centres and oil and gas, each with its source, its doubts and its lead time. Every signal gets a weight and a signed impact, and sits on one map. Today for data centres Growth continues, components stay scarce at 50%, and Irma ends in a recommended move, conditional, with trigger signals, cost if wrong and an owner and due date, and no quantities, because open data cannot see ABB's contracts. Import one new Fingrid item and the chain runs: detection, counter-evidence, the scenario moves by a tenth of a point, the move holds. Every number is computed by code, every assumption is labelled, and the planner decides."

## Likely judge questions, with honest answers

**Is the recommendation just a template?** It is assembled from templates, and every template and threshold is labelled ASSUMPTION. What is computed is which template applies (the leading scenario), the confidence (probability margin and entropy), the trigger signals (matched to real cards by their fields and ranked by computed weight) and the dates. We wrote it in code on purpose: it can be tested, it cannot invent a quantity, and it behaves the same without a key. ABB's planners should rewrite the templates first; the engine does not change when they do.

**Why no quantities or order dates?** Three reasons. The order book lags the market by 18 months or more. The information that decides a purchase (frame contracts, allocation agreements, cash, customer priorities) is not in open data. And our probabilities are traceable, not calibrated, so an order size derived from them would be false precision. We give the earliest conditional direction and leave quantity and timing with the person who holds the other half. If the organisers want quantified moves, that needs ABB data first.

**Are your probabilities real probabilities?** No. They are a transparent ranking of today's evidence: log-odds accumulation with analyst-set relevance and priors. Nobody has yet checked how often a situation shown at 50% happens. The path to calibration is stored: one probability point per day, plus the annotation log, compared with ABB's order intake after 6 to 18 months.

**You use four formulas for the weight. Which one counts, and is it an average?** The product of the four factors counts. It is the weight used in the scenarios, on the map and in every list. The minimum, the geometric mean and the arithmetic mean are shown beside it so you can see how much the choice of formula matters. The arithmetic mean is one of the four, and it is not the headline. A test checks that the weight equals the product value.

**How is the impact computed, and who decides the sign?** Code decides, from two fields on the card: `direction` (is the signal rising, tightening or supportive) and `measures` (what it measures). Rising end demand, orders or supportive policy is favourable; rising supply tightness or component and commodity prices is unfavourable. Size is materiality times the share of the six themes the card loads, with A_ref = 1.5. Both A_ref and the polarity are assumptions with no outcome data behind them, and they are listed with the weight assumptions. A card with no direction has impact 0. The language model proposes `direction` and `measures` when it reads a card and a planner can dispute them; it never sets the sign or the number.

**Brent is treated as unfavourable when it falls. Why?** The two Brent cards (OG-002, OG-009) are classified as end demand, meaning operator spending, not as a component price. A lower expected Brent price or a supply disruption is read as less spending on projects that need relays. The rule's price polarity is meant for what ABB pays for components and would give the opposite sign. It is a classification choice, visible on the card, and the planner can dispute it. The rule cannot say that a high oil price helps operators and hurts shipments at the same time.

**Does the historical comparison prove the method works?** No, and the panel says so: "illustrative comparison, not validation and not a forecast". It has five dates in one cycle, most excerpts are paraphrases, only 9 of the 18 cards have counter-evidence, six dates or figures were not checked at the original page, and the scenario pool is the data-centre one, written by people who know how the cycle ended. What it does show is that the code uses only what was published by each date, and which evidence carried weight when. The leading situation barely changes across the five dates, and we do not hide that.

**How strong is the oil and gas data?** Ten sourced cards, each with one counter-evidence card, from EIA, IEA, Baker Hughes, ABB and trade press. Two are second-hand: OG-001 is a news report of an IEA release, OG-006 is a trade article quoting PwC analysts about transformers. All priors, lead times and loadings are assumptions. Five cards are dated after the demo clock of 3 October 2026, so at that clock they count as fully fresh. The bullwhip inputs for oil and gas are demo data for three of the five metrics. The recommended move there comes with low confidence for a reason: the four situations are close.

**How do you know the lead times are right?** We do not. Each card states its lead-month assumption and the reason. The validation is a back-test against ABB's own order history: lag correlation between card series and relay order intake. That is the single most valuable next step, and the structure (SIG-017 and the BW-5 push-out metric) is in place for it.

**What stops the language model from hallucinating?** It never produces a number that enters the arithmetic. It quotes a sentence and assigns grades; weights, impact, probabilities and the recommendation are computed by tested code from stored fields. Each card shows its quote beside its source link, a dispute halves a card's weight, and a regex guardrail removes purchase, quantity and order-timing language from any model-written text, with a test.

**What is real and what is replayed?** Real: all arithmetic, the weights, the impact, the scenario update, the recommendation, the changes and the negative list, the as-of rule in the historical comparison, and the 223 tests. Replayed without a key: the language-model steps for the demonstration item (classification, counter-evidence, interpretation, brief), marked `replay` in the trace. Simulated: the daily probability history before today, labelled DEMODATA. The public Vercel deployment never uses a key.

**How much of the data is demo data?** In data centres 35 of 37 cards are sourced public items; one is a DEMODATA placeholder (the memory spot spread) and one is an internal placeholder for ABB's SAP frame-order coverage. Three of the five bullwhip indicators take DEMODATA inputs, the push-out metric is not connected, and most card time series are DEMODATA except the sourced anchor points. All ten oil and gas cards and all 18 historical cards are sourced. Every demo value is labelled; replacing one changes the label, not the engine.

**The 24 and 36 month rankings are near ties. Why show them?** Because the lead times differ and ABB's three horizons matter. We say it is a near tie and what flips it: a narrower timing width flips the 24-month leader to the Nordic situation, a wider one flips the 36-month leader back. The 12-month ranking is stable.

**What is the business value in numbers?** We do not claim a saving. The value case is timing: an 18-month window against a 10-week view, a move prepared before the order book shows it, and a stated cost of misreading in both directions. A figure would need ABB's order history and cost of capital, and we will not invent it.

**Who is the user, and did you talk to them?** The component procurement lead or S&OP planner preparing the 18-month commitment and the monthly demand review. The persona is inferred from ABB's briefing and the mentors, not interviewed. The questions we would ask ABB are listed at the end of `docs/SOLUTION.md`.

**How would this plug into ABB's systems?** Cards are a flat schema. SAP exports (frame order coverage, schedule-line changes, supplier confirmations) become cards with grade A through the same collector, and the engine does not change. A new segment needs its own sourced cards, counter-evidence, scenario pool and templates, as oil and gas now has. The interface is a static single-page app that could sit in an intranet portal.

**Why not do this in Excel?** Excel can hold the weights. It cannot read dozens of sources, quote the supporting sentence, search for the counter-case on every strong card, and keep an audit trail of who disputed what. The arithmetic is kept simple enough for Excel so that the planner can check it.

**Is there anything in the app that does not add up?** Known items: the five oil and gas cards dated after the demo clock count as fully fresh, and the historical Today column is empty for oil and gas. The segments that used to be preview entries are removed, not simulated. The region filter is real.
