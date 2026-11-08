#!/usr/bin/env python3
"""Generate an interactive HTML visual dashboard from the processed change-order data."""

from __future__ import annotations

import json
from pathlib import Path
import sys

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Public Contract Amendments: Tech vs. Non-Tech & Program Domains</title>
  <style>
    :root {
      --bg: #0f172a;
      --card-bg: #1e293b;
      --border: #334155;
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
      --accent-blue: #38bdf8;
      --accent-emerald: #34d399;
      --accent-amber: #fbbf24;
      --accent-rose: #f43f5e;
      --accent-purple: #c084fc;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background-color: var(--bg);
      color: var(--text-main);
      line-height: 1.5;
      padding: 24px;
    }
    .container { max-width: 1300px; margin: 0 auto; }
    header { margin-bottom: 28px; border-bottom: 1px solid var(--border); padding-bottom: 16px; }
    h1 { font-size: 1.85rem; font-weight: 700; color: #fff; margin-bottom: 6px; }
    p.subtitle { color: var(--text-muted); font-size: 0.95rem; }
    
    .kpi-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 16px;
      margin-bottom: 28px;
    }
    .kpi-card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 18px;
    }
    .kpi-title { font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-muted); margin-bottom: 6px; }
    .kpi-value { font-size: 1.7rem; font-weight: 700; color: #fff; }
    .kpi-sub { font-size: 0.8rem; color: var(--accent-emerald); margin-top: 4px; }
    .kpi-sub.warning { color: var(--accent-amber); }

    .grid-2 {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
      margin-bottom: 28px;
    }
    @media (max-width: 900px) { .grid-2 { grid-template-columns: 1fr; } }

    .panel {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 20px;
      margin-bottom: 28px;
    }
    .panel h2 { font-size: 1.15rem; font-weight: 600; margin-bottom: 14px; display: flex; align-items: center; justify-content: space-between; }
    
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.875rem;
    }
    th, td {
      padding: 10px 12px;
      text-align: left;
      border-bottom: 1px solid var(--border);
    }
    th { color: var(--text-muted); font-weight: 600; text-transform: uppercase; font-size: 0.75rem; letter-spacing: 0.04em; }
    tr:hover td { background-color: rgba(255, 255, 255, 0.02); }
    .num { text-align: right; }
    
    .bar-container {
      background: #334155;
      border-radius: 4px;
      height: 8px;
      width: 100%;
      overflow: hidden;
      margin-top: 4px;
    }
    .bar { height: 100%; border-radius: 4px; }

    .badge {
      display: inline-block;
      padding: 2px 8px;
      border-radius: 9999px;
      font-size: 0.72rem;
      font-weight: 600;
      text-transform: capitalize;
    }
    .badge-health { background: rgba(56, 189, 248, 0.15); color: var(--accent-blue); }
    .badge-safety { background: rgba(244, 63, 94, 0.15); color: var(--accent-rose); }
    .badge-labor { background: rgba(251, 191, 36, 0.15); color: var(--accent-amber); }
    .badge-assist { background: rgba(52, 211, 153, 0.15); color: var(--accent-emerald); }
    .badge-admin { background: rgba(192, 132, 252, 0.15); color: var(--accent-purple); }
    .badge-other { background: rgba(148, 163, 184, 0.15); color: var(--text-muted); }

    .tag-or {
      background: rgba(56, 189, 248, 0.2);
      color: var(--accent-blue);
      padding: 4px 8px;
      border-radius: 4px;
      font-family: monospace;
      font-size: 0.9rem;
      font-weight: bold;
    }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>Public Procurement Change Orders & Amendments Dashboard</h1>
      <p class="subtitle" id="subtitle">Empirical analysis of normalized state and local government contracts</p>
    </header>

    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-title">Total Contracts Analyzed</div>
        <div class="kpi-value" id="kpi-total-contracts">–</div>
        <div class="kpi-sub" id="kpi-total-sub">–</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-title">Total Tech Contracts</div>
        <div class="kpi-value" id="kpi-tech-contracts">–</div>
        <div class="kpi-sub" id="kpi-tech-sub">–</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-title">Tech Amendment Odds Ratio</div>
        <div class="kpi-value"><span class="tag-or" id="kpi-or">–</span></div>
        <div class="kpi-sub" id="kpi-or-sub">–</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-title">Software/SaaS Mean Cost Growth</div>
        <div class="kpi-value" id="kpi-saas">–</div>
        <div class="kpi-sub warning">Steepest Escalation Multiplier</div>
      </div>
    </div>

    <div class="grid-2">
      <!-- Jurisdiction Panel -->
      <div class="panel">
        <h2>Jurisdiction Comparison: Tech vs. Non-Tech</h2>
        <table>
          <thead>
            <tr>
              <th>Jurisdiction</th>
              <th class="num">Tech Amend %</th>
              <th class="num">Non-Tech %</th>
              <th class="num">Relative Risk</th>
            </tr>
          </thead>
          <tbody id="jurisdiction-tbody">
            <!-- Injected by script -->
          </tbody>
        </table>
      </div>

      <!-- Subsector Panel -->
      <div class="panel">
        <h2>Tech Subsector Breakdown</h2>
        <table>
          <thead>
            <tr>
              <th>Subsector</th>
              <th class="num">Contracts</th>
              <th class="num">Amend %</th>
              <th class="num">Mean Growth</th>
            </tr>
          </thead>
          <tbody id="subsector-tbody">
            <!-- Injected by script -->
          </tbody>
        </table>
      </div>
    </div>

    <!-- Functional Program Domain Panel -->
    <div class="panel">
      <h2>Tech Contracts by Functional Program Domain</h2>
      <table>
        <thead>
          <tr>
            <th>Program Domain</th>
            <th class="num">Contracts</th>
            <th class="num">Amended</th>
            <th class="num">Amendment Rate</th>
            <th class="num">Added Dollars</th>
            <th class="num">Mean Growth</th>
          </tr>
        </thead>
        <tbody id="domain-tbody">
          <!-- Injected by script -->
        </tbody>
      </table>
    </div>

    <!-- Econometric Model Panel -->
    <div class="panel">
      <h2>Econometric Model: Multi-Variable Logistic Regression (N = <span id="logit-n">–</span>)</h2>
      <p style="color: var(--text-muted); font-size: 0.85rem; margin-bottom: 12px;">
        Dependent Variable: <code>is_amended (0 or 1)</code>. Controls for contract award scale (log10), duration in days (log10), and jurisdiction fixed effects.
      </p>
      <table>
        <thead>
          <tr>
            <th>Model Feature</th>
            <th class="num">Coefficient</th>
            <th class="num">Std Error</th>
            <th class="num">z-stat</th>
            <th class="num">p-value</th>
            <th class="num">Odds Ratio</th>
            <th>95% Confidence Interval</th>
          </tr>
        </thead>
        <tbody id="logistic-tbody">
          <!-- Injected by script -->
        </tbody>
      </table>
    </div>

    <!-- Top Runaway Case Studies Panel -->
    <div class="panel">
      <h2>Notable Tech Expansion & Runaway Case Studies</h2>
      <table>
        <thead>
          <tr>
            <th>Vendor & Jurisdiction</th>
            <th>Department & Program Domain</th>
            <th>Initial Award</th>
            <th>Dollars Added</th>
            <th class="num">Growth %</th>
            <th class="num">Revisions</th>
          </tr>
        </thead>
        <tbody id="casestudies-tbody">
          <!-- Injected by script -->
        </tbody>
      </table>
    </div>

    <!-- Cooperative purchasing, resellers & certification grades -->
    <div id="coop-section" style="display:none">
      <header style="margin-top: 36px;">
        <h1>Cooperative Purchasing, Resellers &amp; Certification Grades</h1>
        <p class="subtitle">Horizontal vs. vertical cooperation (NASPO ValuePoint, Sourcewell, OMNIA, TIPS, Texas DIR, state contracts); single vs. multiple award; prime vendors vs. authorized resellers</p>
      </header>
      <div class="grid-2">
        <div class="panel">
          <h2>Amendment Rate by Channel (horizontal vs. vertical cooperation)</h2>
          <table>
            <thead><tr><th>Channel</th><th class="num">All: n</th><th class="num">All: amend %</th><th class="num">Tech: n</th><th class="num">Tech: amend %</th></tr></thead>
            <tbody id="channel-tbody"></tbody>
          </table>
        </div>
        <div class="panel">
          <h2>Tech Contracts: Prime/Direct vs. Authorized Reseller</h2>
          <table>
            <thead><tr><th>Vendor role</th><th class="num">Contracts</th><th class="num">Amend %</th><th class="num">Net growth</th></tr></thead>
            <tbody id="role-tbody"></tbody>
          </table>
        </div>
      </div>
      <div class="grid-2">
        <div class="panel">
          <h2>Amendment Rate by Cooperative Vehicle</h2>
          <table>
            <thead><tr><th>Vehicle</th><th class="num">Contracts</th><th class="num">Amend %</th><th class="num">Net growth</th></tr></thead>
            <tbody id="vehicle-tbody"></tbody>
          </table>
        </div>
        <div class="panel">
          <h2>Vendor Certification Grade (Washington)</h2>
          <table>
            <thead><tr><th>Grade</th><th class="num">Contracts</th><th class="num">Amend %</th><th class="num">Net growth</th></tr></thead>
            <tbody id="cert-tbody"></tbody>
          </table>
        </div>
      </div>
      <div class="grid-2">
        <div class="panel">
          <h2>Award Structure (contract ledgers)</h2>
          <table>
            <thead><tr><th>Structure</th><th class="num">Contracts</th><th class="num">Amend %</th><th class="num">Net growth</th></tr></thead>
            <tbody id="award-tbody"></tbody>
          </table>
        </div>
        <div class="panel">
          <h2>Vendor Qualification (contract vehicles held)</h2>
          <table>
            <thead><tr><th>Tier</th><th class="num">Contracts</th><th class="num">Amend %</th><th class="num">Net growth</th></tr></thead>
            <tbody id="qual-tbody"></tbody>
          </table>
        </div>
      </div>
      <div class="panel">
        <h2>Who Buys Through Cooperative Contracts (share of sales)</h2>
        <table>
          <thead><tr><th>Program</th><th class="num">Total sales</th><th class="num">State agency</th><th class="num">Local govt</th><th class="num">K-12</th><th class="num">Higher ed</th><th class="num">Out of state</th><th class="num">Other</th></tr></thead>
          <tbody id="coopsales-tbody"></tbody>
        </table>
      </div>
      <div class="grid-2">
        <div class="panel">
          <h2>Texas DIR: Direct vs. Reseller Sales</h2>
          <table>
            <thead><tr><th>Channel / grade</th><th class="num">Sales</th><th class="num">Share</th></tr></thead>
            <tbody id="txdir-tbody"></tbody>
          </table>
        </div>
        <div class="panel">
          <h2>Logistic Model with Channel, Reseller &amp; Grade Terms</h2>
          <table>
            <thead><tr><th>Feature</th><th class="num">Odds ratio</th><th>95% CI</th><th class="num">p</th></tr></thead>
            <tbody id="coop-logit-tbody"></tbody>
          </table>
        </div>
      </div>
    </div>
  </div>

  <script>
    const DATA = __DATA_PLACEHOLDER__;
    const COOP = __COOP_PLACEHOLDER__;

    // Populate Jurisdictions
    const jBody = document.getElementById('jurisdiction-tbody');
    const jNames = {
      'cook_county': 'Cook County, IL',
      'oregon': 'Oregon (ORPIN)',
      'chicago': 'Chicago, IL',
      'washington_state': 'Washington State'
    };
    for (const [key, val] of Object.entries(DATA.jurisdictions)) {
      const tRate = val.tech.amendment_rate_pct;
      const ntRate = val.non_tech.amendment_rate_pct;
      const relDiff = ntRate ? ((tRate - ntRate) / ntRate * 100).toFixed(1) : '0.0';
      const row = `<tr>
        <td><strong>${jNames[key] || key}</strong></td>
        <td class="num">${tRate.toFixed(1)}%</td>
        <td class="num">${ntRate.toFixed(1)}%</td>
        <td class="num" style="color: ${relDiff > 0 ? 'var(--accent-emerald)' : 'var(--text-muted)'}">${relDiff > 0 ? '+' : ''}${relDiff}%</td>
      </tr>`;
      jBody.innerHTML += row;
    }

    // Populate Subsectors
    const subBody = document.getElementById('subsector-tbody');
    for (const [key, val] of Object.entries(DATA.subsectors)) {
      const row = `<tr>
        <td><code>${key}</code></td>
        <td class="num">${val.total_contracts.toLocaleString()}</td>
        <td class="num">${val.amendment_rate_pct.toFixed(1)}%</td>
        <td class="num">${val.mean_cost_growth_pct.toFixed(1)}%</td>
      </tr>`;
      subBody.innerHTML += row;
    }

    // Populate Domains
    const domBody = document.getElementById('domain-tbody');
    const badgeMap = {
      'health_care': 'badge-health',
      'public_safety': 'badge-safety',
      'labor_workforce': 'badge-labor',
      'public_assistance': 'badge-assist',
      'administration_finance': 'badge-admin'
    };
    for (const [key, val] of Object.entries(DATA.program_domains)) {
      const badgeCls = badgeMap[key] || 'badge-other';
      const row = `<tr>
        <td><span class="badge ${badgeCls}">${key.replace(/_/g, ' ')}</span></td>
        <td class="num">${val.total_contracts.toLocaleString()}</td>
        <td class="num">${val.amended_contracts.toLocaleString()}</td>
        <td class="num"><strong>${val.amendment_rate_pct.toFixed(1)}%</strong></td>
        <td class="num">$${(val.added_dollars / 1e6).toFixed(1)}M</td>
        <td class="num" style="color: ${val.mean_cost_growth_pct > 200 ? 'var(--accent-amber)' : 'inherit'}">${val.mean_cost_growth_pct.toFixed(1)}%</td>
      </tr>`;
      domBody.innerHTML += row;
    }

    // Populate Logistic Regression
    const logBody = document.getElementById('logistic-tbody');
    for (const row of DATA.logistic_regression.coefficients) {
      const pStr = row.p_value < 0.001 ? '< 0.001' : row.p_value.toFixed(4);
      const isKey = row.feature === 'is_tech';
      logBody.innerHTML += `<tr style="${isKey ? 'background: rgba(56, 189, 248, 0.08); font-weight: bold;' : ''}">
        <td><code>${row.feature}</code></td>
        <td class="num">${row.coef.toFixed(4)}</td>
        <td class="num">${row.std_err.toFixed(4)}</td>
        <td class="num">${row.z_stat.toFixed(2)}</td>
        <td class="num">${pStr}</td>
        <td class="num" style="color: ${isKey ? 'var(--accent-blue)' : 'inherit'}">${row.odds_ratio.toFixed(4)}</td>
        <td>[${row.ci_95[0].toFixed(2)}, ${row.ci_95[1].toFixed(2)}]</td>
      </tr>`;
    }

    // Populate Case Studies
    const caseBody = document.getElementById('casestudies-tbody');
    for (const c of DATA.top_case_studies.slice(0, 8)) {
      const row = `<tr>
        <td><strong>${c.vendor_name}</strong><br><small style="color: var(--text-muted); text-transform: uppercase;">${c.jurisdiction}</small></td>
        <td>${c.department}<br><span class="badge ${badgeMap[c.tech_domain] || 'badge-other'}">${(c.tech_domain || 'tech').replace(/_/g, ' ')}</span></td>
        <td>$${c.initial_award_val.toLocaleString(undefined, {maximumFractionDigits: 0})}</td>
        <td style="color: var(--accent-emerald);">+$${c.delta_val.toLocaleString(undefined, {maximumFractionDigits: 0})}</td>
        <td class="num"><strong>+${c.pct_growth.toFixed(1)}%</strong></td>
        <td class="num">${c.amendment_count}</td>
      </tr>`;
      caseBody.innerHTML += row;
    }

    // KPIs computed from results
    {
      const t = DATA.overall.tech, n = DATA.overall.non_tech;
      const total = t.total_contracts + n.total_contracts;
      const nJur = Object.keys(DATA.jurisdictions).length;
      document.getElementById('kpi-total-contracts').textContent = total.toLocaleString();
      document.getElementById('kpi-total-sub').textContent = `Across ${nJur} jurisdictions`;
      document.getElementById('subtitle').textContent =
        `Empirical analysis of ${total.toLocaleString()} normalized contracts across ${nJur} state and local jurisdictions`;
      document.getElementById('kpi-tech-contracts').textContent = t.total_contracts.toLocaleString();
      document.getElementById('kpi-tech-sub').textContent = `${(100 * t.total_contracts / total).toFixed(1)}% of total portfolio`;
      const tech = DATA.logistic_regression.coefficients.find(r => r.feature === 'is_tech');
      document.getElementById('kpi-or').textContent = `OR = ${tech.odds_ratio.toFixed(2)}`;
      document.getElementById('kpi-or-sub').textContent =
        `${((tech.odds_ratio - 1) * 100).toFixed(1)}% higher odds (p ${tech.p_value < 0.001 ? '< 0.001' : '= ' + tech.p_value.toFixed(3)})`;
      document.getElementById('kpi-saas').textContent = `+${DATA.subsectors.software_saas.mean_cost_growth_pct.toFixed(1)}%`;
      document.getElementById('logit-n').textContent = DATA.logistic_regression.n_obs.toLocaleString();
    }

    // Cooperative / reseller section
    if (COOP) {
      document.getElementById('coop-section').style.display = 'block';
      const pct = v => (v === undefined ? '–' : `${v.toFixed(1)}%`);
      const money = v => v >= 1e9 ? `$${(v / 1e9).toFixed(2)}B` : `$${(v / 1e6).toFixed(1)}M`;
      const lab = k => k.replace(/_/g, ' ');

      const ch = document.getElementById('channel-tbody');
      for (const [k, v] of Object.entries(COOP.by_channel_all || {})) {
        const t = (COOP.by_channel_tech || {})[k] || {};
        ch.innerHTML += `<tr><td>${lab(k)}</td><td class="num">${v.total_contracts.toLocaleString()}</td>
          <td class="num">${pct(v.amendment_rate_pct)}</td><td class="num">${(t.total_contracts || 0).toLocaleString()}</td>
          <td class="num">${pct(t.amendment_rate_pct)}</td></tr>`;
      }
      const simple = (id, obj) => {
        const el = document.getElementById(id);
        for (const [k, v] of Object.entries(obj || {})) {
          el.innerHTML += `<tr><td>${lab(k)}</td><td class="num">${v.total_contracts.toLocaleString()}</td>
            <td class="num">${pct(v.amendment_rate_pct)}</td><td class="num">${pct(v.net_portfolio_growth_pct)}</td></tr>`;
        }
      };
      simple('role-tbody', COOP.by_vendor_role_tech);
      simple('vehicle-tbody', COOP.by_coop_vehicle);
      simple('cert-tbody', COOP.by_certification);
      simple('award-tbody', COOP.by_award_structure);
      simple('qual-tbody', COOP.by_qualification_tier);

      const cs = document.getElementById('coopsales-tbody');
      for (const [prog, v] of Object.entries(COOP.cooperative_sales || {})) {
        const c = v.by_customer_type, sh = k => c[k] ? c[k].share_pct : 0;
        const known = ['state_agency', 'local_government', 'k12', 'higher_ed', 'out_of_state'];
        const other = 100 - known.reduce((a, k) => a + sh(k), 0);
        cs.innerHTML += `<tr><td>${lab(prog)}</td><td class="num">${money(v.total_sales)}</td>
          ${known.map(k => `<td class="num">${sh(k).toFixed(1)}%</td>`).join('')}<td class="num">${other.toFixed(1)}%</td></tr>`;
      }

      const tx = (COOP.cooperative_sales || {}).texas_dir;
      if (tx) {
        const el = document.getElementById('txdir-tbody');
        const block = (title, obj) => {
          el.innerHTML += `<tr><td colspan="3" style="color: var(--text-muted); font-size: 0.8rem; text-transform: uppercase;">${title}</td></tr>`;
          for (const [k, v] of Object.entries(obj || {}))
            el.innerHTML += `<tr><td>${lab(k)}</td><td class="num">${money(v.sales)}</td><td class="num">${v.share_pct.toFixed(1)}%</td></tr>`;
        };
        block('Sales channel', tx.by_sales_channel);
        block('Prime grade (direct sales)', tx.prime_cert_direct_sales);
        block('Prime grade (reseller sales)', tx.prime_cert_reseller_sales);
        block('Reseller grade (reseller sales)', tx.reseller_cert_reseller_sales);
      }

      const lg = document.getElementById('coop-logit-tbody');
      for (const r of ((COOP.logit_pooled || {}).coefficients || [])) {
        if (r.feature.startsWith('jurisdiction_') || r.feature === 'Intercept') continue;
        lg.innerHTML += `<tr><td><code>${r.feature}</code></td><td class="num">${r.odds_ratio.toFixed(3)}</td>
          <td>[${r.ci_95[0].toFixed(2)}, ${r.ci_95[1].toFixed(2)}]</td>
          <td class="num">${r.p_value < 0.001 ? '< 0.001' : r.p_value.toFixed(3)}</td></tr>`;
      }
    }
  </script>
</body>
</html>
"""

def main() -> int:
    results_path = Path("data/processed/tech_analysis_results.json")
    if not results_path.exists():
        print(f"Error: {results_path} not found. Run scripts/analyze_tech_impact.py first.", file=sys.stderr)
        return 1

    with results_path.open(encoding="utf-8") as f:
        data = json.load(f)

    coop_path = Path("data/processed/cooperative_reseller_results.json")
    coop = None
    if coop_path.exists():
        with coop_path.open(encoding="utf-8") as f:
            coop = json.load(f)
    else:
        print(f"Note: {coop_path} not found; skipping cooperative/reseller section "
              "(run scripts/analyze_cooperative_resellers.py).", file=sys.stderr)

    html_content = HTML_TEMPLATE.replace("__DATA_PLACEHOLDER__", json.dumps(data, indent=2))
    html_content = html_content.replace("__COOP_PLACEHOLDER__", json.dumps(coop, default=str))

    out_path = Path("data/processed/dashboard.html")
    with out_path.open("w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"Successfully generated interactive dashboard: {out_path}", file=sys.stderr)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

