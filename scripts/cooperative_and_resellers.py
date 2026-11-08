#!/usr/bin/env python3
"""Cooperative-purchasing, vendor/reseller, and certification-grade harmonization.

Shared helpers imported by ``normalize_and_classify.py``:

* ``detect_coop_vehicle`` / ``normalize_coop_name`` -- map free text or an explicit
  cooperative-name field to a canonical vehicle (NASPO ValuePoint, Sourcewell, OMNIA
  Partners, TIPS, E&I, NCPA, GSA, BuyBoard, HGACBuy, Texas DIR, MHEC, ...).
* ``ResellerRegistry`` -- firms observed acting as *authorized resellers* of another
  firm's contract (Texas DIR reseller fields, NY OGS value-added reseller report) plus
  a curated list of national value-added resellers. Used to tag ``vendor_role``.
* ``harmonize_*_cert`` -- collapse HUB / OMWBE / MWBE / DBE / small / veteran flags into
  one ordered certification grade.
* ``build_cooperative_sales`` / ``build_reseller_relationships`` -- harmonized tables of
  cooperative-contract spend (who buys, through which vehicle, via prime or reseller,
  and with what certification) and of prime-vendor -> reseller authorizations.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

# --------------------------------------------------------------------------------------
# Cooperative vehicles
# --------------------------------------------------------------------------------------

STATE_MASTER = "state_master_contract"

# Ordered: first match wins. Patterns are applied to lower-cased text.
COOP_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("naspo_valuepoint", re.compile(r"naspo|value ?point|\bwsca\b")),
    ("sourcewell", re.compile(r"sourcewell|\bnjpa\b|national joint powers")),
    ("omnia_partners", re.compile(r"omnia|u\.?s\.? communities|national ipa|\bnipa\b")),
    ("tips_taps", re.compile(r"\btips\b|\btaps\b|interlocal purchasing system")),
    ("e_and_i", re.compile(r"\be ?& ?i\b|\be and i\b")),
    ("ncpa", re.compile(r"\bncpa\b|national cooperative purchasing alliance")),
    ("gsa_federal", re.compile(r"gsa (?:schedule|advantage|contract|mas)|federal supply schedule|\b1122 program|gsa cooperative purchasing")),
    ("buyboard", re.compile(r"buy ?board")),
    ("hgacbuy", re.compile(r"h-?gac")),
    ("texas_dir", re.compile(r"\bdir-(?:tso|cpo|sdd|tele|ctsa)|texas dir\b|department of information resources")),
    ("mhec", re.compile(r"\bmhec\b|midwestern higher education")),
    ("peppm", re.compile(r"peppm")),
    ("kcda", re.compile(r"\bkcda\b")),
    ("wsipc", re.compile(r"\bwsipc\b")),
    ("oetc", re.compile(r"\boetc\b")),
    ("internet2", re.compile(r"internet ?2")),
    ("calif_cmas", re.compile(r"\bcmas\b")),
    ("other_cooperative", re.compile(r"cooperative (?:purchas|contract|agreement|procurement)|piggy-?back|co-?op contract")),
]

# Additional loose rules used only for explicit "which cooperative?" fields.
EXPLICIT_EXTRA: list[tuple[str, re.Pattern[str]]] = [
    ("gsa_federal", re.compile(r"^gsa\b")),
    ("texas_dir", re.compile(r"^dir\b")),
    (STATE_MASTER, re.compile(r"\bwa cooperative\b|statewide|master contract|\bdes\b|\bsvar\b|software value added reseller|sbctc")),
]

EMPTY_TOKENS = {"", "n/a", "na", "no", "none", "n", "0", "false", "sole source", "not applicable", "-"}


def detect_coop_vehicle(*texts: str) -> str:
    """Return a canonical cooperative vehicle detected in free text, or ''."""
    combined = " ".join(t for t in texts if t).lower()
    if not combined:
        return ""
    for name, pat in COOP_PATTERNS:
        if pat.search(combined):
            return name
    return ""


def normalize_coop_name(raw: str) -> str:
    """Normalize an explicit cooperative-name field (e.g. WA IT report)."""
    s = (raw or "").strip().lower()
    if s in EMPTY_TOKENS:
        return ""
    v = detect_coop_vehicle(s)
    if v:
        return v
    for name, pat in EXPLICIT_EXTRA:
        if pat.search(s):
            return name
    return "other_cooperative"


def procurement_channel(vehicle: str) -> str:
    if not vehicle:
        return "direct_or_unknown"
    if vehicle == STATE_MASTER:
        return "statewide_master"
    return "cooperative"


# --------------------------------------------------------------------------------------
# Vendor names & resellers
# --------------------------------------------------------------------------------------

_SUFFIXES = {
    "INC", "INCORPORATED", "LLC", "L L C", "CORP", "CORPORATION", "CO", "COMPANY", "LTD",
    "LIMITED", "LP", "LLP", "PLLC", "PLC", "GROUP", "HOLDINGS", "USA", "US", "NA",
}


def normalize_vendor_name(name: str) -> str:
    """Upper-case, strip punctuation, DBA clauses and corporate suffixes."""
    s = (name or "").upper()
    s = re.split(r"\b(?:D/?B/?A|DOING BUSINESS AS)\b", s)[0]
    s = s.replace("&", " AND ")
    s = re.sub(r"[^A-Z0-9 ]+", " ", s)
    toks = s.split()
    if toks and toks[0] == "THE":
        toks = toks[1:]
    while toks and toks[-1] in _SUFFIXES:
        toks = toks[:-1]
    return " ".join(toks)


# National value-added resellers / public-sector distributors. Matched as a prefix of
# the normalized vendor name, so "CDW GOVERNMENT" and "CDW G" both match "CDW".
CURATED_RESELLERS = [
    "CDW", "SHI INTERNATIONAL", "INSIGHT PUBLIC SECTOR", "INSIGHT DIRECT",
    "CARAHSOFT", "PRESIDIO", "EPLUS", "PC CONNECTION", "GOVCONNECTION", "CONNECTION PUBLIC SECTOR",
    "SOFTCHOICE", "SOFTWAREONE", "SOFTWARE ONE", "CRAYON SOFTWARE", "ZONES", "COMPUCOM",
    "WORLD WIDE TECHNOLOGY", "SIRIUS COMPUTER", "CDI COMPUTER", "TRACE3", "OPTIV", "DLT SOLUTIONS",
    "IMMIX", "EN POINTE", "DALY COMPUTERS", "NETSYNC", "MYTHICS", "VERTOSOFT", "GTS TECHNOLOGY",
    "LOGICALIS", "CONVERGE TECHNOLOGY", "COMPUTACENTER", "TD SYNNEX", "INGRAM MICRO",
    "ARROW ELECTRONICS", "DYNTEK", "SIRIUS FEDERAL",
]


# Manufacturers / OEMs that show up in reseller fields (selling their own or partner
# products) but should be treated as primes. Matched as name prefixes.
OEM_EXCLUSIONS = [
    "DELL", "HP", "HEWLETT PACKARD", "CISCO", "MICROSOFT", "ORACLE", "IBM", "UNISYS", "CANON",
    "RICOH", "XEROX", "SHARP", "KONICA", "KYOCERA", "LENOVO", "APPLE", "MOTOROLA", "VERIZON",
    "AT AND T", "T MOBILE", "LUMEN", "CENTURYLINK", "PANASONIC", "SAMSUNG", "NETAPP", "VMWARE",
]


class ResellerRegistry:
    """Firms whose dominant observed role is *authorized reseller* of another firm's contract.

    A firm qualifies when it appears as a reseller on >= ``min_relationships`` distinct
    (contract, prime vendor) pairs AND on more such pairs than the number of contracts on
    which it is itself the prime vendor. This keeps national VARs (CDW, SHI, Carahsoft...)
    and drops OEMs/primes that occasionally resell (Dell, Ricoh, Staples...).
    """

    def __init__(self, min_relationships: int = 2) -> None:
        self.min_relationships = min_relationships
        self.as_reseller: dict[str, set[tuple[str, str]]] = {}
        self.as_prime: dict[str, set[str]] = {}
        self.sources: dict[str, set[str]] = {}
        self.prefixes = [normalize_vendor_name(n) for n in CURATED_RESELLERS]
        self.oem_prefixes = [normalize_vendor_name(n) for n in OEM_EXCLUSIONS]
        self._exact: set[str] | None = None

    def add_reseller(self, name: str, contract: str, prime: str, source: str) -> None:
        key = normalize_vendor_name(name)
        if len(key) < 3:
            return
        self.as_reseller.setdefault(key, set()).add((contract, normalize_vendor_name(prime)))
        self.sources.setdefault(key, set()).add(source)
        self._exact = None

    def add_prime(self, name: str, contract: str) -> None:
        key = normalize_vendor_name(name)
        if key:
            self.as_prime.setdefault(key, set()).add(contract)
            self._exact = None

    @property
    def exact(self) -> set[str]:
        if self._exact is None:
            self._exact = {
                k for k, rel in self.as_reseller.items()
                if len(rel) >= self.min_relationships and len(rel) > len(self.as_prime.get(k, ()))
                and not self._is_oem(k)
            }
        return self._exact

    def _is_oem(self, key: str) -> bool:
        return any(key == p or key.startswith(p + " ") for p in self.oem_prefixes)

    def role(self, vendor_name: str) -> str:
        key = normalize_vendor_name(vendor_name)
        if not key:
            return "unknown"
        if self._is_oem(key):
            return "prime_or_direct"
        if key in self.exact:
            return "authorized_reseller"
        for p in self.prefixes:
            if key == p or key.startswith(p + " "):
                return "authorized_reseller"
        return "prime_or_direct"

    def rows(self) -> list[dict[str, Any]]:
        out = []
        for k in sorted(set(self.as_reseller) | set(self.prefixes)):
            n_res = len(self.as_reseller.get(k, ()))
            n_prime = len(self.as_prime.get(k, ()))
            curated = k in self.prefixes
            out.append({
                "reseller_key": k,
                "reseller_relationships": n_res,
                "prime_contracts": n_prime,
                "classified_as_reseller": int(curated or k in self.exact),
                "sources": ";".join(sorted(self.sources.get(k, set()) | ({"curated"} if curated else set()))),
            })
        return sorted(out, key=lambda r: (-r["classified_as_reseller"], -r["reseller_relationships"], r["reseller_key"]))


def _load(raw_dir: Path, name: str) -> list[dict[str, Any]]:
    path = raw_dir / name / "records.json"
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def build_reseller_registry(raw_dir: Path) -> ResellerRegistry:
    reg = ResellerRegistry()
    for ds in ("tx_dir_sales_archive", "tx_dir_sales_fy2026"):
        for r in _load(raw_dir, ds):
            cn, res, ven = r.get("contract_number") or "", r.get("reseller_name") or "", r.get("vendor_name") or ""
            reg.add_prime(ven, cn)
            if res and normalize_vendor_name(res) != normalize_vendor_name(ven):
                reg.add_reseller(res, cn, ven, "texas_dir_sales")
    for r in _load(raw_dir, "tx_dir_active_contracts"):
        cn, res, ven = r.get("contract_number") or "", r.get("reseller_name") or "", r.get("primary_vendor_name") or ""
        reg.add_prime(ven, cn)
        if res and normalize_vendor_name(res) != normalize_vendor_name(ven):
            reg.add_reseller(res, cn, ven, "texas_dir_contracts")
    for r in _load(raw_dir, "ny_var_report"):
        cn, ven = r.get("master_contract_id") or "", r.get("master_contract_vendor_name") or ""
        var = r.get("value_added_re_seller_var_vendor_name") or ""
        reg.add_prime(ven, cn)
        if var and normalize_vendor_name(var) != normalize_vendor_name(ven):
            reg.add_reseller(var, cn, ven, "ny_ogs_var")
    return reg


# --------------------------------------------------------------------------------------
# Certification grades
# --------------------------------------------------------------------------------------

# Ordered from most to least specific. "not_reported" = the source has no such field.
CERT_GRADES = [
    "minority_or_women_owned",  # HUB (TX), OMWBE (WA), MWBE (NY), minority flag (Baton Rouge)
    "disadvantaged_business",   # DBE
    "veteran_owned",            # incl. Texas HUB "Disabled Veteran"
    "small_business",
    "not_certified",
    "not_reported",
]


def _yes(v: Any) -> bool:
    return str(v or "").strip().lower() in {"y", "yes", "true", "1", "x"}


def harmonize_wa_cert(mwbe: str, small: str, vet: str) -> str:
    """WA agency-contract certification fields. FY2021 packs MWBE/DBE text into ``small``."""
    m, s, v = (mwbe or "").strip().lower(), (small or "").strip().lower(), (vet or "").strip().lower()
    if not (m or s or v):
        return "not_reported"
    text = f"{m} {s}"
    if _yes(m) or "owned" in m or re.search(r"\b(?:mbe|wbe|mwbe|minority|wom[ae]n)\b", text):
        return "minority_or_women_owned"
    if re.search(r"\bdbe\b|disadvantaged", text):
        return "disadvantaged_business"
    if _yes(v) or "veteran" in text:
        return "veteran_owned"
    if _yes(s) or "small" in s:
        return "small_business"
    return "not_certified"


def harmonize_flags_cert(minority: Any = None, dbe: Any = None, vet: Any = None, small: Any = None) -> str:
    vals = [minority, dbe, vet, small]
    if all(v in (None, "") for v in vals):
        return "not_reported"
    if _yes(minority):
        return "minority_or_women_owned"
    if _yes(dbe):
        return "disadvantaged_business"
    if _yes(vet):
        return "veteran_owned"
    if _yes(small):
        return "small_business"
    return "not_certified"


TX_HUB_ABBR = {"AS": "Asian", "WO": "Woman", "HI": "Hispanic", "BL": "Black", "AI": "Native American", "DV": "Disabled Veteran"}


def harmonize_tx_hub(hub: str) -> str:
    h = (hub or "").strip().lower()
    if not h:
        return "not_reported"
    if h in {"non hub", "n/a", "na", "none", "non-hub"}:
        return "not_certified"
    if "veteran" in h or h == "dv":
        return "veteran_owned"
    return "minority_or_women_owned"


# --------------------------------------------------------------------------------------
# Cooperative sales & reseller relationships
# --------------------------------------------------------------------------------------

TX_CUSTOMER = {
    "k-12": "k12", "local government": "local_government", "higher ed": "higher_ed",
    "state agency": "state_agency", "out of state": "out_of_state",
    "assistance org": "nonprofit_assistance_org", "other": "other",
}
DE_SPEND_GROUP = {"A": "state_agency", "S": "k12", "M": "local_government"}


WA_CUSTOMER = {
    "state agency": "state_agency", "enterprise services": "state_agency", "component units": "state_agency",
    "higher ed (state agency)": "higher_ed",
    "cities including towns": "local_government", "county": "local_government",
    "districts, other": "local_government", "port districts": "local_government",
    "libraries": "local_government", "other govt": "local_government",
    "school districts": "k12", "private schools": "k12",
    "tribes": "tribal_government",
    "us states/territories": "out_of_state", "federal government": "federal",
    "usg customers-do not use": "federal",
    "non-profit": "nonprofit_assistance_org", "association/medical": "nonprofit_assistance_org",
}


def harmonize_wa_customer(ct: str) -> str:
    c = (ct or "").strip().lower()
    if c in WA_CUSTOMER:
        return WA_CUSTOMER[c]
    if "higher ed" in c or "college" in c or "universit" in c:
        return "higher_ed"
    if "school" in c:
        return "k12"
    if any(k in c for k in ("city", "cities", "county", "district", "municipal", "port", "town")):
        return "local_government"
    if "tribe" in c or "tribal" in c:
        return "tribal_government"
    return "unknown" if c in ("", "customers", "miscellaneous") else "other"


def _f(v: Any) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def build_cooperative_sales(raw_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    # Texas DIR cooperative contracts (used statewide by local govts, schools, out-of-state)
    for ds in ("tx_dir_sales_archive", "tx_dir_sales_fy2026"):
        for r in _load(raw_dir, ds):
            vendor, reseller = r.get("vendor_name") or "", r.get("reseller_name") or ""
            via_reseller = bool(reseller) and normalize_vendor_name(reseller) != normalize_vendor_name(vendor)
            rows.append({
                "program": "texas_dir",
                "coop_vehicle": "texas_dir",
                "state": "TX",
                "fiscal_year": r.get("fiscal_year") or "",
                "customer_type": TX_CUSTOMER.get((r.get("customer_type") or "").strip().lower(), "other"),
                "contract_number": r.get("contract_number") or "",
                "contract_desc": " / ".join(x for x in (r.get("contract_type"), r.get("contract_subtype")) if x),
                "vendor_name": vendor,
                "vendor_certification": harmonize_tx_hub(r.get("vendor_hub_type") or ""),
                "vendor_cert_raw": r.get("vendor_hub_type") or "",
                "reseller_name": reseller if via_reseller else "",
                "reseller_certification": harmonize_tx_hub(r.get("reseller_hub_type") or "") if via_reseller else "",
                "reseller_cert_raw": (r.get("reseller_hub_type") or "") if via_reseller else "",
                "sales_channel": "via_reseller" if via_reseller else "direct_prime",
                "sales": _f(r.get("sales")),
                "n_lines": int(_f(r.get("n_lines"))),
            })

    # Washington DES statewide master contracts (open to cities, counties, schools, ...)
    for r in _load(raw_dir, "wa_master_contract_sales"):
        rows.append({
            "program": "washington_des_master",
            "coop_vehicle": detect_coop_vehicle(r.get("contract_title") or "") or STATE_MASTER,
            "state": "WA",
            "fiscal_year": r.get("year") or "",
            "customer_type": harmonize_wa_customer(r.get("customer_type") or ""),
            "contract_number": r.get("contract_number") or "",
            "contract_desc": r.get("contract_title") or "",
            "vendor_name": r.get("vendor_name") or "",
            "vendor_certification": harmonize_flags_cert(
                minority=r.get("omwbe"), vet=r.get("vet_owned"), small=r.get("small_business")),
            "vendor_cert_raw": f"omwbe={r.get('omwbe','')};vet={r.get('vet_owned','')};small={r.get('small_business','')}",
            "reseller_name": "",
            "reseller_certification": "",
            "reseller_cert_raw": "",
            "sales_channel": "direct_prime",
            "sales": _f(r.get("sales")),
            "n_lines": int(_f(r.get("n_lines"))),
        })

    # Delaware: external cooperative contracts and statewide central contracts
    for ds, program, amt_field, vendor_field in (
        ("delaware_coop_spend", "delaware_cooperative", "grand_total", "vendor"),
        ("delaware_central_spend", "delaware_central", "total_spend", "vendor_name"),
    ):
        for r in _load(raw_dir, ds):
            desc = r.get("contract_description") or ""
            lcn = r.get("long_contract_number") or ""
            vehicle = detect_coop_vehicle(desc, lcn)
            if not vehicle:
                vehicle = "other_cooperative" if program == "delaware_cooperative" else STATE_MASTER
            rows.append({
                "program": program,
                "coop_vehicle": vehicle,
                "state": "DE",
                "fiscal_year": r.get("fy") or r.get("fiscal_year") or "",
                "customer_type": DE_SPEND_GROUP.get((r.get("spend_group") or "").strip().upper(), "other"),
                "contract_number": lcn or r.get("short_contract_number") or "",
                "contract_desc": desc,
                "vendor_name": r.get(vendor_field) or "",
                "vendor_certification": "not_reported",
                "vendor_cert_raw": "",
                "reseller_name": "",
                "reseller_certification": "",
                "reseller_cert_raw": "",
                "sales_channel": "direct_prime",
                "sales": _f(r.get(amt_field)),
                "n_lines": 1,
            })
    return rows


def build_reseller_relationships(raw_dir: Path) -> list[dict[str, Any]]:
    seen: set[tuple[str, ...]] = set()
    out: list[dict[str, Any]] = []

    def push(row: dict[str, Any]) -> None:
        key = (row["source"], row["contract_id"], normalize_vendor_name(row["prime_vendor"]), normalize_vendor_name(row["reseller"]))
        if key in seen:
            return
        seen.add(key)
        out.append(row)

    for r in _load(raw_dir, "tx_dir_active_contracts"):
        prime, res = r.get("primary_vendor_name") or "", r.get("reseller_name") or ""
        if not res or normalize_vendor_name(res) == normalize_vendor_name(prime):
            continue
        push({
            "source": "texas_dir_active_contracts", "state": "TX",
            "contract_id": r.get("contract_number") or "",
            "contract_desc": r.get("rfo_description") or "",
            "contract_type": " / ".join(x for x in (r.get("contract_type"), r.get("contract_subtype")) if x),
            "prime_vendor": prime,
            "prime_certification": harmonize_tx_hub(r.get("primary_vendor_hub_status") or ""),
            "prime_cert_raw": r.get("primary_vendor_hub_status") or "",
            "reseller": res,
            "reseller_certification": harmonize_tx_hub(r.get("reseller_hub_status") or ""),
            "reseller_cert_raw": r.get("reseller_hub_status") or "",
        })
    for r in _load(raw_dir, "ny_var_report"):
        prime, var = r.get("master_contract_vendor_name") or "", r.get("value_added_re_seller_var_vendor_name") or ""
        if not var:
            continue
        push({
            "source": "ny_ogs_var_report", "state": "NY",
            "contract_id": r.get("master_contract_id") or "",
            "contract_desc": r.get("contract_description") or "",
            "contract_type": "",
            "prime_vendor": prime,
            "prime_certification": "not_reported",
            "prime_cert_raw": "",
            "reseller": var,
            "reseller_certification": "not_reported",
            "reseller_cert_raw": "",
        })
    return out


# --------------------------------------------------------------------------------------
# Washington IT-contract cooperative flags (joined onto WA agency contracts)
# --------------------------------------------------------------------------------------

def agency_key(agency: str) -> str:
    m = re.match(r"\s*(\d{1,3})\b", str(agency or ""))
    return m.group(1).zfill(3) if m else re.sub(r"[^A-Z]", "", str(agency or "").upper())


def contract_key(cno: str) -> str:
    s = re.sub(r"\s*\([^)]*\)\s*$", "", (cno or "").upper())
    return re.sub(r"[^A-Z0-9]", "", s).lstrip("0")


def load_wa_it_coop_flags(raw_dir: Path) -> dict[tuple[str, str], str]:
    flags: dict[tuple[str, str], str] = {}
    for year in range(2020, 2026):
        for r in _load(raw_dir, f"wa_it_contracts_{year}"):
            agency = r.get("agency_number_agency_name") or r.get("agency_number") or r.get("agency_name") or ""
            cno = r.get("contract_no") or ""
            if not cno:
                continue
            name = normalize_coop_name(r.get("cooperative_name_if_applicable") or "")
            if not name and _yes(r.get("cooperative_purchase_yes")):
                name = "other_cooperative"
            key = (agency_key(agency), contract_key(cno))
            if name and (key not in flags or flags[key] == "other_cooperative"):
                flags[key] = name
            else:
                flags.setdefault(key, "")
    return flags
