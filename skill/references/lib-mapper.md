# Lib Mapper

Map source-skill dependencies → browser-side equivalents. This table is **project canon**: an unmapped dep is a compile refusal.

> ⚠️ **HONEST SCOPE (post-codex-review 2026-05-15)**: A `coverage: full` claim is
> a **promise that breaks user trust if wrong**. v0.1 has only validated rows via
> one Python-backend hand-compile, not browser-CORS smoke tests. To prevent
> over-promising, every `full` row is **demoted to `unverified` until evidence is
> recorded** in the Verification log at the bottom of this file. The compile
> workflow's USER GATE 3 must surface the `unverified` status verbatim.

## Schema

Each row:

```
| python / cli dep | browser equivalent | inline size | coverage | last verified | known gaps |
```

- **coverage**: one of
  - `verified-full` — verified by **direct browser fetch from a static `http://` origin**, against a real provider, with a `Last verified` date. Add to the Verification log below.
  - `verified-partial` — same, but with documented feature gaps.
  - `unverified` — claim looks reasonable but no real browser run yet. **USER GATE 3 must surface this.**
  - `stub` — no-op placeholder; will not throw, will not do the work.
  - `none` — refuse compile.
- **last verified**: date + verifier + provider (e.g. `2026-06-10 / xj / OpenAI api.openai.com`). `—` for unverified.
- **inline size**: gzipped, when inlined as `<script>` in the output HTML. `—` if not a JS lib.
- **known gaps**: hands the composer the warning text to surface at USER GATE 3.

## LLM / Image / Audio APIs (most v0.1 skills touch these)

| Dep | Browser equivalent | Inline size | Coverage | Last verified | Known gaps |
|---|---|---|---|---|---|
| `openai` SDK (chat completions) | `fetch` to OpenAI-compatible `/v1/chat/completions` endpoint with `Authorization: Bearer` header | — (built-in) | **unverified** | — | streaming not yet wired in template; non-streaming should work. **No browser-side CORS smoke test yet.** |
| `openai` SDK (images) | `fetch` to OpenAI-compatible `/v1/images/generations` (default) or `/v1/images/edits` (with reference image) | — | **unverified** | — | endpoint must be CORS-friendly; not all third-party proxies are. Some endpoints only support `/edits` (e.g. `image.token-recyclebin.com`) — composer wires `endpoint_mode`. |
| `anthropic` SDK (messages) | `fetch` to `https://api.anthropic.com/v1/messages` with `x-api-key` header + `anthropic-version` | — | **unverified** | — | requires `anthropic-dangerous-direct-browser-access` header; user must opt-in. Browser CORS not tested. |
| Image generation via Claude built-in image tool | Route through an OpenAI-compatible image proxy (Anthropic does not expose a direct image-gen API) | — | **unverified** | — | This is how `ian-handdrawn-ppt` runs in the browser; the proxy CORS friendliness is provider-dependent. |
| DeepSeek `deepseek-chat` | `fetch` to `https://api.deepseek.com/v1/chat/completions` (OpenAI-compatible) | — | **unverified** | — | Was incorrectly marked `full` in initial draft; **demoted post-codex-review**. CORS not browser-tested. `response_format: json_object` reportedly supported. |
| StepFun `step-*` | `fetch` to `https://api.stepfun.com/v1/chat/completions` | — | **unverified** | — | Was `full`; **demoted post-codex-review**. Some models reject `response_format` — use `json_mode: prompt-only` in IR. |
| `image.token-recyclebin.com` (gpt-image-2 proxy) | `fetch` to `/v1/images/generations` or `/v1/images/edits` | — | **unverified** | — | Was implicitly `full` (chosen as hero-case default); **demoted post-codex-review**. Third-party proxy; reachable only over Python backend in `explorecipe`. Browser CORS unknown. |
| 智谱 GLM (`glm-4`) | `fetch` to `https://open.bigmodel.cn/api/paas/v4/chat/completions` | — | **unverified** | — | Was `partial`; auth header differs slightly from OpenAI. Adapter not validated. |
| 即梦 / Doubao image | Custom endpoint | — | none (v0.1) | — | CORS not verified; auth model differs. Refuse until verified. |
| Replicate | — | — | none | — | CORS-hostile; needs server proxy. Refuse. |

**How to promote `unverified` → `verified-full`** (do this when actually running a smoke test, not before):

1. Compile a hero case targeting that provider.
2. Serve over `http://localhost:<port>` (NOT `file://`).
3. Paste your real key, run end-to-end, capture the working network request (DevTools → Network → copy as cURL) into a `verification/<date>-<provider>.md` file.
4. Update the row: change `unverified` → `verified-full`, fill `Last verified` with `<date> / <verifier> / <endpoint>`, drop the `unverified` warning from `Known gaps`.
5. Add the entry to the Verification log at the bottom.

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

## Verification log

| Date | Provider | Endpoint | Verifier | Notes |
|---|---|---|---|---|
| — | — | — | — | _No browser-side end-to-end verification yet. Every `unverified` row above needs one entry here before being promoted to `verified-full`._ |

## Changelog

- **2026-05-15 (post-codex-review)**: All previously `full` rows demoted to `unverified` per codex Issue 2. Reason: the only evidence we had came from Python-backend integration in sibling projects (`explorecipe`, `DB2HTML`); none of these endpoints had been validated for browser-direct CORS. A `full` claim is a user-trust promise — over-promising breaks trust on first run. New promotion path documented above.
- **2026-05-15**: Initial table (v0.1).
