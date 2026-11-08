# Model 9. Metered workflows and agency review (Models 3 + 6)

> Moved from `extensions.md` during the 2026-11 restructure; text unchanged except headings and links. The original is in [`archive/original/`](../archive/original/).

> Shared conventions for all models (risk neutrality, transfers vs. real costs, continuation games after award) are stated in [the folder README](../README.md#conventions).

## Model 9 timing and payoff

The vendor is paid \(t\) per discretionary action and \(R\) for verified raw correctness. It chooses work \(n\in[0,\bar n]\), with raw error probability \(e^{-an}\). The agency observes the raw error rate and then decides whether to review. Review costs \(h\) for screening plus \(\kappa\) per corrected error, and it removes all errors before harm. An uncorrected error causes loss \(L\), and the vendor pays penalty \(f<L\) only for uncorrected errors.

The agency reviews if and only if \(h\le e^{-an}(L-f-\kappa)\), so it reviews whenever

\[
n\le n_c=\frac{1}{a}\ln\frac{L-f-\kappa}{h}.
\]

It reviews at indifference. This tie-break makes the vendor's problem attain its supremum; Model 6 breaks the tie the other way. The vendor maximizes the piecewise payoff

\[
\pi(n)=(t-c)n-\frac d2n^2+R(1-e^{-an})-f\,e^{-an}\,\mathbf 1\{n>n_c\}.
\]

Each piece is concave. The solver takes the optimum on each side of \(n_c\) and compares them, with ties going to the reviewed region.

## Model 9 results

- **Commitment problem with continuous effort.** Below \(n_c\) the agency's review removes the vendor's penalty exposure, as in Model 6. A vendor with \(f>0\) can therefore *bunch* at \(n_c\): it does just little enough work that the agency keeps correcting its errors. The default sweep shows this at \(f=12\), where work stays at the cutoff over a range of usage prices.
- **Usage pay and review substitute.** Higher \(t\) raises work and can push the vendor past \(n_c\). Review then stops, and the public stops paying for corrections, but the public pays for the extra activity instead.
- **Planner benchmark.** The planner chooses \(n\) and review jointly. When it reviews and correction is cheap (\(\kappa a\le c+b\)), it chooses no discretionary work. Paying per action while staff correct the output is then pure excess cost.

**Contract implication:** Price raw correctness, or charge for the agency's correction labor, rather than penalizing only errors that reach applicants. A penalty on uncorrected errors alone is neutralized by the agency's own review.

