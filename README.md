# change_order

## Target Data

The project targets public contract records that can support analysis of amendments and change orders, rather than procurement portals that only list open bids.

### Priority Sources

| Jurisdiction | Dataset | Amendment or change-order coverage |
| --- | --- | --- |
| Oregon | [Historical ORPIN Contracts](https://data.oregon.gov/d/6e9e-sfc4) | Amendment number and date, original award value, amendment value, and total value including amendments. Historical coverage runs through June 2021. |
| Cook County, Illinois | [Awarded Contracts & Amendments](https://datacatalog.cookcountyil.gov/d/qh8j-6k63) | Extensions, renewals, increases, decreases, scope changes, and links to amendment PDFs. Coverage begins in December 2014. |
| Chicago, Illinois | [Contracts](https://data.cityofchicago.org/d/rsxa-ify5) | Contract revisions, revised award amounts, reductions, vendors, departments, dates, and contract PDFs. |
| Washington State | [Agency Contracts](https://data.wa.gov/d/s8d5-pj78) | Amendment numbers, modification descriptions, contractors, amounts, and effective dates. Published by fiscal year. |
| New York City | [SCA Change Order Report](https://data.cityofnewyork.us/d/gzvm-na49) | Change-order numbers, project identifiers, status, dates, and workflow stages. Financial values are limited. |

### Secondary Sources

| Jurisdiction | Dataset | Use and limitation |
| --- | --- | --- |
| Baton Rouge, Louisiana | [Purchase Orders and Contracts](https://data.brla.gov/d/2ung-w7t4) | Contract amounts, extensions, line items, quantities, and costs; no dedicated amendment ledger. |
| Austin, Texas | [Contracts](https://datahub.austintexas.gov/d/84ih-p28j) | Contract versions, authorized limits, spending, and balances; amendments must be inferred from versions and only active contracts are visible. |
| Vermont | [Executed Contracts for Service](https://data.vermont.gov/d/dz5q-8uqb) | Executed contract values and spending; amendment history is limited and the data is published as fiscal-year snapshots. |
| Oregon Lottery | [Lottery Contracts](https://data.oregon.gov/d/rkhh-35im) | Purchase orders, contracts, and amendments with line-item values; values are estimates rather than actual payments. |

### Common Target Fields

- Contract and amendment/change-order identifiers
- Agency, department, project, and contractor
- Original contract value and amended or revised value
- Amendment or change-order amount and cumulative value
- Amendment date, effective date, and completion-date changes
- Description, justification, scope, and status
- Procurement method and contract type
- Link to the source contract or amendment document

### Initial Scope

Start with Oregon ORPIN, Cook County, Chicago, and Washington State. These sources provide the strongest combination of structured contract data and amendment-level information for measuring value growth, extensions, frequency, and contractor or agency patterns. Normalize them into a common schema before adding the secondary sources.

## Downloading the Data

The reproducible downloader uses each portal's public Socrata API. It saves the source metadata, raw JSON records, and a CSV export under `data/raw/<dataset>/`.

Requires Python 3.10 or newer. No third-party packages are required.

```bash
# Download the four primary datasets
python3 scripts/download_data.py --group primary

# Download the four secondary datasets
python3 scripts/download_data.py --group secondary

# Download one dataset for a quick test
python3 scripts/download_data.py --dataset oregon_orpin
```

The downloader paginates through every available record and records the UTC download time, dataset ID, source URL, and portal metadata. Use `--output-dir` to choose another destination. Downloaded files are intentionally ignored by Git so raw data does not enter the repository.