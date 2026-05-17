# IR Core (universal fields)

> **v0.2 (2026-05-15)** — 取代 `ir-schema.md`(已删)。
> 本文档描述 **universal** 字段(任何 `ir_kind` 都必须有);kind-specific 子 schema
> 见 `ir-kinds/<kind>.md`。

IR (Intermediate Representation) 是 **extractor 与 composer 之间的契约**:composer
需要的所有数据都必须在 IR 里;不在 IR 的字段 composer 不许猜。

## Top-level structure

```jsonc
{
  "ir_version":     "0.3",
  "ir_kind":        "image-deck"        // §6.3 (sub-schema: ir-kinds/image-deck.md)
                  | "template-html"     // §6.4 (sub-schema: ir-kinds/template-html.md)
                  | "png-canvas"        // §6.5 (sub-schema: ir-kinds/png-canvas.md)
                  | "pptx-canvas"       // §6.6 spike-gated, schema 草案
                  | "data-table",       // §6.6 spike-gated, schema 草案

  "skill_meta":      { /* §1 */ },
  "input_schema":    [ /* §2 */ ],
  "llm_pipeline":    [ /* §3 — 数组化, v0.3 起支持静态 DAG */ ],
  "browser_runtime": { /* §4 */ },
  "error_ux":        { /* §5 */ },
  "attribution":     { /* §6 — 强制 */ },
  "render":          { /* §7 — polymorphic, shape 取决于 ir_kind */ },
  "theme_overrides": "..."              // §8 — optional, v0.3 frontend-design pass 产出
}
```

`ir_version` 是字符串;v0.3 是当前合法值,composer 同时接受 v0.2(v0.2 IR 是 v0.3 的子集 —— 无 `when`、`uses` 单父)。
`ir_kind` 接受三个完整支持的值与两个 spike-gated 值,见上文。
`theme_overrides`(可选,见 §8)是 v0.3 强制 frontend-design pass 的产物。

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
> **v0.3 关键变化**: 升级为**静态 DAG** —— `uses` 可多父(合流),step 可带 `when`
> 结构化分支条件(分叉)。但图必须在**编译期完全已知且有限**:`uses` 仍只能引
> 前序 step(数组拓扑序),`when` 是数据比较而非运行时自由决策,无循环、无运行时
> 决定的图形状。不满足"编译期已知且有限" → analyzer Phase 4 仍拒为 agent-shaped。

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
    "uses":                   ["intake"],          // v0.3: 可多父 ["intake","classify"]
    "when":                   null,                // v0.3 可选: 见 §3.4 静态 DAG 分支
    "expected_output_schema": { /* JSON Schema */ }
  }
]
```

### 3.1 硬约束 (composer / runtime 强制)

- `uses` 里的每个 id 必须**严格在前**(拓扑序 = 数组顺序)。v0.3 起 `uses` 可含多个父(合流);因为只能引前序,循环天然被排除。
- 每个 step 的 `expected_output_schema` 必须填;前端 JSON 解析失败时落到 `error_ux.json_parse`
- 任意一步**失败**:默认整条 pipeline 终止;UI 显示 "第 N 步失败 + 看 prompt + 重试本步" 按钮(不向上重试)
- 一步被 `when` 或上游**跳过**(skip)≠ 失败:runtime 记 `state.steps[id] = {skipped:true, output:null}`,进度条标灰,pipeline 继续
- skip 传播规则:一个 step 当且仅当**它所有父都被跳过**(或自身 `when` 不命中)才被跳过 —— merge / fan-in 节点只要有一个父跑过就执行
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

### 3.4 `when` — 静态 DAG 分支 (v0.3)

`when` 是 step 的**可选**字段。缺省 / `null` → 该 step 无条件执行。它是一个**结构化条件对象**(不是自由 JS 表达式 —— 它是 build-time 数据,runtime 只做比较,不 `eval`):

```jsonc
"when": {
  "path":  "steps.classify.output.kind",   // dotted lookup into { steps, input }
  "op":    "eq",                           // 见下表
  "value": "A"
}
```

`op` 支持:`eq` / `ne` / `in`(value 为数组)/ `gt` / `gte` / `lt` / `lte` / `exists` / `truthy`。

**合法的静态 DAG**(分叉 + 合流,编译期完全已知):

```jsonc
{ "id": "classify", "uses": [] },
{ "id": "path_a",   "uses": ["classify"],
  "when": { "path": "steps.classify.output.kind", "op": "eq", "value": "A" } },
{ "id": "path_b",   "uses": ["classify"],
  "when": { "path": "steps.classify.output.kind", "op": "eq", "value": "B" } },
{ "id": "merge",    "uses": ["classify", "path_a", "path_b"] }   // 合流, 总执行
```

runtime:`classify` 跑完 → `path_a` / `path_b` 按 `when` 二选一,落选那条 skip → `merge`
合流(它的父没有全部 skip,所以执行)。`merge` 的 prompt 引用被 skip 分支的输出时
(`{{steps.path_b.output.text}}`)Mustache-lite 解析为空串,prompt 模板需写得能容忍。

**强约束**:pipeline 可以在中段分叉,但 `render` 读取的那个**终端 step 必须无条件执行**
(无 `when`,且不会因上游全 skip 而被跳过)。否则 render 拿不到数据。

**仍然禁止的形态**(不是静态 DAG,是 agent-shape):

```jsonc
// ❌ 无界循环 / 轮数运行时决定
{ "id": "refine", "uses": ["refine"], "loop_until": "score > 8" }

// ❌ 运行时才决定图形状 / 工具序列(图本身编译期不可知)
```

判定准则见 `analyzer-checklist.md §4`:**控制流图在编译期是否完全已知且有限**。
已知有限 → 静态 DAG,可编译;运行时才决定轮数 / 形状 → agent-shaped,拒。

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

## 8. `theme_overrides` (optional, v0.3)

一段 **raw CSS 字符串**,composer 原样 inline 到输出 HTML `<style>` 的**最后**(在
skeleton 基础样式与 `BLOCK:HEAD` kind 样式之后),因此能覆盖二者。

```jsonc
"theme_overrides": ":root{--accent:#C2410C}\nheader h1{letter-spacing:-.02em}\n..."
```

这是 v0.3 **强制 frontend-design pass**(见 `SKILL.md` Phase 5、`compiler-workflow.md`)
的产物:composer 跑之前,编译 agent 必须先调 `frontend-design` skill 得到一套与该
skill 主题相称的视觉方案,把产出的 CSS 收进本字段。缺省 / 空串 → 用 skeleton 默认皮肤。

约束:**只放 CSS**,不放 `<script>` / `<link>` / `@import` 远程资源(单文件 + 无运行时
CDN 依赖的硬规则);不放 `url(http...)` 外链。frontend-design 产出若含这些,编译
agent 必须 inline 化或剔除后再写入。

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

## v0.2 → v0.3 IR Migration

**无需迁移脚本**。v0.3 是 v0.2 的严格超集:`when` 字段可选、`uses` 多父只是放宽约束、`theme_overrides` 可选。一份合法的 v0.2 IR 直接就是合法的 v0.3 IR。composer 同时接受 `ir_version` 为 `"0.2"` 或 `"0.3"`。新编译建议把 `ir_version` 写 `"0.3"` 并补上 frontend-design pass 产出的 `theme_overrides`。

---

## Full example

- `examples/ian-handdrawn-ppt.ir.json` — v0.2 image-deck (migration from v0.1)
- `examples/synthetic-essay-polisher.ir.json` — v0.2 template-html (Hero Case 2)
- `examples/guizang-cover.ir.json` — v0.2 png-canvas
