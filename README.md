# Irma — weak-signal scenario monitor for ABB Distribution Solutions

Hackathon prototype (Junction Vaasa 2026, ABB Distribution Solutions challenge).
Segment: data centres. Region: Nordics + Europe, with the US as comparison. Horizon: 12–36 months.

The system reads open-source signals about data-centre demand and electronic-component supply,
weighs them with an ensemble formula the user can inspect (credibility with corroboration, currency,
materiality, the planner's view, and a fit to the 12, 24 and 36 month horizon), keeps four scenarios in
parallel, actively attaches counter-evidence to every strong signal, and from the leading scenario
composes a **recommended move and a next action** in conditional, qualitative form. The move has no
quantities, order points or order dates, because open data cannot see ABB's contracts, allocations and
cash. The planner decides.

## What it does

- **37 signal cards** in the current world situation (35 sourced, 1 DEMODATA placeholder, 1 internal
  placeholder), each with source, date, reliability grade, lead time and linked counter-evidence; 7 point
  against growth and are listed in a negative-signals list with the counter-evidence behind growth-supporting cards.
- **Ensemble weight** `w = min(1, Bel × F × M × H)`, with a band across four aggregators, an attribution
  of the discount, and a weight per horizon `w_h = w × T(h)` that re-ranks signals and scenarios at 1, 2 and 3 years.
- **Four scenarios** out of nine candidate situations, with probabilities, entropy, evidence for and against.
- **Recommended move** (3 to 4 conditional moves, no-regret or contingent, with trigger signals, cost if
  wrong and horizon), a hedge for the runner-up, a next action with owner and due date, and a revisit date.
- **Changes since the last cycle** per signal, a real region filter, scheduled updates, notifications, signal
  tracking, an automatic scout for new signals, and a cited assistant.
- **The minimum chain in one click path**: import the Fingrid Q3 demonstration item, see signal detection,
  source and counter-evidence review, the scenario update, the recommended move and the next action.

## Contents

| Path | What |
|---|---|
| `docs/how-irma-weighs-evidence.html` | Plain-language explainer of the ensemble weight (credibility, currency, materiality, clamp, band, attribution, horizon fit) and the scenario calculation, with diagrams, an interactive calculator and worked examples from the real data. Open it in any browser |
| `docs/SOLUTION.md` | The full solution document: market insight, signal portfolio, problem definition, AI concept (including the recommended move), prototype walkthrough, pitch, self-score, open questions for ABB |
| `DEMO.md` | The 3-minute demo script ordered by judging weight, a 30-second version and the likely judge questions with honest answers |
| `app/backend/engine/` | Deterministic computation: ensemble signal weights and horizon fit, scenario probabilities, the recommended move (`recommend.py`), signal changes and the negative list (`changes.py`), bullwhip metrics |
| `app/backend/agents/` | Eight agents (collector, demand, supply, bullwhip, counter-evidence, scenario, interpretation, explainer), the scout, and the guardrail that strips purchase, quantity and order-timing language from model text |
| `app/backend/data/` | Nine candidate situations (`scenario_archetypes.json`, priors sum to 1), recommendation templates (`recommendations.json`), two mock worlds (`worlds/1` public data, 37 cards with the scout-found one; `worlds/2` constructed downturn, 24 cards), replayed agent outputs. Every value is labelled SOURCE, DEMODATA or ASSUMPTION |
| `app/backend/main.py` | FastAPI API, hourly update scheduler (configurable), notifications, daily history, settings, static front end |
| `app/frontend/` | Irma interface: overview (70/30: current situation with horizon chips and region filter, and the recommended move; signal list, scenario charts, assistant), signals (changes, negative list, import), signal pages with weight attribution, scenarios, notifications, settings. ABB red/white theme with the IRMA logo |
| `app/tests/` | 82 tests: weights, scenarios, recommendation, changes, scout, web verification, API |

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
- `DEMO_TODAY=2026-10-03` — freeze the clock so freshness values match the document.

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
6. The four situations shown are the most likely of nine candidates given the current signals; the ranking is visible. Scheduled updates write one probability point per day; notifications fire only on user-defined thresholds; locking a signal tracks it more closely without changing its weight.
