from __future__ import annotations

import io
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
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app = FastAPI(title="Data classifier", version="0.1.0")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "index.html",
        {"title": "数据分类分级（演示）"},
    )


@app.post("/api/classify")
async def api_classify(file: UploadFile = File(...)) -> JSONResponse:
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="空文件")

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
                "comment": "手机号",
            },
            {
                "database": "crm",
                "table": "customers",
                "column": "user_name",
                "comment": "客户姓名",
            },
            {
                "database": "crm",
                "table": "customers",
                "column": "created_at",
                "comment": "创建时间",
            },
        ]
    }
    return JSONResponse(sample)


def _run_dev() -> None:
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8765, reload=True)


if __name__ == "__main__":
    _run_dev()
