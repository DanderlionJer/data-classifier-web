# Data-Classify

Web app: upload JSON or Excel metadata (database / table / column / comment), classify fields into levels 1-5 using configurable rules.

## Run

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8765
```

Open http://127.0.0.1:8765

## Config

- `app/rules/default_rules.json` — matching rules and tags
- `app/rules/level_mapping.json` — tag to level (1-5)

## JSON input

`{"fields": [{"database":"...","schema":"...","table":"...","column":"...","data_type":"...","comment":"..."}]}`

Or a JSON array of field objects.

## Compliance alignment (reference only)

Structured mapping to **GB/T 35273-2020**, **PIPL**, **DSL** (Data Security Law), and **GDPR** is in `app/rules/compliance_framework.json`. Served at `GET /api/compliance-framework` for tools and audits. Not legal advice.

