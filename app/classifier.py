"""Field classification from metadata only (column / comment / table).



Judgment order (per field):

1. Each rule is evaluated independently. Within one rule, the first match among

   column -> comment -> table wins (column has precedence over comment over table).

2. Rules are listed in JSON with a numeric ``priority``; higher runs first only

   for *suppression* (step 3). All rules still contribute matches unless tags are

   removed by suppression.

3. After all rules run, ``suppresses`` on rules is applied in descending ``priority``

   among *matched* rules only: a higher-priority match may drop tags listed in

   ``suppresses`` (e.g. drop generic ``identifier_technical`` when a passport rule

   matched). Final level = max of remaining tag levels.

4. No cell values, no cross-row context, no ML — only strings on this field row.

"""

from __future__ import annotations



import json

import re

from pathlib import Path

from typing import Any



from app.frameworks import enrich_rules_frameworks, filter_rules_by_frameworks
from app.models import ClassifiedField, DataCategory, FieldDescriptor, RuleMatch



_RULES_JSON = Path(__file__).resolve().parent / "rules" / "default_rules.json"

_MAPPING_JSON = Path(__file__).resolve().parent / "rules" / "level_mapping.json"

_CATEGORY_JSON = Path(__file__).resolve().parent / "rules" / "tag_categories.json"



_NO_MATCH_HINT = (

    "\u672a\u547d\u4e2d\u4efb\u4f55\u89c4\u5219\uff1a\u5f53\u524d\u4ec5\u6839\u636e"

    "\u5217\u540d\u3001\u6ce8\u91ca\u3001\u8868\u540d\u4e2d\u7684\u6b63\u5219/\u5173"

    "\u952e\u8bcd\u5339\u914d\uff1b\u6ce8\u91ca\u4e3a\u7a7a\u6216\u5b57\u6bb5\u7f29"

    "\u5199\u672a\u6536\u5f55\u65f6\u5e38\u89c1\u3002\u53ef\u5728 app/rules/"

    "default_rules.json \u8865\u5145\u89c4\u5219\u6216\u586b\u5199\u5143\u6570\u636e"

    "\u6ce8\u91ca\u3002"

)





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


def load_tag_labels_zh(mapping_path: Path | None = None) -> dict[str, str]:
    """tag id -> Chinese label; keys with empty/whitespace values are omitted."""

    path = mapping_path or _MAPPING_JSON

    data = _load_json(path)

    raw = data.get("tag_labels_zh") or {}

    out: dict[str, str] = {}

    for k, v in raw.items():

        s = str(v).strip()

        if s:

            out[str(k)] = s

    return out


def tags_zh_for_tags(sorted_tags: list[str], tag_labels_zh: dict[str, str]) -> list[str]:
    """Parallel to ``sorted_tags``: Chinese label or empty string if unmapped."""

    return [tag_labels_zh.get(t, "") for t in sorted_tags]


def _zh_join_sorted(tag_ids: set[str], tag_labels_zh: dict[str, str]) -> str | None:

    parts = [tag_labels_zh[t] for t in sorted(tag_ids) if t in tag_labels_zh]

    return ", ".join(parts) if parts else None


def load_tag_category_maps(
    category_path: Path | None = None,
) -> tuple[dict[str, str], dict[str, str]]:
    """Return (tag -> category id, category id -> Chinese label)."""

    path = category_path or _CATEGORY_JSON

    data = _load_json(path)

    raw_cats = data.get("categories") or {}

    raw_map = data.get("tag_to_category") or {}

    labels = {str(k): str(v) for k, v in raw_cats.items()}

    tag_to = {str(k): str(v) for k, v in raw_map.items()}

    return tag_to, labels


def resolve_categories(
    tags: list[str],
    tag_to_category: dict[str, str],
    category_labels: dict[str, str],
) -> list[DataCategory]:
    """Map rule tags to high-level data categories; empty tags -> general_public."""

    seen: list[str] = []

    for t in tags:

        cid = tag_to_category.get(t)

        if cid and cid not in seen:

            seen.append(cid)

    if not seen:

        gid = "general_public"

        return [
            DataCategory(
                id=gid,
                label_zh=category_labels.get(gid, "公开与一般数据"),
            )
        ]

    out: list[DataCategory] = []

    for cid in sorted(seen):

        out.append(
            DataCategory(
                id=cid,
                label_zh=category_labels.get(cid, cid),
            )
        )

    return out





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





def _keywords_match(keywords: list[str] | None, text: str) -> bool:

    if not keywords or not text:

        return False

    t = text.lower()

    for raw in keywords:

        if not raw:

            continue

        k = raw.strip().lower()

        if not k:

            continue

        if len(k) <= 3 and k.isascii() and k.isalnum():

            try:

                if re.search(rf"(?<![a-z0-9_]){re.escape(k)}(?![a-z0-9_])", t):

                    return True

            except re.error:

                pass

        else:

            if k in t:

                return True

    return False





def _rule_match_on(

    rule: dict[str, Any],

    col_text: str,

    comment_text: str,

    table_text: str,

) -> str | None:

    col_ps = _compile_patterns(rule.get("column_patterns"))

    comment_ps = _compile_patterns(rule.get("comment_patterns"))

    table_ps = _compile_patterns(rule.get("table_patterns"))

    col_kw = rule.get("column_keywords") or []

    comment_kw = rule.get("comment_keywords") or []

    table_kw = rule.get("table_keywords") or []



    col_hit = (col_ps and any(p.search(col_text) for p in col_ps)) or _keywords_match(

        col_kw, col_text

    )

    comment_hit = (comment_ps and any(p.search(comment_text) for p in comment_ps)) or _keywords_match(

        comment_kw, comment_text

    )

    table_hit = (table_ps and any(p.search(table_text) for p in table_ps)) or _keywords_match(

        table_kw, table_text

    )



    if rule.get("require_table_and_field"):

        if not table_hit:

            return None

        if not (col_hit or comment_hit):

            return None

        if col_hit:

            return "column"

        return "comment"



    if col_hit:

        return "column"

    if comment_hit:

        return "comment"

    if table_hit:

        return "table"

    return None





def _apply_suppressions(

    matches: list[RuleMatch],

    tags: set[str],

    rules_by_id: dict[str, dict[str, Any]],

) -> tuple[set[str], set[str]]:

    """Drop tags listed in ``suppresses`` using matched rules' priority (high first)."""

    suppressed: set[str] = set()

    matched_ids = {m.rule_id for m in matches}

    ordered = sorted(

        matched_ids,

        key=lambda rid: int(rules_by_id.get(rid, {}).get("priority", 0)),

        reverse=True,

    )

    for rid in ordered:

        for st in rules_by_id.get(rid, {}).get("suppresses") or []:

            if st in tags:

                suppressed.add(st)

                tags.discard(st)

    return tags, suppressed





def classify_field(

    field: FieldDescriptor,

    rules: list[dict[str, Any]],

    tag_levels: dict[str, int],

    tag_to_category: dict[str, str],

    category_labels: dict[str, str],

    tag_labels_zh: dict[str, str],

) -> ClassifiedField:

    col_text = field.column or ""

    comment_text = field.comment or ""

    table_text = field.table or ""



    rules_by_id = {str(r.get("id", "")): r for r in rules if r.get("id")}



    tags: set[str] = set()

    matches: list[RuleMatch] = []



    for rule in rules:

        rid = str(rule.get("id", ""))

        rname = str(rule.get("name", rid))

        std = list(rule.get("standard_refs") or [])



        matched_on = _rule_match_on(rule, col_text, comment_text, table_text)



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



    tags, suppressed = _apply_suppressions(matches, tags, rules_by_id)



    levels = [tag_levels[t] for t in tags if t in tag_levels]

    level = max(levels) if levels else 1



    if matches:

        rationale_parts = [f"\u547d\u4e2d {len(matches)} \u6761\u89c4\u5219"]

    else:

        rationale_parts = [

            f"\u9ed8\u8ba4 1 \u7ea7\uff08\u516c\u5f00/\u4e00\u822c\uff09\u3002{_NO_MATCH_HINT}"

        ]

    tag_list = sorted(tags)

    tags_zh = tags_zh_for_tags(tag_list, tag_labels_zh)

    zh_for_rationale = _zh_join_sorted(tags, tag_labels_zh)

    if zh_for_rationale:

        rationale_parts.append("\u6807\u7b7e: " + zh_for_rationale)

    sup_zh = _zh_join_sorted(suppressed, tag_labels_zh)

    if sup_zh:

        rationale_parts.append(

            "\u6309\u4f18\u5148\u7ea7\u5df2\u79fb\u9664\u6807\u7b7e: " + sup_zh

        )

    rationale = "\uff1b".join(rationale_parts)

    categories = resolve_categories(tag_list, tag_to_category, category_labels)

    return ClassifiedField(

        field=field,

        level=level,

        tags=tag_list,

        tags_zh=tags_zh,

        categories=categories,

        matches=matches,

        rationale=rationale,

    )





def classify_fields(

    fields: list[FieldDescriptor],

    rules_path: Path | None = None,

    mapping_path: Path | None = None,

    category_path: Path | None = None,

    frameworks: frozenset[str] | None = None,

) -> tuple[
    list[ClassifiedField],
    dict[str, int],
    dict[str, int],
    dict[str, str],
    dict[str, str],
]:

    rules = load_rules(rules_path)

    enrich_rules_frameworks(rules)

    rules = filter_rules_by_frameworks(rules, frameworks)

    tag_levels = load_tag_levels(mapping_path)

    tag_labels_zh = load_tag_labels_zh(mapping_path)

    tag_to_category, category_labels = load_tag_category_maps(category_path)

    classified = [
        classify_field(
            f,
            rules,
            tag_levels,
            tag_to_category,
            category_labels,
            tag_labels_zh,
        )
        for f in fields
    ]

    summary: dict[str, int] = {}

    category_summary: dict[str, int] = {}

    for c in classified:

        k = str(c.level)

        summary[k] = summary.get(k, 0) + 1

        for cat in c.categories:

            category_summary[cat.id] = category_summary.get(cat.id, 0) + 1

    return classified, summary, category_summary, category_labels, tag_labels_zh


def rollup_category_counts(classified: list[ClassifiedField]) -> dict[str, int]:
    """Recompute category histogram after tags change (e.g. AI pass)."""

    category_summary: dict[str, int] = {}

    for c in classified:

        for cat in c.categories:

            category_summary[cat.id] = category_summary.get(cat.id, 0) + 1

    return category_summary

