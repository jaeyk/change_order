#!/usr/bin/env python3
"""Download contract and amendment datasets from Socrata open-data portals."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


DATASETS: dict[str, dict[str, str]] = {
    "oregon_orpin": {
        "group": "primary",
        "domain": "data.oregon.gov",
        "dataset_id": "6e9e-sfc4",
    },
    "cook_county": {
        "group": "primary",
        "domain": "datacatalog.cookcountyil.gov",
        "dataset_id": "qh8j-6k63",
    },
    "chicago": {
        "group": "primary",
        "domain": "data.cityofchicago.org",
        "dataset_id": "rsxa-ify5",
    },
    "washington_state": {
        "group": "primary",
        "domain": "data.wa.gov",
        "dataset_id": "s8d5-pj78",
    },
    "baton_rouge": {
        "group": "secondary",
        "domain": "data.brla.gov",
        "dataset_id": "2ung-w7t4",
    },
    "austin": {
        "group": "secondary",
        "domain": "datahub.austintexas.gov",
        "dataset_id": "84ih-p28j",
    },
    "vermont": {
        "group": "secondary",
        "domain": "data.vermont.gov",
        "dataset_id": "dz5q-8uqb",
    },
    "oregon_lottery": {
        "group": "secondary",
        "domain": "data.oregon.gov",
        "dataset_id": "rkhh-35im",
    },
}


def get_json(url: str) -> Any:
    request = Request(url, headers={"User-Agent": "change-order-research/1.0"})
    with urlopen(request, timeout=60) as response:
        return json.load(response)


def fetch_records(domain: str, dataset_id: str, page_size: int) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    offset = 0

    while True:
        query = urlencode({"$limit": page_size, "$offset": offset})
        url = f"https://{domain}/resource/{dataset_id}.json?{query}"
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
    config: dict[str, str],
    page_size: int,
) -> None:
    domain = config["domain"]
    dataset_id = config["dataset_id"]
    metadata_url = f"https://{domain}/api/views/{dataset_id}"
    source_url = f"https://{domain}/d/{dataset_id}"

    print(f"Downloading {name} from {source_url}", file=sys.stderr)
    metadata = get_json(metadata_url)
    records = fetch_records(domain, dataset_id, page_size)
    destination = output_dir / name
    destination.mkdir(parents=True, exist_ok=True)

    metadata_record = {
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_url": source_url,
        "metadata_url": metadata_url,
        "domain": domain,
        "dataset_id": dataset_id,
        "group": config["group"],
        "record_count": len(records),
        "metadata": metadata,
    }
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
        choices=("primary", "secondary", "all"),
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
    except (HTTPError, URLError, TimeoutError, ValueError) as error:
        print(f"download failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())