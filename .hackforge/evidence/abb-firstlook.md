# ABB first look: Irma (2026-11-07)

Persona: supply-chain and component-sourcing planner, ABB Electrification Distribution Solutions, Vaasa (MV protection relays). Sceptical of AI and short on time.

**How this was run.** Both URLs I was given failed. `https://irma-junction-vaasa-2026.vercel.app` returned HTTP 404 NOT_FOUND. The `-ey2htru8y-` deployment URL redirected to a Vercel login page (SSO protection). So I ran the same commit (`20ab40a`, which matches origin/main) locally in Vercel mode (`VERCEL=1`, no API key, a runtime directory under /tmp, real date 2026-11-07, no DEMO_TODAY) and reviewed that. I did not edit any repository files. The only new files are the screenshots and this report. One early pass used DEMO_TODAY=2026-10-03, where the headline was 50% instead of 47%.

## First impression (in the persona's voice)

"Okay, it reads like an S&OP pre-read: a situation, four scenarios with probabilities, and moves with conditions and cost-if-wrong. And it explicitly refuses to give me quantities or order timing, which is the right instinct. But within five minutes I found the same scenario at 47% and 44%, signals cited under the wrong IDs, a region filter that does nothing, and component signals I care about weighted at 0 or 1. So I would not trust the numbers yet, even though I like the format."

## What would convince an ABB audience

- A live URL that opens. Right now the public alias is a 404.
- One number, one meaning: the headline probability should be the same everywhere, with the horizon it refers to stated.
- The recommended move's conditions should point at the right signals, and those signals should carry real weight. The relay-relevant component signals (MCU lead times, DRAM) currently sit at weight 0–8.
- The historical view should state plainly when the method would have flagged the 2022 memory turn, compared with when it actually happened. At the moment it shows rows without a verdict.
- Finnish that is complete. The situation brief and the demand-quality label are still English in FI mode.
- Keep what already works: "no quantities, no timing, the planner decides", counter-evidence on every signal card, a cost-if-wrong on every move, and the placeholder for ABB internal ERP data honestly labelled as not connected.

## Prioritised findings

Legend: **[V]** = I verified it in the app or data. **[O]** = my opinion as the persona.

### HIGH

1. **The live demo is unreachable.** [V]
   - Where: `https://irma-junction-vaasa-2026.vercel.app` gives "404: NOT_FOUND". The `-ey2htru8y-veetin0s-projects.vercel.app` URL redirects to `vercel.com/login` (SSO).
   - Why it matters: a judge with the link sees nothing. Evidence: `abb-firstlook-live-url-404.png`.
   - Fix: re-attach the production alias in Vercel (or redeploy), turn off Deployment Protection for the demo, and re-test from a logged-out browser.

2. **The leading probability disagrees with itself on the same card.** [V]
   - Where: Overview, Recommended move. It shows "Growth continues, components stay scarce **47%**", then "LEADING SITUATION AT THIS TIME HORIZON (1 Y): Growth continues, components stay scarce **44%** — same as the headline". At 3 y it shows 39%.
   - The four-scenario strip stays at 47/35/12/6 whatever horizon is chosen, while the headline claims "next 1–3 years … (47%)".
   - Why it matters: a sceptic sees two different numbers for the same thing labelled "same as the headline" and stops trusting all the numbers. Evidence: `abb-firstlook-overview-47-vs-44.png`.
   - Fix: show one probability per selected horizon everywhere (strip, headline, card), and say which horizon the headline uses.

3. **The recommended move's conditions cite the wrong signal IDs.** [V] Checked against `app/backend/data/worlds/1/signals.json`.
   - "memory contract prices and microcontroller lead times SIG-007, **SIG-018**": SIG-018 is "Micron: memory demand expected to exceed supply through 2027 and 2028". The MCU lead-time signal is **SIG-008**.
   - "signed grid connection deals and firm investments in Finland SIG-003, **SIG-033**": SIG-033 is "Valorem *plans* 30–50 MW data centre in Savonlinna". That is a plan, not a signed deal.
   - "distributor stock mood and the gap between memory spot and contract prices SIG-015, SIG-009" and "ABB's own frame orders and order intake [SIG-020, SIG-017]": both pairs are in reverse order (SIG-015 = spread, SIG-009 = ECIA sentiment; SIG-020 = ABB Q2 order intake, SIG-017 = frame PO placeholder).
   - Why it matters: the selling point is "every condition is traceable". The first trace I followed was wrong.
   - Fix: generate the condition text from the signal records (ID plus short name) instead of hand-written templates, and add a test that every cited ID's name matches its description.

4. **Component signals carry almost no weight, yet drive the headline and the move.** [V]
   - Signals table, Data centres, 1 year: "Industrial 32-bit MCU lead times" weight **1**; "DRAM spot-to-contract price spread" **1**; "ECIA memory IC sales sentiment" **1**; "TrendForce: DRAM contract price change" **8**.
   - At 3 years: all four are **0**, and the "CRITICAL RISKS" quadrant is empty.
   - Yet the headline says "Chips and memory are still hard to get … watch … DRAM contract prices (QoQ)". The Scenarios page credits DRAM with **+0.17**. The procurement and manufacturing moves are conditioned on exactly these signals.
   - Why it matters: for a component planner these are the most important inputs, and the map says to ignore them. Probably recency decay on June 2026 data at today's date. Evidence: `abb-firstlook-signals-3y-critical-risks-empty.png`.
   - Fix: refresh the component data points, or show the decay explicitly ("stale: last data 1 Jun 2026"). Make scenario contributions use the same horizon weight as the map.

5. **The historical brief lists the same signals as both support and counter-evidence.** [V]
   - Where: Historical data (2023-07-01), Situation brief. "Strongest support for the leading scenario: [HS-018] NVIDIA … (+0.12); [HS-017] SIA global chip sales Q1 2023, -21% (**-0.11**); [HS-015] DRAM prices -18 to -23% (**-0.09**). Evidence against it: [HS-017] … (-0.11); [HS-015] … (-0.09)."
   - In the same view the headline says "Chips and memory are easier to get than before" while the leading scenario is "components stay scarce (31%)".
   - Why it matters: this is the "would it have worked" proof, and it contradicts itself. Evidence: `abb-firstlook-historical-full.png`.
   - Fix: filter "support" to positive contributions only, and derive the supply sentence from the leading scenario (or explain the disagreement).

### MEDIUM

6. **The region filter does nothing on the Overview.** [V] Choosing "North America" leaves the headline ("…data centres in the Nordics…"), probabilities, chart, brief and move identical. Why it matters: it looks like a dead control in front of judges. Evidence: `abb-firstlook-region-northamerica-nochange.png`. Fix: either filter or recompute by region, or remove or disable the control on the Overview with a tooltip.

7. **"All segments" still shows the data-centre headline.** [V] With Segment = All segments, CURRENT SITUATION still says "Demand for power equipment from data centres in the Nordics is still growing…", while the scenario and move panels correctly say "Pick one segment". Evidence: `abb-firstlook-allsegments-dc-headline.png`. Fix: show a short cross-segment headline, or the same "pick a segment" state.

8. **"+1.2 pp since yesterday" is compared against simulated data, and that is not disclosed where it appears.** [V] The Scenarios page footnote says "Points before 2026-11-07 are simulated demonstration data (DEMODATA)". The Overview delta badges (+1.2 / −0.4 / −0.3 / −0.5 pp) carry no DEMODATA label. In the 2023 historical view it still shows "+0.9 pp since yesterday". Why it matters: a sceptic will ask "what changed yesterday?" and the honest answer is "nothing real". Evidence: `abb-firstlook-scenarios-demodata-delta.png`. Fix: label the deltas DEMODATA, or hide them until there are two real runs. Hide them in the historical view.

9. **The time horizon is not shared between pages.** [V] After a reload the Overview defaults to "1 y" and Signals to "3 years". The weights then differ: Google signal 34 (1 y) vs 45 (3 y). The assistant cites yet other values ("SIG-008 … weight 0.07" when the 1 y table shows 1). Fix: one global horizon state and one weight scale (0–100 or 0–1, not both).

10. **The Capacity move rests on a data source that is not connected.** [V] The Capacity condition is "ABB's own frame orders and order intake [SIG-020, SIG-017]". SIG-017 is "ABB internal: frame purchase order coverage (placeholder)", weight 0, source "not connected in the prototype". The placeholder can still be approved ("Saved. The weights are recalculated."). [O] It is good that it is labelled Assumption, but a move should not hinge on it. Fix: mark that condition "needs ERP data — not evaluable yet", and disable Approve on placeholders.

11. **The signal card says "AI RECOMMENDATION", but the Overview says the move is made by code.** [V] The signal detail panel heads the move "AI RECOMMENDATION", while the Overview says "The recommended move is generated by code with its conditions". It is also unclear what Approve/Edit/Reject act on: they sit under the recommendation box, but "Approving raises the weight" of the signal. Why it matters: the challenge requires the AI not to decide, and this label undercuts that message. Fix: rename it "Conditional move (rule-based)" and move Approve/Edit/Reject next to the signal's weight with the label "Assess this signal".

12. **The assistant answers with templates rather than the question asked.** [V]
    - "What should I watch for memory chips?" returned the whole procurement move. Its "Signals to watch" lists Google FI and Big-tech Finland before any memory signal, and the response repeats the wrong SIG-018 label.
    - "Why is the leading scenario 47%? What would make it drop?" returned four loosely related signals (Uptime, IEA, Micron, FI connection rule). It did not mention the prior (18%), the top contributors or the refuting conditions, all of which exist on the Scenarios page.
    - A Finnish question asked in EN mode got an English answer. In FI mode the Finnish answer is fine.
    - Footer jargon: "mode: composed" / "mode: retrieval".
    - [O] It is grounded and cited, but it doesn't answer the question asked. Fix: route "why X%" to the scenario contribution breakdown and the refute list, match the reply language to the question, and hide the mode tag.

13. **Finnish UI has untranslated core text.** [V] In FI mode:
    - The whole "Tilannekatsaus" body is English ("Situation as of 2026-11-07. The most likely picture is…"), also after a reload. Evidence: `abb-firstlook-fi-brief-untranslated.png`.
    - "Kysynnän laatu: mixed turning".
    - "Saved. The weights are recalculated."
    - Source field "ABB SAP ERP: frame PO / scheduling agreement coverage…".
    - "ASSUMPTION" badges.
    - The world-switch toast stays in the previous language (it showed "Nykyinen maailmantilanne" after switching to EN).
    - Fix: translate the brief template and the demand-quality labels, and re-render the toast on language change.

14. **The oil and gas headline overstates growth.** [V] It says "Demand for power equipment in oil and gas is still growing", while the four scenarios are 29/25/23/23 (entropy 1.00), confidence is "low", the second scenario is "Spending stays flat", and demand quality is "hoarding risk". The O&G situation brief has no "Evidence against it" section at all, while data centres has one. I found no leftover data-centre wording in the O&G moves. "About this data set: … growth with scarce components" is shared text. Fix: derive the growth verb from the scenario spread ("no clear direction"), and always print counter-evidence (or "none above threshold").

### LOW

15. **The 3-year demand index of 219 looks templated.** [V] Data centres at 3 y shows a demand index of **219** (over 2x in 3 years). The same 219 appears in the 2023 historical view. The scenario narrative has unlabelled numbers ("delivery times stay at or above 8–10 weeks and component lead times stay above 40 weeks"). [O] It is labelled "illustrative, not a forecast", but an axis that goes to 280 invites the question "where is 2.2x from?". Fix: put an ASSUMPTION badge on the chart and the narrative numbers, with a link to the template parameters.

16. **The historical view lacks a verdict.** [O] The 2022-07-01 row still leads with "components stay scarce" (30%) while its strongest signal is "DRAM prices down in 3Q22". It only flips on 2023-01-01, then flips back by 2023-07-01. That is honest, but it does not show earlier warning than a planner reading TrendForce. Fix: add a one-line "flagged turn on / actual turn on / lead or lag" per row.

17. **Jargon on the Overview.** [V] "entropy 0.82", "Uncertainty 0.82", "Demand quality: mixed turning", "smoothing width", "pp", and the header clock "09:43 → 10:43". [O] A planner won't decode these. Fix: plain words ("no scenario is clearly ahead", "next refresh 10:43").

18. **Red "No API key" banner and a run log dated after "today".** [V] Signals shows a red box "No API key: automatic search is off and nothing is added." and a log "2026-10-04 10:34 · … about USD 1.84". With DEMO_TODAY=2026-10-03 that log sits a day after "today". Fix: use a neutral "Demo mode: automatic search off" note.

19. **Signal source details disagree.** [V] The Google card says "reported by The Global Economics / Computer Weekly, Published 9 Sept 2026". The link is `theglobaleconomics.com/2026/09/11/…`, and the counter-evidence source says "Google / Fortum announcement coverage". The card shows no measured value; for example, the MCU card's "52 weeks" appears only inside its counter-evidence. A SOURCE badge appears only in assistant answers, not on cards. Fix: one source line per card, with the measured value and an explicit SOURCE/DEMODATA/ASSUMPTION badge.

20. **Finnish phrasing a Vaasa office would trip on.** [V text / O wording]
    - "Suositeltu siirto" (a chess "move") → "Ehdotettu toimenpide".
    - "Vanha data" → "Historiallinen vertailu".
    - "Ehto · hinta, jos arvio on väärä" → "Ehto · kustannus, jos arvio osuu väärin".
    - "Koodi muodosti tämän malleista" ("malleista" reads as "models") → "…valmiista tekstipohjista".
    - "releosille" → "relekorteille".
    - "jakelijoiden varastotunnelma" → "jakelijoiden varastonäkymä".
    - "Kumoavat merkit" → "Merkit, jotka kumoaisivat arvion".
    - "1 signaalia löydetty" → "1 signaali löydetty".
    - "noin 1.84 USD" → "noin 1,84 USD".
    - "+1.2 pp" → "+1,2 %-yks.".
    - Inconsistent "47%" vs "35 %".
    - Month labels "marras 2026" → "marraskuu 2026" or "11/2026".
    - Both "Tutkimus ja instituutiot" and "Sääntely ja instituutiot" exist.

21. **Minor UI issues.** [V] The Scenarios "Probability by day" chart axis text is about twice the size of the rest of the page. The assistant panel has a large empty area before the first question. A historical snapshot is labelled "CURRENT SITUATION 2023-07-01". favicon.ico returns 404, which is the only console error locally. At 1280x720 the recommended move is below the fold, but the layout is clean with no overlap.

## Verified as good

- [V] The app never gives quantities or order timing. Every move has a condition, a horizon, a cost-if-wrong, an owner and a due date, plus "If the second most likely situation leads".
- [V] Every signal card I opened has counter-evidence. Several carry [ASSUMPTION] tags on the reasoning (for example "verify with ABB how far ahead of energisation relays are ordered").
- [V] The domain fit is mostly right: relay boards depending on memory, assembly slots for long-lead relay types, sharing relays between internal switchgear and external customers, S&OP review, Fingrid/Energinet connection rules, Microsoft's Vaasa/Mustasaari land purchase, and electrification of O&G platforms.
- [V] "How the weight is calculated" shows four formulas and their range (0.45–0.83). [O] It should also list the four input factors with their values.
- [V] Approve, Edit and Reject work, ask for a name and reason, and write an assessment log.
