# Irma: 10-minute pitch

Format: **3-minute video** (pre-recorded, narrated), then **7 minutes of live talk and demo**.
Every number below is read from the running app (`DEMO_TODAY=2026-10-03`, replay mode) or from `docs/SOLUTION.md`; nothing is invented.
The video tells the story; the live part proves it and goes deeper. They don't repeat each other word for word: the video shows each idea once, the live demo opens the evidence behind it.

---

## Part 1: the 3-minute video

Narrator: one continuous `eleven_v3` take (voice to be confirmed), split per scene from the word timings.
Captions show the text without the audio tags.
Visuals: screen recordings of the v2 app over one continuous ABB-red-and-white background, scenes dissolve into each other.
Music: one arc, problem → build → payoff → finale, with a recurring four-note motif. One real drop (the recommended move), one smaller lift (the import). Jokes and whispers duck and muffle the music; they never hard-stop it.

| # | Scene | Narration (spoken; tags in brackets) | Visual | Music / SFX |
|---|---|---|---|---|
| 1 | hook | An ABB protection relay is a tiny computer in a box. Three to four million lines of code, and quite a few memory chips. [sighs] And those chips have to be ordered eighteen months ahead. | A relay icon "opens" into a chip; "18 months" counter | Sparse, low pulse; motif on piano. Soft "tick" per word in "eighteen months" |
| 2 | gap | The order book? It sees about ten weeks. [laughs] That's driving a truck with a ten-week windscreen and an eighteen-month braking distance. The early signs are already out there, in grid reports, price lists and press releases. They just reach the order book too late. | Timeline: 10-week window vs 18-month bar; truck gag; signal sources scroll past | Tension builds slowly; muffled under the laugh; small "honk" on "truck" |
| 3 | meet | Which brings us to Irma. Irma follows thirty-seven signal cards on Nordic data centres and component supply, weighs every one, and keeps four futures open at the same time. | Logo reveal → Overview, the 70/30 split | First lift: drums enter on "Irma" |
| 4 | weights | Each signal gets a weight from zero to one: how credible, how fresh, how big the move, and what the planner thinks. Doubts pull it down. [whispers] Psst, nothing gets to shout until someone has tried to prove it wrong. Code does the maths. The language model only reads and quotes. | SIG-003 weight card, the breakdown bar, the range | Steady build; music muffled for the whisper |
| 5 | balance | And Irma listens to the bad news too. Seven warning cards: Denmark pausing new grid connections, Dublin's constrained areas, a Dutch court saying the grid is full. Then pick a horizon. At one year, growth with scarce chips leads. At three years, the Nordic build-out is neck and neck. | Negative list; click 1 y → 3 y, the leader line changes | Riser starts under "pick a horizon" |
| 6 | move | So what should ABB actually do? Here's the new part. Irma ends in a recommended move. Today, growth continues and components stay scarce, at fifty percent. Prepare a second source for memory-heavy relay boards, so the next commitment window can stretch if supply stays tight. Every move says what would change it, and what it costs if Irma is wrong. Owner. Due date. Done. | Recommendation card, the trigger disclosure opens, owner and due date highlight | **The drop** on "recommended move"; hits on "Owner. Due date. Done." |
| 7 | chain | Then new data arrives. A Fingrid update goes in. Irma checks it, finds two new counter-claims, nudges the scenarios a little, and the move holds. [laughs] Boring is good. Boring means the plan survived the news. | Import page: the run, the trace, the deltas, the move card | Smaller lift; muffled on the laugh |
| 8 | flip | Switch to a constructed downturn, and the move changes: compare the frame orders with real consumption before committing more. Low confidence, and Irma says so. | World situation 2, the move card swaps | Key change, darker chord; motif inverted |
| 9 | close | No order quantities, no crystal ball. Open data can't see ABB's contracts, so the planner decides. Irma just makes sure they decide eighteen months early, not ten weeks late. Irma. From weak signals to proactive decisions. | Overview pull-back → logo, tagline | Full motif, strong outro, final hit on "proactive decisions" |

About 430 words. At this narrator pace that is about 2 min 50 s, leaving room for the gaps and the outro.

**Fact check (where each claim comes from)**

| Claim | Source |
|---|---|
| Relay is a small computer, 3–4 million lines of code; chips ordered 18 months ahead | SOLUTION.md §1 [ABB mentor facts] |
| Order book sees about ten weeks | SOLUTION.md §1.1 link 6: 8–10 weeks delivery time [ABB] |
| 37 signal cards | App, world 1: 36 in signals.json + SIG-033 from the scout |
| Seven warning cards (Energinet, EirGrid, Dutch court) | App: `negative_signals` with kind "signal" = 7; SIG-034, SIG-035, SIG-036 |
| 1 y leader growth with scarce chips; 3 y Nordics neck and neck | App: scenarios_by_horizon 12 → expansion_tight 47%; 36 → nordic_concentration 42% vs 39% |
| 50%, second-source move, owner and due date | App: recommendation (medium confidence, due 2026-10-17) |
| Fingrid import: two new counter-claims, small move, move holds | App: /api/run demo item, counter-cards 3 → 5, leader 49.8% → 49.7%, same move |
| Downturn: compare frame orders with consumption, low confidence | App: world 2 recommendation |

---

## Part 2: the 7-minute talk and live demo

Setup before you start: app on `http://localhost:8766`, **Settings → Reset demonstration state**, world 1, language EN, browser at 1440 px, zoom 100%. A second tab holds the slides (`docs/pitch-slides.html`).

| Time | What you say (key lines) | What you show |
|---|---|---|
| **0:00–0:40** Who and what decision (J4, 15%) | "The user is the component procurement lead preparing ABB's 18-month commitment for memory and microcontrollers, with the S&OP owner. The decision: extend the commitment window, hold it, or pull back. Misread hoarding as demand and ABB carries stock at peak prices. Misread a delay as a turn and it under-orders into allocation." | Slide 1: the user and the decision, the two costs of misreading |
| **0:40–1:40** The market (J2, 20%) | "Demand reaches ABB through a seven-link chain: hyperscaler capex, land and grid inquiries, signed connection agreements, substation design, switchgear tender, the relay order, and 18 months earlier the chip order. Structural drivers (signed agreements, committed programmes) don't reverse with one quarter. Cyclical ones (memory prices, distributor stock) do. 2021–23 is the analogy: lead times rose from 12 to 22 weeks, orders were doubled, then they unwound." | Slide 2: the lag chain with lead times; slide 3: structural vs cyclical, the bullwhip |
| **1:40–4:40** Live demo: the chain (J1 20%, J6 10%) | See the click path below | The app |
| **4:40–5:40** How the AI works (J5, 20%) | "Nine agents. Language models read, classify, look for counter-evidence and write the brief, quoting sources. Code computes every number: the weight, the scenario probabilities, the recommended move. A guardrail strips any quantity or order language from model text. 85 tests cover it, and it runs without a key." | Slide 4: architecture; in the app, Import → **Processing steps** (the trace, with "Recommendation agent (code)") |
| **5:40–6:30** Data, and what's honest (J3, 15%) | "37 cards, 35 from named public sources, every one with a grade, a date, a lead time and a label. What isn't real yet is labelled: the daily history and three of five demand-quality inputs are demo data, and the lead times are assumptions until we back-test them against ABB's order intake. That's where ABB's own data plugs in: frame orders from SAP, the quote pipeline." | Slide 5: data portfolio and the SOURCE / DEMODATA / ASSUMPTION split |
| **6:30–7:00** Close and next step | "Irma doesn't buy anything. It gives the planner the earliest evidence with its doubts attached, and a move to prepare, 18 months early instead of 10 weeks late. Next step: a three-month pilot that back-tests the lead times on ABB's order history." | Slide 6: next steps; back to the Overview |

### Live demo click path (1:40–4:40)

1. **Overview** (0:30). "Current situation on the left, the recommended move on the right. Growth continues, components stay scarce, 50%, medium confidence." Open **Trigger · cost if wrong** on the procurement move: "It stays valid while memory contract prices and microcontroller lead times keep confirming tight supply. If supply eases, the second source still has modest value." Point at **Next action**: owner, due 2026-10-17, revisit 2026-10-31.
2. **Horizon** (0:20). Click **3 y**: "At three years the Nordic build-out leads, 42 to 39, a near tie. The card tells you to read the hedge, and it opens." Click **1 y** again.
3. **A signal** (0:35). Click **Google FI investment EUR 13 bn** (SIG-003). "Weight 0.59: grade A, fresh, large. Here is where the discount comes from, here is the range across four ways of combining the factors, and the weight at one, two and three years."
4. **The other side** (0:25). **Signals**: point at **Negative signals and counter-evidence** on the right. Set **Region: Nordics**: the lists filter. Set it back to All.
5. **New data** (0:50). **Import data → Import demonstration item** (a labelled DEMODATA Fingrid update). "Detection: it updates SIG-001. Counter-evidence: two new counter-claims. Scenario: 49.8 to 49.7%, Nordics up 0.2. Recommended move: unchanged, still medium confidence. Next action: same owner, same due date." Open **Processing steps** briefly if time allows.
6. **The planner decides** (0:20). Open **SIG-001**, type "GW is not relays for our mix", click **Dispute**: the weight halves to 0.09, logged with name and reason. Under **Earlier versions of this card** the original grade-A Fingrid report is kept.

If you are short of time, skip step 6; if you have spare time, switch to **World situation 2** on the Overview (the move changes, low confidence) and switch back. Switching worlds resets the import.

### Backup plan

- If the live app fails: play `~/Projects/irma-v2-pitch-video/out/demo-backup.mp4` (a 3-minute silent screen recording of the click path above) and narrate over it.
- If the laptop fails: the slides contain screenshots of every demo step.
- If the network fails: nothing changes. The app runs locally in replay mode and needs no internet or API key.

### Likely questions

See `DEMO.md` → "Likely judge questions, with honest answers".
