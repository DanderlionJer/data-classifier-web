from __future__ import annotations

import io
import json
from typing import Any

import pandas as pd

from app.models import FieldDescriptor

# Header aliases (ASCII + \u escapes for Chinese) to avoid source encoding issues
_HEADER_ALIASES: dict[str, list[str]] = {
    "database": ["database", "db", "\u5e93", "\u6570\u636e\u5e93", "database_name", "catalog"],
    "schema": ["schema", "\u6a21\u5f0f", "schema_name"],
    "table": ["table", "\u8868", "\u8868\u540d", "table_name"],
    "column": [
        "column",
        "\u5217",
        "\u5b57\u6bb5",
        "\u5b57\u6bb5\u540d",
        "\u5217\u540d",
        "column_name",
        "name",
    ],
    "data_type": ["data_type", "type", "\u7c7b\u578b", "\u6570\u636e\u7c7b\u578b", "dtype"],
    "comment": ["comment", "\u6ce8\u91ca", "\u8bf4\u660e", "\u5907\u6ce8", "description", "desc"],
}


def _normalize_headers(df: pd.DataFrame) -> pd.DataFrame:
    col_map: dict[str, str] = {}
    lower_to_orig = {str(c).strip().lower(): c for c in df.columns}

    for canonical, aliases in _HEADER_ALIASES.items():
        for a in aliases:
            key = a.lower()
            if key in lower_to_orig:
                col_map[lower_to_orig[key]] = canonical
                break
        else:
            for c in df.columns:
                cs = str(c).strip()
                if cs in aliases:
                    col_map[c] = canonical
                    break

    out = df.rename(columns=col_map)
    if "column" not in out.columns:
        if len(out.columns) == 1:
            out = out.rename(columns={out.columns[0]: "column"})
    return out


def _row_to_field(row: dict[str, Any]) -> FieldDescriptor | None:
    col = row.get("column") or row.get("name")
    if col is None or (isinstance(col, float) and pd.isna(col)):
        return None
    s = str(col).strip()
    if not s:
        return None

    def g(*keys: str) -> str:
        for k in keys:
            v = row.get(k)
            if v is None or (isinstance(v, float) and pd.isna(v)):
                continue
            return str(v).strip()
        return ""

    return FieldDescriptor(
        database=g("database"),
        schema=g("schema"),
        table=g("table"),
        column=s,
        data_type=g("data_type"),
        comment=g("comment"),
    )


def _dataframe_to_fields(df: pd.DataFrame) -> list[FieldDescriptor]:
    df = _normalize_headers(df)
    fields: list[FieldDescriptor] = []
    for _, row in df.iterrows():
        f = _row_to_field(row.to_dict())
        if f:
            fields.append(f)
    return fields


def parse_excel(content: bytes) -> list[FieldDescriptor]:
    df = pd.read_excel(io.BytesIO(content), engine="openpyxl")
    return _dataframe_to_fields(df)


def parse_csv_bytes(content: bytes) -> list[FieldDescriptor]:
    df = pd.read_csv(io.BytesIO(content), encoding="utf-8-sig")
    return _dataframe_to_fields(df)


def parse_json_bytes(content: bytes) -> list[FieldDescriptor]:
    data = json.loads(content.decode("utf-8-sig"))
    return parse_json_obj(data)


def parse_json_obj(data: Any) -> list[FieldDescriptor]:
    if isinstance(data, dict) and "fields" in data:
        items = data["fields"]
    elif isinstance(data, list):
        items = data
    else:
        raise ValueError('JSON must be {"fields": [...]} or an array of field objects')

    fields: list[FieldDescriptor] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        col = item.get("column") or item.get("column_name") or item.get("name")
        if not col:
            continue
        fields.append(
            FieldDescriptor(
                database=str(item.get("database") or ""),
                schema=str(item.get("schema") or ""),
                table=str(item.get("table") or item.get("table_name") or ""),
                column=str(col),
                data_type=str(item.get("data_type") or item.get("type") or ""),
                comment=str(item.get("comment") or item.get("description") or ""),
            )
        )
    if not fields:
        raise ValueError("No fields parsed; check JSON structure")
    return fields


def sniff_and_parse(filename: str, content: bytes) -> list[FieldDescriptor]:
    name = filename.lower()
    if name.endswith(".json"):
        return parse_json_bytes(content)
    if name.endswith(".csv"):
        return parse_csv_bytes(content)
    if name.endswith((".xlsx", ".xls")):
        return parse_excel(content)
    try:
        return parse_json_bytes(content)
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
        pass
    try:
        return parse_excel(content)
    except Exception as e:
        raise ValueError(f"Unrecognized file format: {e}") from e
