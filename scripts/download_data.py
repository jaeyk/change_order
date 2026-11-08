#!/usr/bin/env python3
"""Download contract and amendment datasets from Socrata open-data portals."""

from __future__ import annotations

import argparse
import csv
import json
import sys
import shutil
import ssl
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

SSL_CONTEXT = ssl.create_default_context()


# Groups:
#   primary / secondary  -- contract ledgers with amendment histories (original 9 sources)
#   expansion            -- additional state and local contract ledgers with amendment data
#   cooperative          -- cooperative-purchasing (NASPO ValuePoint, Sourcewell, OMNIA, TIPS,
#                           Texas DIR, state master contracts...) sales, vehicle flags, and
#                           vendor/reseller relationships with certification (HUB/MWBE) grades
#
# Datasets with a "query" are aggregated server-side with SoQL (the raw tables hold
# millions of invoice lines); every other dataset is downloaded row-for-row.
TX_DIR_GROUP_COLS = (
    "fiscal_year,customer_type,rfo_number,contract_number,contract_type,contract_subtype,"
    "vendor_name,vendor_hub_type,reseller_name,reseller_hub_type"
)

DATASETS: dict[str, dict[str, Any]] = {
    # ---- primary -----------------------------------------------------------
    "oregon_orpin": {"group": "primary", "domain": "data.oregon.gov", "dataset_id": "6e9e-sfc4"},
    "cook_county": {"group": "primary", "domain": "datacatalog.cookcountyil.gov", "dataset_id": "qh8j-6k63"},
    "chicago": {"group": "primary", "domain": "data.cityofchicago.org", "dataset_id": "rsxa-ify5"},
    "washington_state": {"group": "primary", "domain": "data.wa.gov", "dataset_id": "s8d5-pj78"},  # FY2024
    # ---- secondary ---------------------------------------------------------
    "baton_rouge": {"group": "secondary", "domain": "data.brla.gov", "dataset_id": "2ung-w7t4"},
    "austin": {"group": "secondary", "domain": "datahub.austintexas.gov", "dataset_id": "84ih-p28j"},
    "vermont": {"group": "secondary", "domain": "data.vermont.gov", "dataset_id": "dz5q-8uqb"},
    "oregon_lottery": {"group": "secondary", "domain": "data.oregon.gov", "dataset_id": "rkhh-35im"},
    "nyc_sca": {"group": "secondary", "domain": "data.cityofnewyork.us", "dataset_id": "gzvm-na49"},
    # ---- expansion: more states & local governments ------------------------
    "washington_fy2021": {"group": "expansion", "domain": "data.wa.gov", "dataset_id": "buf8-6px9"},
    "washington_fy2022": {"group": "expansion", "domain": "data.wa.gov", "dataset_id": "pwse-3zea"},
    "washington_fy2023": {"group": "expansion", "domain": "data.wa.gov", "dataset_id": "mz6y-pfem"},
    "washington_fy2025": {"group": "expansion", "domain": "data.wa.gov", "dataset_id": "6fx9-ncas"},
    "oregon_judicial": {"group": "expansion", "domain": "data.oregon.gov", "dataset_id": "3wxk-gaen"},
    "oregon_treasury": {"group": "expansion", "domain": "data.oregon.gov", "dataset_id": "4iz8-xm93"},
    "west_hollywood": {"group": "expansion", "domain": "data.weho.org", "dataset_id": "atdr-sk64"},
    # ---- cooperative purchasing, resellers & certification grades -----------
    "wa_it_contracts_2020": {"group": "cooperative", "domain": "data.wa.gov", "dataset_id": "reg9-mjd3"},
    "wa_it_contracts_2021": {"group": "cooperative", "domain": "data.wa.gov", "dataset_id": "bcyw-k8i3"},
    "wa_it_contracts_2022": {"group": "cooperative", "domain": "data.wa.gov", "dataset_id": "dzvi-rs2c"},
    "wa_it_contracts_2023": {"group": "cooperative", "domain": "data.wa.gov", "dataset_id": "hycx-v82h"},
    "wa_it_contracts_2024": {"group": "cooperative", "domain": "data.wa.gov", "dataset_id": "ktim-amuz"},
    "wa_it_contracts_2025": {"group": "cooperative", "domain": "data.wa.gov", "dataset_id": "3txe-z9i9"},
    "wa_master_contract_sales": {
        "group": "cooperative", "domain": "data.wa.gov", "dataset_id": "n8q6-4twj",
        "query": {
            "$select": "year,customer_type,contract_number,contract_title,vendor_name,omwbe,vet_owned,"
                       "small_business,sum(q1_sales_reported)+sum(q2_sales_reported)+sum(q3_sales_reported)"
                       "+sum(q4_sales_reported) as sales,count(*) as n_lines",
            "$group": "year,customer_type,contract_number,contract_title,vendor_name,omwbe,vet_owned,small_business",
            "$order": "year,contract_number,vendor_name,customer_type",
        },
    },
    "tx_dir_sales_archive": {
        "group": "cooperative", "domain": "data.texas.gov", "dataset_id": "w64c-ndf7",
        "query": {
            "$select": TX_DIR_GROUP_COLS + ",sum(purchase_amount) as sales,count(*) as n_lines",
            "$group": TX_DIR_GROUP_COLS,
            "$order": TX_DIR_GROUP_COLS,
        },
    },
    "tx_dir_sales_fy2026": {
        "group": "cooperative", "domain": "data.texas.gov", "dataset_id": "a743-wj72",
        "query": {
            "$select": TX_DIR_GROUP_COLS + ",sum(purchase_amount) as sales,count(*) as n_lines",
            "$group": TX_DIR_GROUP_COLS,
            "$order": TX_DIR_GROUP_COLS,
        },
    },
    "tx_dir_active_contracts": {"group": "cooperative", "domain": "data.texas.gov", "dataset_id": "vipt-h4ye"},
    "ny_var_report": {"group": "cooperative", "domain": "data.ny.gov", "dataset_id": "cjqa-a3p4"},
    "delaware_coop_spend": {"group": "cooperative", "domain": "data.delaware.gov", "dataset_id": "6a9e-y46r"},
    "delaware_central_spend": {"group": "cooperative", "domain": "data.delaware.gov", "dataset_id": "sifm-293u"},
}

# ---- reseller evidence --------------------------------------------------------------
# Federal Supply Schedule contracts (GSA MAS + VA FSS) from USASpending, award type IDV_C.
# Used (1) as extra reseller evidence -- holders registered under wholesale/retail NAICS
# (42, 44-45) are dealers -- and (2) for the vendor-qualification covariate (GSA MAS holder).
DATASETS["federal_supply_schedules"] = {
    "group": "federal_schedules",
    "source": "usaspending",
    "endpoint": "https://api.usaspending.gov/api/v2/search/spending_by_award/",
    "filters": {
        "award_type_codes": ["IDV_C"],
        "time_period": [{"start_date": "2007-10-01", "end_date": datetime.now(timezone.utc).strftime("%Y-%m-%d")}],
    },
    "fields": [
        "Award ID", "Recipient Name", "Recipient UEI", "Start Date", "End Date", "Last Date to Order",
        "Awarding Agency", "Awarding Sub Agency", "Description", "NAICS", "PSC", "Contract Award Type",
    ],
}

GROUPS = ("primary", "secondary", "expansion", "cooperative", "federal_schedules")


def get_json(url: str, payload: dict[str, Any] | None = None) -> Any:
    """GET (or POST a JSON payload) and decode the JSON response."""
    data = json.dumps(payload).encode() if payload is not None else None
    headers = {"User-Agent": "change-order-research/1.0"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    request = Request(url, data=data, headers=headers)
    try:
        with urlopen(request, context=SSL_CONTEXT, timeout=300) as response:
            return json.load(response)
    except URLError as e:
        # Some Python builds (e.g. Homebrew) ship without access to the OS trust store.
        # Fall back to curl, which uses the system certificates, instead of disabling
        # certificate verification.
        if "CERTIFICATE_VERIFY_FAILED" in str(e) and shutil.which("curl"):
            cmd = ["curl", "-sSfL", "--max-time", "600", "-A", "change-order-research/1.0"]
            if data is not None:
                cmd += ["-X", "POST", "-H", "Content-Type: application/json", "--data-binary", "@-"]
            out = subprocess.run(cmd + [url], input=data, capture_output=True, check=True)
            return json.loads(out.stdout)
        raise


def fetch_usaspending(config: dict[str, Any], page_size: int = 100) -> list[dict[str, Any]]:
    """Keyset-paginate USASpending's spending_by_award search (avoids deep-page limits)."""
    records: list[dict[str, Any]] = []
    last_id: Any = None
    last_sort: Any = None
    while True:
        payload: dict[str, Any] = {
            "filters": config["filters"],
            "fields": config["fields"],
            "limit": min(page_size, 100),
            "sort": "Award ID",
            "order": "asc",
            "page": 1,
        }
        if last_id is not None:
            payload["last_record_unique_id"] = last_id
            payload["last_record_sort_value"] = last_sort
        for attempt in range(6):
            try:
                page = get_json(config["endpoint"], payload)
                break
            except (HTTPError, URLError, TimeoutError, subprocess.CalledProcessError) as err:
                if attempt == 5:
                    raise
                wait = 5 * 2 ** attempt
                print(f"  request failed ({err}); retrying in {wait}s", file=sys.stderr)
                time.sleep(wait)
        rows = page.get("results", [])
        for r in rows:
            for key in ("NAICS", "PSC"):
                v = r.pop(key, None) or {}
                r[f"{key.lower()}_code"] = v.get("code") if isinstance(v, dict) else v
                r[f"{key.lower()}_description"] = v.get("description") if isinstance(v, dict) else ""
        records.extend(rows)
        if len(records) % 5000 < len(rows) or not rows:
            print(f"  fetched {len(records):,} records", file=sys.stderr)
        meta = page.get("page_metadata", {})
        if not rows or not meta.get("hasNext"):
            print(f"  fetched {len(records):,} records", file=sys.stderr)
            return records
        last_id, last_sort = meta.get("last_record_unique_id"), meta.get("last_record_sort_value")


def fetch_records(
    domain: str,
    dataset_id: str,
    page_size: int,
    query: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    offset = 0

    while True:
        params = dict(query or {})
        params.update({"$limit": page_size, "$offset": offset})
        if "$order" not in params:
            params["$order"] = ":id"  # stable paging
        url = f"https://{domain}/resource/{dataset_id}.json?{urlencode(params)}"
        page = get_json(url)
        if not isinstance(page, list):
            raise ValueError(f"Expected a list from {url}")
        records.extend(page)
        print(f"  fetched {len(records):,} records", file=sys.stderr)
        if len(page) < page_size:
            return records
        offset += page_size


def write_dataset(
    output_dir: Path,
    name: str,
    config: dict[str, Any],
    page_size: int,
) -> None:
    if config.get("source") == "usaspending":
        print(f"Downloading {name} from {config['endpoint']}", file=sys.stderr)
        records = fetch_usaspending(config)
        metadata_record = {
            "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
            "source_url": config["endpoint"],
            "group": config["group"],
            "filters": config["filters"],
            "record_count": len(records),
        }
        _write_outputs(output_dir / name, metadata_record, records)
        return

    domain = config["domain"]
    dataset_id = config["dataset_id"]
    metadata_url = f"https://{domain}/api/views/{dataset_id}"
    source_url = f"https://{domain}/d/{dataset_id}"

    print(f"Downloading {name} from {source_url}", file=sys.stderr)
    metadata = get_json(metadata_url)
    records = fetch_records(domain, dataset_id, page_size, config.get("query"))
    metadata_record = {
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_url": source_url,
        "metadata_url": metadata_url,
        "domain": domain,
        "dataset_id": dataset_id,
        "group": config["group"],
        "aggregation_query": config.get("query"),
        "record_count": len(records),
        "metadata": metadata,
    }
    _write_outputs(output_dir / name, metadata_record, records)


def _write_outputs(destination: Path, metadata_record: dict[str, Any], records: list[dict[str, Any]]) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "metadata.json").write_text(
        json.dumps(metadata_record, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (destination / "records.json").write_text(
        json.dumps(records, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    fieldnames = sorted({key for record in records for key in record})
    with (destination / "records.csv").open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--group",
        choices=GROUPS + ("all",),
        default="primary",
        help="Dataset group to download (default: primary)",
    )
    parser.add_argument(
        "--dataset",
        choices=tuple(DATASETS),
        action="append",
        help="Download a named dataset; may be supplied more than once",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/raw"),
        help="Directory for downloaded datasets (default: data/raw)",
    )
    parser.add_argument(
        "--page-size",
        type=int,
        default=50_000,
        help="Number of records requested per API page (default: 50000)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.page_size < 1:
        raise ValueError("--page-size must be positive")

    names = args.dataset or [
        name
        for name, config in DATASETS.items()
        if args.group == "all" or config["group"] == args.group
    ]
    try:
        for name in names:
            write_dataset(args.output_dir, name, DATASETS[name], args.page_size)
    except (HTTPError, URLError, TimeoutError, ValueError, subprocess.CalledProcessError) as error:
        print(f"download failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())