from __future__ import annotations

import asyncio
import json
import os
import re
from collections.abc import Awaitable, Callable
from typing import Any

import httpx

from app.classifier import (
    load_tag_category_maps,
    load_tag_labels_zh,
    resolve_categories,
    tags_zh_for_tags,
)
from app.models import AIEnhancementInfo, ClassifiedField
from app.settings import AISettings, get_ai_settings


def _allowed_tags(tag_levels: dict[str, int]) -> list[str]:
    return sorted(tag_levels.keys())


def _clamp_level(n: int) -> int:
    return max(1, min(5, int(n)))


def _level_from_tags(tags: list[str], tag_levels: dict[str, int]) -> int:
    levels = [tag_levels[t] for t in tags if t in tag_levels]
    return max(levels) if levels else 1


def _build_system_prompt(allowed: list[str]) -> str:
    tags_csv = ", ".join(allowed)
    return (
        "You refine data-field classification for compliance inventory. "
        "Input is RULE ENGINE output on metadata only (DB/table/column names, types, comments). "
        "No row values are provided. "
        "Policy: minimize FALSE POSITIVES. Keep baseline level when ambiguous. "
        "Downgrade when rules look too aggressive for generic/technical fields. "
        "Upgrade only with clear personal/sensitive meaning in name or comment. "
        f"Allowed tags (subset only): {tags_csv}. "
        'Respond with JSON object {"items": [...] } only, no markdown. '
        'Each item: {"i": batch_index, "level": 1-5, "tags": [...], '
        '"note": short Chinese rationale, "review_suggested": bool}. '
        "review_suggested=true when you materially disagree with baseline or want human spot-check."
    )


def _parse_ai_json(text: str) -> dict[str, Any]:
    text = text.strip()
    m = re.search(r"\{[\s\S]*\}\s*\Z", text)
    if m:
        text = m.group(0)
    return json.loads(text)


def _ai_payload_item(
    batch_index: int, c: ClassifiedField, settings: AISettings
) -> dict[str, Any]:
    f = c.field
    return {
        "i": batch_index,
        "database": (f.database or "")[:120],
        "schema": (f.schema_name or "")[:120],
        "table": (f.table or "")[:120],
        "column": (f.column or "")[:120],
        "data_type": (f.data_type or "")[:80],
        "comment": (f.comment or "")[: settings.max_comment_len],
        "rule_level": c.level,
        "rule_tags": c.tags[:40],
        "rule_rationale": (c.rationale or "")[: settings.max_rationale_len],
        "matched_rules": [m.rule_id for m in c.matches[:20]],
    }


def _user_message_for_batch(batch: list[ClassifiedField], settings: AISettings) -> str:
    payload_items = [_ai_payload_item(j, batch[j], settings) for j in range(len(batch))]
    return json.dumps({"items": payload_items}, ensure_ascii=False)


def _split_classified_into_batches(
    classified: list[ClassifiedField], settings: AISettings
) -> list[list[ClassifiedField]]:
    """Limit each request by field count and UTF-8 JSON size (avoids gateway / client errors)."""
    batches: list[list[ClassifiedField]] = []
    batch: list[ClassifiedField] = []
    for c in classified:
        trial = batch + [c]
        msg = _user_message_for_batch(trial, settings)
        size_b = len(msg.encode("utf-8"))
        if batch and (len(trial) > settings.batch_size or size_b > settings.max_request_bytes):
            batches.append(batch)
            batch = [c]
        else:
            batch = trial
    if batch:
        batches.append(batch)
    return batches


def _openai_compatible_url(settings: AISettings) -> str:
    return f"{settings.base_url}/chat/completions"


def _anthropic_url(settings: AISettings) -> str:
    return f"{settings.base_url}/messages"


def _extract_openai_content(data: dict[str, Any]) -> str:
    return (data.get("choices") or [{}])[0].get("message", {}).get("content") or ""


def _extract_anthropic_content(data: dict[str, Any]) -> str:
    parts: list[str] = []
    for block in data.get("content") or []:
        if isinstance(block, dict) and block.get("type") == "text":
            parts.append(str(block.get("text") or ""))
    return "".join(parts)


async def _call_ai_batch(
    client: httpx.AsyncClient,
    settings: AISettings,
    system: str,
    user_msg: str,
) -> str:
    if settings.provider == "anthropic":
        body: dict[str, Any] = {
            "model": settings.model,
            "max_tokens": 8192,
            "system": system,
            "messages": [{"role": "user", "content": user_msg}],
        }
        headers = {
            "x-api-key": settings.api_key,
            "anthropic-version": settings.anthropic_version,
            "Content-Type": "application/json",
        }
        r = await client.post(_anthropic_url(settings), headers=headers, json=body)
        r.raise_for_status()
        return _extract_anthropic_content(r.json())

    body = {
        "model": settings.model,
        "temperature": 0.1,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_msg},
        ],
        "response_format": {"type": "json_object"},
    }
    if os.environ.get("DATA_CLASSIFIER_AI_DISABLE_RESPONSE_FORMAT", "").strip().lower() in (
        "1",
        "true",
        "yes",
    ):
        body.pop("response_format", None)
    headers = {
        "Authorization": f"Bearer {settings.api_key}",
        "Content-Type": "application/json",
    }
    r = await client.post(_openai_compatible_url(settings), headers=headers, json=body)
    r.raise_for_status()
    return _extract_openai_content(r.json())


def _merge_ai_batch_result(
    batch: list[ClassifiedField],
    by_i: dict[int, dict[str, Any]],
    settings: AISettings,
    tag_levels: dict[str, int],
    tag_to_category: dict[str, str],
    category_labels: dict[str, str],
    tag_labels_zh: dict[str, str],
) -> list[ClassifiedField]:
    merged: list[ClassifiedField] = []
    for j, c in enumerate(batch):
        base = ClassifiedField.model_validate(c.model_dump())
        it = by_i.get(j)
        if not it:
            merged.append(base)
            continue
        raw_tags = it.get("tags")
        if raw_tags is None:
            tag_out = list(base.tags)
        else:
            ai_tags = [str(t) for t in raw_tags if str(t) in tag_levels]
            tag_out = sorted(set(ai_tags))
        ai_level = _clamp_level(it.get("level", base.level))
        lvl_tags = _level_from_tags(tag_out, tag_levels)
        final_level = max(ai_level, lvl_tags)
        note = it.get("note")
        if note is not None:
            note = str(note)[:1200]
        review = bool(it.get("review_suggested"))
        meta = AIEnhancementInfo(
            model=settings.model,
            baseline_level=base.level,
            baseline_tags=list(base.tags),
            baseline_rationale=base.rationale,
            review_suggested=review,
            note=note,
        )
        rationale_parts = [base.rationale, f"AI({settings.model}): {note or ''}"]
        new_rationale = "；".join(p for p in rationale_parts if p)
        new_categories = resolve_categories(tag_out, tag_to_category, category_labels)
        new_tags_zh = tags_zh_for_tags(tag_out, tag_labels_zh)
        merged.append(
            base.model_copy(
                update={
                    "level": final_level,
                    "tags": tag_out,
                    "tags_zh": new_tags_zh,
                    "categories": new_categories,
                    "rationale": new_rationale,
                    "ai": meta,
                }
            )
        )
    return merged


async def _enhance_one_batch(
    client: httpx.AsyncClient,
    batch: list[ClassifiedField],
    settings: AISettings,
    system: str,
    tag_levels: dict[str, int],
    tag_to_category: dict[str, str],
    category_labels: dict[str, str],
    tag_labels_zh: dict[str, str],
) -> list[ClassifiedField]:
    user_msg = _user_message_for_batch(batch, settings)
    try:
        content = await _call_ai_batch(client, settings, system, user_msg)
        parsed = _parse_ai_json(content)
        items = parsed.get("items")
        if not isinstance(items, list):
            raise ValueError("missing items")
        by_i: dict[int, dict[str, Any]] = {}
        for it in items:
            if isinstance(it, dict) and isinstance(it.get("i"), int):
                by_i[it["i"]] = it
    except Exception:
        return list(batch)
    return _merge_ai_batch_result(
        batch,
        by_i,
        settings,
        tag_levels,
        tag_to_category,
        category_labels,
        tag_labels_zh,
    )


async def enhance_classified_fields(
    classified: list[ClassifiedField],
    tag_levels: dict[str, int],
    progress: Callable[[int, str], Awaitable[None]] | None = None,
) -> list[ClassifiedField]:
    if not classified:
        return classified
    settings = get_ai_settings()
    if not settings.api_key:
        return classified

    tag_to_category, category_labels = load_tag_category_maps()

    tag_labels_zh = load_tag_labels_zh()

    allowed = _allowed_tags(tag_levels)
    system = _build_system_prompt(allowed)

    field_batches = _split_classified_into_batches(classified, settings)
    total_batches = max(1, len(field_batches))

    timeout = httpx.Timeout(
        settings.timeout_sec,
        connect=min(30.0, settings.timeout_sec),
    )
    conc = settings.max_concurrent_batches
    limits = httpx.Limits(
        max_connections=max(10, conc * 4),
        max_keepalive_connections=max(4, conc * 2),
    )
    sem = asyncio.Semaphore(conc)
    progress_lock = asyncio.Lock()
    done_count = 0

    if progress:
        await progress(
            0,
            f"AI：请求模型中（{total_batches} 批，最多 {conc} 路并行）…",
        )

    async with httpx.AsyncClient(timeout=timeout, limits=limits) as client:

        async def run_one(batch: list[ClassifiedField]) -> list[ClassifiedField]:
            nonlocal done_count
            async with sem:
                merged = await _enhance_one_batch(
                    client,
                    batch,
                    settings,
                    system,
                    tag_levels,
                    tag_to_category,
                    category_labels,
                    tag_labels_zh,
                )
            async with progress_lock:
                done_count += 1
                if progress:
                    pct = min(100, int(100 * done_count / total_batches))
                    await progress(
                        pct,
                        f"AI：已完成 {done_count}/{total_batches} 批（并行 {conc} 路）",
                    )
            return merged

        batch_results = await asyncio.gather(*[run_one(b) for b in field_batches])

    out: list[ClassifiedField] = []
    for part in batch_results:
        out.extend(part)
    return out
