# Better signal weighting for Irma: methods, and a concrete ensemble design

Focus: a better formula for signal weights, "maybe many formulas combined into one result".
Scope read: `app/backend/engine/weights.py`, `engine/scenarios.py`, `engine/archetypes.py`, `data/scenario_archetypes.json`,
`docs/how-irma-weighs-evidence.html`, `data/worlds/1/signals.json` (32 signals), `evidence.json` (31 counter-evidence items).
Prototype numbers below were computed by a scratch script in `/tmp` (no project file touched), world 1, today = 2026-10-07.

---

## 1. Key findings (what changes our solution)

1. **The current formula is already a recognised method, just not named.** `R * (1 - C)` is exactly the belief that a claim is true when
   a source supports it with strength R and counter-evidence attacks it with strength C, combined with Yager's rule (Dempster-Shafer family):
   `Bel = s(1 - c)`. And the counter-evidence noisy-OR is the Dempster combination of independent simple-support functions. So we can
   keep the arithmetic, name it correctly in the docs (defensible to judges), and *extend* it (corroboration, plausibility band) without
   changing today's numbers when there is only one source.
2. **Average estimators of the same quantity, multiply conditions of different things.** This one rule decides the whole design.
   The forecasting-combination literature says simple averages beat fitted weights when you have no outcome data (we have none).
   The intelligence/composite-indicator literature says conjunctive conditions ("is it true AND still current AND big enough") must be
   non-compensatory. So: product across the different conditions, mean inside any component that has several estimators of one thing.
   A pure geometric-mean ensemble was tested and **rejected**: it lifts the Fingrid card (3 counter-claims) from 0.147 to 0.527 and DRAM
   from 0.33 to 0.69, i.e. it hides doubt, and it would invalidate every threshold (0.15 admit, 0.25 strong, 0.4 notify, 0.6 cap).
3. **Lead time is stored (`lead_months`, `type`, `classification`) but never used by the engine** (grep: only `pipeline.py` stores it,
   `main.py` only exposes `horizon_months [12, 36]`). A horizon-fit factor T(h) makes the 12/24/36-month view real: prototype shows the
   scenario ranking at 36 months differs from 12 months (`nordic_concentration` 0.405 vs `expansion_tight` 0.399 at 36m; at 12m
   `expansion_tight` 0.467 vs 0.309). The 36m gap is razor-thin and flips with the kernel width, so show it as a range, not a verdict.
4. **Real bug / hole in the current code:** `signal_weight` has no final clamp. With R=F=S=1, C=0 and a "confirm" annotation H=1.5 the
   weight is 1.5, outside [0,1]. The cap only applies to unchallenged signals. Add `min(1.0, ...)`.
5. **The scenario update is already a weighted logarithmic opinion pool / product of experts** (Genest and Zidek) and, read as
   Bayes, `exp(k * w * r)` is a per-signal odds multiplier (Good's weight of evidence). We can show "this signal multiplies the odds of
   scenario X by x1.4 (1.5 dB)" with zero new numbers. Because softmax is shift-invariant, a signal that fits all scenarios equally
   already has no effect: that is ACH's "no diagnostic value" rule for free. Add a display-only diagnosticity score; do **not** put it in
   the weight (double counting).
6. **Data limits are the binding constraint, not the maths.** History exists for only 10 of 32 signals, of which 8 are `DEMODATA` and
   only 2 are `SOURCE`. A z-score-of-change component is therefore dormant until real histories are loaded. `DEMODATA` history must
   never drive a weight. There is no field for corroborating sources, event/cluster id, or lead-time range (min/max); these are the
   three cheap additions that unlock the rest.
7. **Hiltunen's three dimensions give the UI grouping for free** (signal = visibility and corroboration, issue = size and timing,
   interpretation = doubt and human view). Presentation only, not extra arithmetic.

---

## 2. What the current code does (facts)

- `w = R * F * S * (1 - C) * H`; R A/B/C = 1.0/0.7/0.4; F = 0.5^(age/half-life by update frequency: 14/30/60/120/240/90 d);
  S = classified strength; C = min(0.8, 1 - prod(1 - R_ce * strength_ce)); H = product of annotation multipliers (confirm 1.2,
  dispute 0.5, comment 1.0) clamped [0.25, 1.5]; unchallenged (`ce_searched` false) capped at 0.6; rounded to 4 decimals.
- Scenario layer: `L_s = ln(prior_s) + k * sum_i w_i * r_is`, softmax, top 4 of 9 archetypes renormalised; k = 1.5 from
  `scenario_archetypes.json` (scenarios.py default 2.0 is not what runs; the how-it-works page says 1.5, consistent).
- Today's distribution (31 evaluable): max 0.573, median 0.155, 10/32 at or above 0.25. Five multiplicative factors compress weights hard:
  a signal scoring 0.8 on every factor gets 0.33.
- Fields available per signal: `reliability` A/B/C, `source_class`, `source{name,url,date}`, `update_frequency`, `observed_at`, `strength`,
  `classification` (structural 16 / cyclical 9 / mixed 7), `type` (leading 18 / lagging 8 / coincident 6), `lead_months` (3..48) plus free-text
  rationale, `history` (+`history_label`), `counter_evidence[]`, `ce_searched`, `annotations[]`, `tracking{checks,last_checked}`, `axes`.
  Counter-evidence items: `reliability`, `strength`, `against`, `source`.
- Lead-time rationales quote ranges for 8 signals; the ratio high/low is 1.5, 1.67, 2, 2, 2, 3, 3, 3 (median 2). This anchors the kernel
  width below.

---

## 3. Method catalogue

Notation: `R` source reliability in [0,1], `s,c` support/counter masses, `t` age in days, `h` horizon months, `L` lead months.

### 3.1 Source reliability grading (Admiralty Code / NATO intelligence grading)
Two independent ratings: source reliability A-F and information credibility 1-6 (1 = confirmed by other independent sources,
2 = probably true, 3 = possibly true ... 6 = cannot be judged). ICD 203 asks analysts to describe source quality, access, bias,
possible deception and timeliness separately from the judgement.
Formula: lookup then numeric map, `R = {"A":1.0,"B":0.7,"C":0.4}[grade]` (existing; the numbers are ASSUMPTION, no standard assigns them).
The credibility digit is exactly what corroboration and counter-evidence measure, so it can be *derived by code* and displayed as
"A1 / B3" on the card.
Fields: `reliability` (have). Credibility digit: needs corroboration list (missing) and `counter_evidence`/`ce_searched` (have).
Source: Admiralty code, ICD 203.

### 3.2 Bayesian log-likelihood-ratio updating (Good's weight of evidence)
Posterior odds = prior odds x Bayes factor; `ln BF` is additive over independent evidence.
`odds_multiplier = exp(k * w * r)`; `deciban = 10*log10(odds_multiplier) = 4.343 * k * w * r`.
Irma's update already has this shape; `r` is an analyst-set direction, not a measured likelihood ratio, so it is *calibrated-looking, not
calibrated*. Kass-Raftery reading: BF 1-3.2 "bare mention", 3.2-10 "substantial", 10-100 "strong". With k=1.5 and |r| up to ~0.5, one
perfect signal gives BF about 2.1, i.e. "bare mention", which is the honest message: no single weak signal is decisive.
Caveat: independence. Correlated evidence is double counted (naive-Bayes overconfidence); see 4.7 for the cluster fix.
Fields: have everything. Source: Bayes factor, Weight of evidence.

### 3.3 Recency decay (half-life)
Exponential: `F = 0.5 ** (age / T_half)` (existing). Alternative with a hard expiry: MISP polynomial
`score = base * (1 - (t/tau) ** (1/delta))`, plus "sightings" that reset the clock when an indicator is re-confirmed.
Recommendation: keep exponential (explainable as a half-life); adopt the MISP idea of **refresh on re-confirmation**:
`age_eff = today - max(observed_at, last_confirmed)`.
Fields: `observed_at`, `update_frequency` (have); `tracking.last_checked` exists but is null everywhere (missing in practice).
Source: MISP decaying indicators, arXiv 1803.11052.

### 3.4 Lead-time alignment with the decision horizon
No standard "weight" exists; the standard idea is that a leading indicator turns before the reference series by a stable lead (OECD CLI:
6-9 months). Our own construction: the signal's effect on ABB demand arrives about `L` months after observation, with log-normal timing
uncertainty. Full design in section 4.4.
`T(h) = exp(-0.5 * (ln(h/L) / s)**2)` for "not arrived yet", and persistence once arrived if the signal is structural.
Fields: `lead_months`, `classification` (have); `lead_min`/`lead_max` structured (missing, only prose).
Source: OECD CLI FAQ (lead concept). The kernel itself is ASSUMPTION.

### 3.5 Corroboration counts
Independent sources reporting the same fact raise credibility. Noisy-OR (Pearl): `s = 1 - prod_j (1 - R_j)` over *independent* sources.
This is identical to Dempster's rule on simple-support functions with Shafer discount alpha = R_j. Source independence is the whole game
(syndicated copies of one press release are one source); ICD 203 and Admiralty digit 1 both say "independent".
Fields: **missing**. Add optional `corroboration: [{name,url,reliability,derived_from}]` filled by the scout; code counts a source only
if its publisher domain differs and `derived_from` is empty. Default (no list) = single source, so numbers do not change.
Source: Noisy-OR (Pearl 1988), Dempster-Shafer, ICD 203.

### 3.6 Dempster-Shafer evidence theory
Mass on subsets, belief `Bel` (lower bound) and plausibility `Pl = 1 - Bel(not A)` (upper bound); Dempster's rule normalises away
conflict K, which gives absurd results under high conflict (Zadeh's two-doctor example). Yager's rule moves conflict mass to
"unknown" instead.
Use only at **claim level on the frame {true, false}** (one signal), never across 9 scenarios:
```python
s = 1 - prod(1 - R_j for j in independent_sources)          # support (3.5)
c = min(0.8, 1 - prod(1 - R_ce * strength_ce))               # attack (existing noisy-OR, cap = ASSUMPTION)
bel = s * (1 - c)                                            # Yager: conflict s*c goes to "unknown"
pl  = 1 - c * (1 - s)                                        # upper bound
```
`bel` is the credibility component; `[bel, pl]` is a displayable uncertainty band. With one source and no counter-evidence bel = R.
Fields: as 3.5 plus existing. Source: Dempster-Shafer theory.

### 3.7 Weighted ensembles: geometric vs arithmetic mean of sub-scores
OECD/JRC handbook: arithmetic mean is fully compensatory (a failure in one component is offset by strength in another); geometric mean
is "less compensatory" and penalises unbalanced profiles; neither is neutral, the choice is a statement about whether trade-offs are
acceptable. For *conditions that must all hold* we want non-compensatory. Formulas:
```python
prod = c1 * c2 * c3                      # strictest, scale-compressing (current)
gm   = (c1 * c2 * c3) ** (1/3)           # rescales to component scale, weak on doubt
am   = (c1 + c2 + c3) / 3                # fully compensatory
mn   = min(c1, c2, c3)                   # weakest link
```
Measured on four real cards (cred, fresh, mat): Fingrid prod 0.147 / gm 0.527 / min 0.284 / am 0.576; Google 0.573 / 0.831 / 0.79 / 0.832;
DRAM 0.327 / 0.689 / 0.40 / 0.737; Uptime 0.495 / 0.791 / 0.60 / 0.806. The spread is the *structural model uncertainty*; we show it
rather than hide it (section 4.6). Source: OECD/JRC Handbook.

### 3.8 Analysis of Competing Hypotheses (ACH)
Heuer: build a hypothesis x evidence matrix, judge **diagnosticity** (evidence consistent with all hypotheses has little or no diagnostic
value), work across the matrix, and favour the hypothesis with the *least inconsistent* evidence rather than the most confirming evidence.
Formulas (display / cross-check only, not in w):
```python
diagnosticity_i = max(r_is for s) - min(r_is for s)                 # 0 = fits every scenario equally
inconsistency_s = sum(w_i * -min(0, r_is) for i)                    # ACH-style score; compare ranking with p_s
```
Flag when the probability leader is not the ACH least-inconsistent scenario ("the leading scenario is also the most contradicted").
Fields: `scenario_links` / `axes` (have). Source: Heuer ch. 8, CIA tradecraft primer.

### 3.9 Signal-to-noise: z-score of change vs history
Robust version (Iglewicz and Hoaglin, NIST handbook): `z_mod = 0.6745 * (x_latest - median(prev)) / MAD(prev)`; conventional flag at |z|>3.5.
```python
S_z = min(1.0, abs(z_mod) / 3.5)          # 3.5 is the published outlier threshold, not our number
```
Dormant unless `history_label == "SOURCE"` and enough prior points (min prior n = 6 is an ASSUMPTION: below that MAD is unstable; MAD = 0 -> fall back).
Fields: `history` (22 of 32 empty, 8 DEMODATA, 2 SOURCE): **almost entirely missing**. Source: NIST handbook.

### 3.10 Foresight weak-signal literature (Ansoff; Hiltunen)
Ansoff (1975): strategic discontinuities are rarely sudden; they are preceded by faint, ambiguous indicators that give lead time if
interpreted. Hiltunen (2008): the "future sign" has three dimensions, **signal** (visibility, amount of it), **issue** (the content and
real-world size, e.g. a heavily publicised practice present in only 1% of stores is a loud signal on a small issue) and
**interpretation** (the receiver's understanding); a weak signal scores low on all or most of them.
Mapping, as UI grouping only: signal = corroboration + currency, issue = materiality + horizon fit, interpretation = counter-evidence + human view.
No formula; the value is that it justifies a three-group breakdown and warns against treating media volume as strength.
Source: Ansoff via CMR, Hiltunen (JFS and Aalto records).

### 3.11 How forecast ensembles combine models
- Simple average is hard to beat ("forecast combination puzzle"): estimating combination weights from small samples adds more error than
  the bias it removes (Smith and Wallis 2009; Stock and Watson). We have no outcome data, so **equal weights**.
- Linear pool (arithmetic mean of probabilities) vs logarithmic pool (geometric, `p ∝ prod p_i^w_i`); log pool is externally Bayesian
  (Genest and Zidek 1986). Irma's softmax update is a log pool.
- Tetlock-style aggregation can *extremise* a combined probability when forecasters hold partly independent information
  (Satopää et al. 2014, logit model). Not applicable here: our weights are not forecasters' probabilities.
- Later, when outcomes exist, evaluate with proper scoring rules (Brier/log; Gneiting and Raftery 2007) before changing any weight.
Fields: none. Source: combination reviews and papers below.

---

## 4. Proposed ensemble design

### 4.1 Components (five), and what each ensembles

| # | Component | Question it answers | Formula | Inside it |
|---|---|---|---|---|
| 1 | **Credibility** `Bel` | Is the claim true? | `s*(1-c)` (3.6) | noisy-OR over independent sources (3.5), noisy-OR over counter-evidence (existing), Yager combination |
| 2 | **Currency** `F` | Is it still current? | `0.5 ** (age_eff / T_half)` (3.3) | refreshed by re-confirmation |
| 3 | **Materiality** `M` | How big is the move relative to noise? | `mean(S_llm, S_z)` over the estimators available (3.9) | a true ensemble of two estimators of one quantity |
| 4 | **Human view** `H` | What does the planner say? | existing product of annotation multipliers, clamp [0.25, 1.5] | unchanged |
| 5 | **Horizon fit** `T(h)` | Does it speak about month 12, 24 or 36? | kernel (4.4) | persistence rule by `classification` |

Reliability grade A/B/C stays, but now lives inside component 1.

### 4.2 Combination into one weight in [0,1]

```python
def weight(sig, h=None):
    bel, pl   = credibility(sig)                 # component 1
    F         = currency(sig)                    # component 2
    M         = materiality(sig)                 # component 3
    H         = human_factor(sig)                # component 4
    w = min(1.0, bel * F * M * H)                # horizon-free headline weight (NEW: clamp)
    if not sig["ce_searched"]:
        w = min(w, UNCHALLENGED_CAP)             # 0.6, invariant
    return w if h is None else w * horizon_fit(sig, h)   # w_h in [0, w]
```

Why this combination:
- Credibility, currency, materiality are different, jointly necessary conditions: product is the correct conjunction (and is what the
  how-it-works page already teaches), so the headline weight keeps today's scale and today's thresholds (0.15 admit, 0.25 strong, 0.4
  notify, 0.6 cap) stay valid. With one source, no history and horizon unused, **the new weight equals the old weight to the digit**
  (regression test), apart from the clamp at 1.
- Where several estimators measure the same quantity (materiality; corroborating sources) we pool them: mean for estimators,
  noisy-OR for independent confirmations. Equal weights because there is nothing to fit them on.
- Horizon fit multiplies last and separately so one card has one headline `w` plus three horizon values `w_12, w_24, w_36`.
- Alternatives tried and rejected: geometric-mean ensemble (rescales everything, hides doubt, breaks thresholds), arithmetic mean
  (compensatory, Fingrid would score 0.58), fitted/learned weights (no outcomes; combination puzzle), Dempster across 9 scenarios
  (Zadeh conflict, no mass assignments exist), explicit likelihood ratios (no measured ones).

### 4.3 Invariants and labelling

| Invariant | How it is kept |
|---|---|
| Unchallenged capped at 0.6 | applied after the product, before the horizon multiplier; `w_h <= w` so it holds at every horizon |
| Disputed signal halved | `H` carries x0.5 per dispute, inside the product, so `w(disputed) = 0.5 * w(undisputed)` whenever neither value is bound by the 0.6 cap or the clamp (same as today). Unit-test that ratio |
| Weight in [0,1] | final `min(1.0, .)` (new) |
| All numbers computed in code | LLM supplies only grades, strength, direction, classification, corroboration flags, lead range; every arithmetic step is code |
| No invented numbers | every constant below is listed with a label and justification; any estimator without valid input is *skipped*, never defaulted |

Labels carried per component, rule: the component takes the worst label of its inputs (SOURCE < DEMODATA < ASSUMPTION), and `DEMODATA` inputs
are **excluded** from the headline weight (shown greyed only).

| Constant / input | Label | Justification |
|---|---|---|
| R: A=1.0, B=0.7, C=0.4 | ASSUMPTION | existing, no standard numeric map for Admiralty letters |
| Counter cap 0.8 | ASSUMPTION | existing; keeps at least 20% of belief so one doubt cannot erase a signal |
| Half-lives 14/30/60/90/120/240 d | ASSUMPTION | existing; tied to publication cadence |
| Unchallenged cap 0.6; human x1.2 / x0.5 / [0.25,1.5] | ASSUMPTION | existing |
| S (strength) | ASSUMPTION (LLM judgement) unless `S_z` from SOURCE history | judgement from card |
| Outlier threshold 3.5, constant 0.6745 | SOURCE | Iglewicz and Hoaglin via NIST |
| Min prior history points = 6 for `S_z` | ASSUMPTION | MAD is unstable on short series; below it the estimator is skipped |
| Kernel width s = ln 2 | ASSUMPTION | median high/low ratio of the 8 quoted lead ranges is 2; analysts' ranges are systematically too narrow (Soll and Klayman 2004, intervals sometimes ~40% of calibrated width), so we widen to ln 2 and show s = ln 1.5 and ln 3 as sensitivity |
| Equal weights across estimators | ASSUMPTION | combination puzzle; no outcome data |
| Independence = different publisher domain and no `derived_from` | ASSUMPTION | cheap proxy for circular reporting |
| `lead_months` | existing ASSUMPTION labels in rationale | unchanged |

### 4.4 Connecting each signal to the 12/24/36-month horizon through lead time

Horizons are the same three yearly buckets the archetypes already use (`demand_yearly` and `supply_yearly` have 3 entries, years 1-3).
Interpretation: `L` = months from *now* until the signal's effect shows up in ABB relay demand or deliverable supply.

```python
S_LOG = math.log(2)                                   # ASSUMPTION, see 4.3
def horizon_fit(sig, h):                              # h in {12, 24, 36}
    L, cls = sig["lead_months"], sig["classification"]
    sym = math.exp(-0.5 * (math.log(h / L) / S_LOG) ** 2)
    if h < L:                                         # effect not arrived inside this horizon
        return sym
    persist = {"structural": 1.0, "cyclical": sym, "mixed": (1 + sym) / 2}[cls]
    return persist                                    # structural effects stay; cyclical ones fade
```
Rule of thumb it encodes: a 3-month DRAM price (cyclical) informs year 1 only; a signed grid-connection agreement (structural, L=30)
speaks mostly to years 2-3; structural "research anchors" with L=36 speak to year 3 and stay relevant after. Table (s = ln 2):

| Signal | L | class | T12 | T24 | T36 |
|---|---|---|---|---|---|
| SIG-001 Fingrid signed agreements | 30 | structural | 0.42 | 0.95 | 1.00 |
| SIG-003 Google EUR 13 bn | 20 | structural | 0.76 | 1.00 | 1.00 |
| SIG-007 DRAM contract prices | 4 | cyclical | 0.28 | 0.04 | 0.01 |
| SIG-028 Uptime survey | 12 | mixed | 1.00 | 0.80 | 0.64 |

Scenario layer per horizon: run the existing `select_scenarios` three times with `weights[sig] = w_h`. Prototype (existing priors, k=1.5, today 2026-10-07):

| | expansion_tight | nordic_concentration | expansion_easing | deferred_tight | entropy |
|---|---|---|---|---|---|
| today (no horizon) | 0.499 | 0.361 | 0.106 | 0.035 | 0.77 |
| 12 m, s=ln2 | 0.467 | 0.309 | 0.148 | 0.076 | 0.86 |
| 24 m | 0.418 | 0.390 | 0.159 | 0.034 | 0.82 |
| 36 m | 0.399 | 0.405 | 0.166 | 0.030 | 0.82 |

Read it honestly: horizon weights shrink total evidence, so the prior pulls harder (entropy up), and the 36m leader changes with the kernel
(s = ln 3 gives expansion_tight 0.423 vs nordic 0.393 at 36m; s = ln 1.5 gives nordic 0.414 vs 0.385). Show the horizon view with the
sensitivity range and say "leader at 36m not robust". These are DEMODATA-influenced outputs, not forecasts.

Upgrade path when structured ranges exist (`lead_min`, `lead_max`): replace the kernel with the share of the lead interval that falls
inside the bucket (h-12, h] (or reached by h for structural). No kernel constant left.
Known data ambiguity: lagging signals carry `lead_months` 24-48 (research anchors). Define the field in the docs as "months until the
effect reaches ABB demand or supply" for every type, or exempt `type == "lagging"` anchors from T (T = 1).

### 4.5 Extra checks that are not in the weight

- `diagnosticity` and `inconsistency` (3.8) shown on scenario view; warning when leader differs from the ACH least-inconsistent scenario.
- Correlated-evidence discount at scenario level (optional): signals sharing an `event_id` or publisher domain are clustered; scale each
  cluster so its total weight is the noisy-OR of its members, no new constant:
  `w_i' = w_i * (1 - prod_j(1 - w_j)) / sum_j w_j`. Prevents Fingrid agreements, Fingrid queue and Fingrid grid code counting as three
  independent votes. (Today 3 signals come from datacenterdynamics.com, 2 each from iea.org, trendforce.com; overlaps are mild, so this is a
  robustness feature, not urgent.)
- Odds multiplier chip per contribution: `exp(k*w_h*r)`, and decibans.

### 4.6 Showing the per-component breakdown

1. **Discount waterfall, order-independent.** Start at 1.00 and show each factor. Attribute the total loss by log-share
   `share_k = ln(1/c_k) / sum_k ln(1/c_k)` (a product is a sum of logs, so the shares add to 100% and do not depend on order).
   Real cards: Fingrid 0.147 = credibility 66% / currency 23% / materiality 12% of the loss; Google 0.573 = 42/39/19; DRAM 0.327 = 82/4/15;
   Uptime 0.495 = 18/9/73. A user instantly sees *why* a weight is low (doubt, age, or small move).
2. **Hiltunen grouping** of the same bars: Signal (source support s, currency), Issue (materiality, horizon fit), Interpretation (counter-evidence
   1-c, human view).
3. **Credibility band** `[Bel, Pl]` as a thin bar; width = what is unknown.
4. **Horizon chips** `12m 0.42 | 24m 0.95 | 36m 1.00` with the lead time and rationale on hover.
5. **Structural sensitivity band**: report `w` as headline but show the range over aggregators prod/gm/min/am (3.7) and whether the signal's rank
   in the top 5 is stable ("rank stable under all four rules" vs "depends on how factors are combined"). This is the honest use of "many
   formulas combined": the ensemble of *aggregators* informs uncertainty, the product stays the number.
6. **Label chips** per input (SOURCE/DEMODATA/ASSUMPTION) and the worst-label rule on each bar; formula string in the existing `formula`
   field, e.g. `w = min(1, Bel*F*M*H); Bel = s(1-c); w_h = w*T(h)`.
7. Return shape (extends the existing dict): `components{credibility{s,c,bel,pl,grade_code}, currency, materiality{estimators[], spread},
   human, horizon{12,24,36}}`, `loss_share`, `sensitivity{prod,gm,min,am}`, `labels`, `unchallenged_cap_applied`.

### 4.7 Implementation order (cheapest first)
1. Clamp to 1; rename formulas in docs (Yager/noisy-OR, Good's weight of evidence); regression test that new == old with one source.
2. `horizon_fit` + per-horizon scenario runs + sensitivity band (uses data we already have).
3. Breakdown API/UI (loss share, Hiltunen groups, label chips).
4. Add optional fields: `corroboration[]`, `event_id`, `lead_min/lead_max`, real `history` for Fingrid, DRAM, copper; then switch on corroboration and `S_z`.
5. Only after outcomes exist: back-test with proper scoring rules; do not tune weights before.

---

## 5. Uncertain or unverified points
- Hiltunen's exact definitions come from abstracts and secondary summaries (Aalto/JFS pages); I did not read the full paper. DOI not given.
- Heuer ch. 8 wording confirmed only through search summaries (the CIA PDF did not parse); the diagnosticity principle is well established.
- Yager equivalence `Bel = s(1-c)` is my derivation from the standard rule (checked algebraically: m(A)=s(1-c), conflict s*c to the frame); the
  existing code adds the 0.8 cap on c, which is not part of Yager.
- Gneiting and Raftery 2007 and Stock and Watson 2004 cited from memory/search listing; DOI of the former: 10.1198/016214506000001437 (unverified).
- The kernel shape, persistence rule and `s = ln 2` are our design choices (ASSUMPTION), not literature.

---

## 6. Sources

- [Admiralty code (Wikipedia)](https://en.wikipedia.org/wiki/Admiralty_code)
- [ICD 203 Analytic Standards (ODNI, via FAS)](https://irp.fas.org/dni/icd/icd-203.pdf)
- [Bayes factor (Wikipedia): Kass-Raftery scale, Good's weight of evidence](https://en.wikipedia.org/wiki/Bayes_factor)
- [Decaying Indicators of Compromise (arXiv 1803.11052)](https://arxiv.org/pdf/1803.11052)
- [MISP: decaying of indicators](https://www.misp-project.org/2019/09/12/Decaying-Of-Indicators.html)
- [OECD composite leading indicators FAQ (lead of 6-9 months)](https://search.oecd.org/sdd/compositeleadingindicatorsclifrequentlyaskedquestionsfaqs.htm)
- [Dempster-Shafer theory (Wikipedia): belief, plausibility, Zadeh, Yager, discounting](https://en.wikipedia.org/wiki/Dempster%E2%80%93Shafer_theory)
- [Pearl, Probabilistic Reasoning in Intelligent Systems (noisy-OR)](https://shop.elsevier.com/books/probabilistic-reasoning-in-intelligent-systems/pearl/978-0-08-051489-5)
- [OECD/JRC Handbook on Constructing Composite Indicators](https://knowledge4policy.ec.europa.eu/sites/default/files/jrc47008_handbook_final.pdf)
- [Heuer, Psychology of Intelligence Analysis (CIA), ch. 8 ACH](https://www.cia.gov/resources/csi/static/Pyschology-of-Intelligence-Analysis.pdf)
- [CIA Tradecraft Primer: structured analytic techniques](https://www.cia.gov/resources/csi/static/Tradecraft-Primer-apr09.pdf)
- [NIST e-Handbook: modified z-score (Iglewicz and Hoaglin)](https://www.itl.nist.gov/div898/handbook/eda/section3/eda35h.htm)
- [Ansoff 1975, Managing Strategic Surprise by Response to Weak Signals (CMR)](https://cmr.berkeley.edu/1975/02/18-2-managing-strategic-surprise-by-response-to-weak-signals)
- [Hiltunen, The Signification Process of the Future Sign (JFS)](https://jfsdigital.org/articles-and-essays/2011-2/vol-16-no-1-september/articles/the-signification-process-of-the-future-sign)
- [Hiltunen, aaltodoc record on the future sign](https://aaltodoc.aalto.fi/items/35593471-b2ed-4670-8445-cfa9d0da1502)
- [Smith and Wallis 2009, A simple explanation of the forecast combination puzzle](https://econpapers.repec.org/RePEc:bla:obuest:v:71:y:2009:i:3:p:331-355)
- [Forecast combinations: an over 50-year review (arXiv 2205.04216)](https://arxiv.org/pdf/2205.04216)
- [Genest and Zidek 1986, Combining probability distributions (linear vs logarithmic pools)](https://projecteuclid.org/journals/statistical-science/volume-1/issue-1/Combining-Probability-Distributions-A-Critique-and-an-Annotated-Bibliography/10.1214/ss/1177013825.full)
- [Satopää et al., combining probability forecasts and extremizing (arXiv 1501.06943)](https://arxiv.org/pdf/1501.06943)
- [Soll and Klayman 2004, Overconfidence in interval estimates](https://doi.org/10.1037/0278-7393.30.2.299)
- [Sitra weak signals explorer (Finnish foresight tool, context)](https://www.sitra.fi/en/tool/weak-signals-explorer/)
