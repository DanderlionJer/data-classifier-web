from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Callable
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
# Prefer values from project .env so a blank shell/user env var does not block the key.
load_dotenv(BASE_DIR / ".env", override=True)

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from markupsafe import Markup

from app.ai_enhance import enhance_classified_fields
from app.classifier import classify_fields, load_tag_levels, rollup_category_counts
from app.frameworks import (
    applied_frameworks_label,
    list_countries_for_api,
    list_standards_for_api,
    normalize_country_param,
    resolve_classify_frameworks,
)
from app.ingest import sniff_and_parse
from app.settings import ai_enhancement_configured, public_ai_status, get_ai_settings
from app.models import ClassifyResponse

FRAMEWORK_PATH = BASE_DIR / "app" / "rules" / "compliance_framework.json"
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app = FastAPI(title="Data classifier", version="0.1.0")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    raw = json.dumps(list_standards_for_api(), ensure_ascii=False)
    standards_embed = Markup(raw.replace("</", "<\\/"))
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "title": "\u6570\u636e\u5206\u7c7b\u5206\u7ea7\uff08\u56fd\u6807/GDPR\u5bf9\u9f50\u6f14\u793a\uff09",
            "standards_embed_json": standards_embed,
        },
    )


@app.get("/api/compliance-framework")
async def compliance_framework() -> JSONResponse:
    if not FRAMEWORK_PATH.is_file():
        raise HTTPException(status_code=404, detail="compliance_framework.json missing")
    with FRAMEWORK_PATH.open(encoding="utf-8") as f:
        data = json.load(f)
    return JSONResponse(data)


@app.get("/api/standards")
async def api_standards() -> JSONResponse:
    return JSONResponse(list_standards_for_api())


@app.get("/api/countries")
async def api_countries() -> JSONResponse:
    """Country / region list with default framework ids; meta from country_frameworks.json."""
    p = BASE_DIR / "app" / "rules" / "country_frameworks.json"
    data: dict
    if p.is_file():
        with p.open(encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {"meta": {}}
    data["countries"] = list_countries_for_api()
    return JSONResponse(data)


async def _build_classify_response(
    fields: list,
    fw_sel,
    want_ai: bool,
    progress: Callable[[int, str], Awaitable[None]] | None,
    country_iso: str | None = None,
) -> ClassifyResponse:
    if progress:
        await progress(8, "\u89c4\u5219\u5f15\u64ce\u5206\u7c7b\u4e2d\u2026")
    classified, summary, category_summary, category_labels, tag_labels_zh = classify_fields(
        fields, frameworks=fw_sel
    )
    ai_applied = False
    ai_model = None
    ai_provider = None
    if want_ai:
        if not ai_enhancement_configured():
            raise HTTPException(
                status_code=503,
                detail="AI \u589e\u5f3a\u672a\u914d\u7f6e\uff1a\u8bf7\u7ba1\u7406\u5458\u8bbe\u7f6e\u73af\u5883\u53d8\u91cf DATA_CLASSIFIER_AI_API_KEY",
            )
        if progress:
            await progress(12, "\u51c6\u5907\u8c03\u7528 AI \u6a21\u578b\u2026")
        tag_levels = load_tag_levels()

        async def ai_sub(sub_pct: int, msg: str) -> None:
            mapped = 14 + int(81 * sub_pct / 100)
            if progress:
                await progress(min(mapped, 96), msg)

        classified = await enhance_classified_fields(
            classified, tag_levels, progress=ai_sub
        )
        summary = {}
        for c in classified:
            k = str(c.level)
            summary[k] = summary.get(k, 0) + 1
        category_summary = rollup_category_counts(classified)
        ai_applied = True
        s_ai = get_ai_settings()
        ai_model = s_ai.model
        ai_provider = s_ai.provider
    if progress:
        await progress(99, "\u751f\u6210\u54cd\u5e94\u2026")
    return ClassifyResponse(
        fields=classified,
        summary=summary,
        category_summary=category_summary,
        category_labels=category_labels,
        tag_labels_zh=tag_labels_zh,
        country=country_iso,
        applied_frameworks=applied_frameworks_label(fw_sel),
        ai_enhancement_applied=ai_applied,
        ai_model=ai_model,
        ai_provider=ai_provider,
    )


@app.post("/api/classify", response_model=None)
async def api_classify(
    file: UploadFile = File(...),
    frameworks: str | None = Form(default=None),
    country: str | None = Form(default=None),
    ai_enhance: str | None = Form(default=None),
    stream_progress: str | None = Form(default=None),
) -> JSONResponse | StreamingResponse:
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="\u7a7a\u6587\u4ef6")

    try:
        fields = sniff_and_parse(file.filename or "upload", raw)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    country_iso: str | None = None
    if (country or "").strip():
        try:
            country_iso = normalize_country_param(country)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e)) from e
    try:
        fw_sel = resolve_classify_frameworks(frameworks, country)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e

    want_ai = (ai_enhance or "").strip().lower() in ("1", "true", "yes", "on")
    use_stream = (stream_progress or "").strip().lower() in ("1", "true", "yes", "on")

    if use_stream:

        async def sse_line(obj: dict) -> bytes:
            return f"data: {json.dumps(obj, ensure_ascii=False)}\n\n".encode("utf-8")

        async def event_gen():
            queue: asyncio.Queue[tuple[int, str] | None] = asyncio.Queue()

            async def reporter(pct: int, msg: str) -> None:
                await queue.put((pct, msg))

            async def worker() -> ClassifyResponse:
                try:
                    return await _build_classify_response(
                        fields, fw_sel, want_ai, reporter, country_iso
                    )
                finally:
                    await queue.put(None)

            try:
                yield await sse_line(
                    {"type": "progress", "pct": 2, "message": "\u5df2\u63a5\u6536\u6587\u4ef6\u2026"}
                )
                task = asyncio.create_task(worker())
                while True:
                    item = await queue.get()
                    if item is None:
                        break
                    pct, msg = item
                    yield await sse_line({"type": "progress", "pct": pct, "message": msg})
                body = await task
                yield await sse_line(
                    {"type": "result", "data": body.model_dump(mode="json", by_alias=True)}
                )
            except HTTPException as e:
                yield await sse_line(
                    {"type": "error", "detail": str(e.detail), "status": e.status_code}
                )
            except Exception as e:
                yield await sse_line({"type": "error", "detail": str(e), "status": 500})

        return StreamingResponse(
            event_gen(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    body = await _build_classify_response(fields, fw_sel, want_ai, None, country_iso)
    return JSONResponse(content=body.model_dump(mode="json", by_alias=True))


@app.get("/api/ai-status")
async def ai_status() -> JSONResponse:
    return JSONResponse(public_ai_status())

@app.get("/api/sample-json")
async def sample_json() -> JSONResponse:
    sample = {
        "fields": [
            {
                "database": "crm",
                "schema": "public",
                "table": "customers",
                "column": "mobile_phone",
                "data_type": "varchar(20)",
                "comment": "\u624b\u673a\u53f7",
            },
            {
                "database": "crm",
                "table": "customers",
                "column": "user_name",
                "comment": "\u5ba2\u6237\u59d3\u540d",
            },
            {
                "database": "crm",
                "table": "customers",
                "column": "created_at",
                "comment": "\u521b\u5efa\u65f6\u95f4",
            },
        ]
    }
    return JSONResponse(sample)


def _run_dev() -> None:
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8767, reload=True)


if __name__ == "__main__":
    _run_dev()
