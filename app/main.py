from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.classifier import classify_fields
from app.ingest import sniff_and_parse
from app.models import ClassifyResponse

BASE_DIR = Path(__file__).resolve().parent.parent
FRAMEWORK_PATH = BASE_DIR / "app" / "rules" / "compliance_framework.json"
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app = FastAPI(title="Data classifier", version="0.1.0")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "index.html",
        {"title": "\u6570\u636e\u5206\u7c7b\u5206\u7ea7\uff08\u56fd\u6807/GDPR\u5bf9\u9f50\u6f14\u793a\uff09"},
    )


@app.get("/api/compliance-framework")
async def compliance_framework() -> JSONResponse:
    if not FRAMEWORK_PATH.is_file():
        raise HTTPException(status_code=404, detail="compliance_framework.json missing")
    with FRAMEWORK_PATH.open(encoding="utf-8") as f:
        data = json.load(f)
    return JSONResponse(data)


@app.post("/api/classify")
async def api_classify(file: UploadFile = File(...)) -> JSONResponse:
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="\u7a7a\u6587\u4ef6")

    try:
        fields = sniff_and_parse(file.filename or "upload", raw)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    classified, summary = classify_fields(fields)
    body = ClassifyResponse(
        fields=classified,
        summary=summary,
    )
    return JSONResponse(content=body.model_dump(mode="json", by_alias=True))


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

    uvicorn.run("app.main:app", host="127.0.0.1", port=8765, reload=True)


if __name__ == "__main__":
    _run_dev()
