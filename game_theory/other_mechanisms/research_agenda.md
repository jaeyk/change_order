# A common research and simulation agenda

> Moved from `extensions.md` during the 2026-11 restructure; text unchanged except headings and links. The original is in [`archive/original/`](../archive/original/).

> Shared conventions for all models (risk neutrality, transfers vs. real costs, continuation games after award) are stated in [the folder README](../README.md#conventions).

The models separate six mechanisms that otherwise look alike in expenditure records: paying for defects, paying for activity, rewarding a proxy, underfunding shared scrutiny, relying on agency correction, and changing the delivered product after acceptance.

For each simulation, report vendor revenue and profit separately; also report real vendor costs, agency payments, agency labor, applicant harm, and verified outcomes. Keep transfer accounting explicit. Start with continuation choices, then add competitive initial bids and participation constraints. Do not interpret a fixed-fee change as reducing profit or improving welfare without recalculating behavior and initial prices.

Useful first comparisons are:

1. Model 2: vary paid repair margins and warranty enforcement; locate the zero-effort threshold.
2. Model 3: compare usage-only, outcome-only, and mixed payment across case difficulty and burden; include both overprovision and underprovision.
3. Model 4: compare vendor and public thresholds under changes in error prevalence, calibration, rewards, and enforceability.
4. Model 5: compare coordinated testing with pure and symmetric mixed equilibria; report both omitted and duplicated tests.
5. Model 6: map the three review regimes and compare equilibrium costs with joint optimal effort and review.
6. Model 7: vary auditability, available remedies, and credible continuation losses; distinguish harmless cost reductions from harmful substitution.

The highest-priority combined extension is Model 1 plus Model 2: endogenous defects produce amendment opportunities whose margins depend on lock-in. A second is Model 3 plus Model 6: metered workflows and agency review jointly determine the full cost of correct completion. Combining models requires re-solving choices, since standalone comparative statics need not survive their interaction.

These notes provide analytical continuation equilibria and conditional benchmarks. The simulation project *(earlier project; not in this repo)* implements the baseline, all six standalone extensions, the two priority combined games (Models 8 and 9), optimal contract design over stated instruments, and a calibration to the contract documents. Structural estimation with cost data, other combinations, and causal empirical tests remain future work.
