# Render Libs (inline JS / format conversion)

> v0.2 (2026-05-15) — 从 `lib-mapper.md` 拆出。本文件管 **render-time inline JS lib**:
> 例如 marked.js, DOMPurify, pptxgenjs, JSZip。
> API 调用契约(LLM / image API)→ 见 `adapters.md`。

## Schema

```
| python / cli dep | browser equivalent | inline size (gzip) | coverage | known gaps |
```

## File generation libs

| Dep | Browser equivalent | Inline size | Coverage | Known gaps | 触发字段 |
|---|---|---|---|---|---|
| (markdown 渲染) | `marked` UMD | ~12 KB gzip | full | CommonMark 完整;GFM 扩展默认开 | `ir_kind = template-html` 且 `render.output_form = markdown` |
| (HTML XSS 净化) | `DOMPurify` UMD | ~22 KB gzip | full | strict / relaxed 两档配置 | `ir_kind = template-html` 且 `render.sanitizer ∈ {dompurify-strict, dompurify-relaxed}` |
| `python-pptx` | `pptxgenjs` UMD | ~340 KB gzip | partial(text/shape/picture/table OK;chart 受限;无 python-pptx 主题继承) | 仅 `pptx-canvas` (spike-gated) | `ir_kind = pptx-canvas` |
| `python-docx` | `docx` (docxjs) | ~190 KB gzip | partial | 基本 paragraph/heading/table;无 track-changes | (无 IR 触发,v0.2 未支持) |
| `Pillow` / PIL | HTML5 `<canvas>` | — (built-in) | partial | open/resize/crop/text overlay OK;高级 filter 要自写 | `ir_kind = png-canvas` 且 `render.compositing != none`(v0.2 仅占位) |
| `pandas` | `duckdb-wasm` | ~6 MB gzip | full(SQL-shaped ops) | inline 太重;只有 skill 真要 SQL 才用。`data-table` v0.2 **明确禁用** `transform.kind = "sql"` | (无 v0.2 触发) |
| `matplotlib` | `Plotly` 或 `Chart.js` | 60-280 KB gzip | partial | 极坐标/3D 不支持 | (无 v0.2 触发) |
| `numpy` (轻 shape 数学) | `mathjs` 或手写 | ~60 KB | partial | 仅薄便利;重 linalg 必拒 | (无) |
| `markdown` (CommonMark) | `marked` | 12 KB | full | (与上面 marked 同) | (与上同) |
| `markdown-it` plugin | `markdown-it` UMD | ~25 KB | full | 不是所有 plugin 都有 JS 版,逐 skill 验证 | (无 v0.2 触发) |
| `PyPDF2` / `pypdf` (read) | `pdf.js` | ~280 KB | partial | 文字提取 OK;表单/批注部分 | (无 v0.2 触发) |
| `python-magic` | extension-based detect | — | stub | "够用"对 skill 输入流而言 | (无显式触发) |
| zip read/write | `JSZip` UMD | 95 KB | full | 仅 zip-emit 模式才 inline(v0.2 不支持) | (无 v0.2 触发) |

## File system / shell / env

(语义不变,从 v0.1 lib-mapper.md §"File system / shell / env" 复制)

| Dep | Browser equivalent | Coverage | Notes |
|---|---|---|---|
| `os.environ` | `localStorage` (compile-time → run-time) | partial | 只用于用户粘的 key,**绝不**用于 compile-time 注入 |
| `subprocess` / shell | — | **none** | 拒绝: `refusal: needs-shell` |
| `requests` 到私 endpoint | — | **none** | 拒绝: `refusal: private-api` |
| `requests` 到公开 CORS-friendly endpoint | `fetch` | full | — |
| `glob` / `pathlib` / `os.path` | — | **none** | 拒绝: `refusal: needs-fs` |
| `tempfile` | in-memory `Blob` | full | — |

## 添加新行

USER GATE 3b 说: 不要静默加。问用户。格式:

```
| <dep> | <browser equiv> | <inline size> | <coverage> | <gaps + verification status> | <触发字段> |
```

加完, 也在 `Changelog` 下加一行。

## 与 `adapters.md` 的边界

| 文件 | 管什么 | 例 |
|---|---|---|
| `adapters.md` | run-time 走 fetch 调用的 **API 契约**(URL, header, payload shape) | `openai-chat-compat`, `openai-images-compat`, `anthropic-chat` |
| `render-libs.md` (本) | 编译时 **inline 进 HTML 的 JS 库**(纯 client-side, 无 API 调用) | `marked`, `DOMPurify`, `pptxgenjs`, `JSZip` |

边界判定: 这个东西在浏览器里**直接跑代码**还是**通过 fetch 调外部服务**? 前者归 render-libs,后者归 adapters。

## Changelog

- **2026-05-15 (v0.2)**: 从 `lib-mapper.md` 拆出 render-libs / adapters 两文件;明确边界。新增 marked / DOMPurify(为 template-html plugin)。pptxgenjs 行明确 spike-gated。
- **2026-05-15 (v0.1)**: 初表(原 `lib-mapper.md`)。
