from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from app.models import ClassifiedField, FieldDescriptor, RuleMatch

_RULES_JSON = Path(__file__).resolve().parent / "rules" / "default_rules.json"
_MAPPING_JSON = Path(__file__).resolve().parent / "rules" / "level_mapping.json"


def _load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def load_rules(rules_path: Path | None = None) -> list[dict[str, Any]]:
    path = rules_path or _RULES_JSON
    data = _load_json(path)
    rules = data.get("rules") or []
    return sorted(rules, key=lambda r: int(r.get("priority", 0)), reverse=True)


def load_tag_levels(mapping_path: Path | None = None) -> dict[str, int]:
    path = mapping_path or _MAPPING_JSON
    data = _load_json(path)
    tags = data.get("tag_levels") or {}
    return {str(k): int(v) for k, v in tags.items()}


def _compile_patterns(patterns: list[str] | None) -> list[re.Pattern[str]]:
    if not patterns:
        return []
    out: list[re.Pattern[str]] = []
    for p in patterns:
        try:
            out.append(re.compile(p))
        except re.error:
            continue
    return out


def classify_field(
    field: FieldDescriptor,
    rules: list[dict[str, Any]],
    tag_levels: dict[str, int],
) -> ClassifiedField:
    col_text = field.column or ""
    comment_text = field.comment or ""
    table_text = field.table or ""

    tags: set[str] = set()
    matches: list[RuleMatch] = []

    for rule in rules:
        rid = str(rule.get("id", ""))
        rname = str(rule.get("name", rid))
        std = list(rule.get("standard_refs") or [])

        col_ps = _compile_patterns(rule.get("column_patterns"))
        comment_ps = _compile_patterns(rule.get("comment_patterns"))
        table_ps = _compile_patterns(rule.get("table_patterns"))

        matched_on: str | None = None
        if col_ps and any(p.search(col_text) for p in col_ps):
            matched_on = "column"
        elif comment_ps and any(p.search(comment_text) for p in comment_ps):
            matched_on = "comment"
        elif table_ps and any(p.search(table_text) for p in table_ps):
            matched_on = "table"

        if matched_on:
            for t in rule.get("tags") or []:
                tags.add(str(t))
            matches.append(
                RuleMatch(
                    rule_id=rid,
                    rule_name=rname,
                    matched_on=matched_on,
                    standard_refs=[str(x) for x in std],
                )
            )

    levels = [tag_levels[t] for t in tags if t in tag_levels]
    level = max(levels) if levels else 1

    rationale_parts = [f"命中 {len(matches)} 条规则"] if matches else ["未命中规则，默认 1 级"]
    if tags:
        rationale_parts.append("标签: " + ", ".join(sorted(tags)))
    rationale = "；".join(rationale_parts)

    return ClassifiedField(
        field=field,
        level=level,
        tags=sorted(tags),
        matches=matches,
        rationale=rationale,
    )


def classify_fields(
    fields: list[FieldDescriptor],
    rules_path: Path | None = None,
    mapping_path: Path | None = None,
) -> tuple[list[ClassifiedField], dict[str, int]]:
    rules = load_rules(rules_path)
    tag_levels = load_tag_levels(mapping_path)
    classified = [classify_field(f, rules, tag_levels) for f in fields]
    summary: dict[str, int] = {}
    for c in classified:
        k = str(c.level)
        summary[k] = summary.get(k, 0) + 1
    return classified, summary
