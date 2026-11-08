#!/usr/bin/env python3
"""Robustness checks for the vendor-strategy findings (strategies.md).

Each check re-estimates the headline quantities under one change of sample, definition or
method, and records whether each headline claim survives. Claims:

  C1  Software & SaaS has the largest escalation excess (P(2nd amendment > 1st) - 0.5).
  C2  Software & SaaS has the largest vendor share of amendment risk.
  C3  IT services is the only subsector whose first amendments come early more often than chance.
  C4  Every subsector amends late (last 10% of term or after) far more often than chance.
  C5  Software & SaaS contracts compound the most (value after K amendments, same cohort).
  C6  No sector re-awards to its previous vendor more often than chance.
  C7  Resellers are amended less often than other vendors in hardware & telecom.
  C8  Holdovers ('extended until a new contract is awarded') are more common in software and
      general-technology documents than in non-technology documents.

Writes robustness/results/checks.json and prints a summary. Standard library only; reuses the
simulation's fingerprint code so definitions match simulations/.
"""

from __future__ import annotations

import csv
import json
import math
import random
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "simulations"))
sys.path.insert(0, str(ROOT / "scripts"))
import simulate_amendments as sim  # noqa: E402

PROCESSED = ROOT / "data/processed"
OUT = ROOT / "robustness/results"
SUBS = ["software_saas", "hardware_telecom", "it_services", "tech_general", "non_tech"]
SEED = 20261108


# ----------------------------------------------------------------------------------------------
# data
# ----------------------------------------------------------------------------------------------

def load() -> tuple[dict, dict, list[dict]]:
    """Contracts (all ledgers), amendments by contract, and the simulation's records."""
    contracts = {(r["jurisdiction"], r["contract_id"]): r
                 for r in csv.DictReader((PROCESSED / "contracts_normalized.csv").open(encoding="utf-8"))}
    amends = defaultdict(list)
    for r in csv.DictReader((PROCESSED / "amendments_normalized.csv").open(encoding="utf-8")):
        amends[(r["jurisdiction"], r["contract_id"])].append(r)
    groups = sim.load_sector_contracts()
    recs = {}
    for name, cs in groups.items():
        for c in cs:
            recs[(c["jurisdiction"], c["contract_id"])] = c
    for k, c in recs.items():
        row = contracts[k]
        c["sub"] = row["tech_subsector"] if row["is_tech"] == "1" else "non_tech"
        c["initial"] = float(row["initial_award_val"] or 0)
        c["final"] = float(row["final_award_val"] or 0)
        c["start_year"] = int(row["start_date"][:4]) if row["start_date"][:4].isdigit() else None
        c["title"] = row["title_desc"]
        c["role"] = row["vendor_role"]
    return contracts, amends, list(recs.values())


def by_sub(recs: list[dict]) -> dict[str, list[dict]]:
    g = defaultdict(list)
    for c in recs:
        g[c["sub"]].append(c)
    return g


# ----------------------------------------------------------------------------------------------
# metrics
# ----------------------------------------------------------------------------------------------

def metrics(recs: list[dict], rng: random.Random, reps: int = 20, with_chance: bool = True) -> dict:
    """Headline quantities for each subsector in a set of contract records."""
    out = {}
    for s, cs in by_sub(recs).items():
        timed = [c for c in cs if c["timed"]]
        fp = sim.fingerprints(timed) if timed else {}
        m = {"contracts": len(cs), "timed": len(timed),
             "escal_excess": None if fp.get("escal") is None else round(fp["escal"] - 0.5, 4),
             "escal_n": fp.get("escal_n"), "vendor": sim.fingerprints(cs)["vendor"]}
        if m["vendor"] is not None:
            m["vendor"] = round(m["vendor"], 4)
        if with_chance and len(timed) >= 300 and fp.get("early") is not None:
            draws = sim.matched_chance(timed, rng, reps)
            for k in ("early", "late"):
                d = draws.get(k, [])
                if d:
                    mu, sd = statistics.mean(d), statistics.pstdev(d)
                    m[k] = {"observed": round(fp[k], 4), "chance": round(mu, 4),
                            "z": round((fp[k] - mu) / sd, 2) if sd > 0 else None}
        out[s] = m
    return out


def claims(m: dict) -> dict[str, bool | None]:
    """Evaluate C1-C4 on a metrics dict (subsectors with < 50 escalation pairs are not ranked)."""
    esc = {s: v["escal_excess"] for s, v in m.items() if v.get("escal_excess") is not None and (v.get("escal_n") or 0) >= 50}
    ven = {s: v["vendor"] for s, v in m.items() if v.get("vendor") is not None and v["contracts"] >= 300}
    res: dict[str, bool | None] = {}
    res["C1"] = (max(esc, key=esc.get) == "software_saas") if "software_saas" in esc and len(esc) >= 3 else None
    res["C2"] = (max(ven, key=ven.get) == "software_saas") if "software_saas" in ven and len(ven) >= 3 else None
    early = {s: v["early"] for s, v in m.items() if isinstance(v.get("early"), dict) and v["early"]["z"] is not None}
    if "it_services" in early and len(early) >= 3:
        res["C3"] = early["it_services"]["z"] >= 2 and all(e["z"] < 2 for s, e in early.items() if s != "it_services")
    else:
        res["C3"] = None
    late = {s: v["late"] for s, v in m.items() if isinstance(v.get("late"), dict) and v["late"]["z"] is not None}
    res["C4"] = all(l["z"] >= 2 and l["observed"] >= 1.5 * l["chance"] for l in late.values()) if len(late) >= 3 else None
    return res


def gmean(xs: list[float]) -> float:
    return math.exp(sum(math.log(x) for x in xs) / len(xs))


def snowball(recs: list[dict], amends: dict, K: int = 6, stat: str = "gmean") -> dict[str, tuple[float, int]]:
    """Value after K amendments (multiple of original) for contracts amended > K times (delta ledgers)."""
    import make_figures as mf  # noqa: E402
    out = {}
    g = by_sub(recs)
    for s, cs in g.items():
        vals = []
        for c in cs:
            if c["jurisdiction"] not in mf.DELTA_LEDGERS or c["initial"] < 1000:
                continue
            seq = sorted(amends.get((c["jurisdiction"], c["contract_id"]), []),
                         key=lambda a: (a["amendment_date"] or "9999", a["amendment_seq"]))
            if len(seq) <= K:
                continue
            v = c["initial"]
            for a in seq[:K]:
                try:
                    v += float(a["delta_amount"] or 0)
                except ValueError:
                    pass
            vals.append(max(v, 0.01 * c["initial"]) / c["initial"])
        if len(vals) >= 20:
            f = {"gmean": gmean, "median": statistics.median, "mean": statistics.mean}[stat]
            out[s] = (round(f(vals), 3), len(vals))
    return out


def c5(sb: dict) -> bool | None:
    if "software_saas" not in sb or len(sb) < 3:
        return None
    return max(sb, key=lambda s: sb[s][0]) == "software_saas"


# ----------------------------------------------------------------------------------------------
# checks
# ----------------------------------------------------------------------------------------------

def run_variant(name: str, recs: list[dict], amends: dict, rng: random.Random, note: str, chance: bool = True,
                K: int = 6) -> dict:
    m = metrics(recs, rng, with_chance=chance)
    sb = snowball(recs, amends, K=K)
    cl = claims(m)
    cl["C5"] = c5(sb)
    print(f"  {name:45s} " + " ".join(f"{k}={'—' if v is None else ('✓' if v else '✗')}" for k, v in cl.items()))
    return {"note": note, "metrics": m, "snowball": sb, "claims": cl}


def follow_on(contracts: dict, window: str) -> dict[str, dict]:
    """Consecutive same-vendor awards within jurisdiction x department x subsector vs shuffled order."""
    cells = defaultdict(list)
    for (j, _), r in contracts.items():
        v, d = r["vendor_name"].upper().strip(), r["department"].strip()
        if v and d and r["start_date"][:4].isdigit():
            sub = r["tech_subsector"] if r["is_tech"] == "1" else "non_tech"
            cells[(j, d, sub)].append((r["start_date"][:10], v))
    rng = random.Random(SEED)
    out = {}
    for s in SUBS:
        h = n = 0
        sh = [0] * 10
        for (j, d, sub), aw in cells.items():
            if sub != s:
                continue
            if window == "none":
                aw = sorted(aw)
            elif window == "month":
                aw = sorted({(x[:7], v) for x, v in aw})
            elif window == "quarter":
                aw = sorted({(f"{x[:4]}Q{(int(x[5:7]) - 1) // 3}", v) for x, v in aw})
            elif window == "year":
                aw = sorted({(x[:4], v) for x, v in aw})
            seq = [v for _, v in aw]
            if len(seq) < 2:
                continue
            h += sum(a == b for a, b in zip(seq, seq[1:]))
            n += len(seq) - 1
            for k in range(10):
                p = seq[:]
                rng.shuffle(p)
                sh[k] += sum(a == b for a, b in zip(p, p[1:]))
        if n:
            out[s] = {"observed": round(h / n, 4), "shuffled": round(statistics.mean(sh) / n, 4),
                      "excess_pts": round(100 * (h - statistics.mean(sh)) / n, 2), "pairs": n}
    return out


def fisher_one_sided(a: int, b: int, c: int, d: int) -> float:
    """P(X >= a) for the 2x2 table [[a, b], [c, d]] under the hypergeometric null."""
    n1, n2, k = a + b, c + d, a + c
    tot = math.comb(n1 + n2, k)
    return sum(math.comb(n1, x) * math.comb(n2, k - x) for x in range(a, min(n1, k) + 1)) / tot


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)
    contracts, amends, recs = load()
    res: dict = {"checks": {}}
    print(f"{len(recs):,} contracts in the fingerprint sample")

    def add(key, **kw):
        res["checks"][key] = run_variant(key, rng=rng, amends=amends, **kw)

    print("R0 baseline")
    add("R0_baseline", recs=recs, note="As in simulations/ and strategies.md")

    print("R1 leave one ledger out")
    for j in sorted({c["jurisdiction"] for c in recs}):
        sub = [c for c in recs if c["jurisdiction"] != j]
        add(f"R1_drop_{j}", recs=sub, note=f"Drop the {j} ledger")

    print("R2 one ledger at a time")
    for j in sorted({c["jurisdiction"] for c in recs}):
        sub = [c for c in recs if c["jurisdiction"] == j]
        if len(sub) >= 2000:
            add(f"R2_only_{j}", recs=sub, note=f"Only the {j} ledger")

    print("R3 award size thresholds")
    for t in (25_000, 100_000):
        add(f"R3_min_{t}", recs=[c for c in recs if c["initial"] >= t], note=f"Original award >= ${t:,}")

    print("R4 start-year window (censoring)")
    add("R4_start_2005_2019", recs=[c for c in recs if c["start_year"] and 2005 <= c["start_year"] <= 2019],
        note="Contracts starting 2005-2019 (older ones lack histories; newer ones are right-censored)")

    print("R5 outliers")
    add("R5_trim", recs=[c for c in recs if c["n"] <= 30 and (c["initial"] <= 0 or c["final"] / max(c["initial"], 1) <= 20)],
        note="Drop contracts with > 30 amendments or final value > 20x original")

    print("R6 classification")
    import re
    strict = re.compile(r"software|licen[cs]e|saas|subscription|cloud|maintenance and support|erp|crm|platform", re.I)
    recs6 = []
    for c in recs:
        if c["sub"] == "software_saas" and not strict.search(c["title"] or ""):
            continue  # keep only unambiguous software titles
        recs6.append(c)
    add("R6_strict_software", recs=recs6, note="Software & SaaS restricted to titles naming software, licences, SaaS, cloud, ERP/CRM")

    print("R7 escalation definition: last vs first positive amendment")
    r7 = {}
    for s, cs in by_sub(recs).items():
        a = b = 0
        for c in cs:
            z = c["sizes"]
            if len(z) >= 2 and z[-1] != z[0]:
                a += z[-1] > z[0]
                b += 1
        r7[s] = {"p_last_gt_first": round(a / b, 4) if b else None, "excess": round(a / b - 0.5, 4) if b else None, "pairs": b}
    ok = max((s for s in r7 if r7[s]["pairs"] >= 50), key=lambda s: r7[s]["excess"]) == "software_saas"
    res["checks"]["R7_last_vs_first"] = {"note": "P(last positive amendment > first)", "by_sector": r7, "claims": {"C1": ok}}
    print(f"  {'R7_last_vs_first':45s} C1={'✓' if ok else '✗'}")

    print("R8 snowball statistic and cohort")
    r8 = {}
    for K in (4, 6, 8):
        for stat in ("gmean", "median"):
            sb = snowball(recs, amends, K=K, stat=stat)
            r8[f"K{K}_{stat}"] = {"values": sb, "C5": c5(sb)}
            print(f"  {'R8_K' + str(K) + '_' + stat:45s} C5={'—' if c5(sb) is None else ('✓' if c5(sb) else '✗')}  "
                  + " ".join(f"{s}={v[0]}" for s, v in sorted(sb.items())))
    res["checks"]["R8_snowball_variants"] = {"note": "Value after K amendments: K = 4, 6, 8; geometric mean or median", **r8}

    print("R9 permutation test: software vs non-tech escalation within ledger")
    soft = [c for c in recs if c["sub"] in ("software_saas", "non_tech") and len(c["sizes"]) >= 2 and c["sizes"][0] != c["sizes"][1]]
    def diff(labels):
        g = defaultdict(lambda: [0, 0])
        for c, l in zip(soft, labels):
            g[l][0] += c["sizes"][1] > c["sizes"][0]
            g[l][1] += 1
        return g["software_saas"][0] / g["software_saas"][1] - g["non_tech"][0] / g["non_tech"][1]
    obs = diff([c["sub"] for c in soft])
    by_j = defaultdict(list)
    for i, c in enumerate(soft):
        by_j[c["jurisdiction"]].append(i)
    prng = random.Random(SEED)
    null = []
    for _ in range(1000):
        lab = [c["sub"] for c in soft]
        for idx in by_j.values():
            sub = [lab[i] for i in idx]
            prng.shuffle(sub)
            for i, l in zip(idx, sub):
                lab[i] = l
        null.append(diff(lab))
    p = (1 + sum(x >= obs for x in null)) / (1 + len(null))
    res["checks"]["R9_permutation"] = {"note": "Shuffle software / non-tech labels within ledger, 1,000 draws",
                                       "observed_diff": round(obs, 4), "null_p95": round(sorted(null)[949], 4),
                                       "p_value": round(p, 4), "pairs": len(soft), "claims": {"C1": p < 0.05}}
    print(f"  R9 observed diff {obs:+.3f}, null 95th pct {sorted(null)[949]:+.3f}, p = {p:.4f}")

    print("R10 matched-chance seeds")
    r10 = {}
    for seed in (1, 2, 3):
        m = metrics(recs, random.Random(seed), reps=20)
        r10[f"seed_{seed}"] = {s: {k: v[k]["z"] for k in ("early", "late") if isinstance(v.get(k), dict)} for s, v in m.items()}
        cl = claims(m)
        r10[f"seed_{seed}"]["claims"] = {"C3": cl["C3"], "C4": cl["C4"]}
        print(f"  seed {seed}: C3={cl['C3']} C4={cl['C4']}")
    res["checks"]["R10_seeds"] = {"note": "Matched-chance z-scores for early / late with three other seeds", **r10}

    print("R11 follow-on definitions")
    r11 = {w: follow_on(contracts, w) for w in ("none", "month", "quarter", "year")}
    res["checks"]["R11_follow_on"] = {"note": "Collapse repeat awards to the same vendor within: nothing / month / quarter / year", **r11}
    for w, v in r11.items():
        print(f"  window={w:8s} " + " ".join(f"{s}:{x['excess_pts']:+.1f}" for s, x in v.items()))

    print("R12 resellers in hardware & telecom, within ledger")
    r12 = {}
    for j in sorted({r["jurisdiction"] for r in contracts.values()}):
        hw = [r for r in contracts.values() if r["jurisdiction"] == j and r["tech_subsector"] == "hardware_telecom"
              and r["is_tech"] == "1" and r["amendment_observable"] == "1"]
        rs = [r for r in hw if r["vendor_role"] == "authorized_reseller"]
        ot = [r for r in hw if r["vendor_role"] != "authorized_reseller"]
        if len(rs) >= 30 and len(ot) >= 30:
            rate = lambda xs: sum(r["is_amended"] == "1" for r in xs) / len(xs)
            r12[j] = {"resellers": len(rs), "reseller_rate": round(rate(rs), 4), "others": len(ot),
                      "other_rate": round(rate(ot), 4), "lower": rate(rs) < rate(ot)}
            print(f"  {j:20s} resellers {rate(rs):.1%} (n={len(rs)}) vs others {rate(ot):.1%} (n={len(ot)})")
    res["checks"]["R12_resellers_within_ledger"] = {"note": "Hardware & telecom amendment rate, resellers vs others, by ledger",
                                                    "by_ledger": r12,
                                                    "claims": {"C7": all(v["lower"] for v in r12.values()) if r12 else None}}

    print("R13 holdover documents: exact test")
    docs = json.loads((ROOT / "synthesis/results/document_summary.json").read_text())["by_sector"]
    tot = lambda s: sum(docs.get(s, {}).values())
    hold = lambda s: docs.get(s, {}).get("re-competition delayed", 0)
    a = hold("software_saas") + hold("tech_general")
    b = tot("software_saas") + tot("tech_general") - a
    c, d = hold("non_tech"), tot("non_tech") - hold("non_tech")
    pv = fisher_one_sided(a, b, c, d)
    res["checks"]["R13_holdover_exact"] = {"note": "Fisher exact test (one-sided): holdover share, software + general tech vs non-tech",
                                           "software_general": [a, a + b], "non_tech": [c, c + d], "p_value": round(pv, 6),
                                           "claims": {"C8": pv < 0.05}}
    print(f"  holdovers {a}/{a + b} vs {c}/{c + d}: p = {pv:.2g}")

    print("R14 out-of-sample: ledgers added after the theory and simulations were built")
    r14 = {}
    for j in ("dc", "nyc_checkbook", "wa_doh"):
        rows = [r for r in contracts.values() if r["jurisdiction"] == j and r["amendment_observable"] == "1"]
        if not rows:
            continue
        t = {}
        for s in SUBS:
            xs = [r for r in rows if (r["tech_subsector"] if r["is_tech"] == "1" else "non_tech") == s]
            am = [r for r in xs if r["is_amended"] == "1"]
            gr = [float(r["final_award_val"]) / float(r["initial_award_val"]) for r in am
                  if float(r["initial_award_val"] or 0) >= 1000 and float(r["final_award_val"] or 0) > 0]
            # escalation by event order (DC events are ordered by option period and document version)
            a = b = 0
            for r in xs:
                seq = [float(x["delta_amount"] or 0) for x in amends.get((j, r["contract_id"]), [])]
                pos = [x for x in seq if x > 0]
                if len(pos) >= 2 and pos[0] != pos[1]:
                    a += pos[1] > pos[0]
                    b += 1
            t[s] = {"contracts": len(xs), "amended_share": round(len(am) / len(xs), 4) if xs else None,
                    "mean_amendments": round(statistics.mean(int(r["amendment_count"] or 0) for r in xs), 3) if xs else None,
                    "median_growth_when_amended": round(statistics.median(gr), 3) if len(gr) >= 20 else None,
                    "escal_excess": round(a / b - 0.5, 4) if b >= 30 else None, "escal_pairs": b}
        r14[j] = t
        print(f"  {j}: " + "; ".join(f"{s} amended {v['amended_share']}, growth {v['median_growth_when_amended']}, "
                                     f"escal {v['escal_excess']}" for s, v in t.items() if v["contracts"]))
    res["checks"]["R14_out_of_sample"] = {"note": "New ledgers (DC, NYC Checkbook, WA Dept. of Health)", **r14}

    # survival table
    surv = defaultdict(lambda: Counter())
    for key, chk in res["checks"].items():
        for cl, v in (chk.get("claims") or {}).items():
            surv[cl]["held" if v else ("failed" if v is False else "n/a")] += 1
    res["survival"] = {k: dict(v) for k, v in sorted(surv.items())}
    print("\nClaim survival across checks:", json.dumps(res["survival"]))
    (OUT / "checks.json").write_text(json.dumps(res, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
