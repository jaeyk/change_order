#!/usr/bin/env python3
"""Build the explicit sampling frame and its coverage table.

Frame (the governments the study aims to describe), from Census Vintage 2024 population estimates:
  * all 50 states and the District of Columbia;
  * every incorporated place (city) with population >= 300,000;
  * every county with population >= 1,000,000, except county-equivalents that are not separate
    governments (New York City boroughs; consolidated city-counties counted once as the city;
    Connecticut / Massachusetts counties with no county government).

Coverage: each frame unit is matched to
  * the contract datasets found by scripts/discover_sources.py (sources/catalog_hits.csv), via the
    reviewed domain map sources/portal_map.csv;
  * the curated list of transparency systems (sources/transparency_systems.csv);
  * the jurisdictions already in the analysis sample.

Writes sources/frame.csv and sources/coverage.csv and prints summary counts.
"""

from __future__ import annotations

import csv
import re
import subprocess
from collections import defaultdict
from pathlib import Path

RAW = Path("data/raw/census")
SRC = Path("sources")
CENSUS = {
    "sub-est2024.csv": "https://www2.census.gov/programs-surveys/popest/datasets/2020-2024/cities/totals/sub-est2024.csv",
    "co-est2024-alldata.csv": "https://www2.census.gov/programs-surveys/popest/datasets/2020-2024/counties/totals/co-est2024-alldata.csv",
}
CITY_MIN, COUNTY_MIN = 300_000, 1_000_000
# county-equivalents that are not a separate government in the frame
NOT_SEPARATE = {
    ("New York", "Bronx County"): "NYC borough (part of New York City)",
    ("New York", "Kings County"): "NYC borough (part of New York City)",
    ("New York", "New York County"): "NYC borough (part of New York City)",
    ("New York", "Queens County"): "NYC borough (part of New York City)",
    ("New York", "Richmond County"): "NYC borough (part of New York City)",
    ("Pennsylvania", "Philadelphia County"): "consolidated with the City of Philadelphia",
    ("Florida", "Duval County"): "consolidated with the City of Jacksonville",
    ("California", "San Francisco County"): "consolidated with the City of San Francisco",
    ("Colorado", "Denver County"): "consolidated with the City of Denver",
    ("Tennessee", "Davidson County"): "consolidated with Nashville",
    ("Kentucky", "Jefferson County"): "consolidated with Louisville",
    ("Indiana", "Marion County"): "consolidated with Indianapolis",
    ("Massachusetts", "Middlesex County"): "no county government (abolished 1997)",
    ("Massachusetts", "Suffolk County"): "no county government (abolished 1999)",
}
STATE_ABBR = dict(zip(
    "Alabama Alaska Arizona Arkansas California Colorado Connecticut Delaware District_of_Columbia Florida Georgia "
    "Hawaii Idaho Illinois Indiana Iowa Kansas Kentucky Louisiana Maine Maryland Massachusetts Michigan Minnesota "
    "Mississippi Missouri Montana Nebraska Nevada New_Hampshire New_Jersey New_Mexico New_York North_Carolina "
    "North_Dakota Ohio Oklahoma Oregon Pennsylvania Rhode_Island South_Carolina South_Dakota Tennessee Texas Utah "
    "Vermont Virginia Washington West_Virginia Wisconsin Wyoming".replace("_", "~").split(),
    "AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK "
    "OR PA RI SC SD TN TX UT VT VA WA WV WI WY".split()))
STATE_ABBR = {k.replace("~", " "): v for k, v in STATE_ABBR.items()}

NARROW = re.compile(r"covid|executive order 166|discretionary|food procurement|tree contract|palantir|largest|"
                    r"cdbg|community development block|storm recovery|hvac|bonding|social service|"
                    r"expiring contracts|prequalified|dbe_contracts|vendor evaluation", re.I)

# jurisdictions already in the analysis sample (contracts_normalized.csv), mapped to frame ids
SAMPLE = {
    "chicago": "city:IL:chicago", "cook_county": "county:IL:cook", "oregon": "state:OR",
    "oregon_lottery": "state:OR", "oregon_treasury": "state:OR", "oregon_judicial": "state:OR",
    "washington_state": "state:WA", "vermont": "state:VT", "austin": "city:TX:austin",
    "nyc_sca": "city:NY:new_york", "wa_doh": "state:WA", "nyc_checkbook": "city:NY:new_york",
    "dc": "state:DC", "dc (same government)": "city:DC:washington",
    "baton_rouge": "outside_frame:LA:baton_rouge",
    "west_hollywood": "outside_frame:CA:west_hollywood",
}


def slug(s: str) -> str:
    s = re.sub(r"\s*\(balance\)", "", s.lower())
    s = re.sub(r" (city|town|village|cdp|county|urban county|metropolitan government|metro government)$", "", s)
    s = re.sub(r"/jefferson county metro government$|-davidson metropolitan government$|-fayette urban county$", "", s)
    return re.sub(r"[^a-z]+", "_", s).strip("_")


def fetch() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    for name, url in CENSUS.items():
        if not (RAW / name).exists():
            subprocess.run(["curl", "-s", "--max-time", "300", "-o", str(RAW / name), url], check=True)


def build_frame() -> list[dict]:
    fetch()
    frame = []
    places = list(csv.DictReader((RAW / "sub-est2024.csv").open(encoding="latin-1")))
    for r in places:
        if r["SUMLEV"] == "040" and r["STNAME"] in STATE_ABBR:
            st = STATE_ABBR[r["STNAME"]]
            frame.append({"unit_id": f"state:{st}", "level": "state", "name": r["STNAME"], "state": st,
                          "population_2024": int(r["POPESTIMATE2024"]), "note": ""})
    for r in places:
        if r["SUMLEV"] == "162" and int(r["POPESTIMATE2024"]) >= CITY_MIN:
            st = STATE_ABBR[r["STNAME"]]
            name = "City and County of Honolulu" if r["NAME"] == "Urban Honolulu CDP" else r["NAME"]
            if name.endswith("CDP"):
                continue  # census-designated places are not governments
            frame.append({"unit_id": f"city:{st}:{slug(name.replace('City and County of ', ''))}", "level": "city", "name": name,
                          "state": st, "population_2024": int(r["POPESTIMATE2024"]), "note": ""})
    for r in csv.DictReader((RAW / "co-est2024-alldata.csv").open(encoding="latin-1")):
        if r["SUMLEV"] == "050" and int(r["POPESTIMATE2024"]) >= COUNTY_MIN:
            st = STATE_ABBR[r["STNAME"]]
            note = NOT_SEPARATE.get((r["STNAME"], r["CTYNAME"]), "")
            frame.append({"unit_id": f"county:{st}:{slug(r['CTYNAME'])}", "level": "county",
                          "name": f"{r['CTYNAME']}, {r['STNAME']}", "state": st,
                          "population_2024": int(r["POPESTIMATE2024"]),
                          "note": note, "excluded": "1" if note else "0"})
    for f in frame:
        f.setdefault("excluded", "0")
    return frame


def main() -> int:
    frame = build_frame()
    SRC.mkdir(exist_ok=True)
    with (SRC / "frame.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["unit_id", "level", "name", "state", "population_2024", "excluded", "note"])
        w.writeheader()
        w.writerows(frame)
    units = {f["unit_id"]: f for f in frame if f["excluded"] == "0"}

    # catalog hits -> units through the reviewed portal map
    pmap = {}
    if (SRC / "portal_map.csv").exists():
        for r in csv.DictReader((SRC / "portal_map.csv").open(encoding="utf-8")):
            pmap[r["domain"]] = r["unit_id"]
    review = {}
    if (SRC / "ledger_review.csv").exists():
        review = {r["dataset_id"]: r for r in csv.DictReader((SRC / "ledger_review.csv").open(encoding="utf-8"))}
    hits = defaultdict(list)
    if (SRC / "catalog_hits.csv").exists():
        for r in csv.DictReader((SRC / "catalog_hits.csv").open(encoding="utf-8")):
            u = pmap.get(r["title"]) or pmap.get(r["domain"]) or pmap.get(r["publisher"])
            if NARROW.search(r["title"]):
                continue  # single-program or emergency-only lists do not cover the government's contracts
            if r["dataset_id"] in review:
                r["class"] = review[r["dataset_id"]]["reviewed_class"]
            if u and r["class"] in ("A", "B", "C") and r["foreign"] == "0":
                hits[u].append(r)
    systems = defaultdict(list)
    if (SRC / "transparency_systems.csv").exists():
        for r in csv.DictReader((SRC / "transparency_systems.csv").open(encoding="utf-8")):
            systems[r["unit_id"]].append(r)
    in_sample = defaultdict(list)
    for j, u in SAMPLE.items():
        in_sample[u].append(j)

    rows = []
    for u, f in units.items():
        hs = hits.get(u, [])
        ss = systems.get(u, [])
        best_open = "A" if any(h["class"] == "A" for h in hs) else "B" if any(h["class"] == "B" for h in hs) else \
            "C" if hs else ""
        sys_amend = any(s.get("amendment_history") == "yes" for s in ss)
        sys_ok = [s for s in ss if s.get("access") in ("api", "bulk download")]
        if in_sample.get(u):
            status = "in sample"
        elif best_open == "A" or (sys_amend and sys_ok):
            status = "available: amendment history"
        elif best_open == "B" or sys_ok:
            status = "available: snapshot only"
        elif ss:
            status = "system exists, no bulk access"
        elif best_open == "C":
            status = "related data only"
        else:
            status = "nothing found"
        rows.append({**f, "status": status, "in_sample": ";".join(in_sample.get(u, [])),
                     "open_data_best": best_open,
                     "open_data_datasets": " ; ".join(f"{h['class']}:{h['domain']}/{h['dataset_id']} {h['title'][:50]}"
                                                    for h in sorted(hs, key=lambda h: h["class"])[:6]),
                     "transparency_systems": " ; ".join(f"{s['system']} ({s['access']}, amendments: "
                                                        f"{s['amendment_history']})" for s in ss)})
    fields = ["unit_id", "level", "name", "state", "population_2024", "status", "in_sample", "open_data_best",
              "open_data_datasets", "transparency_systems"]
    with (SRC / "coverage.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(sorted(rows, key=lambda r: (["state", "city", "county"].index(r["level"]), -r["population_2024"])))
    tab = defaultdict(lambda: defaultdict(int))
    pop = defaultdict(lambda: defaultdict(int))
    for r in rows:
        tab[r["level"]][r["status"]] += 1
        pop[r["level"]][r["status"]] += r["population_2024"]
    for lvl in ("state", "city", "county"):
        print(lvl, sum(tab[lvl].values()), dict(tab[lvl]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
