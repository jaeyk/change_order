# Game theory: amendments as a vendor strategy

This folder models how vendors can use contract amendments to keep and extend public business after winning an award. It started as a broader set of procurement models from earlier work. In November 2026 it was reorganized around one question that the empirical side of this repository can test:

> **Why do amendments happen?** Some arrive by chance: statutes change, caseloads shift. Others arrive by design: work is left out of the bid and bought back later under lock-in. Design pays because vendors earn over the whole life of a product, while agencies' award decisions concentrate on starting the agreement.

The models are theoretical. Their results are conditional on stated assumptions and are not evidence that any vendor behaved strategically.

## Reading order

| # | File | What it adds | Status |
| --- | --- | --- | --- |
| 1 | [amendments/01_lockin_bargaining.md](amendments/01_lockin_bargaining.md) | **Model 1.** After award, the incumbent and agency bargain over additional work against a replacement vendor. Switching costs raise the amendment margin; competition moves anticipated margins into lower initial bids. | From earlier work |
| 2 | [amendments/02_paid_remediation.md](amendments/02_paid_remediation.md) | **Model 2.** Defects that are not enforceably covered become paid amendments, which weakens prevention. | From earlier work |
| 3 | [amendments/03_lockin_and_remediation.md](amendments/03_lockin_and_remediation.md) | **Model 8.** Models 1 + 2: dependence raises the repair margin, which lowers prevention, which raises the return to dependence. | From earlier work |
| 4 | [amendments/04_chance_vs_design.md](amendments/04_chance_vs_design.md) | **Model 10.** Amendments come from chance (\(\lambda_0\)) and from a scope gap \(g\) chosen in the bid. With an award rule that weights later costs by \(\phi<1\), competition *selects* gaps even at zero profit, and lock-in turns the gap into a spiral when \(\phi<\tfrac12\). | **New** |
| 5 | [amendments/05_empirical_tests.md](amendments/05_empirical_tests.md) | First evidence from the repository's contract data, a map from model quantities to fields, and tests that separate chance from design. | **New** |
| 6 | [amendments/07_simulated_implications.md](amendments/07_simulated_implications.md) | Simulates five worlds (chance, design gaps, lock-in spiral, routine renewals, mixed) to derive which fingerprints separate them, then scores sectors. Software & SaaS and general enterprise IT carry the lock-in fingerprints (vendor concentration + escalating amendments); stated reasons in the ledgers rarely say why. Code and results: [simulations/](../simulations/README.md). | **New** |
| 7 | [amendments/06_contract_design_and_calibration.md](amendments/06_contract_design_and_calibration.md) | How the agency would set instruments, and how an earlier project calibrated \(\hat\lambda\) and amendment growth from contract documents. | From earlier work |

## Map of the models

| Model | Mechanism | Where |
| --- | --- | --- |
| 1 | Lock-in and amendment bargaining | `amendments/` |
| 2 | Paid remediation of preventable defects | `amendments/` |
| 8 | Lock-in × paid remediation | `amendments/` |
| 10 | Chance vs. design; horizon gap between vendor and agency | `amendments/` (new) |
| 3 | Metered workflows (pay per action) | `other_mechanisms/` |
| 4 | Rewarding flags instead of correct decisions | `other_mechanisms/` |
| 5 | Shared validation under cooperative purchasing | `other_mechanisms/` |
| 6 | Human review and the agency's inability to commit (with a noisy-signal extension) | `other_mechanisms/` |
| 7 | Post-award substitution and audit credibility | `other_mechanisms/` |
| 9 | Metered work × agency review | `other_mechanisms/` |

Models 3–7 and 9 study other ways vendor incentives and public costs diverge. They are kept, unchanged, for reference; see [other_mechanisms/README.md](other_mechanisms/README.md).

## Conventions

Each model is a game played after award unless it says otherwise. Contract terms are committed before the vendor acts. Players are risk neutral and parameters are common knowledge. Penalties are expected monetary transfers: social comparisons exclude transfers and count real costs and public harm. Fully informed competition for the award offsets anticipated amendment margins through lower bids, so distortions show up as wasted effort, dependence and burden rather than as vendor profit. Persistent profit requires a friction such as limited entry, incumbency advantages or a floor on bids. Symbols are local to each model.

## How this connects to the rest of the repository

| Theory | Data and code |
| --- | --- |
| Amendment counts and growth (\(\lambda_0+g\), award-to-final ratio) | `data/processed/contracts_normalized.csv`, `amendments_normalized.csv`; Figure 3 |
| Lock-in proxies (\(k\), \(p\)) | Tech subsector, `award_structure`, `vendor_role`, `qualification_tier` |
| Award-rule weight \(\phi\) | `procurement_method`, `procurement_channel` (central, cooperative) |
| Descriptive amendment dynamics | `scripts/amendment_dynamics.py` → `data/processed/amendment_dynamics.json` |
| Why amendments happened (stated reasons) | `scripts/amendment_reasons.py` → `data/processed/amendment_reasons.csv` |
| Simulated implications and sector fingerprints | [`simulations/`](../simulations/README.md) → `simulations/results/`; Figure 5 |

## Folder layout

```text
game_theory/
├── README.md                     this file
├── amendments/                   the focus: why amendments happen and how vendors use them
├── other_mechanisms/             models of other vendor incentives, kept for reference
└── archive/original/             the four notes exactly as they were before the restructure
```

The original notes referred to a manuscript (`manuscript/vendor_exploitation.md`), a simulation package (`simulation/`) and a browser game (`game/`) from the earlier project. Those are not in this repository; links to them are now marked "earlier project; not in this repo".
