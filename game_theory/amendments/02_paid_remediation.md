# Model 2. Paid remediation and endogenous defects

> Moved from `extensions.md` during the 2026-11 restructure; text unchanged except headings and links. The original is in [`archive/original/`](../archive/original/).

> Shared conventions for all models (risk neutrality, transfers vs. real costs, continuation games after award) are stated in [the folder README](../README.md#conventions).

## Loophole and timing

The baseline treats additional work as exogenous. Here the vendor can prevent some defects, and unresolved defects may become paid amendments.

The agency first fixes a warranty/enforcement arrangement. The vendor chooses prevention effort \(e\geq0\). A defect occurs with probability \(d(e)=\exp(-e)\). Conditional on a defect, an enforceable warranty classification occurs with probability \(w\in[0,1]\). Otherwise the agency purchases repair as additional work. The vendor anticipates these outcomes when choosing effort.

Assume repair is necessary and the agency will purchase it at the specified price; this requires its avoided service loss or replacement cost to exceed that price. The model does not derive the repair price. It can be supplied by the baseline bargaining game.

## Payoff and solution

Prevention costs \(ce^2/2\), with \(c>0\). A defect classified under warranty costs the vendor \(r+f\), where \(r\geq0\) is actual repair cost and \(f\geq0\) is a penalty. Otherwise the paid amendment yields net margin \(\mu\geq0\), after repair cost.

The vendor's payoff, excluding the initial payment, is

\[
\pi(e)=-\frac{c}{2}e^2+\exp(-e)[(1-w)\mu-w(r+f)].
\]

Define the net private loss from a defect as

\[
D=w(r+f)-(1-w)\mu.
\]

If \(D\leq0\), the unique optimum is \(e^*=0\). If \(D>0\), the objective is strictly concave and the unique positive optimum satisfies

\[
ce^*=D\exp(-e^*).
\]

Positive prevention effort therefore requires, when \(\mu+r+f>0\),

\[
w>\frac{\mu}{\mu+r+f}.
\]

Increasing the repair margin reduces effort for \(w<1\) while the solution remains interior. Increasing enforceable warranty coverage raises effort. Nominal warranty language alone does not determine \(w\); classification, evidence, and actual enforcement do.

## Public benchmark and implications

Let \(H>0\) be the expected real repair cost plus agency and applicant harm per defect, excluding transfers. A planner minimizes \(ce^2/2+H\exp(-e)\), giving

\[
ce^{SP}=H\exp(-e^{SP}).
\]

The vendor underinvests if \(D<H\), matches the benchmark if \(D=H\), and overinvests if \(D>H\). Thus stronger penalties are not unconditionally optimal once they exceed the social loss or have enforcement costs.

The loophole is payment for preventable failure combined with weak allocation of repair responsibility. The equilibrium demonstrates reduced prevention, not affirmative sabotage or intent to misrepresent quality.

**Contract implication:** Classify promised functionality and new scope clearly; make covered repairs nonbillable and enforce the distinction. Any repair-price restriction must still leave participation and service-continuity constraints feasible.

**Evidence and distinguishing prediction:** Compare defect incidence and prevention investment across contracts with different enforceable repair obligations, conditional on complexity. Paid repair margins should matter less where warranty enforcement is strong. Amendment totals alone cannot distinguish this mechanism from legitimate scope changes.

