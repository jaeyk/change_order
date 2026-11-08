# Model 5. Cooperative purchasing and shared validation

> Moved from `extensions.md` during the 2026-11 restructure; text unchanged except headings and links. The original is in [`archive/original/`](../archive/original/).

> Shared conventions for all models (risk neutrality, transfers vs. real costs, continuation games after award) are stated in [the folder README](../README.md#conventions).

## Loophole and timing

After a shared purchasing arrangement makes a product available, \(N\geq2\) agencies simultaneously decide whether to fund a common validation test. Each chooses \(x_i\in\{0,1\}\). One test is sufficient, and its result is shared. Testing costs the agency \(c>0\); each agency receives expected benefit \(B>0\) if at least one agency tests.

The benefit is the expected avoided loss from detecting and responding to a common defect. Product availability is not assumed to establish actual deployment. Participation and deployment are fixed for this subgame; the vendor is passive here.

## Payoffs and equilibria

\[
u_i=B\mathbf{1}\!\left\{\sum_jx_j\geq1\right\}-cx_i.
\]

If \(B<c<NB\), no agency is willing to test alone, so no testing is the unique Nash equilibrium. Yet one test produces social surplus \(NB-c>0\). This is a straightforward collective-action failure.

If \(0<c<B\), there are \(N\) asymmetric pure equilibria: exactly one agency tests. These equilibria achieve the efficient amount of testing. There is also a symmetric mixed equilibrium in which each agency tests with probability

\[
x^*=1-\left(\frac{c}{B}\right)^{1/(N-1)}.
\]

To derive it, volunteering yields \(B-c\); not volunteering yields \(B[1-(1-x)^{N-1}]\). Indifference requires \((1-x)^{N-1}=c/B\).

The probability no test occurs in the symmetric equilibrium is

\[
\Pr(\text{no test})=(1-x^*)^N
=\left(\frac{c}{B}\right)^{N/(N-1)}.
\]

For fixed \(c/B\in(0,1)\), this probability increases with \(N\). Mixed play can also duplicate testing. The result is specific to the symmetric mixed equilibrium; it does not imply that larger purchasing groups must have less validation under coordinated responsibility.

## Local validation and institutional implications

A shared test need not establish local suitability. Add an independent local test costing \(\ell_i\) and yielding local benefit \(L_i\), with no spillovers. With full internalization, agency \(i\) performs it exactly when \(L_i\geq\ell_i\). There is no free-riding problem in that independent local decision.

To explain inadequate local testing, introduce a separate mechanism: underestimated local mismatch or applicant harms not fully valued by the agency. If it values only \(\omega_iL_i\), \(0\leq\omega_i<1\), local testing is omitted despite positive social value when

\[
\omega_iL_i<\ell_i<L_i.
\]

The simulation implements this local decision with symmetric agencies (parameters \(\ell\), \(L\), \(\omega\)), testing at indifference. It reports local welfare loss \(N(L-\ell)\) in the omission region and adds it to the shared-test loss.

**Contract implication:** Assign and fund common testing explicitly, while separating it from jurisdiction-specific validation. Shared purchasing can improve validation through cost sharing; the model does not imply cooperative purchasing is inherently harmful.

**Evidence and distinguishing prediction:** Compare arrangements with assigned validation responsibility against arrangements relying on voluntary contributions. Distinguish common testing, local testing, purchasing eligibility, actual orders, and deployment. Group size alone cannot identify free riding because group composition and coordination differ.

