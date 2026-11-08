#!/usr/bin/env python3
"""Descriptive amendment dynamics: first evidence on chance vs. design (game_theory Model 10).

Reads data/processed/contracts_normalized.csv and amendments_normalized.csv and writes
data/processed/amendment_dynamics.json with:

1. continuation: P(at least k+1 amendments | at least k), tech vs. non-tech. A homogeneous
   Poisson count implies this probability FALLS with k; a rise signals heterogeneity across
   contracts (amendment-prone contracts) or state dependence (amendments breed amendments).
2. timing: days from start to first amendment, and its position within the original term.
3. vendor_dispersion: how much vendor-level amendment rates vary beyond binomial chance
   (Pearson chi-square / df; 1 = pure chance).
4. amendment_types: Washington and Chicago amendment text classified into extension,
   funding, scope, and administrative changes.

Descriptive only: none of these separates chance from design on its own (see
game_theory/amendments/05_empirical_tests.md).
"""

from __future__ import annotations

import csv
import json
import math
import re
import statistics
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

PROCESSED = Path("data/processed")
COUNT_LEDGERS = ("chicago", "cook_county", "oregon", "washington_state")
DATED_LEDGERS = ("chicago", "oregon", "cook_county")

TYPE_PATTERNS = [
    ("administrative", re.compile(r"correct|clerical|administrative|name change|assign|novation|address|contact|"
                                  r"signator|typo|error in amendment", re.I)),
    ("scope", re.compile(r"scope|sow|statement of work|add(?:ed|ing)? (?:services|deliverable|task|module|functional)|"
                         r"new (?:requirement|service|task)|change order|enhancement|modif(?:y|ication) of work", re.I)),
    ("extension", re.compile(r"extend|extension|renew|period of performance|term|time only|end date", re.I)),
    ("funding", re.compile(r"fund|increase|add(?:ed|ing)? \$|compensation|budget|cost|price|rate|amount", re.I)),
]


def classify(text: str) -> list[str]:
    hits = [name for name, pat in TYPE_PATTERNS if pat.search(text or "")]
    return hits or ["unclassified"]


def main() -> int:
    contracts = [r for r in csv.DictReader((PROCESSED / "contracts_normalized.csv").open(encoding="utf-8"))
                 if r["amendment_observable"] == "1"]
    out: dict = {}

    # 1. continuation probabilities
    cont = {}
    for label, is_tech in (("tech", "1"), ("non_tech", "0")):
        counts = [int(r["amendment_count"]) for r in contracts
                  if r["is_tech"] == is_tech and r["jurisdiction"] in COUNT_LEDGERS]
        probs = []
        for k in range(10):
            at_least_k = sum(1 for n in counts if n >= k)
            probs.append(round(sum(1 for n in counts if n >= k + 1) / at_least_k, 4) if at_least_k else None)
        mean = statistics.mean(counts)
        var = statistics.pvariance(counts)
        cont[label] = {"contracts": len(counts), "p_next_given_k": probs,
                       "mean_amendments": round(mean, 3), "variance": round(var, 3),
                       "variance_to_mean": round(var / mean, 2) if mean else None}
    # Poisson benchmark with the same mean, for comparison
    def poisson_cont(mu: float) -> list[float]:
        pmf = [math.exp(-mu) * mu ** n / math.factorial(n) for n in range(60)]
        surv = [sum(pmf[n:]) for n in range(60)]
        return [round(surv[k + 1] / surv[k], 4) for k in range(10)]
    for label in cont:
        cont[label]["poisson_benchmark"] = poisson_cont(cont[label]["mean_amendments"])
    out["continuation"] = cont

    # 2. timing of the first amendment
    first: dict[tuple[str, str], date] = {}
    for r in csv.DictReader((PROCESSED / "amendments_normalized.csv").open(encoding="utf-8")):
        if r["jurisdiction"] not in DATED_LEDGERS or not r["amendment_date"]:
            continue
        try:
            d = date.fromisoformat(r["amendment_date"][:10])
        except ValueError:
            continue
        k = (r["jurisdiction"], r["contract_id"])
        if k not in first or d < first[k]:
            first[k] = d
    timing = {}
    for label, is_tech in (("tech", "1"), ("non_tech", "0")):
        days, rel = [], []
        for r in contracts:
            k = (r["jurisdiction"], r["contract_id"])
            if r["is_tech"] != is_tech or k not in first or not r["start_date"]:
                continue
            try:
                g = (first[k] - date.fromisoformat(r["start_date"])).days
            except ValueError:
                continue
            if -30 <= g <= 3650:
                days.append(g)
                if r["duration_days"] and float(r["duration_days"]) > 0:
                    rel.append(g / float(r["duration_days"]))
        days.sort()
        timing[label] = {
            "contracts": len(days),
            "median_days_to_first": statistics.median(days),
            "share_within_180_days": round(sum(1 for x in days if x <= 180) / len(days), 3),
            "median_position_in_original_term": round(statistics.median(rel), 3),
            "share_in_first_quarter_of_term": round(sum(1 for x in rel if x <= 0.25) / len(rel), 3),
            "share_after_90pct_of_term": round(sum(1 for x in rel if x >= 0.9) / len(rel), 3),
        }
    out["timing"] = timing

    # 3. vendor dispersion beyond binomial chance
    disp = {}
    for j in COUNT_LEDGERS:
        byv: dict[str, list[int]] = defaultdict(list)
        for r in contracts:
            if r["jurisdiction"] == j and r["vendor_name"].strip():
                byv[r["vendor_name"].upper().strip()].append(int(r["is_amended"]))
        vs = {v: x for v, x in byv.items() if len(x) >= 20}
        if len(vs) < 10:
            continue
        p = sum(map(sum, vs.values())) / sum(map(len, vs.values()))
        chi = sum((sum(x) - len(x) * p) ** 2 / (len(x) * p * (1 - p)) for x in vs.values())
        rates = sorted(sum(x) / len(x) for x in vs.values())
        q = lambda f: round(rates[int(f * (len(rates) - 1))], 3)
        disp[j] = {"vendors_with_20plus": len(vs), "pooled_rate": round(p, 3),
                   "chi2_over_df": round(chi / (len(vs) - 1), 2),
                   "vendor_rate_p10_p50_p90": [q(.1), q(.5), q(.9)]}
    out["vendor_dispersion"] = disp

    # 4. amendment types from text (Washington modification text; Chicago revision descriptions are PO titles)
    types: dict[str, Counter] = defaultdict(Counter)
    tech_ids = {(r["jurisdiction"], r["contract_id"]): r["is_tech"] for r in contracts}
    for r in csv.DictReader((PROCESSED / "amendments_normalized.csv").open(encoding="utf-8")):
        if r["jurisdiction"] != "washington_state":
            continue
        label = "tech" if tech_ids.get((r["jurisdiction"], r["contract_id"])) == "1" else "non_tech"
        for t in classify(r["category"]):
            types[label][t] += 1
    out["washington_amendment_types"] = {k: dict(v.most_common()) for k, v in types.items()}

    (PROCESSED / "amendment_dynamics.json").write_text(json.dumps(out, indent=1, default=str))
    print(json.dumps(out, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
