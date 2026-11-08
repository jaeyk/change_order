# Sampling frame, coverage, and potential biases

This note says which governments the data can speak for, how the sources were found, where the sample is thin or skewed, and what has been done (and remains) to fix it. The variable-level description of each source is in [data.md](data.md).

## 1. What the sample is

The analysis sample is **not a probability sample**. It is every contract ledger we could find that (a) a US state or local government publishes openly, (b) can be downloaded in full by script, and (c) records contract values, ideally with amendment histories. Commercial data are excluded (Section 6).

As of the 2026-11-08 download:

| | Contracts | With amendment history | Amended |
| --- | ---: | ---: | ---: |
| 15 ledgers from 9 states and DC | 694,856 | 513,571 (11 ledgers) | 158,004 |
| Of which: dated amendments (timing tests) | | 7 ledgers | |

## 2. The frame: who the study aims to describe

The target population is US state and large local governments. The explicit frame (`sources/frame.csv`, built by `scripts/build_frame.py` from Census Vintage 2024 population estimates) is:

| Level | Rule | Units |
| --- | --- | ---: |
| State | All 50 states and the District of Columbia | 51 |
| City | Every incorporated place with population ≥ 300,000 (Honolulu counted as the City and County) | 72 |
| County | Every county with population ≥ 1,000,000 that is a separate government | 43 |
| **Total** | | **166** |

Seven large counties are not separate governments and are left out: the four New York City boroughs over one million people, Philadelphia and Duval (consolidated with their cities), and Middlesex County, Massachusetts (no county government since 1997).

The roughly 90,000 other local governments (smaller cities, townships, school districts, special districts) are outside the frame. Almost none publish contract ledgers, and the few that do (West Hollywood, Baton Rouge) are kept in the sample but flagged as outside the frame.

## 3. How sources were found

1. **Catalog sweep** (`scripts/discover_sources.py` → `sources/catalog_hits.csv`). Nine queries ("contracts", "contract amendments", "change orders", "contract modifications", "purchase orders", "procurement", "awarded contracts", "vendor contracts", "contract register") against four public catalogs:
   - **Socrata** discovery API: every Socrata portal.
   - **data.gov** (new catalog search API): harvests state and local portals on other platforms (CKAN, ArcGIS, custom).
   - **ArcGIS Hub**: ArcGIS Online open data.
   - **OpenDataSoft** network.

   Each hit is classified from its title and columns:
   - **A:** contract ledger with amendment history.
   - **B:** contract-level snapshot.
   - **C:** related data (bids, plans, spending).

   The class is then reviewed by hand where it matters (`sources/ledger_review.csv`). For example, the New York authorities reports have renewal fields but cannot be linked across years, so they are B, not A.
2. **State and city transparency systems** (`sources/transparency_systems.csv`). These are statutory contract-transparency sites outside open-data portals: Checkbook NYC, Virginia eVA, New York Open Book, the Texas LBB contracts database, Florida FACTS, the Pennsylvania Contracts e-Library, Illinois Comptroller, the Colorado CMS and California SCPRS. Each was checked for an API or bulk download on 2026-11-08.
3. **Coverage table** (`sources/coverage.csv`): every frame unit with its best available source and status.

## 4. Coverage of the frame

| Status | States (of 51) | Cities (of 72) | Counties (of 43) | All (of 166) |
| --- | ---: | ---: | ---: | ---: |
| In sample | 4 (4% of pop.) | 4 (22% of pop.) | 1 (6% of pop.) | 9 |
| Available: snapshot only | 5 (30% of pop.) | 5 (5% of pop.) | 4 (8% of pop.) | 14 |
| System exists, no bulk access | 4 (16% of pop.) | 0 (0% of pop.) | 0 (0% of pop.) | 4 |
| Related data only | 1 (1% of pop.) | 6 (12% of pop.) | 1 (4% of pop.) | 8 |
| Nothing found | 37 (49% of pop.) | 57 (61% of pop.) | 37 (82% of pop.) | 131 |

Population shares are of each level's frame population (2024 estimates).

**Every frame government with something found:**

| Government | Status | What we have or found |
| --- | --- | --- |
| California | available: snapshot only | SCPRS Purchase Order Data FY2012–2015 (data.ca.gov) (bulk download, amendments: no) — Open data: Funding Positions of CalPERS Contracting Agencies |
| Texas | available: snapshot only | LBB Contracts Database (interactive only, amendments: yes) — Open data: Texas Commission on Environmental Quality - Curren; Official - DIR Current Active Cooperative Contract; ARCHIVE DIR Cooperative Contract Sales Data   Fisc |
| Florida | system exists, no bulk access | FACTS (Florida Accountability Contract Tracking System) (interactive only, amendments: yes) |
| New York | available: snapshot only | Open Book New York – Contracts (interactive export, amendments: yes) — Open data: MTA Procurements: Beginning 2018; Procurement Report for State Authorities; Master Contract Value Added Resellers (VAR) Report |
| Pennsylvania | system exists, no bulk access | Contracts e-Library (interactive export, amendments: yes) |
| Illinois | system exists, no bulk access | State Contracts (Illinois Comptroller) (interactive export, amendments: partial) |
| Virginia | available: snapshot only | eVA Procurement Data (data.virginia.gov) (bulk download, amendments: partial) |
| Washington | in sample | In sample: washington_state, wa_doh — Open data: Agency Contracts Fiscal Year 2024; Agency Contracts Fiscal Year 2021; Agency Contracts Fiscal Year 2023 |
| Colorado | system exists, no bulk access | Contract Management System (public site) (interactive only, amendments: yes) |
| Oregon | in sample | In sample: oregon, oregon_lottery, oregon_treasury, oregon_judicial — Open data: Historical - ORPIN - Contracts Issued - Multi-Year; Historical - ORPIN - Contracts Expired - Multi-Yea; Treasury Contracts - Multi-Year Report |
| Oklahoma | related data only | Open data: Statewide Contract Cost Savings; of Management and Enterprise Services/statewide-contracts-solicitations-search Statewide Contracts & Solicitations Search |
| Delaware | available: snapshot only | Open data: Proposals Received By Contract; Statewide Central Contract Spend; Central Contract Line Item Spend |
| District of Columbia | in sample | In sample: dc — Open data: Contracts from PASS; Purchase Orders from PASS |
| Vermont | in sample | In sample: vermont — Open data: Executed Contracts for Service; Contract List; Contracts for Service Executed 2014 to Present |
| New York city | in sample | In sample: nyc_sca, nyc_checkbook — Checkbook NYC (Contracts API) (api, amendments: partial) — Open data: Directory Of Awarded Construction Contracts; DYCD Contractors; Department of Youth and Community Development (DYC |
| Los Angeles city | related data only | Open data: Rental Contracts Completed at El Pueblo Historical |
| Chicago city | in sample | In sample: chicago — Open data: Contracts; Performance Metrics - Procurement Services - Task |
| Austin city | in sample | In sample: austin — Open data: Purchase Order Quantity Price detail for Commodity; Official - DIR Current Active Cooperative Contract; Official - VSR Data for Cooperative & Tele Contrac |
| San Francisco city | related data only | Open data: Vendor Payments (Vouchers); Vendor Payments (Purchase Order Summary) |
| Seattle city | available: snapshot only | Open data: HSD Contracts 2016 |
| Denver city | related data only | Open data: City of Denver Procurement Transactions |
| Washington city | in sample | In sample: dc |
| Detroit city | available: snapshot only | Open data: OCP Procurement Agreements |
| Baltimore city | available: snapshot only | Open data: Baltimore City Contracts Bureau of Purchases Depar |
| Atlanta city | available: snapshot only | Open data: Contracts Data |
| Mesa city | related data only | Open data: Business Services - Purchases Against Contracts |
| Kansas City city | available: snapshot only | Open data: List of KCMO City Contracts |
| Oakland city | related data only | Open data: Contracts Awarding |
| Cincinnati city | related data only | Open data: Fleet Procurement |
| Cook County, Illinois | in sample | In sample: cook_county — Open data: Procurement - Awarded Contracts & Amendments; Procurement - Intent to Execute; Procurement - Intent to Award |
| San Diego County, California | related data only | Open data: Procurement Forecast |
| Miami-Dade County, Florida | available: snapshot only | Open data: Purchase Orders (INFORMS) - 2025; Purchase Orders (INFORMS) - 2024; Purchase Orders (INFORMS) - 2021 |
| King County, Washington | available: snapshot only | Open data: Procurement Contracts; Best Starts for Kids Funding Award Database |
| Fulton County, Georgia | available: snapshot only | Open data: Purchasing: Purchase Orders |
| Montgomery County, Maryland | available: snapshot only | Open data: Contracts |

"Nothing found" means none of the four catalogs and none of the checked transparency systems returned a contract ledger for that government. It does not mean the government publishes nothing: many post contract search pages or PDFs that no catalog indexes. Only nine states' own transparency systems have been reviewed so far (Section 7, fix 7).

## 5. Potential biases

| # | Bias | What it is | Likely direction / consequence | How we check or limit it |
| --- | --- | --- | --- | --- |
| 1 | **Selection on transparency** | Governments that publish full contract ledgers with amendments are larger, more professionalized and more transparency-minded, and are concentrated in the West, the Midwest and the Northeast corridor (WA, OR, IL, NY, DC). | If better-run procurement offices write tighter contracts, amendment rates and growth are **understated** relative to the frame. Sector contrasts are less affected than levels. | Compare sectors *within* ledgers (R2 in [robustness_checks.md](robustness_checks.md)); report levels per ledger. |
| 2 | **Concentration in a few ledgers** | Before the 2026-11-08 additions, Washington, Chicago and Oregon held 98% of contracts with amendment histories, and Oregon alone held 61% of technology contracts with histories. New York City (Checkbook) and DC now add 240,000 contracts, but they carry no amendment dates. | Timing and escalation results still rest mostly on Oregon, Chicago and Washington. One ledger's coding conventions could drive a "sector" result. | Leave-one-ledger-out and one-ledger-at-a-time checks (R1, R2). |
| 3 | **Platform bias** | Earlier sources came only from Socrata. | Socrata customers skew toward large, well-funded portals. | Sweep extended to data.gov, ArcGIS Hub and OpenDataSoft. That found DC (ArcGIS) and Washington Health histories (Socrata, missed by the earlier keyword searches). |
| 4 | **What counts as an amendment differs** | Chicago records every revision; Washington labels amendments in FY2023+ reports; NYC counts registered versions, which includes non-monetary changes (83% of amended NYC contracts never change value); DC mixes planned option exercises with modifications; Washington Health records version periods. | Amendment *counts* are not comparable across ledgers; *value growth* is more comparable. Planned options inflate DC's counts. | Within-ledger comparisons; DC option exercises are labelled separately in `amendments_normalized.csv`; NYC and DC are used for counts and size only. |
| 5 | **Dollar thresholds** | Some ledgers cover only contracts above a threshold (Texas LBB above $50k; Pennsylvania above $5k; Colorado personal services above a statutory amount). Chicago and Oregon include small purchases. | Mixing thresholds changes the size mix by ledger. | Award-size thresholds of $25k and $100k (R3). |
| 6 | **Time coverage and censoring** | ORPIN stops in 2021; Washington's labelled amendments start in FY2023; Washington Health histories cover contracts active in 2016–19 (so long-lived contracts are over-represented); recent contracts have had little time to be amended. | Right-censoring understates amendments for recent starts; the Washington Health window over-represents long-running contracts. | Start-year window 2005–2019 (R4). |
| 7 | **Survivorship in snapshots** | West Hollywood lists active contracts only; Atlanta lists current contracts. | Contracts that ended early or were never amended may be missing. | These ledgers are small and excluded from timing tests. |
| 8 | **Sector classification** | Technology subsectors come from keyword and commodity-code rules on titles. | Misclassification blurs sector differences, mostly toward zero. | Strict software definition (R6). |
| 9 | **Vendor name matching** | No shared vendor ID across or within ledgers. | Split names understate vendor concentration and follow-on awards; merged names overstate them. | Follow-on test with several de-duplication windows (R11). |
| 10 | **Federal side missing** | Federal contracts (FPDS) are not in this sample. | The study speaks to state and local procurement only. | Planned as a separate next step (FPDS is a census of federal contract actions, with modification reason codes). |

## 6. Sources excluded on principle: commercial data

Commercial aggregators (for example GovSpend, Deltek GovWin, HigherGov, Starbridge, and the scraped checkbooks on OpenTheBooks) hold purchase orders for thousands of agencies and would widen coverage fastest. **They are not used.** The reasons are about replicability, not quality:

- **Licensing.** The data cannot be redistributed, so another researcher cannot rebuild the sample without buying the same licence, and licences change.
- **Undocumented processing.** Vendors clean, de-duplicate and categorize records with proprietary rules that cannot be inspected, so measurement choices that drive the results (what counts as an amendment, how vendors are matched) would be hidden.
- **Unstable coverage.** Which agencies are included, and since when, depends on the vendor's collection agreements and can change between pulls without notice.
- **No provenance to the public record.** Every record in this repository can be traced to a government-published URL and re-downloaded with `scripts/download_data.py`.

The same rule excludes data obtained only through private arrangements. Public-records responses would qualify only if the released files are posted publicly so others can retrieve the same data.

## 7. How to fix it: recommendations and status

| # | Fix | Bias addressed | What it involves | Status (2026-11-08) |
| --- | --- | --- | --- | --- |
| 1 | **Explicit frame** | 1 (selection made visible) | Define the target governments from Census population data | **Done:** `sources/frame.csv` (166 governments) |
| 2 | **Coverage table** | 1 | Record for every frame unit what is published, where, and whether it has amendment history | **Done:** `sources/coverage.csv`; summary in Section 4 |
| 3 | **Multi-platform catalog sweep** | 3 | Search Socrata, data.gov, ArcGIS Hub and OpenDataSoft with the same queries; review candidates by hand | **Done:** `scripts/discover_sources.py`, `sources/catalog_hits.csv`, `sources/ledger_review.csv` |
| 4 | **Add every downloadable ledger with amendment history** | 2 | Ingest new A-class ledgers | **Done:** ORPIN Expired (+5,824 Oregon contracts), Washington Dept. of Health (1,681 contracts, histories back to 2000), DC PASS (10,588 contracts), Checkbook NYC (229,702 contracts) |
| 5 | **Transparency systems with APIs or bulk files** | 1, 2 | Script the ones that allow it | **Partly done:** Checkbook NYC ingested. Virginia eVA (purchase-order lines from 245 state agencies and 900+ local bodies, about 1 GB per year) is downloadable; it needs a streaming aggregator and is **next**. |
| 6 | **Interactive-only transparency systems** | 1, 2 | NY Open Book, Florida FACTS, Texas LBB, Pennsylvania e-Library, Colorado CMS, Illinois Comptroller have amendment data behind search forms. Either write per-system search scrapers (slow, fragile) or file public-records requests for bulk extracts and post them publicly | **Not started.** Records requests are the more replicable route. |
| 7 | **Check every state's own site** | 1 | 38 states have no source found by the catalogs; each state's transparency or procurement site needs a manual check | **Not started:** listed as "nothing found" in `sources/coverage.csv` |
| 8 | **Robustness to ledger composition** | 2, 4, 6 | Leave-one-ledger-out, within-ledger replication, out-of-sample ledgers | **Done:** [robustness_checks.md](robustness_checks.md) |
| 9 | **Harmonize amendment definitions** | 4 | Separate monetary amendments, time extensions, option exercises and administrative versions where the source allows | **Partly done:** DC options labelled; NYC versions vs. value changes separated in analysis. A common taxonomy is next. |
| 10 | **Weighting** | 1 | Reweight ledgers to the frame (by population or spending) for level estimates | **Not done.** Coverage is too thin (9 of 166 frame governments, 7 with amendment histories) for credible weights; sector contrasts within ledgers are reported instead. |
| 11 | **Federal contracts** | 10 | FPDS / USASpending contract actions with modification reason codes | **Next step, separate work** |
| — | Commercial aggregators | — | — | **Excluded** (Section 6) |

## 8. Reproduce

```bash
python3 scripts/discover_sources.py                 # catalog sweep -> sources/catalog_hits.csv (about 1 hour at 3 s per request)
python3 scripts/download_data.py --group frame_expansion   # new open-data ledgers and covariate sources
python3 scripts/download_data.py --group transparency      # Checkbook NYC API
python3 scripts/normalize_and_classify.py
python3 scripts/build_frame.py                      # sources/frame.csv and sources/coverage.csv
```
