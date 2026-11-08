#!/usr/bin/env python3
"""Build the horizontal-vs-vertical cooperative purchasing network page.

Inputs:  data/processed/contracts_normalized.csv, data/processed/cooperative_sales.csv
Outputs: data/processed/procurement_network.json, data/processed/procurement_network.html

Tiers (top to bottom): state buyers, state & multi-state vehicles, local cooperatives,
local buyers. Short edges stay within a level of government (horizontal pooling or
central purchasing); long edges cross levels (vertical piggybacking). Federal links are
thin in these data and are reported as a footnote instead of a tier.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

PROCESSED = Path("data/processed")
TEMPLATE = Path(__file__).with_name("procurement_network_template.html")

STATE = {"TX": "Texas", "WA": "Washington", "DE": "Delaware", "IL": "Illinois", "LA": "Louisiana",
         "OR": "Oregon", "CA": "California", "NY": "New York", "VT": "Vermont"}
VEH = {"texas_dir": "Texas DIR", "naspo_valuepoint": "NASPO ValuePoint", "sourcewell": "Sourcewell",
       "omnia_partners": "OMNIA Partners", "tips_taps": "TIPS/TAPS", "ncpa": "NCPA", "e_and_i": "E&I Cooperative",
       "mhec": "MHEC", "mmcap": "MMCAP", "gsa_federal": "GSA schedules", "buyboard": "BuyBoard",
       "hgacbuy": "HGACBuy", "kcda": "KCDA", "wsipc": "WSIPC", "oetc": "OETC", "peppm": "PEPPM",
       "internet2": "Internet2", "calif_cmas": "California CMAS", "local_joint_purchase": "Joint purchases",
       "other_cooperative": "Unnamed cooperative"}
STATE_LEVEL = {"naspo_valuepoint", "mhec", "mmcap", "texas_dir", "state_master_contract", "state_contract",
               "calif_cmas", "e_and_i", "internet2"}
BUYER = {"washington_state": ("Washington state agencies", "state_buyer"),
         "oregon": ("Oregon state agencies", "state_buyer"), "oregon_lottery": ("Oregon state agencies", "state_buyer"),
         "oregon_judicial": ("Oregon state agencies", "state_buyer"),
         "oregon_treasury": ("Oregon state agencies", "state_buyer"),
         "vermont": ("Vermont state agencies", "state_buyer"), "chicago": ("Chicago", "local_buyer"),
         "cook_county": ("Cook County", "local_buyer"), "baton_rouge": ("Baton Rouge", "local_buyer"),
         "west_hollywood": ("West Hollywood", "local_buyer"), "austin": ("Austin", "local_buyer"),
         "nyc_sca": ("NYC School Constr. Auth.", "local_buyer"),
         "wa_doh": ("Washington state agencies", "state_buyer"), "nyc_checkbook": ("New York City", "local_buyer"),
         "dc": ("District of Columbia agencies", "state_buyer")}
CUSTOMER = {"state_agency": ("state agencies", "state_buyer"), "higher_ed": ("public universities", "state_buyer"),
            "local_government": ("local governments", "local_buyer"), "k12": ("school districts", "local_buyer"),
            "out_of_state": ("other states", "state_buyer"), "federal": ("federal agencies", "federal"),
            "tribal_government": ("tribal governments", "local_buyer")}
DIRECTIONS = ["vertical_downward", "horizontal", "vertical_upward", "central", "unknown"]


def vehicle_name(v: str, state: str, program: str = "") -> str:
    if v == "state_master_contract":
        return {"WA": "WA DES statewide", "OR": "Oregon DAS price agreements",
                "DE": "Delaware statewide"}.get(state, f"{STATE.get(state, state)} statewide")
    if v == "state_contract":
        return f"{STATE.get(state, state)} state contracts"
    if v == "other_cooperative" and program == "delaware_cooperative":
        return "Delaware external cooperatives"
    return VEH.get(v, v)


def vehicle_row(v: str) -> str:
    if v == "gsa_federal":
        return "federal"
    return "state_vehicle" if v in STATE_LEVEL else "local_vehicle"


def pack(counter: Counter) -> dict:
    edges, federal = [], []
    for (buyer, brow, vehicle, vrow, direction), value in counter.items():
        if value <= 0:
            continue
        e = {"buyer": buyer, "brow": brow, "vehicle": vehicle, "vrow": vrow, "dir": direction, "value": round(value)}
        (federal if "federal" in (brow, vrow) else edges).append(e)
    key = lambda e: -e["value"]
    return {"edges": sorted(edges, key=key), "federal": sorted(federal, key=key)}


def main() -> int:
    ledger: Counter = Counter()
    with (PROCESSED / "contracts_normalized.csv").open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            v = r["coop_vehicle"]
            if not v or r["jurisdiction"] not in BUYER:
                continue
            name = vehicle_name(v, r["state"])
            if v == "state_contract" and r["jurisdiction"] == "chicago":
                t = r["title_desc"].lower()
                name = "Illinois state contracts" if ("illinois" in t or "cms" in t) else "Other states' contracts"
            buyer, brow = BUYER[r["jurisdiction"]]
            ledger[(buyer, brow, name, vehicle_row(v), r["coop_direction"] or "unknown")] += 1

    sales: Counter = Counter()
    with (PROCESSED / "cooperative_sales.csv").open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["customer_type"] not in CUSTOMER:
                continue
            label, brow = CUSTOMER[r["customer_type"]]
            st = STATE[r["state"]]
            buyer = f"Other states (via {st})" if r["customer_type"] == "out_of_state" else f"{st}: {label}"
            v = r["coop_vehicle"]
            sales[(buyer, brow, vehicle_name(v, r["state"], r["program"]), vehicle_row(v),
                   r["coop_direction"] or "unknown")] += float(r["sales"] or 0)

    data = {"dollars": pack(sales), "contracts": pack(ledger)}
    totals = {view: {d: sum(e["value"] for e in data[view]["edges"] if e["dir"] == d) for d in DIRECTIONS}
              for view in data}
    (PROCESSED / "procurement_network.json").write_text(json.dumps({"data": data, "totals": totals}, indent=1))
    html = TEMPLATE.read_text(encoding="utf-8")
    html = html.replace("__DATA__", json.dumps(data, separators=(",", ":"))).replace("__TOTALS__", json.dumps(totals))
    (PROCESSED / "procurement_network.html").write_text(html, encoding="utf-8")
    for view, t in totals.items():
        print(view, {k: f"{v:,}" for k, v in t.items()})
    print(f"Wrote {PROCESSED / 'procurement_network.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
