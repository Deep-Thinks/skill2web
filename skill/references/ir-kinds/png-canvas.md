# IR kind: `png-canvas`

> v0.2 sub-schema. 通用字段见 `../ir-core.md` §1-§6。本文档描述 `render` 多态部分
> (§7) 在 `ir_kind: "png-canvas"` 下的 shape。

## 适用场景

- 输入 → LLM 出**一段** image prompt → 调**一次**图像 API → 输出**一张** PNG
- 例: `guizang-ppt 封面分支`(21:9 / 1:1 / 3:4 / 16:9 单张封面)、独立海报 / 配图

## 与 `image-deck` 的关键差异

| 字段 | image-deck | png-canvas |
|---|---|---|
| LLM 输出形态 | 多张 slides 数组 | 单段 image prompt(或单 spine) |
| `render.iterator` | 必填 | **不需要** |
| `render.per_item` | 必填 | **不需要**(用 top-level `prompt_template` 等) |
| `render.static_assets.role_locks` / `archetypes` | 必填(页间一致性) | **不需要** |
| `render.canvas_size` | 由 `size_by_role` 推 | **必填**(单图固定尺寸) |
| 输出图片数 | N (= LLM 输出数组长度) | **1** |

## `render` shape

```jsonc
"render": {
  "canvas_size":     "1024x1536",          // 单图固定尺寸 (例 21:9 1536x768, 1:1 1024x1024, 3:4 1024x1536, 16:9 1536x864)

  "static_assets": {                       // 比 image-deck 简化: 无 role_locks / archetypes
    "style_lock":        "...",
    "reference_clauses": [ "..." ]
  },

  "prompt_template": "套用 style_lock + reference_clauses + 用户输入 → 单图 prompt。\n占位符:\n  {{static_assets.style_lock}}\n  {{static_assets.reference_clauses.0}}\n  {{steps.<step_id>.output.<field>}}\n  {{input.<key>}}",

  "data_binding":    "$.steps.<step_id>.output",  // 当 prompt_template 引用 LLM 输出时

  "api":             "openai-images-compat",
  "endpoint_mode":   "generations" | "edits",     // png-canvas 默认 "generations"(单图无需 reference);DESIGN §12.4

  "compositing":     "none" | "text-overlay" | "image-merge",  // v0.2 仅支持 "none"
  "fonts":           []                    // 仅 compositing != "none" 用, v0.2 不实现
}
```

## 字段语义

### `canvas_size`

字符串 `"<W>x<H>"`,直接传给图像 API。常用比例:

| 比例 | 推荐尺寸 | 备注 |
|---|---|---|
| 1:1 (方图) | `1024x1024` | OpenAI / DALL-E / gpt-image-2 都支持 |
| 21:9 (超宽封面) | `1536x768`(≈ 21:10)或 `2520x1080`(精确 21:9, 部分 endpoint 不支持) | gpt-image-2 不原生支持 21:9, 用 1536x1024 代;v0.3 可加客户端 canvas crop |
| 16:9 | `1536x864`(精确)或 `1536x1024`(降级) | 同上 |
| 3:4 (人像) | `1024x1536` | 海报常用 |

### `static_assets`

只有两个字段(对比 image-deck 五个):
- `style_lock`: 风格锚文本(verbatim inline)
- `reference_clauses`: 数组,文字 reference 块(verbatim inline)

**没有 `role_locks` / `archetypes` / `theme_tokens.size_by_role`** — 单图无角色概念,大小由 `canvas_size` 直接定。

### `prompt_template`

占位符命名空间(同 image-deck `per_item.prompt_template`,但少了 `{{item.X}}` 与 `{{total}}`):

| 命名空间 | 说明 |
|---|---|
| `{{static_assets.X}}` | 全局,从 `render.static_assets` |
| `{{steps.<id>.output.X}}` | 由 `data_binding` 定位的 LLM 输出字段 |
| `{{input.<key>}}` | 用户表单输入 |

### `data_binding`

可选。若 `prompt_template` 直接引用 `{{steps.X.output.Y}}` 形式,可不填(skeleton 的 mustache-lite 解 dotted path)。
若想让 prompt_template 用更短的 `{{Y}}` 形式, 设 `data_binding = "$.steps.X.output"` 让 root 直接挂上去。

### `endpoint_mode` 默认 (DESIGN §12.4 决议)

- `generations`: png-canvas 默认。单图无需 reference image, 直接 from-scratch 生成。
- `edits`: 仅当 endpoint(例 `image.token-recyclebin.com`)只支持 `/edits` 时, 前端会自动构造一张 blank PNG 作为 reference。

### `compositing` (v0.2 占位)

| 值 | 状态 | 用途 |
|---|---|---|
| `none` | ✅ 仅支持 | 单图 PNG 直接呈现 |
| `text-overlay` | 🔬 v0.3 占位 | 在生成的图上叠加可选标题 / 字幕(用 canvas fillText) |
| `image-merge` | 🔬 v0.3 占位 | 多图叠加(头像 + 背景 + Logo) |

v0.2 时 `compositing != "none"` → composer 拒绝。

## Sub-schema 校验 (composer 强制)

- `render.canvas_size`: 字符串, 形如 `<W>x<H>`, 两数都是正整数
- `render.static_assets.style_lock`: 字符串(允许空)
- `render.static_assets.reference_clauses`: 字符串数组(允许空)
- `render.prompt_template`: 字符串, 至少有一个占位符
- `render.api`: 必须是 `"openai-images-compat"`
- `render.endpoint_mode`: `"generations"` 或 `"edits"`
- `render.compositing`: v0.2 必须是 `"none"`(其它值拒绝)
- `browser_runtime.image_adapter`: 必须不为 null

## 与 image-deck 的边界

png-canvas IR 不应有 `iterator` / `per_item` / `archetypes` / `role_locks` / `size_by_role`。如果上游 skill 真的要"多张相关图",改用 `image-deck`(N=1 也合法)。
