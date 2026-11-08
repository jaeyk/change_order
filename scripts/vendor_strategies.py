#!/usr/bin/env python3
"""Vendor strategies by sector: one table that puts every strategy measure side by side.

Pulls the amendment fingerprints already estimated in simulations/ and the document codes in
synthesis/, and adds two measures not computed elsewhere:

* follow-on awards: how often a department's next contract in a sector goes to the same vendor
  as its previous one, against a benchmark that shuffles the order of awards within each
  jurisdiction x department x sector cell (same vendors, same counts, random timing);
* sales channel: cooperative / central vehicles, authorized resellers and multiple-award
  vehicles, with amendment rates and value growth in each.

Writes data/processed/vendor_strategies.json. Reads only processed files; standard library only.
"""

from __future__ import annotations

import csv
import json
import math
import random
import statistics
from collections import Counter, defaultdict
from pathlib import Path

PROCESSED = Path("data/processed")
SECTORS = ["software_saas", "hardware_telecom", "it_services", "tech_general", "non_tech"]
SIM_KEY = {s: ("non_tech" if s == "non_tech" else f"subsector:{s}") for s in SECTORS}
SHUFFLES = 20
SEED = 20261108


def growth(r: dict) -> float | None:
    try:
        a, b = float(r["initial_award_val"]), float(r["final_award_val"])
    except ValueError:
        return None
    return b / a if a >= 1000 and b > 0 else None


def wilson(k: int, n: int) -> list[float]:
    if not n:
        return [None, None]
    p, z = k / n, 1.96
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(c - h, 4), round(c + h, 4)]


def incumbent_rate(seq: list[str]) -> tuple[int, int]:
    """Awards that go to the same vendor as the cell's previous award (a run of follow-ons).

    Order matters here, so shuffling the order within a cell gives a benchmark with the same
    vendors and counts but no continuity."""
    hits = sum(1 for a, b in zip(seq, seq[1:]) if a == b)
    return hits, max(len(seq) - 1, 0)


def main() -> int:
    rows = list(csv.DictReader((PROCESSED / "contracts_normalized.csv").open(encoding="utf-8")))
    out: dict = {"sectors": {}}

    # ---- simulation fingerprints and document codes (already estimated) ----------------------
    fp = defaultdict(dict)
    for r in csv.DictReader(open("simulations/results/sector_fingerprints.csv", encoding="utf-8")):
        if r["observed"]:
            fp[r["sector"]][r["fingerprint"]] = (float(r["observed"]), float(r["chance_mean"]), float(r["z"]))
    rank = {r["sector"]: r for r in csv.DictReader(open("simulations/results/lockin_ranking.csv", encoding="utf-8"))}
    docs = json.load(open("synthesis/results/document_summary.json", encoding="utf-8"))["by_sector"]
    snow = json.load(open("figures/figure_data.json", encoding="utf-8"))["snowball"]

    # ---- follow-on awards ------------------------------------------------------------------
    cells: dict[tuple, list[tuple[str, str]]] = defaultdict(list)
    for r in rows:
        v, d = r["vendor_name"].upper().strip(), r["department"].strip()
        if v and d and r["start_date"][:4].isdigit():
            cells[(r["jurisdiction"], d, r["tech_subsector"])].append((r["start_date"][:10], v))
    rng = random.Random(SEED)
    follow = {}
    for s in SECTORS:
        obs_h = obs_n = 0
        sh_h = [0] * SHUFFLES
        for (j, d, sec), awards in cells.items():
            if sec != s or len(awards) < 2:
                continue
            # one entry per vendor per month, so split purchase orders are not counted as follow-ons
            awards = sorted({(d[:7], v) for d, v in awards})
            if len(awards) < 2:
                continue
            seq = [v for _, v in awards]
            h, n = incumbent_rate(seq)
            obs_h, obs_n = obs_h + h, obs_n + n
            for k in range(SHUFFLES):
                perm = seq[:]
                rng.shuffle(perm)
                sh_h[k] += incumbent_rate(perm)[0]
        bench = statistics.mean(sh_h) / obs_n if obs_n else None
        follow[s] = {"awards": obs_n, "to_incumbent": round(obs_h / obs_n, 4), "ci95": wilson(obs_h, obs_n),
                     "shuffled_order_benchmark": round(bench, 4),
                     "excess_pts": round(100 * (obs_h / obs_n - bench), 1),
                     "ratio": round((obs_h / obs_n) / bench, 3)}

    # ---- concentration: top-4 vendors' share of dollars, median across jurisdictions ---------
    dollars = defaultdict(lambda: defaultdict(float))
    for r in rows:
        try:
            x = float(r["final_award_val"] or r["initial_award_val"] or 0)
        except ValueError:
            continue
        if x > 0 and r["vendor_name"].strip():
            dollars[(r["jurisdiction"], r["tech_subsector"])][r["vendor_name"].upper().strip()] += x
    conc = {}
    for s in SECTORS:
        shares = []
        for (j, sec), byv in dollars.items():
            if sec == s and len(byv) >= 10:
                tot = sum(byv.values())
                shares.append(sum(sorted(byv.values(), reverse=True)[:4]) / tot)
        conc[s] = round(statistics.median(shares), 3) if shares else None

    # ---- amendment outcomes and channels --------------------------------------------------
    for s in SECTORS:
        sec = [r for r in rows if r["tech_subsector"] == s]
        obs = [r for r in sec if r["amendment_observable"] == "1"]
        amended = [r for r in obs if r["is_amended"] == "1"]
        g = [x for x in (growth(r) for r in amended) if x]
        channel = {}
        for name, test in (
            ("cooperative_or_central", lambda r: r["procurement_channel"] not in ("", "direct_or_unknown")),
            ("authorized_reseller", lambda r: r["vendor_role"] == "authorized_reseller"),
            ("multiple_award", lambda r: r["award_structure"].startswith("multiple_award")),
            ("federal_schedule_holder", lambda r: r["gsa_mas_holder"] == "1"),
        ):
            inn = [r for r in sec if test(r)]
            inn_obs = [r for r in inn if r["amendment_observable"] == "1"]
            out_obs = [r for r in obs if not test(r)]
            rate = lambda xs: round(sum(r["is_amended"] == "1" for r in xs) / len(xs), 4) if xs else None
            gi = [x for x in (growth(r) for r in inn_obs if r["is_amended"] == "1") if x]
            channel[name] = {"share": round(len(inn) / len(sec), 4), "contracts": len(inn),
                             "amend_rate": rate(inn_obs), "amend_rate_others": rate(out_obs),
                             "observable": len(inn_obs),
                             "median_growth_when_amended": round(statistics.median(gi), 3) if len(gi) >= 20 else None}
        f = fp[SIM_KEY[s]]
        d = docs.get(s, {})
        dn = sum(d.values())
        fx = lambda k: {"observed": round(f[k][0], 4), "chance": round(f[k][1], 4), "z": f[k][2]} if k in f else None
        rk = rank.get(SIM_KEY[s], {})
        out["sectors"][s] = {
            "contracts": len(sec), "observable": len(obs),
            "amended_share": round(len(amended) / len(obs), 4) if obs else None,
            "median_growth_when_amended": round(statistics.median(g), 3) if g else None,
            "share_amended_doubling": round(sum(x >= 2 for x in g) / len(g), 4) if g else None,
            "value_after_6_amendments": snow["panel_a"].get(s, [None])[-1],
            "value_after_6_ci95": snow["panel_a_ci95"].get(s, [None])[-1],
            "cohort_6plus": snow["panel_a_n"].get(s),
            "fingerprints": {k: fx(k) for k in ("early", "late", "escal", "vendor", "accel_pre", "cont")},
            "evidence_tier": rk.get("evidence_tier_label"), "thin": rk.get("thin") == "True",
            "documents": {"coded": dn, "re_competition_delayed": d.get("re-competition delayed", 0),
                          "design": d.get("design", 0), "chance": d.get("chance", 0),
                          "no_cause_stated": d.get("no cause stated", 0)},
            "follow_on": follow[s], "top4_dollar_share_median": conc[s], "channels": channel,
        }

    (PROCESSED / "vendor_strategies.json").write_text(json.dumps(out, indent=1))
    hdr = ("sector", "n", "amend", "grow", "6x", "early o/c", "late o/c", "escal o/c", "vendor", "follow o/b",
           "top4", "coop", "resell", "multi")
    print(" | ".join(hdr))
    for s, v in out["sectors"].items():
        F = v["fingerprints"]
        oc = lambda k: f"{F[k]['observed']:.2f}/{F[k]['chance']:.2f}"
        c = v["channels"]
        print(" | ".join(map(str, (s, v["contracts"], v["amended_share"], v["median_growth_when_amended"],
                                   v["value_after_6_amendments"], oc("early"), oc("late"), oc("escal"),
                                   round(F["vendor"]["observed"], 2),
                                   f"{v['follow_on']['to_incumbent']:.2f}/{v['follow_on']['shuffled_order_benchmark']:.2f}",
                                   v["top4_dollar_share_median"], c["cooperative_or_central"]["share"],
                                   c["authorized_reseller"]["share"], c["multiple_award"]["share"]))))
    for s, v in out["sectors"].items():
        print(s, json.dumps(v["channels"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
