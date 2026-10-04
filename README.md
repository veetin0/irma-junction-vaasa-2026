# Irma — weak-signal scenario monitor for ABB Distribution Solutions

Hackathon prototype (Junction Vaasa 2026, ABB Distribution Solutions challenge).
Segment: data centres. Region: Nordics + Europe, with the US as comparison. Horizon: 12–36 months.

The system reads open-source signals about data-centre demand and electronic-component supply,
weighs them with a formula the user can inspect, keeps four scenarios in parallel, actively attaches
counter-evidence to every strong signal, and writes what each scenario would mean for ABB in
conditional form. It does not recommend purchases, quantities or order points. The planner decides.

## Contents

| Path | What |
|---|---|
| `docs/how-irma-weighs-evidence.html` | Plain-language explainer of the weight and scenario calculations, with diagrams and worked examples. Open it in any browser |
| `docs/SOLUTION.md` | The full solution document: market insight, signal portfolio, problem definition, AI concept, prototype, pitch, self-score, open questions for ABB |
| `app/backend/engine/` | Deterministic computation: signal weights, scenario probabilities, bullwhip metrics |
| `app/backend/agents/` | Eight agents (collector, demand, supply, bullwhip, counter-evidence, scenario, interpretation, explainer) and the recommendation guardrail |
| `app/backend/data/` | Nine candidate situations (`scenario_archetypes.json`), two mock worlds (`worlds/1` public data, `worlds/2` constructed downturn), replayed agent outputs. Every value is labelled SOURCE, DEMODATA or ASSUMPTION |
| `app/backend/main.py` | FastAPI API, hourly update scheduler (configurable), notifications, daily history, settings, static front end |
| `app/frontend/` | Irma interface: overview (signal list, scenario tabs with one large chart, market summary, assistant), signals with import, scenarios, notifications, settings. ABB red/white theme with the IRMA logo |
| `app/tests/` | Engine and pipeline tests |

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

The repository root holds what Vercel needs: `index.py` loads the app, and `pyproject.toml` lists the dependencies and Python 3.13.

1. Import the GitHub repository at https://vercel.com/new. Keep the root directory and the detected settings, and deploy.
2. Optional environment variables under Settings › Environment Variables: `DEMO_TODAY=2026-10-03` freezes the clock to match the demo; `ANTHROPIC_API_KEY` turns on the live agents.

On Vercel the code is read-only, so settings and new scout signals are saved under `/tmp/irma` and reset when the instance restarts. The hourly scheduler and the startup scout are off there (`IRMA_BACKGROUND=0`); use "Run update now" and "Search now" instead. A public deployment with an API key lets anyone run paid agent calls, so set a spending limit in the Anthropic Console or deploy without a key.

## Test

```bash
cd app && DEMO_TODAY=2026-10-03 python3 -m pytest tests -q
```

## Principles enforced in code

1. The LLM reads and classifies; code computes every number (`engine/`).
2. No agent recommends. A regex guardrail (`agents/llm.py`) strips purchase language from any generated text.
3. Every signal carries a source, date, provenance label, lead-time assumption and linked counter-evidence.
4. An unchallenged signal is capped at weight 0.6; a disputed signal is halved; both are logged.
5. Four scenarios are always shown with their evidence for and against; entropy is displayed as the uncertainty measure.
6. The four situations shown are the most likely of nine candidates given the current signals; the ranking is visible. Scheduled updates write one probability point per day; notifications fire only on user-defined thresholds; locking a signal tracks it more closely without changing its weight.
