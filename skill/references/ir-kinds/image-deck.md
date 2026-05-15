# IR kind: `image-deck`

> v0.2 sub-schema. 通用字段见 `../ir-core.md` §1-§6。本文档只描述 `render` 多态部分
> (§7) 在 `ir_kind: "image-deck"` 下的 shape。

## 适用场景

- 输入(文章/大纲/主题) → LLM 拆解 → 一个 "slides" array → 每张 slide 调一次图像 API → PNG 网格
- 例: `ian-handdrawn-ppt`(中文手绘技术 PPT)、`guizang-ppt 配图分支`

## 灵魂字段: `render.static_assets`

image-deck 与其它 kind 的最大区别: **它有 `static_assets`**。这一组字段是
"风格锚"——必须 verbatim inline 进 HTML,不能 paraphrase。

## `render` shape

```jsonc
"render": {
  "static_assets": {
    "style_lock":         "...verbatim text block from references/prompt-patterns.md...",
    "role_locks": {
      "cover": "...Page-role-cover...",
      "body":  "...Page-role-body..."
      // 其它角色名允许
    },
    "reference_clauses": [
      "...optional verbatim style-anchor text..."
    ],
    "archetypes": [
      "cover-metaphor", "single-concept", "left-right-contrast",
      "horizontal-process", "circular-mechanism", "branching-map",
      "classification-map", "matrix-table", "main-metaphor", "takeaway"
    ],
    "theme_tokens": {
      "paper":  "#FBFAF5",
      "ink":    "#111111",
      "size_by_role": { "cover": "1536x1024", "body": "1536x1024" }
    }
  },

  "iterator":  "$.steps.<step_id>.output.slides",   // ★ v0.2: 路径前缀
                                                      // 由 llm_pipeline 命名空间决定
                                                      // 单 step pipeline 通常是
                                                      // "$.steps.plan.output.slides"
  "per_item": {
    "prompt_template": "Use case: ...\nApply the deck style lock:\n{{static_assets.style_lock}}\nPage role lock:\n{{static_assets.role_locks[item.role]}}\nTitle exactly: {{item.title}}\nArchetype: {{item.archetype}}\nMain point: {{item.main_point}}\nComposition:\n{{item.composition}}\nRequired text only:\n{{#item.required_text}}- {{.}}\n{{/item.required_text}}",
    "size_by_role": { "cover": "1536x1024", "body": "1536x1024" },
    "api":          "openai-images-compat",          // 见 ../adapters.md
    "endpoint_mode":"generations" | "edits"          // 见下文
  }
}
```

## `iterator` 语义 (v0.2)

`$.steps.<step_id>.output.slides` 表示"在 LLM pipeline 第 `<step_id>` step 的 output
里取 `slides` 数组"。运行时 composer 注入的 `state.steps[<step_id>].output` 是该 step
解析后的 JSON。

单 step pipeline → 通常 `$.steps.plan.output.slides`。

## `per_item.prompt_template` 占位符命名空间

| 命名空间 | 含义 |
|---|---|
| `{{static_assets.X}}` | 全局,从 IR.render.static_assets |
| `{{item.X}}` | 每次迭代,从 iterator 当前元素 |
| `{{#item.list}}{{.}}{{/item.list}}` | 数组迭代(Mustache-lite) |
| `{{total}}` | iterator 数组总长 |

特殊: `{{static_assets.role_locks[item.role]}}` 用 `item.role` 字段动态选 role_lock;
mustache-lite 实现见 `templates/skeleton.html`。

## `per_item.api`

固定 `openai-images-compat`(v0.2)。其它 image API 在 v0.3 才加。

## `endpoint_mode`

| 模式 | URL | 何时用 |
|---|---|---|
| `generations` | `/images/generations` | OpenAI 原生 / 大多数兼容 endpoint |
| `edits` | `/images/edits` | 不支持 generations 的 endpoint(例 `image.token-recyclebin.com`)。前端会自动构造一张 blank PNG 作为 reference |

`endpoint_mode` 是 IR 默认;终端用户可以在 Settings 切换。

## Sub-schema 校验 (composer 强制)

- `render.static_assets.style_lock`: 字符串(允许空,但字段必须存在 — composer 无条件读)
- `render.static_assets.role_locks`: 对象,key 必须包含 `iterator` 数组里所有出现的 `item.role` 值
- `render.static_assets.archetypes`: 字符串数组(允许空)
- `render.static_assets.theme_tokens.size_by_role`: 必须覆盖 `iterator` 数组里所有出现的 `item.role` 值
- `render.iterator`: 必须以 `$.steps.<id>.output.` 开头, 其中 `<id>` 必须是 `llm_pipeline` 中存在的 step id
- `render.per_item.prompt_template`: 字符串, 至少包含一个 `{{item.X}}` 占位符
- `render.per_item.api`: 必须是 `"openai-images-compat"`
- `render.per_item.endpoint_mode`: `"generations"` 或 `"edits"`
- `browser_runtime.image_adapter`: 必须不为 null

## v0.1 兼容性

`ian-handdrawn-ppt` v0.1 IR 走 migration(见 `../ir-core.md` v0.1→v0.2 表)后直接落到本 schema。
没有任何字段语义改变,只是位置移到 `render.` 下,iterator 路径加前缀。
