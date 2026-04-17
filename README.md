# Data-Classify

Web app: upload JSON or Excel metadata (database / table / column / comment), classify fields into **levels 1–5**, **rule tags**, and **high-level data categories** (business-facing types derived from tags via a separate mapping file).

## Run

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8767
```

Open http://127.0.0.1:8767

## Config

- `app/rules/default_rules.json` — matching rules and tags
- `app/rules/level_mapping.json` — `tag_levels` (tag → sensitivity 1–5) and optional `tag_labels_zh` (tag → Chinese label for UI). Tags with no `tag_labels_zh` entry show **no** Chinese in the web “标签” column or in `tags_zh` (empty strings only).
- `app/rules/tag_categories.json` — tag → **data category** id, plus `categories` (id → Chinese label). Fields with no matching rules default to category `general_public` (“公开与一般数据”). **File must be UTF-8** (not UTF-16).
- `app/rules/country_frameworks.json` — **country / region → default framework ids** (ISO 3166-1 alpha-2, e.g. `NL` → `GDPR`, `US` → `EO14117`, `CN` → `35273` + `43697`). `meta.how_to_extend_zh` describes how to add countries or attach new standards after registering them in `app/frameworks.py` (`STANDARDS_REGISTRY`).

## API

- `GET /api/countries` — `meta` from `country_frameworks.json` plus validated `countries[]` (`id`, `label_zh`, `framework_ids`, …).
- `GET /api/standards` — each standard includes `associated_country_ids` (reverse index from the country file).

`POST /api/classify` form fields:

- `frameworks` — JSON array of framework ids (optional). If **non-empty**, it determines rule filtering.
- `country` — optional ISO code. If `frameworks` is **omitted or empty**, the country’s `framework_ids` from `country_frameworks.json` are used. Invalid `country` → `422`.

## API output (`POST /api/classify`)

Each field in `fields[]` includes:

- `level`, `tags` (internal ids), `tags_zh` (Chinese per `tags` entry, same order; `""` if unmapped), `matches`, `rationale` (tag lines in rationale use Chinese only when mapped)
- `categories`: array of `{ "id", "label_zh" }` — one or more data types for that column (from final tags after suppression)

Top-level response also includes:

- `category_summary`: `{ "<category_id>": <count>, ... }` — counts how many fields were assigned each category (a field with multiple categories increments each)
- `category_labels`: full id → `label_zh` map from `tag_categories.json` (for UI legends)
- `tag_labels_zh`: tag id → Chinese label from `level_mapping.json` (entries with empty values are omitted)
- `country`: echoed ISO code when the client sent `country` (audit / UI)

The MCP tool `classify_metadata_fields` accepts optional `country_iso` and returns the same shape via `ClassifyResponse`. Use `list_country_framework_profiles` for the country → standards table.

## JSON input

`{"fields": [{"database":"...","schema":"...","table":"...","column":"...","data_type":"...","comment":"..."}]}`

Or a JSON array of field objects.

## Compliance alignment (reference only)

Structured mapping to **GB/T 35273-2020**, **PIPL**, **DSL** (Data Security Law), and **GDPR** is in `app/rules/compliance_framework.json`. Served at `GET /api/compliance-framework` for tools and audits. Not legal advice.

## AI enhancement (optional)

Administrators can enable **optional** post-classification refinement via a remote HTTP API. The browser **never** receives the API key; only the server reads it from the environment.

Supported backends:

- **OpenAI-compatible** (`openai`, or any custom base URL): `POST …/chat/completions`, `Authorization: Bearer …`, optional `response_format` JSON mode.
- **DeepSeek** (`deepseek`): same wire format as OpenAI; default base `https://api.deepseek.com/v1`, default model `deepseek-chat`.
- **Anthropic Claude** (`anthropic` / `claude`): Messages API at `POST …/messages`, `x-api-key` + `anthropic-version`; default base `https://api.anthropic.com/v1`.

| Variable | Meaning |
|----------|---------|
| `DATA_CLASSIFIER_AI_API_KEY` | Secret API key (required for AI mode) |
| `DATA_CLASSIFIER_AI_PROVIDER` | `auto` (default), `openai`, `deepseek`, `anthropic` or `claude`. With `auto`, provider is inferred from `DATA_CLASSIFIER_AI_BASE_URL` host (`anthropic.com` → Anthropic, `deepseek.com` → DeepSeek, else OpenAI-compatible). |
| `DATA_CLASSIFIER_AI_BASE_URL` | API base URL (no trailing path). If unset, defaults by provider: OpenAI `https://api.openai.com/v1`, DeepSeek `https://api.deepseek.com/v1`, Anthropic `https://api.anthropic.com/v1`. |
| `DATA_CLASSIFIER_AI_MODEL` | Model id; if unset: `gpt-4o-mini` (OpenAI), `deepseek-chat` (DeepSeek), `claude-3-5-sonnet-20241022` (Anthropic). |
| `DATA_CLASSIFIER_AI_ANTHROPIC_VERSION` | Anthropic API version header, default `2023-06-01`. |
| `DATA_CLASSIFIER_AI_TIMEOUT_SEC` | HTTP timeout seconds, default `120` |
| `DATA_CLASSIFIER_AI_BATCH_SIZE` | Fields per request (5–80), default `40` |
| `DATA_CLASSIFIER_AI_MAX_COMMENT_LEN` | Truncate comment in prompt, default `400` |
| `DATA_CLASSIFIER_AI_DISABLE_RESPONSE_FORMAT` | Set to `true` if an OpenAI-compatible provider rejects `response_format` (ignored for Anthropic). |

`GET /api/ai-status` returns `available`, `provider`, `model`, and `base_url_host` when configured (no secrets). When the user enables **AI 增强**, only **metadata** (column names, comments, types, rule output) is sent to the configured endpoint.

Restart the application process after changing these variables (settings are cached on the server).

## 迭代记录（产品变更）

### 已提交到 Git 的版本

| 日期 | 提交 | 说明 |
|------|------|------|
| 2026-04-14 | `30c5567` | 初始版本：FastAPI Web、JSON/Excel 上传、`POST /api/classify`、可配置规则与 1–5 级映射 |
| 2026-04-14 | `b53480e` | 合规对齐：`app/rules/compliance_framework.json`、`GET /api/compliance-framework`；首页增加合规说明入口（README 中此前默认开发端口为 **8765**） |
| 2026-04-15 | `55b81b5` | 规则与引擎：扩充 GB/GDPR 等缺口规则、`default_rules.json`、按优先级抑制标签、表上下文、`tools/build_rules.py` 等 |

以上版本**不包含**下列「工作区增量」中的 API/UI；若只克隆远端或只检出上述提交，界面会回到较简形态。

### 当前工作区增量（尚未 `git commit`）

下列能力存在于本机**未提交**的改动中（`git status` 可见）；其中多个模块当前仍为 **untracked**，未纳入版本库：

- **API**：`GET /api/standards`、`GET /api/countries`、`GET /api/ai-status`；`POST /api/classify` 支持 `country`（ISO）、`frameworks`（适用标准多选）、`ai_enhance`、`stream_progress`（SSE 进度流）
- **前端**：国家/地区下拉（联动默认标准）、适用标准多选（tooltip 显示关联国家）、已选文件反馈、分类进度条、SSE 解析、可选「AI 增强」勾选区
- **数据类别**：`app/rules/tag_categories.json`；引擎在 `classify_field` 中根据最终 tags 解析类别；`ClassifyResponse` 含 `categories` / `category_summary` / `category_labels`；首页展示「数据类别分布」与结果表「数据类别」列；AI 增强在改写 tags 后会重新计算类别
- **代码**：`app/frameworks.py`、`app/ai_enhance.py`、`app/settings.py`（及 `tools/` 下补丁/辅助脚本等，视本机文件而定）
- **依赖**：以当前 `requirements.txt` 为准（相对已提交版本通常增加如 `httpx`、`python-dotenv` 等）

**若你发现「昨天有的功能今天没了」**，请依次确认：是否在**同一目录** `data-classifier-web` 下运行、是否误执行 `git restore` / 换了一台只拉了仓库的机器、以及 `git status` 是否仍显示上述改动与未跟踪文件。要长期保留请执行 `git add` + `git commit`（并 `git push` 到远端）。

