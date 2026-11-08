# Procurement, vendor dependence, and public burden

## Purpose and status

This note develops a proposed game-theoretic model based on [Vendor profits and procurement vulnerabilities](../manuscript/vendor_exploitation.md). It formalizes how competition for an initial contract can coexist with subsequent vendor dependence, costly amendments, and weak incentives to reduce applicant burden.

This is a theoretical framework, not an empirical finding about particular vendors. The baseline distinguishes amendment margins, total vendor profits, agency expenditures, and applicant burdens. It does not assume that cost overruns establish misconduct or that artificial intelligence necessarily increases vendor power.

This document is **Model 1: procurement, dependence, and amendment bargaining**. [Additional models](extensions.md) develop paid remediation, metered workflows, rewarded flags, shared validation (with local validation), human review, and post-award substitution (Models 2–7), and two combined games: lock-in with paid remediation (Model 8) and metered work with agency review (Model 9). The same note covers optimal contract design and calibration to the contract documents.

## 1. Players and timing

The players are a public agency and vendors competing for its contract. After the award, the winner becomes the incumbent; alternative vendors determine the agency's replacement option. Applicants bear administrative burdens but are not strategic players in the baseline.

1. **Contract design:** The agency chooses effective monitoring intensity \(m\), portability requirements \(p\), and payment terms. Treat the enforceable failure consequence \(F\) as fixed initially.
2. **Award:** Vendors compete on initial price \(P_0\), anticipating implementation costs and continuation opportunities.
3. **Implementation:** The winner chooses quality effort \(e\) and proprietary dependence \(k\).
4. **Continuation:** With probability \(\lambda\), an exogenous policy change or operational need requires additional work. The agency and incumbent bargain over an amendment. The agency can instead use a replacement vendor.

The baseline holds the arrival of additional work independent of vendor effort. It therefore does not model deliberate quality degradation to generate remediation revenue. That stronger mechanism requires an explicit extension distinguishing billable new work from defects covered by existing obligations.

## 2. Primitives and assumptions

| Symbol | Meaning |
| --- | --- |
| \(P_0\) | Initial award payment |
| \(e\geq0\) | Vendor quality effort |
| \(k\geq0\) | Investment in proprietary dependence |
| \(m\in[0,1]\) | Probability that a failure is detected and enforcement occurs |
| \(p\geq0\) | Agency portability requirements |
| \(q(e)\in[0,1]\) | Probability of satisfactory performance |
| \(C(e)\) | Quality effort cost |
| \(K(k)\) | Cost of creating dependence |
| \(F\geq0\) | Vendor consequence for an enforced failure |
| \(\lambda\in[0,1]\) | Probability of additional work |
| \(c_I\) | Incumbent cost of the additional work |
| \(c_R\) | Replacement vendor's price for that work |
| \(S(k,p)\) | Agency switching cost |
| \(\theta\in[0,1]\) | Incumbent bargaining weight |
| \(V\) | Agency value of satisfactory performance |
| \(B(e)\) | Expected applicant burden |
| \(\omega\geq0\) | Agency weight on applicant burden |
| \(G(m,p)\) | Agency cost of monitoring and portability |

Assume risk neutrality, \(q'>0\), \(q''\leq0\), increasing convex \(C\) and \(K\), and \(B'<0\). Costs and bargaining conditions are common knowledge in the baseline. The agency observes contract terms but cannot directly contract on effort or dependence. Monitoring makes performance failures enforceable with probability \(m\).

Quality and dependence are separate choices. Dependence has no productive benefit in this deliberately simple baseline; an extension should allow proprietary integration to improve service or reduce implementation cost. All monetary quantities can be interpreted as discounted values.

## 3. Continuation bargaining

Start with an additive switching-cost specification:

\[
S(k,p)=s_0+\alpha k-\beta p,
\]

with \(\alpha,\beta>0\), restricted to a domain where \(S\geq0\).

If bargaining fails, the agency buys the additional work from a replacement vendor at total cost \(c_R+S\), and the incumbent receives no continuation profit. Continuing with the incumbent creates surplus

\[
\Delta(k,p)=c_R+S(k,p)-c_I.
\]

For \(\Delta\geq0\), generalized Nash bargaining solves

\[
\max_A (A-c_I)^\theta[c_R+S(k,p)-A]^{1-\theta},
\]

giving

\[
A^*=c_I+\theta\Delta(k,p).
\]

The incumbent receives margin \(\theta\Delta\); the agency retains surplus \((1-\theta)\Delta\) relative to replacement. If \(\Delta<0\), replacement is efficient and this interior continuation formula does not apply. Subsequent baseline expressions assume the equilibrium lies in the continuation region.

Higher switching costs increase the amendment margin. This is a bargaining mechanism, not proof that an amendment is unnecessary or improperly priced.

## 4. Vendor choices

Expected vendor profit is

\[
\Pi=P_0-C(e)-K(k)+\lambda\theta\Delta(k,p)-mF[1-q(e)].
\]

An interior optimum under the additive specification satisfies

\[
C'(e^*)=mFq'(e^*),
\qquad
K'(k^*)=\lambda\theta\alpha.
\]

Under the stated curvature assumptions, stronger effective enforcement raises quality effort, while a higher probability of additional work or greater vendor bargaining power raises investment in dependence. Boundary solutions must be checked when effort or dependence is zero.

### Portability and the incentive to create dependence

Additive portability reduces switching costs and amendment prices, but it does **not** change the marginal return to dependence within the continuation region. To capture portability weakening that incentive, use

\[
S(k,p)=s_0+\frac{\alpha k}{1+p}.
\]

Then

\[
K'(k^*)=\frac{\lambda\theta\alpha}{1+p}.
\]

With strictly convex \(K\), stronger portability lowers equilibrium dependence as well as the switching cost attributable to that dependence. This specification leaves the unavoidable baseline switching cost \(s_0\) unchanged.

## 5. Initial competition and lifecycle payments

With identical vendors, free entry, unrestricted feasible bids, and fully anticipated continuation profits, initial competition drives expected total profit to zero:

\[
P_0^*=C(e^*)+K(k^*)+mF[1-q(e^*)]
-\lambda\theta\Delta(k^*,p).
\]

Expected amendment margins can therefore support low initial bids without deception. A positive amendment margin is not the same as positive expected total profit.

In the continuation region, expected gross lifecycle payments are

\[
P_0^*+\lambda A^*
=C(e^*)+K(k^*)+mF[1-q(e^*)]+\lambda c_I.
\]

Thus, with full competition, anticipated bargaining margins cancel between initial and subsequent payments. Dependence can still waste resources through \(K(k^*)\), and insufficient quality can still impose applicant burdens. Lower amendment prices alone need not imply an equal reduction in lifecycle expenditures because initial bids can adjust.

Persistent excess expected profits require additional frictions, such as limited entry, heterogeneous vendor advantages, buyer misperceptions, or restrictions on how far initial prices can fall. A nonnegative bid constraint can bind if expected continuation margins exceed initial costs; the zero-profit expression then requires reconsideration.

## 6. Agency objective

A baseline agency objective is

\[
W=Vq(e^*)-P_0-\lambda A^*-\omega B(e^*)-G(m,p).
\]

The agency anticipates vendor responses when choosing \(m\) and \(p\). A small \(\omega\) means that applicant burden has little influence on procurement decisions, even when it is socially costly.

This expression treats \(F\) as a vendor consequence that is not received as agency revenue. If \(F\) is instead a monetary penalty paid to the agency, add \(mF[1-q(e^*)]\) to its objective. This accounting choice matters for evaluating enforcement: transfers should not be confused with real resource costs.

Agency value is also distinct from total social welfare. A social-welfare calculation should count real implementation, monitoring, switching, and burden costs, while treating payments between the agency and vendors as transfers where appropriate.

## 7. Baseline predictions

1. **Enforcement and quality:** Greater effective enforcement increases quality effort when failures are measurable and consequences are credible.
2. **Future work and dependence:** More likely amendments increase investment in dependence when that investment strengthens continuation bargaining power.
3. **Portability:** Portability lowers amendment margins; it also reduces dependence investment when it lowers the marginal effect of proprietary investment on switching costs.
4. **Initial-price offsets:** Anticipated continuation margins lower competitive initial bids. Award prices alone are insufficient to evaluate procurement cost.
5. **Burden externalization:** Weak agency weighting of applicant burden can lead to inadequate monitoring even when vendor profits are competed away.

These are conditional theoretical predictions. Empirical associations need not identify the mechanisms: complex systems can simultaneously have greater switching costs, more amendments, and more operational failures.

## 8. Extensions linked to the manuscript

| Scenario | Proposed extension | Question or prediction |
| --- | --- | --- |
| Repeated verification | Vendor influences billable checks \(n\), with payment \(tn\) and a separate accuracy outcome | Does marginal payment reward avoidable checks after accounting for mandated procedures? |
| Flags rather than accuracy | Payment rewards flagged cases; false positives impose weak contractual consequences | Does the vendor choose an excessively permissive flagging threshold? |
| Cooperative purchasing | Multiple agencies can invest in shared and local validation | Is validation underprovided when benefits spill over, and when does local mismatch offset shared testing benefits? |
| Service-continuity extensions | Replacement risks interruption of essential services | Does a weaker outside option increase amendment or renewal margins? |
| Vendor-shaped specifications | An incumbent can influence requirements before entry | Do restrictive specifications reduce entry and prevent initial competition from dissipating continuation rents? |
| Layered suppliers | Integrator, software producer, and data provider divide control and liability | Does fragmented responsibility reduce enforceable quality incentives? |
| Changes after evaluation | Vendor can change configurations after acceptance under imperfect detection | When do savings from substitution accrue to the vendor while quality costs fall on the agency? |
| Generative AI review labor | Vendor effort and agency review labor jointly determine accuracy | Can required human review shift quality-control costs to the agency and reduce vendor effort? |
| Agency-funded adaptation | Ownership and transferability of retrieval resources and evaluation assets affect switching costs | Do contractual rights prevent publicly funded adaptation from strengthening incumbent dependence? |
| Agentic usage | Vendor controls retries, tool calls, and delegated tasks under metered payment | Does usage pricing reward costly workflows relative to verified, correct completion? |
| Agentic action and liability | Actions require permissions and can cause recoverable or irreversible harm | How do authorization limits and recovery obligations affect effort, autonomy, and public costs? |

The table is an extension roadmap. [Models 2–9](extensions.md) now solve selected continuation games for several of these mechanisms; the remaining ideas are not yet solved games. Their predictions depend on the specified control rights, observability, costs, and payment rules. In particular, mandated checks should not be modeled as vendor choices, and human review should not automatically be treated as waste.

## 9. Suggested first simulation

Use the portability-interaction specification and functional forms

\[
q(e)=1-\exp(-e),\quad C(e)=\frac{c_e}{2}e^2,
\quad K(k)=\frac{c_k}{2}k^2,
\]

\[
B(e)=b\exp(-e),\qquad
G(m,p)=\frac{g_m}{2}m^2+\frac{g_p}{2}p^2,
\]

with positive cost parameters. Then quality solves

\[
c_e e^*=mF\exp(-e^*),
\]

and dependence is

\[
k^*=\frac{\lambda\theta\alpha}{c_k(1+p)}.
\]

For a simple baseline, choose parameters with \(c_R+s_0\geq c_I\) so continuation is always feasible. Check whether the competitive initial bid remains nonnegative before imposing any bid floor.

Compare contract designs across monitoring, portability, amendment frequency, bargaining power, and the agency's weight on burden. Report initial prices, amendment prices, gross and net lifecycle payments, total expected vendor profits, quality, dependence, and applicant burden separately. Solve the agency's contract-design problem after verifying vendor responses and boundary cases.

The [simulation project](../simulation/README.md) implements this baseline, six standalone extensions, two combined games, the agency's contract-design problem (including the choice of \(m\) and \(p\) here), and a calibration to the contract documents in `data/`.

## 10. Evidence needed

Potential empirical measures include initial bids and exclusions, amendment histories, portability and data rights, transition provisions, performance standards, enforcement records, invoices, verified service outcomes, and applicant interactions. Tests should account for scope changes, caseload, technical complexity, regulation, and the reasons for additional work.

The manuscript's EPIC and StateScoop materials can help identify vendors and contracting arrangements. Establishing bargaining power, excess profits, intentional degradation, or burden-shifting mechanisms requires additional contract, cost, performance, and implementation evidence.
