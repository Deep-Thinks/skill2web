# Lib Mapper

Map source-skill dependencies → browser-side equivalents. This table is **project canon**: an unmapped dep is a compile refusal.

## Schema

Each row:

```
| python / cli dep | browser equivalent | inline size | coverage | known gaps |
```

- **coverage**: `full` (drop-in OK) / `partial` (most features) / `stub` (no-op placeholder) / `none` (refuse)
- **inline size**: gzipped, when inlined as `<script>` in the output HTML. `—` if not a JS lib.
- **known gaps**: hands the composer the warning text to surface at USER GATE 3.

## LLM / Image / Audio APIs (most v0.1 skills touch these)

| Dep | Browser equivalent | Inline size | Coverage | Known gaps |
|---|---|---|---|---|
| `openai` SDK (chat completions) | `fetch` to OpenAI-compatible `/v1/chat/completions` endpoint with `Authorization: Bearer` header | — (built-in) | full | streaming not yet wired in template; non-streaming works. |
| `openai` SDK (images) | `fetch` to OpenAI-compatible `/v1/images/generations` (default) or `/v1/images/edits` (when a reference image is needed) | — | full | endpoint must be CORS-friendly; not all third-party proxies are. **Verify at USER GATE 3.** Some endpoints only support `/edits` (e.g. `image.token-recyclebin.com`) — composer wires `endpoint_mode` setting. |
| `anthropic` SDK (messages) | `fetch` to `https://api.anthropic.com/v1/messages` with `x-api-key` header + `anthropic-version` | — | partial | requires `anthropic-dangerous-direct-browser-access` header (Anthropic explicitly supports this since 2024); user must opt-in. |
| Image generation via Claude built-in image tool | Same as `openai` images via a public-proxy endpoint | — | partial | Anthropic doesn't expose a direct image-gen API; route to OpenAI-compatible proxy. **This is exactly how `ian-handdrawn-ppt` works in the browser**. |
| DeepSeek `deepseek-chat` | `fetch` to `https://api.deepseek.com/v1/chat/completions` (OpenAI-compatible) | — | full | CORS verified in v0.1 hero case (TODO: actually verify post-launch). `response_format: json_object` supported on `deepseek-chat`. |
| StepFun `step-*` | `fetch` to `https://api.stepfun.com/v1/chat/completions` | — | full | Same as DeepSeek; some models don't support `response_format` — use `json_mode: prompt-only` in IR. |
| 智谱 GLM (`glm-4`) | `fetch` to `https://open.bigmodel.cn/api/paas/v4/chat/completions` | — | partial | API contract similar but auth header differs slightly; **needs adapter PR before use**. |
| 即梦 / Doubao image | Custom endpoint | — | none (v0.1) | CORS not verified; auth model differs. Refuse until verified. |
| Replicate | — | — | none | CORS-hostile; needs server proxy. Refuse. |

## File generation libs

| Dep | Browser equivalent | Inline size | Coverage | Known gaps |
|---|---|---|---|---|
| `python-pptx` | `pptxgenjs` (UMD build from CDN inlined as `<script>`) | ~340 KB gzip | partial | text/shape/picture/table OK; chart support limited; no `python-pptx`-style theme inheritance. **For `render_phase.kind = pptx-canvas` only.** |
| `python-docx` | `docx` (from `docxjs`) | ~190 KB gzip | partial | basic paragraphs/headings/tables; no track-changes, no advanced styles. |
| `Pillow` / `PIL` | HTML5 `<canvas>` API directly | — | partial | open/resize/crop/text overlay OK; advanced filters (gaussian blur, etc.) require custom code. |
| `pandas` (data wrangling) | `duckdb-wasm` | ~6 MB gzip | full for SQL-shaped ops | inline cost is heavy; only use when skill genuinely needs SQL. For light tabular work, hand-roll. |
| `matplotlib` | `Plotly` (offline build) or `Chart.js` | 60-280 KB gzip | partial | scientific notation, polar/3D — none. For 80% bar/line/scatter — Chart.js fine. |
| `numpy` (used purely for shape math) | `mathjs` or hand-rolled | 60 KB | partial | only when numpy is a thin convenience; refuse if heavy linalg. |
| `Pillow` text rendering with Chinese fonts | `<canvas>` `fillText` + system fonts | — | partial | Chinese font availability depends on user's OS; not pixel-identical to PIL. For ian-handdrawn-ppt-style skills, **text is baked into the image by the image-gen model**, not by client-side canvas — so this rarely matters in practice. |

## Format conversion / IO

| Dep | Browser equivalent | Inline size | Coverage | Known gaps |
|---|---|---|---|---|
| `markdown` (CommonMark parse) | `marked` | 12 KB | full | — |
| `markdown-it` plugins | `markdown-it` UMD | 25 KB | full | not all plugin ecosystems available; verify per skill. |
| `PyPDF2` / `pypdf` (read) | `pdf.js` | 280 KB | partial | text extraction OK; forms/annotations partial. |
| `python-magic` (MIME detect) | dumb extension-based detect | — | stub | "good enough" for skill-input flow. |
| zip read/write | `JSZip` UMD | 95 KB | full | inline only when needed (v0.1 default: skip; manual download per file). |

## File system / shell / env

| Dep | Browser equivalent | Coverage | Notes |
|---|---|---|---|
| `os.environ` | `localStorage` (compile-time → run-time) | partial | only for user-pasted keys, never for compile-time injection. |
| `subprocess` / shell call | — | **none** | refuse: shell calls cannot exist in a browser-only artifact. |
| `requests` to private endpoints | — | **none** | refuse: see `refusal: private-api`. |
| `requests` to public CORS-friendly endpoints | `fetch` | full | — |
| `glob` / `pathlib` | — | **none** | refuse: no filesystem. |
| `tempfile` | in-memory Blob | full | — |

## Adapter names (used by IR.browser_runtime)

The IR refers to adapters by short name. The composer wires each to a code template:

| Adapter name | Wraps | Composer inlines |
|---|---|---|
| `openai-chat-compat` | OpenAI/DeepSeek/StepFun/智谱 chat completions (Bearer auth, `/v1/chat/completions`) | `callLLM()` (~25 lines) |
| `anthropic-chat` | Anthropic Messages API (`x-api-key`, `anthropic-version`, `dangerous-direct-browser-access`) | `callAnthropicLLM()` (~30 lines) |
| `openai-images-compat` | OpenAI/Compat `/images/generations` or `/images/edits` | `callImageAPI()` + `makeBlankPng()` (~50 lines, see hero case) |
| `none` | — | no API wiring; render_phase only |

## Adding a new row

USER GATE 3 says: don't silently add. Ask the user. Format for new rows:

```
| <dep>  | <browser equiv>  | <inline size> | <coverage>  | <gaps + verification status> |
```

After adding, **also** add a one-line entry under `# Changelog` at the bottom of this file:

## Changelog

- 2026-05-15: Initial table (v0.1). Validated rows: `openai` SDK chat/images, DeepSeek, StepFun. Unvalidated but listed: 智谱, Anthropic direct-browser. All others marked `none` or `stub` pending real-world verification.
