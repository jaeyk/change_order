# Synthesis results (November 2026)

Where each step of [next_steps.md](next_steps.md) stands: what worked, what failed, and what each result can support. Predictions for steps 4 and 5 were written before any estimates and are kept in `results/predictions.json`.

## Summary

| Step | Status | Main result |
| --- | --- | --- |
| 1a. Power | **Done** | The lock-in tests are well powered in most sectors. Hardware & telecom, health care and public assistance would detect a Software-sized escalation effect with at least 99.5% probability, so their lack of escalation is a finding, not missing data. IT services (40%) and environment (28%) are underpowered. |
| 1b. Parameter recovery | **Done — failed the estimator** | In synthetic data with *no* lock-in, step 2's estimator still returned a lock-in share of 0.04–0.24, with intervals excluding zero in 2 of 3 replicates. |
| 2. SMM by sector | **Run, not usable** | Fits improved after the estimator was rebuilt (smooth common random numbers, multiple starts). But step 1b shows the lock-in share is **not identified** by the ten moments. Estimates are kept in `results/smm_estimates.csv` for diagnosis only. |
| 3. Validation | Stopped | Depends on step 2. |
| 4. Channels | Stopped | Uses the same estimator; would inherit its bias. |
| 5. Vendor types | Stopped | Same as step 4. |
| 6. Amendment documents | **Done** | 235 Chicago amendment documents OCR'd and coded. Explicit causes are rare. "Extended until a new contract is awarded" is common, concentrated in software and general technology, and rises with amendment order. |
| 7. Chance shocks | **Dropped** | Event studies of COVID-19 and H.R. 1 were set aside: amendment rates swing with funding cycles, and no state eligibility-system ledger covers H.R. 1. |
| 8. Counterfactuals | Stopped | Would rest on unidentified step 2 parameters. |

## What holds up

Three independent kinds of evidence point the same way.

1. **Fingerprints vs. matched chance** ([simulations/](../simulations/README.md)). Software & SaaS and general enterprise IT show both of the robust lock-in fingerprints: vendor concentration and escalating amendment sizes. Non-technology contracts are weakest.
2. **Power** (step 1a). Where a sector shows *no* escalation, the test could have found it, so the ranking is not an artifact of sample size.
3. **Documents** (step 6, [Y4](figures/y4_documents.png)). Share of amendments extended "until a new contract is awarded":

   | Sector | Share |
   | --- | ---: |
   | Software & SaaS | 34% |
   | General technology | 34% |
   | IT services | 20% |
   | Hardware & telecom | 11% |
   | Non-technology | 4% |

   The share rises from 12% of first amendments to 30% of fourth-or-later amendments. That is the renewal-instead-of-re-competition regime the simulations identified, and it is concentrated in the same sectors.

## What the documents say about *why*

- **Explicit causes are rare.** Of 235 documents, 6 state a chance cause and 7 a design cause:
  - *chance:* federal and state health grants, ARPA-funded COVID testing, a new low-income utility-relief program;
  - *design:* payment of previously approved change orders, a sole-source modification, a renegotiated price increase.

  72% state no cause beyond the change itself, usually a time extension, a vendor-limit (funding) increase, or both.
- **Contracts are extended while re-competition waits.** 21% of documents use this language. It is the mechanism Models 1 and 10 point to: re-competing is costly, so the incumbent continues. The documents do not say whose delay it is: the agency's procurement pipeline, or a vendor that is hard to replace.
- **Coder reliability.** The automated coder was revised against a manual review of 47 documents, so its 92% agreement on 38 decidable cases is in-sample. A held-out check before the last revision found all 8 unseen "chance" codes were false. All were triggered by a standard recital ("incorporate … changes in laws and/or City policies"), now filtered. Delay and no-cause codes were 26/26 correct. Treat chance and design counts as approximate; treat delay counts as reliable.
- **Coverage.** 65 of the 300 sampled revisions, mostly from 2003–2011, have no document online (the server returns a logo image), so the coded sample is mostly from 2012 onward.

## Why step 2 failed, and how to fix it

The lock-in component trades off against vendor dispersion (`sv`) and contract heterogeneity (`shape`). All three raise variance and vendor concentration. The only moment specific to lock-in is escalation, which rests on a few hundred amendment pairs per sector. Fixes, in order:

1. **Add moments that only lock-in moves:**
   - escalation *by amendment order*;
   - the correlation between a vendor's escalation and its share of renewal extensions;
   - the document-coded "extended until a new contract" share by order (step 6).
2. **Use vendor-level structure:** estimate the designer indicator from vendor histories pooled across agencies (Model 10's repeated-play prediction), not only from the variance it creates.
3. **Re-run recovery first.** Proceed to steps 3–5 and 8 only once a no-lock-in world returns a lock-in share near zero.

## Files

- `results/power_by_sector.csv`: step 1a.
- `results/smm_recovery.csv`: step 1b.
- `results/smm_estimates.csv` / `.json`: step 2, diagnostic only.
- `results/document_sample.csv`, `document_codes.csv`, `document_summary.json`, `document_manual_review.csv`, `document_agreement.json`: step 6. The PDFs and OCR text are in git-ignored `data/raw/chicago_documents/`.
- `figures/y4_documents.png`.
