# Simulated implications: which sectors look designed?

> New in the 2026-11 restructure. Simulates the logical implications of [Model 10](04_chance_vs_design.md) and the lock-in models ([1](01_lockin_bargaining.md), [8](03_lockin_and_remediation.md)), then checks which sectors' contract histories carry them. Code: `scripts/amendment_reasons.py`, [`simulations/simulate_amendments.py`](../../simulations/README.md). Output: [`simulations/results/`](../../simulations/results/), `data/processed/amendment_reasons_summary.json`. Figures: [S1–S3](../../simulations/figures/) and [Figure 5](../../figures/fig5_amendment_fingerprints.png).

## 1. Why simulate instead of regress

A regression of amendments on sector reports *that* sectors differ. It cannot say whether the difference has the shape a theory implies. Here each theory is turned into a data-generating process. Its implications are derived by simulation, and each sector is checked against the *pattern* of implications.

The comparison point matters. Contracts differ in how amendment-prone they are, and that alone produces many patterns that look strategic. A rising chance of "one more amendment" is one example. So every world and every sector is compared with a **pure-chance world matched to its own amendment-count distribution**: a negative binomial with the same mean and variance, and arrivals at a constant rate over the term. A fingerprint counts only if it departs from *that* benchmark.

## 2. Five worlds

| World | Process |
| --- | --- |
| A. Chance, heterogeneous | Each contract draws its own amendment rate (gamma mixing); arrivals uniform over the term; sizes independent |
| B. Design, no lock-in | A + vendor-level scope gaps (Model 10's \(g\)) that surface at implementation |
| C. Design with lock-in spiral | B + each amendment raises dependence \(k\), which raises the hazard of the next amendment, the margin (size) on later amendments, and the odds of an end-of-term extension instead of re-competition |
| D. Chance + routine renewals | A + planned end-of-term renewals that do not depend on the contract's history |
| E. Mixed | Half the contracts as A, half as C |

Parameters are illustrative: 300 vendors and about 4,500 contracts per world, with 40 replicates of each matched chance world.

## 3. Implications, derived rather than assumed

z-scores against each world's own matched chance world. **+** and **−** mark |z| ≥ 2; **·** marks no detectable difference.

| Fingerprint | B gaps | C lock-in | D renewals | E mixed |
| --- | :---: | :---: | :---: | :---: |
| First amendment in first 25% of term | **+** (30) | · | − | − |
| An amendment in last 10% of term or later | − | **+** (20) | **+** (40) | **+** |
| Late lift: P(late \| earlier) ÷ P(late \| none) | **+** | − | − | − |
| Next gap shorter (before term end) | − | · | · | · |
| Second amendment larger than first | · | **+** (8.8) | · | **+** |
| Vendor share of variance in amendment risk | **+** (31) | **+** (17) | · | · |

In world C, dependence saturates after about four amendments. An earlier version without that cap let a few contracts run away with hundreds of amendments; the cap is the realistic case, and it changed two conclusions (see point 3).

What the simulation teaches:

1. **A rising "one more amendment" curve is not evidence of design.** Chance alone produces it when contracts differ in how amendment-prone they are ([S2](../../simulations/figures/s2_continuation_curves.png)). In the data, the observed curve actually sits *below* the matched-chance curve after the first amendment.
2. **End-of-term amendments do not separate design from routine renewals.** Lock-in (C) and planned renewals (D) both produce them. Early amendments are the signature of implementation-stage scope gaps (B) only.
3. **Two fingerprints do the separating:**
   - **Vendor share of risk** separates *design* (B or C) from chance and renewals (A, D).
   - **Escalating amendment size** separates *lock-in* (C) specifically, because the bargaining margin grows with dependence.

   Acceleration between amendments appears only when dependence grows without limit, so it is reported as supporting evidence, not as a test.

[S1](../../simulations/figures/s1_simulated_histories.png) shows sample contract histories from each world.

## 4. What the sectors show

Sectors are tech subsectors, tech program domains and non-technology contracts. Timing and size fingerprints use Chicago, Oregon ORPIN and Cook County, which record dated amendments with dollar changes. Bulk-migration dates (more than 200 amendments on one date) are dropped. The vendor share adds Washington and is estimated within ledger × department cells, against a within-cell permutation null.

**Every sector shares one regime.** All sectors have far fewer early amendments than chance (z from −5 to −131) and far more end-of-term amendments (+10 to +116). This is the renewal signature, shared by worlds C and D. The implementation-gap world (B) is negatively correlated with every sector. **Where design is present, it does not appear as scope gaps discovered early. It appears around renewal and in how amendment sizes grow.**

**Evidence tiers.** Effects are observed minus matched chance ([S3](../../simulations/figures/s3_lockin_fingerprints.png)):
- **Tier 1:** vendor-level design + escalation (lock-in) + acceleration in support.
- **Tier 2:** design + escalation.
- **Tier 3:** vendor-level design only.

| Tier | Sector | Contracts | Next amendment larger (chance ≈ 0.50) | Vendor share (chance ≈ 0.02) | Next gap shorter (supporting) |
| :---: | --- | ---: | ---: | ---: | ---: |
| 1 | **Software & SaaS** | 17,482 | **0.66** (+0.16) | **0.16** (+0.14) | **0.71** |
| 1 | **General enterprise IT** | 17,646 | **0.64** (+0.15) | **0.17** (+0.13) | **0.56** |
| 1 | General technology | 20,759 | **0.54** (+0.04) | **0.29** (+0.27) | **0.53** |
| 2 | Administration & finance (tech) | 2,602 | **0.66** (+0.15) | **0.21** (+0.15) | 0.43 |
| 2 | Non-technology | 278,380 | **0.53** (+0.03) | **0.15** (+0.14) | 0.50 |
| 3 | Hardware & telecom | 4,942 | 0.56 | **0.15** (+0.11) | **0.68** |
| 3 | Health care (tech) | 7,710 | 0.55 | **0.19** (+0.17) | **0.69** |
| 3 | Public assistance (tech) | 9,483 | 0.49 | **0.30** (+0.29) | **0.56** |
| *thin* | Environment, IT services, public safety, transportation (tech) | 2,000–3,000 each | | | |

Bold values are significantly above matched chance (z ≥ 2). "Thin" means fewer than 30 contracts with the timed or sized amendment pairs the tests need.

**Software & SaaS is the sector most aligned with the lock-in theory**, with general enterprise IT a close second. Both show vendor-level concentration *and* amendments that grow from one to the next (+15–16 points above chance), with acceleration in support. General technology meets the same tests but with a small escalation effect (+4 points).

**Non-technology contracts show the weakest lock-in signal.** Escalation is barely above chance (+3 points), and there is no acceleration. Their pattern is closest to routine renewals plus vendor-level differences.

**Public assistance, health care and hardware show a vendor component without escalation.** That fits vendor-level differences (who does the work, or a gap strategy) more than a margin that grows with lock-in.

## 5. Why amendments happened: stated reasons

`scripts/amendment_reasons.py` classifies the reason text that ledgers record: Washington's modification field and Chicago revision notes. Oregon and Cook County amendment text repeats the contract title. Each amendment is coded as chance, design-indicative, ambiguous, neutral or uninformative.

| | Washington | Chicago |
| --- | ---: | ---: |
| Amendments | 72,264 | 96,984 |
| With informative reason text | 39,038 (54%) | 3,363 (3%) |
| …of which ambiguous: "extend", "add funds", "renewal", no cause | 36,932 | 2,822 |
| Chance: statutes (e.g. ESHB 2642, ESSB 5693), grants, COVID, caseload | 539 | 1 |
| Design-indicative: change orders, missing original funding, rate increases, bridge to re-procurement | 97 | 22 |
| Neutral: planned options, corrections, cost-of-living increases granted by the city | 1,470 | 518 |

**The records mostly do not say why.** Over 90% of informative reasons are "extend" or "add funds" without a cause, and explicitly causal reasons are rare: 659 of 169,248 amendments in these two ledgers. Where a cause is stated, chance outnumbers design, but recording is selective. Agencies have reasons to write down a statute number and few reasons to write "work we omitted from the original scope".

So stated reasons cannot rank sectors, and the fingerprints above carry the weight. Reading the amendment *documents* would settle more. Chicago links every record to its documents, but they sit behind a JavaScript viewer, and collecting them means rendering about 69,000 pages on the city's server. That is a deliberate next step, not something to run casually.

## 6. Limits

- **Matched chance assumes a constant hazard over the term.** Real chance needs could cluster, for example at fiscal-year starts. The acceleration fingerprint therefore uses only amendments before the last 10% of the term, so end-of-term clustering cannot drive it.
- **The vendor share mixes strategy with specialization.** Cells hold ledger and department fixed, but vendors within a department can still do different kinds of work.
- **Escalation uses the first two positive dollar changes.** A large first amendment followed by a small top-up counts against escalation even under lock-in.
- **World parameters are illustrative, not estimated.** The signatures are qualitative implications. The next step is to estimate the world parameters by simulated method of moments, sector by sector, so that each sector gets an estimated designed share \(\sigma\) rather than a pattern match.
