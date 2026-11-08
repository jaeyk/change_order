# Model 10. Chance versus design: why amendments happen

> New in the 2026-11 restructure. Builds on [Model 1](01_lockin_bargaining.md) (notation for bargaining and switching costs) and connects to [Model 2](02_paid_remediation.md) and [Model 8](03_lockin_and_remediation.md). Status: proposed model with analytical results; not yet simulated or estimated.

## 1. The question

Some amendments happen by chance. A statute changes, caseloads shift, a partner system is replaced. Others happen by design. Required work is left out of the bid or described loosely, so it has to be bought later, when the incumbent can price it under lock-in.

Design pays because the two sides look at different horizons. A vendor earns over the whole life of a product: the base contract, its amendments, renewals and follow-on work. The agency's award decision is made by people judged on getting the agreement signed at a good headline price. Costs that arrive later, often under different staff and budgets, carry less weight at the moment of award.

Model 1 treats the arrival of additional work as exogenous (probability \(\lambda\)). This model makes part of that arrival a vendor choice and asks when competition for the award *rewards* that choice.

## 2. Players, timing, and primitives

1. **Evaluation rules.** The agency commits to how it scores bids: weight \(\phi\in[0,1]\) on anticipated amendment payments, scope-review intensity \(d>0\), and portability \(p\geq0\).
2. **Bidding.** \(N\geq2\) identical vendors each submit a price \(P_0\) and a scope coverage. A bid leaves a share \(g\in[0,\bar g]\) of the required work out of scope or underspecified (the *scope gap*). The agency awards to the lowest perceived cost
   \[
   \hat C=P_0+\phi\,\mathbb E[\text{amendment payments}].
   \]
3. **Implementation.** The winner chooses proprietary dependence \(k\geq0\), as in Model 1. It is not contractible.
4. **Amendments.** Over the lifecycle the agency buys two kinds of additional work:
   - *chance work*: expected quantity \(\lambda_0\geq0\), independent of the vendor;
   - *designed work*: the \(g\) units left out of the bid, which the agency must still buy.

   Each unit is priced by the Model 1 bargaining solution,
   \[
   A(k,p)=c+\theta\,\Delta(k,p),\qquad
   \Delta(k,p)=c_R+S(k,p)-c,\qquad
   S(k,p)=s_0+\frac{\alpha k}{1+p}.
   \]

| Symbol | Meaning |
| --- | --- |
| \(c\) | Real cost per unit of work, the same whether it is done at award or later by amendment |
| \(\lambda_0\) | Expected chance work (units) over the lifecycle |
| \(g\) | Scope gap chosen in the bid; becomes designed amendment work |
| \(D(g)=\tfrac d2g^2\) | Expected cost to the vendor of a gap: risk of being caught in evaluation, disqualified, or losing reputation |
| \(\phi\) | Weight the award decision puts on amendment payments (1 = full lifecycle view; 0 = headline price only) |
| \(k,\;K(k)=\tfrac{c_k}2k^2\) | Proprietary dependence and its cost (Model 1) |
| \(\theta,\alpha,p,s_0,c_R\) | Bargaining weight, dependence effect, portability, base switching cost, replacement price (Model 1) |
| \(\Delta_0=c_R+s_0-c\) | Bargaining surplus without dependence (\(k=0\)) |

Monetary amounts are discounted to the award date. Players are risk neutral and parameters are common knowledge, as in the other models.

## 3. Where \(\phi\) comes from: the horizon gap

Let amendment spending occur over the lifecycle \([0,T]\) with timing density \(a(t)\), and let the award decision weigh only costs inside the decision-maker's accountability horizon \(\tau\leq T\), discounted at rate \(r\). Then
\[
\phi=\frac{\int_0^{\tau}e^{-rt}a(t)\,dt}{\int_0^{T}e^{-rt}a(t)\,dt}.
\]
The vendor's profits count all of \([0,T]\). So \(\phi<1\) whenever \(\tau<T\): the official's term, the budget cycle or the initial contract term ends before the product's life does. An award rule that scores only the bid price is the extreme case \(\phi=0\).

Two consequences follow. First, \(\phi\) falls as the product's life (renewals, extensions, follow-on work) grows relative to the initial term. Second, a vendor that can move designed amendments later in the lifecycle lowers the effective \(\phi\) on exactly those amendments. The baseline below uses a single \(\phi\); Section 8 lists timing choice as an extension.

## 4. Vendor profit and dependence

The vendor delivers \(1-g\) units of base scope at award and performs all amendment work at cost \(c\). Its expected lifecycle profit is
\[
\Pi=P_0-c(1-g)-D(g)-K(k)+(\lambda_0+g)\,\theta\,\Delta(k,p).
\]
Revenue on amendment work covers its cost \(c\) plus the bargaining margin \(\theta\Delta\). So the scope gap converts \(g\) units of competitively priced base work into bargained work.

**Dependence (implementation stage).** \(\Pi\) is strictly concave in \(k\), and
\[
k^*(g)=\frac{(\lambda_0+g)\,\theta\alpha}{c_k(1+p)}.
\]

**Proposition 1 (gaps and lock-in are complements).** Designed amendments raise the return to dependence: \(\partial k^*/\partial g>0\) whenever \(\theta\alpha>0\). Compared with Model 1, where dependence responds only to the chance of additional work, a vendor that plans to sell back omitted scope invests more in making itself hard to replace.

## 5. Bidding equilibrium

Identical vendors compete on perceived cost, so the winning bid earns zero expected profit:
\[
P_0^*(g)=c(1-g)+D(g)+K(k^*(g))-(\lambda_0+g)\,\theta\,\Delta(k^*(g),p).
\]
Substituting into the award rule gives the perceived cost of a bid with gap \(g\):
\[
\hat C(g)=c(1-g)+\phi(\lambda_0+g)c+D(g)+K(k^*)-(1-\phi)(\lambda_0+g)\,\theta\,\Delta(k^*,p).
\]
Competition selects the \(g\) that minimizes \(\hat C\). Write
\[
\beta\equiv\frac{\theta^2\alpha^2}{c_k(1+p)^2}\geq0,
\]
the strength of the lock-in feedback. Using \(K(k^*)=\tfrac\beta2(\lambda_0+g)^2\) and \(\theta\Delta(k^*)=\theta\Delta_0+(\lambda_0+g)\beta\),
\[
\hat C'(g)=-(1-\phi)(c+\theta\Delta_0)+dg-(1-2\phi)(\lambda_0+g)\beta,\qquad
\hat C''(g)=d-(1-2\phi)\beta.
\]

**Proposition 2 (equilibrium scope gap).** If \(d>(1-2\phi)\beta\), the equilibrium gap is
\[
g^*=\min\!\left\{\bar g,\;\max\!\left\{0,\;
\frac{(1-\phi)(c+\theta\Delta_0)+(1-2\phi)\lambda_0\beta}{d-(1-2\phi)\beta}\right\}\right\}.
\]
If \(d\leq(1-2\phi)\beta\), \(\hat C\) is concave in \(g\) and the equilibrium is the corner \(g^*=\bar g\).

Three results follow.

1. **A full lifecycle view removes design.** At \(\phi=1\) the numerator is \(-\lambda_0\beta\leq0\), so \(g^*=0\). Every amendment is then chance work.
2. **The horizon gap alone is enough.** With no bargaining power and no lock-in (\(\theta=0\)), \(g^*=(1-\phi)c/d>0\) whenever \(\phi<1\). Moving work into amendments takes even its *real cost* out of the perceived price, not just a margin. Bargaining power and lock-in amplify the incentive but do not create it.
3. **Lock-in turns the horizon gap into a spiral when the award is price-focused.** For \(\phi<\tfrac12\), dependence raises the amendment price, which raises the payoff to gaps, which raises dependence: \(g^*\) rises with \(\beta\). For \(\phi>\tfrac12\) the feedback reverses. The agency now sees enough of the margin that the induced dependence (a real cost in the bid) outweighs what it hides.

**Comparative statics (interior case).** \(g^*\) falls with \(\phi\) and \(d\), and rises with the base surplus \(\Delta_0\). It rises with the bargaining weight \(\theta\) unambiguously when \(\phi\leq\tfrac12\); above that, the extra lock-in that \(\theta\) induces works against it. Portability \(p\) lowers \(\beta\), so it lowers \(g^*\) when \(\phi<\tfrac12\). (The closed form was checked against a numerical minimization of \(\hat C\) over 2,000 random parameter draws, including the corner cases.)

**Designed share of amendments.** \(\sigma=g^*/(\lambda_0+g^*)\). Total expected amendment work \(\lambda_0+g^*\) mixes the two sources, and the share of design rises as \(\phi\) falls.

## 6. Who pays

With competitive bidding, margins cancel between the low bid and later amendments, as in Model 1. Expected lifecycle payments are
\[
P_0^*+(\lambda_0+g^*)A(k^*)=c(1+\lambda_0)+D(g^*)+K(k^*(g^*)).
\]
Against the full-lifecycle benchmark (\(\phi=1\): \(g=0\), \(k=k^*(0)\)), the agency pays the extra amount
\[
\underbrace{\tfrac d2 g^{*2}}_{\text{gaming the evaluation}}
+\underbrace{\tfrac\beta2\big[(\lambda_0+g^*)^2-\lambda_0^2\big]}_{\text{extra lock-in}}
+\;\varepsilon g^*,
\]
where \(\varepsilon\geq0\) is any real cost of doing work late: rework, delay, applicant burden. None of this is vendor profit under full competition. It is waste created by the evaluation rule.

Three features matter for measurement:

- **The headline price falls.** \(dP_0^*/dg<0\) near \(g=0\). Low awards and large later growth come together by construction. The award-to-final growth ratio rises with \(g^*\), which is the snowball in [Figure 3](../../figures/fig3_amendment_snowball.png).
- **Rents need a friction.** Positive expected profit requires imperfect competition, an incumbency advantage at the next award, or a binding floor \(P_0\geq0\). The floor binds when expected margins exceed base-scope cost, and then the vendor *buys in*: it bids at the floor and keeps the excess.
- **Chance amendments are not waste.** Work \(\lambda_0\) is real and needed. A model or audit that treats all amendment spending as overrun overstates the problem.

## 7. What distinguishes chance from design

| Observable | Chance (\(\lambda_0\)) | Design (\(g\), \(k\)) |
| --- | --- | --- |
| Timing | Follows outside events (statute dates, caseload shocks), spread over the life | Early, when gaps surface at implementation, or late, beyond the award horizon and at renewal points |
| Link to the award price | None | Lower award relative to estimates or other bids predicts more and larger amendments |
| Link to the award rule | None | Fewer designed amendments where awards score lifecycle cost (higher \(\phi\)) or review scope closely (higher \(d\)) |
| Content | New requirements | Work that was in the original need or solicitation; price and time increases without new scope |
| Path over amendments | Count roughly Poisson: constant rate given the contract | Hazard rising with prior amendments where dependence grows (state dependence) |
| Vendor pattern | Explained by type of work | Persistent vendor effects across agencies and buyers for the same type of work |
| Lock-in proxies | Weak relation | Strong relation: proprietary technology, single award, sole-source follow-ons, no portability terms |

No single row identifies design: complex work is both lock-in-prone and exposed to chance. Identification needs variables that move one channel and not the other (Section 9 of [the empirical plan](05_empirical_tests.md)).

## 8. Agency levers implied by the model

| Lever | Parameter | Effect |
| --- | --- | --- |
| Score bids on lifecycle cost (expected amendments, renewals, transition) | \(\phi\uparrow\) | Removes design entirely at \(\phi=1\); weakens the lock-in spiral once \(\phi>\tfrac12\) |
| Review scope completeness before award; independent cost estimates | \(d\uparrow\) | Lowers \(g^*\) directly |
| Portability, data rights, transition assistance | \(p\uparrow\Rightarrow\beta\downarrow,\ \Delta\downarrow\) | Lowers the amendment price and dampens the spiral |
| Pre-priced change rate cards | caps \(\theta\Delta\) | Lowers but does not remove design: the \((1-\phi)c\) term remains |
| Make omitted-but-required scope non-billable | \(g\) not paid | Equivalent to a prohibitive \(D(g)\) when enforceable |
| Keep accountability for lifecycle outcomes with the award decision | \(\tau\uparrow\Rightarrow\phi\uparrow\) | Addresses the horizon gap at its source |

## 9. Extensions

1. **Timing choice.** Let the vendor choose when designed amendments arrive. Backloading past \(\tau\) lowers their effective \(\phi\), which predicts late, extension-type amendments.
2. **Renewals as amendments.** Extensions near expiry are the cheapest way to avoid re-competition. Model the re-bid as an outside option whose cost rises with \(k\).
3. **Stochastic arrival.** Make chance work a Poisson process at rate \(\lambda_0\) and designed work a separate process at rate \(\gamma g\). Counts are then Poisson with mean \(t(\lambda_0+\gamma g)\), so heterogeneity in \(g\) across vendors and agencies produces overdispersion.
4. **Repeated play across agencies.** A vendor's gap strategy is common across its contracts, which gives the vendor-effect prediction. Reputation can discipline it only if amendment histories are visible at award.
5. **Combine with Model 2.** Defects that become paid repairs are a second designed channel. Model 8 already combines them with lock-in.
