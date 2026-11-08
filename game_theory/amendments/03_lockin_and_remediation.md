# Model 8. Lock-in and paid remediation (Models 1 + 2)

> Moved from `extensions.md` during the 2026-11 restructure; text unchanged except headings and links. The original is in [`archive/original/`](../archive/original/).

> Shared conventions for all models (risk neutrality, transfers vs. real costs, continuation games after award) are stated in [the folder README](../README.md#conventions).

## Model 8 timing and payoff

This combines the baseline's bargaining over additional work with Model 2's endogenous defects. The agency fixes warranty enforcement \(w\) and portability \(p\). The vendor then chooses prevention effort \(e\) and proprietary dependence \(k\). Exogenous additional work arrives with probability \(\lambda\), as in Model 1. Independently, a defect occurs with probability \(\exp(-e)\). With probability \(w\) it is covered: the vendor repairs it at cost \(r\) and pays penalty \(f\). Otherwise it becomes a paid amendment.

Both kinds of amendment are priced by generalized Nash bargaining against a replacement vendor, with switching cost \(S(k,p)=s_0+\alpha k/(1+p)\). New work is priced at \(A=c_I+\theta(c_R+S-c_I)\) and an uncovered repair at \(r+\mu(k)\), where

\[
\mu(k)=\theta\,[r_R+S(k,p)-r]
\]

and \(r_R\) is the replacement vendor's repair price. The repair margin of Model 2 is now endogenous: dependence raises it. Excluding the initial payment, the vendor's payoff is

\[
\pi(e,k)=-\frac{c}{2}e^2-\frac{c_k}{2}k^2+\lambda\theta\Delta(k,p)+e^{-e}\big[(1-w)\mu(k)-w(r+f)\big].
\]

## Model 8 solution

The payoff is quadratic and concave in \(k\), so the best response is exact:

\[
k^*(e)=\frac{\theta\alpha\,[\lambda+(1-w)e^{-e}]}{c_k(1+p)}.
\]

Dependence now has two returns: leverage over new work and leverage over repairs. More defects raise the second return. Substituting \(k^*(e)\) gives a one-dimensional profile in \(e\). The envelope theorem gives its slope:

\[
-ce+e^{-e}D(k^*(e)),\qquad D(k)=w(r+f)-(1-w)\mu(k).
\]

The profile need not be concave, because dependence and defects are strategic complements. The solver therefore runs a global grid search over \(e\) and then bisects on this slope inside the winning bracket. Competitive initial bids still drive expected profit to zero.

## Model 8 results

- **Feedback loop.** Dependence raises the repair margin. That lowers prevention, which raises defect frequency, which raises the return to dependence.
- **Portability raises prevention.** Portability lowers \(k^*\) and hence \(\mu\), which raises \(D\) and therefore effort. This prediction is absent from both standalone models: in Model 1 portability affects only dependence, and in Model 2 the repair margin is fixed.
- **Bargaining power without lock-in.** If \(\theta=0\), repairs carry no margin and \(k^*=0\). Effort then solves Model 2 with \(\mu=0\).
- **Planner benchmark.** A planner chooses \(k=0\) and \(ce=He^{-e}\). Excess social cost combines underprevention with wasteful dependence.

**Contract implication:** Warranty enforcement and portability are complements. Weak portability makes a given warranty less effective, because every uncovered defect becomes a lock-in-priced amendment.

