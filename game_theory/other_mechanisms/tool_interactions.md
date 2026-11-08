# Which governance tools are a menu, and which are a package?

This note backs the labels in Change Order's toolbox. Results are illustrative: the parameters are not estimated.

## Method

Each pair of tools is switched off and on, for four cells. With the objective oriented so higher is better:

    I = V(both) - V(A only) - V(B only) + V(neither)

- **Package (complements):** I > 0. Together they do more than the sum of the parts.
- **Menu (additive):** I is near 0. Each is worth the same with or without the other.
- **Overlap (substitutes):** I < 0. Together they do less than the sum of the parts.

The third category was not part of the original question, but it is what the tests most often found.

**Models.** tool_interactions.py *(earlier project; not in this repo)* evaluates each pair at the defaults and across 500 seeded draws, with each parameter varied by ±30%. |I| under 5% of the two solo effects counts as additive. A label is robust if 80% of draws agree.

**Game.** tool-interactions.mjs *(earlier project; not in this repo)* runs a full 2^7 factorial on the real engine: 153,600 games with paired seeds. Results are in tool-interactions.md *(earlier project; not in this repo)*. The cutoff is 10% of the solo effects, and values within 2 standard errors of zero count as additive. It was set after seeing a first run, so sensitivity at 5% is reported below. Win rate is not used because it is a threshold outcome.

**Rule for the toolbox.** A pair gets a label only if the models and the game agree. Otherwise it is listed as unsettled.

## Results

| Pair | Models | Game | Toolbox |
| --- | --- | --- | --- |
| Monitoring + penalties | Package (1, 7) | Package | **Package** |
| Clear rules + an exit | Substitutes (1, 8) | Overlap | **Overlap** |
| Stepping in + penalties | Substitutes (6) | Overlap on service, no clear effect on spending | **Overlap** |
| Monitoring + clear rules | Additive (1) | Menu at 10%, package at 5% | **Menu**, least certain |
| Monitoring + an exit | Additive (1) | Package, just past the 10% cutoff on service | Unsettled |
| Penalties + an exit | Additive (1) | Overlap | Unsettled |
| Clear rules + penalties | Package (2, 8) | Conflict: money and service disagree | Unsettled |

Know-how and competition are not labeled. No model tests know-how as such: the `s0` lever in Model 1 has no effect on agency value under competitive bidding, so it is uninformative, and Model 13 is the proper test. The models assume competition rather than switching it. Game-only results for these two are in the game report.

## Names used in the game

The table above uses research names. The toolbox shows: monitoring = "Checking the work"; penalties = "Fines for poor service"; clear rules = "Bug and price rules"; an exit = "A way to switch vendors"; stepping in = "Your staff fixing errors"; know-how = "Your own technical staff"; competition = "Competitive bidding".

## Findings to carry forward

1. **Pure menus are rare.** Only one pair passes as a menu, and that label is sensitive to the cutoff.
2. **"Package" depends on the starting point.** Monitoring and penalties are a package going from nothing to both. Once both exist, more of each is a substitute, because Model 1 multiplies them and effort has diminishing returns.
3. **`recommendations.md` and Model 8 overstate one claim.** They call warranty enforcement and portability complements. On total social cost they are substitutes (I = -0.91 for warranty 0 to 0.9 and portability 0 to 3, robust in 95% of draws). On prevention effort, the sign depends on the range: positive from warranty 0 to 0.5 (+0.085), negative from 0.5 to 0.9 (-0.079). The wording has not been changed yet.
4. **The game's "clear rules" and the models' are not one lever.** The game bundles defect classification with a rate card, and its penalties are on service levels rather than defects. That may explain the conflict on clear rules + penalties.
