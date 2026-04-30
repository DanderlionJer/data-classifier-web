"""Selectable compliance frameworks for rule filtering."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_COUNTRY_JSON = Path(__file__).resolve().parent / "rules" / "country_frameworks.json"
_country_rows_cache: list[dict[str, Any]] | None = None
_country_by_id_cache: dict[str, dict[str, Any]] | None = None


# --- Canonical IDs (UI / API / country_frameworks.json) -----------------------------
UNIVERSAL = "UNIVERSAL"

FW_35273 = "35273"
FW_43697 = "43697"
FW_PIPL = "PIPL"
FW_GDPR = "GDPR"
FW_UK_GDPR_DPA = "UK_GDPR_DPA"
FW_FADP = "FADP"
FW_APPI = "APPI"
FW_PIPA = "PIPA"
FW_PDPA_SG = "PDPA_SG"
FW_PRIVACY_ACT_AU = "PRIVACY_ACT_AU"
FW_PIPEDA_CA = "PIPEDA_CA"
FW_DPDPA_IN = "DPDPA_IN"
FW_LGPD = "LGPD"
FW_PDPA_NZ = "PDPA_NZ"
FW_PDPA_MY = "PDPA_MY"
FW_PDPA_TH = "PDPA_TH"
FW_VN_PDPD = "VN_PDPD"
FW_DPA_PH = "DPA_PH"
FW_PDP_ID = "PDP_ID"
FW_LFPDPPP_MX = "LFPDPPP_MX"
FW_PDPL_AE = "PDPL_AE"
FW_PDPL_SA = "PDPL_SA"
FW_KVKK = "KVKK"
FW_POPIA = "POPIA"
FW_IL_PRIVACY = "IL_PRIVACY"
FW_PDPA_TW = "PDPA_TW"
FW_PDPO_HK = "PDPO_HK"
FW_PDPA_MO = "PDPA_MO"
FW_AR_PDPA = "AR_PDPA"
FW_CO_PDPA = "CO_PDPA"
FW_US_CA_CPRA = "US_CA_CPRA"

FW_EO14117 = "EO14117"

# When multiple frameworks are selected and EO14117 is among them, rules that map
# to EO14117 get this boost for suppression ordering only (see effective_rule_priority).
EO14117_PRIORITY_BOOST_WHEN_MULTI = 5
FW_US_HIPAA = "US_HIPAA"
FW_US_GLBA = "US_GLBA"
FW_US_COPPA = "US_COPPA"
FW_PCI_DSS = "PCI_DSS"
FW_NIST_CSF = "NIST_CSF"
FW_US_FED_CYBER = "US_FED_CYBER"

# Jurisdiction-style privacy laws (metadata tagging aligns across these for PII rules).
PRIVACY_LAW_CORE: tuple[str, ...] = (
    FW_35273,
    FW_43697,
    FW_PIPL,
    FW_GDPR,
    FW_UK_GDPR_DPA,
    FW_FADP,
    FW_APPI,
    FW_PIPA,
    FW_PDPA_SG,
    FW_PRIVACY_ACT_AU,
    FW_PIPEDA_CA,
    FW_DPDPA_IN,
    FW_LGPD,
    FW_PDPA_NZ,
    FW_PDPA_MY,
    FW_PDPA_TH,
    FW_VN_PDPD,
    FW_DPA_PH,
    FW_PDP_ID,
    FW_LFPDPPP_MX,
    FW_PDPL_AE,
    FW_PDPL_SA,
    FW_KVKK,
    FW_POPIA,
    FW_IL_PRIVACY,
    FW_PDPA_TW,
    FW_PDPO_HK,
    FW_PDPA_MO,
    FW_AR_PDPA,
    FW_CO_PDPA,
    FW_US_CA_CPRA,
)

STANDARDS_REGISTRY: list[dict[str, str]] = [
    {
        "id": FW_35273,
        "code": "GB/T 35273-2020",
        "title_zh": "信息安全技术 个人信息安全规范",
        "title_en": "Personal information security specification",
    },
    {
        "id": FW_43697,
        "code": "GB/T 43697-2024",
        "title_zh": "数据安全技术 数据分类分级规则",
        "title_en": "Data security technology — Rules for data classification and grading",
        "reference_zh": "https://baike.baidu.com/item/%E6%95%B0%E6%8D%AE%E5%AE%89%E5%85%A8%E6%8A%80%E6%9C%AF%E6%95%B0%E6%8D%AE%E5%88%86%E7%B1%BB%E5%88%86%E7%BA%A7%E8%A7%84%E5%88%99/64208400",
    },
    {
        "id": FW_PIPL,
        "code": "PIPL",
        "title_zh": "中华人民共和国个人信息保护法",
        "title_en": "Personal Information Protection Law of the PRC",
    },
    {
        "id": FW_GDPR,
        "code": "GDPR",
        "title_zh": "欧盟通用数据保护条例",
        "title_en": "EU General Data Protection Regulation",
    },
    {
        "id": FW_UK_GDPR_DPA,
        "code": "UK GDPR + DPA 2018",
        "title_zh": "英国数据保护（UK GDPR 与《2018 数据保护法》）",
        "title_en": "UK GDPR and Data Protection Act 2018",
    },
    {
        "id": FW_FADP,
        "code": "FADP",
        "title_zh": "瑞士联邦数据保护法",
        "title_en": "Swiss Federal Act on Data Protection",
    },
    {
        "id": FW_APPI,
        "code": "APPI",
        "title_zh": "日本个人信息保护法",
        "title_en": "Act on the Protection of Personal Information (Japan)",
    },
    {
        "id": FW_PIPA,
        "code": "PIPA",
        "title_zh": "韩国个人信息保护法",
        "title_en": "Personal Information Protection Act (Korea)",
    },
    {
        "id": FW_PDPA_SG,
        "code": "PDPA (SG)",
        "title_zh": "新加坡个人数据保护法",
        "title_en": "Singapore Personal Data Protection Act",
    },
    {
        "id": FW_PRIVACY_ACT_AU,
        "code": "Privacy Act 1988 (AU)",
        "title_zh": "澳大利亚隐私法（含 APPs）",
        "title_en": "Australia Privacy Act 1988",
    },
    {
        "id": FW_PIPEDA_CA,
        "code": "PIPEDA",
        "title_zh": "加拿大个人信息保护与电子文档法",
        "title_en": "Personal Information Protection and Electronic Documents Act",
    },
    {
        "id": FW_DPDPA_IN,
        "code": "DPDPA",
        "title_zh": "印度数字个人数据保护法",
        "title_en": "Digital Personal Data Protection Act (India)",
    },
    {
        "id": FW_LGPD,
        "code": "LGPD",
        "title_zh": "巴西通用数据保护法",
        "title_en": "Lei Geral de Proteção de Dados (Brazil)",
    },
    {
        "id": FW_PDPA_NZ,
        "code": "Privacy Act 2020 (NZ)",
        "title_zh": "新西兰隐私法 2020",
        "title_en": "New Zealand Privacy Act 2020",
    },
    {
        "id": FW_PDPA_MY,
        "code": "PDPA (MY)",
        "title_zh": "马来西亚个人数据保护法",
        "title_en": "Malaysia Personal Data Protection Act",
    },
    {
        "id": FW_PDPA_TH,
        "code": "PDPA (TH)",
        "title_zh": "泰国个人数据保护法",
        "title_en": "Thailand Personal Data Protection Act",
    },
    {
        "id": FW_VN_PDPD,
        "code": "Decree 13 / PD (VN)",
        "title_zh": "越南个人数据保护相关法令（如第 13/2023/ND-CP 号议定）",
        "title_en": "Viet Nam personal data protection decree context",
    },
    {
        "id": FW_DPA_PH,
        "code": "DPA (PH)",
        "title_zh": "菲律宾数据隐私法",
        "title_en": "Data Privacy Act of 2012 (Philippines)",
    },
    {
        "id": FW_PDP_ID,
        "code": "UU PDP",
        "title_zh": "印度尼西亚个人数据保护法",
        "title_en": "Indonesia Personal Data Protection Law",
    },
    {
        "id": FW_LFPDPPP_MX,
        "code": "LFPDPPP",
        "title_zh": "墨西哥联邦个人数据法",
        "title_en": "Federal Law on Protection of Personal Data (Mexico)",
    },
    {
        "id": FW_PDPL_AE,
        "code": "PDPL (AE)",
        "title_zh": "阿联酋个人数据保护法",
        "title_en": "UAE Personal Data Protection Law",
    },
    {
        "id": FW_PDPL_SA,
        "code": "PDPL (SA)",
        "title_zh": "沙特阿拉伯个人数据法",
        "title_en": "Saudi Arabia Personal Data Protection Law",
    },
    {
        "id": FW_KVKK,
        "code": "KVKK",
        "title_zh": "土耳其个人数据保护法",
        "title_en": "Turkey Law on Protection of Personal Data",
    },
    {
        "id": FW_POPIA,
        "code": "POPIA",
        "title_zh": "南非个人信息保护法",
        "title_en": "Protection of Personal Information Act (South Africa)",
    },
    {
        "id": FW_IL_PRIVACY,
        "code": "Privacy (IL)",
        "title_zh": "以色列隐私保护法体系",
        "title_en": "Israel privacy protection laws",
    },
    {
        "id": FW_PDPA_TW,
        "code": "PDPA (TW)",
        "title_zh": "台湾个人资料保护法",
        "title_en": "Taiwan Personal Data Protection Act",
    },
    {
        "id": FW_PDPO_HK,
        "code": "PDPO",
        "title_zh": "香港个人资料（私隐）条例",
        "title_en": "Hong Kong Personal Data (Privacy) Ordinance",
    },
    {
        "id": FW_PDPA_MO,
        "code": "PDPA (MO)",
        "title_zh": "澳门个人资料保护法",
        "title_en": "Macao personal data protection law",
    },
    {
        "id": FW_AR_PDPA,
        "code": "Ley 25.326",
        "title_zh": "阿根廷个人数据保护法",
        "title_en": "Argentina Personal Data Protection Law 25.326",
    },
    {
        "id": FW_CO_PDPA,
        "code": "Ley 1581",
        "title_zh": "哥伦比亚个人数据保护法",
        "title_en": "Colombia Data Protection Law 1581",
    },
    {
        "id": FW_US_CA_CPRA,
        "code": "CPRA / CCPA",
        "title_zh": "美国加州消费者隐私法及修正案（CCPA/CPRA）",
        "title_en": "California Consumer Privacy Act / CPRA",
    },
    {
        "id": FW_EO14117,
        "code": "EO 14117",
        "title_zh": "美国第14117号行政令（敏感个人数据 / 关注国语境）",
        "title_en": "US Executive Order 14117 (sensitive data / countries of concern)",
        "scope_note_zh": "本工具为字段/元数据级粗分类，不单独实现 CPI 组合、linked/linkable 判定、bulk 门槛或政府相关数据分层。与多标准并选时，对带 EO14117 的规则在标签抑制链上略提高优先级。",
    },
    {
        "id": FW_US_HIPAA,
        "code": "HIPAA",
        "title_zh": "美国健康保险携带和责任法案（PHI / HIPAA）",
        "title_en": "US HIPAA (Privacy & Security Rules, PHI context)",
    },
    {
        "id": FW_US_GLBA,
        "code": "GLBA",
        "title_zh": "美国金融服务现代化法（GLBA）隐私规则语境",
        "title_en": "US Gramm-Leach-Bliley Act (financial privacy context)",
    },
    {
        "id": FW_US_COPPA,
        "code": "COPPA",
        "title_zh": "美国儿童在线隐私保护法",
        "title_en": "US Children's Online Privacy Protection Act",
    },
    {
        "id": FW_PCI_DSS,
        "code": "PCI DSS",
        "title_zh": "支付卡行业数据安全标准（行业合规参考）",
        "title_en": "PCI Data Security Standard",
    },
    {
        "id": FW_NIST_CSF,
        "code": "NIST CSF",
        "title_zh": "NIST 网络安全框架（自愿性控制参考）",
        "title_en": "NIST Cybersecurity Framework",
    },
    {
        "id": FW_US_FED_CYBER,
        "code": "US Fed Cyber",
        "title_zh": "美国联邦网络安全与关键基础设施语境（含 CISA 等指引性要求）",
        "title_en": "US federal cybersecurity & critical infrastructure (CISA context)",
    },
]

SELECTABLE_FRAMEWORK_IDS: frozenset[str] = frozenset(s["id"] for s in STANDARDS_REGISTRY)


def _dedupe(seq: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for x in seq:
        if x in seen:
            continue
        seen.add(x)
        out.append(x)
    return out


def _pii_with_us_health(eo14117: bool) -> list[str]:
    base = list(PRIVACY_LAW_CORE) + [FW_US_HIPAA]
    if eo14117:
        base.append(FW_EO14117)
    return _dedupe(base)


def _load_country_tables() -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    global _country_rows_cache, _country_by_id_cache
    if _country_rows_cache is not None and _country_by_id_cache is not None:
        return _country_rows_cache, _country_by_id_cache
    if not _COUNTRY_JSON.is_file():
        _country_rows_cache = []
        _country_by_id_cache = {}
        return _country_rows_cache, _country_by_id_cache
    raw = json.loads(_COUNTRY_JSON.read_text(encoding="utf-8"))
    rows_in = raw.get("countries") or []
    out_list: list[dict[str, Any]] = []
    by_id: dict[str, dict[str, Any]] = {}
    for row in rows_in:
        cid = str(row.get("id", "")).strip().upper()
        if not cid:
            continue
        fids = [str(x).strip() for x in (row.get("framework_ids") or []) if str(x).strip()]
        unknown = [x for x in fids if x not in SELECTABLE_FRAMEWORK_IDS]
        if unknown:
            raise ValueError(
                f"country_frameworks.json: country {cid} references unknown framework ids: "
                + ", ".join(unknown)
            )
        normalized = {
            **row,
            "id": cid,
            "framework_ids": fids,
        }
        out_list.append(normalized)
        by_id[cid] = normalized
    _country_rows_cache = out_list
    _country_by_id_cache = by_id
    return _country_rows_cache, _country_by_id_cache


def list_countries_for_api() -> list[dict[str, Any]]:
    """Countries / regions with default selectable framework ids (see country_frameworks.json)."""
    rows, _ = _load_country_tables()
    return [
        {
            "id": r["id"],
            "label_zh": r.get("label_zh") or "",
            "label_en": r.get("label_en") or "",
            "framework_ids": list(r.get("framework_ids") or []),
            "notes_zh": r.get("notes_zh") or "",
        }
        for r in rows
    ]


def framework_ids_for_country(country_id: str) -> list[str] | None:
    """Return framework ids for ISO code, or ``None`` if unknown."""
    _, by_id = _load_country_tables()
    row = by_id.get(country_id.strip().upper())
    if row is None:
        return None
    return list(row.get("framework_ids") or [])


def normalize_country_param(country: str | None) -> str | None:
    c = (country or "").strip().upper()
    if not c:
        return None
    if framework_ids_for_country(c) is None:
        raise ValueError(
            f"unknown country code: {c}. "
            f"Valid: {', '.join(sorted(_load_country_tables()[1]))}"
        )
    return c


def resolve_classify_frameworks(
    frameworks: str | None,
    country: str | None,
) -> frozenset[str] | None:
    """Non-empty ``frameworks`` wins; else use ``country`` defaults; else all rules (``None``)."""
    fw_sel = parse_frameworks_param(frameworks)
    if fw_sel:
        validate_framework_selection(fw_sel)
        return fw_sel
    cid = (country or "").strip().upper()
    if cid:
        ids = framework_ids_for_country(cid)
        if ids is None:
            raise ValueError(
                f"unknown country code: {cid}. "
                f"Valid: {', '.join(sorted(_load_country_tables()[1]))}"
            )
        if not ids:
            return None
        sel = frozenset(ids)
        validate_framework_selection(sel)
        return sel
    return None


_CYBER: list[str] = [FW_NIST_CSF, FW_US_FED_CYBER]
_CYBER_PCI: list[str] = [FW_NIST_CSF, FW_US_FED_CYBER, FW_PCI_DSS]

FRAMEWORKS_BY_RULE_ID: dict[str, list[str]] = {
    "pii_id_card": _pii_with_us_health(True),
    "passport_travel": _pii_with_us_health(True),
    "pii_phone": _pii_with_us_health(True),
    "pii_email": _pii_with_us_health(True),
    "pii_legal_name": _pii_with_us_health(True),
    "pii_login_alias": _pii_with_us_health(False),
    "pii_bank": _dedupe(_pii_with_us_health(True) + [FW_US_GLBA, FW_PCI_DSS]),
    "health": _pii_with_us_health(True),
    "biometric": _pii_with_us_health(True),
    "religion_belief": _pii_with_us_health(True),
    "political_opinion": _pii_with_us_health(True),
    "union_membership": _pii_with_us_health(True),
    "sexual_orientation": _pii_with_us_health(True),
    "genetic_data": _pii_with_us_health(True),
    "criminal_justice": _pii_with_us_health(True),
    "location": _pii_with_us_health(True),
    "vehicle_plate": _pii_with_us_health(True),
    "tax_social": _dedupe(_pii_with_us_health(True) + [FW_US_GLBA]),
    "ad_tracking_id": _pii_with_us_health(True),
    "child": _dedupe(_pii_with_us_health(True) + [FW_US_COPPA]),
    "password_secret": _dedupe([UNIVERSAL] + _pii_with_us_health(True) + _CYBER_PCI),
    "cookie_session": _dedupe([UNIVERSAL] + _pii_with_us_health(True) + _CYBER_PCI),
    "internal_only": _dedupe([UNIVERSAL] + list(PRIVACY_LAW_CORE)),
    "address_postal": _pii_with_us_health(True),
    "birth_gender": _pii_with_us_health(True),
    "internal_user_key": _dedupe([UNIVERSAL, FW_43697] + list(PRIVACY_LAW_CORE) + _CYBER),
    "party_customer_id": _dedupe(_pii_with_us_health(True) + [FW_US_GLBA]),
    "technical_id": _dedupe([UNIVERSAL, FW_43697] + list(PRIVACY_LAW_CORE) + _CYBER_PCI),
    "device_serial": _dedupe(_pii_with_us_health(True) + _CYBER),
    "network_device": _dedupe(_pii_with_us_health(True) + _CYBER),
    "education_job": _pii_with_us_health(False),
    "photo_avatar": _pii_with_us_health(True),
    "social_account": _pii_with_us_health(False),
    "crypto_salt": _dedupe([UNIVERSAL, FW_43697] + list(PRIVACY_LAW_CORE) + _CYBER),
    "encrypted_profile_payload": _dedupe(_pii_with_us_health(True) + _CYBER),
}


def enrich_rules_frameworks(rules: list[dict[str, Any]]) -> None:
    """Mutate rules in place: set ``frameworks`` if the key is absent.

    If ``frameworks`` is present (including ``[]``), it is left unchanged: an
    explicit empty list means the rule never applies when standards are selected.
    """
    default = _dedupe([UNIVERSAL] + list(PRIVACY_LAW_CORE))
    for r in rules:
        if "frameworks" in r:
            continue
        rid = str(r.get("id", ""))
        r["frameworks"] = list(
            FRAMEWORKS_BY_RULE_ID.get(
                rid,
                default,
            )
        )


def parse_frameworks_param(raw: str | None) -> frozenset[str] | None:
    """Parse JSON array, comma-list, or empty = all rules."""
    if raw is None:
        return None
    s = raw.strip()
    if not s:
        return None
    try:
        data = json.loads(s)
        if isinstance(data, list):
            return frozenset(str(x).strip() for x in data if str(x).strip())
        if isinstance(data, str) and data.strip():
            return frozenset({data.strip()})
    except json.JSONDecodeError:
        pass
    return frozenset(x.strip() for x in s.split(",") if x.strip())


def effective_rule_priority(
    rule: dict[str, Any],
    selected: frozenset[str] | None,
) -> int:
    """Base ``priority`` from the rule, optionally boosted for EO14117 in multi-select.

    When the caller selected **more than one** framework and **EO14117** is among
    them, rules whose ``frameworks`` list includes ``EO14117`` get a small increase.
    This only affects **suppression** ordering in ``app.classifier`` (higher
    effective priority runs first), not which rules match.
    """
    p = int(rule.get("priority", 0))
    if not selected or len(selected) < 2:
        return p
    if FW_EO14117 not in selected:
        return p
    fws = rule.get("frameworks")
    if fws and FW_EO14117 in fws:
        return p + EO14117_PRIORITY_BOOST_WHEN_MULTI
    return p


def filter_rules_by_frameworks(
    rules: list[dict[str, Any]],
    selected: frozenset[str] | None,
) -> list[dict[str, Any]]:
    """Keep rules whose ``frameworks`` intersects (selected | UNIVERSAL).

    When ``selected`` is set, rules with an empty ``frameworks`` list are dropped.
    """
    if not selected:
        return rules
    sel = set(selected) | {UNIVERSAL}
    out: list[dict[str, Any]] = []
    for r in rules:
        raw = r.get("frameworks")
        fw = set(raw) if raw is not None else set()
        if not fw:
            continue
        if fw & sel:
            out.append(r)
    return out


def validate_framework_selection(selected: frozenset[str] | None) -> None:
    if not selected:
        return
    bad = set(selected) - SELECTABLE_FRAMEWORK_IDS
    if bad:
        raise ValueError(
            "unknown framework ids: " + ", ".join(sorted(bad)) + ". "
            "Valid: " + ", ".join(sorted(SELECTABLE_FRAMEWORK_IDS))
        )


def applied_frameworks_label(selected: frozenset[str] | None) -> list[str]:
    if not selected:
        return ["all"]
    return sorted(selected)


def _summarize_country_labels_zh(labels: list[str], *, head: int = 5) -> str:
    """Short line for UI: list few names then total count."""
    if not labels:
        return "未列入国家默认值（可按需手动勾选）"
    if len(labels) <= head:
        return "、".join(labels)
    return "、".join(labels[:head]) + f" 等共 {len(labels)} 个国家/地区"


def list_standards_for_api() -> list[dict[str, Any]]:
    """Return registry for GET /api/standards; adds country linkage fields per standard."""
    rows, _ = _load_country_tables()
    country_label_zh: dict[str, str] = {}
    for row in rows:
        cid = row["id"]
        lab = (row.get("label_zh") or "").strip()
        country_label_zh[cid] = lab or cid
    fw_to_countries: dict[str, list[str]] = {}
    for row in rows:
        cid = row["id"]
        for fid in row.get("framework_ids") or []:
            fw_to_countries.setdefault(str(fid), []).append(cid)
    for lst in fw_to_countries.values():
        lst.sort()
    out: list[dict[str, Any]] = []
    for s in STANDARDS_REGISTRY:
        d = dict(s)
        assoc = fw_to_countries.get(s["id"], [])
        d["associated_country_ids"] = assoc
        labels_zh = [country_label_zh.get(x, x) for x in assoc]
        d["associated_country_labels_zh"] = labels_zh
        d["associated_countries_summary_zh"] = _summarize_country_labels_zh(labels_zh)
        out.append(d)
    return out
