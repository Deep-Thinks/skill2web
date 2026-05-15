# Hero Case 1 v0.2 重编译笔记

> 2026-05-15。这份文件是 DESIGN-v0.2.md §13 "Phase A 验收" 的回归证据。

## 输入

- v0.1 IR: `skill/examples/ian-handdrawn-ppt.ir.v0.1.json`(归档,源自 v0.1 hero case)
- 走 `skill/migrate_v01_to_v02.py` → v0.2 IR: `skill/examples/ian-handdrawn-ppt.ir.json`
- 走 `skill/compose.py` → 本目录 `index.html`

## Migration 转换核对

| v0.1 字段 | v0.2 字段 | 实际状态 |
|---|---|---|
| `ir_version: "0.1"` | `ir_version: "0.2"` | ✅ |
| `ir_kind: "image-deck"` | 同 | ✅ |
| `static_assets.*` (top-level) | `render.static_assets.*` | ✅ 整块下移 |
| `llm_phase: { ... }` | `llm_pipeline: [ { id: "plan", uses: [], ...llm_phase } ]` | ✅ |
| `render_phase: { kind, iterator, per_item }` | `render: { iterator, per_item }` | ✅ kind 升 top-level |
| `render_phase.iterator: "$.slides"` | `render.iterator: "$.steps.plan.output.slides"` | ✅ |
| `user_prompt_template` 中的 `{{scenario}}` 等 | `{{input.scenario}}` 等 | ✅ |

## 行为等价性核对

v0.2 composer 输出与 v0.1 hero case (../ian-handdrawn-ppt/index.html) 的 JS 行为对照:

| 函数 / 行为 | v0.1 位置 | v0.2 位置 | 等价 |
|---|---|---|---|
| `loadSettings` / `saveSettings` / `clearSettings` | 行 432-485 | skeleton.html | ✅ |
| `bindUI` / `startGenerate` / `collectFormValues` | 行 406-557 | skeleton.html | ✅(input form 由 IR 生成,字段一致) |
| `callLLM` | 行 581-608 | adapters/openai-chat-compat.js | ✅ |
| `callImageAPI` / `callImageGenerations` / `callImageEdits` / `imageFetch` / `makeBlankPng` / `blobToBase64` | 行 752-831 | adapters/openai-images-compat.js | ✅ |
| `extractJson` / `jsonpathLite` / `mustacheLite` / `lookupCtx` / `escapeForPrompt` | 行 610-653 | skeleton.html | ✅(mustache-lite 增强了 dynamic-key dereference 与 nested ctx,向下兼容 v0.1 模板) |
| `initSlideCards` / `renderSlideCard` / `updateSlideCard` | 行 656-705 | blocks/image-deck.html | ✅ |
| `generateAllImages` / `runWithConcurrency` / `processSlide` | 行 707-749 | blocks/image-deck.html (`runWithConcurrency` 移到 skeleton 复用) | ✅ |
| `downloadOne` / `sanitize` / `downloadAllImages` / `retryOne` / `retryFailedSlides` / `showPrompt` | 行 834-871 | blocks/image-deck.html | ✅ |
| `log` / `escapeHtml` / `markStep` / `resetStep` | 行 488-497, 559-564 | skeleton.html | ✅(`markStep` 现在以 `ps-<step_id>` 为 id, 不再硬编 step-plan/step-images) |

**关键增量(v0.2 强化,不是回归)**:
- progress 区块 step 列表自动按 `llm_pipeline` 长度生成,1-N step 都能渲染
- `runLlmStep()` 按 `step.json_mode` 解析 LLM 输出, json_mode="off" 时把 `text` 包成 `output.text` (template-html 用得到)
- `state.steps[<id>].output` 命名空间替代了 v0.1 的 `state.blueprint`(等价但 namespaced)
- input form values 命名空间从 `{{key}}` 升 `{{input.<key>}}` (run-time mustache-lite 双语法都解析,但 IR 用 input. 前缀消歧义)

## 已知体验差异

- v0.1 progress 区块 hard-code "规划 spine (LLM)" + "生成图像 (并发)" 两行;
  v0.2 自动按 pipeline 生成,加上"渲染输出"一行。文案略变,行为不变。
- v0.1 `state.blueprint` 直接挂 LLM 输出;
  v0.2 `state.steps.plan.output` 命名 — render 阶段读 `RENDER_CONFIG.iterator = "$.steps.plan.output.slides"`,语义等价。

## 验收 (DESIGN-v0.2.md §13 v0.2 ship)

- ✅ JS 语法 OK (Node.js `new Function()` 通过, 713 行)
- ✅ 文件 < 100 KB (45 KB)
- ✅ 单 `<script>` 块, 无外部 CDN
- ✅ 页脚 attribution + skill2web 字样齐
- ⏳ 浏览器端到端跑通 — 由用户首次实测后回填(同 v0.1 hero case 的 LESSONS §五)

## 复现命令

```bash
# 从 v0.1 IR 升 v0.2
python3 skill/migrate_v01_to_v02.py skill/examples/ian-handdrawn-ppt.ir.v0.1.json /tmp/migrated.json

# 用 v0.2 composer 重编
python3 skill/compose.py skill/examples/ian-handdrawn-ppt.ir.json hero-cases/ian-handdrawn-ppt-v0.2/index.html

# 本地跑(浏览器端 CORS 风险见 v0.1 hero case LESSONS §五)
cd hero-cases/ian-handdrawn-ppt-v0.2/ && python3 -m http.server 8765
# 浏览器开 http://localhost:8765/
```
