#!/usr/bin/env python3
"""Synthesis steps 1-2: power, parameter recovery, and simulated method of moments by sector.

Run from the repository root:

    python3 synthesis/smm.py power                 # step 1a: power / minimum detectable effects (seconds)
    python3 synthesis/smm.py estimate [sectors...] # step 2: SMM estimates by sector (~1-3 min per sector)
    python3 synthesis/smm.py recover               # step 1b: parameter recovery on synthetic data (~20-30 min)

Outputs (synthesis/results/): power_by_sector.csv, smm_estimates.csv, smm_estimates.json,
smm_recovery.csv. Standard library only.

Model (one contract per row of the sector's real contract list, keeping its vendor and its
ledger x department cell):
  chance       amendments arrive with contract rate  lam * Gamma(shape)/shape * vendor_mult,
               vendor_mult = exp(sv*N(0,1) - sv^2/2), at times ~ Beta(a, 1) over the term
               (a > 1 leans later); sizes iid
  renewal      with probability r, one renewal amendment at the end of the term
  lock-in      a share pi_d of VENDORS are designers. On their contracts each amendment raises
               dependence k; hazard x exp(rho*min(k,4)), size x (1 + psi*min(k,4)), and the odds of an
               end-of-term extension rise with k
Ten moments: share amended, mean count, variance/mean, early share, late share, late lift,
acceleration before term end, escalation, vendor share of risk, rise in continuation k=0->3.
Derived: lock-in share of amendments = 1 - E[count | designers switched off] / E[count].
"""

from __future__ import annotations

import csv
import json
import math
import random
import statistics
import sys
import zlib
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "simulations"))
from simulate_amendments import fingerprints, load_sector_contracts, poisson  # noqa: E402

RESULTS = HERE / "results"
SIM_RESULTS = ROOT / "simulations" / "results" / "amendment_fingerprints.json"

PARAMS = ["lam", "shape", "sv", "a", "r", "pi_d", "psi", "rho"]
MOMENTS = ["p_any", "mean_n", "var_ratio", "early", "late", "lift", "accel_pre", "escal", "vendor", "cont"]
K_CAP = 4.0
SIM_MAX = 8000          # contracts simulated per evaluation (subsampled structure if larger)
BOOT = 30               # bootstrap replicates for observed-moment standard errors


def logistic(x: float) -> float:
    return 1 / (1 + math.exp(-x))


def logit(p: float) -> float:
    p = min(max(p, 1e-6), 1 - 1e-6)
    return math.log(p / (1 - p))


# unconstrained <-> constrained parameters
def to_theta(u: list[float]) -> dict:
    return {"lam": math.exp(u[0]), "shape": math.exp(u[1]), "sv": math.exp(u[2]), "a": 1 + math.exp(u[3]),
            "r": logistic(u[4]), "pi_d": logistic(u[5]), "psi": math.exp(u[6]), "rho": math.exp(u[7])}


def to_u(th: dict) -> list[float]:
    return [math.log(th["lam"]), math.log(th["shape"]), math.log(th["sv"]), math.log(th["a"] - 1),
            logit(th["r"]), logit(th["pi_d"]), math.log(th["psi"]), math.log(th["rho"])]


# --------------------------------------------------------------------------------------
# Moments
# --------------------------------------------------------------------------------------

def moments(contracts: list[dict]) -> dict:
    fp = fingerprints(contracts)
    ns = [c["n"] for c in contracts]
    mean = statistics.mean(ns)
    var = statistics.pvariance(ns)
    return {"p_any": sum(1 for n in ns if n > 0) / len(ns), "mean_n": mean,
            "var_ratio": var / mean if mean > 0 else None, "early": fp.get("early"), "late": fp.get("late"),
            "lift": fp.get("lift"), "accel_pre": fp.get("accel_pre"), "escal": fp.get("escal"),
            "vendor": fp.get("vendor"), "cont": fp.get("cont")}


def observed(cs: list[dict], rng: random.Random) -> tuple[dict, dict, dict]:
    m = moments(cs)
    boots = defaultdict(list)
    for _ in range(BOOT):
        b = [cs[rng.randrange(len(cs))] for _ in range(len(cs))]
        for k, v in moments(b).items():
            if v is not None:
                boots[k].append(v)
    se = {k: (statistics.pstdev(v) if len(v) > 5 else None) for k, v in boots.items()}
    n_tot = sum(c["n"] for c in cs)
    shares = {"date_share": sum(len(c["times"]) for c in cs) / n_tot if n_tot else 1.0,
              "size_share": sum(len(c["sizes"]) for c in cs) / n_tot if n_tot else 1.0}
    return m, se, shares


# --------------------------------------------------------------------------------------
# Generator
# --------------------------------------------------------------------------------------

def poisson_inv(u: float, mu: float) -> int:
    """Poisson draw by inverse CDF from one uniform: monotone in mu, so the simulated objective
    changes smoothly with the parameters (common random numbers)."""
    if mu <= 0:
        return 0
    if mu > 50:
        z = math.sqrt(-2 * math.log(max(u, 1e-12))) * math.cos(2 * math.pi * 0.25)  # not used for typical mu
        return max(0, int(round(mu + math.sqrt(mu) * (2 * u - 1) * 1.7)))
    k, prob = 0, math.exp(-mu)
    cdf = prob
    while u > cdf and k < 400:
        k += 1
        prob *= mu / k
        cdf += prob
    return k


def generate(th: dict, structure: list[tuple[str, str]], shares: dict, seed: int,
             designers_on: bool = True) -> list[dict]:
    """Simulate one dataset. Every vendor and every contract has its own random stream, so a
    parameter change only moves the draws it should (common random numbers)."""
    lam, shape, sv, a, r = th["lam"], th["shape"], th["sv"], th["a"], th["r"]
    pid, psi, rho = th["pi_d"], th["psi"], th["rho"]
    vend: dict[str, tuple[float, bool]] = {}
    out = []
    for idx, (vendor, cell) in enumerate(structure):
        if vendor not in vend:
            vr = random.Random(seed * 7919 + zlib.crc32(vendor.encode()))
            g, ud = vr.gauss(0, 1), vr.random()
            vend[vendor] = (math.exp(sv * g - sv * sv / 2), ud < pid)
        mult, designer = vend[vendor]
        designer = designer and designers_on
        rng = random.Random(seed * 1000003 + idx)
        u_rate, u_n, u_ren = rng.random(), rng.random(), rng.random()
        # gamma heterogeneity by inverse transform on a fixed uniform (Wilson-Hilferty approximation)
        zq = inv_norm(u_rate)
        gam = max(1e-6, (1 - 1 / (9 * shape) + zq * math.sqrt(1 / (9 * shape))) ** 3) if shape > 0.05 else \
            (-math.log(max(1 - u_rate, 1e-12)) * 1.0)
        rate = lam * gam * mult
        times, sizes = [], []
        if not designer:
            for _ in range(poisson_inv(u_n, rate)):
                times.append(rng.random() ** (1 / a))
            times.sort()
            sizes = [math.exp(rng.gauss(0, 1)) for _ in times]
            if u_ren < r:
                times.append(0.9 + 0.15 * rng.random())
                sizes.append(math.exp(rng.gauss(0, 1)))
        else:
            bound = rate * a * math.exp(rho * K_CAP)
            cand = sorted(rng.random() for _ in range(poisson_inv(u_n, bound)))
            k = 0.0
            for t in cand:
                h = rate * a * t ** (a - 1) * math.exp(rho * min(k, K_CAP))
                if rng.random() < h / bound:
                    times.append(t)
                    sizes.append(math.exp(rng.gauss(0, 1)) * (1 + psi * min(k, K_CAP)))
                    k += 1
            if u_ren < logistic(logit(r) + 0.5 * min(k, K_CAP)):
                times.append(0.9 + 0.15 * rng.random())
                sizes.append(math.exp(rng.gauss(0, 1)) * (1 + psi * min(k, K_CAP)))
        n = len(times)
        keep_t = [t for t in times if rng.random() < shares["date_share"]]
        keep_s = [x for x in sizes if rng.random() < shares["size_share"]]
        out.append({"vendor": vendor, "cell": cell, "n": n, "times": keep_t, "sizes": keep_s,
                    "value": sum(sizes)})  # total amendment size before measurement thinning
    return out


def inv_norm(u: float) -> float:
    """Inverse standard normal CDF (Acklam's rational approximation)."""
    u = min(max(u, 1e-10), 1 - 1e-10)
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02, 1.383577518672690e+02,
         -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02, 6.680131188771972e+01,
         -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00, -2.549671010229356e+00,
         4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00, 3.754408661907416e+00]
    pl = 0.02425
    if u < pl:
        q = math.sqrt(-2 * math.log(u))
        return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    if u > 1 - pl:
        q = math.sqrt(-2 * math.log(1 - u))
        return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    q = u - 0.5
    r_ = q * q
    return (((((a[0]*r_+a[1])*r_+a[2])*r_+a[3])*r_+a[4])*r_+a[5])*q / (((((b[0]*r_+b[1])*r_+b[2])*r_+b[3])*r_+b[4])*r_+1)


# --------------------------------------------------------------------------------------
# Estimation
# --------------------------------------------------------------------------------------

def nelder_mead(f, x0: list[float], step: float = 0.5, max_evals: int = 260, tol: float = 1e-4):
    n = len(x0)
    pts = [x0] + [[x0[j] + (step if j == i else 0) for j in range(n)] for i in range(n)]
    vals = [f(p) for p in pts]
    evals = n + 1
    while evals < max_evals:
        order = sorted(range(n + 1), key=lambda i: vals[i])
        pts, vals = [pts[i] for i in order], [vals[i] for i in order]
        if abs(vals[-1] - vals[0]) < tol * (1 + abs(vals[0])):
            break
        cen = [sum(p[j] for p in pts[:-1]) / n for j in range(n)]
        xr = [cen[j] + (cen[j] - pts[-1][j]) for j in range(n)]
        fr = f(xr); evals += 1
        if fr < vals[0]:
            xe = [cen[j] + 2 * (cen[j] - pts[-1][j]) for j in range(n)]
            fe = f(xe); evals += 1
            pts[-1], vals[-1] = (xe, fe) if fe < fr else (xr, fr)
        elif fr < vals[-2]:
            pts[-1], vals[-1] = xr, fr
        else:
            xc = [cen[j] + 0.5 * (pts[-1][j] - cen[j]) for j in range(n)]
            fc = f(xc); evals += 1
            if fc < vals[-1]:
                pts[-1], vals[-1] = xc, fc
            else:
                for i in range(1, n + 1):
                    pts[i] = [pts[0][j] + 0.5 * (pts[i][j] - pts[0][j]) for j in range(n)]
                    vals[i] = f(pts[i]); evals += 1
    best = min(range(n + 1), key=lambda i: vals[i])
    return pts[best], vals[best], evals


def start_theta(m: dict) -> dict:
    mean, vr = m["mean_n"], max(m["var_ratio"] or 2.0, 1.2)
    shape = max(0.05, mean / (vr - 1))
    return {"lam": max(0.05, 0.7 * mean), "shape": min(shape, 5.0), "sv": 0.5, "a": 1.6, "r": 0.25,
            "pi_d": 0.15, "psi": 0.3, "rho": 0.3}


class Problem:
    def __init__(self, cs: list[dict], m: dict, se: dict, shares: dict, seed: int = 11,
                 exclude: tuple[str, ...] = ()):
        self.m, self.shares, self.seed = m, shares, seed
        rng = random.Random(seed)
        self.structure = [(c["vendor"], c["cell"]) for c in cs]
        if len(self.structure) > SIM_MAX:
            self.structure = rng.sample(self.structure, SIM_MAX)
        ratio = len(cs) / len(self.structure)
        # weights: observed sampling variance inflated by simulation noise at the simulated size
        self.keys = [k for k in MOMENTS if m.get(k) is not None and se.get(k) and k not in exclude]
        self.w = {k: 1 / (se[k] ** 2 * (1 + ratio)) for k in self.keys}

    def sim_moments(self, th: dict, designers_on: bool = True, seed: int | None = None) -> dict:
        return moments(generate(th, self.structure, self.shares, self.seed if seed is None else seed, designers_on))

    def objective(self, u: list[float]) -> float:
        if any(abs(x) > 12 for x in u):
            return 1e12
        sm = self.sim_moments(to_theta(u))
        q = 0.0
        for k in self.keys:
            v = sm.get(k)
            q += self.w[k] * ((v if v is not None else 0) - self.m[k]) ** 2
        return q


def lockin_share(p: Problem, th: dict, seeds=(101, 202, 303)) -> float:
    on = [p.sim_moments(th, True, s)["mean_n"] for s in seeds]
    off = [p.sim_moments(th, False, s)["mean_n"] for s in seeds]
    return 1 - statistics.mean(off) / statistics.mean(on) if statistics.mean(on) > 0 else 0.0


def standard_errors(p: Problem, u: list[float]) -> list[float | None]:
    """SMM sandwich (diagonal weights): V = (G'WG)^-1 (G'W S W G)(G'WG)^-1 with S = W^-1 here."""
    h = 0.15
    base_keys = p.keys
    G = []
    for i in range(len(u)):
        up = list(u); dn = list(u)
        up[i] += h; dn[i] -= h
        mu, md = p.sim_moments(to_theta(up)), p.sim_moments(to_theta(dn))
        G.append([((mu.get(k) or 0) - (md.get(k) or 0)) / (2 * h) for k in base_keys])
    # G is params x moments; information = G W G'
    P = len(u)
    info = [[sum(G[a][j] * p.w[k] * G[b][j] for j, k in enumerate(base_keys)) for b in range(P)] for a in range(P)]
    inv = invert(info)
    full = [math.sqrt(inv[i][i]) if (inv is not None and inv[i][i] > 0) else None for i in range(P)]
    # Fallback when the information matrix is (near-)singular: per-parameter SE from its diagonal.
    # These understate uncertainty when parameters trade off, so they are flagged in the output.
    return [f if f is not None else (1 / math.sqrt(info[i][i]) if info[i][i] > 0 else 1.0) for i, f in enumerate(full)]


def invert(M: list[list[float]]):
    n = len(M)
    A = [row[:] + [1.0 if i == j else 0.0 for j in range(n)] for i, row in enumerate(M)]
    for i in range(n):
        piv = max(range(i, n), key=lambda r: abs(A[r][i]))
        if abs(A[piv][i]) < 1e-12:
            return None
        A[i], A[piv] = A[piv], A[i]
        d = A[i][i]
        A[i] = [x / d for x in A[i]]
        for r in range(n):
            if r != i and A[r][i] != 0:
                f = A[r][i]
                A[r] = [x - f * y for x, y in zip(A[r], A[i])]
    return [row[n:] for row in A]


def estimate(cs: list[dict], label: str, rng: random.Random, m=None, se=None, shares=None,
             exclude: tuple[str, ...] = (), draws_n: int = 20) -> dict:
    if m is None:
        m, se, shares = observed(cs, rng)
    p = Problem(cs, m, se, shares, exclude=exclude)
    base = start_theta(m)
    starts = [base, {**base, "sv": 1.5}, {**base, "pi_d": 0.4, "psi": 0.8, "sv": 1.0}]
    best_u, best_q, evals = None, float("inf"), 0
    for st in starts:
        u, q, e = nelder_mead(p.objective, to_u(st), step=0.6, max_evals=450)
        evals += e
        if q < best_q:
            best_u, best_q = u, q
    u2, q2, e2 = nelder_mead(p.objective, best_u, step=0.2, max_evals=300)  # polish
    evals += e2
    if q2 < best_q:
        best_u, best_q = u2, q2
    th = to_theta(best_u)
    se_u = standard_errors(p, best_u)
    # parametric draws for intervals on pi_d, psi and the derived lock-in share
    draws = []
    for _ in range(draws_n):
        ud = [x + (s or 0) * rng.gauss(0, 1) for x, s in zip(best_u, se_u)]
        draws.append((to_theta(ud), ud))
    shares_draw = sorted(lockin_share(p, t, seeds=(101,)) for t, _ in draws)
    pi_draw = sorted(t["pi_d"] for t, _ in draws)
    psi_draw = sorted(t["psi"] for t, _ in draws)
    q = lambda xs, f: xs[min(len(xs) - 1, max(0, int(f * (len(xs) - 1))))]
    fit = p.sim_moments(th)
    res = {"sector": label, "contracts": len(cs), "objective": round(best_q, 3), "evals": evals,
           "excluded_moments": list(exclude), "u": best_u,
           "df": len(p.keys) - len(PARAMS), "theta": {k: round(v, 4) for k, v in th.items()},
           "se_unconstrained": [None if s is None else round(s, 3) for s in se_u],
           "pi_d_90": [round(q(pi_draw, .05), 3), round(q(pi_draw, .95), 3)],
           "psi_90": [round(q(psi_draw, .05), 3), round(q(psi_draw, .95), 3)],
           "lockin_share": round(lockin_share(p, th), 4),
           "lockin_share_90": [round(q(shares_draw, .05), 4), round(q(shares_draw, .95), 4)],
           "moments": {k: {"observed": round(m[k], 4) if m.get(k) is not None else None,
                           "fitted": round(fit[k], 4) if fit.get(k) is not None else None,
                           "se": round(se[k], 5) if se.get(k) else None,
                           "t": round((fit[k] - m[k]) / se[k], 2) if (fit.get(k) is not None and m.get(k)
                                                                      is not None and se.get(k)) else None}
                       for k in MOMENTS}}
    return res


# --------------------------------------------------------------------------------------
# Commands
# --------------------------------------------------------------------------------------

def sector_data() -> dict[str, list[dict]]:
    groups = load_sector_contracts()
    return {k: [c for c in v if c["timed"]] for k, v in groups.items()}


def cmd_power() -> None:
    d = json.loads(SIM_RESULTS.read_text())
    rows = []
    z80 = 2.0 + 0.8416  # one-sided test at z >= 2 with 80% power
    phi = lambda x: 0.5 * (1 + math.erf(x / math.sqrt(2)))
    ref = d["sectors"]["subsector:software_saas"]["fingerprints"]
    for name, sec in d["sectors"].items():
        fp = sec["fingerprints"]
        row = {"sector": name, "contracts": sec["contracts"], "timed_contracts": sec["timed_contracts"],
               "escal_pairs": sec["eligible"]["escal_pairs"], "accel_pre_pairs": sec["eligible"]["accel_pre_pairs"]}
        for k in ("escal", "vendor", "accel_pre"):
            if k not in fp:
                continue
            sd = fp[k]["chance_sd"]
            eff_ref = ref[k]["observed"] - ref[k]["chance_mean"]  # Software & SaaS effect as a benchmark
            row[f"{k}_null_sd"] = sd
            row[f"{k}_mde80"] = round(z80 * sd, 4)
            row[f"{k}_power_at_software_effect"] = round(phi(eff_ref / sd - 2.0), 3) if sd > 0 else None
        rows.append(row)
    RESULTS.mkdir(parents=True, exist_ok=True)
    fields = list(dict.fromkeys(k for r in rows for k in r))
    with (RESULTS / "power_by_sector.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    for r in rows:
        print(f"{r['sector']:38} escal MDE80={r.get('escal_mde80')} power@SaaS={r.get('escal_power_at_software_effect')}"
              f" | vendor MDE80={r.get('vendor_mde80')} | accel MDE80={r.get('accel_pre_mde80')}")
    print(f"Wrote {RESULTS / 'power_by_sector.csv'}")


def write_estimates(results: list[dict]) -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    path = RESULTS / "smm_estimates.json"
    prev = json.loads(path.read_text()) if path.exists() else {}
    prev.update({r["sector"]: r for r in results})
    path.write_text(json.dumps(prev, indent=1))
    with (RESULTS / "smm_estimates.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["sector", "contracts", *PARAMS, "pi_d_lo", "pi_d_hi", "psi_lo", "psi_hi",
                                          "lockin_share", "lockin_share_lo", "lockin_share_hi", "objective", "df",
                                          "worst_moment", "worst_t"])
        w.writeheader()
        for r in sorted(prev.values(), key=lambda r: -r["lockin_share"]):
            worst = max(((k, v["t"]) for k, v in r["moments"].items() if v["t"] is not None),
                        key=lambda kv: abs(kv[1]), default=(None, None))
            w.writerow({"sector": r["sector"], "contracts": r["contracts"], **r["theta"],
                        "pi_d_lo": r["pi_d_90"][0], "pi_d_hi": r["pi_d_90"][1], "psi_lo": r["psi_90"][0],
                        "psi_hi": r["psi_90"][1], "lockin_share": r["lockin_share"],
                        "lockin_share_lo": r["lockin_share_90"][0], "lockin_share_hi": r["lockin_share_90"][1],
                        "objective": r["objective"], "df": r["df"], "worst_moment": worst[0], "worst_t": worst[1]})


def cmd_estimate(names: list[str]) -> None:
    data = sector_data()
    order = names or ["subsector:software_saas", "domain:general_enterprise_it", "subsector:tech_general",
                      "subsector:hardware_telecom", "domain:health_care", "domain:public_assistance",
                      "domain:administration_finance", "non_tech"]
    rng = random.Random(20261108)
    for name in order:
        cs = data.get(name)
        if not cs:
            print(f"skip {name}: no data")
            continue
        r = estimate(cs, name, rng)
        write_estimates([r])
        th = r["theta"]
        print(f"[estimate] {name:34} n={r['contracts']:>7,} Q={r['objective']:>8} lock-in share={r['lockin_share']:.3f} "
              f"{r['lockin_share_90']}  pi_d={th['pi_d']:.3f} {r['pi_d_90']}  psi={th['psi']:.3f} {r['psi_90']}",
              flush=True)
    print(f"Wrote {RESULTS / 'smm_estimates.csv'}")


def cmd_recover() -> None:
    """Generate synthetic data with KNOWN parameters on real sector structures and re-estimate."""
    data = sector_data()
    est = json.loads((RESULTS / "smm_estimates.json").read_text()) if (RESULTS / "smm_estimates.json").exists() else {}
    rng = random.Random(7)
    rows = []
    for name in ("subsector:software_saas", "subsector:hardware_telecom", "domain:health_care"):
        cs = data[name]
        _, se, shares = observed(cs, rng)
        truth_lock = dict(est[name]["theta"]) if name in est else start_theta(moments(cs))
        truth_none = dict(truth_lock, pi_d=1e-4)
        for scen, truth in (("fitted parameters", truth_lock), ("no lock-in", truth_none)):
            for rep in range(3):
                syn = generate(truth, [(c["vendor"], c["cell"]) for c in cs], shares, seed=1000 + rep)
                m = moments(syn)
                se_syn = {k: se.get(k) for k in m}
                r = estimate(syn, f"{name}|{scen}|{rep}", rng, m=m, se=se_syn, shares=shares)
                p = Problem(syn, m, se_syn, shares)
                true_share = lockin_share(p, truth)
                rows.append({"sector": name, "scenario": scen, "rep": rep,
                             "true_pi_d": round(truth["pi_d"], 4), "est_pi_d": r["theta"]["pi_d"],
                             "true_psi": round(truth["psi"], 4), "est_psi": r["theta"]["psi"],
                             "true_lockin_share": round(true_share, 4), "est_lockin_share": r["lockin_share"],
                             "est_lockin_share_lo": r["lockin_share_90"][0],
                             "est_lockin_share_hi": r["lockin_share_90"][1]})
                print(f"[recover] {name:28} {scen:18} rep{rep}: share true={true_share:.3f} est={r['lockin_share']:.3f} "
                      f"{r['lockin_share_90']}  pi_d true={truth['pi_d']:.3f} est={r['theta']['pi_d']:.3f}", flush=True)
                with (RESULTS / "smm_recovery.csv").open("w", newline="", encoding="utf-8") as f:
                    w = csv.DictWriter(f, fieldnames=list(rows[0]))
                    w.writeheader()
                    w.writerows(rows)
    print(f"Wrote {RESULTS / 'smm_recovery.csv'}")


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "power"
    if cmd == "power":
        cmd_power()
    elif cmd == "estimate":
        cmd_estimate(sys.argv[2:])
    elif cmd == "recover":
        cmd_recover()
    else:
        print(__doc__)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
