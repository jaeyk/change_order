#!/usr/bin/env python3
"""Normalize and classify public contracts into a unified schema with Tech vs Non-Tech classification."""

from __future__ import annotations

import csv
import json
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from cooperative_and_resellers import (
    STATE_MASTER,
    agency_key,
    build_award_structure,
    build_cooperative_sales,
    build_vendor_qualifications,
    build_reseller_registry,
    build_reseller_relationships,
    contract_key,
    coop_direction,
    detect_coop_vehicle,
    harmonize_flags_cert,
    harmonize_wa_cert,
    load_wa_it_coop_flags,
    normalize_vendor_name,
    procurement_channel,
    vendor_qualification,
)

# Ledgers whose published extracts carry no usable amendment history:
#   baton_rouge -- one header + line items per PO, single snapshot date, no versions
#   nyc_sca     -- change-order-only file (every contract selected on the outcome)
#   vermont     -- repeated rows are duplicates; max amount never changes across rows
#   austin      -- one version per document in the published extract
# They stay in the data (certifications, cooperative tags, award structure) but are
# excluded from amendment-rate comparisons and regressions.
NO_AMENDMENT_HISTORY = {"baton_rouge", "nyc_sca", "vermont", "austin"}

# State and level of government for each normalized jurisdiction.
JURISDICTION_META: dict[str, tuple[str, str]] = {
    "cook_county": ("IL", "county"),
    "chicago": ("IL", "city"),
    "oregon": ("OR", "state"),
    "oregon_lottery": ("OR", "state"),
    "oregon_judicial": ("OR", "state"),
    "oregon_treasury": ("OR", "state"),
    "washington_state": ("WA", "state"),
    "vermont": ("VT", "state"),
    "baton_rouge": ("LA", "city"),  # consolidated city-parish
    "austin": ("TX", "city"),
    "west_hollywood": ("CA", "city"),
    "nyc_sca": ("NY", "special_authority"),
}

SOFTWARE_SAAS_PATTERN = re.compile(
    r'\b(software|saas|cloud|app|application|database|crm|erp|oracle|sap|salesforce|workday|tyler technologies|licensing|license|subscription|portal|web application|gis|mapping software)\b',
    re.IGNORECASE
)
HARDWARE_TELECOM_PATTERN = re.compile(
    r'\b(hardware|server|servers|storage|mainframe|network|networking|router|switch|cisco|telecom|telecommunications|cellular|broadband|fiber|voip|copier|printer|laptop|desktop|peripherals|cdw|insight|shi corp|system solutions)\b',
    re.IGNORECASE
)
IT_SERVICES_PATTERN = re.compile(
    r'\b(it consulting|it services|technology services|cyber|cybersecurity|systems integrator|integration|programmer|developer|staff augmentation|technical support|help desk|sdi presence|kyndryl|accenture|cgi|deloitte|infosys|computer programming)\b',
    re.IGNORECASE
)
TECH_BROAD_PATTERN = re.compile(
    r'\b(information technology|it\b|tech\b|technology|computing|digital|telecom|telecommunications)\b',
    re.IGNORECASE
)

PROGRAM_DOMAINS = {
    "health_care": re.compile(
        r'\b(health|hospital|medical|medicaid|medicare|clinic|public health|patient|clinical|pharmacy|mental health|behavioral health|cerner|epic|nursing)\b',
        re.IGNORECASE
    ),
    "public_assistance": re.compile(
        r'\b(child welfare|public assistance|human services|dhs|social services|snap|tanf|food stamps|foster|child support|eligibility|disabilities|aging|family and support)\b',
        re.IGNORECASE
    ),
    "public_safety": re.compile(
        r'\b(police|sheriff|fire|emergency|911|dispatch|jail|corrections|cad|rms|court|courts|justice|prosecutor|public defender|law enforcement|homeland security|surveillance)\b',
        re.IGNORECASE
    ),
    "labor_workforce": re.compile(
        r'\b(labor|employment|workforce|unemployment|workers comp|occupational|licensing board|wage|job service)\b',
        re.IGNORECASE
    ),
    "environment": re.compile(
        r'\b(environment|environmental|ecology|parks|wildlife|forestry|natural resources|clean water|air quality|conservation|agriculture|fish)\b',
        re.IGNORECASE
    ),
    "transportation": re.compile(
        r'\b(transportation|transit|aviation|airport|highway|dot|traffic|roads|streets|toll|ferry|parking)\b',
        re.IGNORECASE
    ),
    "administration_finance": re.compile(
        r'\b(finance|revenue|tax|treasury|budget|comptroller|assessor|payroll|human resources|civil service|procurement|das|general services|clerk)\b',
        re.IGNORECASE
    ),
}

def classify_program_domain(dept: str, title: str, comm: str) -> str:
    combined = f"{dept} {title} {comm}".lower()
    scores = {}
    for domain, pattern in PROGRAM_DOMAINS.items():
        matches = len(pattern.findall(combined))
        if matches > 0:
            scores[domain] = matches
    if not scores:
        return "general_enterprise_it"
    return max(scores.items(), key=lambda x: x[1])[0]

def clean_currency(val: Any) -> float:
    if val is None:
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip()
    if not s or s in ("$   - 0", "$   -", "-", "0", "$0", "None"):
        return 0.0
    is_neg = False
    if s.startswith("(") and s.endswith(")"):
        is_neg = True
        s = s[1:-1]
    elif s.startswith("-"):
        is_neg = True
        s = s[1:]
    s = re.sub(r"[^\d.]", "", s)
    if not s:
        return 0.0
    try:
        f = float(s)
        return -f if is_neg else f
    except ValueError:
        return 0.0

def parse_iso_date(val: Any) -> datetime | None:
    if not val:
        return None
    s = str(val).strip()
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.split(".")[0])
    except Exception:
        return None

def format_date(dt: datetime | None) -> str:
    return dt.strftime("%Y-%m-%d") if dt else ""

def classify_contract(title: str, dept: str, comm: str, vendor: str) -> tuple[int, str, str]:
    combined = f"{title} {dept} {comm} {vendor}".lower()
    
    # Check if department is central IT
    is_tech_dept = any(k in dept.lower() for k in [
        "enterprise technology", "innovation and technology", "doit", "information technology",
        "it solutions", "cio", "enterprise information services"
    ])
    
    is_tech_comm = "information technology" in comm.lower() or "telecommunications" in comm.lower()
    
    is_tech_keyword = bool(TECH_BROAD_PATTERN.search(combined)) or bool(SOFTWARE_SAAS_PATTERN.search(combined)) or bool(HARDWARE_TELECOM_PATTERN.search(combined)) or bool(IT_SERVICES_PATTERN.search(combined))
    
    if not (is_tech_dept or is_tech_comm or is_tech_keyword):
        return 0, "non_tech", "non_tech"
        
    domain = classify_program_domain(dept, title, comm)

    # Classify subsector
    if SOFTWARE_SAAS_PATTERN.search(combined):
        return 1, "software_saas", domain
    elif HARDWARE_TELECOM_PATTERN.search(combined):
        return 1, "hardware_telecom", domain
    elif IT_SERVICES_PATTERN.search(combined):
        return 1, "it_services", domain
    elif is_tech_dept or is_tech_comm:
        return 1, "tech_general", domain
    return 1, "tech_general", domain


def process_cook_county(raw_dir: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    path = raw_dir / "cook_county" / "records.json"
    if not path.exists():
        return [], []
    with path.open(encoding="utf-8") as f:
        records = json.load(f)

    groups = defaultdict(list)
    for r in records:
        cno = r.get("contract_number")
        if cno:
            groups[cno].append(r)

    contract_rows = []
    amendment_rows = []

    for cno, rows in groups.items():
        base_rows = [r for r in rows if (r.get("category") or {}).get("description") == "New Contract"]
        amend_rows = [r for r in rows if (r.get("category") or {}).get("description") == "Amendment"]
        
        # If no explicit "New Contract", use first by system_release
        if not base_rows and rows:
            sorted_rows = sorted(rows, key=lambda x: str(x.get("system_release") or ""))
            base_rows = [sorted_rows[0]]
            amend_rows = sorted_rows[1:]

        primary = base_rows[0] if base_rows else rows[0]
        dept = primary.get("lead_department") or ""
        vendor = primary.get("vendor_name") or ""
        desc = primary.get("description") or ""
        comm = primary.get("commodity_type") or ""
        
        orig_val = sum(clean_currency(r.get("amount")) for r in base_rows)
        added_val = sum(clean_currency(r.get("amount")) for r in amend_rows)
        final_val = orig_val + added_val
        
        start_dt = parse_iso_date(primary.get("start_date"))
        end_dt = parse_iso_date(primary.get("end_date"))
        duration_days = (end_dt - start_dt).days if (start_dt and end_dt and end_dt >= start_dt) else None

        is_tech, subsector, domain = classify_contract(desc, dept, comm, vendor)
        amend_count = len(amend_rows)
        is_amended = 1 if amend_count > 0 or added_val != 0 else 0
        pct_growth = (added_val / orig_val * 100.0) if orig_val > 0 else 0.0

        contract_rows.append({
            "jurisdiction": "cook_county",
            "contract_id": cno,
            "title_desc": desc,
            "department": dept,
            "vendor_name": vendor,
            "commodity_or_type": comm,
            "is_tech": is_tech,
            "tech_subsector": subsector,
            "tech_domain": domain,
            "initial_award_val": orig_val,
            "final_award_val": final_val,
            "delta_val": added_val,
            "pct_growth": round(pct_growth, 2),
            "amendment_count": amend_count,
            "is_amended": is_amended,
            "start_date": format_date(start_dt),
            "end_date": format_date(end_dt),
            "duration_days": duration_days if duration_days is not None else "",
        })

        for idx, ar in enumerate(amend_rows, 1):
            a_dt = parse_iso_date(ar.get("system_release"))
            a_amt = clean_currency(ar.get("amount"))
            amendment_rows.append({
                "jurisdiction": "cook_county",
                "contract_id": cno,
                "amendment_seq": idx,
                "amendment_date": format_date(a_dt),
                "delta_amount": a_amt,
                "category": "Amendment",
                "description": ar.get("description") or "",
            })

    return contract_rows, amendment_rows


def process_chicago(raw_dir: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    path = raw_dir / "chicago" / "records.json"
    if not path.exists():
        return [], []
    with path.open(encoding="utf-8") as f:
        records = json.load(f)

    groups = defaultdict(list)
    for r in records:
        po = r.get("purchase_order_contract_number")
        if po:
            groups[po].append(r)

    contract_rows = []
    amendment_rows = []

    for po, rows in groups.items():
        base_rows = [r for r in rows if str(r.get("revision_number")) == "0"]
        rev_rows = [r for r in rows if str(r.get("revision_number")) != "0"]

        primary = base_rows[0] if base_rows else rows[0]
        dept = primary.get("department") or ""
        vendor = primary.get("vendor_name") or ""
        desc = primary.get("purchase_order_description") or ""
        ctype = primary.get("contract_type") or ""
        ptype = (primary.get("procurement_type") or "").strip()
        # Chicago records the procurement method explicitly:
        #   REFERENCE CONTRACT = buying off another government's contract (piggyback)
        #   JOINT PURCHASE     = joint solicitation with sister agencies (CHA, CPS, Park District...)
        #   MASTER AGREEMENT   = the City's own master agreement (not cooperative)
        if ptype.upper() == "REFERENCE CONTRACT":
            vehicle = detect_coop_vehicle(desc) or "other_cooperative"
        elif ptype.upper() == "JOINT PURCHASE":
            vehicle = "local_joint_purchase"
        else:
            vehicle = detect_coop_vehicle(desc)

        orig_val = sum(clean_currency(r.get("award_amount")) for r in base_rows)
        added_val = sum(clean_currency(r.get("award_amount")) for r in rev_rows)
        final_val = orig_val + added_val

        start_dt = parse_iso_date(primary.get("start_date"))
        end_dt = parse_iso_date(primary.get("end_date"))
        duration_days = (end_dt - start_dt).days if (start_dt and end_dt and end_dt >= start_dt) else None

        is_tech, subsector, domain = classify_contract(desc, dept, ctype, vendor)
        amend_count = len(rev_rows)
        is_amended = 1 if amend_count > 0 or added_val != 0 else 0
        pct_growth = (added_val / orig_val * 100.0) if orig_val > 0 else 0.0

        contract_rows.append({
            "jurisdiction": "chicago",
            "contract_id": po,
            "title_desc": desc,
            "department": dept,
            "vendor_name": vendor,
            "commodity_or_type": ctype,
            "is_tech": is_tech,
            "tech_subsector": subsector,
            "tech_domain": domain,
            "initial_award_val": orig_val,
            "final_award_val": final_val,
            "delta_val": added_val,
            "pct_growth": round(pct_growth, 2),
            "amendment_count": amend_count,
            "is_amended": is_amended,
            "start_date": format_date(start_dt),
            "end_date": format_date(end_dt),
            "duration_days": duration_days if duration_days is not None else "",
            "coop_vehicle": vehicle,
            "procurement_method": ptype,
        })

        for idx, ar in enumerate(rev_rows, 1):
            a_dt = parse_iso_date(ar.get("approval_date"))
            a_amt = clean_currency(ar.get("award_amount"))
            amendment_rows.append({
                "jurisdiction": "chicago",
                "contract_id": po,
                "amendment_seq": ar.get("revision_number") or idx,
                "amendment_date": format_date(a_dt),
                "delta_amount": a_amt,
                "category": "Revision",
                "description": ar.get("purchase_order_description") or "",
            })

    return contract_rows, amendment_rows


def process_oregon(raw_dir: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    path = raw_dir / "oregon_orpin" / "records.json"
    if not path.exists():
        return [], []
    with path.open(encoding="utf-8") as f:
        records = json.load(f)

    groups = defaultdict(list)
    for r in records:
        doc = r.get("document_number")
        if doc:
            groups[doc].append(r)

    contract_rows = []
    amendment_rows = []

    for doc, rows in groups.items():
        try:
            rows.sort(key=lambda x: int(x.get("amendment_number") or 0))
        except Exception:
            pass

        base = rows[0]
        final = rows[-1]
        
        dept = base.get("agency_name") or ""
        vendor = base.get("contractor_information") or ""
        title = base.get("award_title") or ""
        atype = base.get("award_type") or ""

        orig_val = clean_currency(base.get("original_award_value"))
        final_val = clean_currency(final.get("total_award_value_w_amendments")) or orig_val
        delta_val = final_val - orig_val

        start_dt = parse_iso_date(base.get("original_start_date"))
        end_dt = parse_iso_date(base.get("expiration_date"))
        duration_days = (end_dt - start_dt).days if (start_dt and end_dt and end_dt >= start_dt) else None

        is_tech, subsector, domain = classify_contract(title, dept, atype, vendor)
        amend_count = len(rows) - 1
        is_amended = 1 if amend_count > 0 or delta_val != 0 else 0
        pct_growth = (delta_val / orig_val * 100.0) if orig_val > 0 else 0.0

        contract_rows.append({
            "jurisdiction": "oregon",
            "contract_id": doc,
            "title_desc": title,
            "department": dept,
            "vendor_name": vendor,
            "commodity_or_type": atype,
            "is_tech": is_tech,
            "tech_subsector": subsector,
            "tech_domain": domain,
            "initial_award_val": orig_val,
            "final_award_val": final_val,
            "delta_val": delta_val,
            "pct_growth": round(pct_growth, 2),
            "amendment_count": amend_count,
            "is_amended": is_amended,
            "start_date": format_date(start_dt),
            "end_date": format_date(end_dt),
            "duration_days": duration_days if duration_days is not None else "",
            # ORPIN "Price Agreement" = DAS statewide price agreement (central state contract)
            "coop_vehicle": detect_coop_vehicle(title) or (STATE_MASTER if atype == "Price Agreement" else ""),
            "procurement_method": atype,
        })

        for r in rows[1:]:
            a_dt = parse_iso_date(r.get("amendment_date"))
            a_amt = clean_currency(r.get("amendment_value"))
            amendment_rows.append({
                "jurisdiction": "oregon",
                "contract_id": doc,
                "amendment_seq": r.get("amendment_number") or "",
                "amendment_date": format_date(a_dt),
                "delta_amount": a_amt,
                "category": "Amendment",
                "description": r.get("award_title") or "",
            })

    return contract_rows, amendment_rows


WA_FISCAL_YEAR_DATASETS = [
    ("washington_fy2021", 2021),
    ("washington_fy2022", 2022),
    ("washington_state", 2024),  # FY2024 (original dataset name kept for compatibility)
    ("washington_fy2023", 2023),
    ("washington_fy2025", 2025),
]


def process_washington(raw_dir: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Pool WA agency-contract reports FY2021-FY2025.

    Contracts are keyed by (agency number, contract number) -- contract numbers such as
    "K1234" are reused across agencies. Rows repeated across fiscal-year reports are
    de-duplicated on (agency, contract, cost, start date). Cooperative vehicles come from the
    WA IT Contracts reports (explicit NASPO/Sourcewell/... field) and from a
    "Statewide Contract" procurement type.
    """
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    seen: set[tuple[str, str, float, str]] = set()
    for name, fy in WA_FISCAL_YEAR_DATASETS:
        path = raw_dir / name / "records.json"
        if not path.exists():
            continue
        with path.open(encoding="utf-8") as f:
            records = json.load(f)
        for r in records:
            cno = (r.get("agency_contract_no") or "").strip()
            if not cno:
                continue
            agency = r.get("agency_number_agency_name") or r.get("agency_name") or ""
            akey = agency_key(agency)
            cost = clean_currency(r.get("cost_of_contract") or r.get("state_amount"))
            start = str(r.get("contract_effective_start") or r.get("period_of_performance_start") or "")[:10]
            dedupe = (akey, cno.upper(), cost, start)
            if dedupe in seen:
                continue
            seen.add(dedupe)
            r["_fy"] = fy
            r["_agency"] = agency
            groups[(akey, cno)].append(r)

    coop_flags = load_wa_it_coop_flags(raw_dir)
    contract_rows = []
    amendment_rows = []

    for (akey, cno), rows in groups.items():
        rows.sort(key=lambda x: (
            str(x.get("contract_effective_start") or x.get("period_of_performance_start") or ""),
            x["_fy"],
            str(x.get("agency_contract_amendment") or ""),
        ))
        primary = rows[0]
        dept = primary["_agency"]
        vendor = primary.get("contractor_name_search_for") or primary.get("contractor_name") or ""
        desc = f"{primary.get('purpose_of_the_contract') or ''} {primary.get('purpose_of_the_contract_1') or ''}".strip()
        proc_type = primary.get("procurement_type") or primary.get("procurement_type_competitive") or ""

        start_key = lambda x: str(x.get("contract_effective_start") or x.get("period_of_performance_start") or "")
        pvendor = normalize_vendor_name(primary.get("contractor_name_search_for") or primary.get("contractor_name") or "")
        # Rows on the original start date from *other* contractors are co-awardees (multiple
        # award), not amendments.
        co_awardees = [r for r in rows[1:] if start_key(r) == start_key(primary) and normalize_vendor_name(
            r.get("contractor_name_search_for") or r.get("contractor_name") or "") != pvendor]
        rows = [r for r in rows if not any(r is c for c in co_awardees)]
        costs = [clean_currency(r.get("cost_of_contract") or r.get("state_amount")) for r in rows]
        orig_val = costs[0] if costs else 0.0
        final_val = max(costs) if costs else orig_val
        delta_val = final_val - orig_val

        start_dt = parse_iso_date(primary.get("contract_effective_start") or primary.get("period_of_performance_start"))
        end_dt = parse_iso_date(rows[-1].get("contract_effective_end_date") or rows[-1].get("period_of_performance_end"))
        duration_days = (end_dt - start_dt).days if (start_dt and end_dt and end_dt >= start_dt) else None

        is_tech, subsector, domain = classify_contract(desc, dept, proc_type, vendor)
        amend_count = len(rows) - 1
        is_amended = 1 if amend_count > 0 or delta_val != 0 else 0
        pct_growth = (delta_val / orig_val * 100.0) if orig_val > 0 else 0.0

        vehicle = coop_flags.get((akey, contract_key(cno)), "")
        if not vehicle:
            vehicle = detect_coop_vehicle(desc, primary.get("explanation_of_costs_optional") or "")
        if not vehicle and "statewide contract" in proc_type.lower():
            vehicle = STATE_MASTER

        cert = harmonize_wa_cert(
            primary.get("minority_woman_owned") or "",
            primary.get("small_business") or primary.get("small_business_status_optional") or "",
            primary.get("veteran") or "",
        )

        contract_rows.append({
            "jurisdiction": "washington_state",
            "contract_id": f"{akey}:{cno}",
            "title_desc": desc,
            "department": dept,
            "vendor_name": vendor,
            "commodity_or_type": proc_type,
            "is_tech": is_tech,
            "tech_subsector": subsector,
            "tech_domain": domain,
            "initial_award_val": orig_val,
            "final_award_val": final_val,
            "delta_val": delta_val,
            "pct_growth": round(pct_growth, 2),
            "amendment_count": amend_count,
            "is_amended": is_amended,
            "start_date": format_date(start_dt),
            "end_date": format_date(end_dt),
            "duration_days": duration_days if duration_days is not None else "",
            "coop_vehicle": vehicle,
            "procurement_method": proc_type,
            "vendor_certification": cert,
            "n_contractors": 1 + len({normalize_vendor_name(
                r.get("contractor_name_search_for") or r.get("contractor_name") or "") for r in co_awardees}),
        })

        for r in rows[1:]:
            a_dt = parse_iso_date(r.get("contract_effective_start"))
            a_amt = clean_currency(r.get("cost_of_contract"))
            amendment_rows.append({
                "jurisdiction": "washington_state",
                "contract_id": f"{akey}:{cno}",
                "amendment_seq": r.get("agency_contract_amendment") or "",
                "amendment_date": format_date(a_dt),
                "delta_amount": a_amt,
                "category": r.get("contract_modifications") or "Amendment",
                "description": r.get("purpose_of_the_contract") or "",
            })

    return contract_rows, amendment_rows


def process_baton_rouge(raw_dir: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Baton Rouge purchase orders.

    Each source_document has exactly one header row (record_type 'H', carrying the PO total)
    and N line-item rows ('D', item_number 1..N, amount 0). There is a single input date per
    document and no version / change-order field, so the ledger is a current snapshot:
    amendments are NOT observable. Line items are counted, not treated as amendments.
    """
    path = raw_dir / "baton_rouge" / "records.json"
    if not path.exists():
        return [], []
    with path.open(encoding="utf-8") as f:
        records = json.load(f)

    groups = defaultdict(list)
    for r in records:
        sdoc = r.get("source_document")
        if sdoc:
            groups[sdoc].append(r)

    contract_rows = []
    for sdoc, rows in groups.items():
        headers = [r for r in rows if r.get("record_type") == "H"]
        primary = headers[0] if headers else rows[0]
        dept = primary.get("dept_name") or ""
        vendor = primary.get("vendor_name_1") or ""
        desc = primary.get("source_doc_desc") or ""
        comm = primary.get("source_doc_type_description") or ""
        value = clean_currency(primary.get("total_amount"))
        start_dt = parse_iso_date(primary.get("input_date"))
        is_tech, subsector, domain = classify_contract(desc, dept, comm, vendor)
        contract_rows.append({
            "jurisdiction": "baton_rouge",
            "contract_id": sdoc,
            "title_desc": desc,
            "department": dept,
            "vendor_name": vendor,
            "commodity_or_type": comm,
            "is_tech": is_tech,
            "tech_subsector": subsector,
            "tech_domain": domain,
            "initial_award_val": value,
            "final_award_val": value,
            "delta_val": 0.0,
            "pct_growth": 0.0,
            "amendment_count": 0,
            "is_amended": 0,
            "amendment_observable": 0,
            "n_line_items": sum(1 for r in rows if r.get("record_type") == "D"),
            "start_date": format_date(start_dt),
            "end_date": "",
            "duration_days": "",
            "vendor_certification": harmonize_flags_cert(
                minority=primary.get("isminority"),
                dbe=primary.get("dbe") if str(primary.get("dbe") or "").upper() == "Y" else primary.get("smb_dbe") or primary.get("dbe"),
                vet=primary.get("vet_sm_bus"),
            ),
        })
    return contract_rows, []


def process_nyc_sca(raw_dir: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    path = raw_dir / "nyc_sca" / "records.json"
    if not path.exists():
        return [], []
    with path.open(encoding="utf-8") as f:
        records = json.load(f)

    groups = defaultdict(list)
    for r in records:
        cid = r.get("change_order_project_sca_contract_identifier")
        if cid:
            groups[cid].append(r)

    contract_rows = []
    amendment_rows = []

    for cid, rows in groups.items():
        primary = rows[0]
        dept = "NYC School Construction Authority"
        vendor = primary.get("change_order_project_to_vendor_") or ""
        desc = primary.get("change_order_project_title") or ""
        comm = "School Construction Change Order"

        start_dt = parse_iso_date(primary.get("change_order_document_date"))
        is_tech, subsector, domain = classify_contract(desc, dept, comm, vendor)
        amend_count = len(rows)

        contract_rows.append({
            "jurisdiction": "nyc_sca",
            "amendment_observable": 0,  # change-order-only file: every contract is selected on the outcome
            "contract_id": cid,
            "title_desc": desc,
            "department": dept,
            "vendor_name": vendor,
            "commodity_or_type": comm,
            "is_tech": is_tech,
            "tech_subsector": subsector,
            "tech_domain": domain,
            "initial_award_val": 0.0,
            "final_award_val": 0.0,
            "delta_val": 0.0,
            "pct_growth": 0.0,
            "amendment_count": amend_count,
            "is_amended": 1,
            "start_date": format_date(start_dt),
            "end_date": "",
            "duration_days": "",
        })

        for r in rows:
            a_dt = parse_iso_date(r.get("change_order_document_date"))
            amendment_rows.append({
                "jurisdiction": "nyc_sca",
                "contract_id": cid,
                "amendment_seq": r.get("change_order_number") or "",
                "amendment_date": format_date(a_dt),
                "delta_amount": 0.0,
                "category": "Change Order",
                "description": r.get("change_order_project_title") or "",
            })

    return contract_rows, amendment_rows


def process_vermont(raw_dir: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    path = raw_dir / "vermont" / "records.json"
    if not path.exists():
        return [], []
    with path.open(encoding="utf-8") as f:
        records = json.load(f)

    groups = defaultdict(list)
    for r in records:
        cid = r.get("contract")
        if cid:
            groups[cid].append(r)

    contract_rows = []
    amendment_rows = []

    for cid, rows in groups.items():
        primary = rows[0]
        dept = primary.get("bu_name") or ""
        vendor = primary.get("vendor_name") or ""
        desc = primary.get("description") or ""
        comm = primary.get("type") or ""

        # Repeated rows are mostly duplicates with blank dates; a change in the maximum amount
        # is the observable amendment signal.
        dated = [r for r in rows if r.get("start_date")] or rows
        primary = dated[0]
        amounts = [clean_currency(r.get("max_amount")) for r in dated]
        distinct_amounts = list(dict.fromkeys(a for a in amounts if a))
        orig_val = distinct_amounts[0] if distinct_amounts else 0.0
        final_val = max(distinct_amounts) if distinct_amounts else orig_val
        start_dt = parse_iso_date(primary.get("start_date"))
        end_dt = parse_iso_date(max((str(r.get("exp_date") or "") for r in dated), default="") or None)
        duration_days = (end_dt - start_dt).days if (start_dt and end_dt and end_dt >= start_dt) else None

        is_tech, subsector, domain = classify_contract(desc, dept, comm, vendor)
        amend_count = max(len(distinct_amounts) - 1, 0)

        contract_rows.append({
            "jurisdiction": "vermont",
            "contract_id": cid,
            "title_desc": desc,
            "department": dept,
            "vendor_name": vendor,
            "commodity_or_type": comm,
            "is_tech": is_tech,
            "tech_subsector": subsector,
            "tech_domain": domain,
            "initial_award_val": orig_val,
            "final_award_val": final_val,
            "delta_val": final_val - orig_val,
            "pct_growth": round((final_val - orig_val) / orig_val * 100.0, 2) if orig_val > 0 else 0.0,
            "amendment_count": amend_count,
            "is_amended": 1 if amend_count > 0 else 0,
            "start_date": format_date(start_dt),
            "end_date": format_date(end_dt),
            "duration_days": duration_days if duration_days is not None else "",
        })

    return contract_rows, amendment_rows


def process_austin(raw_dir: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    path = raw_dir / "austin" / "records.json"
    if not path.exists():
        return [], []
    with path.open(encoding="utf-8") as f:
        records = json.load(f)

    groups = defaultdict(list)
    for r in records:
        doc = r.get("doc_id")
        if doc:
            groups[doc].append(r)

    contract_rows = []
    amendment_rows = []

    for doc, rows in groups.items():
        try:
            rows.sort(key=lambda x: int(x.get("doc_vers_no") or 0))
        except Exception:
            pass
        base = rows[0]
        # Several vendor lines can share a version (co-awardees on one master agreement);
        # amendments are additional versions, not additional vendor lines.
        versions = sorted({_int(r.get("doc_vers_no")) for r in rows})
        final = [r for r in rows if _int(r.get("doc_vers_no")) == versions[-1]][0]
        dept = base.get("doc_dept_cd") or ""
        vendor = base.get("lgl_nm") or ""
        desc = base.get("doc_dscr") or ""
        comm = base.get("cat_dscr") or ""

        orig_val = clean_currency(base.get("ma_prch_lmt_am"))
        final_val = clean_currency(final.get("ma_prch_lmt_am")) or orig_val
        delta_val = final_val - orig_val

        start_dt = parse_iso_date(base.get("efbgn_dt"))
        end_dt = parse_iso_date(base.get("efend_dt"))
        duration_days = (end_dt - start_dt).days if (start_dt and end_dt and end_dt >= start_dt) else None

        is_tech, subsector, domain = classify_contract(desc, dept, comm, vendor)
        amend_count = len(versions) - 1
        pct_growth = (delta_val / orig_val * 100.0) if orig_val > 0 else 0.0

        contract_rows.append({
            "jurisdiction": "austin",
            "contract_id": doc,
            "title_desc": desc,
            "department": dept,
            "vendor_name": vendor,
            "commodity_or_type": comm,
            "is_tech": is_tech,
            "tech_subsector": subsector,
            "tech_domain": domain,
            "initial_award_val": orig_val,
            "final_award_val": final_val,
            "delta_val": delta_val,
            "pct_growth": round(pct_growth, 2),
            "amendment_count": amend_count,
            "is_amended": 1 if amend_count > 0 or delta_val != 0 else 0,
            "start_date": format_date(start_dt),
            "end_date": format_date(end_dt),
            "duration_days": duration_days if duration_days is not None else "",
            "procurement_method": base.get("rpt_dscr") or "",
            "coop_vehicle": detect_coop_vehicle(desc) or (
                "other_cooperative" if "cooperative" in f"{base.get('rpt_dscr')} {comm}".lower() else ""),
        })

    return contract_rows, amendment_rows


def process_oregon_lottery(raw_dir: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    path = raw_dir / "oregon_lottery" / "records.json"
    if not path.exists():
        return [], []
    with path.open(encoding="utf-8") as f:
        records = json.load(f)

    groups = defaultdict(list)
    for r in records:
        po = r.get("purchase_order")
        if po:
            groups[po].append(r)

    contract_rows = []
    amendment_rows = []

    for po, rows in groups.items():
        primary = rows[0]
        dept = "Oregon Lottery"
        vendor = primary.get("vendor") or ""
        desc = primary.get("contract_description") or ""
        comm = primary.get("line_item_description") or ""

        # Rows are PO line items. A change order shows up as lines created on a later date,
        # so amendments = distinct creation dates after the first (not the number of lines).
        dates = sorted({str(r.get("created") or "")[:10] for r in rows} - {""})
        first = dates[0] if dates else ""
        orig_val = sum(clean_currency(r.get("net_amount")) for r in rows
                       if str(r.get("created") or "")[:10] == first or not first)
        final_val = sum(clean_currency(r.get("net_amount")) for r in rows)
        start_dt = parse_iso_date(first) if first else parse_iso_date(primary.get("created"))

        is_tech, subsector, domain = classify_contract(desc, dept, comm, vendor)
        amend_count = max(len(dates) - 1, 0)

        contract_rows.append({
            "jurisdiction": "oregon_lottery",
            "contract_id": po,
            "title_desc": desc,
            "department": dept,
            "vendor_name": vendor,
            "commodity_or_type": comm,
            "is_tech": is_tech,
            "tech_subsector": subsector,
            "tech_domain": domain,
            "initial_award_val": orig_val,
            "final_award_val": final_val,
            "delta_val": final_val - orig_val,
            "pct_growth": round((final_val - orig_val) / orig_val * 100.0, 2) if orig_val > 0 else 0.0,
            "amendment_count": amend_count,
            "is_amended": 1 if amend_count > 0 else 0,
            "n_line_items": len(rows),
            "start_date": format_date(start_dt),
            "end_date": "",
            "duration_days": "",
        })

    return contract_rows, amendment_rows


def _base_contract_row(jurisdiction: str, cid: str, desc: str, dept: str, vendor: str, comm: str,
                       orig_val: float, final_val: float, amend_count: int, is_amended: int,
                       start_dt: datetime | None, end_dt: datetime | None) -> dict[str, Any]:
    delta_val = final_val - orig_val
    duration_days = (end_dt - start_dt).days if (start_dt and end_dt and end_dt >= start_dt) else None
    is_tech, subsector, domain = classify_contract(desc, dept, comm, vendor)
    return {
        "jurisdiction": jurisdiction,
        "contract_id": cid,
        "title_desc": desc,
        "department": dept,
        "vendor_name": vendor,
        "commodity_or_type": comm,
        "is_tech": is_tech,
        "tech_subsector": subsector,
        "tech_domain": domain,
        "initial_award_val": orig_val,
        "final_award_val": final_val,
        "delta_val": delta_val,
        "pct_growth": round((delta_val / orig_val * 100.0) if orig_val > 0 else 0.0, 2),
        "amendment_count": amend_count,
        "is_amended": is_amended,
        "start_date": format_date(start_dt),
        "end_date": format_date(end_dt),
        "duration_days": duration_days if duration_days is not None else "",
    }


def _parse_us_date(val: Any) -> datetime | None:
    s = str(val or "").strip()
    if not s:
        return None
    try:
        return datetime.strptime(s, "%m/%d/%Y")
    except ValueError:
        return parse_iso_date(s)


def process_oregon_judicial(raw_dir: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Oregon Judicial Dept. multi-year report.

    One row per contract per fiscal year (a few early rows carry a '-<version>' suffix).
    ``total_contract_value`` is the running value including amendments; in FY2017+ rows
    ``total_amendments`` holds the running *number* of amendments (earlier rows hold dollars).
    """
    path = raw_dir / "oregon_judicial" / "records.json"
    if not path.exists():
        return [], []
    with path.open(encoding="utf-8") as f:
        records = json.load(f)

    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in records:
        an = (r.get("award_number") or "").strip()
        if not an:
            continue
        base, sep, ver = an.rpartition("-")
        if not (sep and base and ver.isdigit()):
            base, ver = an, "0"
        r["_ver"] = int(ver)
        groups[base].append(r)

    contract_rows, amendment_rows = [], []
    for base, rows in groups.items():
        rows.sort(key=lambda x: (str(x.get("fiscal_year") or ""), x["_ver"]))
        first, last = rows[0], rows[-1]
        orig_val = clean_currency(first.get("original_contract_value")) or clean_currency(first.get("total_amendments"))
        values = [clean_currency(r.get("total_contract_value")) for r in rows if r.get("total_contract_value")]
        final_val = values[-1] if values else orig_val
        counts = [
            int(float(r["total_amendments"])) for r in rows
            if int(r.get("fiscal_year") or 0) >= 2017 and r.get("total_amendments")
            and float(r["total_amendments"]).is_integer() and float(r["total_amendments"]) < 500
        ]
        versions = {r["_ver"] for r in rows}
        amend_count = max(counts) if counts else max(len(versions) - 1, 0)
        contract_rows.append(_base_contract_row(
            "oregon_judicial", base, first.get("award_title") or "", "Oregon Judicial Department",
            first.get("company_name") or "", first.get("award_type") or "", orig_val, final_val,
            amend_count, 1 if amend_count > 0 or abs(final_val - orig_val) > 0.5 else 0,
            parse_iso_date(first.get("contract_effective_date")), parse_iso_date(last.get("contract_expiration_date")),
        ))
        prev = orig_val
        for r in rows[1:]:
            v = clean_currency(r.get("total_contract_value"))
            if v and abs(v - prev) > 0.5:
                amendment_rows.append({
                    "jurisdiction": "oregon_judicial", "contract_id": base, "amendment_seq": r.get("fiscal_year"),
                    "amendment_date": "", "delta_amount": v - prev,
                    "category": "Value change (fiscal-year snapshot)", "description": r.get("award_title") or "",
                })
                prev = v
    return contract_rows, amendment_rows


def process_oregon_treasury(raw_dir: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Oregon State Treasury: NTE amount plus a supplemental (amendment) amount/date."""
    path = raw_dir / "oregon_treasury" / "records.json"
    if not path.exists():
        return [], []
    with path.open(encoding="utf-8") as f:
        records = json.load(f)

    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in records:
        if r.get("contract_id"):
            groups[r["contract_id"]].append(r)

    contract_rows, amendment_rows = [], []
    for cid, rows in groups.items():
        rows.sort(key=lambda x: str(x.get("fiscal_year") or ""))
        first, last = rows[0], rows[-1]
        orig_val = clean_currency(first.get("contract_nte_amount"))
        supplements: dict[str, float] = {}
        for r in rows:
            if r.get("supplemental_effective_date") or clean_currency(r.get("supplemental_contract_amount")):
                supplements[str(r.get("supplemental_effective_date") or r.get("fiscal_year"))] = clean_currency(
                    r.get("supplemental_contract_amount"))
        final_val = orig_val + sum(supplements.values())
        end_dt = _parse_us_date(last.get("supplemental_expiration_date") or last.get("expiration_date"))
        row = _base_contract_row(
            "oregon_treasury", cid, first.get("award_title") or "", "Oregon State Treasury",
            first.get("contractor_name") or "", first.get("contract_classification") or "",
            orig_val, final_val, len(supplements), 1 if supplements else 0,
            _parse_us_date(first.get("effective_date")), end_dt,
        )
        contract_rows.append(row)
        for i, (d, amt) in enumerate(sorted(supplements.items()), 1):
            amendment_rows.append({
                "jurisdiction": "oregon_treasury", "contract_id": cid, "amendment_seq": i,
                "amendment_date": format_date(_parse_us_date(d)), "delta_amount": amt,
                "category": "Supplemental", "description": first.get("award_title") or "",
            })
    return contract_rows, amendment_rows


def process_west_hollywood(raw_dir: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """City of West Hollywood active contracts: original amount vs. current contract total."""
    path = raw_dir / "west_hollywood" / "records.json"
    if not path.exists():
        return [], []
    with path.open(encoding="utf-8") as f:
        records = json.load(f)

    contract_rows = []
    for r in records:
        cid = r.get("contract_number")
        if not cid:
            continue
        orig_val = clean_currency(r.get("original_amount"))
        final_val = clean_currency(r.get("contract_total")) or orig_val
        try:
            amend_count = int(float(r.get("contract_amendments") or 0))
        except ValueError:
            amend_count = 0
        desc = f"{r.get('short_description') or ''} {r.get('full_description') or ''}".strip()
        contract_rows.append(_base_contract_row(
            "west_hollywood", cid, desc, f"Division {r.get('managing_division') or ''}".strip(),
            r.get("contractor_name") or "", r.get("contract_type") or "", orig_val, final_val,
            amend_count, 1 if amend_count > 0 or abs(final_val - orig_val) > 0.5 else 0,
            parse_iso_date(r.get("contract_entered")), parse_iso_date(r.get("contract_expiration")),
        ))
    return contract_rows, []


def _int(v: Any) -> int:
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return 0


# (dataset dir, contract-id field, vendor field, id transform, version fn) used to count
# distinct contractors on the ORIGINAL award of each contract ID. Counting only the lowest
# version keeps vendor renames on later revisions from looking like multiple awards (which
# would mechanically correlate with being amended).
CONTRACTOR_COUNT_SPECS = {
    "cook_county": ("cook_county", "contract_number", "vendor_name", None,
                    lambda r: 0 if (r.get("category") or {}).get("description") == "New Contract" else 1),
    "chicago": ("chicago", "purchase_order_contract_number", "vendor_name", None,
                lambda r: _int(r.get("revision_number"))),
    "oregon": ("oregon_orpin", "document_number", "contractor_information", None,
               lambda r: _int(r.get("amendment_number"))),
    "baton_rouge": ("baton_rouge", "source_document", "vendor_name_1", None, lambda r: 0),
    "austin": ("austin", "doc_id", "lgl_nm", None, lambda r: _int(r.get("doc_vers_no"))),
    "vermont": ("vermont", "contract", "vendor_name", None, lambda r: 0),
    "oregon_lottery": ("oregon_lottery", "purchase_order", "vendor", None, lambda r: 0),
    "oregon_judicial": ("oregon_judicial", "award_number", "company_name",
                        lambda a: a.rpartition("-")[0] if a.rpartition("-")[2].isdigit() and a.rpartition("-")[0] else a,
                        lambda r: _int(r.get("fiscal_year"))),
    "oregon_treasury": ("oregon_treasury", "contract_id", "contractor_name", None, lambda r: _int(r.get("fiscal_year"))),
    "west_hollywood": ("west_hollywood", "contract_number", "contractor_name", None, lambda r: 0),
    "nyc_sca": ("nyc_sca", "change_order_project_sca_contract_identifier", "change_order_project_to_vendor_", None,
                lambda r: 0),
}


def count_contractors(raw_dir: Path) -> dict[tuple[str, str], int]:
    """Distinct contractors on the original (lowest-version) award of each contract ID."""
    best: dict[tuple[str, str], tuple[int, set[str]]] = {}
    for jur, (ds, id_field, vendor_field, fn, version) in CONTRACTOR_COUNT_SPECS.items():
        path = raw_dir / ds / "records.json"
        if not path.exists():
            continue
        with path.open(encoding="utf-8") as f:
            for r in json.load(f):
                cid = r.get(id_field)
                v = normalize_vendor_name(r.get(vendor_field) or "")
                if not cid or not v:
                    continue
                cid = fn(str(cid).strip()) if fn else cid
                ver = version(r)
                key = (jur, cid)
                cur = best.get(key)
                if cur is None or ver < cur[0]:
                    best[key] = (ver, {v})
                elif ver == cur[0]:
                    cur[1].add(v)
    return {k: len(v[1]) for k, v in best.items()}


def award_structure(n_contractors: int, vendor_role: str) -> str:
    base = "multiple_award" if n_contractors > 1 else "single_award"
    role = "reseller" if vendor_role == "authorized_reseller" else "prime_direct"
    return f"{base}_{role}"


def main() -> int:
    raw_dir = Path("data/raw")
    out_dir = Path("data/processed")
    out_dir.mkdir(parents=True, exist_ok=True)

    all_contracts: list[dict[str, Any]] = []
    all_amendments: list[dict[str, Any]] = []

    processors = [
        ("Cook County", process_cook_county),
        ("Chicago", process_chicago),
        ("Oregon", process_oregon),
        ("Washington State (FY2021-FY2025)", process_washington),
        ("Baton Rouge", process_baton_rouge),
        ("NYC SCA", process_nyc_sca),
        ("Vermont", process_vermont),
        ("Austin", process_austin),
        ("Oregon Lottery", process_oregon_lottery),
        ("Oregon Judicial", process_oregon_judicial),
        ("Oregon Treasury", process_oregon_treasury),
        ("West Hollywood", process_west_hollywood),
    ]
    for label, fn in processors:
        print(f"Processing {label}...", file=sys.stderr)
        c_rows, a_rows = fn(raw_dir)
        all_contracts.extend(c_rows)
        all_amendments.extend(a_rows)
        print(f"  {label}: {len(c_rows):,} contracts, {len(a_rows):,} amendments", file=sys.stderr)

    print(f"Total normalized: {len(all_contracts):,} contracts, {len(all_amendments):,} amendments", file=sys.stderr)

    # Procurement channel, vendor role and certification grade for every contract
    print("Building reseller registry (Texas DIR, NY OGS VAR, curated VARs)...", file=sys.stderr)
    registry = build_reseller_registry(raw_dir)
    print(f"  {len(registry.exact):,} firms classified as resellers from observed relationships "
          f"(+{len(registry.prefixes)} curated VAR prefixes)", file=sys.stderr)
    quals = build_vendor_qualifications(raw_dir)
    print(f"  {len(quals):,} vendors with observed contract-vehicle qualifications", file=sys.stderr)
    contractor_counts = count_contractors(raw_dir)
    for c in all_contracts:
        if not c.get("n_contractors"):
            c["n_contractors"] = contractor_counts.get((c["jurisdiction"], c["contract_id"]), 1)
        state, level = JURISDICTION_META.get(c["jurisdiction"], ("", ""))
        c["state"] = state
        c["gov_level"] = level
        vehicle = c.get("coop_vehicle") or detect_coop_vehicle(c["title_desc"], c["commodity_or_type"])
        c["coop_vehicle"] = vehicle
        direction = coop_direction(vehicle, level, state)
        c["coop_direction"] = direction
        c["procurement_channel"] = procurement_channel(vehicle, direction)
        c["vendor_role"] = registry.role(c["vendor_name"])
        c["vendor_certification"] = c.get("vendor_certification") or "not_reported"
        c["award_structure"] = award_structure(c["n_contractors"], c["vendor_role"])
        c["amendment_observable"] = 0 if c["jurisdiction"] in NO_AMENDMENT_HISTORY else 1
        c.setdefault("n_line_items", "")
        c.setdefault("procurement_method", "")
        c.update(vendor_qualification(quals, c["vendor_name"]))

    # Write contracts CSV
    contract_fields = [
        "jurisdiction", "state", "gov_level", "contract_id", "title_desc", "department", "vendor_name",
        "commodity_or_type", "is_tech", "tech_subsector", "tech_domain", "initial_award_val",
        "final_award_val", "delta_val", "pct_growth", "amendment_count",
        "is_amended", "start_date", "end_date", "duration_days",
        "coop_vehicle", "coop_direction", "procurement_channel", "vendor_role", "vendor_certification",
        "n_contractors", "award_structure", "amendment_observable", "n_line_items", "procurement_method",
        "qualification_tier", "gsa_mas_holder", "n_vehicles_held", "fss_holder_role",
    ]
    with (out_dir / "contracts_normalized.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=contract_fields)
        writer.writeheader()
        writer.writerows(all_contracts)

    # Write amendments CSV
    amend_fields = [
        "jurisdiction", "contract_id", "amendment_seq", "amendment_date",
        "delta_amount", "category", "description"
    ]
    with (out_dir / "amendments_normalized.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=amend_fields)
        writer.writeheader()
        writer.writerows(all_amendments)

    # Cooperative-purchasing sales (Texas DIR, WA DES master contracts, Delaware)
    coop_sales = build_cooperative_sales(raw_dir)
    for r in coop_sales:
        r["vendor_role"] = registry.role(r["vendor_name"])
    if coop_sales:
        with (out_dir / "cooperative_sales.csv").open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(coop_sales[0]))
            writer.writeheader()
            writer.writerows(coop_sales)
    print(f"  cooperative_sales.csv: {len(coop_sales):,} rows", file=sys.stderr)

    # Prime vendor -> authorized reseller relationships, and the reseller registry
    rel = build_reseller_relationships(raw_dir)
    if rel:
        with (out_dir / "reseller_relationships.csv").open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rel[0]))
            writer.writeheader()
            writer.writerows(rel)
    print(f"  reseller_relationships.csv: {len(rel):,} rows", file=sys.stderr)
    # Contract-vehicle qualifications per vendor (covariates)
    qrows = sorted(quals.values(), key=lambda r: r["vendor_key"])
    if qrows:
        with (out_dir / "vendor_qualifications.csv").open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(qrows[0]))
            writer.writeheader()
            writer.writerows(qrows)
    print(f"  vendor_qualifications.csv: {len(qrows):,} rows", file=sys.stderr)

    # Single vs. multiple award, prime-direct vs. resellers, for cooperative vehicles
    awards = build_award_structure(raw_dir)
    if awards:
        fields = list(dict.fromkeys(k for r in awards for k in r))
        with (out_dir / "award_structure.csv").open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(awards)
    print(f"  award_structure.csv: {len(awards):,} rows", file=sys.stderr)

    with (out_dir / "reseller_registry.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["reseller_key", "reseller_relationships", "prime_contracts",
                                               "classified_as_reseller", "sources"])
        writer.writeheader()
        writer.writerows(registry.rows())

    print("Successfully wrote normalized contracts and amendments to data/processed/", file=sys.stderr)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
