# Adapters (API 调用契约)

> v0.2 (2026-05-15) — 从 `lib-mapper.md` 拆出。理由 (DESIGN-v0.2.md §2):
> adapter (API 调用) 与 render lib (inline JS) 演化逻辑不同 ——
> adapter 看 CORS / auth / endpoint shape; lib 看 inline size / 语义等价性。
> 混在一张表越改越乱。

本文档管 **API adapter**: composer 编译时 inline 一段 JS 函数(例如 `callLLM()`)
到输出 HTML 的 `<script>`。每个 adapter 对应 `templates/adapters/<name>.js` 一个文件。

inline JS lib(marked.js / DOMPurify / pptxgenjs 等)→ 见 `render-libs.md`。

## Schema

```
| adapter name | wraps | 触发字段 | composer inlines | coverage | last verified | known gaps |
```

- **adapter name**: IR `browser_runtime.{llm,image}_adapter` 字段引用的短名
- **wraps**: 协议 / endpoint shape
- **触发字段**: 在 IR 哪个字段被引用
- **composer inlines**: `templates/adapters/<file>.js`
- **coverage**: `verified-full` / `verified-partial` / `unverified` / `stub` / `none` (定义见 v0.1 lib-mapper.md, 不变)
- **last verified**: 日期 + 验证者 + provider
- **known gaps**: 给 USER GATE 3 用的警告文本

## LLM adapters

| Name | Wraps | 触发字段 | Composer inlines | Coverage | Last verified | Known gaps |
|---|---|---|---|---|---|---|
| `openai-chat-compat` | OpenAI / DeepSeek / StepFun / 智谱 等 chat completions (`/v1/chat/completions`, Bearer auth) | `browser_runtime.llm_adapter = "openai-chat-compat"` | `adapters/openai-chat-compat.js` (~25 行) | **verified-partial** | 2026-05-15 | **StepFun + xiaomimimo 的浏览器 CORS 已实测 OK** (preflight `Access-Control-Allow-Origin: *` + 完整 POST 200); DeepSeek / 智谱 / OpenAI 仍未实测。streaming 未接(v0.2 不接)。|
| `anthropic-chat` | Anthropic Messages API (`/v1/messages`, `x-api-key`, `anthropic-version`) | `browser_runtime.llm_adapter = "anthropic-chat"` | `adapters/anthropic-chat.js` (~30 行) | **unverified** | — | 必须带 `anthropic-dangerous-direct-browser-access` header;浏览器 CORS 未测 |

## Image adapters

| Name | Wraps | 触发字段 | Composer inlines | Coverage | Last verified | Known gaps |
|---|---|---|---|---|---|---|
| `openai-images-compat` | OpenAI / 兼容 endpoint `/v1/images/generations` 或 `/v1/images/edits` | `browser_runtime.image_adapter = "openai-images-compat"` 且 `ir_kind ∈ {image-deck, png-canvas}` | `adapters/openai-images-compat.js` (~50 行,含 `makeBlankPng` for edits 模式) | **unverified** | — | endpoint 必须 CORS 友好;`image.token-recyclebin.com` 只支持 `/edits`;OpenAI 原生只支持 `/generations` |

## "no API" adapter

| Name | Wraps | 触发字段 | Composer inlines | Coverage |
|---|---|---|---|---|
| `none` | (无 API 调用) | `browser_runtime.image_adapter = null` 用于 template-html / data-table 等不需要图像 API 的 kind | (空) | n/a |

## Provider 默认 endpoints (v0.2)

> 这一节由 USER GATE 3a (provider) 引用。**默认值在 IR `browser_runtime.default_endpoints`,
> 不在本文件硬写**。本表只列"哪些 endpoint **看起来** OpenAI 兼容"。

| Provider | LLM base_url | 推荐 model | Image base_url | 推荐 model | 备注 |
|---|---|---|---|---|---|
| DeepSeek | `https://api.deepseek.com/v1` | `deepseek-chat` | — | — | 国内便宜;Python 后端验证过,浏览器 CORS 未测 |
| StepFun | `https://api.stepfun.com/v1` | `step-3.5-flash` / `step-2-mini` | (image 见下) | (跨试) | **2026-05-15 浏览器 CORS 已实测 OK** (`*` + 完整 POST 200, 通过 prompt-master / app-onboarding-blueprint hero case 验证); 部分模型拒 `response_format`,IR 用 `prompt-only`; reasoning 模型 (`step-3.5-flash`) 必须 `max_tokens >= 1000` 否则 content 空 |
| xiaomimimo | `https://api.xiaomimimo.com/v1` | `mimo-v2-pro` | — | — | **2026-05-15 CORS 已实测 OK** (preflight `*`), 但 key 失效 — 仅作为 CORS 友好的备选 endpoint 文档 |
| OpenAI 官方 | `https://api.openai.com/v1` | `gpt-4o-mini` | `https://api.openai.com/v1` | `dall-e-3` 或 `gpt-image-1` | CORS 友好;价格高、国内访问难 |
| `image.token-recyclebin.com` | — | — | `https://image.token-recyclebin.com/v1` | `gpt-image-2` | 只支持 `/edits`,IR 走 `endpoint_mode: "edits"`;Python 后端验证过,浏览器 CORS 未测 |
| Anthropic direct-browser | `https://api.anthropic.com/v1` | `claude-haiku-4-5` 等 | (无原生图像 API) | — | 必须用户 opt-in dangerous-direct-browser-access |

## 如何把 `unverified` → `verified-full`

(沿用 v0.1 流程, 不变)

1. 编译一个 hero case 指向该 provider
2. 用 `python3 -m http.server` 或 GitHub Pages 跑
3. 粘真 key 端到端跑通
4. DevTools Network 抓成功的 fetch 调用 → `verification/<date>-<provider>.md`
5. 本表对应行 `unverified` → `verified-full`,填 `Last verified`,从 `Known gaps` 移除 unverified 警告
6. 在 `Verification log` 加一行

## Verification log

| Date | Provider | Endpoint | Verifier | Notes |
|---|---|---|---|---|
| — | — | — | — | _v0.2 仍无浏览器端到端验证。每个 `unverified` 行需要一行才能升 `verified-full`。_ |

## Changelog

- **2026-05-15 (v0.2)**: 从 `lib-mapper.md` 拆出。所有 LLM/image API 调用契约集中在本文件;render-time inline JS lib 移到 `render-libs.md`。Verification log 仍空。
- **2026-05-15 (v0.1, post-codex-review)**: 所有 `full` 行 demoted 为 `unverified`(理由见原 lib-mapper.md changelog)。
