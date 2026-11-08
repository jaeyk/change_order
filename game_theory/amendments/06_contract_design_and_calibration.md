# Contract design and calibration

> Moved from `extensions.md` during the 2026-11 restructure; text unchanged except headings and links. The original is in [`archive/original/`](../archive/original/).

> Shared conventions for all models (risk neutrality, transfers vs. real costs, continuation games after award) are stated in [the folder README](../README.md#conventions).

## Optimal contract design

The continuation games above take contract terms as given. `simulation/design.py` *(earlier project; not in this repo)* solves the prior stage: the agency commits to instruments within stated bounds, anticipating the equilibrium they induce. Each problem specifies an objective and optional quadratic governance costs \(g x^2/2\) per instrument.

Under fully informed competitive bidding, the agency's expected payments equal real vendor costs plus expected penalties. With transfers netted and burden fully weighted, its objective then equals social cost. Model 1 keeps the agency's own objective, so the burden weight \(\omega\) matters. The search is a grid with successive zooming rather than a derivative method, because Models 6, 7 and 9 have discrete regime changes. Where an interval of instruments is optimal, one optimum is reported.

The default problems reproduce the analytic benchmarks:

- **Model 4.** The optimal flag reward equals \(c+mf(1-\tau_{SP})\).
- **Model 3.** Any single instrument reaches the one-dimensional public optimum.
- **Model 6.** A penalty above \(L-h/p_L\) removes the review commitment problem, reaching the planner's cost.

The problems also show results that are not available in closed form:

- **Model 1.** The agency's optimal monitoring rises with its weight on applicant burden.
- **Model 2.** A repair-price cap substitutes for costly warranty enforcement, lowering the optimal enforcement level.
- **Models 8 and 9.** The jointly optimal warranty and portability terms (Model 8), and usage and penalty terms (Model 9), differ from the standalone prescriptions.

These remain illustrative: the value, cost and governance parameters are not estimated.


## Calibration to the contract documents

`simulation/calibrate.py` *(earlier project; not in this repo)* reads the models through the contracts in `data/`. Its inputs are:

- hand-verified amendment histories, each with a source quote;
- prices, service-level penalty caps, and negotiated deviations;
- clause codes from a reproducible regular-expression pass that records every match, with manual overrides.

The data identify two quantities. One is the frequency of priced unplanned work (\(\hat\lambda\)). The other is the amendment growth ratio, which pins the amendment price once the base contract is normalized. Coded terms map to monitoring, portability, penalty exposure and warranty enforcement through editable rules.

The records cannot separate the incumbent's cost from its bargaining margin. The bargaining weight \(\theta\) is therefore reported as an identified set: the values for which a nonnegative incumbent cost reproduces the observed amendment. Choices depend on the coded terms and \(\hat\lambda\); the dollar records constrain only how much amendment spending the model can attribute to margin.

The calibration report also re-solves Model 1's design problem at the coded terms. It records structural restrictions for Models 3–5:

- no coded contract pays for verified outcomes;
- none states a false-positive standard;
- cooperative cloud addenda lack local acceptance-testing language.

