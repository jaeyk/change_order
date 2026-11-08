#!/usr/bin/env python3
"""Sweep public open-data catalogs for contract ledgers, so the sample's coverage is documented.

Catalogs searched (all free, keyless, public):
  socrata     api.us.socrata.com/api/catalog/v1   (every Socrata-hosted portal)
  datagov     catalog.data.gov/search             (federal catalog; harvests state/local portals)
  arcgis      hub.arcgis.com/api/search/v1        (ArcGIS Hub / ArcGIS Online open data)
  opendatasoft data.opendatasoft.com/api/explore/v2.1/catalog  (OpenDataSoft network)

For every dataset whose title names contracts, purchase orders or procurement, the script records
its columns (when the catalog exposes them, or from the ArcGIS layer definition) and classifies it:

  A  contract ledger with amendment history   (amendment / modification / revision / original-vs-current fields)
  B  contract ledger, snapshot only           (contract-level rows with money and vendor fields)
  C  related                                   (bids, buying plans, cooperative sales, spending)
  -  not a ledger

Writes sources/catalog_hits.csv. Polite: one request every 3 seconds.

    python3 scripts/discover_sources.py            # all catalogs
    python3 scripts/discover_sources.py socrata    # one catalog
"""

from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import quote, urlencode

OUT = Path("sources/catalog_hits.csv")
PAUSE = 3.0
QUERIES = ["contracts", "contract amendments", "change orders", "contract modifications", "purchase orders",
           "procurement", "awarded contracts", "vendor contracts", "contract register"]

TITLE = re.compile(r"contract|purchase.?order|procure|change.?order|\bawards?\b|vendor|supplier", re.I)
NOT_LEDGER = re.compile(r"land.?use|easement|grant(?:s|ee)? (?:program|application)|survey123|_form\b|"
                        r"zoning|parcel|permit|license(?:d|s)? (?:business|contractor)|contractor licens|"
                        r"covid.*vaccin|minority.?business directory|certified (?:firms|vendors)", re.I)
AMEND = re.compile(r"amend|modif|change.?order|revision|supplement|\bversion|orig|initial_?(?:amount|value|award|"
                   r"contract|cost)|current_?(?:amount|value|contract)|revised|renewal|extension|total_?(?:award|"
                   r"contract)_?value_?w", re.I)
MONEY = re.compile(r"amount|value|cost|price|total|dollar|\bamt|spend|paid|encumb", re.I)
PARTY = re.compile(r"vendor|supplier|contractor|payee|company|firm|awardee|business_name|recipient", re.I)
RELATED = re.compile(r"bid|solicitation|buying.?plan|forecast|cooperative|statewide contract|spend|payment|checkbook|"
                     r"expenditure", re.I)
FOREIGN = re.compile(r"\.(?:au|ca|uk|nz|mx|cl|ie|fr|es|it|de|be|ch|za|br|co|in|ph|ng|ke)(?:/|$)|\.gc\.ca|gov\.uk|"
                     r"opendata\.paris|data\.gouv", re.I)


def get(url: str, data: bytes | None = None) -> dict:
    """GET (or POST) JSON with certificate verification, via curl for a consistent TLS stack."""
    cmd = ["curl", "-s", "--max-time", "90", "-H", "Accept: application/json", url]
    for attempt in range(3):
        r = subprocess.run(cmd, capture_output=True, text=True)
        time.sleep(PAUSE)
        try:
            return json.loads(r.stdout)
        except json.JSONDecodeError:
            time.sleep(5 * (attempt + 1))
    return {}


def classify(title: str, cols: list[str]) -> str:
    if not TITLE.search(title) or NOT_LEDGER.search(title):
        return "-"
    c = " ".join(cols)
    has_money, has_party = bool(MONEY.search(c)), bool(PARTY.search(c) or PARTY.search(title))
    if cols and has_money and any(AMEND.search(x) for x in cols) and has_party:
        return "A"
    if cols and has_money and has_party and not RELATED.search(title):
        return "B"
    if RELATED.search(title) or (cols and has_money):
        return "C"
    return "B?" if not cols else "-"


def socrata() -> list[dict]:
    rows = []
    for q in QUERIES:
        for off in range(0, 5000, 100):
            d = get(f"https://api.us.socrata.com/api/catalog/v1?{urlencode({'q': q, 'only': 'dataset', 'limit': 100, 'offset': off})}")
            res = d.get("results", [])
            for r in res:
                m, s = r["metadata"], r["resource"]
                rows.append({"platform": "socrata", "domain": m.get("domain", ""), "dataset_id": s["id"],
                             "title": s.get("name", ""), "publisher": s.get("attribution") or m.get("domain", ""),
                             "publisher_type": "", "updated": (s.get("updatedAt") or "")[:10],
                             "url": f"https://{m.get('domain')}/d/{s['id']}",
                             "columns": "|".join(s.get("columns_field_name", []))})
            if len(res) < 100:
                break
    return rows


def datagov() -> list[dict]:
    rows = []
    for q in QUERIES:
        after = None
        for _ in range(10):
            params = {"q": q, "per_page": 100}
            if after:
                params["after"] = after
            d = get(f"https://catalog.data.gov/search?{urlencode(params)}")
            res = d.get("results", [])
            for r in res:
                dc, org = r.get("dcat", {}), r.get("organization") or {}
                dist = [x.get("downloadURL") or x.get("accessURL") or "" for x in (dc.get("distribution") or []) if isinstance(x, dict)]
                rows.append({"platform": "datagov", "domain": r.get("publisher") or "", "dataset_id": r.get("slug", ""),
                             "title": dc.get("title", ""), "publisher": org.get("title", ""),
                             "publisher_type": org.get("organization_type", ""),
                             "updated": (dc.get("modified") or "")[:10],
                             "url": f"https://catalog.data.gov/dataset/{r.get('slug', '')}",
                             "columns": "", "distribution": " ".join(dist[:3])})
            after = d.get("after")
            if not after or len(res) < 100:
                break
    return rows


def arcgis() -> list[dict]:
    rows = []
    for q in QUERIES:
        for start in range(1, 1001, 100):
            d = get(f"https://hub.arcgis.com/api/search/v1/collections/dataset/items?"
                    f"{urlencode({'q': q, 'limit': 100, 'startindex': start})}")
            feats = d.get("features", [])
            for f in feats:
                p = f["properties"]
                title = p.get("title") or ""
                cols = []
                if TITLE.search(title) and not NOT_LEDGER.search(title) and p.get("url"):
                    lay = get(p["url"].rstrip("/") + ("" if re.search(r"/\d+$", p["url"]) else "/0") + "?f=json")
                    cols = [x.get("name", "") for x in lay.get("fields") or []]
                rows.append({"platform": "arcgis", "domain": (p.get("url") or "").split("/")[2] if p.get("url") else "",
                             "dataset_id": p.get("id", ""), "title": title, "publisher": p.get("source") or p.get("owner", ""),
                             "publisher_type": "", "updated": "", "url": p.get("url", ""),
                             "columns": "|".join(cols)})
            if len(feats) < 100:
                break
    return rows


def opendatasoft() -> list[dict]:
    rows = []
    for q in QUERIES:
        for off in range(0, 1000, 100):
            where = quote(f'search("{q}")')
            d = get(f"https://data.opendatasoft.com/api/explore/v2.1/catalog/datasets?where={where}&limit=100&offset={off}")
            res = d.get("results", [])
            for r in res:
                meta = (r.get("metas") or {}).get("default", {})
                lang = meta.get("language") or ""
                rows.append({"platform": "opendatasoft", "domain": r.get("dataset_id", "").split("@")[-1],
                             "dataset_id": r.get("dataset_id", ""), "title": meta.get("title", ""),
                             "publisher": meta.get("publisher") or "", "publisher_type": lang,
                             "updated": (meta.get("modified") or "")[:10], "url": "",
                             "columns": "|".join(x.get("name", "") for x in r.get("fields", []))})
            if len(res) < 100:
                break
    return rows


def main() -> int:
    which = sys.argv[1:] or ["socrata", "datagov", "arcgis", "opendatasoft"]
    old = []
    if OUT.exists():
        old = [r for r in csv.DictReader(OUT.open(encoding="utf-8")) if r["platform"] not in which]
    new = []
    for name in which:
        try:
            got = globals()[name]()
        except Exception as e:  # keep what the other catalogs returned
            print(f"{name}: failed ({e!r})", flush=True)
            continue
        print(f"{name}: {len(got)} raw hits", flush=True)
        new += got
        write(old + new)
    write(old + new)
    return 0


def write(all_rows: list[dict]) -> None:
    seen, rows = set(), []
    for r in all_rows:
        key = (r["platform"], r["dataset_id"])
        if key in seen:
            continue
        seen.add(key)
        r.setdefault("distribution", "")
        r = {k: (v or "") for k, v in r.items()}
        r["foreign"] = "1" if FOREIGN.search(r["domain"] + "/") or (r["platform"] == "opendatasoft" and r["publisher_type"] not in ("", "en")) else "0"
        r["class"] = classify(r["title"], [c for c in r["columns"].split("|") if c])
        rows.append(r)
    OUT.parent.mkdir(exist_ok=True)
    fields = ["platform", "class", "foreign", "domain", "dataset_id", "title", "publisher", "publisher_type",
              "updated", "url", "distribution", "columns"]
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(sorted(rows, key=lambda r: (r["class"], r["platform"], r["domain"])))
    us = [r for r in rows if r["foreign"] == "0"]
    for c in ("A", "B", "B?", "C"):
        print(c, sum(r["class"] == c for r in us), "datasets on", len({r["domain"] for r in us if r["class"] == c}), "domains")


if __name__ == "__main__":
    raise SystemExit(main())
