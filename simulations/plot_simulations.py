#!/usr/bin/env python3
"""Figures for the amendment simulations (standard-library SVG).

Run from the repository root after simulations/simulate_amendments.py:

    python3 simulations/plot_simulations.py

Outputs (simulations/figures/):
  s1_simulated_histories.svg   example contract histories drawn from each theory world
  s2_continuation_curves.svg   why a rising "one more amendment" curve is not evidence of design
  s3_lockin_fingerprints.svg   sectors vs. their matched-chance band on the lock-in fingerprints
"""

from __future__ import annotations

import json
import math
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(HERE))

from make_figures import (BLUE, GRAY, GRAY_LIGHT, INK, INK2, INK3, ORANGE, AQUA, RULE, BAND,  # noqa: E402
                          SURFACE, SECTOR_LABEL, Svg)
from simulate_amendments import world  # noqa: E402

RESULTS = HERE / "results"
OUT = HERE / "figures"
WORLD_LABEL = {"A": "A. Chance, heterogeneous contracts", "B": "B. Design: scope gaps, no lock-in",
               "C": "C. Design: lock-in spiral", "D": "D. Chance + routine renewals"}
WORLD_COLOR = {"A": GRAY, "B": BLUE, "C": ORANGE, "D": AQUA}


# --------------------------------------------------------------------------------------
# S1: example histories
# --------------------------------------------------------------------------------------

def histories_figure(path: Path, per_world: int = 18) -> None:
    rng = random.Random(7)
    W, panel_h, top = 1180, 300, 110
    H = top + 2 * panel_h + 90
    svg = Svg(W, H, "S1. Simulated contract histories")
    svg.text(24, 36, "S1. What each theory world looks like, contract by contract", size=18, weight="bold")
    svg.text(24, 58, f"{per_world} amended contracts drawn at random from each simulated world. Each row is a contract; "
                     "each dot an amendment, placed at its time in the original term; dot area = amendment size.",
             size=12.5, fill=INK2)
    pw, gap = (W - 48 - 30) / 2, 30
    for i, kind in enumerate(("A", "B", "C", "D")):
        x0 = 24 + (i % 2) * (pw + gap)
        y0 = top + (i // 2) * panel_h
        cs = [c for c in world(kind, rng, n_vendors=120) if c["times"]]
        rng.shuffle(cs)
        cs = sorted(cs[:per_world], key=lambda c: len(c["times"]))
        svg.text(x0, y0, WORLD_LABEL[kind], size=13.5, weight="bold")
        px0, px1, py0 = x0 + 10, x0 + pw - 10, y0 + 16
        rowh = (panel_h - 70) / per_world
        xmap = lambda t: px0 + min(t, 1.05) / 1.05 * (px1 - px0)
        svg.add(f'<rect x="{xmap(0.9):.1f}" y="{py0 - 2}" width="{xmap(1.05) - xmap(0.9):.1f}" '
                f'height="{rowh * per_world + 4:.1f}" fill="{BAND}"/>')
        svg.add(f'<rect x="{xmap(0):.1f}" y="{py0 - 2}" width="{xmap(0.25) - xmap(0):.1f}" '
                f'height="{rowh * per_world + 4:.1f}" fill="{BAND}" opacity="0.6"/>')
        svg.line(xmap(1.0), py0 - 2, xmap(1.0), py0 + rowh * per_world + 2, stroke=INK3, dash="3 3")
        for r, c in enumerate(cs):
            y = py0 + r * rowh + rowh / 2
            svg.line(px0, y, px1, y, stroke=RULE)
            for t, s in zip(c["times"], c["sizes"]):
                rad = 2.2 + 9 * math.sqrt(min(s, 1.0))
                svg.add(f'<circle cx="{xmap(t):.1f}" cy="{y:.1f}" r="{rad:.1f}" fill="{WORLD_COLOR[kind]}" '
                        f'fill-opacity="0.8" stroke="{SURFACE}" stroke-width="1"/>')
        ay = py0 + rowh * per_world + 16
        for t, lab in ((0, "award"), (0.25, "25%"), (0.5, "50%"), (0.9, "90%"), (1.0, "end of term")):
            svg.text(xmap(t), ay, lab, size=10.5, fill=INK3, anchor="middle")
    svg.text(24, H - 46, "Shaded: first quarter of the term (where implementation-stage gaps surface) and the last 10% "
                         "through extension (where renewals land).", size=11, fill=INK3)
    svg.text(24, H - 28, "Read: B front-loads amendments; in C amendments grow as dependence builds and contracts are "
                         "extended past term; D adds renewals regardless of history; A: some contracts are just busier.",
             size=11, fill=INK3)
    svg.save(path)


# --------------------------------------------------------------------------------------
# S2: continuation curves
# --------------------------------------------------------------------------------------

def nb_continuation(mean: float, var: float, kmax: int = 10) -> list[float]:
    shape = mean * mean / (var - mean)
    p = shape / (shape + mean)
    pmf = [math.exp(math.lgamma(n + shape) - math.lgamma(shape) - math.lgamma(n + 1)
                    + shape * math.log(p) + n * math.log(1 - p)) for n in range(400)]
    surv = [sum(pmf[n:]) for n in range(kmax + 2)]
    return [surv[k + 1] / surv[k] for k in range(kmax)]


def continuation_figure(path: Path) -> None:
    dyn = json.loads((ROOT / "data/processed/amendment_dynamics.json").read_text())["continuation"]
    W, H = 1180, 560
    svg = Svg(W, H, "S2. A rising continuation curve is not evidence of design")
    svg.text(24, 36, "S2. A rising “one more amendment” curve is not evidence of design", size=18, weight="bold")
    svg.text(24, 58, "Probability that a contract with k amendments gets another. Observed (Chicago, Cook County, Oregon, "
                     "Washington) vs. two pure-chance benchmarks with the same mean.", size=12.5, fill=INK2)
    for pi, (key, title) in enumerate((("tech", "Technology contracts"), ("non_tech", "Non-technology contracts"))):
        d = dyn[key]
        obs = d["p_next_given_k"]
        poisson = d["poisson_benchmark"]
        nb = nb_continuation(d["mean_amendments"], d["variance"])
        x0, y0, w, h = 24 + pi * 580, 120, 540, 330
        svg.text(x0, y0 - 18, f"{title} (n={d['contracts']:,})", size=14, weight="bold")
        xmap = lambda k: x0 + 50 + k * (w - 230) / 9
        ymap = lambda v: y0 + h - v * h
        for t in (0, 0.25, 0.5, 0.75, 1.0):
            svg.line(x0 + 50, ymap(t), x0 + w - 180, ymap(t), stroke=RULE)
            svg.text(x0 + 42, ymap(t) + 4, f"{t:.0%}", size=11, fill=INK3, anchor="end")
        for k in range(10):
            svg.text(xmap(k), y0 + h + 18, str(k), size=11, fill=INK3, anchor="middle")
        svg.text(x0 + 50 + (w - 230) / 2, y0 + h + 38, "Amendments so far (k)", size=12, fill=INK2, anchor="middle")
        series = [("Observed", obs, ORANGE, None),
                  ("Chance, contracts differ\n(matched negative binomial)", nb, BLUE, "6 4"),
                  ("Chance, all contracts alike\n(Poisson)", poisson, GRAY, "2 4")]
        ends = []
        for label, vals, color, dash in series:
            pts = [(xmap(k), ymap(v)) for k, v in enumerate(vals[:10]) if v is not None]
            d_ = f' stroke-dasharray="{dash}"' if dash else ""
            svg.add(f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in pts)}" fill="none" '
                    f'stroke="{color}" stroke-width="2.5"{d_}/>')
            for x, y in pts:
                svg.add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" fill="{color}" stroke="{SURFACE}" stroke-width="1.5"/>')
            ends.append([pts[-1][1], label, pts[-1][0]])
        ends.sort()
        for i in range(1, len(ends)):
            need = 15 + 13 * ends[i - 1][1].count("\n")
            if ends[i][0] - ends[i - 1][0] < need:
                ends[i][0] = ends[i - 1][0] + need
        for y, label, x in ends:
            for li, line in enumerate(label.split("\n")):
                svg.text(x + 10, y + 4 + li * 13, line, size=11, fill=INK if li == 0 else INK2)
    svg.text(24, H - 46, "When contracts differ in how amendment-prone they are, chance alone makes the curve rise. "
                         "Only the deviation from the matched benchmark can point to design.", size=11, fill=INK3)
    svg.text(24, H - 28, "Source: data/processed/amendment_dynamics.json (scripts/amendment_dynamics.py).",
             size=11, fill=INK3)
    svg.save(path)


# --------------------------------------------------------------------------------------
# S3: lock-in fingerprints by sector
# --------------------------------------------------------------------------------------

def lockin_figure(path: Path) -> None:
    d = json.loads((RESULTS / "amendment_fingerprints.json").read_text())
    order = [r["sector"] for r in d["lockin_ranking"]]
    panels = [("escal", "Next amendment larger", "core · share of amendment pairs", 0.3, 1.0, [0.3, 0.5, 0.7, 0.9]),
              ("vendor", "Vendor share of risk", "core · variance share, ledger × department", 0.0, 0.45,
               [0.0, 0.1, 0.2, 0.3, 0.4]),
              ("accel_pre", "Next gap shorter", "supporting · pairs before term end", 0.3, 1.0,
               [0.3, 0.5, 0.7, 0.9])]
    W, top, rh, left = 1180, 130, 30, 250
    H = top + rh * len(order) + 110
    svg = Svg(W, H, "S3. Lock-in fingerprints by sector")
    svg.text(24, 36, "S3. Lock-in fingerprints, sector by sector", size=18, weight="bold")
    svg.text(24, 58, "Gray band: what a pure-chance world with the same amendment counts produces (mean ± 2 SD). Dot: "
                     "observed. Filled orange = significantly above chance; open = within or below.", size=12.5, fill=INK2)
    pw = (W - left - 40) / 3
    for pi, (key, title, sub, lo, hi, ticks) in enumerate(panels):
        x0 = left + pi * pw + 10
        x1 = x0 + pw - 30
        xmap = lambda v: x0 + (min(max(v, lo), hi) - lo) / (hi - lo) * (x1 - x0)
        svg.text(x0, top - 40, title, size=13, weight="bold")
        svg.text(x0, top - 24, sub, size=11, fill=INK3)
        for t in ticks:
            svg.line(xmap(t), top - 12, xmap(t), top + rh * len(order) - 6, stroke=RULE)
            svg.text(xmap(t), top + rh * len(order) + 10, f"{t:.1f}", size=10.5,
                     fill=INK3, anchor="middle")
        for ri, name in enumerate(order):
            fp = d["sectors"][name]["fingerprints"].get(key)
            y = top + ri * rh + rh / 2 - 6
            if not fp:
                continue
            m, sd, ob, z = fp["chance_mean"], fp["chance_sd"], fp["observed"], fp["z"]
            svg.add(f'<rect x="{xmap(m - 2 * sd):.1f}" y="{y - 7}" width="{max(2, xmap(m + 2 * sd) - xmap(m - 2 * sd)):.1f}" '
                    f'height="14" rx="3" fill="{GRAY_LIGHT}" opacity="0.7"/>')
            svg.line(xmap(m), y - 7, xmap(m), y + 7, stroke=GRAY, width=1.5)
            sig = z is not None and z >= 2
            svg.add(f'<circle cx="{xmap(ob):.1f}" cy="{y:.1f}" r="5.5" fill="{ORANGE if sig else SURFACE}" '
                    f'stroke="{ORANGE if sig else INK2}" stroke-width="2"/>')
            svg.text(min(xmap(ob) + 10, x1 + 26), y + 4, f"{ob:.2f}", size=10.5, fill=INK2)
    for ri, name in enumerate(order):
        sec = d["sectors"][name]
        y = top + ri * rh + rh / 2 - 6
        thin = sec.get("thin")
        tier = sec.get("evidence_tier")
        svg.text(24, y + 4, SECTOR_LABEL.get(name, name) + (" (thin)" if thin else ""), size=12,
                 weight="bold" if (tier == 1 and not thin) else "normal", fill=INK if not thin else INK2)
        svg.text(left - 6, y + 4, f"tier {tier}", size=11, fill=INK3, anchor="end")
    svg.text(24, H - 46, "Tier 1: vendor-level design + escalation (lock-in) + acceleration. Tier 2: design + escalation. "
                         "Tier 3: vendor-level design only. Within tier, ordered by escalation; thin sectors last.",
             size=11, fill=INK3)
    svg.text(24, H - 28, "Vendor share separates design (gap or lock-in worlds) from chance and routine renewals; "
                         "escalation separates lock-in. Acceleration appears only if dependence grows without limit.",
             size=11, fill=INK3)
    svg.save(path)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    histories_figure(OUT / "s1_simulated_histories.svg")
    continuation_figure(OUT / "s2_continuation_curves.svg")
    lockin_figure(OUT / "s3_lockin_fingerprints.svg")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
