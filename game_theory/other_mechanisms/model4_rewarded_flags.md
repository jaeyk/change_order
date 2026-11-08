# Model 4. Rewarding flags instead of correct decisions

> Moved from `extensions.md` during the 2026-11 restructure; text unchanged except headings and links. The original is in [`archive/original/`](../archive/original/).

> Shared conventions for all models (risk neutrality, transfers vs. real costs, continuation games after award) are stated in [the folder README](../README.md#conventions).

## Loophole and timing

The agency sets a reward \(t\geq0\) per flagged case and an enforceable penalty \(f\geq0\) for a false flag. The vendor observes a calibrated posterior probability \(z\in[0,1]\) that a case contains a relevant payment error, then chooses whether to flag it. Payment error is not assumed to mean intentional fraud.

Flagging has real processing cost \(c\geq0\). A false flag is identified and penalized with probability \(m\in[0,1]\). The vendor earns zero incremental payoff from not flagging. Calibration and case composition are fixed; manipulating scores is outside this model.

## Vendor and public thresholds

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

## Implications

Higher per-flag rewards lower the vendor threshold. For \(t>c\), stronger false-positive enforcement raises it. These results concern marginal cases, not a claim that all flags are unnecessary.

Because false negatives are not directly penalized here, simply removing flag rewards can generate underflagging. A richer design can reward validated discoveries and account for missed errors as well as erroneous flags. Selective appeals also matter: observed reversals are not an unbiased measure of all false positives if many applicants cannot appeal.

**Contract implication:** Avoid equating flags or estimated savings with verified recoveries and accurate decisions. Include the costs of false positives and missed errors in the measurement design.

**Evidence and distinguishing prediction:** Changes in per-flag incentives should shift thresholds and the composition of marginal flagged cases, conditional on underlying prevalence. Use representative adjudication samples, appeal-adjusted outcomes, and actual recoveries rather than only the number of flags.

