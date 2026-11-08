#!/usr/bin/env python3
"""Synthesis step 6: why amendments happened, read from the amendment documents themselves.

Chicago links every contract revision to its document. The viewer page embeds a direct PDF link
(ecm.chicago.gov ... DPSWebDocumentViewer?id=...&osName=eContentContracts&el=0&image=image). The
PDFs are scans, so the first pages are OCR'd with macOS Vision (synthesis/tools/ocr.swift).

    python3 synthesis/document_sample.py sample     # draw the stratified sample (no network)
    python3 synthesis/document_sample.py download   # fetch PDFs politely (one at a time, 3 s apart)
    python3 synthesis/document_sample.py ocr        # OCR first pages (macOS only; builds the helper)
    python3 synthesis/document_sample.py code       # classify stated purpose, summarize

Sample: Chicago revisions (revision_number > 0) with a document, stratified by sector
(software & SaaS, general technology, hardware & telecom, IT services, non-technology) x amendment
order (1st, 2nd-3rd, 4th+), 20 per stratum (300 total), fixed seed. Each sampled revision also
carries the fingerprint the simulations use: whether it is larger than the previous positive
revision (escalation).

Outputs: synthesis/results/document_sample.csv, document_codes.csv, document_summary.json.
PDFs and OCR text: data/raw/chicago_documents/ (git-ignored).
"""

from __future__ import annotations

import csv
import json
import random
import re
import subprocess
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import parse_qs, quote, urlparse

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "scripts"))
from amendment_reasons import RULES, classify  # noqa: E402

RESULTS = HERE / "results"
DOCS = ROOT / "data" / "raw" / "chicago_documents"
OCR_BIN = HERE / "tools" / "ocr"
PER_STRATUM = 20
PAUSE_SECONDS = 3.0
SECTORS = {"software_saas": "software & SaaS", "tech_general": "general technology",
           "hardware_telecom": "hardware & telecom", "it_services": "IT services", "non_tech": "non-technology"}


def order_bucket(k: int) -> str:
    return "1st" if k == 1 else "2nd-3rd" if k <= 3 else "4th+"


def num(v) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def direct_url(viewer_url: str) -> str | None:
    q = parse_qs(urlparse(viewer_url).query)
    doc_id = (q.get("id") or [None])[0]
    if not doc_id:
        return None
    return ("https://ecm.chicago.gov/eSMARTContracts/service/DPSWebDocumentViewer?id="
            f"{quote(doc_id)}&osName=eContentContracts&el=0&image=image")


def cmd_sample() -> None:
    sector = {}
    for r in csv.DictReader((ROOT / "data/processed/contracts_normalized.csv").open(encoding="utf-8")):
        if r["jurisdiction"] == "chicago":
            sector[r["contract_id"]] = r["tech_subsector"]
    raw = json.loads((ROOT / "data/raw/chicago/records.json").read_text())
    by_po: dict[str, list[dict]] = defaultdict(list)
    for r in raw:
        if r.get("purchase_order_contract_number"):
            by_po[r["purchase_order_contract_number"]].append(r)
    frame = []
    for po, rows in by_po.items():
        revs = sorted((r for r in rows if str(r.get("revision_number")) not in ("0", "", "None")),
                      key=lambda r: (int(num(r.get("revision_number"))), r.get("approval_date") or ""))
        prev_pos = None
        for k, r in enumerate(revs, 1):
            amt = num(r.get("award_amount"))
            escal = None
            if amt > 0:
                escal = (amt > prev_pos) if prev_pos is not None else None
                prev_pos = amt
            url = (r.get("contract_pdf") or {}).get("url")
            if not url or po not in sector:
                continue
            frame.append({"po": po, "revision_number": r.get("revision_number"), "order": k,
                          "order_bucket": order_bucket(k), "sector": sector[po],
                          "approval_date": (r.get("approval_date") or "")[:10], "award_amount": amt,
                          "escalating": escal, "department": r.get("department") or "",
                          "vendor": r.get("vendor_name") or "", "description": r.get("purchase_order_description") or "",
                          "viewer_url": url, "pdf_url": direct_url(url)})
    rng = random.Random(20261108)
    strata: dict[tuple, list[dict]] = defaultdict(list)
    for f in frame:
        strata[(f["sector"], f["order_bucket"])].append(f)
    sample = []
    for s in SECTORS:
        for b in ("1st", "2nd-3rd", "4th+"):
            pool = strata.get((s, b), [])
            take = rng.sample(pool, min(PER_STRATUM, len(pool)))
            for t in take:
                t["stratum_size"] = len(pool)
            sample += take
    for i, s in enumerate(sample):
        s["doc_key"] = f"{s['po']}_r{s['revision_number']}"
    RESULTS.mkdir(parents=True, exist_ok=True)
    with (RESULTS / "document_sample.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(sample[0]))
        w.writeheader()
        w.writerows(sample)
    print(f"frame={len(frame):,} revisions with documents; sample={len(sample)}")
    print(Counter((s["sector"], s["order_bucket"]) for s in sample))


def load_sample() -> list[dict]:
    return list(csv.DictReader((RESULTS / "document_sample.csv").open(encoding="utf-8")))


def cmd_download() -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    sample = load_sample()
    got = 0
    for i, s in enumerate(sample, 1):
        out = DOCS / f"{s['doc_key']}.pdf"
        if any((DOCS / f"{s['doc_key']}{ext}").exists() for ext in (".pdf", ".unavailable")):
            continue
        if not s["pdf_url"]:
            continue
        r = subprocess.run(["curl", "-sSL", "--max-time", "180", "-A", "change-order-research/1.0",
                            "-o", str(out), "-w", "%{http_code} %{content_type}", s["pdf_url"]],
                           capture_output=True, text=True)
        status = r.stdout.strip()
        if status.startswith("200") and ("image/png" in status or "image/tif" in status):
            # For older records (mostly 2003-2011) the server returns the City of Chicago logo
            # (a 287x54 PNG) instead of a document: the document is not available online.
            out.unlink(missing_ok=True)
            (DOCS / f"{s['doc_key']}.unavailable").write_text(status)
            print(f"[{i}/{len(sample)}] {s['doc_key']}: not available online ({status})")
        elif not status.startswith("200") or "pdf" not in status:
            print(f"[{i}/{len(sample)}] {s['doc_key']}: {status or r.stderr.strip()[:80]}")
            out.unlink(missing_ok=True)
        else:
            got += 1
            if got % 25 == 0:
                print(f"[{i}/{len(sample)}] downloaded {got}", flush=True)
        time.sleep(PAUSE_SECONDS)
    print(f"downloaded {got} new documents; total on disk "
          f"{sum(1 for p in DOCS.iterdir() if p.suffix in ('.pdf', '.png', '.tif'))}")


def cmd_ocr(pages: int = 4) -> None:
    if not OCR_BIN.exists():
        subprocess.run(["swiftc", "-O", str(HERE / "tools" / "ocr.swift"), "-o", str(OCR_BIN)], check=True)
    n = 0
    for pdf in sorted(list(DOCS.glob("*.pdf")) + list(DOCS.glob("*.png")) + list(DOCS.glob("*.tif"))):
        txt = pdf.with_suffix(".txt")
        if txt.exists():
            continue
        r = subprocess.run([str(OCR_BIN), str(pdf), str(pages)], capture_output=True, text=True)
        txt.write_text(r.stdout, encoding="utf-8")
        n += 1
        if n % 25 == 0:
            print(f"OCR {n}", flush=True)
    print(f"OCR'd {n} documents")


# ---- coding -------------------------------------------------------------------------

PURPOSE = re.compile(
    r"(whereas[^.;]{0,400}[.;])|((?:this|the)\s+(?:amendment|modification|revision|change order)[^.]{0,400}\.)|"
    r"((?:purpose|in order) (?:of|to)[^.]{0,300}\.)|((?:agree|agrees) (?:to|that)[^.]{0,300}\.)|"
    r"((?:extend|increase|add|modify|amend)\w*\s[^.]{0,300}\.)", re.I)
DOC_TYPE = [
    ("amendment/modification", re.compile(r"\bamendment\b|\bmodification\b|\bmodify\b", re.I)),
    ("change order", re.compile(r"change order", re.I)),
    ("renewal/extension", re.compile(r"\brenew|\bextension\b|\bextend", re.I)),
    ("original contract text", re.compile(r"request for proposal|specification|bid (?:form|proposal)|"
                                          r"general conditions|scope of services", re.I)),
]


# Chicago's standard justification, in the summary report and again in the recitals
BOILERPLATE = re.compile(
    r"(?:(?:it has been determined|(?:chief procurement officer|cpo) has determined).{0,700}?authori[sz]ed\s+\w{1,3}\s+law\.?)"
    r"|(?:[^.]{0,300}germane to the original (?:agreement|contract)[^.]{0,300}\.?)"   # OCR variants of the same text
    r"|(?:[^.]{0,200}mayoral executive order[^.]{0,400}\.)"                          # minimum-wage clause
    r"|(?:[^.]{0,200}regulations governing the administration of compensation plan[^.]{0,300}\.)"
    r"|(?:[^.]{0,120}(?:state and federal )?law enforcement officers[^.]{0,200}\.)"
    # standard recital that updates boilerplate terms; not the reason for the amendment
    r"|(?:incorporate certain terms,? conditions,? and changes in laws? and/or city polic\w+[^.;]{0,120})", re.I | re.S)
MOD_TYPES = [  # Chicago "Mod Reason" vocabulary -> change type
    ("time extension", re.compile(r"TIME EXT|EXTENSION|EXTEND|RENEW", re.I)),
    ("vendor limit increase (funds)", re.compile(r"\bVLI\b|VENDOR LIMIT|INCREASE|ADD(?:ITIONAL)? FUND|FUNDING", re.I)),
    ("scope change", re.compile(r"SCOPE|ADD(?:ITIONAL)? (?:WORK|SERVICES|ITEMS|LINE)|NEW ITEMS|CHANGE ORDER", re.I)),
    ("price change", re.compile(r"PRICE|RATE|ESCALAT|COLA", re.I)),
    ("administrative", re.compile(r"ASSIGN|NAME CHANGE|NOVATION|CORRECT|ADMIN|ADDRESS|INSURANCE|DECREASE|REDUC", re.I)),
]
CAUSES = [  # cause statements in the description and recitals
    ("chance: grant or outside funding", "chance", re.compile(
        r"grant (?:award|funds|funding)|federal (?:funds|funding|award)|state (?:funds|funding|grant)|"
        r"\bHUD\b|\bCDBG\b|\bARPA\b|CARES act|appropriat\w+ (?:by|from) the (?:state|federal)|"
        r"(?:FEMA|DOJ|BJA|HHS|IDPH|IDHS) ", re.I)),
    ("chance: law, regulation or new program", "chance", re.compile(
        r"(?:new|amended|recent|change[sd]? (?:in|to) (?:the )?)(?:state |federal )?(?:law|statute|regulation|rule)s?|"
        r"public act \d|legislat\w+|consent decree|court order|federal (?:mandate|requirement)|state mandate|"
        r"(?:new|city) program (?:for|to)|utility relief|relief program", re.I)),
    ("chance: emergency / COVID", "chance", re.compile(r"covid|pandemic|emergency declaration|disaster", re.I)),
    ("chance: demand or volume", "chance", re.compile(
        r"(?:increase\w*|higher|additional) (?:demand|usage|volume|caseload|participants|ridership|clients)", re.I)),
    ("design: change order / unforeseen work", "design", re.compile(
        r"change order|additional work (?:required|necessary)|unforeseen (?:conditions|work)|not included in the "
        r"original|omitted|inadvertent", re.I)),
    ("re-competition delayed: extended until a new contract is awarded", "re-competition delayed", re.compile(
        r"(?:until|pending|while) (?:a |the )?(?:new|replacement|successor) (?:contract|agreement|vendor|solicitation|"
        r"procurement)|re-?procure|new (?:rfp|solicitation) (?:is|has)", re.I)),
    ("neutral: planned price adjustment under the contract", "neutral", re.compile(
        r"pursuant to [^.]{0,120}(?:price adjustment|rate adjustment|escalation|labor rate)[^.]{0,40}(?:clause|section|"
        r"provision|of the contract)|price adjustment for material costs", re.I)),
    ("design: price or rate increase", "design", re.compile(
        r"(?:rate|price|fee)s? increase|increase (?:in )?(?:the )?(?:hourly |unit )?(?:rates?|prices?|fees?)", re.I)),
    ("design: system / license dependence", "design", re.compile(
        r"(?:sole|proprietary|only) (?:source|vendor|provider)|maintenance and support of (?:the )?(?:existing|"
        r"current)|licen[cs]e (?:renewal|fees)|upgrade (?:of|to) the (?:existing|current)", re.I)),
]


def field_after(lines: list[str], label: str, stop: tuple[str, ...]) -> str:
    for i, ln in enumerate(lines):
        if ln.strip().lower().startswith(label.lower()):
            out = []
            for nxt in lines[i + 1:i + 14]:
                t = nxt.strip()
                if any(t.lower().startswith(x.lower()) for x in stop):
                    break
                if t and not re.fullmatch(r"[\d\s\-/.]+", t):
                    out.append(t)
            return " ".join(out)
    return ""


def code_text(text: str) -> dict:
    lines = text.splitlines()
    mod_reason = field_after(lines, "Mod Reason", ("Description", "Term of Contract"))
    description = field_after(lines, "Description", ("Term of Contract", "Procurement Services"))
    body = BOILERPLATE.sub(" ", re.sub(r"\s+", " ", text))
    passages = [m.group(0) for m in PURPOSE.finditer(body)][:80]
    # causes come only from the amendment's own purpose: Mod Reason, description, recitals, operative clauses
    recitals = " ".join(m.group(0) for m in re.finditer(r"whereas[^;]{0,500}[;.]", body, re.I))
    ops = ""
    m = re.search(r"agree[s]? (?:as follows|that)", body, re.I)
    if m:
        ops = body[m.end():m.end() + 1500]
    cause_text = " ".join((mod_reason, description, recitals, ops))
    type_text = mod_reason + " " + description if (mod_reason or description) else recitals + " " + ops[:600]
    types = [name for name, pat in MOD_TYPES if pat.search(type_text)]
    causes = [name for name, bin_, pat in CAUSES if pat.search(cause_text)]
    bins = {bin_ for name, bin_, pat in CAUSES if name in causes}
    if "neutral" in bins:  # a price change made under the contract's own clause is planned, not designed
        causes = [c for c in causes if not c.startswith("design: price")]
        bins = {bin_ for name, bin_, pat in CAUSES if name in causes}
    if "design" in bins and "chance" in bins:
        primary = "design + chance"
    elif "design" in bins:
        primary = "design"
    elif "chance" in bins:
        primary = "chance"
    elif "re-competition delayed" in bins:
        primary = "re-competition delayed"
    elif "neutral" in bins:
        primary = "neutral"
    else:
        primary = "no cause stated"
    dtype = [name for name, pat in DOC_TYPE if pat.search(body[:4000])]
    return {"chars": len(body), "has_summary_report": int("modification summary report" in body.lower()),
            "mod_reason": mod_reason[:120], "description": description[:200],
            "change_types": ";".join(types) or "unclassified", "causes": ";".join(causes),
            "primary_bin": primary, "doc_type": ";".join(dtype),
            "excerpt": " | ".join(p[:220] for p in passages[:4])}


def cmd_code() -> None:
    sample = load_sample()
    rows = []
    for s in sample:
        txt = DOCS / f"{s['doc_key']}.txt"
        if not txt.exists():
            continue
        c = code_text(txt.read_text(encoding="utf-8", errors="ignore"))
        rows.append({**{k: s[k] for k in ("doc_key", "po", "revision_number", "order", "order_bucket", "sector",
                                          "approval_date", "award_amount", "escalating", "department", "vendor")},
                     **c})
    with (RESULTS / "document_codes.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    summ: dict = {"documents_coded": len(rows), "by_sector": {}, "by_order": {}, "by_escalation": {}}
    for key, field in (("by_sector", "sector"), ("by_order", "order_bucket"), ("by_escalation", "escalating")):
        g = defaultdict(Counter)
        for r in rows:
            g[r[field] or "n/a"][r["primary_bin"]] += 1
        summ[key] = {k: dict(v) for k, v in g.items()}
    summ["change_types"] = dict(Counter(x for r in rows for x in r["change_types"].split(";") if x))
    summ["causes"] = dict(Counter(x for r in rows for x in r["causes"].split(";") if x))
    summ["with_summary_report"] = sum(int(r["has_summary_report"]) for r in rows)
    (RESULTS / "document_summary.json").write_text(json.dumps(summ, indent=1))
    print(json.dumps(summ, indent=1))


def agreement() -> None:
    """Compare automated primary codes with the manual review (synthesis/results/document_manual_review.csv)."""
    man = {r["doc_key"]: r for r in csv.DictReader((RESULTS / "document_manual_review.csv").open(encoding="utf-8"))}
    auto = {r["doc_key"]: r for r in csv.DictReader((RESULTS / "document_codes.csv").open(encoding="utf-8"))}
    collapse = lambda c: "design" if c.startswith("design") else c
    pairs = [(collapse(auto[k]["primary_bin"]), man[k]["manual_code"]) for k in man
             if k in auto and man[k]["manual_code"] != "uncertain"]
    agree = sum(1 for a, m in pairs if a == m)
    by = defaultdict(lambda: [0, 0])
    for a, m in pairs:
        by[a][1] += 1
        by[a][0] += a == m
    out = {"reviewed": len(man), "decidable": len(pairs), "agreement": round(agree / len(pairs), 3) if pairs else None,
           "precision_by_automated_code": {k: f"{v[0]}/{v[1]}" for k, v in by.items()},
           "confusion": dict(Counter(f"auto={a} | manual={m}" for a, m in pairs if a != m))}
    (RESULTS / "document_agreement.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    fn = {"sample": cmd_sample, "download": cmd_download, "ocr": cmd_ocr, "code": cmd_code,
          "agreement": agreement}.get(cmd)
    if not fn:
        print(__doc__)
        return 1
    fn()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
