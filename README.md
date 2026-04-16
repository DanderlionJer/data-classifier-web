# Data-Classify

Web app: upload JSON or Excel metadata (database / table / column / comment), classify fields into levels 1-5 using configurable rules.

## Run

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8767
```

Open http://127.0.0.1:8767

## Config

- `app/rules/default_rules.json` — matching rules and tags
- `app/rules/level_mapping.json` — tag to level (1-5)

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

- **API**：`GET /api/standards`、`GET /api/ai-status`；`POST /api/classify` 支持表单字段 `frameworks`（适用标准多选）、`ai_enhance`、`stream_progress`（SSE 进度流）
- **前端**：适用标准多选、已选文件反馈、分类进度条、SSE 解析、可选「AI 增强」勾选区
- **代码**：`app/frameworks.py`、`app/ai_enhance.py`、`app/settings.py`（及 `tools/` 下补丁/辅助脚本等，视本机文件而定）
- **依赖**：以当前 `requirements.txt` 为准（相对已提交版本通常增加如 `httpx`、`python-dotenv` 等）

**若你发现「昨天有的功能今天没了」**，请依次确认：是否在**同一目录** `data-classifier-web` 下运行、是否误执行 `git restore` / 换了一台只拉了仓库的机器、以及 `git status` 是否仍显示上述改动与未跟踪文件。要长期保留请执行 `git add` + `git commit`（并 `git push` 到远端）。

