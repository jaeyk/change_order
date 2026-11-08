# Model 6 extension: hidden effort, noisy diagnostics, and commitment

This extends [Model 6](../other_mechanisms/model6_human_review.md),
retaining its payoffs and changing the agency's information. The implementation is
review_spiel.py *(earlier project; not in this repo)*. OpenSpiel represents the extensive-form
game and independently checks unilateral deviation gains. Parameters remain illustrative.

## Timing and information

1. The vendor chooses low effort (zero cost, error probability pL) or high effort
   (cost c, error probability pH < pL).
2. Nature draws a good/bad diagnostic. Accuracy a is in [0.5, 1]:
   P(good | high) = a and P(good | low) = 1-a.
3. The agency observes only that diagnostic and chooses review or skip.
4. Review costs h and corrects all errors; otherwise errors cause loss L and
   trigger a vendor payment f to the agency. The common fixed payment is omitted.

The diagnostic is evidence about effort/quality, not the realized error itself.
Conditional on effort, it is independent of the eventual error. Error uncertainty
is integrated out in terminal payoffs. Review is corrective labor, not an
additional information-acquisition decision. Signal accuracy is exogenous and
costless here; endogenous audit acquisition is a future extension.

The vendor's utility is -c·1{high} - f·p_e·(1-r).
The agency's utility is -h·r - (L-f)·p_e·(1-r).
Their sum is negative social cost: -c·1{high} - h·r - L·p_e·(1-r).
Thus this is a general-sum game: penalties transfer resources between players.
Loss L aggregates agency/applicant harm, following the existing model; it is not
a separately estimated applicant-only loss measure.

## Discretionary review

Write x = P(high), and r_good, r_bad for signal-contingent review probabilities.
Let s_e(z) be the probability of signal z under effort e. Bayes' rule gives

    P(high | z) = x s_H(z) / [x s_H(z) + (1-x) s_L(z)].

The agency reviews if posterior expected error times (L-f) exceeds h, skips if
it is lower, and may mix at equality. The vendor chooses high effort if

    f[pL(1 - s_L · r) - pH(1 - s_H · r)] > c,

chooses low if the inequality reverses, and may mix at equality.

For a < 1 both signals have positive probability under either effort. Every
agency information set is reached, even under pure vendor strategies, so these
best responses and Bayes beliefs establish sequential rationality. We enumerate
the 27 support patterns (zero, one, or indifferent for each of x, r_good, r_bad)
and solve their linear feasibility conditions with SciPy. OpenSpiel's separate
tree-based best-response computation checks each retained policy. NashConv is
the sum of both players' gains from unilateral deviation, in payoff units.

One feasible representative is retained per support and identical policies are
deduplicated. This is not enumeration of every point in a degenerate equilibrium
continuum, nor a selection theory. At a = 0.5 different signal-contingent policies
can have identical outcomes. We report their review probabilities separately.

At a = 1 the signal reveals effort. Off-path review must then be specified by
backward induction, not arbitrary Nash threats. The implementation reproduces
Model 6's selection: skip review at agency indifference; low effort at vendor
indifference. It does not enumerate other possible equilibria at equality.

## Enforceable commitment

The agency publicly commits before effort to a pair of review probabilities.
The vendor observes these probabilities, but not the future random draw. This
assumes the policy can be enforced even if the agency would later prefer to
change it. For each target effort, a two-variable linear program minimizes agency
net cost subject to the vendor's incentive constraint and probabilities in [0,1].

Vendor indifference selects low effort, as in Model 6. To induce high effort we
require a positive incentive margin (default 1e-6 payoff units). The reported
solution is optimal under this additional margin constraint, not necessarily the
exact optimum over an open strict-incentive region. This avoids implicitly
assuming favorable follower tie-breaking. The margin is configurable in Python.

The report includes deviation gains for the committed policy evaluated in the
*uncommitted* game. A positive agency gain there measures temptation to abandon
the policy, not failure of the commitment optimization. A commitment outcome is
not labeled a Nash equilibrium of the discretionary game.

## What the default example reveals

Use pH = 0.1, pL = 0.5, L = 100, f = 20, h = 20, c = 5.

| Information / policy | P(high) | Review probability | Social cost | Agency net cost |
| --- | --- | --- | --- | --- |
| Revealing diagnostic, backward induction | 0 | 1 | 20 | 20 |
| Uninformative diagnostic, low-effort equilibrium | 0 | 1 | 20 | 20 |
| Uninformative diagnostic, high-effort equilibrium | 1 | 0 | 15 | 8 |
| Uninformative diagnostic, mixed equilibrium outcomes | 0.625 | 0.375 | 26.25 | 20 |
| Enforceable no-review commitment | 1 | 0 | 15 | 8 |

With a noisy full-support signal and a pure high-effort equilibrium, both signals
leave posterior probability one on high effort. A deviation to low effort does
not become perfectly detectable. The agency therefore skips review after either
signal, leaving the vendor exposed to penalties if it deviates. With a perfectly
revealing diagnostic, low effort becomes observable and triggers corrective
review, eliminating those penalties. The discontinuity at perfect information is
a feature of this simplified game's information structure, not a numerical bug.

The low-effort/full-review equilibrium survives hidden effort, but uniqueness
does not. Neither better diagnostics nor commitment is automatically a social
improvement. For example, at h = 10 the agency prefers the committed high-effort
outcome (agency cost 8), although its social cost 15 exceeds the low-effort/review
equilibrium's social cost 10. Penalty revenue helps explain this difference.
Equilibrium selection, commitment feasibility, imperfect correction, and the
agency's treatment of penalty revenue merit further study.

## Reproduce and inspect

From `simulation/`:

```sh
uv sync --locked --extra spiel
.venv/bin/python -m unittest test_review_spiel -v
.venv/bin/python review_spiel.py
```

The runner covers 25 combinations of review cost and signal accuracy and creates
a new timestamped `outputs/review_spiel_*/` directory containing `results.json`
and `REPORT.md`. JSON includes parameters, both players' deviation gains,
outcomes, dependency versions, and hashes of the implementation, base models,
and lockfile. The original nine-model runner and browser game are unchanged.

Validation checks observable-model parity (including ties), information hiding,
terminal transfer accounting, Bayes-consistent review, analytical mixed outcomes,
OpenSpiel deviation gains, and commitment feasibility/optimality against an
independent grid. The optional tests skip when OpenSpiel/SciPy are absent.

OpenSpiel references: [framework](https://github.com/google-deepmind/open_spiel),
[Python game example](https://github.com/google-deepmind/open_spiel/blob/master/open_spiel/python/games/kuhn_poker.py),
[best response and NashConv](https://github.com/google-deepmind/open_spiel/blob/master/open_spiel/python/algorithms/exploitability.py).
