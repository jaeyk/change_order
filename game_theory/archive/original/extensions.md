# Extensions: procurement loopholes, combined games, design, and calibration

These models extend the [baseline procurement game](README.md) and the mechanisms in the [vendor manuscript memo](../manuscript/vendor_exploitation.md). Each changes one assumption so its mechanism can be distinguished from switching-cost bargaining. They are proposed theoretical models with conditional analytical results, not evidence that a vendor used a loophole.

## How to read and combine the models

Each model specifies a continuation game after award. Contract parameters are chosen and committed before the vendor acts; they are fixed when solving the continuation equilibrium. Agency decisions within the game are stated explicitly. Optimal initial contract design and competitive bidding are separate stages, not claimed to be solved here.

Fixed initial payments are omitted from continuation payoffs because they do not affect the choices examined. Vendors must still satisfy participation constraints. As in the baseline, fully informed initial competition can offset anticipated continuation margins through lower bids; distortions in effort, workload, validation, and burden can survive that offset. Persistent excess total profits require an entry, information, financing, or bargaining friction.

Unless stated otherwise, players are risk neutral, parameters are common knowledge, and penalties are enforceable expected monetary transfers. Social comparisons exclude transfers and count real costs and public harm. Symbols are local to each model. Equality in a decision threshold permits indifference; strict inequalities give unique choices.

| Model | Assumption changed from baseline | Central result |
| --- | --- | --- |
| 2. Paid remediation | Vendor effort changes future billable work | Paid repair margins can weaken prevention incentives |
| 3. Metered workflows | Vendor controls the quantity purchased | Per-action payment can create excessive work; fixed fees can create too little |
| 4. Rewarded flags | Payment rewards an intermediate metric | A vendor's flagging threshold can differ from the public-value threshold |
| 5. Shared validation | Multiple agencies benefit from testing | Shared validation can be underprovided even with rational buyers |
| 6. Human review | Agency labor substitutes for vendor effort | Ex post review can induce low vendor effort and hidden public labor costs |
| 7. Post-award substitution | Delivered quality can change after acceptance | Limited detection makes cheaper, harmful substitution privately attractive |
| 8. Lock-in and remediation (1+2) | Uncovered defects are priced by lock-in bargaining | Portability raises prevention; dependence and defects reinforce each other |
| 9. Metered work and review (3+6) | Agency review follows vendor-chosen billable work | Vendors can bunch at the review threshold; usage pay and public correction labor substitute |

Models 2–7 follow Model 1, the existing baseline. Models 8 and 9 combine the two pairs identified below as highest priority; the models need not all be combined into one large game.

## Model 2. Paid remediation and endogenous defects

### Loophole and timing

The baseline treats additional work as exogenous. Here the vendor can prevent some defects, and unresolved defects may become paid amendments.

The agency first fixes a warranty/enforcement arrangement. The vendor chooses prevention effort \(e\geq0\). A defect occurs with probability \(d(e)=\exp(-e)\). Conditional on a defect, an enforceable warranty classification occurs with probability \(w\in[0,1]\). Otherwise the agency purchases repair as additional work. The vendor anticipates these outcomes when choosing effort.

Assume repair is necessary and the agency will purchase it at the specified price; this requires its avoided service loss or replacement cost to exceed that price. The model does not derive the repair price. It can be supplied by the baseline bargaining game.

### Payoff and solution

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

### Public benchmark and implications

Let \(H>0\) be the expected real repair cost plus agency and applicant harm per defect, excluding transfers. A planner minimizes \(ce^2/2+H\exp(-e)\), giving

\[
ce^{SP}=H\exp(-e^{SP}).
\]

The vendor underinvests if \(D<H\), matches the benchmark if \(D=H\), and overinvests if \(D>H\). Thus stronger penalties are not unconditionally optimal once they exceed the social loss or have enforcement costs.

The loophole is payment for preventable failure combined with weak allocation of repair responsibility. The equilibrium demonstrates reduced prevention, not affirmative sabotage or intent to misrepresent quality.

**Contract implication:** Classify promised functionality and new scope clearly; make covered repairs nonbillable and enforce the distinction. Any repair-price restriction must still leave participation and service-continuity constraints feasible.

**Evidence and distinguishing prediction:** Compare defect incidence and prevention investment across contracts with different enforceable repair obligations, conditional on complexity. Paid repair margins should matter less where warranty enforcement is strong. Amendment totals alone cannot distinguish this mechanism from legitimate scope changes.

## Model 3. Metered verification and agent-selected work

### Loophole and timing

The agency commits to a per-action payment \(t\geq0\) and a bonus \(R\geq0\) for an independently verified successful outcome. The vendor then chooses discretionary workflow intensity \(n\in[0,\bar n]\). This can represent optional verification, retries, tool calls, or delegated subtasks. Legally required checks are fixed outside \(n\).

Conditional on fixed case difficulty, verified success has probability

\[
q(n)=1-\exp(-an),\qquad a>0.
\]

The vendor bears real cost \(cn+dn^2/2\), with \(c\geq0,d>0\). Applicants and agency staff bear additional real cost \(bn\), with \(b\geq0\). The agency values verified success at \(V>0\).

### Payoff and solution

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

### Implications and limits

Usage pricing does not automatically create excessive work. Excess depends on the price, outcome incentives, real processing costs, and burdens. A fixed fee with no outcome reward gives \(t=R=0\) and zero discretionary work, potentially creating severe underprovision. A cost cap alone can similarly truncate useful work.

An outcome bonus \(R=V\) plus a charge equal to external burden per action would align marginal incentives in this simplified setting. This uses a net action payment \(t=-b\), outside the nonnegative usage-price restriction, and requires a fixed payment sufficient for participation. It is an alignment benchmark, not a ready-made contract recommendation.

For agentic systems, \(n\) represents workflow choices economically controlled by the supplier through orchestration. It does not assume the software is itself a strategic player. If the agency mandates all calls, this vendor-choice mechanism disappears. Outcome measurement must include correctness and authorization; a nominally closed case is not sufficient.

**Contract implication:** Combine verified completion measures with cost and workload visibility; evaluate caps against successful completion rather than call reduction alone.

**Evidence and distinguishing prediction:** Holding case mix and verified success constant, higher marginal action payments predict higher workflow intensity at an interior optimum. Measure cost per correct completed case, retries, repeat checks, applicant interactions, and failure billing. Raw call counts alone are inconclusive.

## Model 4. Rewarding flags instead of correct decisions

### Loophole and timing

The agency sets a reward \(t\geq0\) per flagged case and an enforceable penalty \(f\geq0\) for a false flag. The vendor observes a calibrated posterior probability \(z\in[0,1]\) that a case contains a relevant payment error, then chooses whether to flag it. Payment error is not assumed to mean intentional fraud.

Flagging has real processing cost \(c\geq0\). A false flag is identified and penalized with probability \(m\in[0,1]\). The vendor earns zero incremental payoff from not flagging. Calibration and case composition are fixed; manipulating scores is outside this model.

### Vendor and public thresholds

The incremental vendor payoff from a flag is

\[
u_V(z)=t-c-mf(1-z).
\]

For \(mf>0\), the vendor flags if

\[
z\geq\tau_V=1-\frac{t-c}{mf},
\]

with thresholds outside \([0,1]\) interpreted as flag-none or flag-all policies, allowing indifference at endpoints. If \(mf=0\), it flags all cases when \(t>c\), none when \(t<c\), and is indifferent when equal.

Suppose correctly flagging an error provides public benefit \(v>0\), while a false flag imposes harm \(h\geq0\). Relative to no flag, public value is

\[
u_{SP}(z)=zv-(1-z)h-c.
\]

The public threshold is

\[
\tau_{SP}=\frac{h+c}{v+h}.
\]

If \(c>v\), no case yields positive public value from flagging. Otherwise overflagging occurs when the vendor threshold is below the public threshold and there is probability mass between them. Underflagging occurs when the ordering is reversed.

An interior threshold can be aligned by setting

\[
t=c+mf(1-\tau_{SP}),
\]

but this requires reliable calibration, enforceable false-positive identification, and knowledge of public benefits and harms.

### Implications

Higher per-flag rewards lower the vendor threshold. For \(t>c\), stronger false-positive enforcement raises it. These results concern marginal cases, not a claim that all flags are unnecessary.

Because false negatives are not directly penalized here, simply removing flag rewards can generate underflagging. A richer design can reward validated discoveries and account for missed errors as well as erroneous flags. Selective appeals also matter: observed reversals are not an unbiased measure of all false positives if many applicants cannot appeal.

**Contract implication:** Avoid equating flags or estimated savings with verified recoveries and accurate decisions. Include the costs of false positives and missed errors in the measurement design.

**Evidence and distinguishing prediction:** Changes in per-flag incentives should shift thresholds and the composition of marginal flagged cases, conditional on underlying prevalence. Use representative adjudication samples, appeal-adjusted outcomes, and actual recoveries rather than only the number of flags.

## Model 5. Cooperative purchasing and shared validation

### Loophole and timing

After a shared purchasing arrangement makes a product available, \(N\geq2\) agencies simultaneously decide whether to fund a common validation test. Each chooses \(x_i\in\{0,1\}\). One test is sufficient, and its result is shared. Testing costs the agency \(c>0\); each agency receives expected benefit \(B>0\) if at least one agency tests.

The benefit is the expected avoided loss from detecting and responding to a common defect. Product availability is not assumed to establish actual deployment. Participation and deployment are fixed for this subgame; the vendor is passive here.

### Payoffs and equilibria

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

### Local validation and institutional implications

A shared test need not establish local suitability. Add an independent local test costing \(\ell_i\) and yielding local benefit \(L_i\), with no spillovers. With full internalization, agency \(i\) performs it exactly when \(L_i\geq\ell_i\). There is no free-riding problem in that independent local decision.

To explain inadequate local testing, introduce a separate mechanism: underestimated local mismatch or applicant harms not fully valued by the agency. If it values only \(\omega_iL_i\), \(0\leq\omega_i<1\), local testing is omitted despite positive social value when

\[
\omega_iL_i<\ell_i<L_i.
\]

The simulation implements this local decision with symmetric agencies (parameters \(\ell\), \(L\), \(\omega\)), testing at indifference. It reports local welfare loss \(N(L-\ell)\) in the omission region and adds it to the shared-test loss.

**Contract implication:** Assign and fund common testing explicitly, while separating it from jurisdiction-specific validation. Shared purchasing can improve validation through cost sharing; the model does not imply cooperative purchasing is inherently harmful.

**Evidence and distinguishing prediction:** Compare arrangements with assigned validation responsibility against arrangements relying on voluntary contributions. Distinguish common testing, local testing, purchasing eligibility, actual orders, and deployment. Group size alone cannot identify free riding because group composition and coordination differ.

## Model 6. Human review and the agency's inability to commit

The [OpenSpiel extension](noisy_review.md) relaxes observable quality to a noisy
diagnostic, checks equilibrium deviation gains, and compares discretionary review
with enforceable commitment. The baseline below remains its analytical benchmark.

### Loophole and timing

The vendor receives a fixed contract payment and chooses high or low quality effort. High effort costs \(c>0\) and gives raw error probability \(p_H\); low effort costs zero and gives \(p_L>p_H\). Define \(\Delta=p_L-p_H>0\).

The agency then observes a diagnostic revealing the resulting error rate and chooses review \(r\in\{0,1\}\). Review costs real staff resources \(h>0\) and, for tractability, catches all errors before they cause harm. An uncorrected error causes agency/applicant loss \(L>0\), and the vendor pays a penalty \(f\geq0\) to the agency. Only uncorrected errors trigger the penalty; raw errors corrected by staff do not.

Effort is not directly contractible, and the diagnostic does not itself trigger a remedy. The agency cannot commit in advance to forgo review when review later becomes worthwhile. This is a sequential game with observable quality at the review stage, not a hidden-action inference game.

### Backward induction

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

### Welfare comparison and implications

Penalty payments are transfers. A planner able to choose both effort and review compares total costs

\[
C^{SP}(H)=c+\min\{h,p_HL\},\qquad
C^{SP}(L)=\min\{h,p_LL\}.
\]

The low-effort equilibrium is inefficient only when the high-effort expression is smaller, or the agency's transfer-sensitive review choice itself differs from the social choice. Cheap review can be efficient; human review is not inherently a procurement failure.

For example, let \(p_H=0.1,p_L=0.5,L=100,f=20,h=20,c=5\). The agency reviews only after low effort because \(8<20<40\). The equilibrium is low effort plus review, with real cost 20. A planner chooses high effort and no review, with real cost \(5+10=15\).

**Contract implication:** Measure raw output errors and review labor, rather than only errors that survive agency correction. A remedy tied to verified raw errors can preserve effort incentives even when staff prevent downstream harm. Payment for agency review costs can also change incentives, but its effect depends on attribution and enforceability.

**Evidence and distinguishing prediction:** Systems can show few final errors while imposing substantial public review labor. Compare raw error rates, staff corrections, handoffs, and total time per correct case. Test whether vendor effort responds to raw-error standards rather than only final-outcome penalties.

## Model 7. Post-award substitution and audit credibility

### Loophole and timing

A vendor passes acceptance with a high-quality configuration. It then chooses whether to retain it or substitute a cheaper configuration. Substitution saves the vendor \(s>0\) over the remaining contract and causes incremental expected public harm \(H\geq0\). The agency commits to audit probability \(a\in[0,1]\), at expected cost \(ka\), where \(k>0\).

Conditional on substitution and audit, evidence supports enforcement with probability \(d\in(0,1]\). Detection imposes a penalty \(F\geq0\) and loss of future vendor margin \(R\geq0\). Audits occur after the harm represented by \(H\); they deter through expected sanctions rather than undoing that harm. The baseline configuration has zero incremental payoff and harm.

### Vendor response and deterrence

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

### Social benchmark and interaction with the baseline

Cost savings \(s\) are real resource savings, so substitution is socially beneficial absent other costs when \(s>H\). Deterrence is not automatically desirable merely because the supplier benefits. If substitution is harmful on net, \(H>s\), the social comparison between toleration and deterrence includes audit cost: deterring is worthwhile when

\[
ka_{\min}<H-s,
\]

assuming sanctions are transfers and termination has no additional real costs. Real replacement or interruption costs would also need to enter welfare.

The future margin \(R\) links this model to the baseline: expected continuation business can discipline quality if it is genuinely at risk. But severe agency dependence can make termination noncredible. If only fraction \(\rho\in[0,1]\) of the threatened loss is credibly enforceable, replace \(R\) by \(\rho R\). Lower credibility raises the audit probability needed for deterrence. This extension treats \(\rho\) as a parameter; a renegotiation game would be needed to derive it.

**Contract implication:** Specify performance floors, change notification, audit evidence, and feasible remedies. A cheaper configuration that meets the same public standard should not be treated as harmful substitution. Credible remedies matter more than nominal termination language.

**Evidence and distinguishing prediction:** Look for changes in configuration, cost, and measured quality after acceptance, and relate them to auditability and credible remedies. Version changes alone cannot establish degradation or inappropriate conduct.

## Model 8. Lock-in and paid remediation (Models 1 + 2)

### Model 8 timing and payoff

This combines the baseline's bargaining over additional work with Model 2's endogenous defects. The agency fixes warranty enforcement \(w\) and portability \(p\). The vendor then chooses prevention effort \(e\) and proprietary dependence \(k\). Exogenous additional work arrives with probability \(\lambda\), as in Model 1. Independently, a defect occurs with probability \(\exp(-e)\). With probability \(w\) it is covered: the vendor repairs it at cost \(r\) and pays penalty \(f\). Otherwise it becomes a paid amendment.

Both kinds of amendment are priced by generalized Nash bargaining against a replacement vendor, with switching cost \(S(k,p)=s_0+\alpha k/(1+p)\). New work is priced at \(A=c_I+\theta(c_R+S-c_I)\) and an uncovered repair at \(r+\mu(k)\), where

\[
\mu(k)=\theta\,[r_R+S(k,p)-r]
\]

and \(r_R\) is the replacement vendor's repair price. The repair margin of Model 2 is now endogenous: dependence raises it. Excluding the initial payment, the vendor's payoff is

\[
\pi(e,k)=-\frac{c}{2}e^2-\frac{c_k}{2}k^2+\lambda\theta\Delta(k,p)+e^{-e}\big[(1-w)\mu(k)-w(r+f)\big].
\]

### Model 8 solution

The payoff is quadratic and concave in \(k\), so the best response is exact:

\[
k^*(e)=\frac{\theta\alpha\,[\lambda+(1-w)e^{-e}]}{c_k(1+p)}.
\]

Dependence now has two returns: leverage over new work and leverage over repairs. More defects raise the second return. Substituting \(k^*(e)\) gives a one-dimensional profile in \(e\). The envelope theorem gives its slope:

\[
-ce+e^{-e}D(k^*(e)),\qquad D(k)=w(r+f)-(1-w)\mu(k).
\]

The profile need not be concave, because dependence and defects are strategic complements. The solver therefore runs a global grid search over \(e\) and then bisects on this slope inside the winning bracket. Competitive initial bids still drive expected profit to zero.

### Model 8 results

- **Feedback loop.** Dependence raises the repair margin. That lowers prevention, which raises defect frequency, which raises the return to dependence.
- **Portability raises prevention.** Portability lowers \(k^*\) and hence \(\mu\), which raises \(D\) and therefore effort. This prediction is absent from both standalone models: in Model 1 portability affects only dependence, and in Model 2 the repair margin is fixed.
- **Bargaining power without lock-in.** If \(\theta=0\), repairs carry no margin and \(k^*=0\). Effort then solves Model 2 with \(\mu=0\).
- **Planner benchmark.** A planner chooses \(k=0\) and \(ce=He^{-e}\). Excess social cost combines underprevention with wasteful dependence.

**Contract implication:** Warranty enforcement and portability are complements. Weak portability makes a given warranty less effective, because every uncovered defect becomes a lock-in-priced amendment.

## Model 9. Metered workflows and agency review (Models 3 + 6)

### Model 9 timing and payoff

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

### Model 9 results

- **Commitment problem with continuous effort.** Below \(n_c\) the agency's review removes the vendor's penalty exposure, as in Model 6. A vendor with \(f>0\) can therefore *bunch* at \(n_c\): it does just little enough work that the agency keeps correcting its errors. The default sweep shows this at \(f=12\), where work stays at the cutoff over a range of usage prices.
- **Usage pay and review substitute.** Higher \(t\) raises work and can push the vendor past \(n_c\). Review then stops, and the public stops paying for corrections, but the public pays for the extra activity instead.
- **Planner benchmark.** The planner chooses \(n\) and review jointly. When it reviews and correction is cheap (\(\kappa a\le c+b\)), it chooses no discretionary work. Paying per action while staff correct the output is then pure excess cost.

**Contract implication:** Price raw correctness, or charge for the agency's correction labor, rather than penalizing only errors that reach applicants. A penalty on uncorrected errors alone is neutralized by the agency's own review.

## Optimal contract design

The continuation games above take contract terms as given. `simulation/design.py` solves the prior stage: the agency commits to instruments within stated bounds, anticipating the equilibrium they induce. Each problem specifies an objective and optional quadratic governance costs \(g x^2/2\) per instrument.

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

`simulation/calibrate.py` reads the models through the contracts in `data/`. Its inputs are:

- hand-verified amendment histories, each with a source quote;
- prices, service-level penalty caps, and negotiated deviations;
- clause codes from a reproducible regular-expression pass that records every match, with manual overrides.

The data identify two quantities. One is the frequency of priced unplanned work (\(\hat\lambda\)). The other is the amendment growth ratio, which pins the amendment price once the base contract is normalized. Coded terms map to monitoring, portability, penalty exposure and warranty enforcement through editable rules.

The records cannot separate the incumbent's cost from its bargaining margin. The bargaining weight \(\theta\) is therefore reported as an identified set: the values for which a nonnegative incumbent cost reproduces the observed amendment. Choices depend on the coded terms and \(\hat\lambda\); the dollar records constrain only how much amendment spending the model can attribute to margin.

The calibration report also re-solves Model 1's design problem at the coded terms. It records structural restrictions for Models 3–5:

- no coded contract pays for verified outcomes;
- none states a false-positive standard;
- cooperative cloud addenda lack local acceptance-testing language.

## A common research and simulation agenda

The models separate six mechanisms that otherwise look alike in expenditure records: paying for defects, paying for activity, rewarding a proxy, underfunding shared scrutiny, relying on agency correction, and changing the delivered product after acceptance.

For each simulation, report vendor revenue and profit separately; also report real vendor costs, agency payments, agency labor, applicant harm, and verified outcomes. Keep transfer accounting explicit. Start with continuation choices, then add competitive initial bids and participation constraints. Do not interpret a fixed-fee change as reducing profit or improving welfare without recalculating behavior and initial prices.

Useful first comparisons are:

1. Model 2: vary paid repair margins and warranty enforcement; locate the zero-effort threshold.
2. Model 3: compare usage-only, outcome-only, and mixed payment across case difficulty and burden; include both overprovision and underprovision.
3. Model 4: compare vendor and public thresholds under changes in error prevalence, calibration, rewards, and enforceability.
4. Model 5: compare coordinated testing with pure and symmetric mixed equilibria; report both omitted and duplicated tests.
5. Model 6: map the three review regimes and compare equilibrium costs with joint optimal effort and review.
6. Model 7: vary auditability, available remedies, and credible continuation losses; distinguish harmless cost reductions from harmful substitution.

The highest-priority combined extension is Model 1 plus Model 2: endogenous defects produce amendment opportunities whose margins depend on lock-in. A second is Model 3 plus Model 6: metered workflows and agency review jointly determine the full cost of correct completion. Combining models requires re-solving choices, since standalone comparative statics need not survive their interaction.

These notes provide analytical continuation equilibria and conditional benchmarks. The [simulation project](../simulation/README.md) implements the baseline, all six standalone extensions, the two priority combined games (Models 8 and 9), optimal contract design over stated instruments, and a calibration to the contract documents. Structural estimation with cost data, other combinations, and causal empirical tests remain future work.
