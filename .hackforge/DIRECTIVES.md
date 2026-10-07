# Team directives
Directives override HackForge defaults, never an official rule.

| # | Directive | Source |
|---|---|---|
| 1 | Write a better formula for weight calculation; maybe several formulas combined into a single result | prompts/00-team.md |
| 2 | Add a recommendation section that shows ABB what they should do, based on the program | prompts/00-team.md |
| 3 | Show the latest signal changes in the signal list | prompts/00-team.md |
| 4 | Connect the signals to the time horizon | prompts/00-team.md |
| 5 | Add a negative-signals list on the Signals page | prompts/00-team.md |
| 6 | Make the UI a little clearer while still showing all the relevant info | prompts/00-team.md |
| 7 | Split the Current Situation overview 70/30, with the recommended move on the main page | prompts/00-team.md |
| 8 | Modalities: suggest (propose at the decision checkpoint) | hackforge.yaml |
| 9 | Standing project constraints (from memory of the original build): no invented numbers (SOURCE / DEMODATA / ASSUMPTION labels), balanced counter-evidence, structural vs cyclical separated, the human decides, "LLM reads and classifies, code computes", no filler language, keep the llm.py guardrail | user memory |
| 10 | Don't push anywhere or add the original GitHub remote; this is the v2 copy (preview port 8766) | user memory |

Note on 2 vs 9: the old rule "never recommend purchases or quantities" meets the brief, which asks for a "decision recommendation for ABB → next action". Resolution: recommendations are conditional, qualitative decision moves (what to prepare, review, watch, or with whom to talk), each tied to scenario probability and its triggers, with no order quantities or timing. The guardrail stays.
