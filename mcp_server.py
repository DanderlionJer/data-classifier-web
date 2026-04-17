"""MCP server (stdio) for data-classifier: tools wrap the same engine as the FastAPI app.

Run (from project root):

  python mcp_server.py

Cursor: MCP server command (cwd = project root):

  python mcp_server.py

Requires: pip install mcp (see requirements.txt).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from dotenv import load_dotenv

load_dotenv(_ROOT / ".env", override=True)

from mcp.server.fastmcp import FastMCP
from pydantic import TypeAdapter, ValidationError

from app.ai_enhance import enhance_classified_fields
from app.classifier import classify_fields, load_tag_levels, rollup_category_counts
from app.frameworks import (
    applied_frameworks_label,
    list_countries_for_api,
    list_standards_for_api,
    normalize_country_param,
    resolve_classify_frameworks,
)
from app.models import ClassifyResponse, FieldDescriptor
from app.settings import ai_enhancement_configured, get_ai_settings

mcp = FastMCP(
    "data-classifier",
    instructions=(
        "Classify database column metadata (names, comments, types) into sensitivity levels "
        "and tags aligned with GB/T 35273, GB/T 43697, GDPR, etc. Input is JSON only, no raw table data."
    ),
)


@mcp.tool()
def list_data_standards() -> str:
    """Return selectable standard/framework ids and labels (JSON array). Use ids in classify_metadata_fields."""
    return json.dumps(list_standards_for_api(), ensure_ascii=False, indent=2)


@mcp.tool()
def list_country_framework_profiles() -> str:
    """Return country/region ISO codes and default selectable framework ids (JSON). Editable in app/rules/country_frameworks.json."""
    path = _ROOT / "app" / "rules" / "country_frameworks.json"
    if path.is_file():
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {"meta": {}}
    data["countries"] = list_countries_for_api()
    return json.dumps(data, ensure_ascii=False, indent=2)


@mcp.tool()
def get_compliance_framework() -> str:
    """Return app/rules/compliance_framework.json for mapping references (JSON object)."""
    path = _ROOT / "app" / "rules" / "compliance_framework.json"
    if not path.is_file():
        return json.dumps({"error": "compliance_framework.json not found"}, ensure_ascii=False)
    with path.open(encoding="utf-8") as f:
        return f.read()


@mcp.tool()
async def classify_metadata_fields(
    fields_json: str,
    frameworks_json: str | None = None,
    country_iso: str | None = None,
    use_ai_enhance: bool = False,
) -> str:
    """Classify a list of field metadata rows into levels 1-5 and tags.

    fields_json: JSON array of objects. Keys: database, schema, table, column (required), data_type, comment.
    frameworks_json: JSON array of framework ids (e.g. ["35273","43697","GDPR"]). If omitted or empty, country_iso defaults apply.
    country_iso: Optional ISO 3166-1 alpha-2 (e.g. NL -> GDPR, US -> EO14117). See list_country_framework_profiles.
    use_ai_enhance: If true, runs optional LLM pass (needs DATA_CLASSIFIER_AI_API_KEY in .env).
    """
    try:
        raw = json.loads(fields_json)
    except json.JSONDecodeError as e:
        return json.dumps({"error": "invalid fields_json", "detail": str(e)}, ensure_ascii=False)

    if not isinstance(raw, list):
        return json.dumps({"error": "fields_json must be a JSON array"}, ensure_ascii=False)

    try:
        fields = TypeAdapter(list[FieldDescriptor]).validate_python(raw)
    except ValidationError as e:
        return json.dumps({"error": "field validation failed", "detail": e.json()}, ensure_ascii=False)

    if not fields:
        return json.dumps(
            {"error": "empty fields list", "fields": [], "summary": {}},
            ensure_ascii=False,
        )

    country_resolved: str | None = None
    if (country_iso or "").strip():
        try:
            country_resolved = normalize_country_param(country_iso)
        except ValueError as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)
    try:
        fw_sel = resolve_classify_frameworks(frameworks_json, country_iso)
    except ValueError as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)

    classified, summary, category_summary, category_labels, tag_labels_zh = classify_fields(
        fields, frameworks=fw_sel
    )
    ai_applied = False
    ai_model = None
    ai_provider = None

    if use_ai_enhance:
        if not ai_enhancement_configured():
            return json.dumps(
                {
                    "error": "AI enhancement requested but DATA_CLASSIFIER_AI_API_KEY is not configured",
                },
                ensure_ascii=False,
            )
        tag_levels = load_tag_levels()
        classified = await enhance_classified_fields(classified, tag_levels, progress=None)
        summary = {}
        for c in classified:
            k = str(c.level)
            summary[k] = summary.get(k, 0) + 1
        category_summary = rollup_category_counts(classified)
        ai_applied = True
        s_ai = get_ai_settings()
        ai_model = s_ai.model
        ai_provider = s_ai.provider

    body = ClassifyResponse(
        fields=classified,
        summary=summary,
        category_summary=category_summary,
        category_labels=category_labels,
        tag_labels_zh=tag_labels_zh,
        country=country_resolved,
        applied_frameworks=applied_frameworks_label(fw_sel),
        ai_enhancement_applied=ai_applied,
        ai_model=ai_model,
        ai_provider=ai_provider,
    )
    return json.dumps(body.model_dump(mode="json", by_alias=True), ensure_ascii=False, indent=2)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()