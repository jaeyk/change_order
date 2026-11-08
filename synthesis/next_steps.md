# Next steps: from pattern matching to estimation

Each step below lists its question, inputs, method, outputs, and what would change our conclusions. Steps 1–2 come first because every later step uses their estimates.

Current state (November 2026):
- **Simulations** ([simulations/](../simulations/README.md)) classify sectors against five illustrative worlds.
- **Robust fingerprints:**
  - *Vendor share of amendment risk* separates design from chance and routine renewals.
  - *Escalating amendment size* separates lock-in.
- **Leading sectors:** Software & SaaS and general enterprise IT show both.

---

## 1. Parameter recovery and power

**Question.** At the sample sizes we actually have, can the fingerprints detect design and lock-in, and can their parameters be recovered?

**Inputs.** `simulations/simulate_amendments.py` (`world()`), and each sector's real numbers of contracts, timed contracts and eligible amendment pairs (`simulations/results/sector_fingerprints.csv`).

**Method.**
1. For a grid of known parameters (gap intensity, lock-in strength \(\rho,\psi\), renewal probability, vendor dispersion), simulate datasets with each sector's exact sample structure.
2. Run the same fingerprint pipeline and record how often each fingerprint reaches |z| ≥ 2. That is the power.
3. Run the estimator from step 2 on the simulated data and compare estimates with the truth. That is recovery.

**Outputs.** A power table by sector × fingerprint, and the minimum detectable escalation effect per sector. This decides which "thin" sectors (environment, IT services, public safety, transportation) can be analyzed at all, and replaces the ad hoc "fewer than 30 pairs" rule.

**What would change conclusions.** Low power for escalation in mid-size sectors would mean their "tier 3" label reflects missing evidence, not absence of lock-in.

## 2. Simulated method of moments, sector by sector

**Question.** How much of each sector's amendment activity is designed rather than chance, and how strong is lock-in?

**Inputs.** Observed moments per sector:
- amendment-count mean and variance;
- the continuation curve at k = 0…5;
- the early, late and late-lift shares;
- escalation and acceleration probabilities;
- vendor share of risk;
- the award-to-final growth path in Figure 3.

**Method.** Specify a mixture world: chance with heterogeneity, plus a designed component with share \(\sigma\) and saturating lock-in \((\rho,\psi,k_{cap})\), plus renewals. Choose parameters to minimize the weighted distance between simulated and observed moments. The weights come from the inverse bootstrap covariance of the observed moments, and standard errors come from the bootstrap. Use common random numbers so the objective is smooth in the parameters.

**Outputs.** Per sector, with confidence intervals:
- \(\hat\sigma\), the designed share of amendments;
- \(\hat\psi\), how fast amendment margins grow with dependence;
- the renewal probability;
- a vendor-dispersion parameter;
- an overidentification test showing which moments the model fails to fit.

**What would change conclusions.** If Software & SaaS has \(\hat\sigma\) indistinguishable from non-tech once heterogeneity is fit jointly, the current ranking is a pattern artifact.

## 3. Out-of-sample validation

**Question.** Does the fitted model predict what it was not fit to?

**Method.**
- **Held-out moments.** Fit without the value-growth path, then predict Figure 3's snowball: about 2.4× after six amendments for hardware/telecom and 1.5× for non-tech.
- **Held-out ledgers.** Fit on Chicago and Oregon, predict Cook County, then predict Washington's timing (once Washington's amendment dates are validated).
- **Held-out time.** Fit on contracts awarded before 2015, predict later cohorts.

**Outputs.** Prediction errors by sector, and a short list of patterns the model cannot reproduce. Those feed back into the theory.

## 4. Comparative statics across procurement channels

**Question.** Model 10 predicts more designed amendments when the award puts less weight \(\phi\) on later costs. Does the estimated designed share move with proxies for \(\phi\)?

**Inputs.** `procurement_channel` and `coop_direction`:
- central state contract;
- horizontal cooperative;
- vertical piggyback;
- own solicitation.

Also `procurement_method`: competitive, sole source, statewide contract, reference contract.

**Method.**
1. Rerun step 2 separately by channel, within sector where sample size allows.
2. Write down the model's predicted ordering before looking at the estimates. For example, vehicles that pre-price changes leave less room for designed margins, so escalation should be weaker there.
3. Compare the estimated ordering with the predicted one.

**What would change conclusions.** An ordering opposite to the prediction would point to selection (which work goes through which channel) rather than \(\phi\). That would call for a design that holds work type fixed.

## 5. Vendor-level lock-in

**Question.** Is the lock-in signature concentrated in certain kinds of vendors?

**Inputs.** `vendor_role` (prime vs. authorized reseller), `qualification_tier` and `gsa_mas_holder`, `award_structure` (single vs. multiple award), plus the vendor random effects from step 2.

**Method.** Estimate step 2's vendor-dispersion and escalation parameters separately by vendor type. Check whether the vendors with the largest estimated design effects keep that profile across agencies and ledgers, which is Model 10's repeated-play prediction.

**Outputs.** Lock-in parameters by vendor type, and the persistence of vendor effects across buyers.

**Already known.** Holding a GSA schedule (odds ratio 1.42 pooled, 1.81 in Washington) and multiple award (2.9 pooled) predict higher amendment odds, controlling for contract size, duration and jurisdiction. Step 5 asks whether that reflects design or the kind of work those vendors do.

## 6. Ground truth from amendment documents

**Question.** Can we observe *why* amendments happened, and do those reasons agree with the estimated designed share?

**Inputs.** Chicago links every record to its contract documents, but they sit behind a JavaScript viewer. Washington's modification text is classified by `scripts/amendment_reasons.py`.

**Method.**
1. **Pilot sample.** Draw a stratified sample of about 300 Chicago amendment documents: by sector, by amendment order, and by fingerprint (escalating vs. not). Collect them slowly with headless Chrome, with a few seconds between requests and only after you approve.
2. **Hand-code.** Label a subset with the reason taxonomy (chance, design, ambiguous, neutral).
3. **Measure agreement.** Compare the text classifier with the hand codes.
4. **Validate the estimates.** Check whether amendments the model attributes to design (later, larger, at lock-in-prone vendors) are more often documented as restored scope, change orders or rate increases.

**Outputs.** A validated reason sample, classifier accuracy, and an external check on step 2's \(\hat\sigma\).

**Needs approval** because it sends many requests to a city server.

## 7. Chance shocks — dropped

Event studies of dated outside shocks (COVID-19 in March 2020, H.R. 1 in July 2025) were set aside because the data are not good enough:
- amendment rates in the available ledgers swing with funding and biennium cycles, so a dated shock cannot be isolated;
- no state eligibility-system ledger covers the H.R. 1 period.

The chance channel is instead read from what amendment records and documents state (steps 2 and 6).

---

## 8. Policy counterfactuals

**Question.** Under the estimated parameters, how much amendment spending would each lever avoid?

**Method.** Feed the step 2 estimates into Model 10 and simulate each lever by sector:
- **Lifecycle-cost scoring** at award (raise \(\phi\)).
- **Portability and data rights** (lower \(\beta\)).
- **Pre-priced change rate cards** (cap the margin).
- **Non-billable omitted scope** (make \(g\) unpaid).

Report changes in amendment counts, award-to-final growth and expected lifecycle payments, with uncertainty carried through from the estimates.

**Outputs.** A sector × lever table of predicted effects. This is the policy-facing deliverable, and its validity rests on steps 2–4.

---

## Order of work and files (as implemented)

| Step | Code (planned) | Output |
| --- | --- | --- |
| 1 | `synthesis/smm.py power`, `synthesis/smm.py recover` | `synthesis/results/power_by_sector.csv` |
| 2 | `synthesis/smm.py estimate` | `synthesis/results/smm_estimates.csv`, fit diagnostics |
| 3 | `synthesis/steps.py validate` | `synthesis/results/validation.csv` |
| 4–5 | `synthesis/steps.py channels`, `synthesis/steps.py vendors` | `synthesis/results/smm_by_channel.csv`, `smm_by_vendor_type.csv` |
| 6 | `synthesis/document_sample.py` (after approval) | `synthesis/results/document_codes.csv` |
| 7 | dropped | — |
| 8 | `synthesis/steps.py counterfactuals` | `synthesis/results/policy_counterfactuals.csv` |

Steps 1 and 2 use only code and data already in the repository and can start immediately.
