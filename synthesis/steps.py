#!/usr/bin/env python3
"""Synthesis steps 3, 4, 5 and 8 (step 6 is synthesis/document_sample.py; step 7, chance-shock event
studies, was dropped: the ledgers are not good enough to isolate a dated shock).

Run from the repository root after `python3 synthesis/smm.py estimate`:

    python3 synthesis/steps.py validate         # step 3: leave-one-moment-out and time-split prediction
    python3 synthesis/steps.py channels         # step 4: estimates by procurement channel
    python3 synthesis/steps.py vendors          # step 5: estimates by vendor type
    python3 synthesis/steps.py counterfactuals  # step 8: policy levers under the estimated parameters

Predictions recorded BEFORE the estimates were seen (2026-11-08):
  step 4  Catalog / pre-priced vehicles cap the margin: escalation (psi) and the lock-in share should
          be lower for central state contracts and cooperative purchases than for own solicitations.
  step 5  Resellers control less of a product's dependence than primes -> lower lock-in share.
          GSA schedule holders sell at pre-negotiated ceilings -> lower psi.
          Multiple-award contracts face order-level competition -> lower psi.
"""

from __future__ import annotations

import csv
import json
import math
import random
import re
import statistics
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import smm  # noqa: E402

RESULTS = HERE / "results"
PROCESSED = ROOT / "data" / "processed"
PREDICTIONS = {
    "channels": "Escalation and lock-in share lower for central state contracts and cooperative purchases "
                "than for own solicitations (pre-priced vehicles cap the margin).",
    "vendors": "Lower lock-in share for resellers than primes; lower escalation for GSA schedule holders and "
               "for multiple-award contracts.",
}


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    fields = list(dict.fromkeys(k for r in rows for k in r))
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {path}")


def summary_row(label: str, group: str, r: dict) -> dict:
    th = r["theta"]
    return {"analysis": label, "group": group, "contracts": r["contracts"],
            "lockin_share": r["lockin_share"], "lockin_share_lo": r["lockin_share_90"][0],
            "lockin_share_hi": r["lockin_share_90"][1], "pi_d": th["pi_d"], "pi_d_lo": r["pi_d_90"][0],
            "pi_d_hi": r["pi_d_90"][1], "psi": th["psi"], "psi_lo": r["psi_90"][0], "psi_hi": r["psi_90"][1],
            "rho": th["rho"], "renewal_r": th["r"], "objective": r["objective"],
            "escal_observed": r["moments"]["escal"]["observed"], "vendor_observed": r["moments"]["vendor"]["observed"]}


# --------------------------------------------------------------------------------------
# Step 3: validation
# --------------------------------------------------------------------------------------

def cmd_validate() -> None:
    data = smm.sector_data()
    rng = random.Random(31)
    rows = []
    # (a) leave one moment out, predict it
    for name in ("subsector:software_saas", "domain:general_enterprise_it", "domain:health_care", "non_tech"):
        cs = data[name]
        m, se, shares = smm.observed(cs, rng)
        for k in ("escal", "vendor"):
            r = smm.estimate(cs, name, rng, m=m, se=se, shares=shares, exclude=(k,), draws_n=4)
            mk = r["moments"][k]
            rows.append({"test": "leave-one-moment-out", "sector": name, "held_out": k,
                         "observed": mk["observed"], "predicted": mk["fitted"], "se": mk["se"], "t": mk["t"],
                         "lockin_share_without_it": r["lockin_share"]})
            print(f"[validate] {name:34} without {k:7}: observed={mk['observed']} predicted={mk['fitted']} t={mk['t']} "
                  f"lock-in share={r['lockin_share']:.3f}", flush=True)
    # (b) time split: fit on contracts starting before 2015, predict those starting 2015 or later
    for name in ("subsector:software_saas", "domain:general_enterprise_it", "domain:health_care", "non_tech"):
        cs = data[name]
        early = [c for c in cs if c["start_date"][:4] and c["start_date"][:4] < "2015"]
        late = [c for c in cs if c["start_date"][:4] and c["start_date"][:4] >= "2015"]
        if len(early) < 500 or len(late) < 500:
            continue
        r = smm.estimate(early, name + "|<2015", rng, draws_n=4)
        mt, set_, sht = smm.observed(late, rng)
        p = smm.Problem(late, mt, set_, sht)
        pred = p.sim_moments(smm.to_theta(r["u"]))
        for k in smm.MOMENTS:
            if mt.get(k) is None or not set_.get(k) or pred.get(k) is None:
                continue
            rows.append({"test": "time split (<2015 -> 2015+)", "sector": name, "held_out": k,
                         "observed": round(mt[k], 4), "predicted": round(pred[k], 4), "se": round(set_[k], 5),
                         "t": round((pred[k] - mt[k]) / set_[k], 2),
                         "lockin_share_without_it": r["lockin_share"]})
        print(f"[validate] time split {name}: done", flush=True)
    write_csv(RESULTS / "validation.csv", rows)


# --------------------------------------------------------------------------------------
# Steps 4-5: estimates by channel and by vendor type
# --------------------------------------------------------------------------------------

def grouped_estimates(label: str, groups: dict[str, list[dict]], min_n: int = 500) -> list[dict]:
    rng = random.Random(41)
    rows = []
    for g, cs in groups.items():
        if len(cs) < min_n:
            print(f"[{label}] skip {g}: {len(cs)} contracts")
            continue
        r = smm.estimate(cs, g, rng, draws_n=12)
        rows.append(summary_row(label, g, r))
        print(f"[{label}] {g:40} n={len(cs):>7,} lock-in share={r['lockin_share']:.3f} {r['lockin_share_90']} "
              f"psi={r['theta']['psi']:.3f} {r['psi_90']} escal obs={r['moments']['escal']['observed']}", flush=True)
    return rows


def all_timed() -> list[dict]:
    from simulate_amendments import load_sector_contracts
    groups = load_sector_contracts()
    seen, out = set(), []
    for key in ("all_tech", "non_tech"):
        for c in groups[key]:
            if c["timed"] and (c["jurisdiction"], c["contract_id"]) not in seen:
                seen.add((c["jurisdiction"], c["contract_id"]))
                out.append(c)
    return out


def cmd_channels() -> None:
    cs = all_timed()
    groups: dict[str, list[dict]] = defaultdict(list)
    for c in cs:
        ch = c["channel"]
        g = ("own solicitation / unknown" if ch == "direct_or_unknown" else
             "central state contract" if ch == "central_state_contract" else "cooperative (any direction)")
        groups[f"{'tech' if c['is_tech'] == '1' else 'non-tech'}: {g}"].append(c)
    print({k: len(v) for k, v in groups.items()})
    rows = grouped_estimates("channels", dict(groups))
    write_csv(RESULTS / "smm_by_channel.csv", rows)


def cmd_vendors() -> None:
    cs = [c for c in all_timed() if c["is_tech"] == "1"]
    groups: dict[str, list[dict]] = defaultdict(list)
    for c in cs:
        groups["tech: " + ("authorized reseller" if c["vendor_role"] == "authorized_reseller" else "prime / direct")].append(c)
        groups["tech: " + ("GSA schedule holder" if c["gsa_mas_holder"] == "1" else "no GSA schedule")].append(c)
        groups["tech: " + ("multiple award" if c["award_structure"].startswith("multiple") else "single award")].append(c)
    print({k: len(v) for k, v in groups.items()})
    rows = grouped_estimates("vendors", dict(groups))
    write_csv(RESULTS / "smm_by_vendor_type.csv", rows)


# --------------------------------------------------------------------------------------
# Step 8: counterfactuals
# --------------------------------------------------------------------------------------

LEVERS = {
    # scenario: (description, function(theta) -> theta)
    "lifecycle scoring": ("Award weighs later costs more: designer share halved (Model 10: g* ∝ 1−φ; "
                          "φ from 0.4 to 0.7 halves 1−φ)", lambda t: {**t, "pi_d": t["pi_d"] * 0.5}),
    "portability": ("Data rights and transition help halve the effect of dependence on margin and hazard",
                    lambda t: {**t, "psi": t["psi"] * 0.5, "rho": t["rho"] * 0.5}),
    "rate cards": ("Pre-priced changes: no margin escalation with dependence",
                   lambda t: {**t, "psi": 1e-6}),
    "all three": ("Lifecycle scoring + portability + rate cards",
                  lambda t: {**t, "pi_d": t["pi_d"] * 0.5, "psi": 1e-6, "rho": t["rho"] * 0.5}),
}


def cmd_counterfactuals() -> None:
    est = json.loads((RESULTS / "smm_estimates.json").read_text())
    data = smm.sector_data()
    rng = random.Random(53)
    rows = []
    for name, r in est.items():
        if name not in data or "u" not in r:
            continue
        cs = data[name]
        _, _, shares = smm.observed(cs, rng)
        p = smm.Problem(cs, {k: 0 for k in smm.MOMENTS}, {k: 1 for k in smm.MOMENTS}, shares)
        draws = [r["u"]] + [[x + (s or 0) * rng.gauss(0, 1) for x, s in zip(r["u"], r["se_unconstrained"])]
                            for _ in range(10)]

        def outcome(th, seed):
            sim = smm.generate(th, p.structure, shares, seed)
            return (statistics.mean(c["n"] for c in sim), statistics.mean(c["value"] for c in sim))

        for lever, (desc, f) in LEVERS.items():
            dn, dv = [], []
            for i, u in enumerate(draws):
                th = smm.to_theta(u)
                b = [outcome(th, s) for s in (11, 12)]
                c = [outcome(f(th), s) for s in (11, 12)]
                bn, bv = statistics.mean(x[0] for x in b), statistics.mean(x[1] for x in b)
                cn, cv = statistics.mean(x[0] for x in c), statistics.mean(x[1] for x in c)
                dn.append(100 * (cn - bn) / bn if bn else 0)
                dv.append(100 * (cv - bv) / bv if bv else 0)
            point_n, point_v = dn[0], dv[0]
            sn, sv_ = sorted(dn[1:]), sorted(dv[1:])
            rows.append({"sector": name, "lever": lever, "description": desc,
                         "pct_change_amendments": round(point_n, 1),
                         "pct_change_amendments_lo": round(sn[0], 1), "pct_change_amendments_hi": round(sn[-1], 1),
                         "pct_change_amendment_value": round(point_v, 1),
                         "pct_change_amendment_value_lo": round(sv_[0], 1),
                         "pct_change_amendment_value_hi": round(sv_[-1], 1)})
            print(f"[counterfactual] {name:34} {lever:18} amendments {point_n:+6.1f}%  value {point_v:+6.1f}%", flush=True)
    write_csv(RESULTS / "policy_counterfactuals.csv", rows)


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    fn = {"validate": cmd_validate, "channels": cmd_channels, "vendors": cmd_vendors,
          "counterfactuals": cmd_counterfactuals}.get(cmd)
    if not fn:
        print(__doc__)
        return 1
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "predictions.json").write_text(json.dumps(PREDICTIONS, indent=1))
    fn()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
