# Model 3. Metered verification and agent-selected work

> Moved from `extensions.md` during the 2026-11 restructure; text unchanged except headings and links. The original is in [`archive/original/`](../archive/original/).

> Shared conventions for all models (risk neutrality, transfers vs. real costs, continuation games after award) are stated in [the folder README](../README.md#conventions).

## Loophole and timing

The agency commits to a per-action payment \(t\geq0\) and a bonus \(R\geq0\) for an independently verified successful outcome. The vendor then chooses discretionary workflow intensity \(n\in[0,\bar n]\). This can represent optional verification, retries, tool calls, or delegated subtasks. Legally required checks are fixed outside \(n\).

Conditional on fixed case difficulty, verified success has probability

\[
q(n)=1-\exp(-an),\qquad a>0.
\]

The vendor bears real cost \(cn+dn^2/2\), with \(c\geq0,d>0\). Applicants and agency staff bear additional real cost \(bn\), with \(b\geq0\). The agency values verified success at \(V>0\).

## Payoff and solution

\[
\pi(n)=(t-c)n-\frac{d}{2}n^2+R[1-\exp(-an)].
\]

The objective is strictly concave. Its interior optimum satisfies

\[
t-c-dn^*+Ra\exp(-an^*)=0.
\]

At zero, choose \(n^*=0\) if \(t-c+Ra\leq0\). At the upper bound, choose \(n^*=\bar n\) if the marginal payoff evaluated there is nonnegative. Otherwise the unique root is interior.

For pure usage payment, \(R=0\):

\[
n^*=\min\{\bar n,\max\{0,(t-c)/d\}\}.
\]

The public benchmark maximizes

\[
W(n)=V[1-\exp(-an)]-(c+b)n-\frac{d}{2}n^2.
\]

At an interior public optimum \(n^{SP}\),

\[
Va\exp(-an^{SP})=c+b+dn^{SP}.
\]

Evaluating the vendor's marginal payoff at that optimum gives

\[
\pi'(n^{SP})=t+b+(R-V)a\exp(-an^{SP}).
\]

If this expression is positive, the vendor chooses more work than the interior public optimum; if negative, less. This comparison uses strict concavity and a common feasible interval.

## Implications and limits

Usage pricing does not automatically create excessive work. Excess depends on the price, outcome incentives, real processing costs, and burdens. A fixed fee with no outcome reward gives \(t=R=0\) and zero discretionary work, potentially creating severe underprovision. A cost cap alone can similarly truncate useful work.

An outcome bonus \(R=V\) plus a charge equal to external burden per action would align marginal incentives in this simplified setting. This uses a net action payment \(t=-b\), outside the nonnegative usage-price restriction, and requires a fixed payment sufficient for participation. It is an alignment benchmark, not a ready-made contract recommendation.

For agentic systems, \(n\) represents workflow choices economically controlled by the supplier through orchestration. It does not assume the software is itself a strategic player. If the agency mandates all calls, this vendor-choice mechanism disappears. Outcome measurement must include correctness and authorization; a nominally closed case is not sufficient.

**Contract implication:** Combine verified completion measures with cost and workload visibility; evaluate caps against successful completion rather than call reduction alone.

**Evidence and distinguishing prediction:** Holding case mix and verified success constant, higher marginal action payments predict higher workflow intensity at an interior optimum. Measure cost per correct completed case, retries, repeat checks, applicant interactions, and failure billing. Raw call counts alone are inconclusive.

