#!/usr/bin/env python3
"""Classify why amendments happened, from the reason text the ledgers record.

Maps each amendment's stated reason to the chance-vs-design framework of
game_theory/amendments/04_chance_vs_design.md:

  chance      outside events the vendor does not control: legislation/regulation,
              external funding, emergencies, demand or caseload changes
  design      reasons the theory links to vendor strategy: restoring omitted or unclear
              scope, change orders for unforeseen work, price/rate increases without new
              scope, bridge extensions that postpone re-procurement, paid fixes
  ambiguous   could be either: time extensions and funding increases with no stated cause,
              generic scope additions
  neutral     not a change in the deal: planned renewal options, administrative corrections,
              assignments and name changes
  uninformative  text such as "Amendment", "Y", "Cost"

Sources with reason text: Washington `contract_modifications` (amendment rows) and Chicago
revision descriptions. Oregon and Cook County amendment text repeats the contract title, so
it is not classified. Chicago's contract PDFs would give fuller reasons but sit behind a
JavaScript document viewer (see game_theory/amendments/07_simulated_implications.md).

Outputs: data/processed/amendment_reasons.csv, data/processed/amendment_reasons_summary.json
"""

from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

PROCESSED = Path("data/processed")

# (reason, bin, pattern). Order matters: the first match wins.
RULES: list[tuple[str, str, re.Pattern[str]]] = [
    ("administrative", "neutral", re.compile(
        r"correct|clerical|administrative|name change|assign|novation|address|contact|signat|typo|"
        r"insurance|w-?9|tax id|reallocat|move funds|re-?align|replace (?:exhibit|attachment)|language|"
        r"update (?:exhibit|attachment|terms)|boilerplate|housekeeping|technical amendment", re.I)),
    # Cost-of-living increases granted by the government (e.g. Chicago delegate agencies) are a
    # policy decision, not a vendor-initiated price change.
    ("cost_of_living", "neutral", re.compile(r"\bCOLA\b|cost of living", re.I)),
    ("renewal_option", "neutral", re.compile(
        r"exercis\w* (?:the )?(?:option|renewal)|option (?:year|period|to (?:renew|extend))|renewal option|"
        r"optional (?:renewal|extension)|per (?:the )?(?:original )?(?:contract|agreement) (?:terms|option)|"
        r"(?:first|second|third|1st|2nd|3rd) (?:renewal|extension)", re.I)),
    ("legal_regulatory", "chance", re.compile(
        r"legislat|statut|\blaw\b|new rule|rule change|regulat|mandat|federal requirement|court order|ruling|"
        r"\bRCW\b|\bWAC\b|\bE?S?S?[HS]B\b|\bHB ?\d|\bSB ?\d|compliance with|policy change", re.I)),
    ("emergency", "chance", re.compile(
        r"covid|pandemic|emergency (?:declaration|response|order|proclamation)|disaster declaration|wildfire|"
        r"outbreak", re.I)),
    ("external_funding", "chance", re.compile(
        r"grant|federal fund|appropriat|allotment|proviso|carryover|carry-over|\bARPA\b|\bCARES\b|\bFEMA\b|"
        r"\bHUD\b|\bCDBG\b|new biennium|biennium budget|supplemental (?:funding|budget|appropriation)", re.I)),
    ("demand_volume", "chance", re.compile(
        r"caseload|volume|additional (?:clients|participants|students|beds|slots|cases|units|referrals|youth)|"
        r"increase\w* (?:in )?(?:demand|enrollment|usage|participants|clients)|higher (?:demand|usage)", re.I)),
    ("bridge_extension", "design", re.compile(
        r"until (?:a )?(?:new|replacement|successor) (?:contract|procurement|vendor|system)|pending (?:re-?)?procure|"
        r"bridge (?:contract|agreement|period|extension)|transition (?:period|services)|"
        r"continue (?:services|operations) (?:until|while|during)|interim (?:contract|agreement|period|services)|"
        r"re-?procurement|new rfp|while (?:the )?(?:agency|department) (?:procures|solicits)", re.I)),
    ("scope_restore_change_order", "design", re.compile(
        r"change order|omitted|inadvertent|not included in (?:the )?original|clarif\w* (?:of )?(?:the )?"
        r"(?:scope|deliverable|requirement)|unforeseen|unanticipated|additional work (?:required|needed)|"
        r"originally (?:intended|required)|missing", re.I)),
    ("price_adjustment", "design", re.compile(
        r"rate increase|price increase|escalat|increase\w* (?:the )?(?:hourly |unit )?(?:rate|price)|"
        r"inflation|rate adjust|price adjust|new rates", re.I)),
    ("paid_fix", "design", re.compile(r"defect|\bbug|remediat|warranty|fix(?:es|ing)?\b", re.I)),
    ("renewal_unspecified", "ambiguous", re.compile(r"\brenew", re.I)),
    ("scope_addition", "ambiguous", re.compile(
        r"scope|\bsow\b|statement of work|deliverable|additional (?:services|work|tasks?|functionality|modules?)|"
        r"add(?:s|ed|ing)? (?:services|tasks?|work|functionality|module|deliverable|component)|expand|enhance|"
        r"new (?:services?|tasks?|module|phase)|phase", re.I)),
    ("time_extension", "ambiguous", re.compile(
        r"extend|extension|ext\b|period of performance|end date|term\b|time only|no[- ]cost", re.I)),
    ("funding_increase", "ambiguous", re.compile(
        r"add(?:s|ed|ing)? (?:funds|funding|dollars|money|\$)|increase\w* (?:the )?(?:contract )?"
        r"(?:amount|funding|maximum|ceiling|limit|value|compensation|budget|total)|vendor limit|\bcost\b|"
        r"additional (?:funds|funding)|\badd\w*\b.{0,40}\b(?:fund\w*|compensation|dollars)\b", re.I)),
]

UNINFORMATIVE = re.compile(r"^\s*(?:amendment|amend|amendments other|other|y|n|na|n/a|none|yes|no|cost|sow cost|"
                           r"revision|original|new contract|\d+|-|\.)?\s*$", re.I)


CHICAGO_CHANGE_NOTE = re.compile(
    r"^\s*(?:EXT|EXTEND|EXTENSION|INCREASE|INCR|ADD|ADDING|COLA|AMEND|MODIFY|MOD|REVISE|CHANGE|DECREASE|RENEW|"
    r"CORRECT|TO (?:EXTEND|INCREASE|ADD|CORRECT|PROVIDE|REFLECT|CHANGE))\b|\bCOLA\b|EXT(?:END)? \d+ (?:DAYS|MONTHS)|"
    r"INCREASE (?:VENDOR )?LIMIT|ADD(?:ING)? FUNDS|TIME EXTENSION", re.I)


def classify(text: str) -> tuple[str, str]:
    t = (text or "").strip()
    if UNINFORMATIVE.match(t):
        return "uninformative", "uninformative"
    for reason, bin_, pat in RULES:
        if pat.search(t):
            return reason, bin_
    return "other_stated", "ambiguous"


def main() -> int:
    contracts = {}
    with (PROCESSED / "contracts_normalized.csv").open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            contracts[(r["jurisdiction"], r["contract_id"])] = r
    titles = {k: (v["title_desc"] or "").strip().upper() for k, v in contracts.items()}

    rows = []
    with (PROCESSED / "amendments_normalized.csv").open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            j = r["jurisdiction"]
            if j == "washington_state":
                text = r["category"]
            elif j == "chicago":
                # Chicago revision rows mostly carry the PO title (often with a T-number or program-code
                # prefix). Keep only text written as a change note.
                text = r["description"]
                if text.strip().upper() == titles.get((j, r["contract_id"]), "") or not CHICAGO_CHANGE_NOTE.search(text):
                    text = ""
            else:
                continue
            reason, bin_ = classify(text)
            c = contracts.get((j, r["contract_id"]), {})
            rows.append({"jurisdiction": j, "contract_id": r["contract_id"], "amendment_seq": r["amendment_seq"],
                         "amendment_date": r["amendment_date"], "reason": reason, "reason_bin": bin_,
                         "is_tech": c.get("is_tech", ""), "tech_subsector": c.get("tech_subsector", ""),
                         "tech_domain": c.get("tech_domain", ""), "text": text[:200]})

    with (PROCESSED / "amendment_reasons.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    summary: dict = {"by_jurisdiction": {}, "by_sector": {}, "by_domain": {}}
    for key, field in (("by_jurisdiction", "jurisdiction"), ("by_sector", "tech_subsector"), ("by_domain", "tech_domain")):
        groups: dict[str, Counter] = defaultdict(Counter)
        reasons: dict[str, Counter] = defaultdict(Counter)
        for r in rows:
            g = r[field] or "unknown"
            if field == "tech_domain" and r["is_tech"] != "1":
                g = "non_tech"
            groups[g][r["reason_bin"]] += 1
            reasons[g][r["reason"]] += 1
        for g, c in groups.items():
            informative = sum(v for k, v in c.items() if k != "uninformative")
            causal = c["chance"] + c["design"]
            summary[key][g] = {
                "amendments": sum(c.values()), "informative": informative,
                "bins": dict(c), "reasons": dict(reasons[g].most_common()),
                "design_share_of_informative": round(c["design"] / informative, 4) if informative else None,
                "chance_share_of_informative": round(c["chance"] / informative, 4) if informative else None,
                "design_share_of_causal": round(c["design"] / causal, 4) if causal else None,
                "causal_reasons": causal,
            }
    (PROCESSED / "amendment_reasons_summary.json").write_text(json.dumps(summary, indent=1))
    for g, s in sorted(summary["by_sector"].items()):
        print(f"{g:18} n={s['amendments']:>7,} informative={s['informative']:>6,} bins={s['bins']} "
              f"design/causal={s['design_share_of_causal']}")
    print("jurisdictions:", {g: (s["amendments"], s["informative"]) for g, s in summary["by_jurisdiction"].items()})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
