from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
p = ROOT / "app" / "main.py"
t = p.read_text(encoding="utf-8")

if "import asyncio" not in t:
    t = t.replace("import json\n", "import asyncio\nimport json\n", 1)
if "Awaitable" not in t:
    t = t.replace(
        "from pathlib import Path\n",
        "from collections.abc import Awaitable, Callable\nfrom pathlib import Path\n",
        1,
    )
if "StreamingResponse" not in t:
    t = t.replace(
        "from fastapi.responses import HTMLResponse, JSONResponse\n",
        "from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse\n",
        1,
    )

start = t.index('@app.post("/api/classify")')
end = t.index('@app.get("/api/ai-status")')

build_fn = '''async def _build_classify_response(
    fields: list,
    fw_sel,
    want_ai: bool,
    progress: Callable[[int, str], Awaitable[None]] | None,
) -> ClassifyResponse:
    if progress:
        await progress(8, "\\u89c4\\u5219\\u5f15\\u64ce\\u5206\\u7c7b\\u4e2d\\u2026")
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
                detail="AI \\u589e\\u5f3a\\u672a\\u914d\\u7f6e\\uff1a\\u8bf7\\u7ba1\\u7406\\u5458\\u8bbe\\u7f6e\\u73af\\u5883\\u53d8\\u91cf DATA_CLASSIFIER_AI_API_KEY",
            )
        if progress:
            await progress(12, "\\u51c6\\u5907\\u8c03\\u7528 AI \\u6a21\\u578b\\u2026")
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
        ai_applied = True
        s_ai = get_ai_settings()
        ai_model = s_ai.model
        ai_provider = s_ai.provider
    if progress:
        await progress(99, "\\u751f\\u6210\\u54cd\\u5e94\\u2026")
    return ClassifyResponse(
        fields=classified,
        summary=summary,
        applied_frameworks=applied_frameworks_label(fw_sel),
        ai_enhancement_applied=ai_applied,
        ai_model=ai_model,
        ai_provider=ai_provider,
    )


'''

new_classify = '''@app.post("/api/classify")
async def api_classify(
    file: UploadFile = File(...),
    frameworks: str | None = Form(default=None),
    ai_enhance: str | None = Form(default=None),
    stream_progress: str | None = Form(default=None),
) -> JSONResponse | StreamingResponse:
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="\\u7a7a\\u6587\\u4ef6")

    try:
        fields = sniff_and_parse(file.filename or "upload", raw)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    fw_sel = parse_frameworks_param(frameworks)
    try:
        validate_framework_selection(fw_sel)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e

    want_ai = (ai_enhance or "").strip().lower() in ("1", "true", "yes", "on")
    use_stream = (stream_progress or "").strip().lower() in ("1", "true", "yes", "on")

    if use_stream:

        async def sse_line(obj: dict) -> bytes:
            return f"data: {json.dumps(obj, ensure_ascii=False)}\\n\\n".encode("utf-8")

        async def event_gen():
            queue: asyncio.Queue[tuple[int, str] | None] = asyncio.Queue()

            async def reporter(pct: int, msg: str) -> None:
                await queue.put((pct, msg))

            async def worker() -> ClassifyResponse:
                try:
                    return await _build_classify_response(fields, fw_sel, want_ai, reporter)
                finally:
                    await queue.put(None)

            try:
                yield await sse_line(
                    {"type": "progress", "pct": 2, "message": "\\u5df2\\u63a5\\u6536\\u6587\\u4ef6\\u2026"}
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

    body = await _build_classify_response(fields, fw_sel, want_ai, None)
    return JSONResponse(content=body.model_dump(mode="json", by_alias=True))


'''

t = t[:start] + build_fn + new_classify + t[end:]
p.write_text(t, encoding="utf-8", newline="\n")
print("patched main.py")
