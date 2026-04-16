from __future__ import annotations

import json
import os
import re
from collections.abc import Awaitable, Callable
from typing import Any

import httpx

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

    allowed = _allowed_tags(tag_levels)
    system = _build_system_prompt(allowed)

    out: list[ClassifiedField] = []
    batch_ranges = list(range(0, len(classified), settings.batch_size))
    total_batches = max(1, len(batch_ranges))

    async with httpx.AsyncClient(timeout=settings.timeout_sec) as client:
        for batch_idx, start in enumerate(batch_ranges):
            if progress:
                sub = int(100 * batch_idx / total_batches)
                await progress(
                    sub,
                    f"AI：第 {batch_idx + 1}/{total_batches} 批（请求模型）…",
                )
            batch = classified[start : start + settings.batch_size]
            payload_items: list[dict[str, Any]] = []
            for j, c in enumerate(batch):
                f = c.field
                payload_items.append(
                    {
                        "i": j,
                        "database": (f.database or "")[:120],
                        "schema": (f.schema_name or "")[:120],
                        "table": (f.table or "")[:120],
                        "column": (f.column or "")[:120],
                        "data_type": (f.data_type or "")[:80],
                        "comment": (f.comment or "")[: settings.max_comment_len],
                        "rule_level": c.level,
                        "rule_tags": c.tags[:40],
                        "rule_rationale": (c.rationale or "")[:600],
                        "matched_rules": [m.rule_id for m in c.matches[:20]],
                    }
                )
            user_msg = json.dumps({"items": payload_items}, ensure_ascii=False)
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
                out.extend(batch)
                if progress:
                    await progress(
                        int(100 * (batch_idx + 1) / total_batches),
                        f"AI：第 {batch_idx + 1} 批失败，已保留规则结果",
                    )
                continue

            for j, c in enumerate(batch):
                base = ClassifiedField.model_validate(c.model_dump())
                it = by_i.get(j)
                if not it:
                    out.append(base)
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
                out.append(
                    base.model_copy(
                        update={
                            "level": final_level,
                            "tags": tag_out,
                            "rationale": new_rationale,
                            "ai": meta,
                        }
                    )
                )
            if progress:
                sub_done = int(100 * (batch_idx + 1) / total_batches)
                await progress(
                    min(sub_done, 100),
                    f"AI：已完成 {batch_idx + 1}/{total_batches} 批",
                )
    return out
