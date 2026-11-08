#!/usr/bin/env python3
"""Empirical analysis and econometric modeling of Tech vs. Non-Tech contract change orders."""

from __future__ import annotations

import csv
import json
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


def mat_mul(A: list[list[float]], B: list[list[float]]) -> list[list[float]]:
    n, m, p = len(A), len(B), len(B[0])
    res = [[0.0] * p for _ in range(n)]
    for i in range(n):
        for k in range(m):
            aik = A[i][k]
            if aik != 0:
                for j in range(p):
                    res[i][j] += aik * B[k][j]
    return res


def mat_vec(A: list[list[float]], x: list[float]) -> list[float]:
    return [sum(a * b for a, b in zip(row, x)) for row in A]


def mat_transpose(A: list[list[float]]) -> list[list[float]]:
    return [list(col) for col in zip(*A)]


def mat_inv(A: list[list[float]]) -> list[list[float]]:
    n = len(A)
    aug = [row[:] + [1.0 if i == j else 0.0 for j in range(n)] for i, row in enumerate(A)]
    for i in range(n):
        pivot = aug[i][i]
        if abs(pivot) < 1e-12:
            for k in range(i + 1, n):
                if abs(aug[k][i]) > abs(pivot):
                    aug[i], aug[k] = aug[k], aug[i]
                    pivot = aug[i][i]
                    break
        if abs(pivot) < 1e-12:
            raise ValueError("Matrix is singular")
        for j in range(2 * n):
            aug[i][j] /= pivot
        for k in range(n):
            if k != i:
                factor = aug[k][i]
                if factor != 0:
                    for j in range(2 * n):
                        aug[k][j] -= factor * aug[i][j]
    return [row[n:] for row in aug]


def sigmoid(z: float) -> float:
    if z < -35:
        return 1e-15
    if z > 35:
        return 1.0 - 1e-15
    return 1.0 / (1.0 + math.exp(-z))


def normal_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def fit_logistic_regression(
    X: list[list[float]],
    y: list[float],
    feature_names: list[str],
    max_iter: int = 25,
    tol: float = 1e-6,
) -> dict[str, Any]:
    n = len(X)
    p = len(X[0])
    beta = [0.0] * p

    for iteration in range(max_iter):
        p_vec = [sigmoid(sum(X[i][j] * beta[j] for j in range(p))) for i in range(n)]
        weights = [max(pi * (1.0 - pi), 1e-6) for pi in p_vec]

        # Compute X^T * W * X and X^T * (y - p)
        XtWX = [[0.0] * p for _ in range(p)]
        score = [0.0] * p

        for i in range(n):
            err = y[i] - p_vec[i]
            wi = weights[i]
            xi = X[i]
            for j in range(p):
                score[j] += xi[j] * err
                w_xij = wi * xi[j]
                for k in range(j, p):
                    val = w_xij * xi[k]
                    XtWX[j][k] += val
                    if j != k:
                        XtWX[k][j] += val

        # L2 ridge regularization for numerical stability
        for j in range(p):
            XtWX[j][j] += 1e-4

        try:
            cov = mat_inv(XtWX)
        except ValueError:
            break

        delta = mat_vec(cov, score)
        max_delta = max(abs(d) for d in delta)
        for j in range(p):
            beta[j] += delta[j]

        if max_delta < tol:
            break

    # Final covariance
    p_vec = [sigmoid(sum(X[i][j] * beta[j] for j in range(p))) for i in range(n)]
    weights = [max(pi * (1.0 - pi), 1e-6) for pi in p_vec]
    XtWX = [[0.0] * p for _ in range(p)]
    for i in range(n):
        wi = weights[i]
        xi = X[i]
        for j in range(p):
            w_xij = wi * xi[j]
            for k in range(j, p):
                val = w_xij * xi[k]
                XtWX[j][k] += val
                if j != k:
                    XtWX[k][j] += val
    for j in range(p):
        XtWX[j][j] += 1e-4
    cov = mat_inv(XtWX)

    results = []
    for j in range(p):
        se = math.sqrt(max(cov[j][j], 1e-12))
        z = beta[j] / se
        p_val = 2.0 * (1.0 - normal_cdf(abs(z)))
        odds_ratio = math.exp(beta[j])
        ci_lower = math.exp(beta[j] - 1.96 * se)
        ci_upper = math.exp(beta[j] + 1.96 * se)
        results.append({
            "feature": feature_names[j],
            "coef": round(beta[j], 4),
            "std_err": round(se, 4),
            "z_stat": round(z, 2),
            "p_value": p_val,
            "odds_ratio": round(odds_ratio, 4),
            "ci_95": (round(ci_lower, 4), round(ci_upper, 4)),
        })

    return {"n_obs": n, "coefficients": results}


def fit_ols(
    X: list[list[float]],
    y: list[float],
    feature_names: list[str],
) -> dict[str, Any]:
    n = len(X)
    p = len(X[0])

    XtX = [[0.0] * p for _ in range(p)]
    Xty = [0.0] * p

    for i in range(n):
        xi = X[i]
        yi = y[i]
        for j in range(p):
            Xty[j] += xi[j] * yi
            xij = xi[j]
            for k in range(j, p):
                val = xij * xi[k]
                XtX[j][k] += val
                if j != k:
                    XtX[k][j] += val

    for j in range(p):
        XtX[j][j] += 1e-6
    cov = mat_inv(XtX)
    beta = mat_vec(cov, Xty)

    residuals = [y[i] - sum(X[i][j] * beta[j] for j in range(p)) for i in range(n)]
    rss = sum(r * r for r in residuals)
    y_mean = sum(y) / n
    tss = sum((yi - y_mean) ** 2 for yi in y)
    r_squared = 1.0 - (rss / tss) if tss > 0 else 0.0

    sigma2 = rss / (n - p) if n > p else 1.0
    results = []
    for j in range(p):
        se = math.sqrt(max(cov[j][j] * sigma2, 1e-12))
        t = beta[j] / se
        p_val = 2.0 * (1.0 - normal_cdf(abs(t)))
        results.append({
            "feature": feature_names[j],
            "coef": round(beta[j], 4),
            "std_err": round(se, 4),
            "t_stat": round(t, 2),
            "p_value": p_val,
        })

    return {"n_obs": n, "r_squared": round(r_squared, 4), "coefficients": results}


def load_contracts(csv_path: Path) -> list[dict[str, Any]]:
    contracts: list[dict[str, Any]] = []
    with csv_path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            try:
                orig_val = float(r.get("initial_award_val") or 0)
                final_val = float(r.get("final_award_val") or 0)
                delta_val = float(r.get("delta_val") or 0)
                pct_growth = float(r.get("pct_growth") or 0)
                is_amended = int(r.get("is_amended") or 0)
                amend_count = int(r.get("amendment_count") or 0)
                is_tech = int(r.get("is_tech") or 0)
                duration_str = r.get("duration_days")
                duration = float(duration_str) if duration_str else 0.0
            except (ValueError, TypeError):
                continue

            contracts.append({
                "jurisdiction": r.get("jurisdiction", ""),
                "contract_id": r.get("contract_id", ""),
                "title_desc": r.get("title_desc", ""),
                "department": r.get("department", ""),
                "vendor_name": r.get("vendor_name", ""),
                "commodity_or_type": r.get("commodity_or_type", ""),
                "is_tech": is_tech,
                "tech_subsector": r.get("tech_subsector", "non_tech"),
                "tech_domain": r.get("tech_domain", "non_tech"),
                "initial_award_val": orig_val,
                "final_award_val": final_val,
                "delta_val": delta_val,
                "pct_growth": pct_growth,
                "amendment_count": amend_count,
                "is_amended": is_amended,
                "duration_days": duration,
                "state": r.get("state", ""),
                "gov_level": r.get("gov_level", ""),
                "coop_vehicle": r.get("coop_vehicle", ""),
                "coop_direction": r.get("coop_direction", ""),
                "n_contractors": int(r.get("n_contractors") or 1),
                "award_structure": r.get("award_structure", ""),
                "amendment_observable": int(r.get("amendment_observable") or 1),
                "qualification_tier": r.get("qualification_tier", "none_observed"),
                "gsa_mas_holder": int(r.get("gsa_mas_holder") or 0),
                "n_vehicles_held": int(r.get("n_vehicles_held") or 0),
                "fss_holder_role": r.get("fss_holder_role", ""),
                "procurement_channel": r.get("procurement_channel", "direct_or_unknown"),
                "vendor_role": r.get("vendor_role", "unknown"),
                "vendor_certification": r.get("vendor_certification", "not_reported"),
            })
    return contracts


def compute_metrics(records: list[dict[str, Any]]) -> dict[str, Any]:
    total_count = len(records)
    if total_count == 0:
        return {}
    amended = [r for r in records if r["is_amended"] == 1]
    amend_rate = (len(amended) / total_count) * 100.0

    orig_dollars = sum(r["initial_award_val"] for r in records)
    delta_dollars = sum(r["delta_val"] for r in records)
    net_growth = (delta_dollars / orig_dollars * 100.0) if orig_dollars > 0 else 0.0

    # Filter for substantial amended contracts >$1,000
    amended_gt_1k = [
        r["pct_growth"] for r in amended
        if r["initial_award_val"] >= 1000 and r["pct_growth"] > -99
    ]
    median_growth = statistics.median(amended_gt_1k) if amended_gt_1k else 0.0
    mean_growth = statistics.mean(amended_gt_1k) if amended_gt_1k else 0.0

    return {
        "total_contracts": total_count,
        "amended_contracts": len(amended),
        "amendment_rate_pct": round(amend_rate, 2),
        "orig_dollars": orig_dollars,
        "added_dollars": delta_dollars,
        "net_portfolio_growth_pct": round(net_growth, 2),
        "median_cost_growth_pct": round(median_growth, 2),
        "mean_cost_growth_pct": round(mean_growth, 2),
    }


def analyze_case_studies(contracts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # Top tech overruns
    tech_overruns = [
        r for r in contracts
        if r["is_tech"] == 1 and r["initial_award_val"] >= 50000 and r["delta_val"] >= 1000000
    ]
    tech_overruns.sort(key=lambda x: x["delta_val"], reverse=True)
    return tech_overruns[:15]


def main() -> int:
    csv_path = Path("data/processed/contracts_normalized.csv")
    if not csv_path.exists():
        print("Processed file not found. Running normalization...", file=sys.stderr)
        from normalize_and_classify import main as run_norm
        run_norm()

    print(f"Loading normalized contracts from {csv_path}...", file=sys.stderr)
    contracts = load_contracts(csv_path)
    print(f"Loaded {len(contracts):,} contracts.", file=sys.stderr)
    n_all = len(contracts)
    contracts = [r for r in contracts if r["amendment_observable"] == 1]
    print(f"Using {len(contracts):,} contracts whose ledgers record amendment history "
          f"(excluded {n_all - len(contracts):,} from Baton Rouge / NYC SCA).", file=sys.stderr)

    # 1. Overall Tech vs Non-Tech
    tech_contracts = [r for r in contracts if r["is_tech"] == 1]
    non_tech_contracts = [r for r in contracts if r["is_tech"] == 0]

    overall_tech = compute_metrics(tech_contracts)
    overall_non_tech = compute_metrics(non_tech_contracts)

    print("\n" + "=" * 78)
    print(" 1. OVERALL TECH VS. NON-TECH PROCUREMENT METRICS")
    print("=" * 78)
    print(f"{'Metric':<35} | {'Tech Contracts':<18} | {'Non-Tech Contracts':<18}")
    print("-" * 78)
    print(f"{'Total Contracts':<35} | {overall_tech['total_contracts']:<18,d} | {overall_non_tech['total_contracts']:<18,d}")
    print(f"{'Amended Contracts':<35} | {overall_tech['amended_contracts']:<18,d} | {overall_non_tech['amended_contracts']:<18,d}")
    print(f"{'Amendment Rate (%)':<35} | {overall_tech['amendment_rate_pct']:<18.2f}% | {overall_non_tech['amendment_rate_pct']:<18.2f}%")
    print(f"{'Initial Award Dollars':<35} | ${overall_tech['orig_dollars']:<17,.0f} | ${overall_non_tech['orig_dollars']:<17,.0f}")
    print(f"{'Added Amendment Dollars':<35} | ${overall_tech['added_dollars']:<17,.0f} | ${overall_non_tech['added_dollars']:<17,.0f}")
    print(f"{'Net Portfolio Cost Growth (%)':<35} | {overall_tech['net_portfolio_growth_pct']:<18.2f}% | {overall_non_tech['net_portfolio_growth_pct']:<18.2f}%")
    print(f"{'Median Cost Growth (Amended >$1k)':<35} | {overall_tech['median_cost_growth_pct']:<18.2f}% | {overall_non_tech['median_cost_growth_pct']:<18.2f}%")
    print(f"{'Mean Cost Growth (Amended >$1k)':<35} | {overall_tech['mean_cost_growth_pct']:<18.2f}% | {overall_non_tech['mean_cost_growth_pct']:<18.2f}%")

    # 2. Jurisdiction Breakdown
    jurisdiction_counts: dict[str, int] = defaultdict(int)
    for r in contracts:
        jurisdiction_counts[r["jurisdiction"]] += 1
    jurisdictions = sorted(jurisdiction_counts, key=lambda j: -jurisdiction_counts[j])
    print("\n" + "=" * 78)
    print(" 2. JURISDICTION COMPARISON: TECH VS. NON-TECH")
    print("=" * 78)
    jurisdiction_results = {}
    for j in jurisdictions:
        j_tech = [r for r in tech_contracts if r["jurisdiction"] == j]
        j_non_tech = [r for r in non_tech_contracts if r["jurisdiction"] == j]
        m_tech = compute_metrics(j_tech)
        m_non_tech = compute_metrics(j_non_tech)
        jurisdiction_results[j] = {"tech": m_tech, "non_tech": m_non_tech}
        if not m_tech or not m_non_tech:
            continue

        rel_diff = (
            ((m_tech["amendment_rate_pct"] - m_non_tech["amendment_rate_pct"]) / m_non_tech["amendment_rate_pct"] * 100.0)
            if m_non_tech.get("amendment_rate_pct")
            else 0.0
        )
        print(f"\n[{j.upper()}]")
        print(f"  Tech Amendment Rate:     {m_tech['amendment_rate_pct']:.1f}% ({m_tech['amended_contracts']:,}/{m_tech['total_contracts']:,})")
        print(f"  Non-Tech Amendment Rate: {m_non_tech['amendment_rate_pct']:.1f}% ({m_non_tech['amended_contracts']:,}/{m_non_tech['total_contracts']:,})")
        print(f"  Relative Amendment Risk: {rel_diff:+.1f}%")
        print(f"  Tech Net Cost Growth:    {m_tech['net_portfolio_growth_pct']:.1f}% vs Non-Tech: {m_non_tech['net_portfolio_growth_pct']:.1f}%")
        print(f"  Tech Mean Cost Growth:   {m_tech['mean_cost_growth_pct']:.1f}% vs Non-Tech: {m_non_tech['mean_cost_growth_pct']:.1f}%")

    # 3. Subsectors
    subsectors = ["software_saas", "hardware_telecom", "it_services", "tech_general", "non_tech"]
    print("\n" + "=" * 78)
    print(" 3. TECH SUBSECTOR BREAKDOWN")
    print("=" * 78)
    print(f"{'Subsector':<20} | {'Contracts':<10} | {'Amended':<10} | {'Amend %':<8} | {'Added Dollars':<16} | {'Mean Growth %':<12}")
    print("-" * 78)
    subsector_results = {}
    for sub in subsectors:
        sub_contracts = [r for r in contracts if r["tech_subsector"] == sub]
        m = compute_metrics(sub_contracts)
        subsector_results[sub] = m
        print(
            f"{sub:<20} | {m['total_contracts']:<10,d} | {m['amended_contracts']:<10,d} | "
            f"{m['amendment_rate_pct']:<7.1f}% | ${m['added_dollars']:<15,.0f} | {m['mean_cost_growth_pct']:<11.1f}%"
        )

    # 4. Program Domains
    domains = [
        "public_assistance", "general_enterprise_it", "health_care",
        "public_safety", "administration_finance", "transportation",
        "environment", "labor_workforce"
    ]
    print("\n" + "=" * 78)
    print(" 4. TECH CONTRACTS BY FUNCTIONAL PROGRAM DOMAIN")
    print("=" * 78)
    print(f"{'Program Domain':<24} | {'Contracts':<10} | {'Amended':<8} | {'Rate %':<7} | {'Added Dollars':<16} | {'Mean Growth %':<12}")
    print("-" * 78)
    domain_results = {}
    for dom in domains:
        dom_contracts = [r for r in tech_contracts if r["tech_domain"] == dom]
        m = compute_metrics(dom_contracts)
        domain_results[dom] = m
        print(
            f"{dom:<24} | {m['total_contracts']:<10,d} | {m['amended_contracts']:<8,d} | "
            f"{m['amendment_rate_pct']:<6.1f}% | ${m['added_dollars']:<15,.0f} | {m['mean_cost_growth_pct']:<11.1f}%"
        )

    # 5. Top Case Studies
    top_cases = analyze_case_studies(contracts)
    print("\n" + "=" * 78)
    print(" 5. NOTABLE TECH EXPANSION & OVERRUN CASE STUDIES ACROSS DOMAINS")
    print("=" * 78)
    for idx, c in enumerate(top_cases[:8], 1):
        print(f"{idx}. {c['vendor_name']} ({c['jurisdiction'].upper()}) - Domain: {c['tech_domain']}")
        print(f"   Department:  {c['department']}")
        print(f"   Description: {c['title_desc'][:65]}")
        print(f"   Original:    ${c['initial_award_val']:,.0f} -> Added: +${c['delta_val']:,.0f} (+{c['pct_growth']:.1f}% over {c['amendment_count']} amendments)\n")

    # 6. Econometric Regression Modeling
    print("=" * 78)
    print(" 6. ECONOMETRIC MODEL: LOGISTIC REGRESSION (AMENDMENT PROBABILITY)")
    print("=" * 78)

    # Prepare matrix X, y
    # Sample 40,000 contracts for fast IRLS convergence
    reg_contracts = [r for r in contracts if r["initial_award_val"] > 0]
    # Jurisdiction fixed effects for every jurisdiction with outcome variation (>=200 obs);
    # the largest such jurisdiction is the reference category.
    outcomes: dict[str, list[int]] = defaultdict(list)
    for r in reg_contracts:
        outcomes[r["jurisdiction"]].append(r["is_amended"])
    fe_pool = {j for j, ys in outcomes.items() if len(ys) >= 200 and 0 < sum(ys) < len(ys)}
    reg_contracts = [r for r in reg_contracts if r["jurisdiction"] in fe_pool]
    reference = max(fe_pool, key=lambda j: len(outcomes[j]))
    fe_juris = sorted(fe_pool - {reference})
    stride = max(1, len(reg_contracts) // 40000)
    sampled = reg_contracts[::stride]

    feature_names = ["Intercept", "is_tech", "log10_initial_award", "log10_duration_days"] + [
        f"jurisdiction_{j}" for j in fe_juris
    ]
    X_mat: list[list[float]] = []
    y_vec: list[float] = []

    for r in sampled:
        log_award = math.log10(max(r["initial_award_val"], 1.0))
        log_dur = math.log10(max(r["duration_days"], 1.0))
        X_mat.append([1.0, float(r["is_tech"]), log_award, log_dur] + [
            1.0 if r["jurisdiction"] == j else 0.0 for j in fe_juris
        ])
        y_vec.append(float(r["is_amended"]))

    logit_res = fit_logistic_regression(X_mat, y_vec, feature_names)

    logit_res["reference_jurisdiction"] = reference
    print(f"Logistic Regression Model (N = {logit_res['n_obs']:,} contracts; reference jurisdiction = {reference}):")
    print(f"{'Feature':<25} | {'Coef':<8} | {'SE':<8} | {'z':<6} | {'p-value':<8} | {'Odds Ratio':<10} | {'95% CI':<14}")
    print("-" * 88)
    for row in logit_res["coefficients"]:
        p_str = "<0.001" if row["p_value"] < 0.001 else f"{row['p_value']:.4f}"
        ci_str = f"[{row['ci_95'][0]:.2f}, {row['ci_95'][1]:.2f}]"
        print(
            f"{row['feature']:<25} | {row['coef']:<8.4f} | {row['std_err']:<8.4f} | "
            f"{row['z_stat']:<6.2f} | {p_str:<8} | {row['odds_ratio']:<10.4f} | {ci_str:<14}"
        )

    # Save summary results to JSON
    out_dir = Path("data/processed")
    out_dir.mkdir(parents=True, exist_ok=True)
    summary_data = {
        "overall": {"tech": overall_tech, "non_tech": overall_non_tech},
        "jurisdictions": jurisdiction_results,
        "subsectors": subsector_results,
        "program_domains": domain_results,
        "top_case_studies": top_cases[:10],
        "logistic_regression": logit_res,
    }
    with (out_dir / "tech_analysis_results.json").open("w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2)

    print(f"\nSaved structured analysis results to {out_dir / 'tech_analysis_results.json'}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
