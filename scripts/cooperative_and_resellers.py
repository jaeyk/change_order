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
from collections import Counter, defaultdict
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
    ("tips_taps", re.compile(r"\btips(?:/taps|-usa| usa| contract| cooperative| #| no\b)|interlocal purchasing system")),
    # free text needs context: "E & I" alone is often "electrical & instrumentation"
    ("e_and_i", re.compile(r"\be ?& ?i (?:cooperative|contract)|\be and i cooperative")),
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
    ("mmcap", re.compile(r"mmcap|multi-?state contracting alliance")),
    # A (named) state's own contract used by someone else, e.g. "State of Illinois contract
    # CMS7903500" in Chicago's ledger, "State Contract 4400028024" in Baton Rouge's.
    ("state_contract", re.compile(r"\bstate (?:of [a-z]+ )?(?:contract|price agreement|term contract)\b(?!or)|\bcms ?\d{5,}|cms master")),
    ("other_cooperative", re.compile(r"cooperative (?:purchas|contract|procurement)|piggy-?back|co-?op contract|joint purchas|reference contract")),
]

# Additional loose rules used only for explicit "which cooperative?" fields.
EXPLICIT_EXTRA: list[tuple[str, re.Pattern[str]]] = [
    ("gsa_federal", re.compile(r"^gsa\b")),
    ("tips_taps", re.compile(r"^tips\b")),
    ("e_and_i", re.compile(r"^e ?& ?i\b|^e and i\b")),
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


# --------------------------------------------------------------------------------------
# Direction of cooperative purchasing: horizontal vs. vertical
# --------------------------------------------------------------------------------------
# Level of government that *established* each vehicle.
VEHICLE_LEVEL: dict[str, str] = {
    "gsa_federal": "federal",
    "naspo_valuepoint": "multi_state",   # lead state solicits for participating states
    "mhec": "multi_state",               # interstate compact
    "mmcap": "multi_state",
    "texas_dir": "state",
    STATE_MASTER: "state",
    "state_contract": "state",
    "calif_cmas": "state",
    "e_and_i": "higher_ed_consortium",
    "internet2": "higher_ed_consortium",
    "sourcewell": "local_consortium",    # MN service cooperative (local govts / schools)
    "omnia_partners": "local_consortium",  # lead public agencies are cities/counties/schools
    "tips_taps": "local_consortium",     # Texas ESC Region 8
    "ncpa": "local_consortium",
    "buyboard": "local_consortium",      # Texas school boards association
    "hgacbuy": "local_consortium",       # Houston-Galveston Area Council
    "kcda": "local_consortium",
    "wsipc": "local_consortium",
    "oetc": "local_consortium",
    "peppm": "local_consortium",
    "local_joint_purchase": "local_consortium",  # joint solicitation among local agencies
    "other_cooperative": "unknown",
}

# Rank used to compare the vehicle's level with the buyer's level.
LEVEL_RANK = {
    "federal": 3,
    "multi_state": 2, "state": 2, "higher_ed_consortium": 2,  # public universities are state entities
    "local_consortium": 1, "local": 1,
}

# Buyer level for contract-ledger gov_level values and harmonized customer types.
BUYER_LEVEL = {
    "state": "state", "state_agency": "state", "higher_ed": "state",
    "county": "local", "city": "local", "special_authority": "local",
    "local_government": "local", "k12": "local",
    "federal": "federal",
    "out_of_state": "other_state",
}

DIRECTIONS = ["horizontal", "vertical_downward", "vertical_upward", "central", "unknown"]


# Vehicles owned by one specific state: "central" only for that state's own buyers.
VEHICLE_HOME_STATE = {"texas_dir": "TX", "calif_cmas": "CA"}


def coop_direction(vehicle: str, buyer: str, buyer_state: str = "") -> str:
    """Classify how a buyer relates to the government that set up the vehicle.

    horizontal         peers pooling: states via NASPO ValuePoint / MHEC; locals via Sourcewell,
                       OMNIA, TIPS, BuyBoard...; one state using another state's contract
    vertical_downward  a lower level buying off a higher level's contract: cities, counties and
                       school districts on Texas DIR / WA DES / state contracts; states or
                       locals on GSA schedules; locals on NASPO ValuePoint via a state addendum
    vertical_upward    a higher level buying through a local-government consortium (e.g. a
                       state agency using Sourcewell or OMNIA)
    central            a state agency using its own state's central/master contract
                       (centralized purchasing, not cooperative)
    unknown            vehicle or buyer level unknown
    """
    if not vehicle:
        return ""
    v_level = VEHICLE_LEVEL.get(vehicle, "unknown")
    b_level = BUYER_LEVEL.get(buyer, buyer)
    if v_level == "unknown" or b_level not in ("federal", "state", "local", "other_state"):
        return "unknown"
    if b_level == "other_state":
        # e.g. another state's agency (or its locals) buying off Texas DIR
        return "horizontal" if v_level in ("state", "multi_state") else "unknown"
    vr, br = LEVEL_RANK[v_level], LEVEL_RANK[b_level]
    if vr > br:
        return "vertical_downward"
    if vr < br:
        return "vertical_upward"
    if v_level == "state":
        home = VEHICLE_HOME_STATE.get(vehicle)
        if home and buyer_state and buyer_state != home:
            return "horizontal"  # another state's contract
        return "central"  # a state agency on its own state's master contract
    return "horizontal"


def procurement_channel(vehicle: str, direction: str = "") -> str:
    if not vehicle:
        return "direct_or_unknown"
    if direction == "central":
        return "central_state_contract"
    return f"cooperative_{direction or 'unknown'}"


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
        self.dealers: set[str] = set()  # federal schedule holders registered under wholesale/retail NAICS
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
        if key in self.exact or key in self.dealers:
            return "authorized_reseller"
        for p in self.prefixes:
            if key == p or key.startswith(p + " "):
                return "authorized_reseller"
        return "prime_or_direct"

    def rows(self) -> list[dict[str, Any]]:
        out = []
        for k in sorted(set(self.as_reseller) | set(self.prefixes) | self.dealers):
            n_res = len(self.as_reseller.get(k, ()))
            n_prime = len(self.as_prime.get(k, ()))
            curated = k in self.prefixes
            extra = ({"curated"} if curated else set()) | ({"fss_dealer_naics"} if k in self.dealers else set())
            out.append({
                "reseller_key": k,
                "reseller_relationships": n_res,
                "prime_contracts": n_prime,
                "classified_as_reseller": int(curated or k in self.exact or k in self.dealers),
                "sources": ";".join(sorted(self.sources.get(k, set()) | extra)),
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
    # Federal schedule holders whose schedule contracts are mostly under wholesale/retail NAICS
    # (42xxxx, 44-45xxxx) are dealers/resellers -- this reaches regional resellers nationwide.
    roles: dict[str, Counter[str]] = defaultdict(Counter)
    for r in _load(raw_dir, "federal_supply_schedules"):
        key = normalize_vendor_name(r.get("Recipient Name") or "")
        if len(key) >= 3:
            roles[key][naics_role(r.get("naics_code") or "")] += 1
    for key, c in roles.items():
        if c.most_common(1)[0][0] == "dealer_reseller" and not reg._is_oem(key):
            reg.dealers.add(key)
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
    rows = _build_cooperative_sales(raw_dir)
    for r in rows:
        r["buyer_level"] = BUYER_LEVEL.get(r["customer_type"], "unknown")
        r["vehicle_level"] = VEHICLE_LEVEL.get(r["coop_vehicle"], "unknown")
        r["coop_direction"] = coop_direction(r["coop_vehicle"], r["customer_type"])
    return rows


def _build_cooperative_sales(raw_dir: Path) -> list[dict[str, Any]]:
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


# --------------------------------------------------------------------------------------
# Federal Supply Schedules (GSA MAS / VA FSS): extra reseller evidence (holders under
# wholesale/retail NAICS are dealers) and a vendor-qualification covariate.
# --------------------------------------------------------------------------------------

def naics_role(code: str) -> str:
    """Manufacturer vs. dealer/reseller vs. service provider, from a NAICS code."""
    c = str(code or "")
    if c[:2] in ("31", "32", "33"):
        return "manufacturer"
    if c[:2] == "42" or c[:2] in ("44", "45"):
        return "dealer_reseller"
    if c[:2] in ("51", "54", "56", "61", "62", "81", "23", "48", "49", "53"):
        return "service_provider"
    return "other" if c else "unknown"


def schedule_program(r: dict[str, Any]) -> str:
    agency = (r.get("Awarding Agency") or "").lower()
    if "general services" in agency:
        return "gsa_mas"
    if "veterans" in agency:
        return "va_fss"
    return "other_fss"


def load_fss(raw_dir: Path) -> list[dict[str, Any]]:
    return _load(raw_dir, "federal_supply_schedules")


# --------------------------------------------------------------------------------------
# Vendor qualifications: which pre-qualified vehicles a firm holds (used as covariates)
# --------------------------------------------------------------------------------------

QUAL_FLAGS = [
    "gsa_mas_holder", "va_fss_holder", "texas_dir_prime", "texas_dir_reseller",
    "ny_ogs_master_holder", "ny_ogs_var", "wa_des_master_holder", "delaware_contract_holder",
]


def build_vendor_qualifications(raw_dir: Path) -> dict[str, dict[str, Any]]:
    quals: dict[str, dict[str, Any]] = {}

    def q(name: str) -> dict[str, Any] | None:
        key = normalize_vendor_name(name)
        if len(key) < 3:
            return None
        if key not in quals:
            quals[key] = {"vendor_key": key, **{f: 0 for f in QUAL_FLAGS},
                          "fss_contracts": 0, "fss_naics_roles": Counter()}
        return quals[key]

    for r in load_fss(raw_dir):
        rec = q(r.get("Recipient Name") or "")
        if rec is None:
            continue
        prog = schedule_program(r)
        if prog == "gsa_mas":
            rec["gsa_mas_holder"] = 1
        elif prog == "va_fss":
            rec["va_fss_holder"] = 1
        rec["fss_contracts"] += 1
        rec["fss_naics_roles"][naics_role(r.get("naics_code") or "")] += 1

    for ds in ("tx_dir_sales_archive", "tx_dir_sales_fy2026"):
        for r in _load(raw_dir, ds):
            if (rec := q(r.get("vendor_name") or "")):
                rec["texas_dir_prime"] = 1
            res = r.get("reseller_name") or ""
            if res and normalize_vendor_name(res) != normalize_vendor_name(r.get("vendor_name") or ""):
                if (rec := q(res)):
                    rec["texas_dir_reseller"] = 1
    for r in _load(raw_dir, "tx_dir_active_contracts"):
        if (rec := q(r.get("primary_vendor_name") or "")):
            rec["texas_dir_prime"] = 1
        res = r.get("reseller_name") or ""
        if res and normalize_vendor_name(res) != normalize_vendor_name(r.get("primary_vendor_name") or ""):
            if (rec := q(res)):
                rec["texas_dir_reseller"] = 1
    for r in _load(raw_dir, "ny_var_report"):
        if (rec := q(r.get("master_contract_vendor_name") or "")):
            rec["ny_ogs_master_holder"] = 1
        if (rec := q(r.get("value_added_re_seller_var_vendor_name") or "")):
            rec["ny_ogs_var"] = 1
    for r in _load(raw_dir, "wa_master_contract_sales"):
        if (rec := q(r.get("vendor_name") or "")):
            rec["wa_des_master_holder"] = 1
    for ds, field in (("delaware_coop_spend", "vendor"), ("delaware_central_spend", "vendor_name")):
        for r in _load(raw_dir, ds):
            if (rec := q(r.get(field) or "")):
                rec["delaware_contract_holder"] = 1

    for rec in quals.values():
        roles: Counter[str] = rec.pop("fss_naics_roles")
        rec["fss_holder_role"] = roles.most_common(1)[0][0] if roles else ""
        prime_flags = ("texas_dir_prime", "ny_ogs_master_holder", "wa_des_master_holder", "delaware_contract_holder")
        rec["n_vehicles_held"] = sum(rec[f] for f in QUAL_FLAGS)
        if rec["gsa_mas_holder"] or rec["va_fss_holder"]:
            tier = "federal_schedule_holder"
        elif any(rec[f] for f in prime_flags):
            tier = "state_vehicle_prime"
        elif rec["texas_dir_reseller"] or rec["ny_ogs_var"]:
            tier = "authorized_reseller_only"
        else:
            tier = "none_observed"
        rec["qualification_tier"] = tier
    return quals


def vendor_qualification(quals: dict[str, dict[str, Any]], vendor_name: str) -> dict[str, Any]:
    rec = quals.get(normalize_vendor_name(vendor_name))
    if not rec:
        return {"qualification_tier": "none_observed", "gsa_mas_holder": 0, "n_vehicles_held": 0, "fss_holder_role": ""}
    return {k: rec[k] for k in ("qualification_tier", "gsa_mas_holder", "n_vehicles_held", "fss_holder_role")}


# --------------------------------------------------------------------------------------
# Award structure of cooperative vehicles
# --------------------------------------------------------------------------------------

def build_award_structure(raw_dir: Path) -> list[dict[str, Any]]:
    """One row per (source, contract): single vs. multiple award, prime-direct vs. resellers.

    * multiple_award: >= 2 prime contractors under the same solicitation / statewide contract
      (Texas DIR RFO, NY OGS lot, WA DES or Delaware statewide contract number).
    * reseller dimension: number of distinct authorized resellers selling under the contract
      (Texas DIR, NY OGS).
    """
    out: list[dict[str, Any]] = []

    def structure(n_primes: int, n_resellers: int | None, holder_role: str = "") -> str:
        base = "multiple_award" if n_primes > 1 else "single_award"
        if holder_role == "dealer_reseller":
            return f"{base}_dealer_holder"
        if n_resellers is None:
            return f"{base}_prime_direct_or_unknown"
        return f"{base}_with_resellers" if n_resellers > 0 else f"{base}_prime_direct"

    # Texas DIR: RFO -> contracts (one prime each) -> resellers (active list + sales)
    tx_resellers: dict[str, set[str]] = defaultdict(set)
    tx_prime: dict[str, str] = {}
    tx_rfo: dict[str, str] = {}
    tx_desc: dict[str, str] = {}
    for r in _load(raw_dir, "tx_dir_active_contracts"):
        cn = r.get("contract_number") or ""
        tx_prime[cn] = r.get("primary_vendor_name") or tx_prime.get(cn, "")
        tx_rfo[cn] = r.get("rfo_number") or ""
        tx_desc[cn] = r.get("rfo_description") or ""
        res = r.get("reseller_name") or ""
        if res and normalize_vendor_name(res) != normalize_vendor_name(tx_prime[cn]):
            tx_resellers[cn].add(normalize_vendor_name(res))
    for ds in ("tx_dir_sales_archive", "tx_dir_sales_fy2026"):
        for r in _load(raw_dir, ds):
            cn = r.get("contract_number") or ""
            tx_prime.setdefault(cn, r.get("vendor_name") or "")
            if r.get("rfo_number"):
                tx_rfo.setdefault(cn, r["rfo_number"])
            tx_desc.setdefault(cn, " / ".join(x for x in (r.get("contract_type"), r.get("contract_subtype")) if x))
            res = r.get("reseller_name") or ""
            if res and normalize_vendor_name(res) != normalize_vendor_name(r.get("vendor_name") or ""):
                tx_resellers[cn].add(normalize_vendor_name(res))
    rfo_size = Counter(v for v in tx_rfo.values() if v)
    for cn, prime in tx_prime.items():
        rfo = tx_rfo.get(cn, "")
        n_primes = rfo_size[rfo] if rfo else 0
        out.append({"source": "texas_dir", "solicitation": rfo, "contract_id": cn, "contract_desc": tx_desc.get(cn, ""),
                    "prime_vendor": prime, "n_primes_in_solicitation": n_primes or "",
                    "n_resellers": len(tx_resellers[cn]),
                    "award_structure": structure(n_primes if rfo else 1, len(tx_resellers[cn])) if rfo else
                    ("unknown_award_with_resellers" if tx_resellers[cn] else "unknown_award_prime_direct")})

    # NY OGS: lot (contract description) -> master contracts -> VARs
    ny: dict[str, dict[str, Any]] = {}
    for r in _load(raw_dir, "ny_var_report"):
        mc = r.get("master_contract_id") or ""
        d = ny.setdefault(mc, {"desc": r.get("contract_description") or "", "prime": r.get("master_contract_vendor_name") or "", "vars": set()})
        var = r.get("value_added_re_seller_var_vendor_name") or ""
        if var and normalize_vendor_name(var) != normalize_vendor_name(d["prime"]):
            d["vars"].add(normalize_vendor_name(var))
    lot_size = Counter(d["desc"] for d in ny.values())
    for mc, d in ny.items():
        out.append({"source": "ny_ogs", "solicitation": d["desc"], "contract_id": mc, "contract_desc": d["desc"],
                    "prime_vendor": d["prime"], "n_primes_in_solicitation": lot_size[d["desc"]],
                    "n_resellers": len(d["vars"]),
                    "award_structure": structure(lot_size[d["desc"]], len(d["vars"]))})

    # WA DES and Delaware statewide contracts: contract number -> vendors (resellers not reported)
    for ds, src, cfield, dfield, vfield in (
        ("wa_master_contract_sales", "washington_des", "contract_number", "contract_title", "vendor_name"),
        ("delaware_central_spend", "delaware_central", "long_contract_number", "contract_description", "vendor_name"),
        ("delaware_coop_spend", "delaware_cooperative", "long_contract_number", "contract_description", "vendor"),
    ):
        vendors: dict[str, set[str]] = defaultdict(set)
        names: dict[tuple[str, str], str] = {}
        desc: dict[str, str] = {}
        for r in _load(raw_dir, ds):
            cn = r.get(cfield) or ""
            v = normalize_vendor_name(r.get(vfield) or "")
            if cn and v:
                vendors[cn].add(v)
                names[(cn, v)] = r.get(vfield) or ""
                desc[cn] = r.get(dfield) or ""
        for cn, vs in vendors.items():
            for v in sorted(vs):
                out.append({"source": src, "solicitation": cn, "contract_id": f"{cn}:{v}", "contract_desc": desc[cn],
                            "prime_vendor": names[(cn, v)], "n_primes_in_solicitation": len(vs),
                            "n_resellers": "", "award_structure": structure(len(vs), None)})

    # Federal Supply Schedules: every schedule is multiple-award by design
    fss = load_fss(raw_dir)
    sched_size = Counter(schedule_program(r) for r in fss)
    for r in fss:
        prog = schedule_program(r)
        role = naics_role(r.get("naics_code") or "")
        out.append({"source": prog, "solicitation": prog, "contract_id": r.get("Award ID") or "",
                    "contract_desc": r.get("Description") or "", "prime_vendor": r.get("Recipient Name") or "",
                    "n_primes_in_solicitation": sched_size[prog], "n_resellers": "",
                    "award_structure": structure(sched_size[prog], None, role),
                    "holder_naics_role": role, "naics_code": r.get("naics_code") or ""})
    return out
