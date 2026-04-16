"""Selectable compliance frameworks for rule filtering."""
from __future__ import annotations

import json
from typing import Any


# Canonical IDs (match UI / API)
UNIVERSAL = "UNIVERSAL"  # always on when any framework is selected; technical baseline rules
FW_35273 = "35273"
FW_GDPR = "GDPR"
FW_43697 = "43697"  # GB/T 43697-2024 数据安全技术 数据分类分级规则
FW_EO14117 = "EO14117"  # US EO 14117 bulk sensitive / countries of concern context

STANDARDS_REGISTRY: list[dict[str, str]] = [
    {
        "id": FW_35273,
        "code": "GB/T 35273-2020",
        "title_zh": "\u4fe1\u606f\u5b89\u5168\u6280\u672f \u4e2a\u4eba\u4fe1\u606f\u5b89\u5168\u89c4\u8303",
        "title_en": "Personal information security specification",
    },
    {
        "id": FW_GDPR,
        "code": "GDPR",
        "title_zh": "\u6b27\u76df\u901a\u7528\u6570\u636e\u4fdd\u62a4\u6761\u4f8b",
        "title_en": "EU General Data Protection Regulation",
    },
    {
        "id": FW_43697,
        "code": "GB/T 43697-2024",
        "title_zh": "\u6570\u636e\u5b89\u5168\u6280\u672f \u6570\u636e\u5206\u7c7b\u5206\u7ea7\u89c4\u5219",
        "title_en": "Data security technology \u2014 Rules for data classification and grading",
        "reference_zh": "https://baike.baidu.com/item/%E6%95%B0%E6%8D%AE%E5%AE%89%E5%85%A8%E6%8A%80%E6%9C%AF%E6%95%B0%E6%8D%AE%E5%88%86%E7%B1%BB%E5%88%86%E7%BA%A7%E8%A7%84%E5%88%99/64208400",
    },
    {
        "id": FW_EO14117,
        "code": "EO 14117",
        "title_zh": "\u7f8e\u56fd\u7b2c14117\u53f7\u884c\u653f\u4ee4\uff08\u654f\u611f\u4e2a\u4eba\u6570\u636e / \u5173\u6ce8\u56fd\u8bed\u5883\uff09",
        "title_en": "US Executive Order 14117 (sensitive data / countries of concern)",
    },
]

SELECTABLE_FRAMEWORK_IDS: frozenset[str] = frozenset(s["id"] for s in STANDARDS_REGISTRY)

FRAMEWORKS_BY_RULE_ID: dict[str, list[str]] = {
    # 43697: 分类分级规则 — 与本工具“按元数据打标签/级别”直接对齐；规则集与 35273 并列为常见国标场景。
    "pii_id_card": [FW_35273, FW_43697, FW_GDPR, FW_EO14117],
    "passport_travel": [FW_35273, FW_43697, FW_GDPR, FW_EO14117],
    "pii_phone": [FW_35273, FW_43697, FW_GDPR, FW_EO14117],
    "pii_email": [FW_35273, FW_43697, FW_GDPR, FW_EO14117],
    "pii_legal_name": [FW_35273, FW_43697, FW_GDPR, FW_EO14117],
    "pii_login_alias": [FW_35273, FW_43697, FW_GDPR],
    "pii_bank": [FW_35273, FW_43697, FW_GDPR, FW_EO14117],
    "health": [FW_35273, FW_43697, FW_GDPR, FW_EO14117],
    "biometric": [FW_35273, FW_43697, FW_GDPR, FW_EO14117],
    "religion_belief": [FW_35273, FW_43697, FW_GDPR, FW_EO14117],
    "political_opinion": [FW_35273, FW_43697, FW_GDPR, FW_EO14117],
    "union_membership": [FW_35273, FW_43697, FW_GDPR, FW_EO14117],
    "sexual_orientation": [FW_35273, FW_43697, FW_GDPR, FW_EO14117],
    "genetic_data": [FW_35273, FW_43697, FW_GDPR, FW_EO14117],
    "criminal_justice": [FW_35273, FW_43697, FW_GDPR, FW_EO14117],
    "location": [FW_35273, FW_43697, FW_GDPR, FW_EO14117],
    "vehicle_plate": [FW_35273, FW_43697, FW_GDPR, FW_EO14117],
    "tax_social": [FW_35273, FW_43697, FW_GDPR, FW_EO14117],
    "ad_tracking_id": [FW_35273, FW_43697, FW_GDPR, FW_EO14117],
    "child": [FW_35273, FW_43697, FW_GDPR, FW_EO14117],
    "password_secret": [UNIVERSAL, FW_35273, FW_43697, FW_GDPR, FW_EO14117],
    "cookie_session": [UNIVERSAL, FW_35273, FW_43697, FW_GDPR, FW_EO14117],
    "internal_only": [UNIVERSAL, FW_35273, FW_43697],
    "address_postal": [FW_35273, FW_43697, FW_GDPR, FW_EO14117],
    "birth_gender": [FW_35273, FW_43697, FW_GDPR, FW_EO14117],
    "internal_user_key": [UNIVERSAL, FW_43697],
    "party_customer_id": [FW_35273, FW_43697, FW_GDPR, FW_EO14117],
    "technical_id": [UNIVERSAL, FW_43697],
    "network_device": [FW_35273, FW_43697, FW_GDPR, FW_EO14117],
    "education_job": [FW_35273, FW_43697, FW_GDPR],
    "photo_avatar": [FW_35273, FW_43697, FW_GDPR, FW_EO14117],
    "social_account": [FW_35273, FW_43697, FW_GDPR],
}


def enrich_rules_frameworks(rules: list[dict[str, Any]]) -> None:
    """Mutate rules in place: set ``frameworks`` if the key is absent.

    If ``frameworks`` is present (including ``[]``), it is left unchanged: an
    explicit empty list means the rule never applies when standards are selected.
    """
    for r in rules:
        if "frameworks" in r:
            continue
        rid = str(r.get("id", ""))
        r["frameworks"] = list(
            FRAMEWORKS_BY_RULE_ID.get(
                rid,
                [UNIVERSAL, FW_35273, FW_43697, FW_GDPR],
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


def list_standards_for_api() -> list[dict[str, str]]:
    """Return registry for GET /api/standards."""
    return list(STANDARDS_REGISTRY)
