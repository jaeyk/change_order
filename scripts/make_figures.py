#!/usr/bin/env python3
"""Render publication figures as standalone SVG (standard library only).

Outputs (figures/):
  fig1_network_dollars.svg      cooperative network, sales dollars
  fig2_network_contracts.svg    cooperative network, contract counts
  fig3_amendment_snowball.svg   how successive amendments compound contract value, by sector
  fig4_growth_by_domain.svg     amendment incidence and value growth by program domain

Inputs: data/processed/procurement_network.json (scripts/build_procurement_network.py),
        data/processed/contracts_normalized.csv, data/processed/amendments_normalized.csv
"""

from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from html import escape
from pathlib import Path

PROCESSED = Path("data/processed")
OUT = Path("figures")

# Validated categorical slots (light surface) + neutrals
BLUE, ORANGE, AQUA, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
INK, INK2, INK3, RULE, BAND, SURFACE = "#15191c", "#4d5458", "#7c8387", "#dfe3e1", "#f1f3f2", "#ffffff"
GRAY, GRAY_LIGHT = "#9aa1a4", "#b9bfc1"
FONT = "Helvetica, Arial, sans-serif"

DIR_STYLE = {
    "vertical_downward": (ORANGE, None, "Vertical down: locals on state/multi-state contracts"),
    "horizontal": (BLUE, None, "Horizontal: peers pooling"),
    "vertical_upward": (AQUA, None, "Vertical up: state on local co-op"),
    "central": (GRAY, "1 5", "Central: own state's contract"),
    "unknown": (GRAY_LIGHT, "6 5", "Direction unknown"),
}

# Ledgers whose amendment rows carry the dollar change of each amendment
DELTA_LEDGERS = {"chicago", "cook_county", "oregon", "oregon_treasury", "oregon_judicial", "washington_state",
                 "oregon_lottery", "wa_doh", "dc"}

SECTORS = [  # (key, label, color)
    ("hardware_telecom", "Hardware & telecom", ORANGE),
    ("tech_general", "General technology", YELLOW),
    ("software_saas", "Software & SaaS", BLUE),
    ("it_services", "IT services", AQUA),
    ("non_tech", "Non-technology", GRAY),
]

DOMAIN_LABEL = {
    "public_assistance": "Public assistance", "environment": "Environment",
    "general_enterprise_it": "General enterprise IT", "health_care": "Health care",
    "public_safety": "Public safety & justice", "labor_workforce": "Labor & workforce",
    "administration_finance": "Administration & finance", "transportation": "Transportation",
    "non_tech": "Non-technology contracts",
}


class Svg:
    def __init__(self, w: int, h: int, title: str):
        self.w, self.h, self.parts = w, h, []
        self.parts.append(f'<rect width="{w}" height="{h}" fill="{SURFACE}"/>')
        self.title = title

    def add(self, s: str) -> None:
        self.parts.append(s)

    def text(self, x, y, s, size=12, fill=INK, anchor="start", weight="normal", italic=False) -> None:
        style = ' font-style="italic"' if italic else ""
        self.add(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" '
                 f'font-weight="{weight}"{style}>{escape(s)}</text>')

    def line(self, x1, y1, x2, y2, stroke=RULE, width=1, dash=None) -> None:
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" '
                 f'stroke-width="{width}"{d}/>')

    def save(self, path: Path) -> None:
        body = "\n".join(self.parts)
        path.write_text(
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
            f'viewBox="0 0 {self.w} {self.h}" font-family="{FONT}" role="img">\n'
            f'<title>{escape(self.title)}</title>\n{body}\n</svg>\n', encoding="utf-8")
        print(f"Wrote {path}")


def wrap(s: str, n: int) -> list[str]:
    lines, cur = [], ""
    for w in s.split():
        if cur and len(cur) + 1 + len(w) > n:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        lines.append(cur)
    return lines[:3]


def money(v: float) -> str:
    if v >= 1e9:
        return f"${v / 1e9:.1f}B"
    if v >= 1e6:
        return f"${v / 1e6:.0f}M"
    return f"${v / 1e3:.0f}K"


# --------------------------------------------------------------------------------------
# Figures 1-2: network
# --------------------------------------------------------------------------------------

ROWS = [("state_buyer", "STATE BUYERS", "agencies, universities, other states"),
        ("state_vehicle", "STATE & MULTI-STATE CONTRACTS", "DIR, DES, NASPO, MMCAP"),
        ("local_vehicle", "LOCAL COOPERATIVES", "Sourcewell, OMNIA, TIPS"),
        ("local_buyer", "LOCAL BUYERS", "cities, counties, schools")]


def network_figure(view: str, data: dict, totals: dict, path: Path, fig_no: int) -> None:
    edges = [dict(e) for e in data[view]["edges"]]
    nodes: dict[str, dict] = {}
    for e in edges:
        e["bk"], e["vk"] = f"{e['brow']}|{e['buyer']}", f"{e['vrow']}|{e['vehicle']}"
        for key, nid, row in ((e["bk"], e["buyer"], e["brow"]), (e["vk"], e["vehicle"], e["vrow"])):
            n = nodes.setdefault(key, {"id": nid, "row": row, "total": 0, "edges": []})
            n["total"] += e["value"]
            n["edges"].append(e)
    by_row = {r: sorted([n for n in nodes.values() if n["row"] == r], key=lambda n: n["id"]) for r, _, _ in ROWS}

    def place():
        for r in by_row.values():
            for i, n in enumerate(r):
                n["pos"] = (i + 0.5) / len(r)

    place()
    for _ in range(8):  # barycentric sweeps reduce crossings
        for r, _, _ in ROWS:
            for n in by_row[r]:
                s = w = 0.0
                for e in n["edges"]:
                    o = nodes[e["vk"] if e["bk"] == f"{n['row']}|{n['id']}" else e["bk"]]
                    ww = math.sqrt(e["value"])
                    s, w = s + o["pos"] * ww, w + ww
                n["bary"] = s / w if w else n["pos"]
            by_row[r].sort(key=lambda n: n["bary"])
            place()

    left, right = 200, 40
    max_count = max(len(v) for v in by_row.values())
    W = max(1100, left + right + max_count * 96)
    top = 160
    row_y = {"state_buyer": top + 70, "state_vehicle": top + 240, "local_vehicle": top + 410, "local_buyer": top + 580}
    H = top + 720 + 90
    unit = "sales" if view == "dollars" else "contracts"
    fmt = money if view == "dollars" else (lambda v: f"{v:,.0f}")
    title = (f"Figure {fig_no}. Who buys off whose contract ({'sales dollars' if view == 'dollars' else 'contract counts'})")
    svg = Svg(W, H, title)
    svg.text(24, 36, title, size=18, weight="bold")
    t = totals[view]
    coop = t["vertical_downward"] + t["horizontal"] + t["vertical_upward"] + t["unknown"]
    sub = (f"Vertical piggybacking {fmt(t['vertical_downward'])} ({100 * t['vertical_downward'] / coop:.0f}% of cooperative {unit}); "
           f"horizontal pooling {fmt(t['horizontal'])} ({100 * t['horizontal'] / coop:.0f}%); "
           f"central purchasing {fmt(t['central'])} shown dotted.")
    svg.text(24, 60, sub, size=13, fill=INK2)
    # legend
    lx, ly = 24, 88
    for d in ("vertical_downward", "horizontal", "vertical_upward", "central", "unknown"):
        color, dash, label = DIR_STYLE[d]
        item_w = 32 + 6.3 * len(label) + 22
        if lx + item_w > W - 24:  # wrap the legend
            lx, ly = 24, ly + 24
        svg.line(lx, ly, lx + 26, ly, stroke=color, width=4, dash=dash)
        svg.text(lx + 32, ly + 4, label, size=12, fill=INK2)
        lx += item_w
    lx, ly = 24, ly + 28
    svg.add(f'<circle cx="{lx + 6}" cy="{ly - 4}" r="5" fill="{SURFACE}" stroke="{INK}" stroke-width="2"/>')
    svg.text(lx + 16, ly, "buyer", size=12, fill=INK2)
    svg.add(f'<rect x="{lx + 66}" y="{ly - 9}" width="10" height="10" rx="2" fill="{INK}"/>')
    svg.text(lx + 82, ly, "contract vehicle (node size = total volume; line width = volume of each link)", size=12, fill=INK2)
    # level bands
    for name, y0, y1 in (("State level", row_y["state_buyer"] - 60, row_y["state_vehicle"] + 60),
                         ("Local level", row_y["local_vehicle"] - 60, row_y["local_buyer"] + 70)):
        svg.add(f'<rect x="12" y="{y0}" width="{W - 24}" height="{y1 - y0}" rx="10" fill="{BAND}"/>')
    for key, label, sub_ in ROWS:
        svg.text(26, row_y[key] - 3, label, size=11, fill=INK3, weight="bold")
        svg.text(26, row_y[key] + 12, sub_, size=11, fill=INK3)
    span = W - left - right
    for n in nodes.values():
        n["x"], n["y"] = left + n["pos"] * span, row_y[n["row"]]
    max_e = max(e["value"] for e in edges)
    max_n = max(n["total"] for n in nodes.values())
    for e in sorted(edges, key=lambda e: -e["value"]):
        a, b = nodes[e["bk"]], nodes[e["vk"]]
        my = (a["y"] + b["y"]) / 2
        color, dash, _ = DIR_STYLE[e["dir"]]
        width = 1.2 + 15 * math.sqrt(e["value"] / max_e)
        d = f' stroke-dasharray="{dash}"' if dash else ""
        svg.add(f'<path d="M{a["x"]:.1f},{a["y"]:.1f} C{a["x"]:.1f},{my:.1f} {b["x"]:.1f},{my:.1f} {b["x"]:.1f},{b["y"]:.1f}" '
                f'fill="none" stroke="{color}" stroke-opacity="0.72" stroke-width="{width:.2f}" stroke-linecap="round"{d}/>')
    for key, _, _ in ROWS:
        for i, n in enumerate(by_row[key]):
            r = 4 + 13 * math.sqrt(n["total"] / max_n)
            if key.endswith("vehicle"):
                svg.add(f'<rect x="{n["x"] - r:.1f}" y="{n["y"] - r:.1f}" width="{2 * r:.1f}" height="{2 * r:.1f}" rx="3" '
                        f'fill="{INK}" stroke="{SURFACE}" stroke-width="2"/>')
            else:
                svg.add(f'<circle cx="{n["x"]:.1f}" cy="{n["y"]:.1f}" r="{r:.1f}" fill="{SURFACE}" stroke="{INK}" stroke-width="2"/>')
            above = key == "state_buyer" or (key in ("state_vehicle", "local_vehicle") and i % 2 == 0)
            lines = wrap(n["id"], 16)
            y0 = n["y"] - r - 8 - (len(lines) - 1) * 13 if above else n["y"] + r + 17
            for k, ln in enumerate(lines):
                svg.text(n["x"], y0 + 13 * k, ln, size=11.5, anchor="middle")
    fed = data[view]["federal"]
    note = ("Federal links omitted (thin in these data): " + "; ".join(f"{e['buyer']} → {e['vehicle']} {fmt(e['value'])}" for e in fed) + ".") if fed else ""
    src = ("Sources: Texas DIR cooperative sales FY2010–FY2027; Washington DES statewide-contract sales 2015–2026; "
           "Delaware statewide and external-cooperative spend FY2023–FY2027." if view == "dollars" else
           "Sources: WA, OR, Chicago, Cook County, Baton Rouge, West Hollywood and Austin contract ledgers; contracts naming a "
           "cooperative vehicle or another government's contract (a lower bound).")
    svg.text(24, H - 46, src, size=11, fill=INK3)
    svg.text(24, H - 28, note, size=11, fill=INK3)
    svg.save(path)


# --------------------------------------------------------------------------------------
# Figure 3: amendment snowball
# --------------------------------------------------------------------------------------

def load_paths() -> tuple[dict, dict]:
    contracts = {}
    with (PROCESSED / "contracts_normalized.csv").open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if (r["jurisdiction"] in DELTA_LEDGERS and r["amendment_observable"] == "1"
                    and float(r["initial_award_val"] or 0) >= 1000):
                contracts[(r["jurisdiction"], r["contract_id"])] = r
    amends = defaultdict(list)
    with (PROCESSED / "amendments_normalized.csv").open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            k = (r["jurisdiction"], r["contract_id"])
            if k in contracts:
                amends[k].append(r)

    def num(s):
        try:
            return float(s)
        except (TypeError, ValueError):
            return 0.0

    paths = {}
    for k, c in contracts.items():
        v0 = float(c["initial_award_val"])
        cum, p = v0, [1.0]
        for r in sorted(amends.get(k, []), key=lambda r: (r["amendment_date"] or "9999", num(r["amendment_seq"]))):
            cum += num(r["delta_amount"])
            p.append(max(cum, 0.01 * v0) / v0)  # floor at 1% so de-obligations stay on a log scale
        paths[k] = p
    return contracts, paths


def gmean(xs: list[float]) -> float:
    return math.exp(sum(math.log(x) for x in xs) / len(xs))


def gmean_ci(xs: list[float]) -> tuple[float, float, float]:
    """Geometric mean with a 95% interval computed on the log scale (mean of logs ± 1.96 SE)."""
    logs = [math.log(x) for x in xs]
    m = sum(logs) / len(logs)
    if len(logs) < 2:
        return math.exp(m), math.exp(m), math.exp(m)
    sd = math.sqrt(sum((v - m) ** 2 for v in logs) / (len(logs) - 1))
    se = sd / math.sqrt(len(logs))
    return math.exp(m), math.exp(m - 1.96 * se), math.exp(m + 1.96 * se)


def snowball_figure(contracts: dict, paths: dict, path: Path) -> dict:
    K = 6
    by_sector = defaultdict(list)
    for k, p in paths.items():
        by_sector[contracts[k]["tech_subsector"]].append(p)
    cohort = {s: [p for p in ps if len(p) > K] for s, ps in by_sector.items()}
    series_a = {s: [gmean_ci([p[i] for p in coh]) for i in range(K + 1)] for s, coh in cohort.items() if coh}
    buckets = [("0", 0, 0), ("1", 1, 1), ("2", 2, 2), ("3–5", 3, 5), ("6–10", 6, 10), ("11+", 11, 10 ** 6)]
    series_b, n_b = {}, {}
    for s, ps in by_sector.items():
        vals, ns = [], []
        for _, lo, hi in buckets:
            g = [p[-1] for p in ps if lo <= len(p) - 1 <= hi]
            vals.append(gmean_ci(g) if len(g) >= 10 else None)
            ns.append(len(g))
        series_b[s], n_b[s] = vals, ns

    def axis_max(series: dict) -> float:
        tops = [v[2] for vals in series.values() for v in vals if v is not None]
        top = max(tops + [2.0])
        return next(t for t in (2, 2.5, 3, 4, 5, 7, 10, 15, 20, 25, 30, 50, 100) if t >= top)

    W, H = 1580, 680
    svg = Svg(W, H, "Figure 3. Amendments snowball contract value")
    svg.text(24, 36, "Figure 3. Amendments snowball contract value", size=18, weight="bold")
    svg.text(24, 58, "Contract value as a multiple of the original award (geometric mean, with 95% confidence intervals). "
                     "Chicago, Cook County, Oregon, Washington and DC ledgers (contracts ≥ $1,000).", size=13, fill=INK2)

    def panel(x0, y0, w, h, xs, series, ymax, title, sub, xlabel, ns_label, ymin=0.9):
        svg.text(x0, y0 - 34, title, size=14, weight="bold")
        svg.text(x0, y0 - 16, sub, size=12, fill=INK2)
        # log scale: equal distances are equal ratios, and the log-scale intervals stay symmetric
        ticks = [t for t in (1, 1.25, 1.5, 2, 2.5, 3, 4, 5, 7, 10, 15, 20, 25, 30, 50, 100)
                 if t <= ymax and (ymax <= 5 or t not in (1.25, 2.5, 4, 7, 15, 25))]
        lo_, hi_ = math.log(ymin), math.log(ymax)
        ymap = lambda v: y0 + h - (math.log(min(max(v, ymin), ymax)) - lo_) / (hi_ - lo_) * h
        xmap = lambda i: x0 + 40 + i * (w - 170) / (len(xs) - 1)
        for t in ticks:
            svg.line(x0 + 40, ymap(t), x0 + w - 130, ymap(t), stroke=RULE)
            svg.text(x0 + 32, ymap(t) + 4, f"{t:g}×", size=11, fill=INK3, anchor="end")
        for i, lab in enumerate(xs):
            svg.text(xmap(i), y0 + h + 18, lab, size=11, fill=INK3, anchor="middle")
        svg.text(x0 + 40 + (w - 170) / 2, y0 + h + 38, xlabel, size=12, fill=INK2, anchor="middle")
        present = [k for k, _, _ in SECTORS if series.get(k)]
        ends = []
        for si, (key, label, color) in enumerate(SECTORS):
            vals = series.get(key)
            if not vals:
                continue
            off = (present.index(key) - (len(present) - 1) / 2) * 5  # nudge bars apart
            pts = [(xmap(i) + off, ymap(v[0])) for i, v in enumerate(vals) if v is not None]
            # 95% interval bars
            for i, v in enumerate(vals):
                if v is None or i == 0 and v[1] == v[2]:
                    continue
                x = xmap(i) + off
                svg.add(f'<line x1="{x:.1f}" y1="{ymap(v[1]):.1f}" x2="{x:.1f}" y2="{ymap(v[2]):.1f}" stroke="{color}" '
                        f'stroke-width="1.5" stroke-opacity="0.55"/>')
                for yy in (ymap(v[1]), ymap(v[2])):
                    svg.add(f'<line x1="{x - 3:.1f}" y1="{yy:.1f}" x2="{x + 3:.1f}" y2="{yy:.1f}" stroke="{color}" '
                            f'stroke-width="1.5" stroke-opacity="0.55"/>')
            dash = ' stroke-dasharray="5 4"' if key == "non_tech" else ""
            svg.add(f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in pts)}" fill="none" stroke="{color}" '
                    f'stroke-width="2.5" stroke-linejoin="round"{dash}/>')
            for x, y in pts:
                svg.add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{color}" stroke="{SURFACE}" stroke-width="2"/>')
            last = [v for v in vals if v is not None][-1]
            ends.append([pts[-1][1], f"{label} {last[0]:.2f}× [{last[1]:.2f}–{last[2]:.2f}]{ns_label(key)}",
                         xmap(len(xs) - 1)])
        ends.sort()
        for i in range(len(ends)):  # de-collide end labels and keep them inside the panel
            ends[i][0] = max(ends[i][0], y0 + 4)
            if i and ends[i][0] - ends[i - 1][0] < 15:
                ends[i][0] = ends[i - 1][0] + 15
        for y, lab, x in ends:
            svg.text(x + 18, y + 4, lab, size=11)

    panel(24, 130, 600, 420, [str(i) for i in range(K + 1)], series_a, axis_max(series_a),
          "A. Value path, amendment by amendment",
          f"Same contracts throughout: those amended at least {K} times", "Amendments so far",
          lambda k: f" (n={len(cohort.get(k, []))})")
    panel(800, 130, 600, 420, [b[0] for b in buckets], series_b, axis_max(series_b),
          "B. Final value by total number of amendments",
          "All contracts; points need ≥ 10 contracts", "Total amendments", lambda k: "")
    svg.text(24, H - 64, "Reading: in panel A every line follows one fixed group of contracts, so the climb is "
                         "compounding, not a change in which contracts are counted. Geometric means damp extreme outliers.",
             size=11, fill=INK3)
    svg.text(24, H - 46, "Log scale; each panel has its own axis. Bars: 95% confidence intervals for the geometric mean (mean of logs ± 1.96 SE); "
                         "sectors are offset slightly so bars do not overlap. Wide bars at 11+ reflect few contracts.",
             size=11, fill=INK3)
    svg.text(24, H - 28, "Pooled across ledgers: within the same ledger, software ≈ non-technology and hardware / general technology "
                         "compound more (robustness_checks.md, R15). DC changes are ordered by option period and version.",
             size=11, fill=INK3)
    svg.save(path)
    pt = lambda vals: [None if v is None else round(v[0], 4) for v in vals]
    ci = lambda vals: [None if v is None else [round(v[1], 4), round(v[2], 4)] for v in vals]
    return {"cohort_min_amendments": K,
            "panel_a": {s: pt(v) for s, v in series_a.items()}, "panel_a_ci95": {s: ci(v) for s, v in series_a.items()},
            "panel_a_n": {s: len(c) for s, c in cohort.items()},
            "panel_b": {s: pt(v) for s, v in series_b.items()}, "panel_b_ci95": {s: ci(v) for s, v in series_b.items()},
            "panel_b_n": n_b}


# --------------------------------------------------------------------------------------
# Figure 4: by program domain
# --------------------------------------------------------------------------------------

def domain_figure(contracts: dict, paths: dict, path: Path) -> dict:
    groups = defaultdict(list)
    for k, p in paths.items():
        c = contracts[k]
        groups[c["tech_domain"] if c["is_tech"] == "1" else "non_tech"].append(p)
    rows = []
    for d, ps in groups.items():
        amended = [p for p in ps if len(p) > 1]
        if len(amended) < 30:
            continue
        rows.append({"domain": d, "n": len(ps), "amended": len(amended),
                     "rate": 100 * len(amended) / len(ps),
                     "growth": gmean([p[-1] for p in amended]),
                     "doubled": 100 * sum(1 for p in amended if p[-1] >= 2) / len(amended)})
    rows.sort(key=lambda r: (r["domain"] == "non_tech", -r["growth"]))
    W, row_h = 1180, 34
    H = 170 + row_h * len(rows) + 70
    svg = Svg(W, H, "Figure 4. Amendment incidence and value growth by program domain")
    svg.text(24, 36, "Figure 4. How often contracts are amended, and how far they grow, by program domain", size=18, weight="bold")
    svg.text(24, 58, "Technology contracts by program domain, with non-technology contracts as reference. Chicago, Cook County, "
                     "Oregon and Washington ledgers.", size=13, fill=INK2)
    label_w, y0 = 230, 130
    cols = [("Share of contracts amended", "rate", 0, 60, lambda v: f"{v:.0f}%", [0, 20, 40, 60]),
            ("Value growth when amended (geometric mean)", "growth", 1, 1.6, lambda v: f"{v:.2f}×", [1, 1.2, 1.4, 1.6]),
            ("Amended contracts that at least doubled", "doubled", 0, 40, lambda v: f"{v:.0f}%", [0, 10, 20, 30, 40])]
    col_w = (W - label_w - 60) / 3
    ref = next(r for r in rows if r["domain"] == "non_tech")
    for ci, (title, key, lo, hi, fmt, ticks) in enumerate(cols):
        x0 = label_w + 30 + ci * col_w
        xs = lambda v: x0 + (v - lo) / (hi - lo) * (col_w - 70)
        svg.text(x0, y0 - 40, title, size=12.5, weight="bold")
        for t in ticks:
            svg.line(xs(t), y0 - 14, xs(t), y0 + row_h * len(rows) - 10, stroke=RULE)
            svg.text(xs(t), y0 - 20, fmt(t), size=10.5, fill=INK3, anchor="middle")
        svg.line(xs(ref[key]), y0 - 14, xs(ref[key]), y0 + row_h * len(rows) - 10, stroke=GRAY, width=1.5, dash="4 3")
        for ri, r in enumerate(rows):
            y = y0 + ri * row_h + 8
            color = GRAY if r["domain"] == "non_tech" else BLUE
            svg.line(xs(lo), y, xs(r[key]), y, stroke=color, width=2)
            svg.add(f'<circle cx="{xs(r[key]):.1f}" cy="{y:.1f}" r="6" fill="{color}" stroke="{SURFACE}" stroke-width="2"/>')
            svg.text(xs(r[key]) + 11, y + 4, fmt(r[key]), size=11)
    for ri, r in enumerate(rows):
        y = y0 + ri * row_h + 8
        if r["domain"] == "non_tech":
            svg.line(24, y - row_h / 2, W - 24, y - row_h / 2, stroke=RULE)
        svg.text(24, y + 4, DOMAIN_LABEL.get(r["domain"], r["domain"]), size=12.5,
                 weight="bold" if r["domain"] == "non_tech" else "normal")
        svg.text(label_w + 4, y + 4, f"n={r['n']:,}", size=10.5, fill=INK3, anchor="end")
    svg.text(24, H - 30, "Dashed vertical line = non-technology reference. Growth = final value ÷ original award among amended "
                         "contracts (≥ $1,000 original award).", size=11, fill=INK3)
    svg.save(path)
    return {"rows": rows}




# --------------------------------------------------------------------------------------
# Figure 5: fingerprints of chance vs. design (simulated worlds vs. sectors)
# --------------------------------------------------------------------------------------

DIVERGING = {  # blue (below chance) <- gray -> red (above chance), light-surface steps
    -3: "#1c5cab", -2: "#5598e7", -1: "#b7d3f6", 0: "#f0efec", 1: "#f5c1b6", 2: "#e66767", 3: "#b83535",
}
SECTOR_LABEL = {
    "subsector:software_saas": "Software & SaaS", "domain:general_enterprise_it": "General enterprise IT",
    "subsector:tech_general": "General technology", "subsector:hardware_telecom": "Hardware & telecom",
    "subsector:it_services": "IT services", "domain:health_care": "Health care (tech)",
    "domain:public_assistance": "Public assistance (tech)", "domain:transportation": "Transportation (tech)",
    "domain:administration_finance": "Administration & finance (tech)", "domain:public_safety": "Public safety (tech)",
    "domain:environment": "Environment (tech)", "domain:labor_workforce": "Labor & workforce (tech)",
    "all_tech": "All technology", "non_tech": "Non-technology",
}


def bucket(z: float | None) -> int:
    if z is None:
        return 0
    a = abs(z)
    b = 0 if a < 2 else 1 if a < 5 else 2 if a < 10 else 3
    return b if z > 0 else -b


def fingerprint_figure(path: Path) -> dict | None:
    fpath = Path("simulations/results/amendment_fingerprints.json")
    if not fpath.exists():
        return None
    d = json.loads(fpath.read_text())
    cols = [("early", "Early first\namendment"), ("late", "End-of-term\namendment"),
            ("lift", "Late lift after\nearlier amendments"), ("accel_pre", "Acceleration\n(before term end)"),
            ("escal", "Escalating\namendment size"), ("vendor", "Vendor share\nof risk")]
    worlds = [("B", "B  Design: scope gaps, no lock-in"), ("C", "C  Design: lock-in spiral"),
              ("D", "D  Chance + routine renewals"), ("E", "E  Half chance, half lock-in")]
    order = [r["sector"] for r in d.get("lockin_ranking", [])] or list(d["sectors"])
    W, top, left, cw, rh = 1180, 150, 300, 118, 30
    rows = len(worlds) + len(order)
    H = top + rows * rh + 60 + 130
    svg = Svg(W, H, "Figure 5. Which sectors carry the fingerprints of designed amendments")
    svg.text(24, 36, "Figure 5. Which sectors carry the fingerprints of designed amendments", size=18, weight="bold")
    svg.text(24, 58, "Each cell: deviation from a pure-chance world matched to the same amendment-count distribution "
                     "(z-score). Top block: simulated theory worlds. Bottom block: sectors, ranked by lock-in index.",
             size=12.5, fill=INK2)
    for ci, (_, lab) in enumerate(cols):
        x = left + ci * cw + cw / 2
        for li, line in enumerate(lab.split("\n")):
            svg.text(x, top - 32 + li * 14, line, size=11.5, anchor="middle", weight="bold")
    svg.add(f'<rect x="{left + 4 * cw - 4}" y="{top - 46}" width="{2 * cw + 8}" height="{rows * rh + 76}" rx="8" '
            f'fill="none" stroke="{INK3}" stroke-dasharray="4 3"/>')
    svg.text(left + 5 * cw, top + rows * rh + 46, "Core lock-in fingerprints", size=11, fill=INK2, anchor="middle")

    def row(y, label, fp, bold=False, note=""):
        svg.text(24, y + rh / 2 + 4, label, size=12, weight="bold" if bold else "normal")
        if note:
            svg.text(left - 10, y + rh / 2 + 4, note, size=10.5, fill=INK3, anchor="end")
        for ci, (k, _) in enumerate(cols):
            z = (fp.get(k) or {}).get("z")
            b = bucket(z)
            x = left + ci * cw
            svg.add(f'<rect x="{x + 2}" y="{y + 2}" width="{cw - 4}" height="{rh - 4}" rx="3" fill="{DIVERGING[b]}"/>')
            txt = "–" if z is None else (f"{z:+.0f}" if abs(z) >= 10 else f"{z:+.1f}")
            svg.text(x + cw / 2, y + rh / 2 + 4, txt, size=11, anchor="middle",
                     fill=SURFACE if abs(b) >= 2 else INK)

    y = top
    svg.text(24, y - 8, "SIMULATED WORLDS", size=10.5, fill=INK3, weight="bold")
    for k, lab in worlds:
        row(y, lab, d["theory_worlds"][k]["fingerprints_vs_matched_chance"], bold=False)
        y += rh
    y += 10
    svg.line(24, y, W - 24, y, stroke=RULE)
    y += 6
    svg.text(24, y + 6, "SECTORS (Chicago, Oregon, Cook County, Washington; sizes also Oregon Lottery & Treasury)", size=10.5, fill=INK3,
             weight="bold")
    y += 12
    for name in order:
        sec = d["sectors"][name]
        pairs = sec["eligible"]["accel_pre_pairs"] or 0
        note = f"tier {sec.get('evidence_tier')} · n={sec['contracts']:,}" + (" · thin" if sec.get("thin") else "")
        row(y, SECTOR_LABEL.get(name, name), sec["fingerprints"],
            bold=sec.get("evidence_tier") == 1 and not sec.get("thin"), note=note)
        y += rh
    # legend
    ly = H - 70
    labels = {-3: "≤ −10", -2: "−10 to −5", -1: "−5 to −2", 0: "within ±2", 1: "+2 to +5", 2: "+5 to +10", 3: "≥ +10"}
    lx = 24
    svg.text(lx, ly - 8, "z vs. matched chance", size=11, fill=INK2)
    for b in range(-3, 4):
        svg.add(f'<rect x="{lx}" y="{ly}" width="22" height="14" rx="2" fill="{DIVERGING[b]}"/>')
        svg.text(lx + 28, ly + 11, labels[b], size=11, fill=INK2)
        lx += 28 + 7 * len(labels[b]) + 18
    svg.text(24, H - 28, "Vendor share separates design from chance and renewals; escalation separates lock-in. Tier 1 "
                         "(bold) = both, well measured. \"thin\" = fewer than 30 eligible contracts.", size=11, fill=INK3)
    svg.save(path)
    return {"order": order}


def main() -> int:
    OUT.mkdir(exist_ok=True)
    net = json.loads((PROCESSED / "procurement_network.json").read_text())
    network_figure("dollars", net["data"], net["totals"], OUT / "fig1_network_dollars.svg", 1)
    network_figure("contracts", net["data"], net["totals"], OUT / "fig2_network_contracts.svg", 2)
    contracts, paths = load_paths()
    stats = {"snowball": snowball_figure(contracts, paths, OUT / "fig3_amendment_snowball.svg"),
             "domains": domain_figure(contracts, paths, OUT / "fig4_growth_by_domain.svg")}
    stats["fingerprints"] = fingerprint_figure(OUT / "fig5_amendment_fingerprints.svg")
    (OUT / "figure_data.json").write_text(json.dumps(stats, indent=1, default=float))
    print(f"Wrote {OUT / 'figure_data.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
