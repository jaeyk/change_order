#!/usr/bin/env python3
"""Which jurisdictions feed which analysis: counts for Figure Y0.

    python3 synthesis/coverage.py   ->  synthesis/results/data_coverage.json
"""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "simulations"))
from simulate_amendments import load_sector_contracts  # noqa: E402


def main() -> int:
    groups = load_sector_contracts()
    recs = {}
    for k in ("all_tech", "non_tech"):
        for c in groups[k]:
            recs[(c["jurisdiction"], c["contract_id"])] = c
    contracts = list(csv.DictReader((ROOT / "data/processed/contracts_normalized.csv").open(encoding="utf-8")))
    out = {
        "contracts": Counter(r["jurisdiction"] for r in contracts),
        "observable": Counter(r["jurisdiction"] for r in contracts if r["amendment_observable"] == "1"),
        "timing": Counter(c["jurisdiction"] for c in recs.values() if c["times"]),      # dated, within a term
        "sizes": Counter(c["jurisdiction"] for c in recs.values() if len(c["sizes"]) >= 2),  # escalation pairs
        "vendor": Counter(c["jurisdiction"] for c in recs.values() if c["vendor"]),
    }
    rs = ROOT / "data/processed/amendment_reasons_summary.json"
    out["reasons"] = {k: v["informative"] for k, v in json.loads(rs.read_text())["by_jurisdiction"].items()} \
        if rs.exists() else {}
    path = HERE / "results" / "data_coverage.json"
    path.write_text(json.dumps({k: dict(v) for k, v in out.items()}, indent=1))
    print(json.dumps({k: dict(v) for k, v in out.items()}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
