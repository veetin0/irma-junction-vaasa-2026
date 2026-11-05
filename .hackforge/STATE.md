# State
- Phase: build M4–M6 (directive 11) in progress. M4.1 merged on main (c869321). Rate limit hit 2026-11-05 ~12:50, resets 13:50; the 4 data/engine builders (M4.2a oil and gas cards, M4.2b oil and gas scenarios, M4.3a chip-cycle data, M4.3b historical engine) wrote nothing and must be relaunched, then M4.4 wiring, M5, M6
M4 done and merged (gate green, 216 tests, MILESTONE 4). Next: M5 (M5.1 UI, M5.2 map, M5.3 reco wording), then M6.
- Profile: standard (auto: 10 h, team of 1, existing entry being improved) · Models: research sonnet / architect opus / judge opus / build sonnet / craft sonnet / verify sonnet
- Deadline: none set · Time budget 10 h
- Current milestone / wave: —
- Done: init, inventory, directives, brief, RULES.md, baseline judge 7.2, weighting research, OPTIONS, DECISION (pending)
- Next: user review; optional items in LOOP.md
- Best metric vs baseline: tests 33/33 · Latest mock score: 8.1 (7.2 before build)
- Escalations / de-escalations: kickoff scaled down. There is an existing entry and concrete directives, so the improvement options are designed inline instead of by 3 architect agents.; builder A on opus (hardest math)
- Risks & open questions: recommendation directive vs the no-recommendation guardrail (see DIRECTIVES note); 2026-10-07 ~23:00 all 3 M1 builders hit the session rate limit with nothing committed, relaunched 23:33 on new branch names (old empty branches hf/m1-data, hf/m1-reco, worktree-agent-* left for the user to delete)
- Loop backlog (from M2 screenshots):
  - The recommendation card is too tall: about 300 px gap under the left column at 1440. Compact the moves (one line each, details behind a disclosure).
  - The market summary repeats "New information processed" notifications; dedupe.
  - "Latest changes" is empty after a demo import or scout: show what the import changed.
  - /api/run has no recommendation step.
  - /api/method weight_formula is stale.
  - CE short_fi is English.
- Questions for the user: add a LICENSE (which one)? The verifier flagged that none exists. docs/VOICEOVER.md describes the old 6:33 video from the original folder; keep it, update it or drop it?
