# -*- coding: utf-8 -*-
"""Regenerate app/rules/default_rules.json and level_mapping.json (UTF-8). Run: python tools/build_rules.py"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Chinese via unicode escapes so this file stays encoding-safe on all editors.
U = str  # readability alias; use \u in literals below


def rules() -> list[dict]:
    return [
        {
            "id": "pii_id_card",
            "name": "national_id",
            "column_patterns": [
                r"(?i).*(id_card|idcard|identity_card|cert_no|certificate_no|shenfen|citizen_id).*",
                r"(?i).*" + "\u8eab\u4efd\u8bc1" + r".*",
            ],
            "comment_patterns": ["\u8eab\u4efd\u8bc1", r"(?i)id.?card"],
            "tags": ["personal_identifier", "sensitive_cn", "gov_id"],
            "standard_refs": ["GB/T 35273 sensitive personal info", "PIPL"],
            "suppresses": ["identifier_technical"],
            "priority": 100,
        },
        {
            "id": "passport_travel",
            "name": "passport_travel_permit",
            "column_patterns": [
                r"(?i).*(passport|travel_doc|travel_permit|hk_macau|hk_macao|tw_permit|permanent_residence|pr_card).*",
                r"(?i).*" + "\u62a4\u7167" + r".*",
                r"(?i).*" + "\u6e2f\u6fb3" + r".*",
                r"(?i).*" + "\u53f0\u80de" + r".*",
                r"(?i).*" + "\u6c38\u5c45" + r".*",
                r"(?i).*" + "\u901a\u884c\u8bc1" + r".*",
            ],
            "comment_keywords": ["\u62a4\u7167", "\u6e2f\u6fb3", "\u53f0\u80ce", "\u6c38\u5c45"],
            "tags": ["personal_identifier", "sensitive_cn", "gov_id"],
            "standard_refs": ["GB/T 35273", "PIPL", "Travel document"],
            "suppresses": ["identifier_technical"],
            "priority": 99,
        },
        {
            "id": "pii_phone",
            "name": "phone",
            "column_patterns": [
                r"(?i).*(phone|mobile|cell|msisdn|tel_no|telephone|fax_no).*",
                r"(?i).*" + "\u624b\u673a" + r".*",
                r"(?i).*" + "\u7535\u8bdd" + r".*",
            ],
            "comment_patterns": ["\u624b\u673a", "\u7535\u8bdd"],
            "tags": ["personal_identifier", "contact"],
            "standard_refs": ["GB/T 35273", "GDPR personal data"],
            "priority": 90,
        },
        {
            "id": "pii_email",
            "name": "email",
            "column_patterns": [
                r"(?i).*(email|e-mail|e_mail|email_addr|mail_addr|mailbox).*",
                r"(?i).*" + "\u90ae\u7bb1" + r".*",
            ],
            "comment_patterns": ["\u90ae\u7bb1", "\u90ae\u4ef6"],
            "tags": ["personal_identifier", "contact"],
            "standard_refs": ["GDPR personal data"],
            "priority": 85,
        },
        {
            "id": "pii_legal_name",
            "name": "legal_or_display_name",
            "column_patterns": [
                r"(?i).*(full_name|real_name|cust_name|customer_name|legal_name|given_name|family_name|surname|forename).*",
                r"(?i)^(name)$",
                r"(?i).*" + "\u59d3\u540d" + r".*",
                r"(?i).*" + "\u66fe\u7528\u540d" + r".*",
            ],
            "comment_patterns": ["\u59d3\u540d", "\u771f\u5b9e\u59d3\u540d"],
            "tags": ["personal_identifier"],
            "standard_refs": ["GB/T 35273", "GDPR personal data"],
            "priority": 81,
        },
        {
            "id": "pii_login_alias",
            "name": "login_or_nickname",
            "column_patterns": [
                r"(?i).*(user_name|username|login_name|login_id|nick_name|nickname|screen_name|account_name).*",
                r"(?i)^(username|login|nickname)$",
                r"(?i).*" + "\u6635\u79f0" + r".*",
                r"(?i).*" + "\u767b\u5f55\u540d" + r".*",
            ],
            "comment_keywords": ["\u6635\u79f0", "\u8d26\u53f7\u540d", "\u7528\u6237\u540d"],
            "tags": ["login_alias"],
            "standard_refs": ["Often not legal name; assess linkage"],
            "priority": 68,
        },
        {
            "id": "pii_bank",
            "name": "bank_account",
            "column_patterns": [
                r"(?i).*(bank_card|bank_account|account_no|iban|card_no|swift|routing_no).*",
                r"(?i).*" + "\u94f6\u884c\u5361" + r".*",
                r"(?i).*" + "\u8d26\u53f7" + r".*",
            ],
            "comment_patterns": ["\u94f6\u884c\u5361", "\u8d26\u6237"],
            "tags": ["financial", "sensitive_cn"],
            "standard_refs": ["GB/T 35273 sensitive personal info"],
            "suppresses": ["identifier_technical"],
            "priority": 95,
        },
        {
            "id": "health",
            "name": "health_medical",
            "column_patterns": [
                r"(?i).*(diagnos|disease|medical|health_record|patient_id|clinic|hospital|prescription|symptom).*",
                r"(?i).*" + "\u75c5\u5386" + r".*",
                r"(?i).*" + "\u8bca\u65ad" + r".*",
            ],
            "comment_patterns": ["\u75c5\u5386", "\u8bca\u65ad", "\u5065\u5eb7"],
            "table_patterns": [
                r"(?i).*(patient|medical|clinic|hospital|diag|health|emr|his).*",
                r"(?i).*" + "\u75c5\u5386" + r".*",
                r"(?i).*" + "\u8bca\u7597" + r".*",
            ],
            "tags": ["health", "gdpr_special_category"],
            "standard_refs": ["GB/T 35273", "GDPR Art.9"],
            "priority": 95,
        },
        {
            "id": "biometric",
            "name": "biometric",
            "column_patterns": [
                r"(?i).*(face|fingerprint|iris|voiceprint|palmprint|vein_pattern).*",
                r"(?i).*" + "\u6307\u7eb9" + r".*",
                r"(?i).*" + "\u4eba\u8138" + r".*",
            ],
            "tags": ["biometric", "sensitive_cn", "gdpr_special_category"],
            "standard_refs": ["GB/T 35273", "GDPR Art.9"],
            "priority": 95,
        },
        {
            "id": "religion_belief",
            "name": "religion",
            "column_patterns": [
                r"(?i).*(religion|religious|faith|church|mosque|temple).*",
                r"(?i).*" + "\u5b97\u6559" + r".*",
                r"(?i).*" + "\u4fe1\u4ef0" + r".*",
            ],
            "tags": ["sensitive_cn", "gdpr_special_category"],
            "standard_refs": ["GB/T 35273", "GDPR Art.9"],
            "priority": 94,
        },
        {
            "id": "political_opinion",
            "name": "political",
            "column_patterns": [
                r"(?i).*(political|politics|party_affil|vote_preference|election_choice).*",
                r"(?i).*" + "\u653f\u6cbb" + r".*",
                r"(?i).*" + "\u515a\u6d3e" + r".*",
            ],
            "tags": ["sensitive_cn", "gdpr_special_category"],
            "standard_refs": ["GDPR Art.9", "GB/T 35273"],
            "priority": 94,
        },
        {
            "id": "union_membership",
            "name": "trade_union",
            "column_patterns": [
                r"(?i).*(union_member|trade_union|labour_union|labor_union).*",
                r"(?i).*" + "\u5de5\u4f1a" + r".*",
            ],
            "tags": ["sensitive_cn", "gdpr_special_category"],
            "standard_refs": ["GDPR Art.9"],
            "priority": 94,
        },
        {
            "id": "sexual_orientation",
            "name": "sexual_orientation",
            "column_patterns": [
                r"(?i).*(sexual_orientation|lgbt|orientation_gender).*",
                r"(?i).*" + "\u6027\u53d6\u5411" + r".*",
            ],
            "tags": ["sensitive_cn", "gdpr_special_category"],
            "standard_refs": ["GDPR Art.9"],
            "priority": 94,
        },
        {
            "id": "genetic_data",
            "name": "genetic",
            "column_patterns": [
                r"(?i).*(genetic|genome|dna_seq|gene_marker|heredit).*",
                r"(?i).*" + "\u57fa\u56e0" + r".*",
                r"(?i).*" + "\u9057\u4f20" + r".*",
            ],
            "tags": ["sensitive_cn", "gdpr_special_category"],
            "standard_refs": ["GDPR Art.9", "GB/T 35273"],
            "priority": 94,
        },
        {
            "id": "criminal_justice",
            "name": "criminal_justice",
            "column_patterns": [
                r"(?i).*(criminal_record|conviction|felony|misdemeanor|court_case|judgment_no).*",
                r"(?i).*" + "\u524d\u79d1" + r".*",
                r"(?i).*" + "\u72af\u7f6a" + r".*",
                r"(?i).*" + "\u5224\u51b3" + r".*",
            ],
            "tags": ["criminal_justice", "sensitive_cn"],
            "standard_refs": ["High sensitivity; legal basis required"],
            "priority": 94,
        },
        {
            "id": "location",
            "name": "location_track",
            "column_patterns": [
                r"(?i).*(gps|latitude|longitude|lng|lat|geo|location|trajectory).*",
                r"(?i).*" + "\u8f68\u8ff9" + r".*",
                r"(?i).*" + "\u7ecf\u7eac" + r".*",
            ],
            "comment_patterns": ["\u5b9a\u4f4d", "\u8f68\u8ff9"],
            "tags": ["location_trace", "sensitive_cn"],
            "standard_refs": ["GB/T 35273 sensitive personal info"],
            "priority": 90,
        },
        {
            "id": "vehicle_plate",
            "name": "vehicle",
            "column_patterns": [
                r"(?i).*(license_plate|plate_no|vehicle_no|vin|frame_no|car_plate).*",
                r"(?i).*" + "\u8f66\u724c" + r".*",
                r"(?i).*" + "\u8f66\u67b6\u53f7" + r".*",
            ],
            "tags": ["vehicle_plate", "personal_identifier"],
            "standard_refs": ["Often relatable to person"],
            "priority": 79,
        },
        {
            "id": "tax_social",
            "name": "tax_social_insurance",
            "column_patterns": [
                r"(?i).*(tax_id|tin|ssn|social_sec|social_security|pension_no|provident|housing_fund).*",
                r"(?i).*" + "\u7a0e\u53f7" + r".*",
                r"(?i).*" + "\u793e\u4fdd" + r".*",
                r"(?i).*" + "\u516c\u79ef\u91d1" + r".*",
            ],
            "tags": ["tax_personal", "sensitive_cn", "personal_identifier"],
            "standard_refs": ["GB/T 35273", "PIPL"],
            "suppresses": ["identifier_technical"],
            "priority": 91,
        },
        {
            "id": "ad_tracking_id",
            "name": "advertising_device_id",
            "column_patterns": [
                r"(?i).*(idfa|gaid|oaid|aaid|android_id|idfv|advertising_id|ad_id|muid).*",
                r"(?i).*" + "\u5e7f\u544a\u6807\u8bc6" + r".*",
            ],
            "tags": ["ad_identifier", "device_network", "personal_identifier"],
            "standard_refs": ["GDPR ePrivacy / personal data context"],
            "priority": 75,
        },
        {
            "id": "child",
            "name": "minor",
            "column_patterns": [
                r"(?i).*(child|minor|under_14|juvenile).*",
                r"(?i).*" + "\u672a\u6210\u5e74" + r".*",
            ],
            "comment_patterns": ["\u672a\u6210\u5e74"],
            "tags": ["child_data", "sensitive_cn"],
            "standard_refs": ["GB/T 35273"],
            "priority": 92,
        },
        {
            "id": "password_secret",
            "name": "credential",
            "column_patterns": [
                r"(?i).*(password|passwd|pwd|secret|api_key|token|private_key|bearer|refresh_token).*",
                r"(?i).*" + "\u5bc6\u7801" + r".*",
                r"(?i).*" + "\u5bc6\u94a5" + r".*",
            ],
            "tags": ["credential", "security"],
            "standard_refs": ["internal security baseline"],
            "priority": 88,
        },
        {
            "id": "cookie_session",
            "name": "cookie_session",
            "column_patterns": [
                r"(?i).*(cookie|session_key|session_token|csrf|xsrf|jwt_secret).*",
                r"(?i).*" + "Cookie" + r".*",
            ],
            "tags": ["credential", "security"],
            "standard_refs": ["Session / tracking context"],
            "priority": 74,
        },
        {
            "id": "internal_only",
            "name": "internal_business",
            "column_patterns": [
                r"(?i).*(internal|confidential|classified).*",
                r"(?i).*" + "\u85aa\u8d44" + r".*",
                r"(?i).*" + "\u85aa\u916c" + r".*",
                r"(?i).*" + "\u7ee9\u6548" + r".*",
            ],
            "comment_patterns": ["\u5185\u90e8", "\u673a\u5bc6"],
            "tags": ["internal_business"],
            "standard_refs": ["organizational policy TBD"],
            "priority": 70,
        },
        {
            "id": "address_postal",
            "name": "address_postal",
            "column_patterns": [
                r"(?i).*(address|postal|zipcode|zip_code|postcode|mailing|street|road|district|province|city_code).*",
                r"(?i)^mail_addr$",
                r"(?i).*" + "\u5730\u5740" + r".*",
                r"(?i).*" + "\u90ae\u7f16" + r".*",
            ],
            "comment_keywords": ["\u5730\u5740", "\u90ae\u7f16", "address"],
            "tags": ["personal_identifier", "contact"],
            "standard_refs": ["GB/T 35273", "GDPR personal data"],
            "priority": 78,
        },
        {
            "id": "birth_gender",
            "name": "birth_gender",
            "column_patterns": [
                r"(?i).*(birth|born|dob|date_of_birth|age|gender|sex).*",
                r"(?i).*" + "\u51fa\u751f" + r".*",
                r"(?i).*" + "\u751f\u65e5" + r".*",
                r"(?i).*" + "\u5e74\u9f84" + r".*",
                r"(?i).*" + "\u6027\u522b" + r".*",
            ],
            "comment_keywords": ["\u51fa\u751f", "\u751f\u65e5", "\u6027\u522b"],
            "tags": ["personal_identifier"],
            "standard_refs": ["GB/T 35273", "GDPR personal data"],
            "priority": 77,
        },
        {
            "id": "internal_user_key",
            "name": "internal_user_key",
            "column_patterns": [
                r"(?i)^user_id$",
                r"(?i)^usr_id$",
                r"(?i)^system_user_id$",
                r"(?i)^sys_user_id$",
            ],
            "comment_keywords": [
                "\u7528\u6237ID",
                "\u5185\u90e8\u7528\u6237",
                "\u7cfb\u7edf\u7528\u6237",
                "\u5185\u90e8\u8d26\u53f7",
            ],
            "tags": ["internal_surrogate_id"],
            "standard_refs": ["Internal surrogate key"],
            "suppresses": ["identifier_technical"],
            "priority": 63,
        },
        {
            "id": "party_customer_id",
            "name": "party_customer_id",
            "column_patterns": [
                r"(?i)^(cust|customer|client|consumer|buyer|subscriber)_?(id|no|code)$",
                r"(?i)^(member|mbr|vip)_?(id|no)$",
            ],
            "tags": ["personal_identifier", "contact"],
            "standard_refs": ["GB/T 35273", "GDPR personal data"],
            "suppresses": ["identifier_technical"],
            "priority": 62,
        },
        {
            "id": "technical_id",
            "name": "technical_id",
            "column_patterns": [
                r"(?i)^(?:id|pk|uuid|guid)$",
                r"(?i)^(?!user_id$)(?!usr_id$).+_id$",
                r"(?i).+_no$",
                r"(?i).+_code$",
                r"(?i)^(order|ord|txn|transaction|payment|invoice|sku|item|line|batch|seq|serial)_?(id|no|code)$",
            ],
            "column_keywords": ["uuid", "guid"],
            "tags": ["identifier_technical"],
            "standard_refs": ["Technical key; context-dependent"],
            "priority": 55,
        },
        {
            "id": "network_device",
            "name": "network_device",
            "column_patterns": [
                r"(?i).*(ip_addr|ip_address|client_ip|remote_ip|mac_addr|imei|device_id|terminal_id).*",
                r"(?i).*" + "\u624b\u673a\u4e32\u7801" + r".*",
            ],
            "column_keywords": ["imei", "mac"],
            "tags": ["device_network", "personal_identifier"],
            "standard_refs": ["GB/T 35273", "GDPR personal data"],
            "priority": 76,
        },
        {
            "id": "education_job",
            "name": "education_job",
            "column_patterns": [
                r"(?i).*(education|degree|school|university|employer|occupation|title|position|resume).*",
                r"(?i).*" + "\u5b66\u5386" + r".*",
                r"(?i).*" + "\u5c31\u8bfb" + r".*",
                r"(?i).*" + "\u804c\u4f4d" + r".*",
                r"(?i).*" + "\u516c\u53f8" + r".*",
            ],
            "tags": ["personal_identifier"],
            "standard_refs": ["GB/T 35273", "GDPR personal data"],
            "priority": 72,
        },
        {
            "id": "photo_avatar",
            "name": "photo_avatar",
            "column_patterns": [
                r"(?i).*(photo|picture|pic|avatar|headimg|portrait|selfie).*",
                r"(?i).*" + "\u5934\u50cf" + r".*",
                r"(?i).*" + "\u7167\u7247" + r".*",
            ],
            "tags": ["biometric", "sensitive_cn", "gdpr_special_category"],
            "standard_refs": ["GB/T 35273", "GDPR Art.9 if biometric"],
            "priority": 93,
        },
        {
            "id": "social_account",
            "name": "social_account",
            "column_patterns": [
                r"(?i).*(wechat|weixin|openid|unionid|qq|alipay|weibo|dingtalk).*",
                r"(?i).*" + "\u5fae\u4fe1" + r".*",
                r"(?i).*" + "\u652f\u4ed8\u5b9d" + r".*",
            ],
            "tags": ["personal_identifier", "contact"],
            "standard_refs": ["GB/T 35273", "GDPR personal data"],
            "priority": 82,
        },
    ]


def level_mapping() -> dict:
    return {
        "tag_levels": {
            "public": 1,
            "login_alias": 2,
            "internal_business": 2,
            "internal_surrogate_id": 2,
            "identifier_technical": 2,
            "contact": 3,
            "personal_identifier": 3,
            "device_network": 3,
            "vehicle_plate": 3,
            "ad_identifier": 3,
            "financial": 4,
            "health": 4,
            "biometric": 4,
            "location_trace": 4,
            "child_data": 4,
            "sensitive_cn": 4,
            "gdpr_special_category": 4,
            "gov_id": 4,
            "credential": 4,
            "security": 4,
            "tax_personal": 4,
            "criminal_justice": 4,
            "important_data_placeholder": 5,
        },
        "_comment": "Levels are organizational defaults; legal final say required.",
    }


def main() -> None:
    rlist = rules()
    (ROOT / "app" / "rules" / "default_rules.json").write_text(
        json.dumps({"rules": rlist}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    lm = level_mapping()
    if "_comment" in lm:
        lm_out = {k: v for k, v in lm.items() if not k.startswith("_")}
    else:
        lm_out = lm
    (ROOT / "app" / "rules" / "level_mapping.json").write_text(
        json.dumps(lm_out, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print("Wrote default_rules.json (%d rules) and level_mapping.json" % len(rlist))


if __name__ == "__main__":
    main()
