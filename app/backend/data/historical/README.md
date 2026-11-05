# Historical chip-cycle dataset (contract C11, M4.3a)

`chipcycle.json` is the master dataset for the "Historical data" world: 18 sourced signal cards about the 2021-2023 semiconductor cycle, five as-of snapshots, counter-evidence, and what happened next. It is an illustrative comparison, not validation and not a forecast (the label is in `meta.label`, EN and FI).

## Structure

| Key | Content |
|---|---|
| `meta` | id, titles (EN/FI), label, `reference_date` (2023-07-01, ASSUMPTION), schema note, snapshot choice, data-label note |
| `snapshots` | `["2021-07-01", "2022-01-01", "2022-07-01", "2023-01-01", "2023-07-01"]` (the C11 list) |
| `snapshot_index` | per snapshot: `as_of`, `card_ids` and `evidence_ids` known on that date, and a short EN/FI note. Derived from the dates; a test keeps it equal to the `observed_at <= as_of` filter |
| `cards` | `HS-001` to `HS-018`, same fields as `data/worlds/1/signals.json` (six axes, `observed_at`, `value`, `history`, ...) plus `excerpt_kind` (`quote` or `paraphrase`) and, where the date needed a caveat, `date_note` |
| `evidence` | counter-evidence `HCE-001` to `HCE-010` (`against`, `claim`, `source`, `reliability`, `strength`, and `observed_at` = source date) |
| `outcomes` | one per snapshot: `after`, `text` EN/FI, `source` (name, url, date). The source date is later than `after` |

## Rules the data follows

- `observed_at` is the publication date of the source (`observed_at == source.date`). A snapshot at date d uses only cards with `observed_at <= d`, history points `<= d` (every history point is already `<= observed_at`), and evidence with `observed_at <= d`. There is no hindsight in any snapshot list; `tests/test_chipcycle_data.py` checks all of it.
- Every card value is `SOURCE` with a URL. No `DEMODATA`, no invented number. Where a number is a midpoint of a published range it says so in the label (for example PC DRAM -5 to -10% is -7.5). `history` holds only published values; most event cards have none, and the series continue on later cards (SIA sales HS-003, HS-007, HS-017; Susquehanna lead times HS-004, HS-013; DRAM prices HS-006, HS-011, HS-015).
- Judgement fields are labelled as in world 1: `lead_months_rationale` starts with `[ASSUMPTION ...]`; `strength`, `axes`, `direction`, `classification` and `reliability` are the builder's reading (`ASSUMPTION`), not source data. Axes use the world-1 convention: positive = tighter supply, stronger demand, hoarding or amplification, supportive policy; negative = the opposite.
- `excerpt_kind` says whether `excerpt` is a verbatim quote (HS-006, HS-008, both fetched from the page) or a paraphrase of the source (the rest, written from search summaries). Do not present a paraphrase as a quotation.
- Counter-evidence is partial: 10 entries against 9 cards. They come from the same research pass (other cards' sources, or the card's own release), not from a dedicated counter-search per card. `ce_searched` is `true` only on cards that have counter-evidence; the other nine cards were not searched. Say this if asked.

## Snapshots (half-yearly, ASSUMPTION)

Half-yearly gives one phase of the cycle per interval and 3-6 new cards each: shortage building (4 cards), peak sales and first inventory warnings (8), memory prices turning and policy responses (11), destocking (16), trough with the AI counter-trend (18). The engine's early snapshot ranks supply and sales cards first; the late one ranks the AI data-centre card next to the sales decline.

## Sources and dates to double-check

| Card | Source | Note |
|---|---|---|
| HS-001 | Embedded Computing Design, Renesas fire | date 2021-03-31 taken from the search summary; fire itself 2021-03-19 |
| HS-003, HS-007, HS-017 | SIA press releases | dates from Digitimes reprints / slugs (2021-05-04, 2021-11-01, 2023-05-02); verify against the SIA pages |
| HS-004 | The Star (Bloomberg) on Susquehanna | 17 weeks in April 2021; data is a paid index, only the press figure is used |
| HS-010 | ITPro | announcement date 2022-03-17 from a search summary; the article date was not checked; the source gives no investment amount, so the card value is "1 datacenter region" |
| HS-012 | I-Connect007 reprint of the White House fact sheet | secondary host, reliability B |
| HS-013 | Data Center Knowledge (Bloomberg) | fetched; 26.3 weeks Sept 2022, 2022-10-17 |
| HS-014 | Meta Form 8-K exhibit | capex ranges taken from a search summary of the Q3 2022 release, not read in the filing; verify before quoting |
| HS-016 | TechPowerUp quoting Micron's release | secondary host |

Outcomes: the 2024-02-05 SIA release (2023 total USD 526.8 bn, -8.2%) was fetched; the others rest on the search summaries above.

## Research budget used

About 30 research calls (25 searches and 5 page fetches, one of which failed with HTTP 403; the fetched pages are TrendForce 4Q21, Dell'Oro, Data Center Knowledge and SIA 2023). That is over the 25-call target. Not researched: Ukraine neon supply (2022), Nordic power prices 2022, ECIA distributor sentiment for 2021-2023 (its record would be a strong bullwhip card; add if wanted, with a source).

## Next step (M4.3b)

`worlds/2/signals.json`, `evidence.json` and `bullwhip.json` are generated from this file, or committed beside it with a test that they agree. `bullwhip.json` inputs are not in this file; they need their own sourced series (DRAM spot-to-contract spread, MCU lead times) or `DEMODATA` labels.
