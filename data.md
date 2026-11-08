# Data Structure

This document describes every source dataset and every processed file in the pipeline. Raw files live in `data/raw/<dataset>/` (`metadata.json`, `records.json`, `records.csv`); processed files live in `data/processed/`. Neither directory is committed. Run `scripts/download_data.py` and `scripts/normalize_and_classify.py` to rebuild them.

Counts are from the 2026-11-08 download. How these sources were found, which governments they cover, and the biases that follow are in [sampling_frame.md](sampling_frame.md).

---

## Table 1. Source datasets

**Panel A. Contract ledgers.** These give contract-level outcomes and populate `contracts_normalized.csv`.

| Jurisdiction | State | Level | Dataset (portal ID) | Raw unit of observation | Raw records | Normalized contracts | Start years (p1–p99) | Amendment history? | Amended contracts | Fields used for amendments / procurement method |
| :--- | :--- | :--- | :--- | :--- | ---: | ---: | :--- | :--- | ---: | :--- |
| Washington State | WA | State | Agency Contracts FY2021–FY2025 (`buf8-6px9`, `pwse-3zea`, `mz6y-pfem`, `s8d5-pj78`, `6fx9-ncas`) | Contract or amendment row per fiscal-year report; FY2023+ rows labelled (`K123-1` = amendment 1), amendment cost = change | 379,753 | 183,517 | 2005–2025 | Yes, FY2023+ labelled rows (103,398 contracts) | 26,101 | `agency_contract_amendment`, `contract_modifications`, `cost_of_contract`; `procurement_type`; OMWBE / small / veteran flags |
| Chicago | IL | City | Contracts (`rsxa-ify5`) | Contract revision | 186,213 | 89,265 | 1993–2026 | Yes | 33,429 | `revision_number`, `award_amount`; `procurement_type` (reference contract, joint purchase, master agreement) |
| New York City | NY | City | Checkbook NYC Contracts API (NYC Comptroller; registered expense contracts, FY2010–FY2027) | Contract (latest version) per registration year; sub-vendor rows dropped | 301,500 | 229,702 | 2009–2026 | Partial: original vs. current amount and version count, no amendment dates (229,611 contracts) | 68,581 | `prime_contract_original_amount`, `prime_contract_current_amount`, `prime_contract_version`; `prime_contract_award_method`, `parent_contract_id` |
| Oregon (ORPIN) | OR | State | ORPIN Contracts Issued (`6e9e-sfc4`) + Contracts Expired (`8izy-bwhd`, 5,824 documents not in Issued) | Contract amendment | 186,601 | 52,330 | 2004–2021 | Yes (Expired-only documents: running totals, no amendment dates) | 19,189 | `amendment_number`, `original_award_value`, `total_award_value_w_amendments`, `amendment_date`, `amendment_value`; `award_type` (price agreement, IGA) |
| District of Columbia | DC | State-equivalent | OCP contracts from PASS (DC GIS ArcGIS layer `Government_Operations/37`) | Contract × option period × document version | 51,717 | 10,588 | 2009–2026 | Partial: option exercises and modifications with dollar changes, no dates (10,552 contracts) | 6,200 | `CURRENTOPTIONPERIOD`, `DOCUMENTVERSION`, `CONTRACTAMOUNT`; `PROCUREMENTMETHODDESCRIPTION`; `MARKETTYPE` = DCSS (DC Supply Schedule → central) |
| Oregon Lottery | OR | State | Lottery Contracts (`rkhh-35im`) | Purchase-order line item | 24,279 | 12,806 | 2015–2026 | Yes (lines added on later dates) | 1,311 | `created`, `line_no`, `net_amount` |
| Cook County | IL | County | Awarded Contracts & Amendments (`qh8j-6k63`) | Contract or amendment | 8,342 | 5,316 | 2010–2026 | Yes | 1,473 | `category` (New Contract / Amendment), `amount` |
| Oregon State Treasury | OR | State | Treasury Contracts (`4iz8-xm93`) | Contract per fiscal year | 5,136 | 4,991 | 2018–2025 | Yes | 112 | `contract_nte_amount`, `supplemental_contract_amount`, `supplemental_effective_date` |
| Oregon Judicial Dept. | OR | State | Judicial Dept. Contracts (`3wxk-gaen`) | Contract per fiscal year | 2,829 | 2,591 | 2014–2025 | Yes | 579 | `original_contract_value`, `total_contract_value`, `total_amendments` |
| Washington Dept. of Health | WA | State | Contracts Started or Amended, SFY2016–SFY2019 (`mx83-wxi5`, `5s66-2kbs`, `qhn8-3a9e`, `un75-jhzj`) | Contract version (amendment number, period start, cumulative amount); histories back to 2000 | 8,163 | 1,681 | 2011–2019 | Yes, dated by each version's period start (186 contracts also in the statewide ledger are kept there only) | 739 | `amendment_number`, `cost_of_contract` / `maximum_amount`, `start_date` |
| West Hollywood | CA | City | Active Contracts (`atdr-sk64`) | Contract | 1,030 | 1,030 | 1992–2025 | Partial (original vs. current total) | 290 | `original_amount`, `contract_total` |
| Baton Rouge | LA | City-parish | Purchase Orders & Contracts (`2ung-w7t4`) | PO header (`H`) + line items (`D`) | 345,509 | 93,264 | 2017–2026 | **No** (single snapshot) | n/a | DBE / minority / veteran flags; "State Contract" in descriptions |
| Vermont | VT | State | Executed Contracts for Service (`dz5q-8uqb`) | Contract (duplicate rows) | 6,614 | 6,547 | 2018–2022 | **No** | n/a | `max_amount` |
| NYC School Construction Authority | NY | Authority | Change Orders (`gzvm-na49`) | Change order | 11,266 | 887 | 2007–2021 | **No** (change orders only) | n/a | `change_order_number` |
| Austin | TX | City | Contracts (`84ih-p28j`) | Vendor line per contract version | 625 | 341 | 2010–2023 | **No** (one version per document) | n/a | `doc_vers_no`; `rpt_dscr` (procurement method) |
| **Total** | **9 states + DC** | **15 ledgers** (8 state-level, 1 county, 5 city, 1 authority) | **23 datasets** | | **1,519,577** | **694,856** | **1992–2026** | **513,571 contracts with amendment history** (11 ledgers; dated amendments in 7); 181,285 without | **158,004** (30.8% of the analysis sample) | |

**Panel B. Cooperative purchasing, resellers, and vendor qualifications.** These populate `cooperative_sales.csv`, `award_structure.csv`, `vendor_qualifications.csv`, `reseller_relationships.csv`, and `reseller_registry.csv`.

| Source | State | Dataset | Raw unit of observation | Records | Coverage | What it identifies |
| :--- | :--- | :--- | :--- | ---: | :--- | :--- |
| Texas DIR cooperative sales | TX | Archive FY2010–25 (`w64c-ndf7`) + FY2026+ (`a743-wj72`) | Invoice line, aggregated server-side to FY × customer type × RFO × contract × prime × reseller × HUB grades | 13.1M lines → 42,978 | FY2010–FY2027 | Buyer sector (incl. local governments and out-of-state buyers), prime vs. reseller, HUB grade of each |
| Texas DIR active contracts | TX | `vipt-h4ye` | Contract × authorized reseller | 5,193 | Active as of download | Solicitation (RFO) → contracts → authorized resellers |
| Washington DES statewide contracts | WA | `n8q6-4twj` | Quarterly sales, aggregated to year × customer type × contract × vendor | 245,831 lines → 52,299 | 2015–2026 | Buyer type (cities, counties, ports, schools, tribes, other states); OMWBE / veteran / small flags |
| Washington IT Contracts reports | WA | 2020–2025 (`reg9-mjd3`, `bcyw-k8i3`, `dzvi-rs2c`, `hycx-v82h`, `ktim-amuz`, `3txe-z9i9`) | IT contract per agency | 29,967 | FY2020–FY2025 | Explicit cooperative flag and vehicle name (NASPO, Sourcewell, OMNIA, TIPS, E&I…), joined to WA contracts |
| NY OGS value-added reseller (VAR) report | NY | `cjqa-a3p4` | Master contract × VAR | 7,770 | Current | Master-contract vendor → authorized resellers, by contract lot |
| Delaware statewide central contracts | DE | `sifm-293u` | Monthly spend × contract × vendor × buyer group | 22,527 | FY2023–FY2027 | Use of state contracts by agencies, school districts, and municipalities |
| Delaware cooperative spend | DE | `6a9e-y46r` | Monthly spend × external cooperative contract × vendor × buyer group | 2,102 | FY2023–FY2027 | Use of external cooperative contracts by agencies, school districts, and municipalities |
| Federal Supply Schedules (GSA MAS + VA FSS) | US | USASpending `spending_by_award`, award type `IDV_C` | Schedule contract (IDV) | 54,106 (47,928 GSA, 6,178 VA) | 2007–present | (1) Extra reseller evidence: holders under wholesale/retail NAICS (42, 44–45) are dealers; (2) qualification covariate: which firms hold a GSA MAS / VA FSS contract |
| **Total** | **4 states + federal** | **14 datasets** | | **13,442,188 raw rows → 216,942 analysis rows** | **FY2010–FY2027** | |

**Panel C. Downloaded, not in the contract table.** Found by the catalog sweep (`scripts/discover_sources.py`) and downloaded with `--group frame_expansion`, but they cannot give an amendment history. They are kept for covariates and future linkage. Reviews of each are in `sources/ledger_review.csv`.

| Source | State | Dataset | Raw unit of observation | Records | Why not in Panel A | Useful for |
| :--- | :--- | :--- | :--- | ---: | :--- | :--- |
| NY state authorities procurement reports | NY | Authorities Budget Office (`ehig-g5x3`) | Procurement × fiscal-year report | 275,763 | The same contract cannot be linked across annual reports (`transaction_number` is not a contract key) | Number of bids, competitive vs. non-competitive award, purchases under state contract, technology categories |
| MTA procurements | NY | `twsw-2mqa` | Procurement × fiscal-year report | 107,503 | Same structure as the ABO reports | As above |
| Atlanta contracts | GA | `s39g-udq5` | Contract | 619 | Current amount and number of renewals only | Renewal counts |
| Baton Rouge annual contracts | LA | `syff-bi5d` | Annual contract | 71 | Too few rows | Extension dates |
| Cook County buying plans FY2025–26 | IL | `ce4m-t955`, `cbhc-xvrm` | Planned procurement | 345 | Plans, not awards | Pre-award estimated value linked to the current contract number (a future test of buy-in) |
| **Total** | **3 states** | **6 datasets** | | **384,301** | | |

---

## Table 2. Processed files

| File | Unit of observation | Rows | Key | Built from | Purpose |
| :--- | :--- | ---: | :--- | :--- | :--- |
| `contracts_normalized.csv` | Contract | 694,856 | `jurisdiction` + `contract_id` | Panel A ledgers (+ Panel B for vendor flags) | Amendment outcomes with tech, channel, direction, award-structure, vendor-role, qualification, and certification tags |
| `amendments_normalized.csv` | Amendment / revision | 258,150 | `jurisdiction` + `contract_id` + `amendment_seq` | Panel A ledgers | Amendment timing and dollar deltas |
| `cooperative_sales.csv` | Program × FY × buyer type × contract × prime × reseller | 119,906 | (all dimension columns) | Texas DIR, WA DES, Delaware | Who buys through cooperative / statewide contracts, in which direction, through primes or resellers |
| `award_structure.csv` | Cooperative or federal-schedule contract | 63,977 | `source` + `contract_id` | Texas DIR, NY OGS, WA DES, Delaware, GSA MAS, VA FSS | Single vs. multiple award; prime-direct vs. resellers; holder role |
| `vendor_qualifications.csv` | Vendor (normalized name) | 45,449 | `vendor_key` | All Panel B sources | Contract vehicles each firm holds (covariates) |
| `reseller_relationships.csv` | Prime vendor × reseller × contract | 9,775 | `source` + `contract_id` + `prime_vendor` + `reseller` | Texas DIR active contracts, NY OGS VAR | Reseller networks |
| `reseller_registry.csv` | Firm considered as a reseller | 3,891 | `reseller_key` | Texas DIR, NY OGS, federal schedules, curated list | Evidence behind the `vendor_role` classification |
| `amendment_reasons.csv` | Amendment with reason text (Washington, Chicago) | 160,290 | `jurisdiction` + `contract_id` + `amendment_seq` | `amendments_normalized.csv` | Stated reason coded as chance / design / ambiguous / neutral / uninformative |
| `sources/frame.csv` *(committed)* | Frame government | 173 (166 in frame) | `unit_id` | Census Vintage 2024 population estimates | Sampling frame: states + DC, cities ≥ 300k, counties ≥ 1M ([sampling_frame.md](sampling_frame.md)) |
| `sources/coverage.csv` *(committed)* | Frame government | 166 | `unit_id` | frame + catalog hits + transparency systems + sample | Best available source and coverage status of each government |
| `sources/catalog_hits.csv` *(committed)* | Catalog dataset | 8,310 | `platform` + `dataset_id` | Socrata, data.gov, ArcGIS Hub, OpenDataSoft searches | Every contract-related dataset found, auto-classified A / B / C |
| `sources/ledger_review.csv`, `transparency_systems.csv`, `portal_map.csv` *(committed)* | — | — | — | Manual review | Reviewed class of candidate ledgers; state / city transparency systems and their access; portal → government map |
| `robustness/results/*` *(committed)* | — | — | — | Processed tables | Robustness checks R0–R16 ([robustness_checks.md](robustness_checks.md)) |
| `amendment_dynamics.json` | — | — | — | Contract and amendment tables | Continuation probabilities, timing of first amendments, vendor dispersion |
| `simulations/results/*` *(committed, outside `data/processed/`)* | — | — | — | Contract and amendment tables + simulation | Theory-world signatures, sector fingerprints vs. matched chance, lock-in ranking (see [simulations/README.md](simulations/README.md)) |
| `tech_analysis_results.json` | — | — | — | `contracts_normalized.csv` | Tech vs. non-tech metrics and regression |
| `cooperative_reseller_results.json` | — | — | — | All processed CSVs | Channel / direction / award-structure / reseller / qualification / certification results |
| `dashboard.html` | — | — | — | Both JSON results | Interactive dashboard |

---

## Table 3. `contracts_normalized.csv` variables

| Variable | Type | Description |
| :--- | :--- | :--- |
| `jurisdiction` | str | Source ledger (see Table 1, Panel A) |
| `state` | str | Two-letter state |
| `gov_level` | str | `state`, `county`, `city`, `special_authority` |
| `contract_id` | str | Contract identifier (Washington: `<agency number>:<contract number>`) |
| `title_desc`, `department`, `vendor_name`, `commodity_or_type` | str | Descriptive fields from the original award |
| `procurement_method` | str | The source's own procurement-method field (WA `procurement_type`, Chicago `procurement_type`, ORPIN `award_type`, Austin `rpt_dscr`) |
| `is_tech` | 0/1 | Technology contract |
| `tech_subsector` | str | `software_saas`, `hardware_telecom`, `it_services`, `tech_general`, `non_tech` |
| `tech_domain` | str | Program domain of tech contracts (health care, public safety, …) |
| `initial_award_val`, `final_award_val`, `delta_val` | float | Original value, current value, difference (USD) |
| `pct_growth` | float | `delta_val / initial_award_val × 100` |
| `amendment_count`, `is_amended` | int, 0/1 | Number of amendments; any amendment or value change |
| `amendment_observable` | 0/1 | 0 = ledger has no amendment history (Baton Rouge, NYC SCA, Vermont, Austin), Washington contracts seen only in FY2021–22, and NYC / DC contracts with a non-positive original amount. Exclude these from amendment analyses |
| `n_line_items` | int | PO line items (Baton Rouge, Oregon Lottery) |
| `start_date`, `end_date`, `duration_days` | date, date, int | Term of the original award |
| `coop_vehicle` | str | Cooperative / master vehicle used (see README §4C), blank if none |
| `coop_direction` | str | `horizontal`, `vertical_downward`, `vertical_upward`, `central`, `unknown`; blank if no vehicle |
| `procurement_channel` | str | `cooperative_<direction>`, `central_state_contract`, `direct_or_unknown` |
| `n_contractors` | int | Distinct contractors on the original award |
| `award_structure` | str | `single_award_prime_direct`, `single_award_reseller`, `multiple_award_prime_direct`, `multiple_award_reseller` |
| `vendor_role` | str | `prime_or_direct`, `authorized_reseller`, `unknown` |
| `qualification_tier` | str | `federal_schedule_holder`, `state_vehicle_prime`, `authorized_reseller_only`, `none_observed` |
| `gsa_mas_holder` | 0/1 | Vendor holds a GSA MAS contract |
| `n_vehicles_held` | int | Number of vehicle flags set in `vendor_qualifications.csv` |
| `fss_holder_role` | str | NAICS role on federal schedules: `manufacturer`, `dealer_reseller`, `service_provider`, `other` |
| `vendor_certification` | str | `minority_or_women_owned`, `disadvantaged_business`, `veteran_owned`, `small_business`, `not_certified`, `not_reported` |

## Table 4. `amendments_normalized.csv` variables

| Variable | Type | Description |
| :--- | :--- | :--- |
| `jurisdiction`, `contract_id` | str | Links to `contracts_normalized.csv` |
| `amendment_seq` | str | Revision / amendment number (fiscal year for Oregon Judicial snapshots; `<option period> v<document version>` for DC) |
| `amendment_date` | date | Effective or approval date, where reported |
| `delta_amount` | float | Dollar change (Washington: reported contract cost on that row) |
| `category` | str | Source label (Revision, Amendment, Supplemental, Change Order, …); DC: `Option exercised` or `Modification`; WA Dept. of Health: `Amendment (version period start)` |
| `description` | str | Amendment text |

## Table 5. `cooperative_sales.csv` variables

| Variable | Type | Description |
| :--- | :--- | :--- |
| `program` | str | `texas_dir`, `washington_des_master`, `delaware_central`, `delaware_cooperative` |
| `coop_vehicle`, `vehicle_level` | str | Vehicle and the level that established it |
| `state`, `fiscal_year` | str | |
| `customer_type` | str | `state_agency`, `higher_ed`, `local_government`, `k12`, `tribal_government`, `out_of_state`, `federal`, `nonprofit_assistance_org`, `other`, `unknown` |
| `buyer_level` | str | `state`, `local`, `federal`, `other_state`, `unknown` |
| `coop_direction` | str | As in Table 3 |
| `contract_number`, `contract_desc` | str | |
| `vendor_name`, `vendor_role`, `vendor_certification`, `vendor_cert_raw` | str | Prime vendor, its role, and its harmonized and raw grade |
| `reseller_name`, `reseller_certification`, `reseller_cert_raw` | str | Authorized reseller on the sale (Texas DIR only) |
| `sales_channel` | str | `direct_prime` or `via_reseller` |
| `sales` | float | USD |
| `n_lines` | int | Source lines aggregated into the row |

## Table 6. `award_structure.csv` variables

| Variable | Type | Description |
| :--- | :--- | :--- |
| `source` | str | `texas_dir`, `ny_ogs`, `washington_des`, `delaware_central`, `delaware_cooperative`, `gsa_mas`, `va_fss` |
| `solicitation` | str | Texas DIR RFO, NY OGS lot, WA / Delaware statewide contract number, or schedule |
| `contract_id`, `contract_desc`, `prime_vendor` | str | |
| `n_primes_in_solicitation` | int | Primes awarded under the same solicitation |
| `n_resellers` | int | Authorized resellers under the contract (blank where not reported) |
| `award_structure` | str | `single_award` or `multiple_award` + `_prime_direct`, `_with_resellers`, `_prime_direct_or_unknown`, or `_dealer_holder` |
| `holder_naics_role`, `naics_code` | str | Federal schedules only |

## Table 7. `vendor_qualifications.csv` variables (covariates)

| Variable | Type | Description |
| :--- | :--- | :--- |
| `vendor_key` | str | Normalized vendor name (join key) |
| `gsa_mas_holder`, `va_fss_holder` | 0/1 | Holds a GSA MAS / VA FSS contract |
| `texas_dir_prime`, `texas_dir_reseller` | 0/1 | Prime on / authorized reseller under a Texas DIR contract |
| `ny_ogs_master_holder`, `ny_ogs_var` | 0/1 | NY OGS master-contract holder / VAR |
| `wa_des_master_holder`, `delaware_contract_holder` | 0/1 | Vendor on a WA DES or Delaware statewide contract |
| `fss_contracts`, `fss_holder_role` | int, str | Number of schedule contracts; modal NAICS role |
| `n_vehicles_held` | int | Sum of the flags above |
| `qualification_tier` | str | As in Table 3 |

## Table 8. `reseller_relationships.csv` variables

| Variable | Type | Description |
| :--- | :--- | :--- |
| `source`, `state`, `contract_id`, `contract_desc`, `contract_type` | str | Texas DIR active contracts or NY OGS VAR report |
| `prime_vendor`, `prime_certification`, `prime_cert_raw` | str | Contract holder and its grade |
| `reseller`, `reseller_certification`, `reseller_cert_raw` | str | Authorized reseller and its grade |

## Table 9. `reseller_registry.csv` variables

| Variable | Type | Description |
| :--- | :--- | :--- |
| `reseller_key` | str | Normalized firm name |
| `reseller_relationships` | int | Distinct (contract, prime) pairs the firm resells under |
| `prime_contracts` | int | Contracts the firm holds as prime |
| `classified_as_reseller` | 0/1 | Final classification used for `vendor_role` |
| `sources` | str | Evidence: `texas_dir_sales`, `texas_dir_contracts`, `ny_ogs_var`, `fss_dealer_naics`, `curated` |

---

### Notes
- **New York City (Checkbook)** has no amendment rows: each contract carries its original and current amount and its latest version number (`amendment_count` = version − 1). Versions include non-monetary changes, so 83% of amended NYC contracts show no change in value. NYC contracts are used for counts and growth, not timing or escalation.
- **District of Columbia (PASS)** amendments are option-period exercises and document-version modifications, in that order, each with its dollar change but no date. Option exercises are planned at award, so DC amendment counts run high.
- **Washington Dept. of Health** amendment dates are the start of each contract version's period of performance, a close proxy for the effective date. The 186 contracts that also appear in the statewide ledger are kept only there.
- **Washington amendments** are the labelled rows of the FY2023–25 reports, each with its own date and a dollar *change* (not a running total). Contracts seen only in FY2021–22 have `amendment_observable = 0`.
- **Washington** contracts are keyed by agency number plus contract number, because contract numbers such as `K1234` are reused across agencies. Rows repeated across fiscal-year reports are de-duplicated.
- **Co-awardees vs. amendments:** additional contractors on a contract's original award count toward `n_contractors` and are not treated as amendments. This applies to Washington, Austin, and the other ledgers.
- **Server-side aggregation:** Texas DIR and Washington DES sales are aggregated by the data portal (SoQL `$group`). Sales totals are exact, but invoice-level detail is not kept.
- **Name matching:** vendor joins across sources use normalized names (case, punctuation, DBA clauses, and corporate suffixes stripped). There is no shared vendor ID across sources.
