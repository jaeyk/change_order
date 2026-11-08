# Empirical plan: telling chance from design

> New in the 2026-11 restructure. Connects [Model 10](04_chance_vs_design.md) to the contract data in this repository. Numbers below come from `scripts/amendment_dynamics.py` (output: `data/processed/amendment_dynamics.json`) and `scripts/make_figures.py`, and use only ledgers that record amendment history (see the repository README, §6).

## 1. First look: what the data already say

These facts are descriptive. Each is consistent with design, but none rules out chance on its own.

**Amendments are not a constant-rate process.** If amendments arrived at a constant rate for every contract (a homogeneous Poisson count), the probability of one more amendment would *fall* as a contract accumulates them. In the data it *rises*.

| Prior amendments \(k\) | 0 | 1 | 2 | 3 | 5 | 9 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| P(another \| \(k\)), tech | 0.31 | 0.53 | 0.61 | 0.65 | 0.71 | 0.81 |
| P(another \| \(k\)), non-tech | 0.30 | 0.46 | 0.58 | 0.66 | 0.74 | 0.83 |
| Poisson with the same mean, tech | 0.57 | 0.36 | 0.26 | 0.20 | 0.14 | 0.08 |

The variance of amendment counts is 7.0× the mean for tech contracts and 13.4× for non-tech (a Poisson count would give 1×). Washington, Chicago, Cook County, Oregon ORPIN, Oregon Lottery and Oregon Treasury ledgers; 40,335 tech and 221,947 non-tech contracts.

Two explanations fit this, and Model 10 allows both:
- **Heterogeneity.** Some contracts are amendment-prone from the start (large \(g\), complex work).
- **State dependence.** Each amendment raises the chance of the next, for example through dependence \(k\) that grows with the relationship.

**Amendment rates cluster by vendor far beyond chance.** Among vendors with 20 or more contracts in a ledger, the spread of vendor amendment rates is 15.5× (Chicago), 11.8× (Oregon), 11.5× (Oregon Lottery) and 10.1× (Washington) what binomial chance would produce. This is consistent with a vendor-level strategy, but also with vendors specializing in different kinds of work.

**When first amendments arrive.**

| | Median days to first amendment | Within 180 days | In first quarter of term | In last 10% of term or later |
| --- | ---: | ---: | ---: | ---: |
| Tech | 312 | 35.1% | 29.6% | 38.7% |
| Non-tech | 304 | 40.3% | 36.0% | 38.4% |

Chicago, Oregon, Cook County, Washington and Oregon Treasury. Close to two in five first amendments come in the last tenth of the original term or after it, the signature of extensions and renewals (Model 10, extension 2). With Washington's dated amendments included, the median first amendment falls 67% (tech) and 61% (non-tech) of the way through the term, earlier than in the three-ledger version of this table.

**Most Washington amendments extend time or add money; few add scope.** Classifying Washington's amendment text gives extension 18,000 and funding 17,600 against scope 5,400 for non-tech; for tech, extension 4,100, funding 3,200 and scope 850. About half the rows have uninformative text ("Amendment") and stay unclassified.

**Value compounds with each amendment.** For a fixed group of contracts amended at least six times, typical value reaches 3.25× the original award for software & SaaS, 2.76× for hardware/telecom and 2.08× for general technology, against 1.75× for non-technology ([Figure 3](../../figures/fig3_amendment_snowball.png)).

## 2. Mapping model quantities to data

| Model quantity | Proxy available now | Better measure (needs new data) |
| --- | --- | --- |
| Amendment count over the lifecycle, \(\lambda_0+g\) | `amendment_count`, `amendments_normalized.csv` | Linked renewals and follow-on contracts to the same vendor |
| Award-to-final growth | `pct_growth`, Figure 3 | Same, net of indexed price escalation |
| Award weight on lifecycle cost, \(\phi\) | Procurement method (`procurement_method`): competitive vs. sole source vs. statewide or cooperative vehicle; contract term length | Solicitation scoring rules (lifecycle or total-cost-of-ownership criteria) |
| Scope review, \(d\) | None | Independent cost estimates; protest and clarification records |
| Dependence \(k\), portability \(p\) | Tech subsector; single vs. multiple award (`award_structure`); vendor role | Data-rights and transition clauses in contract documents |
| Lock-in bargaining surplus \(\Delta\) | Number of prior contracts with the same agency (incumbency) | Bids from replacement vendors at re-competition |
| Content of amendments | Washington modification text; Chicago revision descriptions | Amendment documents (scope restored vs. new requirement) |
| Chance shocks | Calendar dates of known statute and program changes | Program-change notices by agency |

## 3. Tests, in order of feasibility

> **Status (2026-11-08):** tests 1 and 2 are done in simulation form, not as regressions. See [07_simulated_implications.md](07_simulated_implications.md). The vendor component is estimated within ledger × department cells against a permutation null. State dependence is tested within contracts, by whether successive gaps between amendments shrink and successive amendments grow, which holds for any constant-rate contract regardless of its rate. Tests 3–6 remain.

1. **Count model with a vendor component.** Fit negative-binomial or Poisson-mixture models of amendment counts with exposure (contract duration). Use fixed effects for agency × commodity, and estimate a vendor random effect. Report how much overdispersion the vendor term absorbs *within the same type of work*. Prediction: a large vendor share points to design.
2. **Recurrent-event hazards.** Model the timing of successive amendments (Andersen–Gill or a gap-time model) with a contract-level frailty term. Test whether the hazard still rises with the number of prior amendments after the frailty absorbs heterogeneity. Prediction: state dependence remaining after frailty points to the lock-in spiral (Proposition 1).
3. **End-of-term clustering.** Measure amendments in a window around the original expiry date and compare competitive awards with sole-source and cooperative orders. Prediction: under design, extension amendments concentrate where re-competition is costliest (high `n_vehicles_held`, single award, tech).
4. **Event study around chance shocks.** Use dated statute or program changes (e.g. federal SNAP/Medicaid rule changes for eligibility systems) as exogenous \(\lambda_0\) shocks. Amendments that follow such shocks estimate the chance channel; the remaining amendment volume bounds the designed channel.
5. **Award price and later growth.** Within agency × commodity, test whether a lower initial award relative to comparable contracts predicts more and larger amendments. Prediction from Model 10: \(dP_0^*/dg<0\), so low awards and high growth go together. Needs comparable-contract benchmarks or bid tabulations.
6. **Award-rule variation.** Compare agencies or periods whose solicitations score lifecycle cost with those scoring price only. Prediction: fewer early and late "restored scope" amendments where \(\phi\) is higher.

## 4. Cautions

- **Exposure differs.** Longer contracts have more time to be amended; use duration as exposure, not a covariate only.
- **Selection into ledgers.** The four ledgers record amendments differently. Washington rows may be running totals, and Oregon Judicial has fiscal-year snapshots. Keep estimates within ledger before pooling.
- **Vendor effects are not intent.** A vendor that does hard, uncertain work will be amended more for chance reasons. Compare within type of work and agency before reading vendor effects as strategy.
- **Extensions are not automatically designed.** Some are efficient: re-competition is costly for everyone. Model 10 predicts *where* extensions should cluster under design, not that every extension is strategic.
