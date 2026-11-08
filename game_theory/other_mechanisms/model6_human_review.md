# Model 6. Human review and the agency's inability to commit

> Moved from `extensions.md` during the 2026-11 restructure; text unchanged except headings and links. The original is in [`archive/original/`](../archive/original/).

> Shared conventions for all models (risk neutrality, transfers vs. real costs, continuation games after award) are stated in [the folder README](../README.md#conventions).

The [OpenSpiel extension](model6_noisy_review.md) relaxes observable quality to a noisy
diagnostic, checks equilibrium deviation gains, and compares discretionary review
with enforceable commitment. The baseline below remains its analytical benchmark.

## Loophole and timing

The vendor receives a fixed contract payment and chooses high or low quality effort. High effort costs \(c>0\) and gives raw error probability \(p_H\); low effort costs zero and gives \(p_L>p_H\). Define \(\Delta=p_L-p_H>0\).

The agency then observes a diagnostic revealing the resulting error rate and chooses review \(r\in\{0,1\}\). Review costs real staff resources \(h>0\) and, for tractability, catches all errors before they cause harm. An uncorrected error causes agency/applicant loss \(L>0\), and the vendor pays a penalty \(f\geq0\) to the agency. Only uncorrected errors trigger the penalty; raw errors corrected by staff do not.

Effort is not directly contractible, and the diagnostic does not itself trigger a remedy. The agency cannot commit in advance to forgo review when review later becomes worthwhile. This is a sequential game with observable quality at the review stage, not a hidden-action inference game.

## Backward induction

Assume \(0\leq f<L\), so the agency's net loss from an uncorrected error is \(D=L-f>0\). Its review cost is \(h\); its expected cost without review is \(p_eD\). Thus

\[
r(e)=1\quad\text{if}\quad h<p_eD.
\]

The vendor's cost is

\[
C_V(e)=c\mathbf{1}\{e=H\}+f p_e[1-r(e)].
\]

Away from equality boundaries, there are three regimes:

| Review cost | Agency response | Vendor equilibrium choice |
| --- | --- | --- |
| \(h<p_HD\) | Reviews after either effort | Low effort, since review eliminates all penalties |
| \(p_HD<h<p_LD\) | Reviews after low effort only | Low effort: its cost is zero, versus \(c+fp_H\) under high effort |
| \(h>p_LD\) | Reviews after neither effort | High effort iff \(c<f\Delta\) |

The middle regime captures the commitment problem most sharply. The agency would like the vendor to prevent errors, but once low quality arrives it is worthwhile to supply the missing review labor. The vendor anticipates that response.

## Welfare comparison and implications

Penalty payments are transfers. A planner able to choose both effort and review compares total costs

\[
C^{SP}(H)=c+\min\{h,p_HL\},\qquad
C^{SP}(L)=\min\{h,p_LL\}.
\]

The low-effort equilibrium is inefficient only when the high-effort expression is smaller, or the agency's transfer-sensitive review choice itself differs from the social choice. Cheap review can be efficient; human review is not inherently a procurement failure.

For example, let \(p_H=0.1,p_L=0.5,L=100,f=20,h=20,c=5\). The agency reviews only after low effort because \(8<20<40\). The equilibrium is low effort plus review, with real cost 20. A planner chooses high effort and no review, with real cost \(5+10=15\).

**Contract implication:** Measure raw output errors and review labor, rather than only errors that survive agency correction. A remedy tied to verified raw errors can preserve effort incentives even when staff prevent downstream harm. Payment for agency review costs can also change incentives, but its effect depends on attribution and enforceability.

**Evidence and distinguishing prediction:** Systems can show few final errors while imposing substantial public review labor. Compare raw error rates, staff corrections, handoffs, and total time per correct case. Test whether vendor effort responds to raw-error standards rather than only final-outcome penalties.

