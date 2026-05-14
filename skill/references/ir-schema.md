# IR Schema

The IR (Intermediate Representation) is the **contract between extractor and composer**. Everything the composer needs to fill the HTML template must live in IR; everything not in IR must not be guessed by the composer.

This document is the canonical schema. It is informed by the hand-compile of `ian-handdrawn-ppt` (see `../../hero-cases/ian-handdrawn-ppt/LESSONS.md`); the original DESIGN.md draft IR was revised here based on what hand-compiling actually surfaced.

## Why the draft IR in DESIGN.md was wrong (revisions logged)

| DESIGN.md original | What actually broke | Revision |
|---|---|---|
| `lib_deps` as flat list | image-generation skills don't use python libs; this field was always empty | Folded into `browser_runtime.extra_libs` (often empty) |
| `llm_calls` as array | flow-shaped skills almost always need exactly one LLM call | Renamed `llm_phase`, single object |
| `render_spec.engine` like `pptxgenjs` | Couples render to one specific library | Renamed `render_phase.kind` (an enum) — composer picks engine |
| No `static_assets` field | Style locks / archetypes had no home; ad-hoc inlined | New top-level field — these are the soul of an image-gen skill |
| No `attribution` requirement | Easy to forget the source author footer | New required top-level field |

## Top-level structure

```jsonc
{
  "ir_version":     "0.1",
  "skill_meta":     { /* who, what, license */ },
  "static_assets":  { /* raw text + lookups, inlined verbatim */ },
  "input_schema":   [ /* form fields the end user fills */ ],
  "llm_phase":      { /* the one LLM call that produces the spine */ },
  "render_phase":   { /* what the browser does with the spine */ },
  "browser_runtime":{ /* which APIs + tuning */ },
  "error_ux":       { /* per-error friendly copy */ },
  "attribution":    { /* author + license, mandatory in footer + README */ }
}
```

`ir_version` is a string. v0.1 is the only valid value today. Future schema-breaking changes must bump this.

---

## 1. `skill_meta` (required)

```jsonc
{
  "name":        "ian-handdrawn-ppt",            // kebab-case; from SKILL.md frontmatter
  "display_name":"Ian Handdrawn PPT",            // human-friendly, used in <title>
  "description": "Turn an article into a Chinese handdrawn technical PPT image deck.",
  "source": {
    "type":  "github",                            // "github" | "local" | "zip"
    "url":   "https://github.com/helloianneo/ian-handdrawn-ppt",
    "rev":   "main",                              // optional, commit / branch
    "path_inside_repo": "ian-handdrawn-ppt"      // optional, when SKILL.md is nested
  },
  "license":     "MIT",                          // from LICENSE
  "author":      "Ian",                          // from LICENSE / NOTICE
  "author_links":["https://github.com/helloianneo", "https://ianneo.xyz"]
}
```

---

## 2. `static_assets` (required, **this is the soul**)

The single biggest lesson from hand-compiling: **prompt-shaped skills have a large amount of carefully-tuned static text that must be inlined verbatim.** The extractor's job is to identify these blocks and copy them — not paraphrase, not summarize.

```jsonc
{
  "style_lock":         "...verbatim text block from references/prompt-patterns.md...",
  "role_locks": {
    "cover": "...verbatim Page-role-cover block...",
    "body":  "...verbatim Page-role-body block..."
    // arbitrary additional roles allowed
  },
  "reference_clauses": [
    "...optional verbatim style-anchor text (used in lieu of binary reference image)..."
  ],
  "archetypes": [
    "cover-metaphor", "single-concept", "left-right-contrast",
    "horizontal-process", "circular-mechanism", "branching-map",
    "classification-map", "matrix-table", "main-metaphor", "takeaway"
  ],
  "theme_tokens": {
    // Subset of original theme tokens that the BROWSER needs. Not the full file.
    "paper":  "#FBFAF5",
    "ink":    "#111111",
    "size_by_role": { "cover": "1536x1024", "body": "1536x1024" }
    // Add more fields only if the prompt template references them.
  }
}
```

**Rule**: `static_assets` content is **strings that get inlined into the output HTML verbatim**. They are not parsed at runtime. If you change a character, the visual brand of the source skill is broken.

For skills with no style anchor (e.g. a pure text-render skill), `style_lock` and `role_locks` may be empty strings or absent. `archetypes` may be empty. But **the field must exist** — composer reads it unconditionally.

---

## 3. `input_schema` (required, non-empty)

List of form fields the end user fills in the output HTML.

```jsonc
[
  { "key": "content",  "type": "textarea", "label": "文章 / 大纲", "required": true,
    "placeholder": "粘贴文章或写主题",  "min_chars": 5 },
  { "key": "audience", "type": "text",     "label": "目标读者", "required": false },
  { "key": "scenario", "type": "select",   "label": "使用场景",
    "options": [
      { "value": "teaching", "label": "教学" },
      { "value": "explain",  "label": "科普" },
      { "value": "share",    "label": "分享" }
    ],
    "default": "teaching" },
  { "key": "length",   "type": "select",   "label": "页数",
    "options": [{"value":5,"label":"5"},{"value":8,"label":"8 (推荐)"},{"value":12,"label":"12"}],
    "default": 8 }
]
```

Supported `type`: `text`, `textarea`, `select`, `number`, `file:<mime>` (e.g. `file:image/*`).

**Extractor behavior**: SKILL.md does not declare input fields directly. The extractor must **infer from the Workflow / Defaults sections** and then **ask the user to confirm** before writing IR. There is no automatic mode — input_schema lives in the skill's intent, not in its files.

---

## 4. `llm_phase` (required)

The **one** LLM call that converts user input into a structured "spine" the render phase iterates over.

```jsonc
{
  "model_hint":     "deepseek-chat",       // user can override at run-time
  "temperature":    0.4,
  "json_mode":      "prompt-only",         // "response-format" | "prompt-only" | "off"
  "system_prompt_template":
    "You are the planner for <SKILL_NAME>. Read the user's content and output a deck spine JSON ...\n\nOutput schema:\n{{LLM_OUTPUT_SCHEMA_INLINE}}\n\nRules:\n- ...",
  "user_prompt_template":
    "【场景】{{scenario}}\n【受众】{{audience}}\n【页数】{{length}}\n\n【内容】\n{{content}}",
  "expected_output_schema": {
    "type": "object",
    "required": ["deck_type", "slides"],
    "properties": {
      "deck_type": { "type": "string", "enum": ["teaching", "persuasive", "report", "product", "knowledge-card"] },
      "slides": {
        "type": "array",
        "minItems": 1,
        "items": {
          "type": "object",
          "required": ["role", "title", "archetype", "main_point"],
          "properties": {
            "role":          { "type": "string", "enum": ["cover","body"] },
            "title":         { "type": "string", "maxLength": 12 },
            "subtitle":      { "type": "string" },
            "archetype":     { "type": "string", "enum": [/* from static_assets.archetypes */] },
            "main_point":    { "type": "string" },
            "composition":   { "type": "string" },
            "required_text": { "type": "array", "items": { "type": "string" } }
          }
        }
      }
    }
  }
}
```

**Templating**: `{{...}}` placeholders are simple Mustache-like substitution. Two namespaces:

- **User-input refs** like `{{content}}`, `{{audience}}` — substituted at run-time from form values.
- **Static refs** like `{{LLM_OUTPUT_SCHEMA_INLINE}}` — substituted at **compile-time** (composer fills these from IR).

**`json_mode` choice**:
- `response-format`: include `response_format: {"type": "json_object"}` in the API request. Works on OpenAI, gpt-image-1 backends, sometimes DeepSeek. **Auto-downgrade on 400/404.**
- `prompt-only`: don't set `response_format`; rely on system prompt asking for strict JSON output. Parse with `extractJson()` (try direct, then fenced block, then first `{...}` slice).
- `off`: free-form text output (rare for v0.1 skills).

v0.1 default: `prompt-only` (most compatible).

---

## 5. `render_phase` (required)

What the browser does after `llm_phase` returns a spine.

```jsonc
{
  "kind":      "image-per-slide",   // v0.1: "image-per-slide" only
                                     // v0.2: + "template-html" | "pptx-canvas" | "png-canvas"
  "iterator":  "$.slides",           // JSONPath-lite: which array in the spine to iterate
  "per_item": {
    "prompt_template":
      "Use case: Chinese handdrawn technical PPT visual.\nAsset type: ...\n\nApply the deck style lock:\n{{static_assets.style_lock}}\n\nPage role lock:\n{{static_assets.role_locks[item.role]}}\n\nTitle exactly: {{item.title}}\nArchetype: {{item.archetype}}\nMain point: {{item.main_point}}\n\nComposition:\n{{item.composition}}\n\nRequired text only:\n{{#item.required_text}}- {{.}}\n{{/item.required_text}}",
    "size_by_role": { "cover": "1536x1024", "body": "1536x1024" },
    "api":          "openai-images-compat",      // see browser_runtime
    "endpoint_mode":"generations"                // "generations" | "edits"
  }
}
```

**`iterator` semantics**: `$.slides` means "iterate over the `slides` array in the LLM output". The browser code substitutes `{{item.field}}` per item, and `{{static_assets.X}}` once globally per template.

**`per_item.prompt_template`** uses three placeholder namespaces:

- `{{static_assets.X}}` — global, from IR.static_assets
- `{{item.X}}` — per-iteration, from one element of the iterator
- `{{#item.list}}{{.}}{{/item.list}}` — minimal block iteration for arrays inside items

This is intentionally a **subset of Mustache** to keep the browser runtime tiny (~30 lines).

**`per_item.api`** maps to a browser adapter in `browser_runtime.adapters`. Composer uses this to choose which fetch function to inline.

---

## 6. `browser_runtime` (required)

```jsonc
{
  "llm_adapter":   "openai-chat-compat",          // see lib-mapper.md
  "image_adapter": "openai-images-compat",         // only when kind=image-per-slide
  "default_endpoints": {
    "llm":   { "base_url": "https://api.deepseek.com/v1", "model": "deepseek-chat" },
    "image": { "base_url": "https://image.token-recyclebin.com/v1", "model": "gpt-image-2" }
  },
  "concurrency":   3,                              // parallel render_phase items
  "timeout_ms":    { "llm": 120000, "image": 180000 },
  "retry":         { "llm": 0, "image": 1 },
  "extra_libs":    []                              // e.g. ["pptxgenjs@3"], inlined as <script>
}
```

The end user can override `default_endpoints` and `model` in the output HTML's Settings panel. The compiler picks the defaults at IR time.

**`extra_libs` policy**: only browser-side libs from `lib-mapper.md` with `coverage: full` may be inlined. Anything `partial` or `stub` requires a user gate.

---

## 7. `error_ux` (required)

Friendly user-facing copy for the most common errors. Composer wires these to specific failure points.

```jsonc
{
  "missing_llm_key":   "请先在 [设置] 里填 LLM API Key。怎么获取？...",
  "missing_image_key": "请先在 [设置] 里填图像 API Key。",
  "llm_4xx":           "LLM 调用被拒绝。常见原因：key 失效 / 余额不足 / 不支持该模型。",
  "llm_5xx":           "LLM 服务暂时不可用，过几秒再试。",
  "llm_timeout":       "LLM 响应超时（>120s）。检查网络，或换 base_url。",
  "image_4xx":         "图像 API 调用失败。可能是 endpoint 不支持当前 mode（/generations vs /edits）。试试在 [设置] 切换。",
  "image_5xx":         "图像服务繁忙，会自动重试一次。",
  "image_timeout":     "图像生成超时（>180s）。点这一张的 [重试]。",
  "cors":              "浏览器拒绝了跨域请求。这个 endpoint 可能不允许从网页直接调用 — 你需要一个本地代理，或换一个 CORS 友好的 endpoint。",
  "json_parse":        "LLM 没返回有效 JSON。点 [看 prompt] 查看，或换更强的模型重试。"
}
```

All strings are **plain Chinese with optional fallback English in parens**. End users are non-developers; no stack traces, no Postel-blame.

---

## 8. `attribution` (required, **enforced**)

```jsonc
{
  "source_skill_link":  "https://github.com/helloianneo/ian-handdrawn-ppt",
  "source_author":      "Ian",
  "source_author_link": "https://github.com/helloianneo",
  "source_license":     "MIT",
  "source_license_text_file": "LICENSE",          // path-in-source to include verbatim in README
  "footer_html":
    "本网页由 <a href='https://github.com/...skill2web'>skill2web</a> 从 <a href='{{source_skill_link}}'>{{source_skill_name}}</a>（{{source_author}} · {{source_license}}）编译。"
}
```

The composer **must** insert `footer_html` (after placeholder substitution) into a `<footer>` element of the output HTML, and copy `source_license_text_file` verbatim into the output README.

If a source skill has no LICENSE, **refuse to compile** until the user adds one or explicitly waives (`force_compile_no_license: true` at the top of IR — they own the consequences).

---

## Full example

See `skill/examples/ian-handdrawn-ppt.ir.json` for the reverse-engineered IR of the hero case.
