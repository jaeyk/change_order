#!/usr/bin/env python3
"""Figures for the synthesis results (standard-library SVG). Run from the repository root:

    python3 synthesis/plot_synthesis.py

Outputs (synthesis/figures/):
  y1_estimates.svg       SMM estimates by sector: lock-in share of amendments and escalation, with intervals
  y4_documents.svg       what the amendment documents say about why contracts changed
  y3_counterfactuals.svg predicted change in amendment value under each policy lever, by sector
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "scripts"))
from make_figures import (BLUE, GRAY, GRAY_LIGHT, INK, INK2, INK3, ORANGE, AQUA, RULE, BAND,  # noqa: E402
                          SURFACE, SECTOR_LABEL, Svg)

RES = HERE / "results"
OUT = HERE / "figures"


def estimates_figure(path: Path) -> None:
    est = json.loads((RES / "smm_estimates.json").read_text())
    rows = sorted(est.values(), key=lambda r: -r["lockin_share"])
    W, top, rh, left = 1180, 140, 34, 280
    H = top + rh * len(rows) + 100
    svg = Svg(W, H, "Y1. Estimated lock-in by sector")
    svg.text(24, 36, "Y1. How much of each sector's amendment activity the lock-in mechanism explains", size=18,
             weight="bold")
    svg.text(24, 58, "Simulated method of moments, fitted to ten moments per sector (Chicago, Oregon ORPIN, Cook County). "
                     "Bars: 90% intervals from parameter draws.", size=12.5, fill=INK2)
    panels = [("lockin_share", "Lock-in share of amendments", "amendments that disappear when designers are switched off",
               -0.1, 0.5, [-0.1, 0, 0.1, 0.2, 0.3, 0.4, 0.5], "lockin_share_90"),
              ("psi", "Margin escalation ψ", "growth in amendment size per unit of dependence", 0, 2.0,
               [0, 0.5, 1.0, 1.5, 2.0], "psi_90")]
    pw = (W - left - 40) / 2
    for pi, (key, title, sub, lo, hi, ticks, ci) in enumerate(panels):
        x0 = left + pi * pw + 10
        x1 = x0 + pw - 50
        xm = lambda v: x0 + (min(max(v, lo), hi) - lo) / (hi - lo) * (x1 - x0)
        svg.text(x0, top - 40, title, size=13, weight="bold")
        svg.text(x0, top - 24, sub, size=11, fill=INK3)
        for t in ticks:
            svg.line(xm(t), top - 12, xm(t), top + rh * len(rows) - 8, stroke=RULE if t else INK3)
            svg.text(xm(t), top + rh * len(rows) + 8, f"{t:g}", size=10.5, fill=INK3, anchor="middle")
        for ri, r in enumerate(rows):
            y = top + ri * rh + rh / 2 - 6
            v = r["lockin_share"] if key == "lockin_share" else r["theta"]["psi"]
            lo_, hi_ = r[ci]
            svg.add(f'<rect x="{xm(lo_):.1f}" y="{y - 5}" width="{max(2, xm(hi_) - xm(lo_)):.1f}" height="10" rx="3" '
                    f'fill="{GRAY_LIGHT}"/>')
            svg.add(f'<circle cx="{xm(v):.1f}" cy="{y:.1f}" r="6" fill="{ORANGE}" stroke="{SURFACE}" stroke-width="2"/>')
            svg.text(min(xm(v) + 11, x1 + 30), y + 4, f"{v:.2f}", size=10.5, fill=INK2)
    for ri, r in enumerate(rows):
        y = top + ri * rh + rh / 2 - 6
        worst = max(((k, m["t"]) for k, m in r["moments"].items() if m["t"] is not None), key=lambda kv: abs(kv[1]))
        svg.text(24, y + 4, SECTOR_LABEL.get(r["sector"], r["sector"]), size=12)
        svg.text(left - 6, y + 4, f"n={r['contracts']:,}", size=10.5, fill=INK3, anchor="end")
    svg.text(24, H - 46, "Lock-in share = 1 − E[amendments | lock-in vendors switched off] / E[amendments]. Fit diagnostics "
                         "(objective, worst-fitting moment) are in smm_estimates.csv.", size=11, fill=INK3)
    svg.text(24, H - 28, "Parameters are estimated from aggregate patterns; they describe the data-generating process the "
                         "model needs, not the intent of any vendor.", size=11, fill=INK3)
    svg.save(path)


def counterfactual_figure(path: Path) -> None:
    p = RES / "policy_counterfactuals.csv"
    if not p.exists():
        return
    rows = list(csv.DictReader(p.open(encoding="utf-8")))
    sectors = list(dict.fromkeys(r["sector"] for r in rows))
    levers = list(dict.fromkeys(r["lever"] for r in rows))
    W, top, rh, left = 1180, 140, 30, 280
    H = top + rh * len(sectors) + 110
    svg = Svg(W, H, "Y3. Policy counterfactuals")
    svg.text(24, 36, "Y3. Predicted change in amendment value under each lever", size=18, weight="bold")
    svg.text(24, 58, "Percent change in total amendment value per contract vs. the fitted baseline, by sector. Bars: range "
                     "across parameter draws. Lever mappings are scenarios (see next_steps.md, step 8).", size=12.5,
             fill=INK2)
    pw = (W - left - 30) / len(levers)
    lo, hi = -60, 10
    for li, lev in enumerate(levers):
        x0 = left + li * pw + 8
        x1 = x0 + pw - 24
        xm = lambda v: x0 + (min(max(v, lo), hi) - lo) / (hi - lo) * (x1 - x0)
        svg.text(x0, top - 30, lev[0].upper() + lev[1:], size=12.5, weight="bold")
        for t in (-60, -40, -20, 0):
            svg.line(xm(t), top - 14, xm(t), top + rh * len(sectors) - 8, stroke=RULE if t else INK3)
            svg.text(xm(t), top + rh * len(sectors) + 8, f"{t}%", size=10, fill=INK3, anchor="middle")
        for si, s in enumerate(sectors):
            r = next(x for x in rows if x["sector"] == s and x["lever"] == lev)
            y = top + si * rh + rh / 2 - 6
            v = float(r["pct_change_amendment_value"])
            a, b = float(r["pct_change_amendment_value_lo"]), float(r["pct_change_amendment_value_hi"])
            svg.add(f'<rect x="{xm(a):.1f}" y="{y - 4}" width="{max(2, xm(b) - xm(a)):.1f}" height="8" rx="3" '
                    f'fill="{GRAY_LIGHT}"/>')
            svg.add(f'<circle cx="{xm(v):.1f}" cy="{y:.1f}" r="5.5" fill="{BLUE}" stroke="{SURFACE}" stroke-width="2"/>')
    for si, s in enumerate(sectors):
        svg.text(24, top + si * rh + rh / 2 - 2, SECTOR_LABEL.get(s, s), size=12)
    svg.text(24, H - 46, "Value = sum of simulated amendment sizes (relative units), so changes compare sectors and levers, "
                         "not dollars.", size=11, fill=INK3)
    svg.text(24, H - 28, "These follow from the fitted model; they are as reliable as the fit and the lever mapping.",
             size=11, fill=INK3)
    svg.save(path)


def documents_figure(path: Path) -> None:
    rows = list(csv.DictReader((RES / "document_codes.csv").open(encoding="utf-8")))
    order = ["software_saas", "tech_general", "it_services", "hardware_telecom", "non_tech"]
    label = {"software_saas": "Software & SaaS", "tech_general": "General technology", "it_services": "IT services",
             "hardware_telecom": "Hardware & telecom", "non_tech": "Non-technology"}
    cats = [("re-competition delayed", ORANGE, "Extended until a new contract is awarded"),
            ("design", BLUE, "Design cause stated"), ("chance", AQUA, "Chance cause stated"),
            ("neutral", GRAY, "Planned price adjustment"), ("no cause stated", GRAY_LIGHT, "No cause stated")]
    W, top, rh, left, bw = 1180, 150, 46, 230, 820
    H = top + rh * len(order) + 260
    svg = Svg(W, H, "Y4. What the amendment documents say")
    svg.text(24, 36, "Y4. What 235 Chicago amendment documents say about why the contract changed", size=18, weight="bold")
    svg.text(24, 58, "Stratified sample of revisions (20 per sector × amendment order), OCR'd and coded. Share of documents by "
                     "stated reason.", size=12.5, fill=INK2)
    lx = 24
    for _, color, lab in cats:
        svg.add(f'<rect x="{lx}" y="84" width="14" height="14" rx="2" fill="{color}"/>')
        svg.text(lx + 20, 96, lab, size=12, fill=INK2)
        lx += 20 + 6.6 * len(lab) + 26
    for si, sec in enumerate(order):
        rs = [r for r in rows if r["sector"] == sec]
        y = top + si * rh
        svg.text(24, y + 20, f"{label[sec]}", size=12.5, weight="bold" if sec in ("software_saas", "tech_general") else "normal")
        svg.text(left - 10, y + 20, f"n={len(rs)}", size=10.5, fill=INK3, anchor="end")
        x = left
        for cat, color, _ in cats:
            share = sum(1 for r in rs if (r["primary_bin"].startswith("design") if cat == "design" else r["primary_bin"] == cat)) / len(rs)
            w = share * bw
            if w > 0:
                svg.add(f'<rect x="{x:.1f}" y="{y + 4}" width="{max(w - 2, 0.5):.1f}" height="26" fill="{color}"/>')
                if cat == "re-competition delayed" or share >= 0.08:
                    svg.text(x + 6, y + 22, f"{share:.0%}", size=11.5, fill=SURFACE if cat in ("re-competition delayed", "design") else INK)
            x += w
    # by amendment order
    y0 = top + rh * len(order) + 40
    svg.text(24, y0, "Extended until a new contract is awarded, by amendment order (all sectors)", size=13, weight="bold")
    for bi, b in enumerate(("1st", "2nd-3rd", "4th+")):
        rs = [r for r in rows if r["order_bucket"] == b]
        share = sum(1 for r in rs if r["primary_bin"] == "re-competition delayed") / len(rs)
        y = y0 + 16 + bi * 32
        svg.text(24, y + 17, f"{b} amendment", size=12)
        svg.add(f'<rect x="{left}" y="{y + 2}" width="{share * bw:.1f}" height="22" fill="{ORANGE}"/>')
        svg.text(left + share * bw + 8, y + 18, f"{share:.0%} (n={len(rs)})", size=11.5, fill=INK2)
    svg.text(24, H - 46, "Coder agreement with manual review: 92% on 38 decidable documents (in-sample: rules were revised on "
                         "them). Delay and no-cause codes were 26/26 correct.", size=11, fill=INK3)
    svg.text(24, H - 28, "65 sampled revisions (mostly 2003–2011) have no document online; the coded sample is mostly 2012 onward.",
             size=11, fill=INK3)
    svg.save(path)


COVERAGE_ROWS = [  # jurisdiction, label, note on what limits it
    ("washington_state", "Washington State", "Amendment rows only from FY2023+ reports"),
    ("chicago", "Chicago", "Only ledger with documents online"),
    ("oregon", "Oregon (ORPIN)", "Through 2021"),
    ("cook_county", "Cook County", "No document links"),
    ("oregon_lottery", "Oregon Lottery", "No contract term: no timing"),
    ("oregon_treasury", "Oregon Treasury", "Few dated changes (213)"),
    ("oregon_judicial", "Oregon Judicial", "Fiscal-year snapshots, no dates"),
    ("wa_doh", "WA Dept. of Health", "Version histories from SFY2016–19 reports"),
    ("nyc_checkbook", "New York City (Checkbook)", "Original vs. current + version count; no dates"),
    ("dc", "District of Columbia (PASS)", "Options + versions; no dates"),
    ("west_hollywood", "West Hollywood", "Original vs. current total only"),
    ("baton_rouge", "Baton Rouge", "No amendment history (PO snapshot)"),
    ("vermont", "Vermont", "No amendment history"),
    ("austin", "Austin", "No amendment history"),
    ("nyc_sca", "NYC School Constr. Auth.", "Change orders only"),
]
VALUE_GROWTH = {"chicago", "cook_county", "oregon", "oregon_treasury", "oregon_judicial", "washington_state",
                "oregon_lottery", "wa_doh", "nyc_checkbook", "dc"}


def coverage_figure(path: Path) -> None:
    cov = json.loads((RES / "data_coverage.json").read_text())
    docs = 0
    if (RES / "document_codes.csv").exists():
        docs = sum(1 for _ in csv.DictReader((RES / "document_codes.csv").open(encoding="utf-8")))
    cols = [("Contracts\nnormalized", lambda j: cov["contracts"].get(j)),
            ("Amendment history\n(rates, regressions)", lambda j: cov["observable"].get(j)),
            ("Value growth\n(Figures 3–4)", lambda j: cov["observable"].get(j) if j in VALUE_GROWTH else None),
            ("Timing in term\n(fingerprints)", lambda j: cov["timing"].get(j)),
            ("Amendment sizes\n(escalation)", lambda j: cov["sizes"].get(j)),
            ("Vendor share\nof risk", lambda j: cov["vendor"].get(j)),
            ("Stated reasons\n(record text)", lambda j: cov["reasons"].get(j)),
            ("Amendment\ndocuments (OCR)", lambda j: docs if j == "chicago" else None)]
    W, top, rh, left, cw = 1240, 150, 30, 200, 100
    H = top + rh * len(COVERAGE_ROWS) + 110
    svg = Svg(W, H, "Y0. Which data feed which analysis")
    svg.text(24, 36, "Y0. Which jurisdictions feed which analysis", size=18, weight="bold")
    svg.text(24, 58, "Cells: contracts used (reasons: amendments with informative text; documents: amendment documents read). "
                     "Dash: not usable, with the reason at right.", size=12.5, fill=INK2)
    for ci, (lab, _) in enumerate(cols):
        x = left + ci * cw + cw / 2
        for li, line in enumerate(lab.split("\n")):
            svg.text(x, top - 34 + li * 14, line, size=11, anchor="middle", weight="bold")
    svg.text(left + len(cols) * cw + 10, top - 20, "What limits it", size=11, weight="bold")
    for ri, (j, lab, note) in enumerate(COVERAGE_ROWS):
        y = top + ri * rh
        if ri % 2 == 0:
            svg.add(f'<rect x="16" y="{y - 2}" width="{W - 32}" height="{rh}" fill="{BAND}"/>')
        svg.text(24, y + rh / 2 + 3, lab, size=12)
        for ci, (_, fn) in enumerate(cols):
            v = fn(j)
            x = left + ci * cw + cw / 2
            if v:
                svg.add(f'<rect x="{x - cw / 2 + 6}" y="{y + 3}" width="{cw - 12}" height="{rh - 8}" rx="4" fill="{BLUE}" '
                        f'opacity="0.18"/>')
                svg.text(x, y + rh / 2 + 3, f"{v:,}", size=11, anchor="middle")
            else:
                svg.text(x, y + rh / 2 + 3, "–", size=11, fill=INK3, anchor="middle")
        svg.text(left + len(cols) * cw + 10, y + rh / 2 + 3, note, size=10.5, fill=INK2)
    svg.text(24, H - 46, "Timing: contracts with dated amendments inside a known term. Sizes: contracts with two or more dated "
                         "positive dollar changes.", size=11, fill=INK3)
    svg.text(24, H - 28, "Cooperative-sales data (Texas DIR, Washington DES, Delaware) record spending, not amendments, and feed "
                         "the network figures instead.", size=11, fill=INK3)
    svg.save(path)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    # Y1 (SMM estimates) is not drawn: parameter recovery showed the lock-in share is not identified
    # with the current moments (see synthesis/RESULTS.md). Call estimates_figure() directly to inspect.
    counterfactual_figure(OUT / "y3_counterfactuals.svg")
    if (RES / "document_codes.csv").exists():
        documents_figure(OUT / "y4_documents.svg")
    if (RES / "data_coverage.json").exists():
        coverage_figure(OUT / "y0_data_coverage.svg")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
