# Model 7. Post-award substitution and audit credibility

> Moved from `extensions.md` during the 2026-11 restructure; text unchanged except headings and links. The original is in [`archive/original/`](../archive/original/).

> Shared conventions for all models (risk neutrality, transfers vs. real costs, continuation games after award) are stated in [the folder README](../README.md#conventions).

## Loophole and timing

A vendor passes acceptance with a high-quality configuration. It then chooses whether to retain it or substitute a cheaper configuration. Substitution saves the vendor \(s>0\) over the remaining contract and causes incremental expected public harm \(H\geq0\). The agency commits to audit probability \(a\in[0,1]\), at expected cost \(ka\), where \(k>0\).

Conditional on substitution and audit, evidence supports enforcement with probability \(d\in(0,1]\). Detection imposes a penalty \(F\geq0\) and loss of future vendor margin \(R\geq0\). Audits occur after the harm represented by \(H\); they deter through expected sanctions rather than undoing that harm. The baseline configuration has zero incremental payoff and harm.

## Vendor response and deterrence

The vendor substitutes if

\[
s>ad(F+R).
\]

For \(F+R>0\), the minimum weakly deterring audit probability is

\[
a_{\min}=\frac{s}{d(F+R)}.
\]

Strict deterrence requires a probability above this threshold, unless ties favor retaining quality. If \(s>d(F+R)\), even certain auditing cannot deter substitution under the available remedies. If \(F+R=0\), no audit probability deters positive cost savings.

An agency minimizing expected harm plus audit expenditure, and not retaining sanction revenue, chooses between tolerating substitution at \(a=0\) and deterring at \(a_{\min}\), whenever that threshold is feasible. Under tie-breaking in favor of retention, deterrence is preferred when

\[
ka_{\min}<H.
\]

Intermediate audit probabilities below the threshold add expense without changing the vendor's choice in this discrete model. The agency objective here excludes recovered fines; if the agency retains them, expected sanction revenue must be included and its optimum can change.

## Social benchmark and interaction with the baseline

Cost savings \(s\) are real resource savings, so substitution is socially beneficial absent other costs when \(s>H\). Deterrence is not automatically desirable merely because the supplier benefits. If substitution is harmful on net, \(H>s\), the social comparison between toleration and deterrence includes audit cost: deterring is worthwhile when

\[
ka_{\min}<H-s,
\]

assuming sanctions are transfers and termination has no additional real costs. Real replacement or interruption costs would also need to enter welfare.

The future margin \(R\) links this model to the baseline: expected continuation business can discipline quality if it is genuinely at risk. But severe agency dependence can make termination noncredible. If only fraction \(\rho\in[0,1]\) of the threatened loss is credibly enforceable, replace \(R\) by \(\rho R\). Lower credibility raises the audit probability needed for deterrence. This extension treats \(\rho\) as a parameter; a renegotiation game would be needed to derive it.

**Contract implication:** Specify performance floors, change notification, audit evidence, and feasible remedies. A cheaper configuration that meets the same public standard should not be treated as harmful substitution. Credible remedies matter more than nominal termination language.

**Evidence and distinguishing prediction:** Look for changes in configuration, cost, and measured quality after acceptance, and relate them to auditability and credible remedies. Version changes alone cannot establish degradation or inappropriate conduct.

