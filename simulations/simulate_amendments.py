#!/usr/bin/env python3
"""Simulate the logical implications of chance vs. designed amendments, then ask which
sectors' contract histories carry the design fingerprints.

Theory: game_theory/amendments/04_chance_vs_design.md (Model 10) and Model 1/8 lock-in.
Write-up: game_theory/amendments/07_simulated_implications.md

Part 1 -- theory worlds. Five data-generating processes:
  A  chance, heterogeneous contracts   Poisson arrivals, contract-specific rates (gamma mixing)
  B  design, no lock-in                 A + vendor-level scope gaps surfacing at implementation
  C  design with lock-in spiral          B + each amendment raises dependence k, which raises the
                                         hazard, the size of later amendments, and the chance of
                                         an end-of-term extension instead of re-competition
  D  chance + routine renewals           A + planned end-of-term renewals, independent of history
  E  mixed                               half chance-only contracts, half C
For each, compute the same fingerprints we can compute from the data, and compare each world
with a chance world MATCHED to its own count distribution (negative binomial by moments). That
comparison is what separates "amendment-prone contracts" from "amendments by design".

Part 2 -- sectors. For each sector (tech subsector, tech program domain, non-tech) in the
ledgers with dated amendments and dollar changes (Chicago, Oregon ORPIN, Cook County):
  observed fingerprints vs. their sampling distribution under the sector's matched chance world
  (and, for the vendor fingerprint, a within-cell permutation null). Output: z-scores, the
  number of design predictions each sector satisfies, and which design variant it resembles.

Standard library only. Run from the repository root:

    python3 simulations/simulate_amendments.py              # full run (~15 min)
    python3 simulations/simulate_amendments.py --score-only # re-score saved results, rewrite tables
    python3 simulations/simulate_amendments.py --theory-only # re-simulate theory worlds, keep sector results

Outputs (simulations/results/):
    amendment_fingerprints.json   everything below, plus definitions
    theory_worlds.csv             world x fingerprint: observed, matched-chance mean/sd, z
    sector_fingerprints.csv       sector x fingerprint: observed, matched-chance mean/sd, z
    sector_similarity.csv         sector: cosine similarity to worlds B-E, closest world
    lockin_ranking.csv            sectors ranked by lock-in-specific fingerprints
"""

from __future__ import annotations

import csv
import json
import math
import random
import statistics
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

PROCESSED = Path("data/processed")              # inputs (built by scripts/normalize_and_classify.py)
RESULTS = Path(__file__).resolve().parent / "results"   # outputs, committed with the code
# Ledgers whose amendment rows carry dates and dollar changes (Washington from its labelled FY2023+
# amendment rows; Oregon Lottery from lines added on later dates, no contract term so no timing).
TIMED_LEDGERS = ("chicago", "oregon", "cook_county", "washington_state", "oregon_lottery", "oregon_treasury",
                 "wa_doh")
VENDOR_LEDGERS = TIMED_LEDGERS
BULK_DATE_LEDGERS = ("chicago",)  # Chicago's 2002 system migration stamped thousands of revisions on one date

FINGERPRINTS = {
    # key: (label, design prediction relative to matched chance)
    "early": ("First amendment in first 25% of term", "+ (scope gaps surface at implementation)"),
    "late": ("Any amendment in last 10% of term or after", "+ (extensions instead of re-competition)"),
    "accel": ("P(next gap between amendments is shorter)", "+ (lock-in raises the hazard)"),
    "accel_pre": ("Same, using only amendments before the last 10% of term", "+ (robustness for accel)"),
    "escal": ("P(second amendment larger than first)", "+ (lock-in raises the margin)"),
    "lift": ("Late-extension lift after earlier amendments", "+ (renewal odds rise with dependence)"),
    "vendor": ("Vendor share of variance in amendment risk", "+ (gap strategy is vendor-level)"),
    "cont": ("Rise in P(another amendment) from k=0 to k=3", "none: heterogeneity alone produces it"),
}


# --------------------------------------------------------------------------------------
# Random helpers
# --------------------------------------------------------------------------------------

def poisson(rng: random.Random, mu: float) -> int:
    if mu <= 0:
        return 0
    if mu > 30:
        return max(0, int(round(rng.gauss(mu, math.sqrt(mu)))))
    L, k, p = math.exp(-mu), 0, 1.0
    while True:
        p *= rng.random()
        if p <= L:
            return k
        k += 1


def nb_params(counts: list[int]) -> tuple[float, float]:
    """Negative binomial (gamma-Poisson) shape and mean, by moments."""
    m = statistics.mean(counts)
    v = statistics.pvariance(counts)
    shape = m * m / (v - m) if v > m else 1e6
    return max(shape, 0.02), m


# --------------------------------------------------------------------------------------
# Fingerprints (shared by simulated and real data)
#   contract = {"vendor": str, "cell": str, "n": int, "times": [sorted positions in term units],
#               "sizes": [positive amendment sizes in time order]}
# --------------------------------------------------------------------------------------

def icc(groups: dict[str, dict[str, list[int]]]) -> float | None:
    """Pooled method-of-moments vendor variance share of a binary outcome, within cells."""
    num = den = 0.0
    for vendors in groups.values():
        vs = {v: x for v, x in vendors.items() if len(x) >= 2}
        if len(vs) < 2:
            continue
        N = sum(len(x) for x in vs.values())
        p = sum(sum(x) for x in vs.values()) / N
        if p <= 0 or p >= 1:
            continue
        between = sum(len(x) * (sum(x) / len(x) - p) ** 2 for x in vs.values())
        n0 = (N - sum(len(x) ** 2 for x in vs.values()) / N) / (len(vs) - 1)
        msb = between / (len(vs) - 1)
        msw = sum(sum(x) - len(x) * (sum(x) / len(x)) ** 2 for x in vs.values()) / (N - len(vs))
        s2b = max(0.0, (msb - msw) / n0)
        num += s2b * N
        den += (s2b + msw) * N
    return num / den if den else None


def fingerprints(contracts: list[dict]) -> dict:
    amended = [c for c in contracts if c["times"]]
    out: dict = {"contracts": len(contracts), "amended_with_dates": len(amended)}
    if amended:
        out["early"] = sum(1 for c in amended if c["times"][0] <= 0.25) / len(amended)
        out["late"] = sum(1 for c in amended if any(t >= 0.9 for t in c["times"])) / len(amended)
    # acceleration: compare consecutive gaps between amendments (ties dropped)
    a = b = 0
    for c in contracts:
        t = c["times"]
        if len(t) >= 3:
            g1, g2 = t[1] - t[0], t[2] - t[1]
            if g1 > 0 and g2 > 0 and g1 != g2:
                a += g2 < g1
                b += 1
    out["accel"], out["accel_n"] = (a / b if b else None), b
    # robustness: acceleration using only amendments before the last 10% of the term, so
    # end-of-term clustering (renewals, fiscal-year paperwork) cannot drive it
    a = b = 0
    for c in contracts:
        t = [x for x in c["times"] if x < 0.9]
        if len(t) >= 3:
            g1, g2 = t[1] - t[0], t[2] - t[1]
            if g1 > 0 and g2 > 0 and g1 != g2:
                a += g2 < g1
                b += 1
    out["accel_pre"], out["accel_pre_n"] = (a / b if b else None), b
    # escalation: second positive amendment larger than the first
    a = b = 0
    for c in contracts:
        s = c["sizes"]
        if len(s) >= 2 and s[0] != s[1]:
            a += s[1] > s[0]
            b += 1
    out["escal"], out["escal_n"] = (a / b if b else None), b
    # late-extension lift: P(late | amended before 0.9) / P(late | not amended before 0.9)
    pre = [c for c in contracts if any(t < 0.9 for t in c["times"])]
    nopre = [c for c in contracts if not any(t < 0.9 for t in c["times"])]
    if pre and nopre:
        p1 = sum(1 for c in pre if any(t >= 0.9 for t in c["times"])) / len(pre)
        p0 = sum(1 for c in nopre if any(t >= 0.9 for t in c["times"])) / len(nopre)
        out["lift"] = p1 / p0 if p0 > 0 else None
    # continuation rise
    ns = [c["n"] for c in contracts]
    def cont(k):
        at = sum(1 for n in ns if n >= k)
        return sum(1 for n in ns if n >= k + 1) / at if at else None
    c0, c3 = cont(0), cont(3)
    out["cont"] = (c3 - c0) if (c0 is not None and c3 is not None) else None
    # vendor variance share within cells
    groups: dict[str, dict[str, list[int]]] = defaultdict(lambda: defaultdict(list))
    for c in contracts:
        if c["vendor"]:
            groups[c["cell"]][c["vendor"]].append(1 if c["n"] > 0 else 0)
    out["vendor"] = icc(groups)
    return out


# --------------------------------------------------------------------------------------
# Part 1: theory worlds
# --------------------------------------------------------------------------------------

def world(kind: str, rng: random.Random, n_vendors: int = 300, steps: int = 200) -> list[dict]:
    lam_bar, shape = 0.8, 0.6              # chance arrivals per term, heterogeneity (gamma shape)
    gap_bar = 0.9                           # mean designed (gap) amendments per contract
    rho, eta, psi = 0.35, 1.0, 0.45         # lock-in: hazard elasticity, dependence per amendment, size escalation
    ext0, ext1 = -2.2, 0.55                 # end-of-term extension logit: base, slope in dependence
    k_cap = 4.0                             # dependence saturates: its effect stops growing after ~4 amendments
    routine_renewal = 0.25                  # world D: planned renewal probability, history-independent
    out = []
    for v in range(n_vendors):
        design_v = rng.gammavariate(0.7, 1 / 0.7)  # vendor's gap strategy (mean 1)
        for _ in range(max(1, int(rng.lognormvariate(2.2, 0.8)))):
            lam = rng.gammavariate(shape, lam_bar / shape)
            mixed_design = kind == "E" and rng.random() < 0.5
            design = kind in ("B", "C") or mixed_design
            spiral = kind == "C" or mixed_design
            gaps = poisson(rng, gap_bar * design_v) if design else 0
            times, sizes, k = [], [], 0.0
            if not spiral:
                times = [rng.random() for _ in range(poisson(rng, lam))]
                times += [rng.betavariate(1.2, 6) for _ in range(gaps)]
                times.sort()
                sizes = [rng.lognormvariate(-2.5, 1.0) for _ in times]
            else:
                # time-stepped hazard: chance rate + gap discovery density, scaled by exp(rho*k)
                dt = 1 / steps
                for s in range(steps):
                    t = (s + 0.5) * dt
                    gap_density = gaps * (1.2 * 6 * t ** 0.2 * (1 - t) ** 5) / 1.08  # ~Beta(1.2,6) pdf
                    if rng.random() < (lam + gap_density) * math.exp(rho * min(k, k_cap)) * dt:
                        times.append(t)
                        sizes.append(rng.lognormvariate(-2.5, 1.0) * (1 + psi * min(k, k_cap)))
                        k += eta
                # end of term: extend instead of re-competing, more likely with dependence
                if rng.random() < 1 / (1 + math.exp(-(ext0 + ext1 * min(k, k_cap)))):
                    times.append(rng.uniform(0.9, 1.05))
                    sizes.append(rng.lognormvariate(-2.5, 1.0) * (1 + psi * min(k, k_cap)))
            if kind == "D" and rng.random() < routine_renewal:
                times.append(rng.uniform(0.9, 1.05))
                sizes.append(rng.lognormvariate(-2.5, 1.0))
                order = sorted(range(len(times)), key=lambda i: times[i])
                times, sizes = [times[i] for i in order], [sizes[i] for i in order]
            out.append({"vendor": f"v{v}", "cell": "all", "n": len(times), "times": times, "sizes": sizes})
    return out


def matched_chance(contracts: list[dict], rng: random.Random, reps: int) -> dict[str, list[float]]:
    """Sampling distribution of fingerprints under a chance world matched to the count distribution."""
    shape, mean = nb_params([c["n"] for c in contracts])
    # keep the share of amendments that carry dates/sizes, as in the data
    n_tot = sum(c["n"] for c in contracts)
    date_share = sum(len(c["times"]) for c in contracts) / n_tot if n_tot else 1
    size_share = sum(len(c["sizes"]) for c in contracts) / n_tot if n_tot else 1
    draws: dict[str, list[float]] = defaultdict(list)
    for _ in range(reps):
        sim = []
        for c in contracts:
            n = poisson(rng, rng.gammavariate(shape, mean / shape))
            times = sorted(rng.random() for _ in range(n) if rng.random() < date_share)
            sizes = [rng.lognormvariate(0, 1) for _ in range(n) if rng.random() < size_share]
            sim.append({"vendor": c["vendor"], "cell": c["cell"], "n": n, "times": times, "sizes": sizes})
        fp = fingerprints(sim)
        for k in ("early", "late", "accel", "accel_pre", "escal", "lift", "cont"):
            if fp.get(k) is not None:
                draws[k].append(fp[k])
    return draws


def vendor_null(contracts: list[dict], rng: random.Random, reps: int) -> list[float]:
    """Permutation null for the vendor share: shuffle amended status within cell."""
    by_cell: dict[str, list[int]] = defaultdict(list)
    for i, c in enumerate(contracts):
        by_cell[c["cell"]].append(i)
    vals = []
    for _ in range(reps):
        groups: dict[str, dict[str, list[int]]] = defaultdict(lambda: defaultdict(list))
        for cell, idx in by_cell.items():
            ys = [1 if contracts[i]["n"] > 0 else 0 for i in idx]
            rng.shuffle(ys)
            for i, y in zip(idx, ys):
                if contracts[i]["vendor"]:
                    groups[cell][contracts[i]["vendor"]].append(y)
        v = icc(groups)
        if v is not None:
            vals.append(v)
    return vals


def compare(obs: dict, draws: dict[str, list[float]], vnull: list[float]) -> dict:
    z = {}
    for k in ("early", "late", "accel", "accel_pre", "escal", "lift", "cont"):
        d = draws.get(k, [])
        if obs.get(k) is None or len(d) < 5:
            continue
        mu, sd = statistics.mean(d), statistics.pstdev(d)
        z[k] = {"observed": round(obs[k], 4), "chance_mean": round(mu, 4), "chance_sd": round(sd, 4),
                "z": round((obs[k] - mu) / sd, 2) if sd > 0 else None}
    if obs.get("vendor") is not None and len(vnull) >= 5:
        mu, sd = statistics.mean(vnull), statistics.pstdev(vnull)
        z["vendor"] = {"observed": round(obs["vendor"], 4), "chance_mean": round(mu, 4), "chance_sd": round(sd, 4),
                       "z": round((obs["vendor"] - mu) / sd, 2) if sd > 0 else None}
    return z


def theory_part(rng: random.Random) -> dict:
    res = {}
    labels = {"A": "Chance, heterogeneous contracts", "B": "Design, no lock-in",
              "C": "Design with lock-in spiral", "D": "Chance + routine renewals", "E": "Mixed: half chance, half C"}
    for kind, label in labels.items():
        contracts = world(kind, rng)
        obs = fingerprints(contracts)
        z = compare(obs, matched_chance(contracts, rng, 40), vendor_null(contracts, rng, 40))
        res[kind] = {"label": label, "contracts": len(contracts), "fingerprints_vs_matched_chance": z}
        print(f"[theory {kind}] {label}: " + ", ".join(f"{k} z={v['z']}" for k, v in z.items()))
    return res


# --------------------------------------------------------------------------------------
# Part 2: sectors in the data
# --------------------------------------------------------------------------------------

def load_sector_contracts() -> dict[str, list[dict]]:
    contracts = {}
    for r in csv.DictReader((PROCESSED / "contracts_normalized.csv").open(encoding="utf-8")):
        if r["amendment_observable"] != "1" or r["jurisdiction"] not in VENDOR_LEDGERS:
            continue
        contracts[(r["jurisdiction"], r["contract_id"])] = r
    amends = defaultdict(list)
    date_counts: Counter = Counter()
    rows = list(csv.DictReader((PROCESSED / "amendments_normalized.csv").open(encoding="utf-8")))
    for r in rows:
        if r["jurisdiction"] in TIMED_LEDGERS and r["amendment_date"]:
            date_counts[(r["jurisdiction"], r["amendment_date"])] += 1
    for r in rows:
        k = (r["jurisdiction"], r["contract_id"])
        if k in contracts:
            amends[k].append(r)

    def num(s):
        try:
            return float(s)
        except (TypeError, ValueError):
            return 0.0

    groups: dict[str, list[dict]] = defaultdict(list)
    for k, c in contracts.items():
        j = k[0]
        times, sizes = [], []
        if j in TIMED_LEDGERS:
            seq = []
            for r in amends.get(k, []):
                if not r["amendment_date"]:
                    continue
                if j in BULK_DATE_LEDGERS and date_counts[(j, r["amendment_date"])] > 200:
                    continue  # bulk-loaded migration dates carry no timing information
                seq.append((r["amendment_date"][:10], num(r["delta_amount"])))
            seq.sort()
            sizes = [d for _, d in seq if d > 0]  # escalation needs order, not a contract term
            if c["start_date"] and c["duration_days"] and float(c["duration_days"]) >= 30:
                start, dur = date.fromisoformat(c["start_date"]), float(c["duration_days"])
                for d, _ in seq:
                    try:
                        pos = (date.fromisoformat(d) - start).days / dur
                    except ValueError:
                        continue
                    if -0.05 <= pos <= 3:
                        times.append(max(0.0, pos))
                times.sort()
        n = int(c["amendment_count"] or 0)
        rec = {"vendor": c["vendor_name"].upper().strip(), "cell": f"{j}|{c['department'].upper()[:40]}",
               "n": n, "times": times if j in TIMED_LEDGERS else [], "sizes": sizes, "timed": j in TIMED_LEDGERS,
               # extra fields used by synthesis/ (not by the fingerprints)
               "jurisdiction": j, "start_date": c["start_date"], "end_date": c["end_date"],
               "duration_days": c["duration_days"], "is_tech": c["is_tech"], "tech_domain": c["tech_domain"],
               "channel": c["procurement_channel"], "vendor_role": c["vendor_role"],
               "gsa_mas_holder": c.get("gsa_mas_holder", "0"), "award_structure": c["award_structure"],
               "contract_id": c["contract_id"]}
        if c["is_tech"] == "1":
            groups[f"subsector:{c['tech_subsector']}"].append(rec)
            groups[f"domain:{c['tech_domain']}"].append(rec)
            groups["all_tech"].append(rec)
        else:
            groups["non_tech"].append(rec)
    return groups


def sector_part(rng: random.Random) -> dict:
    groups = load_sector_contracts()
    reasons = {}
    rp = PROCESSED / "amendment_reasons_summary.json"
    if rp.exists():
        rs = json.loads(rp.read_text())
        reasons = {**{f"subsector:{k}": v for k, v in rs["by_sector"].items()},
                   **{f"domain:{k}": v for k, v in rs["by_domain"].items()}}
        if "non_tech" in rs["by_sector"]:
            reasons["non_tech"] = rs["by_sector"]["non_tech"]
    out = {}
    for name, cs in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        timed = [c for c in cs if c["timed"]]
        if len(timed) < 300:
            continue
        reps = max(20, min(120, int(3_000_000 / max(1, len(timed)))))
        obs = fingerprints(timed)
        obs["vendor"] = fingerprints(cs)["vendor"]  # vendor share uses all four ledgers
        z = compare(obs, matched_chance(timed, rng, reps), vendor_null(cs, rng, max(20, reps // 2)))
        design_keys = ("early", "late", "accel", "escal", "lift", "vendor")
        hits = [k for k in design_keys if k in z and z[k]["z"] is not None and z[k]["z"] >= 2]
        against = [k for k in design_keys if k in z and z[k]["z"] is not None and z[k]["z"] <= -2]
        gap_score = statistics.mean([z[k]["z"] for k in ("early", "vendor") if k in z and z[k]["z"] is not None] or [0])
        spiral_score = statistics.mean([z[k]["z"] for k in ("accel", "escal", "lift") if k in z and z[k]["z"] is not None] or [0])
        r = reasons.get(name, {})
        out[name] = {
            "contracts": len(cs), "timed_contracts": len(timed),
            "eligible": {"accel_pairs": obs.get("accel_n"), "accel_pre_pairs": obs.get("accel_pre_n"),
                         "escal_pairs": obs.get("escal_n")},
            "fingerprints": z,
            "design_predictions_met": hits, "design_predictions_contradicted": against,
            "gap_score": round(gap_score, 2), "spiral_score": round(spiral_score, 2),
            "stated_reasons": {k: r.get(k) for k in ("informative", "causal_reasons", "design_share_of_causal",
                                                    "chance_share_of_informative", "design_share_of_informative")} if r else None,
        }
        print(f"[sector] {name:40s} n={len(cs):>7,} met={hits} against={against} "
              f"gap={gap_score:.1f} spiral={spiral_score:.1f}")
    return out


SIM_KEYS = ("early", "late", "accel_pre", "escal", "lift", "cont", "vendor")
# Scale for averaging lock-in effects: deviation of a probability from 0.5 (max 0.5), and a
# vendor variance share (observed values run to ~0.4).
LOCKIN_SCALE = {"accel_pre": 0.5, "escal": 0.5, "vendor": 0.5}
LOCKIN_CORE = ("escal", "vendor")


def score_similarity(result: dict) -> None:
    """Compare each sector's deviation pattern with each theory world's pattern.

    Uses z-scores against each one's own matched chance world, clipped to [-10, 10] so that
    very large samples do not let one fingerprint dominate, and cosine similarity (direction
    only, since z grows with sample size). Also reports sign agreement on fingerprints where
    both are |z| >= 2.
    """
    def vec(fp: dict) -> list[float]:
        return [max(-10.0, min(10.0, (fp.get(k) or {}).get("z") or 0.0)) for k in SIM_KEYS]

    def cos(a, b):
        na, nb = math.sqrt(sum(x * x for x in a)), math.sqrt(sum(x * x for x in b))
        return sum(x * y for x, y in zip(a, b)) / (na * nb) if na and nb else 0.0

    worlds = {k: vec(v["fingerprints_vs_matched_chance"]) for k, v in result["theory_worlds"].items() if k != "A"}
    for name, sec in result["sectors"].items():
        sv = vec(sec["fingerprints"])
        sims = {w: round(cos(sv, wv), 3) for w, wv in worlds.items()}
        agree = {}
        for w, wv in worlds.items():
            both = [(a, b) for a, b in zip(sv, wv) if abs(a) >= 2 and abs(b) >= 2]
            agree[w] = f"{sum(1 for a, b in both if (a > 0) == (b > 0))}/{len(both)}"
        n_dev = sum(1 for x in sv if abs(x) >= 2)
        best = max(sims, key=sims.get)
        sec["similarity_to_worlds"] = sims
        sec["sign_agreement"] = agree
        sec["fingerprints_deviating_from_chance"] = n_dev
        sec["closest_world"] = best if n_dev >= 2 and sims[best] > 0.3 else "A (indistinguishable from chance)"
        # Lock-in-specific fingerprints: what the lock-in world (C) produces robustly and routine
        # renewals (D) cannot: escalating amendment sizes and a vendor-level component. Acceleration
        # is reported as supporting evidence only: in simulation it appears only when dependence
        # grows without limit. Effect sizes, not z, so sectors of different size compare.
        fp = sec["fingerprints"]
        eff = {}
        for k in ("escal", "vendor", "accel_pre"):
            if k in fp and fp[k]["z"] is not None:
                eff[k] = {"effect": round(fp[k]["observed"] - fp[k]["chance_mean"], 4), "z": fp[k]["z"],
                          "significant": abs(fp[k]["z"]) >= 2}
        met = [k for k in LOCKIN_CORE if k in eff and eff[k]["significant"] and eff[k]["effect"] > 0]
        sec["lockin_specific"] = eff
        sec["lockin_fingerprints_met"] = met
        sec["lockin_supporting_accel"] = bool(eff.get("accel_pre", {}).get("significant")
                                             and eff["accel_pre"]["effect"] > 0)
        # Evidence tiers. Vendor concentration separates DESIGN (worlds B and C) from chance and
        # routine renewals (A, D); escalation separates LOCK-IN (C) specifically.
        design = "vendor" in met
        lockin = "escal" in met
        # Tiers use only the robust fingerprints; acceleration (fragile in simulation) is a flag.
        sec["evidence_tier"] = 1 if (design and lockin) else 2 if design else 3
        sec["evidence_tier_label"] = {1: "design + lock-in", 2: "design (vendor-level) only",
                                      3: "not distinguishable from chance/renewals"}[sec["evidence_tier"]]
        sec["thin"] = (sec["eligible"].get("accel_pre_pairs") or 0) < 30 or (sec["eligible"].get("escal_pairs") or 0) < 30
        sec["lockin_index"] = eff.get("escal", {}).get("effect", 0.0)  # escalation effect orders within tier
        print(f"[similarity] {name:40s} dev={n_dev} " + " ".join(f"{w}={v:+.2f}" for w, v in sims.items())
              + f"  -> {sec['closest_world']}  lock-in met={met} index={sec['lockin_index']}")
    ranked = sorted(result["sectors"].items(),
                    key=lambda kv: (kv[1]["thin"], kv[1]["evidence_tier"], -kv[1]["lockin_index"],
                                    -kv[1]["lockin_specific"].get("vendor", {}).get("effect", 0)))
    result["lockin_ranking"] = [{"sector": n, "fingerprints_met": s["lockin_fingerprints_met"],
                                 "supporting_acceleration": s["lockin_supporting_accel"],
                                 "evidence_tier": s["evidence_tier"], "evidence_tier_label": s["evidence_tier_label"],
                                 "thin": s["thin"], "lockin_index": s["lockin_index"]} for n, s in ranked]


def write_tables(result: dict) -> None:
    keys = ("early", "late", "lift", "accel", "accel_pre", "escal", "cont", "vendor")

    def rows_for(name, fp, extra):
        for k in keys:
            if k in fp:
                yield {**extra, "fingerprint": k, "label": FINGERPRINTS[k][0], **fp[k]}

    with (RESULTS / "theory_worlds.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["world", "world_label", "fingerprint", "label", "observed",
                                          "chance_mean", "chance_sd", "z"])
        w.writeheader()
        for k, v in result["theory_worlds"].items():
            w.writerows(rows_for(k, v["fingerprints_vs_matched_chance"], {"world": k, "world_label": v["label"]}))
    with (RESULTS / "sector_fingerprints.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["sector", "contracts", "timed_contracts", "fingerprint", "label",
                                          "observed", "chance_mean", "chance_sd", "z"])
        w.writeheader()
        for k, v in result["sectors"].items():
            w.writerows(rows_for(k, v["fingerprints"], {"sector": k, "contracts": v["contracts"],
                                                         "timed_contracts": v["timed_contracts"]}))
    with (RESULTS / "sector_similarity.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["sector", "contracts", "cos_B_gaps", "cos_C_spiral", "cos_D_renewals",
                                          "cos_E_mixed", "fingerprints_deviating_from_chance", "closest_world"])
        w.writeheader()
        for k, v in result["sectors"].items():
            sim = v.get("similarity_to_worlds", {})
            w.writerow({"sector": k, "contracts": v["contracts"], "cos_B_gaps": sim.get("B"),
                        "cos_C_spiral": sim.get("C"), "cos_D_renewals": sim.get("D"), "cos_E_mixed": sim.get("E"),
                        "fingerprints_deviating_from_chance": v.get("fingerprints_deviating_from_chance"),
                        "closest_world": v.get("closest_world")})
    with (RESULTS / "lockin_ranking.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["rank", "sector", "contracts", "evidence_tier", "evidence_tier_label", "thin",
                                          "fingerprints_met", "supporting_acceleration", "lockin_index",
                                          "accel_pre_effect", "escal_effect", "vendor_effect", "accel_pre_pairs"])
        w.writeheader()
        for i, r in enumerate(result.get("lockin_ranking", []), 1):
            sec = result["sectors"][r["sector"]]
            eff = sec.get("lockin_specific", {})
            w.writerow({"rank": i, "sector": r["sector"], "contracts": sec["contracts"],
                        "evidence_tier": r["evidence_tier"], "evidence_tier_label": r["evidence_tier_label"],
                        "thin": r["thin"],
                        "fingerprints_met": ";".join(r["fingerprints_met"]),
                        "supporting_acceleration": r.get("supporting_acceleration"), "lockin_index": r["lockin_index"],
                        "accel_pre_effect": (eff.get("accel_pre") or {}).get("effect"),
                        "escal_effect": (eff.get("escal") or {}).get("effect"),
                        "vendor_effect": (eff.get("vendor") or {}).get("effect"),
                        "accel_pre_pairs": sec["eligible"].get("accel_pre_pairs")})


def main() -> int:
    import sys
    RESULTS.mkdir(parents=True, exist_ok=True)
    out = RESULTS / "amendment_fingerprints.json"
    if "--score-only" in sys.argv and out.exists():
        result = json.loads(out.read_text())
    elif "--theory-only" in sys.argv and out.exists():
        # re-simulate the theory worlds only; keep the (slow) sector results
        result = json.loads(out.read_text())
        result["theory_worlds"] = theory_part(random.Random(20261108))
    else:
        rng = random.Random(20261108)
        result = {"fingerprint_definitions": {k: {"label": v[0], "design_prediction": v[1]}
                                              for k, v in FINGERPRINTS.items()},
                  "theory_worlds": theory_part(rng), "sectors": sector_part(rng)}
    score_similarity(result)
    out.write_text(json.dumps(result, indent=1))
    write_tables(result)
    print(f"Wrote {out} and CSV tables in {RESULTS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
