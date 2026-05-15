# IR kind: `template-html`

> v0.2 sub-schema. 通用字段见 `../ir-core.md` §1-§6。本文档描述 `render` 多态部分
> (§7) 在 `ir_kind: "template-html"` 下的 shape。Phase B 设计输入: hero case
> `hero-cases/synthetic-essay-polisher/`。

## 适用场景

- 输入(草稿/主题/manuscript) → 1-3 次 LLM 调用 → markdown 或 HTML 文档输出
- 不需要 image API; `browser_runtime.image_adapter` 必须是 null
- 例: `nature-polishing`(润色)、`khazix-writer`(公众号长文)、`guizang-ppt 主流程`(单文件 deck HTML, 多段)

## `render` shape

```jsonc
"render": {
  "output_form":   "markdown" | "html-fragment" | "full-document",

  "template_html": "<article>{{steps.polish.output.title}}...</article>",
                                                   // 可选, 若为空走"标准 article 模板"
  "css_lock":      "/* 可选, inline CSS, 与 image-deck 的 style_lock 同精神 */",
  "data_binding":  "$.steps.<step_id>.output",     // 模板上下文根

  "sanitizer":     "dompurify-strict"
                | "dompurify-relaxed"
                | "none-trust",                     // 必须显式选择, 没有默认值

  "features": {                                    // 可选能力开关
    "toc":              false,
    "footnotes":        false,
    "syntax_highlight": false,
    "print_css":        true,
    "export_pdf":       false                       // v0.2 占位 disabled
  }
}
```

## 字段语义

### `output_form` (discriminator)

| 值 | LLM 输出形态 | composer 行为 |
|---|---|---|
| `markdown` | LLM JSON 中含 markdown 字符串字段(例 `body_md`) | runtime 用内置 markdown subset 渲染器(支持段落 / 标题 / 列表 / 引用 / 代码块 / `*斜* **粗** \`code\` [link]`)+ sanitizer |
| `html-fragment` | LLM 直接输出 HTML 段(包在 JSON 字段里, 例 `body_html`) | runtime 走 sanitizer, 不走 markdown 转换 |
| `full-document` | LLM 输出完整 HTML 文档(包含 `<html>` `<head>`) | runtime 用 iframe 沙箱呈现; 不走 sanitizer (用户必须选 `sanitizer = "none-trust"`) |

### `template_html` (可选)

- 缺省(空字符串或字段不存在) → 走"标准 article 模板":
  ```html
  <h1>{{title}}</h1>
  <div class="article-abstract">{{abstract}}</div>          (若 abstract 存在)
  <h2>{{section.heading}}</h2><div>{{section.body_md}}</div>  (按 sections 数组迭代)
  ```
- 显式给 → 用 mustache-lite 渲染, 上下文根来自 `data_binding`。允许 `{{steps.X.output.Y}}` / `{{#sections}}...{{/sections}}` / `{{#sections}}{{heading}}{{/sections}}`。

### `css_lock`

inline 到 `<style>` 段的 CSS。skeleton 内置已有 article 样式; `css_lock` 是 **追加**(不覆盖)。空字符串合法。

### `data_binding`

JSONPath-lite 表达式, 指向 `state.steps[*].output` 内某个对象作为模板根。例 `$.steps.polish.output`。

### `sanitizer` (强制)

| 值 | 行为 | 何时用 |
|---|---|---|
| `dompurify-strict` | 内置白名单 sanitizer: 仅允许 `p / h1-h6 / ul / ol / li / blockquote / pre / code / strong / em / a / br / hr / span`; `a` 只允许 `href + target + rel`; `code` 允许 `class`。`href` 滤掉 `javascript:` `data:` `vbscript:`。 | LLM 输出可能含恶意 HTML 时(默认推荐) |
| `dompurify-relaxed` | 加白名单 `table / thead / tbody / tr / td / th / img / figure / figcaption / div`; `img` 允许 `src + alt + title`(同样滤协议) | LLM 输出有表格 / 图(且你信任图源) |
| `none-trust` | **完全不净化**, LLM 输出直插 DOM。**XSS 路径** | 仅当 `output_form = "full-document"` 走 iframe 沙箱时, 或 LLM 完全可信(本地模型) |

> ⚠️ **none-trust 必须 USER GATE 警告**: 在 USER GATE 2 (IR confirm) 与 USER GATE 3 都明确告知。skill 作者必须签字"我理解 XSS 风险"。

### `features`

仅 `print_css = true` 在 v0.2 实装(`@media print` 隐藏 settings/input/progress/footer,仅留 article)。

其它 flag 在 v0.2 仅占位:UI 显示按钮但 disabled, hover 提示 "v0.3 ETA"。

## Sub-schema 校验 (composer 强制)

- `render.output_form`: 必须是三个值之一
- `render.template_html`: 字符串(允许空)
- `render.css_lock`: 字符串(允许空)
- `render.data_binding`: 必须以 `$.steps.<id>.output` 开头, `<id>` 必须是 `llm_pipeline` 中存在的 step id
- `render.sanitizer`: 必须三个值之一; **没有默认值** — 缺省视为 IR 无效
- `render.features`: 对象, 至少含 `print_css`(布尔)
- `browser_runtime.image_adapter`: 必须是 null(template-html 不用 image API)

## v0.2 不做(留 v0.3+)

- ❌ TOC / 脚注 / syntax-highlight / 导出 PDF
- ❌ 多文档/zip 输出
- ❌ 服务端渲染回 markdown(只有 LLM → markdown → HTML 单向)

## 与 image-deck 的边界

| 字段 | image-deck | template-html |
|---|---|---|
| `static_assets` | ✅ 必填(灵魂) | ❌ 不应有 |
| `iterator` | ✅ 必填(slides) | ❌ 不应有(单文档输出, 多 section 是数据不是 iterator) |
| `per_item` | ✅ | ❌ |
| `image_adapter` | ✅ openai-images-compat | ❌ null |
| `output_form` | ❌ | ✅ |
| `template_html` | ❌ | ✅ 可选 |
| `sanitizer` | ❌ | ✅ 必填 |

如果 IR 同时含 image-deck 字段与 template-html 字段 → composer 拒绝(违反"一个 skill 一个 ir_kind")。
