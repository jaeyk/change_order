#!/usr/bin/env python3
"""R15: within-ledger (stratified) sector contrasts with bootstrap confidence intervals.

The pooled sector comparisons in strategies.md mix ledgers that differ a lot (Washington's
labelled amendments escalate and grow more, and come earlier, in every sector), and the sectors
are spread unevenly across ledgers (most software contracts are Washington's). This check
compares sectors only within a ledger and then averages the within-ledger gaps, weighting each
ledger by the smaller of the two groups' sample sizes.

Quantities (sector minus non-technology, within ledger):
  escal   P(2nd positive amendment > 1st)                       weight: escalation pairs
  late    share of dated, amended contracts with an amendment in the last 10% of term
  early   share whose first amendment is in the first 25% of term
  vendor  vendor share of variance in amendment risk (cells = ledger x department)
  snow6   log value multiple after 6 amendments (geometric-mean ratio)

95% intervals: 300 bootstrap draws, resampling contracts within ledger and sector.
Writes robustness/results/stratified.json.
"""

from __future__ import annotations

import json
import math
import random
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import run_checks as rc  # noqa: E402

REPS = 300
MIN = {"escal": 20, "late": 30, "early": 30, "vendor": 100, "snow6": 10}


def stat(kind: str, cs: list[dict], amends: dict) -> tuple[float | None, int]:
    if kind == "escal":
        pairs = [c["sizes"][1] > c["sizes"][0] for c in cs if len(c["sizes"]) >= 2 and c["sizes"][0] != c["sizes"][1]]
        return (sum(pairs) / len(pairs) if pairs else None), len(pairs)
    if kind in ("late", "early"):
        am = [c for c in cs if c["times"]]
        if not am:
            return None, 0
        hit = (lambda c: any(t >= 0.9 for t in c["times"])) if kind == "late" else (lambda c: c["times"][0] <= 0.25)
        return sum(map(hit, am)) / len(am), len(am)
    if kind == "vendor":
        v = rc.sim.fingerprints(cs)["vendor"]
        return v, len(cs)
    if kind == "snow6":
        vals = []
        for c in cs:
            if c["initial"] < 1000:
                continue
            seq = sorted(amends.get((c["jurisdiction"], c["contract_id"]), []),
                         key=lambda a: (a["amendment_date"] or "9999", a["amendment_seq"]))
            if len(seq) <= 6:
                continue
            v = c["initial"] + sum(float(a["delta_amount"] or 0) for a in seq[:6])
            vals.append(math.log(max(v, 0.01 * c["initial"]) / c["initial"]))
        return (statistics.mean(vals) if vals else None), len(vals)
    raise ValueError(kind)


def pooled_gap(kind: str, by_ledger: dict, sector: str, amends: dict) -> tuple[float | None, list[dict]]:
    parts = []
    for j, g in by_ledger.items():
        a, na = stat(kind, g.get(sector, []), amends)
        b, nb = stat(kind, g.get("non_tech", []), amends)
        if a is None or b is None or min(na, nb) < MIN[kind]:
            continue
        parts.append({"ledger": j, "sector": round(a, 4), "non_tech": round(b, 4), "gap": round(a - b, 4),
                      "n_sector": na, "n_non_tech": nb, "weight": min(na, nb)})
    if not parts:
        return None, parts
    w = sum(p["weight"] for p in parts)
    return sum(p["gap"] * p["weight"] for p in parts) / w, parts


def main() -> int:
    contracts, amends, recs = rc.load()
    by_ledger: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    for c in recs:
        by_ledger[c["jurisdiction"]][c["sub"]].append(c)
    rng = random.Random(rc.SEED)
    out = {}
    for kind in ("escal", "late", "early", "vendor", "snow6"):
        out[kind] = {}
        for s in ("software_saas", "hardware_telecom", "it_services", "tech_general"):
            est, parts = pooled_gap(kind, by_ledger, s, amends)
            if est is None:
                out[kind][s] = {"estimate": None, "ledgers": parts}
                continue
            if kind == "vendor":
                # resampling contracts duplicates them inside vendors and inflates the vendor share,
                # so a contract-level bootstrap is invalid here; report the point estimate only
                out[kind][s] = {"estimate": round(est, 4), "ci95": None, "ledgers": parts}
                print(f"{kind:7s} {s:17s} within-ledger gap vs non-tech {est:+.3f} (no CI)  "
                      + ", ".join(f"{p['ledger']}:{p['gap']:+.3f}(n={p['n_sector']})" for p in parts))
                continue
            reps = REPS
            draws = []
            used = {p["ledger"] for p in parts}
            for _ in range(reps):
                boot = {j: {k: [rng.choice(v) for _ in v] for k, v in by_ledger[j].items() if k in (s, "non_tech")}
                        for j in used}
                e, _ = pooled_gap(kind, boot, s, amends)
                if e is not None:
                    draws.append(e)
            draws.sort()
            lo, hi = draws[int(0.025 * len(draws))], draws[int(0.975 * len(draws)) - 1]
            out[kind][s] = {"estimate": round(est, 4), "ci95": [round(lo, 4), round(hi, 4)], "ledgers": parts}
            print(f"{kind:7s} {s:17s} within-ledger gap vs non-tech {est:+.3f} [{lo:+.3f}, {hi:+.3f}]  "
                  + ", ".join(f"{p['ledger']}:{p['gap']:+.3f}(n={p['n_sector']})" for p in parts))
    (rc.OUT / "stratified.json").write_text(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
