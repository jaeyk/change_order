# Vendor strategies and how they vary by sector

This note answers one question: **which strategies do vendors appear to use after winning a public contract, and how does that differ by sector?** It brings together several sources:

- the theory: [game_theory/](game_theory/README.md);
- the simulations: [simulations/](simulations/README.md);
- the coded contract documents: [synthesis/](synthesis/README.md);
- two measures added for this note: follow-on awards and sales channels.

Every claim was then put through the checks in [robustness_checks.md](robustness_checks.md).

Numbers come from the 2026-11-08 run: 694,856 contracts in 15 ledgers. Rebuild them with:
- `python3 scripts/vendor_strategies.py`, which writes `data/processed/vendor_strategies.json`;
- `python3 robustness/stratified.py`.

> **How to read this.** Each strategy leaves a pattern that pure chance would not produce. We test for it against a chance benchmark matched to the same amendment counts.
> - **Consistent, not proven.** A sector that shows the pattern is *consistent with* the strategy; this is not proof of intent.
> - **Within-ledger numbers lead.** Ledgers differ a lot, and sectors are spread unevenly across them. For example, most software contracts with dated amendments are Washington's, and Washington's amendments escalate, grow and come early in every sector. So **pooled** sector numbers partly reflect which ledger a contract comes from. The tables below report **within-ledger** gaps (sector minus non-technology, same ledger) where they differ from the pooled picture.
> - **No share estimate.** We cannot yet say *how much* of a sector's amendments are strategic. The estimator built for that could not tell lock-in from no lock-in in synthetic data ([synthesis/RESULTS.md](synthesis/RESULTS.md)).

## 1. The bottom line

| Sector | What the data are consistent with | How robust |
| --- | --- | --- |
| **Software & SaaS** | **Holdover and modest lock-in.** Its contracts are extended until a replacement is ready far more often than non-tech, and its amendment risk depends on the vendor. Its later amendments are a little larger than its earlier ones. | Holdovers: robust, but Chicago documents only. Late-term amendments: robust within ledgers (+16.5 points vs. non-tech). Escalation: **+3.7 points within ledgers**, much smaller than the pooled +16.5. Value compounding: **not** above non-tech within ledgers. |
| **General technology** | **Holdover, and compounding.** Amendments come late; documents cite pending replacements; value grows more than non-tech after repeated amendments. | Late (+6 points) and compounding (+0.28 log) gaps hold within ledgers. Little escalation. |
| **Hardware & telecom** | **Two businesses.** Commodity sales through resellers that are rarely amended, plus a smaller set of service agreements that compound. | Reseller pattern: holds in every ledger. Compounding within ledgers +0.31 log (Chicago, Oregon). |
| **IT services** | **No robust pattern.** The early "buy-in then change order" signal is a Washington feature, where every sector amends early. | Fails outside Washington and above $25k. Small sample. |
| **Non-technology** | **Routine renewals.** | The benchmark. |

Findings that hold in every check:
1. **Incumbents keep the business by amending, not by re-winning.** No sector re-awards to its previous vendor more often than chance, under any de-duplication window.
2. **Resellers in hardware & telecom are rarely amended.** This holds in all five ledgers with enough resellers.
3. **Holdovers are a technology phenomenon.** In Chicago's documents, "extended until a new contract is awarded" appears in 32 of 94 software and general-technology documents against 2 of 45 non-technology ones (p = 0.00005).
4. **The ledgers rarely say why.** About 70% of coded documents state no cause. Explicit design causes (change orders, unforeseen work, licence dependence) are rare in every sector.

What did **not** hold up:
- **Software compounding fastest.** That was a ledger-composition effect.
- **IT services' buy-in pattern.**
- **"Every sector amends late."** This describes Chicago, Oregon and Cook County, but not Washington, whose labelled amendments come early in all sectors.

## 2. The strategies and their fingerprints

| # | Strategy | Theory | What it should leave in the data | Measure used here |
| --- | --- | --- | --- | --- |
| S1 | **Buy-in and buy back.** Leave work out of the bid and sell it back later. | Model 10 (scope gap \(g\)) | Amendments early in the term, when gaps surface | First amendments in the first 25% of the term |
| S2 | **Lock-in escalation.** Each amendment deepens dependence, which raises the price of the next. | Models 1 and 8; Model 10 spiral | Later amendments larger than earlier ones; value compounds | P(2nd amendment > 1st); value after six amendments |
| S3 | **Holdover.** Extend instead of letting the contract be re-competed. | Model 1; Model 10 (late design) | Amendments at or after the end of term; documents citing a pending replacement | Amendments in the last 10% of the term; coded documents |
| S4 | **Vendor-specific playbook.** | Model 10 (persistent vendor effects) | Amendment risk explained by the vendor, holding ledger and department fixed | Vendor share of variance in amendment risk |
| S5 | **Follow-on awards.** | Model 1 (incumbency) | Same vendor wins consecutive awards more often than chance | Consecutive same-vendor awards vs. shuffled order |
| S6 | **Channel choice.** Cooperatives, state contracts, resellers, multiple-award vehicles. | Model 5; channel as \(\phi\) | Different amendment rates and growth by channel within a sector | Amendment rate and growth by channel |
| — | **Paid remediation.** | Model 2 | Repairs billed as amendments | **Not testable**: ledgers do not record defects |

## 3. Results by strategy

Pooled numbers are from `vendor_strategies.json`; within-ledger gaps from `robustness/results/stratified.json`.

### S1. Buy-in and buy back: no robust evidence

| Sector | Pooled: first amendment in first 25% of term (chance) | Within-ledger gap vs. non-tech [95% CI] |
| --- | --- | --- |
| IT services | 69% (49%) | +11.3 pts [+8.4, +14.4], **Washington only**; negative in Chicago and Oregon |
| Software & SaaS | 48% (51%) | −9.9 pts [−11.8, −8.1] |
| Hardware & telecom | 28% (51%) | −2.0 pts [−4.3, +0.4] |
| General technology | 19% (44%) | −8.7 pts [−10.1, −7.5] |
| Non-technology | 38% (52%) | — |

IT services looked like the one sector where vendors buy in and sell back missing scope. That pattern comes entirely from Washington's ledger, where first amendments come early in *every* sector. It also reverses for awards above $25k (R3). The sharper test, whether a low award relative to the agency's estimate predicts more amendments, needs estimates. Cook County's buying plans (now downloaded) could supply some.

### S2. Lock-in escalation: modest in software, absent elsewhere

| Sector | Pooled P(2nd > 1st) − 0.5 | **Within-ledger gap vs. non-tech** | Pooled value after 6 amendments (95% CI) | **Within-ledger log gap after 6** |
| --- | ---: | ---: | ---: | ---: |
| Software & SaaS | +16.5 pts | **+3.7 pts** [+0.2, +7.0] | 2.87× (2.68–3.06), n = 690 | +0.03 [−0.09, +0.15] |
| Hardware & telecom | +5.6 | −1.7 [−7.0, +3.7] | 2.56× (2.23–2.94), n = 172 | **+0.31** [+0.11, +0.49] |
| IT services | +7.4 | −4.1 [−13.6, +3.8] | 2.40× (1.84–3.12), n = 63 | **+0.47** [+0.09, +0.82], Washington only |
| General technology | +4.3 | −0.3 [−4.3, +3.5] | 2.13× (1.96–2.32), n = 457 | **+0.28** [+0.14, +0.41] |
| Non-technology | +6.2 | — | 1.89× (1.85–1.93), n = 6,320 | — |

**Software amendments do escalate more than non-tech ones in the same ledger, but by about 4 points, not 16.** Most of the pooled gap reflects Washington, where escalation is high in every sector.

The software edge:
- **survives** a stricter software definition and last-vs-first measurement;
- **shrinks** above $25k;
- **is absent** in Chicago and in the new DC ledger.

**Compounding tells a different story within ledgers.** Hardware & telecom and general-technology contracts that are amended many times end up further above their original value than non-tech contracts. Software contracts do not. Figure 3 shows the pooled picture, so read it with that in mind.

### S3. Holdover: the most consistent technology pattern

| Sector | Pooled: amendment in last 10% of term or after (chance) | Within-ledger gap vs. non-tech | Documents: "extended until a new contract is awarded" |
| --- | --- | --- | --- |
| Software & SaaS | 55% (27%) | **+16.5 pts** [+14.7, +18.4] | **15 of 44 (34%)** |
| Hardware & telecom | 69% (27%) | **+9.3** [+6.3, +12.1] | 5 of 45 (11%) |
| General technology | 62% (21%) | **+6.1** [+4.7, +7.6] | **17 of 50 (34%)** |
| IT services | 40% (25%) | +2.1 [−1.8, +5.5] | 10 of 51 (20%) |
| Non-technology | 54% (29%) | — | 2 of 45 (4%) |

Technology contracts are amended near or after the end of their term more often than non-tech contracts in the same ledger. The documents name the reason: the contract was extended because its replacement was not ready.
- **By sector:** holdovers are a third of software and general-technology documents, against 4% for non-tech (p = 0.00005).
- **By amendment order:** they rise from 12% of first amendments to 30% of fourth and later.

A holdover benefits the incumbent whether or not it engineered the delay; the documents do not say whose delay it was. Documents are a Chicago sample of 235.

### S4. Vendor-specific amendment behaviour: technology generally, not software alone

| Sector | Pooled vendor share (chance) | Within-ledger gap vs. non-tech |
| --- | ---: | ---: |
| Software & SaaS | 0.36 (0.03) | +0.13 |
| General technology | 0.28 (0.02) | +0.11 |
| IT services | 0.26 (0.10) | +0.11 |
| Hardware & telecom | 0.14 (0.04) | −0.01 |
| Non-technology | 0.18 (0.01) | — |

Who the vendor is explains much more of the variation in amendment risk than chance would, in every sector. Software, general technology and IT services all exceed non-tech within ledgers by similar amounts; hardware does not.
- **Software is not uniquely highest:** it falls below general technology in Oregon and in the 2005–2019 window.
- **Strategy or specialization:** the measure mixes the two, because vendors within a department may do different work.
- **No interval yet:** a valid confidence interval needs a vendor-cluster bootstrap.

### S5. Follow-on awards: no excess in any sector

| Sector | Next award to the previous vendor | Shuffled order | Difference |
| --- | ---: | ---: | ---: |
| Software & SaaS | 2.7% | 2.8% | −0.1 pts |
| Hardware & telecom | 5.6% | 5.9% | −0.3 pts |
| IT services | 7.1% | 5.4% | +1.7 pts |
| General technology | 3.9% | 3.6% | +0.3 pts |
| Non-technology | 0.3% | 0.5% | −0.2 pts |

Repeat entries from the same vendor and department in the same month are collapsed, because these are split purchase orders. With quarter or year windows, every sector is at or below zero (R11). Vendors keep business by amending and extending the contract they hold, not by re-winning.

### S6. Channel choice: resellers in hardware, vehicles everywhere

Shares are of all contracts in the sector. Amendment rates use contracts whose ledger records amendments.

| Sector | Through resellers | Amended: resellers vs. others | Cooperative or state master contract | Amended: vs. others | Multiple-award | Amended: vs. others |
| --- | ---: | --- | ---: | --- | ---: | --- |
| Software & SaaS | 19.3% | 23% vs. 30% | 4.2% | 24% vs. 29% | 2.2% | **44% vs. 28%** |
| Hardware & telecom | **23.9%** | **11% vs. 30%** | 2.0% | 19% vs. 25% | 1.0% | 35% vs. 25% |
| IT services | 4.4% | 41% vs. 42% | 1.3% | 41% vs. 42% | 1.3% | 39% vs. 42% |
| General technology | 3.8% | 21% vs. 34% | 0.8% | 33% vs. 34% | 0.5% | 38% vs. 34% |
| Non-technology | 1.6% | 14% vs. 31% | 0.9% | 35% vs. 31% | 1.3% | **41% vs. 31%** |

- **Hardware & telecom sells through resellers, and those sales are rarely amended.** This holds within every ledger (R12).
- **Resellers are amended less in every sector except IT services.**
- **Multiple-award vehicles are amended more in almost every sector**, which looks like a feature of the vehicle (ceilings raised as orders are placed) rather than of any sector.
- **Growth no longer separates channels.** In the earlier, smaller sample, amended software sold through resellers grew more (median 2.65×). With New York City added, where most amendments change no money, the median growth of amended contracts is 1.0× in most cells.
- **Regressions do not settle direction.** In the logit models, cooperative and reseller terms change sign between the pooled and Washington-only samples (README §5E), so channel comparisons are descriptive.

## 4. Sector profiles

**Software & SaaS (30,581 contracts).** The holdover pattern is clear, and amendment risk is concentrated in particular vendors; later amendments are only slightly larger than earlier ones. In practice that means:
- contracts run to and past their end dates;
- they are extended while replacements are prepared;
- some vendors are amended far more than others.

That fits a lifecycle strategy (Model 10's horizon gap) in which the value comes from continuation, not from escalating change orders. The pooled evidence of strong escalation and fast compounding did not survive within-ledger comparison.

**General technology (29,075 contracts).** The most late-skewed amendments, holdovers in a third of documents, a vendor effect like software's, and, within ledgers, more compounding than non-tech after repeated amendments.

**Hardware & telecom (21,001 contracts).** Mostly commodity sales through resellers that are rarely amended. Within ledgers, the minority of hardware contracts amended many times compound more than non-tech, probably maintenance and telecom service agreements. Splitting goods from recurring services would sharpen this.

**IT services (6,817 contracts).** Amended most often (42% of contracts with histories), but none of its distinctive patterns survives outside Washington. Thin outside Washington.

**Non-technology (607,382 contracts).** The benchmark. Amendments are mostly routine renewals in Chicago, Oregon and Cook County and early changes in Washington. Holdovers are rare in documents.

## 5. What this does not show

- **Intent.** Every fingerprint can arise without strategy: complex products face genuine change; delays may be the agency's; vendor effects may reflect specialization.
- **The designed share.** We report patterns, not percentages of strategic amendments.
- **Buy-in pricing.** No engineer's estimates or losing bids yet.
- **Paid remediation.** The data do not record defects.
- **Representativeness.** The sample is 15 ledgers from 9 states and DC, not a probability sample of governments ([sampling_frame.md](sampling_frame.md)). Timing tests rest on 7 dated ledgers, mostly Washington, Chicago and Oregon.

## 6. Reproduce

```bash
python3 scripts/normalize_and_classify.py         # contracts and amendments
python3 simulations/simulate_amendments.py        # fingerprints vs. matched chance
python3 scripts/make_figures.py                   # Figure 3 values
python3 scripts/vendor_strategies.py              # pooled tables, follow-ons, channels
python3 robustness/run_checks.py                  # R0-R14 (about 7 minutes)
python3 robustness/stratified.py                  # R15 within-ledger gaps (about 15 minutes)
```
