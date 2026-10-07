# Brief

## Problem (one paragraph)
ABB Distribution Solutions (protection and control: relays, breakers, switchgear) wants to see changes, fluctuations and turning points in electrification markets earlier, and turn them into information that supports manufacturing, procurement, capacity and supply-reliability decisions. The chain: global trend → market data → weak signal → scenario → business impact → decision. The goal is not to predict sales figures.

## Challenge owner — what they actually want
Planners and S&OP / procurement leads who need earlier warning than the order book (which, according to the mentors, lags the market by 18+ months), with balanced evidence and scenarios, and a clear recommended next action that stays under human control.

## Given
- Data: public data only (team's choice). ABB slides on ecosystem, challenge and vision in challenge/data/.
- APIs / SDKs / hardware: none given.
- Starter code: none. Our own existing entry, Irma (app/ and docs/), is the starting point.

## Deliverables and deadline
- Deadline (with time zone): not set (the event was 2026-10-03; this is a post-event v2 improvement run, 10 h budget).
- Submission format: six areas (Business & market insight, Data & signal portfolio, Decision problem, AI solution concept, Demonstrable prototype) + modern digital presentation.
- Prototype minimum: New data → signal detection → source and counter-evidence review → scenario → decision recommendation for ABB → next action.

## Assumptions we are making
- A1 — Scope stays the same: data-centre segment, Nordics + Europe (US as comparison), 12–36 months.
- A2 — "Decision recommendation" = a conditional, qualitative move with its trigger and confidence, never order quantities (conservative reading that satisfies both the brief and the ABB mentor feedback).
- A3 — Vercel deploy stays key-less, so every new feature must work in replay mode.

## Ask the organisers
- Q1 — Is a qualitative, conditional recommendation (prepare / watch / review) enough for the "decision recommendation" step, or do judges expect quantified ones?
