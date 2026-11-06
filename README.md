# Irma — weak-signal scenario monitor for ABB Distribution Solutions

Hackathon prototype (Junction Vaasa 2026, ABB Distribution Solutions challenge).
Segments: data centres (default) and oil and gas, plus an All segments view of the signals. Region: Nordics + Europe, with the US as comparison. Horizon: 12–36 months.

The system reads open-source signals about end demand and electronic-component supply, weighs them with an
ensemble formula the user can inspect, keeps four scenarios in parallel for the chosen segment, actively attaches
counter-evidence to every strong signal, and from the leading scenario composes a **recommended move and a next
action** in conditional, qualitative form. The move has no quantities, order points or order dates, because open
data cannot see ABB's contracts, allocations and cash. The planner decides.

## What it does

- **Overview, top to bottom:** a major-signal banner, Current situation (a short market review), a sub-menu
  (segment, region, horizon), the four most likely situations with the chart next to the Irma assistant, the
  Recommended move, and the full Market summary with a Historical data panel.
- **Two real segments.** *Data centres*: 37 signal cards (35 sourced, 1 DEMODATA placeholder, 1 internal placeholder),
  7 of which point against growth. *Oil and gas*: 10 sourced cards, each with counter-evidence, its own eight
  scenarios and its own recommendation templates. *All segments* combines the signals and the map (47 cards); the
  scenario chart and the recommended move are made for one segment, so that view asks you to pick one.
- **Ensemble weight.** Four formulas combine credibility, currency, materiality and the planner's view: product,
  minimum, geometric mean and arithmetic mean. **The product is the weight used**, `w = min(1, Bel × F × M × H)`.
  The other three are shown as a band; the arithmetic mean is one of the four, not the headline. A weight per
  horizon, `w_h = w × T(h)`, re-ranks signals and scenarios at 1, 2 and 3 years.
- **Signed impact.** Each signal also gets an impact from −100 to +100: favourable or unfavourable for ABB relay
  demand and delivery. Sign = direction × polarity of what it measures; size = materiality × min(1, sum of the
  six theme loadings / A_ref), with A_ref = 1.5 (ASSUMPTION). A signal with no recorded direction has impact 0.
- **Signal market map** on the Signals page: weight against impact, filters for segment, region, signal type and
  time horizon, four quadrants (Critical risks, Strategic opportunities, Risks to monitor, Small opportunities),
  a table view, and a detail panel with source, counter-evidence, a conditional recommendation text and
  Approve / Edit / Reject (they log a confirm, comment or dispute).
- **Recommended move** (3 to 4 conditional moves, each "Do in any case" or "Only if the trigger happens", with
  trigger signals, cost if wrong and horizon), what changes if the runner-up wins, a next action with owner and
  due date, and a revisit date.
- **Historical data** ("Vanha data" in Finnish): 18 dated cards from the 2021–2023 chip cycle, replayed at five
  as-of dates using only what had been published by then, next to what happened. It is labelled *illustrative
  comparison, not validation and not a forecast* and has real limits (see below).
- **Changes since the last cycle** per signal, a negative-signals list, scheduled updates, notifications, signal
  tracking, an automatic scout for new signals (data centres only), and a cited assistant.
- **The minimum chain in one click path:** import the Fingrid Q3 demonstration item and see signal detection,
  source and counter-evidence review, the scenario update, the recommended move and the next action.

## Known limits

- Probabilities are a traceable ranking of today's evidence, not calibrated. Weights, priors, lead times, impact
  constants and recommendation templates are labelled ASSUMPTION.
- Oil and gas: two weaker sources (OG-001 and OG-006 are second-hand reports); the Brent cards are read as
  operator spending (measure `end_demand`), which is a choice; five cards are dated after the demo clock
  2026-10-03 and so count as fully fresh at that clock; the bullwhip inputs of BW-1, BW-3 and BW-4 are DEMODATA.
- Historical data: counter-evidence exists for 9 of the 18 cards, 16 of 18 excerpts are paraphrases, six cards
  carry a date or figure not checked at the original page (`app/backend/data/historical/README.md`), and the
  scenario pool is the data-centre one. Five dates in one cycle cannot validate the method.
- Segments that were only a preview before (energy clusters, utility grids, renewable generation, industry,
  e-mobility, hydrogen, buildings) are removed from the menu and are later work.

## Contents

| Path | What |
|---|---|
| `docs/how-irma-weighs-evidence.html` | Plain-language explainer of the ensemble weight (credibility, currency, materiality, clamp, four formulas, attribution, horizon fit), the signed impact and the map, the scenario calculation, and the segments and historical data, with diagrams, an interactive calculator and worked examples from the real data. Open it in any browser |
| `docs/SOLUTION.md` | The full solution document: market insight, signal portfolio (data centres, oil and gas, historical data), problem definition, AI concept (weight, impact, scenarios, recommended move, signal map), prototype walkthrough, pitch, self-score, open questions for ABB |
| `DEMO.md` | The demo script for the current flow (about 7 minutes), a 30-second version and the likely judge questions with honest answers |
| `app/backend/engine/` | Deterministic computation: ensemble signal weights and horizon fit (`weights.py`), signed impact (`impact.py`), scenario probabilities, the recommended move (`recommend.py`), signal changes and the negative list (`changes.py`), the historical as-of comparison (`historical.py`), bullwhip metrics |
| `app/backend/agents/` | Nine agents (collector, demand, supply, bullwhip, counter-evidence, scenario, recommendation (code), interpretation, explainer), the scout, and the guardrail that strips purchase, quantity and order-timing language from model text |
| `app/backend/data/` | Data-centre data (`worlds/1`, 37 cards with the scout-found one; nine candidate situations in `scenario_archetypes.json`, templates in `recommendations.json`), the oil and gas segment (`segments/oilgas/`: 10 cards, 10 counter-evidence cards, eight situations, templates, bullwhip inputs), the historical data set (`historical/chipcycle.json` with its `README.md`), replayed agent outputs. Every value is labelled SOURCE, DEMODATA or ASSUMPTION |
| `app/backend/main.py` | FastAPI API (including `/api/segment`, `/api/historical`), hourly update scheduler (configurable), notifications, daily history, settings, static front end |
| `app/frontend/` | Irma interface: overview (banner, current situation, sub-menu, chart and assistant, recommended move, market summary, historical panel), signals (market map and detail panel, lists, import), signal pages with weight attribution, scenarios, notifications, settings. English and Finnish. ABB red and white theme with the IRMA logo |
| `app/tests/` | 223 tests: weights, impact, scenarios, recommendation and its wording, changes, segments, oil and gas data, historical data and as-of rule, scout, web verification, API |

## Run

```bash
pip install -r app/requirements.txt
```

```bash
./app/run.sh
```

On Windows, run `app\run.bat` instead.

Then open http://localhost:8000. If port 8000 is already taken, choose another one, for example `PORT=8765 ./app/run.sh` (on Windows: `set PORT=8765` before `app\run.bat`).

Optional environment variables:

- `ANTHROPIC_API_KEY` — enables live classification, counter-evidence and briefs with Claude (`ABB_MODEL`, default `claude-opus-5-5`), including web search: incoming items are verified against their primary source, counter-evidence is searched on the web, and on every update cycle a scout searches for new signals and adds only those that pass strict checks (reliable publisher, quote found on the page, recent, on-theme, corroborated, sufficient weight). All of it is limited to an editable domain allowlist (Settings → Web search). Accepted signals are saved in `app/backend/data/worlds/1/additions.json`. Without a key the agents run in replay/heuristic mode and say so in the trace.
- `AGENT_MODE=replay` — force replay mode even with a key.
- `DEMO_TODAY=2026-10-03` — freeze the clock so freshness values match the document. It applies to the current data set only; the Historical data set is fixed at its own reference date, 2023-07-01.

## Deploy to Vercel

Vercel finds the app with the project's Root Directory set either to the repository root (`index.py` and `pyproject.toml` there) or to `app` (`app/pyproject.toml` points to `backend/main.py`). Both list the dependencies and Python 3.13.

1. Import the GitHub repository at https://vercel.com/new. Keep the root directory and the detected settings, and deploy.
2. Optional environment variable under Settings › Environment Variables: `DEMO_TODAY=2026-10-03` freezes the clock to match the demo.

The Vercel deployment never uses an API key. Agents always run on replayed output there, even if `ANTHROPIC_API_KEY` is set, so a public link cannot run paid calls. Live agents run only locally (`./app/run.sh` with the key in your terminal).

On Vercel the code is read-only, so settings are saved under `/tmp/irma` and reset when the instance restarts. The hourly scheduler and the startup scout are off there (`IRMA_BACKGROUND=0`); "Run update now" in Settings recomputes on request.

## Test

```bash
cd app && DEMO_TODAY=2026-10-03 python3 -m pytest tests -q
```

## Principles enforced in code

1. The LLM reads and classifies; code computes every number (`engine/`).
2. The recommendation is written by code, not by a model: conditional, qualitative moves from labelled templates, matched to real signal ids, with no quantities, order points or order dates ("The planner decides"). A regex guardrail (`agents/llm.py`) still strips purchase, quantity and order-timing language from any model-generated text.
3. Every signal carries a source, date, provenance label, lead-time assumption and linked counter-evidence.
4. An unchallenged signal is capped at weight 0.6; a disputed signal is halved; both are logged. A weight never exceeds 1, however many confirmations pile up.
5. Four scenarios are always shown with their evidence for and against; entropy is displayed as the uncertainty measure, and the 12, 24 and 36 month rankings are shown as assumption-dependent, not as verdicts.
6. The four situations shown are the most likely of the segment's candidates (nine for data centres, eight for oil and gas) given the current signals; the ranking is visible. Scheduled updates write one probability point per day; notifications fire only on user-defined thresholds; locking a signal tracks it more closely without changing its weight.
7. The signed impact is computed by code from the card's `direction`, `measures`, materiality and six theme loadings, and is labelled ASSUMPTION (A_ref and the polarity of each measure). The model never sets it.
8. The historical comparison uses only items published on or before each as-of date, and the recorded outcome is shown beside the result, never used in it.
