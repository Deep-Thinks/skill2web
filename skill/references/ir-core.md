# IR Core (universal fields)

> **v0.2 (2026-05-15)** — 取代 `ir-schema.md`(已删)。
> 本文档描述 **universal** 字段(任何 `ir_kind` 都必须有);kind-specific 子 schema
> 见 `ir-kinds/<kind>.md`。

IR (Intermediate Representation) 是 **extractor 与 composer 之间的契约**:composer
需要的所有数据都必须在 IR 里;不在 IR 的字段 composer 不许猜。

## Top-level structure

```jsonc
{
  "ir_version":     "0.2",
  "ir_kind":        "image-deck"        // §6.3 (sub-schema: ir-kinds/image-deck.md)
                  | "template-html"     // §6.4 (sub-schema: ir-kinds/template-html.md)
                  | "png-canvas"        // §6.5 (sub-schema: ir-kinds/png-canvas.md)
                  | "pptx-canvas"       // §6.6 spike-gated, schema 草案
                  | "data-table",       // §6.6 spike-gated, schema 草案

  "skill_meta":      { /* §1 */ },
  "input_schema":    [ /* §2 */ ],
  "llm_pipeline":    [ /* §3 — 数组化, 严格线性 */ ],
  "browser_runtime": { /* §4 */ },
  "error_ux":        { /* §5 */ },
  "attribution":     { /* §6 — 强制 */ },
  "render":          { /* §7 — polymorphic, shape 取决于 ir_kind */ }
}
```

`ir_version` 是字符串;v0.2 是当前唯一合法值。
`ir_kind` 在 v0.2 接受三个完整支持的值与两个 spike-gated 值,见上文。

---

## 1. `skill_meta` (required)

```jsonc
{
  "name":         "ian-handdrawn-ppt",            // kebab-case; 来自 SKILL.md frontmatter
  "display_name": "Ian Handdrawn PPT",            // 友好标题, 用于 <title>
  "description":  "Turn an article into a Chinese handdrawn technical PPT image deck.",
  "source": {
    "type":  "github",                             // "github" | "local" | "zip"
    "url":   "https://github.com/helloianneo/ian-handdrawn-ppt",
    "rev":   "main",                               // optional, commit / branch
    "path_inside_repo": "ian-handdrawn-ppt"        // optional, 当 SKILL.md 嵌套时
  },
  "license":      "MIT",                           // 来自 LICENSE
  "author":       "Ian",                           // 来自 LICENSE / NOTICE
  "author_links": ["https://github.com/helloianneo", "https://ianneo.xyz"]
}
```

字段未变 — v0.1 → v0.2 直接保留。

---

## 2. `input_schema` (required, non-empty)

终端用户在生成的 HTML 里要填的表单字段。

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

支持 `type`: `text`, `textarea`, `select`, `number`, `file:<mime>` (例 `file:image/*`)。

**Extractor 行为**: SKILL.md 不显式声明输入字段。Extractor 必须**从 Workflow / Defaults
推断**,然后**在 USER GATE 2 让用户确认**。input_schema 不在 skill 文件里,而在 skill 意图里。

---

## 3. `llm_pipeline` (required, non-empty array)

> **v0.2 关键变化**: 从 `llm_phase: { ... }` 单对象升为 `llm_pipeline: [ ... ]` 数组。
> 但**严格线性**, `uses` 只能引前序 step。任何 DAG / 分叉 / 合流 → analyzer Phase 4 拒。

```jsonc
[
  {
    "id":                     "intake",            // kebab-case, 在 pipeline 内唯一
    "model_hint":             "deepseek-chat",
    "temperature":            0.4,
    "json_mode":              "prompt-only",       // "response-format" | "prompt-only" | "off"
    "system_prompt_template": "...",
    "user_prompt_template":   "【内容】{{input.content}}",
    "uses":                   [],                  // 第一步必空数组
    "expected_output_schema": { /* JSON Schema */ }
  },
  {
    "id":                     "plan",
    "model_hint":             "deepseek-chat",
    "temperature":            0.4,
    "json_mode":              "prompt-only",
    "system_prompt_template": "...",
    "user_prompt_template":   "前序 intake 结果: {{steps.intake.output.summary}}\n规划 N 张幻灯片...",
    "uses":                   ["intake"],          // 只能引用更早的 step
    "expected_output_schema": { /* JSON Schema */ }
  }
]
```

### 3.1 硬约束 (composer 强制校验)

- `uses` 只能包含**严格在前**的 step id (拓扑序由数组顺序决定,不允许显式拓扑)
- 同一 step 内 `uses` 数组**禁止循环**(implied — uses 只能引前序就排除了)
- 每个 step 的 `expected_output_schema` 必须填;前端 JSON 解析失败时落到 `error_ux.json_parse`
- 任意一步失败:默认整条 pipeline 终止;UI 显示 "第 N 步失败 + 看 prompt + 重试本步" 按钮(不向上重试)
- **1 step 是合法的**,等价于 v0.1 的 `llm_phase` 单对象

### 3.2 模板语法

`{{...}}` 是 Mustache-lite。三个命名空间:

- **Input**: `{{input.<key>}}` — 从用户填的表单值替换(等同于 v0.1 直接 `{{key}}`,但 v0.2 强制加 `input.` 前缀消除歧义)
- **Steps**: `{{steps.<step_id>.output.<dotted-path>}}` — 引用前序 step 输出
- **Static (build-time)**: `{{LLM_OUTPUT_SCHEMA_INLINE}}` 等 — composer 编译时填

`{{#item.list}}{{.}}{{/item.list}}` — 数组迭代(用于 render 阶段较多;LLM 阶段也允许)。

### 3.3 `json_mode` 选择

- `response-format`: 在请求里加 `response_format: {"type": "json_object"}`。OpenAI / 部分 DeepSeek 支持。**400/404 自动降级到 prompt-only。**
- `prompt-only`: 不设 `response_format`;靠 system prompt 要 strict JSON。前端用 `extractJson()` 兜底解析(直接 parse → fenced block → first `{...}` slice)。
- `off`: free-form 文本输出(template-html 的 markdown 输出可以走这个,但 render 端要会用)。

v0.2 默认: `prompt-only`(最兼容)。

### 3.4 禁止的形态

```jsonc
// ❌ DAG 形分叉
{ "id": "branch_a", "uses": ["intake"] },
{ "id": "branch_b", "uses": ["intake"] },
{ "id": "merge",    "uses": ["branch_a", "branch_b"] }   // 合流, 拒绝

// ❌ 条件跳转
{ "id": "decide",   ... },
{ "id": "path_a",   "uses": ["decide"], "if": "decide.output.kind === 'A'" }   // 条件, 拒绝
```

任何这种需求 → analyzer Phase 4 视为 agent-shaped。

---

## 4. `browser_runtime` (required)

```jsonc
{
  "llm_adapter":       "openai-chat-compat",       // 见 references/adapters.md
  "image_adapter":     "openai-images-compat" | null,   // 仅 image-deck / png-canvas 用
  "default_endpoints": {
    "llm":   { "base_url": "https://api.deepseek.com/v1",  "model": "deepseek-chat" },
    "image": { "base_url": "https://image.token-recyclebin.com/v1", "model": "gpt-image-2" }
                                                  // image 字段仅当 image_adapter != null
  },
  "concurrency":       3,                          // 并发 render_phase items
  "timeout_ms":        { "llm": 120000, "image": 180000 },
  "retry":             { "llm": 0, "image": 1 },
  "extra_libs":        []                          // 例 ["pptxgenjs@3"], 仅 spike-gated kind 用
}
```

终端用户可以在输出 HTML 的 Settings 面板覆盖 `default_endpoints` 与 `model`。
Compiler 在 IR 时定 default。

**`extra_libs` 政策**: 只允许 `references/render-libs.md` 中 `verified-full` 的 lib inline。
`verified-partial` 或 `unverified` 需要 user gate。

---

## 5. `error_ux` (required)

最常见错误的友好用户文案。Composer 把这些字符串挂到具体失败点。

```jsonc
{
  "missing_llm_key":   "请先在 [设置] 里填 LLM API Key。",
  "missing_image_key": "请先在 [设置] 里填图像 API Key。",
  "llm_4xx":           "LLM 调用被拒绝。常见原因: key 失效 / 余额不足 / 不支持该模型。",
  "llm_5xx":           "LLM 服务暂时不可用,过几秒再试。",
  "llm_timeout":       "LLM 响应超时(>120s)。检查网络,或换 base_url。",
  "image_4xx":         "图像 API 调用失败。可能是 endpoint 不支持当前 mode(/generations vs /edits)。试试在 [设置] 切换。",
  "image_5xx":         "图像服务繁忙,会自动重试一次。",
  "image_timeout":     "图像生成超时(>180s)。点这一项的 [重试]。",
  "cors":              "浏览器拒绝了跨域请求。这个 endpoint 可能不允许从网页直接调用 — 你需要换一个 CORS 友好的 endpoint,或起一个本地代理。",
  "json_parse":        "LLM 没返回有效 JSON。点 [看 prompt] 查看,或换更强的模型重试。",
  "kind_unsupported":  "此编译产物不支持当前操作 (例如 image-deck 模板下尝试调 PPTX 导出)。"
                                                  // v0.2 新增
}
```

所有字符串是**纯中文,可选英文括注**。终端用户是非开发者;不要 stack trace,不要 Postel-blame。

---

## 6. `attribution` (required, **enforced**)

```jsonc
{
  "source_skill_link":  "https://github.com/helloianneo/ian-handdrawn-ppt",
  "source_author":      "Ian",
  "source_author_link": "https://github.com/helloianneo",
  "source_license":     "MIT",
  "source_license_text_file": "LICENSE",          // path-in-source, README 里要 verbatim 拷贝
  "footer_html":
    "本网页由 <a href='https://github.com/...skill2web'>skill2web</a> 从 <a href='{{source_skill_link}}'>{{source_skill_name}}</a>({{source_author}} · {{source_license}})编译。"
}
```

Composer **必须**把 `footer_html`(占位符替换后)插到输出 HTML 的 `<footer>` 元素;
并把 `source_license_text_file` verbatim 拷到输出 README。

源 skill 没有 LICENSE → **拒绝编译**,直到用户加一个或显式 waive
(`force_compile_no_license: true` 在 IR 顶层 — 用户自负后果)。

---

## 7. `render` (required, polymorphic)

形状取决于 `ir_kind`,详见对应 `ir-kinds/<kind>.md`:

| `ir_kind` | sub-schema 文件 |
|---|---|
| `image-deck` | `ir-kinds/image-deck.md` |
| `template-html` | `ir-kinds/template-html.md` |
| `png-canvas` | `ir-kinds/png-canvas.md` |
| `pptx-canvas` | `ir-kinds/pptx-canvas.md`(spike-gated, 草案) |
| `data-table` | `ir-kinds/data-table.md`(spike-gated, 草案) |

---

## v0.1 → v0.2 IR Migration

见 DESIGN-v0.2.md 附录 A。Migration 是**一次性**(断 v0.1 IR,不维护双 schema)。

| v0.1 字段 | v0.2 字段 | 转换规则 |
|---|---|---|
| `ir_version: "0.1"` | `ir_version: "0.2"` | 直接改 |
| `ir_kind: "image-deck"` | 同名保留 | 不变 |
| `skill_meta`, `input_schema`, `browser_runtime`, `error_ux`, `attribution` | 同名保留 | 字段完全不变 |
| `static_assets.*` (top-level) | `render.static_assets.*` | 整块下移到 `render` |
| `llm_phase: { ... }` | `llm_pipeline: [ { id: "plan", ...llm_phase } ]` | 包成单元素数组,`id: "plan"`, `uses: []` |
| `render_phase: { kind, iterator, per_item }` | `render: { iterator, per_item }` | 整块改名;`kind` 升到 top-level `ir_kind` |
| `render_phase.iterator: "$.slides"` | `render.iterator: "$.steps.plan.output.slides"` | 路径前缀加 `steps.plan.output.` |
| 其它 `$.xxx` 引用 | `$.steps.plan.output.xxx` | 同上 |
| Mustache `{{key}}` (input) | `{{input.<key>}}` | 加前缀消歧义 |

`examples/ian-handdrawn-ppt.ir.json` 在 Phase A 走完 migration → 用 v0.2 composer 重编, 输出 JS 行为语义等价(空白/注释允许差异)。

---

## Full example

- `examples/ian-handdrawn-ppt.ir.json` — v0.2 image-deck (migration from v0.1)
- `examples/synthetic-essay-polisher.ir.json` — v0.2 template-html (Hero Case 2)
- `examples/guizang-cover.ir.json` — v0.2 png-canvas
