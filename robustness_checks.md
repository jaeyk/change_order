# Robustness checks

This note tests the vendor-strategy findings in [strategies.md](strategies.md) one at a time. Each check changes one thing (the sample, a definition or the method) and records whether each headline claim survives.

- **Code:** [robustness/run_checks.py](robustness/run_checks.py) (R0–R14) and [robustness/stratified.py](robustness/stratified.py) (R15).
- **Results:** `robustness/results/checks.json`, `stratified.json` and `r16_jumps.json`.
- **Data:** the run of 2026-11-08: 694,856 contracts, of which 269,787 come from the seven ledgers with dated amendments that the fingerprints use.

## Bottom line

**The most important result is R15.** When sectors are compared **within the same ledger** instead of pooled, several headline findings shrink or disappear. The reason is that sectors are spread unevenly across ledgers, and the ledgers differ a lot:

- **Washington dominates technology.** Most technology contracts with dated amendments are Washington's: 8,216 of the 11,986 software contracts.
- **Washington's ledger behaves differently in every sector.** Its labelled amendments escalate more, grow more and come earlier, for non-technology contracts too.

So pooled sector contrasts partly measure *which ledger a contract comes from*.

| Claim (from strategies.md) | Verdict | Why |
| --- | --- | --- |
| C1. Software & SaaS escalates most (2nd amendment larger than 1st) | **Holds, but much smaller** | Pooled excess +16.5 points; within ledgers, software beats non-tech by **+3.7 points [+0.2, +7.0]**. Software leads in most leave-one-out samples, but not in Chicago alone, and not above $25k (where IT services edges it). |
| C2. Software & SaaS has the largest vendor effect | **Partly holds** | Within ledgers, software's vendor share exceeds non-tech's (+0.13). General technology (+0.11) and IT services (+0.11) are similar, so software is not uniquely highest. Fails in 7 of 17 variants. |
| C3. IT services is the only sector with early (buy-in) amendments | **Does not hold beyond Washington** | Within-ledger gap +11 points, all from Washington, where every sector amends early. In Chicago and Oregon, IT services amends *less* early than non-tech. |
| C4. Every sector amends late, far above chance | **Holds outside Washington** | True in Chicago, Oregon and Cook County. Washington's labelled amendments come early in every sector, and dropping Chicago or Oregon tips the pooled result. |
| C5. Software compounds most (value after 6 amendments) | **Does not hold within ledgers** | Within ledgers, software ≈ non-tech (+0.03 on the log scale, CI spans 0). Hardware & telecom (+0.31) and general technology (+0.28) compound *more* than non-tech. The pooled software lead came from Washington, where *all* sectors compound fast. |
| C6. No follow-on award excess | **Holds** | Excess within ±1.8 points for every sector and every de-duplication window except none (which counts split orders). |
| C7. Resellers in hardware & telecom are amended less | **Holds** | Lower in all five ledgers with enough resellers. |
| C8. Holdovers are concentrated in software & general-tech documents | **Holds** | 32/94 vs. 2/45, exact p = 0.00005 (Chicago documents only). |

## The checks, one by one

Claims are marked ✓ (holds), ✗ (fails) or — (not testable: too few contracts).

### R0. Baseline

Same definitions as `simulations/` and `strategies.md`. All of C1–C5 hold in the pooled sample.

### R1. Leave one ledger out

| Dropped ledger | C1 | C2 | C3 | C4 | C5 |
| --- | :-: | :-: | :-: | :-: | :-: |
| Chicago | ✓ | ✓ | ✗ | ✗ | ✓ |
| Cook County | ✓ | ✓ | ✓ | ✓ | ✓ |
| Oregon | ✓ | ✓ | ✓ | ✗ | ✗ |
| Oregon Lottery | ✓ | ✓ | ✓ | ✓ | ✓ |
| Oregon Treasury | ✓ | ✓ | ✓ | ✓ | ✓ |
| WA Dept. of Health | ✓ | ✓ | ✓ | ✓ | ✓ |
| Washington State | ✓ | ✗ | ✗ | ✓ | ✗ |

**Outcome.**
- **Washington matters most:** without it, software's snowball falls from 3.19× to 2.04× (below hardware, 2.60×) and IT services' early amendments disappear (21% early against 45% by chance).
- **Chicago and Oregon carry the late-amendment pattern (C4).**
- **C1 survives every single drop.**

### R2. One ledger at a time

| Only this ledger | C1 | C2 | C3 | C4 | C5 |
| --- | :-: | :-: | :-: | :-: | :-: |
| Chicago | ✗ | ✓ | — | ✓ | — |
| Oregon | ✓ | ✗ | — | ✓ | ✗ |
| Washington State | ✓ | ✓ | ✗ | ✗ | ✓ |
| Cook County, Oregon Lottery, Oregon Treasury | mostly — | | | | |

**Outcome.**
- **Chicago:** software does not escalate (−7 points, 54 pairs) but has the largest vendor effect (0.43).
- **Oregon:** software escalates most (+29 points, 61 pairs) but has a weak vendor effect (0.16, below general technology's 0.28).
- **Washington:** software leads both measures, but non-tech escalates almost as much (+15 vs. +18 points), and Washington amends *early* in every sector, so C3 and C4 do not apply.

### R3. Award-size thresholds

| Minimum original award | C1 | C2 | C3 | C4 | C5 |
| --- | :-: | :-: | :-: | :-: | :-: |
| $25,000 | ✗ | ✗ | ✗ | ✓ | ✗ |
| $100,000 | ✗ | ✗ | ✗ | ✓ | ✗ |

**Outcome.** Above $25k:
- **Escalation:** software's escalation excess falls from +16.5 to +9.7 points, and IT services (+15.8, only 76 pairs) overtakes it. Software still escalates more than hardware (+5.6), general tech (+2.8) and non-tech (+5.6).
- **Vendor share:** IT services leads.
- **Snowball:** IT services (2.71×, n = 29) edges software (2.42×) and hardware (2.39×).
- **Early amendments:** IT services' early pattern reverses (38% early against 50% by chance).

Much of software's escalation lead comes from small contracts (licence renewals, subscriptions).

### R4. Start years 2005–2019

Removes old contracts with partial histories and recent ones that are right-censored.
- **C1, C4 and C5 hold.**
- **C2 and C3 fail.** Software's vendor share drops to 0.19, below general technology (0.31) and IT services (0.46). IT services' early share falls below chance.

### R5. Outliers

Drops contracts with more than 30 amendments or a final value more than 20× the original. C1, C2, C4 and C5 hold; C3 fails.

### R6. Strict software definition

Keeps only software contracts whose titles name software, licences, SaaS, cloud, ERP or CRM (7,381 of 11,986).
- **C1 holds and strengthens** (+18.7 points).
- **C5 holds** (3.54×).
- **C2 fails:** the strict set's vendor share is 0.20, below general technology's 0.28.

### R7. Escalation measured as last vs. first amendment

P(last positive amendment > first). Software +17.7 points against −7.0 to +5.1 for the rest. **C1 holds.**

### R8. Snowball statistic and cohort

Value after K = 4, 6 and 8 amendments, by geometric mean and by median.
- **C5 holds in 5 of 6 variants.** The exception is the K = 6 median, where IT services (3.05×, n = 31) edges software (2.97×).
- **All of these are pooled**, so they inherit the composition problem that R15 exposes.

### R9. Permutation test

Shuffles the software and non-tech labels *within* each ledger, 1,000 times.
- **Observed gap:** +10.3 points; 95th percentile of the null: +9.6; **p = 0.016**.
- **Most of the pooled gap is composition.** Even random labels that keep each ledger's sector mix produce a gap close to 10 points.
- **The part beyond composition is small**, which R15 measures directly.

### R10. Matched-chance random seeds

Re-runs the matched-chance benchmark for early and late amendments with three other seeds. The z-scores move by a few points; C3 and C4 hold in every seed. **The pooled results are not artifacts of the simulation draw.** Their dependence on ledger composition is a different problem, which R15 addresses.

### R11. Follow-on awards: de-duplication window

Repeat awards to the same vendor are collapsed within each window, then compared with a shuffled award order. The table shows the excess, in percentage points.

| Window | Software | Hardware | IT services | General tech | Non-tech |
| --- | ---: | ---: | ---: | ---: | ---: |
| None | +10.3 | +11.1 | +12.4 | +9.0 | +16.4 |
| Month | −0.1 | −0.3 | +1.7 | +0.3 | −0.2 |
| Quarter | −0.6 | −1.3 | +0.5 | −0.2 | −0.2 |
| Year | −0.8 | −1.8 | −0.7 | −0.6 | −0.2 |

**Outcome.**
- **Without de-duplication**, the large excess is split purchase orders.
- **With any window**, no sector shows a follow-on excess above 2 points. **C6 holds.**

### R12. Resellers in hardware & telecom, within ledger

Amendment rate for resellers vs. all other vendors, by ledger.

| Ledger | Resellers | Others |
| --- | ---: | ---: |
| New York City | 15.4% (n = 2,359) | 26.2% (n = 6,589) |
| Oregon Judicial | 3.3% (n = 390) | 33.0% (n = 646) |
| Oregon Lottery | 4.6% (n = 564) | 7.4% (n = 688) |
| Oregon Treasury | 0.0% (n = 839) | 2.0% (n = 49) |
| Washington State | 8.7% (n = 69) | 24.8% (n = 1,234) |

**C7 holds in every ledger.**

### R13. Holdover documents: exact test

Software and general-technology documents cite "extended until a new contract is awarded" in 32 of 94 cases, against 2 of 45 non-technology documents.
- **One-sided Fisher exact p = 0.00005. C8 holds.**
- **Scope:** all documents are from Chicago, so the comparison is within one ledger by construction. The coder's 92% agreement was measured on the documents used to build its rules.

### R14. Out of sample: ledgers added after the theory and simulations

These ledgers were not used to build the theory, the simulations or `strategies.md`.

| Ledger | Software amended | Non-tech amended | Software escalation | Non-tech escalation |
| --- | ---: | ---: | ---: | ---: |
| District of Columbia | 65% | 58% | +8.4 pts | +10.3 pts |
| New York City (Checkbook) | 23% | 30% | n/a (no amendment order) | n/a |
| WA Dept. of Health | 61% (n = 18) | 43% | n/a (too few) | −4.4 pts |

**Outcome.**
- **Neither new ledger reproduces a software lead.**
- **In DC,** software escalates slightly *less* than non-tech.
- **In New York City,** software is amended *less* often.

DC's escalation is measured by event order (option periods, then document versions) rather than by date, and its amendment counts include planned option exercises, so the comparison is approximate.

### R15. Within-ledger (stratified) comparisons

This is the key check. The table gives each sector's gap from non-tech **within the same ledger**, averaged across ledgers. Each ledger is weighted by the smaller of the two groups' sample sizes. The 95% intervals come from 300 bootstrap draws, resampling contracts within ledger.

| Quantity | Software & SaaS | Hardware & telecom | IT services | General technology |
| --- | ---: | ---: | ---: | ---: |
| Escalation (P(2nd > 1st)) | **+0.037** [+0.002, +0.070] | −0.017 [−0.070, +0.037] | −0.041 [−0.136, +0.038] | −0.003 [−0.043, +0.035] |
| Late amendment (last 10% of term) | **+0.165** [+0.147, +0.184] | **+0.093** [+0.063, +0.121] | +0.021 [−0.018, +0.055] | **+0.061** [+0.047, +0.076] |
| Early first amendment (first 25%) | **−0.099** [−0.118, −0.081] | −0.020 [−0.043, +0.004] | **+0.113** [+0.084, +0.144] | **−0.087** [−0.101, −0.075] |
| Vendor share of amendment risk | +0.129 | −0.014 | +0.111 | +0.110 |
| Log value after 6 amendments | +0.028 [−0.087, +0.151] | **+0.311** [+0.111, +0.487] | **+0.469** [+0.086, +0.824] | **+0.277** [+0.142, +0.411] |

**Bold** = 95% interval excludes zero.

**Vendor share has no interval.** A contract-level bootstrap duplicates contracts inside vendors and inflates the vendor share, so its intervals are invalid; a vendor-cluster bootstrap is still to do.

**Where the averages come from.** The per-ledger gaps are in `robustness/results/stratified.json`.
- **Software's late-amendment gap** comes almost entirely from Washington (+0.21; about 0 in Chicago, Oregon and Cook County).
- **IT services' early gap** is Washington-only.
- **Hardware's and general technology's snowball gaps** come from Chicago and Oregon.

### R16. Extreme single-step jumps

Drops the 57 contracts with any single amendment more than 100× the original award and above $1 million: Chicago 27, Oregon 16, Washington 7, DC 4 and Oregon Judicial 3. They include probable unit errors in DC, for example a $10 million staffing contract recorded as reaching $10.03 billion.
- **The snowball barely moves:** non-tech goes from 1.685× to 1.661×; software is unchanged.
- **Geometric-mean growth of amended contracts** changes in the third digit.
- **Medians and geometric means are robust to these records; sums and arithmetic means are not.** That is why `README.md` §5's mean-growth columns carry a warning.

## What changes in the story

1. **The headline lock-in result is weaker than reported.** Within ledgers:
   - software's escalation edge over non-tech is about **+4 points, not +16**;
   - software does not compound faster than non-tech;
   - its vendor concentration is shared with general technology and IT services.

   The strongest remaining support for software lock-in is qualitative and from one city: holdover extensions in Chicago's documents.
2. **Hardware & telecom and general technology compound more than non-tech within ledgers.** The earlier summary, built on pooled numbers, said the opposite.
3. **There is no robust buy-in pattern.** IT services' early amendments are a Washington feature.
4. **Late, renewal-style amendments describe Chicago, Oregon and Cook County, not Washington.** In Washington's labelled amendments, first amendments come early in every sector.
5. **Several findings are robust:**
   - no excess follow-on awards;
   - resellers in hardware are rarely amended;
   - holdovers are concentrated in technology documents;
   - software contracts are amended late more often than non-tech within ledgers (+16.5 points, mostly Washington).

## Checks not yet done

- **Vendor-cluster bootstrap** for vendor-share intervals.
- **Re-estimating the matched-chance benchmark within each ledger** separately, as R2 does, but for every fingerprint with intervals.
- **A sector × ledger interaction model** of amendment size and escalation, as an alternative to the R15 weighting.
- **Out-of-sample timing tests**, once a new dated ledger is added (Virginia eVA has no amendment dates; FPDS will).
