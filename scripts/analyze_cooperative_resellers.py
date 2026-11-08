#!/usr/bin/env python3
"""Cooperative purchasing, vendor vs. reseller, and certification-grade analysis.

Inputs (from ``normalize_and_classify.py``):
  data/processed/contracts_normalized.csv
  data/processed/cooperative_sales.csv
  data/processed/reseller_relationships.csv

Output:
  data/processed/cooperative_reseller_results.json
"""

from __future__ import annotations

import csv
import json
import math
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from analyze_tech_impact import compute_metrics, fit_logistic_regression, load_contracts

PROCESSED = Path("data/processed")
CERT_ORDER = [
    "minority_or_women_owned", "disadvantaged_business", "veteran_owned",
    "small_business", "not_certified", "not_reported",
]


def rule(title: str) -> None:
    print("\n" + "=" * 92)
    print(f" {title}")
    print("=" * 92)


def metrics_table(contracts: list[dict[str, Any]], key: str, min_n: int = 1,
                  order: list[str] | None = None) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for c in contracts:
        groups[c.get(key) or "(none)"].append(c)
    names = order or sorted(groups, key=lambda k: -len(groups[k]))
    out: dict[str, Any] = {}
    print(f"{key:<28} | {'Contracts':>9} | {'Amended':>8} | {'Rate %':>6} | {'Net growth %':>12} | {'Median growth %':>15}")
    print("-" * 92)
    for name in names:
        rows = groups.get(name, [])
        if len(rows) < min_n:
            continue
        m = compute_metrics(rows)
        out[name] = m
        print(f"{name:<28} | {m['total_contracts']:>9,} | {m['amended_contracts']:>8,} | "
              f"{m['amendment_rate_pct']:>6.1f} | {m['net_portfolio_growth_pct']:>12.1f} | {m['median_cost_growth_pct']:>15.1f}")
    return out


def run_logit(contracts: list[dict[str, Any]], label: str, max_n: int = 40000) -> dict[str, Any]:
    reg = [c for c in contracts if c["initial_award_val"] > 0]
    # Drop jurisdictions with no variation in the outcome (perfect separation).
    by_j: dict[str, list[int]] = defaultdict(list)
    for c in reg:
        by_j[c["jurisdiction"]].append(c["is_amended"])
    keep = {j for j, ys in by_j.items() if 0 < sum(ys) < len(ys) and len(ys) >= 200}
    reg = [c for c in reg if c["jurisdiction"] in keep]
    if not reg:
        return {}
    ref = max(keep, key=lambda j: len(by_j[j]))
    fe = sorted(keep - {ref})
    stride = max(1, len(reg) // max_n)
    sample = reg[::stride]

    certs = ["minority_or_women_owned", "disadvantaged_business", "veteran_owned", "small_business", "not_reported"]
    channels = ["cooperative_horizontal", "cooperative_vertical_downward", "cooperative_vertical_upward",
                "cooperative_unknown", "central_state_contract"]
    names = ["Intercept", "is_tech"] + channels + ["is_reseller", "multiple_award",
                                                    "gsa_mas_holder", "state_vehicle_prime"]
    names += [f"cert_{c}" for c in certs]
    names += ["log10_initial_award", "log10_duration_days"] + [f"jurisdiction_{j}" for j in fe]

    # Drop indicator columns that never vary in the sample (singular design).
    X: list[list[float]] = []
    y: list[float] = []
    for c in sample:
        row = [
            1.0,
            float(c["is_tech"]),
        ]
        row += [1.0 if c["procurement_channel"] == ch else 0.0 for ch in channels]
        row += [1.0 if c["vendor_role"] == "authorized_reseller" else 0.0,
                1.0 if c["n_contractors"] > 1 else 0.0,
                float(c["gsa_mas_holder"]),
                1.0 if c["qualification_tier"] == "state_vehicle_prime" else 0.0]
        row += [1.0 if c["vendor_certification"] == k else 0.0 for k in certs]
        row += [math.log10(max(c["initial_award_val"], 1.0)), math.log10(max(c["duration_days"], 1.0))]
        row += [1.0 if c["jurisdiction"] == j else 0.0 for j in fe]
        X.append(row)
        y.append(float(c["is_amended"]))
    # Keep the intercept, continuous terms, and indicators with >= 10 amended AND >= 10
    # non-amended contracts among those flagged (avoids quasi-separation blow-ups).
    def usable(i: int) -> bool:
        if i == 0 or names[i].startswith("log10_"):
            return True
        pos = sum(1 for r, yy in zip(X, y) if r[i] == 1.0 and yy == 1.0)
        neg = sum(1 for r, yy in zip(X, y) if r[i] == 1.0 and yy == 0.0)
        return pos >= 10 and neg >= 10
    active = [i for i in range(len(names)) if usable(i)]
    dropped = [names[i] for i in range(len(names)) if i not in active]
    X = [[r[i] for i in active] for r in X]
    names = [names[i] for i in active]

    res = fit_logistic_regression(X, y, names)
    res["label"] = label
    res["dropped_sparse_terms"] = dropped
    res["reference_jurisdiction"] = ref
    print(f"\n{label}  (N = {res['n_obs']:,}; reference jurisdiction = {ref}; cert reference = not_certified)")
    if dropped:
        print(f"  dropped sparse terms: {', '.join(dropped)}")
    print(f"{'Feature':<36} | {'Coef':>8} | {'SE':>7} | {'z':>7} | {'p':>7} | {'OR':>7} | 95% CI")
    print("-" * 92)
    for r in res["coefficients"]:
        p = "<0.001" if r["p_value"] < 0.001 else f"{r['p_value']:.3f}"
        print(f"{r['feature']:<36} | {r['coef']:>8.3f} | {r['std_err']:>7.3f} | {r['z_stat']:>7.2f} | {p:>7} | "
              f"{r['odds_ratio']:>7.3f} | [{r['ci_95'][0]:.2f}, {r['ci_95'][1]:.2f}]")
    return res


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def share_table(rows: list[dict[str, str]], key: str, amount: str = "sales") -> dict[str, Any]:
    tot = sum(float(r[amount] or 0) for r in rows)
    agg: Counter[str] = Counter()
    for r in rows:
        agg[r[key] or "(none)"] += float(r[amount] or 0)
    return {k: {"sales": round(v, 2), "share_pct": round(100 * v / tot, 2) if tot else 0.0}
            for k, v in agg.most_common()}


def print_shares(title: str, table: dict[str, Any]) -> None:
    print(f"\n{title}")
    for k, v in table.items():
        print(f"  {k:<34} ${v['sales']:>18,.0f}  {v['share_pct']:>6.2f}%")


def main() -> int:
    all_contracts = load_contracts(PROCESSED / "contracts_normalized.csv")
    # Amendment outcomes only where the ledger records amendment history (drops Baton Rouge's
    # snapshot PO ledger and NYC SCA's change-order-only file).
    contracts = [c for c in all_contracts if c["amendment_observable"] == 1]
    print(f"Loaded {len(all_contracts):,} contracts; {len(contracts):,} with observable amendment history",
          file=sys.stderr)
    results: dict[str, Any] = {}

    # ---------------- A. Coverage: states & levels of government -------------------------
    rule("A. COVERAGE: JURISDICTIONS BY STATE AND LEVEL OF GOVERNMENT")
    cov: dict[str, Any] = {}
    by_j: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for c in all_contracts:
        by_j[c["jurisdiction"]].append(c)
    print("(Amend % shown as n/a where the ledger has no amendment history)")
    print(f"{'Jurisdiction':<20} | {'State':<5} | {'Level':<17} | {'Contracts':>9} | {'Amend %':>7} | {'Tech %':>6}")
    print("-" * 92)
    for j, rows in sorted(by_j.items(), key=lambda kv: -len(kv[1])):
        m = compute_metrics(rows)
        tech = sum(r["is_tech"] for r in rows) / len(rows) * 100
        observable = rows[0]["amendment_observable"] == 1
        cov[j] = {"state": rows[0]["state"], "gov_level": rows[0]["gov_level"], **m,
                  "tech_share_pct": round(tech, 2), "amendment_observable": int(observable)}
        rate = f"{m['amendment_rate_pct']:>7.1f}" if observable else f"{'n/a':>7}"
        print(f"{j:<20} | {rows[0]['state']:<5} | {rows[0]['gov_level']:<17} | {len(rows):>9,} | "
              f"{rate} | {tech:>6.1f}")
    results["coverage"] = cov
    print()
    results["by_gov_level"] = metrics_table(contracts, "gov_level")

    # ---------------- B. Procurement channel / cooperative vehicle ------------------------
    rule("B. AMENDMENT OUTCOMES BY PROCUREMENT CHANNEL: HORIZONTAL VS. VERTICAL COOPERATION")
    print("horizontal = peers pooling (states via NASPO; locals via Sourcewell/OMNIA/TIPS...)")
    print("vertical_downward = lower level piggybacks on higher level's contract (locals on state")
    print("  contracts, states/locals on GSA schedules); vertical_upward = state on a local consortium;")
    print("central = state agency on its own state's master contract (not cooperative)\n")
    results["by_channel_all"] = metrics_table(contracts, "procurement_channel")
    tech = [c for c in contracts if c["is_tech"] == 1]
    print("\nTech contracts only:")
    results["by_channel_tech"] = metrics_table(tech, "procurement_channel")
    print("\nBy cooperative vehicle (all contracts, n >= 20):")
    results["by_coop_vehicle"] = metrics_table(
        [c for c in contracts if c["coop_vehicle"]], "coop_vehicle", min_n=20)
    print("\nVehicle x direction x buyer level (counts):")
    vd = Counter((c["coop_vehicle"], c["coop_direction"], c["gov_level"]) for c in all_contracts if c["coop_vehicle"])
    results["vehicle_direction_counts"] = [
        {"coop_vehicle": v, "coop_direction": d, "buyer_level": b, "contracts": n} for (v, d, b), n in vd.most_common()
    ]
    for (v, d, b), n in vd.most_common(20):
        print(f"  {v:<24} {d:<18} {b:<18} {n:>7,}")
    wa = [c for c in contracts if c["jurisdiction"] == "washington_state"]
    print("\nWashington State only (cooperative flags from WA IT Contracts reports):")
    results["by_channel_washington"] = metrics_table(wa, "procurement_channel")

    # ---------------- C. Vendors vs. resellers -------------------------------------------
    rule("C. PRIME/DIRECT VENDORS VS. AUTHORIZED RESELLERS")
    results["by_vendor_role_all"] = metrics_table(contracts, "vendor_role")
    print("\nTech contracts only:")
    results["by_vendor_role_tech"] = metrics_table(tech, "vendor_role")
    print("\nTech contracts by subsector x vendor role:")
    sub_role: dict[str, Any] = {}
    for sub in ("software_saas", "hardware_telecom", "it_services", "tech_general"):
        print(f"  [{sub}]")
        sub_role[sub] = metrics_table([c for c in tech if c["tech_subsector"] == sub], "vendor_role")
    results["by_subsector_vendor_role"] = sub_role

    # ---------------- D. Certification grades --------------------------------------------
    rule("D. VENDOR CERTIFICATION GRADES (jurisdictions that report grades AND have amendment variation)")
    # Baton Rouge reports DBE/minority/veteran flags but its ledger has no amendment history.
    varied = {j for j, m in cov.items() if m["amendment_observable"] and 0.5 < m["amendment_rate_pct"] < 99.5}
    reported = [c for c in contracts if c["vendor_certification"] != "not_reported" and c["jurisdiction"] in varied]
    print("Jurisdictions included:", ", ".join(sorted({c["jurisdiction"] for c in reported})))
    results["by_certification"] = metrics_table(reported, "vendor_certification", order=CERT_ORDER[:-1])
    print("\nCertification x vendor role:")
    cr: dict[str, Any] = {}
    for role in ("prime_or_direct", "authorized_reseller"):
        print(f"  [{role}]")
        cr[role] = metrics_table([c for c in reported if c["vendor_role"] == role], "vendor_certification",
                                 order=CERT_ORDER[:-1])
    results["by_certification_vendor_role"] = cr

    # ---------------- E. Econometric models ----------------------------------------------
    rule("E. LOGISTIC REGRESSION: P(AMENDED) WITH CHANNEL, RESELLER AND CERTIFICATION TERMS")
    results["logit_pooled"] = run_logit(contracts, "Pooled model, jurisdiction fixed effects")
    results["logit_washington"] = run_logit(wa, "Washington State FY2021-FY2025")

    # ---------------- F. Cooperative sales -----------------------------------------------
    rule("F. COOPERATIVE-CONTRACT SALES: WHO BUYS, AND THROUGH WHOM")
    sales = load_csv(PROCESSED / "cooperative_sales.csv")
    coop: dict[str, Any] = {}
    for program in sorted({r["program"] for r in sales}):
        rows = [r for r in sales if r["program"] == program]
        t = share_table(rows, "customer_type")
        coop[program] = {"total_sales": round(sum(float(r["sales"] or 0) for r in rows), 2), "by_customer_type": t}
        print_shares(f"[{program}] sales by customer type (total ${coop[program]['total_sales']:,.0f})", t)
    print("\nCooperative sales by direction (buyer level vs. level that set up the vehicle):")
    for program in sorted({r["program"] for r in sales}):
        rows = [r for r in sales if r["program"] == program]
        coop[program]["by_direction"] = share_table(rows, "coop_direction")
        print_shares(f"[{program}]", coop[program]["by_direction"])
    tx = [r for r in sales if r["program"] == "texas_dir"]
    if tx:
        coop["texas_dir"]["by_sales_channel"] = share_table(tx, "sales_channel")
        print_shares("[texas_dir] direct-from-prime vs. via authorized reseller", coop["texas_dir"]["by_sales_channel"])
        coop["texas_dir"]["by_vendor_role"] = share_table(tx, "vendor_role")
        via = [r for r in tx if r["sales_channel"] == "via_reseller"]
        direct = [r for r in tx if r["sales_channel"] == "direct_prime"]
        coop["texas_dir"]["prime_cert_direct_sales"] = share_table(direct, "vendor_certification")
        coop["texas_dir"]["prime_cert_reseller_sales"] = share_table(via, "vendor_certification")
        coop["texas_dir"]["reseller_cert_reseller_sales"] = share_table(via, "reseller_certification")
        print_shares("[texas_dir] HUB grade of PRIME on direct sales", coop["texas_dir"]["prime_cert_direct_sales"])
        print_shares("[texas_dir] HUB grade of PRIME on reseller sales", coop["texas_dir"]["prime_cert_reseller_sales"])
        print_shares("[texas_dir] HUB grade of RESELLER on reseller sales", coop["texas_dir"]["reseller_cert_reseller_sales"])
        # HUB pass-through: non-HUB prime whose sale is booked through a HUB reseller
        pass_through = sum(float(r["sales"]) for r in via
                           if r["vendor_certification"] == "not_certified"
                           and r["reseller_certification"] in ("minority_or_women_owned", "veteran_owned"))
        hub_any = sum(float(r["sales"]) for r in tx
                      if r["vendor_certification"] in ("minority_or_women_owned", "veteran_owned")
                      or r["reseller_certification"] in ("minority_or_women_owned", "veteran_owned"))
        coop["texas_dir"]["hub_pass_through_sales"] = round(pass_through, 2)
        coop["texas_dir"]["hub_any_sales"] = round(hub_any, 2)
        print(f"\n  HUB-credited sales (prime or reseller is HUB):        ${hub_any:,.0f}")
        print(f"  ...of which non-HUB prime sold via a HUB reseller:    ${pass_through:,.0f} "
              f"({100 * pass_through / hub_any if hub_any else 0:.1f}%)")
        by_year: dict[str, dict[str, float]] = defaultdict(lambda: {"direct_prime": 0.0, "via_reseller": 0.0})
        for r in tx:
            by_year[r["fiscal_year"]][r["sales_channel"]] += float(r["sales"] or 0)
        coop["texas_dir"]["reseller_share_by_year"] = {
            y: round(100 * v["via_reseller"] / (v["via_reseller"] + v["direct_prime"]), 2)
            for y, v in sorted(by_year.items()) if v["via_reseller"] + v["direct_prime"] > 0
        }
        print("\n  (FY2026+ comes from DIR's new Vendor Sales Reporting system; the drop in reseller share"
              "\n   may partly reflect a reporting change.)")
        print("  Reseller share of Texas DIR sales by fiscal year:",
              ", ".join(f"{y}: {s:.1f}%" for y, s in coop["texas_dir"]["reseller_share_by_year"].items()))
    wam = [r for r in sales if r["program"] == "washington_des_master"]
    if wam:
        coop["washington_des_master"]["by_vendor_certification"] = share_table(wam, "vendor_certification")
        print_shares("[washington_des_master] sales by vendor certification",
                     coop["washington_des_master"]["by_vendor_certification"])
    results["cooperative_sales"] = coop

    # ---------------- G. Reseller networks -----------------------------------------------
    rule("G. PRIME VENDOR -> AUTHORIZED RESELLER NETWORKS")
    rel = load_csv(PROCESSED / "reseller_relationships.csv")
    net: dict[str, Any] = {}
    for src in sorted({r["source"] for r in rel}):
        rows = [r for r in rel if r["source"] == src]
        per_prime = Counter(r["prime_vendor"] for r in rows)
        per_res = Counter(r["reseller"] for r in rows)
        net[src] = {
            "relationships": len(rows),
            "primes": len(per_prime),
            "resellers": len(per_res),
            "median_resellers_per_prime": statistics.median(per_prime.values()),
            "top_primes_by_reseller_count": per_prime.most_common(10),
            "top_resellers_by_prime_count": per_res.most_common(10),
            "reseller_certification": dict(Counter(r["reseller_certification"] for r in rows)),
            "prime_certification": dict(Counter(r["prime_certification"] for r in rows)),
        }
        n = net[src]
        print(f"\n[{src}] {n['relationships']:,} relationships, {n['primes']:,} primes, {n['resellers']:,} resellers "
              f"(median {n['median_resellers_per_prime']} resellers/prime)")
        print("  Top primes:   " + "; ".join(f"{k} ({v})" for k, v in n["top_primes_by_reseller_count"][:6]))
        print("  Top resellers:" + "; ".join(f"{k} ({v})" for k, v in n["top_resellers_by_prime_count"][:6]))
        if src.startswith("texas"):
            same = sum(1 for r in rows if r["prime_cert_raw"] == r["reseller_cert_raw"])
            n["prime_reseller_hub_fields_identical_pct"] = round(100 * same / len(rows), 1)
            print(f"  Prime HUB grades:    {n['prime_certification']}")
            print(f"  Reseller HUB grades: {n['reseller_certification']}")
            print(f"  NOTE: prime and reseller HUB fields are identical on "
                  f"{n['prime_reseller_hub_fields_identical_pct']}% of rows in this source; use the sales data "
                  f"(section F) for prime-vs-reseller grade comparisons.")
    results["reseller_networks"] = net

    # ---------------- H. Award structure -------------------------------------------------
    rule("H. AWARD STRUCTURE: SINGLE VS. MULTIPLE CONTRACTORS, PRIME-DIRECT VS. RESELLER")
    print("Contract ledgers (multiple_award = >1 distinct contractor on the same contract ID;")
    print("suffix = role of the listed vendor):")
    results["by_award_structure"] = metrics_table(contracts, "award_structure")
    print("\nTech contracts only:")
    results["by_award_structure_tech"] = metrics_table(tech, "award_structure")
    awards = load_csv(PROCESSED / "award_structure.csv")
    aw: dict[str, Any] = {}
    print("\nCooperative vehicles (award_structure.csv):")
    for src in sorted({r["source"] for r in awards}):
        rows = [r for r in awards if r["source"] == src]
        cnt = Counter(r["award_structure"] for r in rows)
        sizes = [int(r["n_primes_in_solicitation"]) for r in rows if r["n_primes_in_solicitation"]]
        res = [int(r["n_resellers"]) for r in rows if r["n_resellers"] not in ("", None)]
        aw[src] = {
            "contracts": len(rows),
            "by_structure": dict(cnt),
            "median_primes_per_solicitation": statistics.median(sizes) if sizes else None,
            "share_contracts_with_resellers_pct": round(100 * sum(1 for x in res if x > 0) / len(res), 1) if res else None,
            "median_resellers_when_any": statistics.median([x for x in res if x > 0]) if any(res) else None,
        }
        print(f"\n  [{src}] {len(rows):,} contracts; median primes/solicitation = "
              f"{aw[src]['median_primes_per_solicitation']}; with resellers = {aw[src]['share_contracts_with_resellers_pct']}%")
        for k, v in cnt.most_common():
            print(f"    {k:<44} {v:>7,}  ({100 * v / len(rows):.1f}%)")
    results["award_structure_vehicles"] = aw

    # ---------------- I. Vendor qualifications (covariates) --------------------------------
    rule("I. VENDOR QUALIFICATIONS: CONTRACT VEHICLES HELD (GSA MAS, VA FSS, STATE VEHICLES)")
    results["by_qualification_tier"] = metrics_table(contracts, "qualification_tier")
    print("\nTech contracts only:")
    results["by_qualification_tier_tech"] = metrics_table(tech, "qualification_tier")
    print("\nGSA MAS / VA FSS holders by holder role (NAICS):")
    results["by_fss_holder_role"] = metrics_table(
        [c for c in contracts if c["qualification_tier"] == "federal_schedule_holder"], "fss_holder_role")
    print("\nQualification tier x vendor role:")
    qr: dict[str, Any] = {}
    for role in ("prime_or_direct", "authorized_reseller"):
        print(f"  [{role}]")
        qr[role] = metrics_table([c for c in contracts if c["vendor_role"] == role], "qualification_tier")
    results["by_qualification_vendor_role"] = qr

    out = PROCESSED / "cooperative_reseller_results.json"
    with out.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nSaved {out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
