# Design v0.2 — skill2web 升级到 core + plugin

Generated 2026-05-15
Status: APPROVED-WITH-CONDITIONS（已经 codex consult 续审一轮，scope 按反馈做了 4 处收敛；条件见下方 §11）
关系：在 `DESIGN.md` (v0.1) 基础上扩展。v0.1 文档不动，本文档负责描述 v0.1 → v0.2 的演化与裁剪。
独立审查：codex consult session `019e2743-1b49-7851-9015-c1aef7b7b645`（同一会话覆盖 v0.1 init review + v0.2 plan review）。

---

## 1. 升级目标（用户原话）

> "你检查一下 v0.1 的实现逻辑，它现在不能适配多种 skill，我想让它按照我们 plan 中的一样，适配几乎所有硬性工作流程的 skill。"

进一步澄清：

> "不太需要 Agent 能力的 skill，比较一次性输入输出，中间不需要有任何分叉路线、解决问题的，也就是说能把 skill 化成一个简单 workflow（判断逻辑等比较简单）的就可以。例如 gstack 这种就不行。"

用户点名要支持的三个上游 repo：

1. https://github.com/Yuan1z0825/nature-skills（9 个 skill）
2. https://github.com/op7418/guizang-ppt-skill（PPT 主流程 + 配图 + 封面三分支）
3. https://github.com/KKKKhazix/khazix-skills（4 个 skill）

---

## 2. v0.1 为什么不能适配多种 skill（根因诊断）

v0.1 在文档层提了 4 种 `render_phase.kind`（image-per-slide / template-html / pptx-canvas / png-canvas），但**代码与 IR 实质上和 image-deck 形状同构**。具体锁死点：

| 锁死点 | 位置 | 影响 |
|---|---|---|
| `ir_kind` 只能是 `"image-deck"` | `skill/references/ir-schema.md:48`、`skill/SKILL.md:174` | 其它 kind 直接拒绝 |
| `static_assets.{style_lock,role_locks,archetypes,theme_tokens}` 是 image-deck 专属字段，但被强制塞进 top-level IR | `ir-schema.md:82-110` | 文档 / 海报 / PPTX / 数据类 skill 没这层概念 |
| `llm_phase` 是单一对象，**不是 DESIGN.md 草案的 `llm_calls: [...]` 数组** | `ir-schema.md:148` | 凡需要 2-3 次 LLM 顺序调用的 skill 表达不了 |
| `templates/base.html` 整套 UI 流（slide 网格、image API 设置、`callImageAPI`、blank-PNG fallback）都是 image-deck 专写 | `templates/base.html:752-822` | 换 render 形状需重写 600+ 行 |
| `analyzer-checklist.md` 第 79-88 行硬拒非 `image-per-slide` kind | 同上 | 文档/海报/PPTX 全卡死在 Phase 2 |
| `lib-mapper.md` 把 **API adapter** 和 **render lib** 混在一张表 | `lib-mapper.md:32-73` | 两者演化逻辑不同（adapter 看 CORS / auth；lib 看 inline size / 语义等价性），混合后越改越乱 |

`hero-cases/ian-handdrawn-ppt/LESSONS.md` §2 其实已经预警："`static_assets` 是图像生成型 skill 的灵魂——但其他 kind 没这一层"。`TODO.md` v0.2 条目也写明"必须做第二个非 image-deck hero case，IR 才能真正泛化"。所以 v0.2 不是"补几个 kind"，而是**把 IR 从 image-deck-shaped 提升为 core + plugin**。

---

## 3. 目标 skill 形状归类（扫描三个 repo）

> 来源：general-purpose 子代理对三个上游 repo 的 README / SKILL.md 扫描，2026-05-15。

### 3.1 流程化、可适配（v0.2 编译目标）

| 上游 skill | 输出形态 | 最佳 kind | LLM 调用次数 | 关键依赖 |
|---|---|---|---|---|
| nature-polishing | 润色后 Markdown | template-html | 1 | 无 |
| nature-writing | 手稿章节 Markdown | template-html | 2-3 | 无 |
| nature-data | Data Availability 声明 | template-html | 1 | 无 |
| nature-response | Reviewer 回复信 | template-html | 2-3 | 无 |
| khazix-writer | 公众号长文 Markdown | template-html | 2-3 | 无 |
| guizang-ppt（主流程） | 单文件 HTML 横向翻页 deck | template-html（多段） | 2-3 | 模板已是 HTML，天然适配 |
| guizang-ppt（封面分支） | 21:9 / 1:1 / 3:4 / 16:9 单图封面 | png-canvas | 1 | 图像 API |
| guizang-ppt（配图分支） | 每页一张配图 | image-deck | 4+ | 图像 API |

### 3.2 必须拒绝（agent-shaped 或 browser-incompatible）

| 上游 skill | 拒绝原因 | 对应 refusal 类型 |
|---|---|---|
| nature-citation | 多轮 Crossref 检索 | `agent-shaped` |
| nature-academic-search | 本地 MCP server + 多源跨库 | `needs-local-server` + `agent-shaped` |
| neat-freak | 必须写盘修改 docs/memory | `needs-fs` |
| hv-analysis | 双线 Deep Research + PDF 渲染 | `agent-shaped` + `pdf-rendering-too-heavy` |
| nature-figure | matplotlib 多面板 SVG | `needs-python-matplotlib` |
| nature-reader | 重型 PDF 解析 | `large-input` + `pdf-parse-too-heavy` |
| nature-paper2ppt | 依赖 python-pptx 复杂版式 | **暂列 spike-gated**（见 §5.2 / §8.D） |
| aihot | 依赖私 SaaS API（aihot.virxact.com） | `private-api` |

---

## 4. 演化哲学

v0.2 是 **从单形状到组合架构** 的一次性重构，**不是**逐 kind 增量补丁。理由：

1. **IR shape 改了，UI 流就要拆**——这两件事必须一起做，否则 base.html 会成为 1500 行的 if/else 怪物。
2. **Analyzer 解锁要放最前面**——否则后续每加一个 kind 都要临时改 analyzer 的硬锁（codex Q4 直接指出过）。
3. **不做 DAG llm_pipeline，只做线性 pipeline**——DAG = 偷偷重建 agent runtime，超出"硬性工作流程"的承诺（codex Q3）。

但本 v0.2 **不追求一次抽五个 kind 全跑通**。codex Q5 指出"首批五 kind 全要"是范围失控；我们接受这一点，把 v0.2 拆为：

- **3 个完整支持的 kind**：image-deck（已有）+ template-html（最大用户面）+ png-canvas（低边际成本）
- **2 个 spike-gated kind**：pptx-canvas / data-table（spike 通过才进 v0.3，不通过就转化为 refusal 模板）

这是务实路线：覆盖目标 skill 的 ~80%（nature-polishing/writing/data/response、khazix-writer、guizang-ppt 三分支），把 nature-paper2ppt 与 aihot 这两条尾巴留给后续。

---

## 5. v0.2 完成定义

### 5.1 必须做（v0.2 ship 条件）

- ✅ **IR core schema**（universal 字段）+ **per-kind sub-schema** for image-deck / template-html / png-canvas
- ✅ **Linear `llm_pipeline: [...]`**（`uses` 只能引用前序 step）+ v0.1 → v0.2 IR migration（见附录 A）
- ✅ **Skeleton + blocks + adapters 模板拆分**
- ✅ **Analyzer kind router**（解除 image-per-slide 硬锁；按 kind 分发 sub-checklist）
- ✅ **运行环境等价性检查**（合并 `TODO.md` v0.1.1 条目）
- ✅ **新 refusal 类型**：`needs-headless-browser` / `needs-fs` / `needs-third-party-fetch` / `layout-too-complex` / `private-api`（已部分存在，统一文案）
- ✅ **现 hero case 回归**：`ian-handdrawn-ppt` 用 v0.2 重新编译，输出语义等价于 v0.1
- ✅ **第二个 hero case**：手工编译一个 template-html skill（候选：`nature-polishing` 或 `khazix-writer`），先于自动 compiler 实现

### 5.2 Spike-gated（spike 通过才进 v0.2，否则推迟到 v0.3 或转 refusal）

- 🔬 **pptx-canvas spike**：用 `nature-paper2ppt` 真实 2-3 页输出，手写 pptxgenjs 复刻。判定标准见 §11.S1。
- 🔬 **data-table minimal spike**：仅"LLM 输出 JSON → 渲染表格 → CSV/JSON 导出"的最小形态，**禁用任何外部 SaaS / 私 API**。候选验收 skill：构造一个无依赖的 mock skill。`aihot` 直接进 refusal。判定标准见 §11.S2。

### 5.3 明确不做（v0.2 范围外，留给 v0.3+）

- ❌ frontend-design skill 集成（保留 DESIGN.md v0.2 计划，但实际推到 v0.3）
- ❌ DAG llm_pipeline（仅线性；分叉合流推到 v0.3 或拒绝）
- ❌ SaaS / 私 API adapter（CORS + 鉴权两座大山，v0.2 不碰）
- ❌ Local Python reverse proxy mode（保留 TODO.md v0.3 条目不变）
- ❌ 同一 IR 同时承载多 kind（guizang-ppt"主输出 + 旁挂资源"形态，要求用户拆成两次编译）

---

## 6. IR Schema v0.2

### 6.1 Top-level（universal）

```jsonc
{
  "ir_version": "0.2",
  "ir_kind":    "image-deck" | "template-html" | "png-canvas"
              | "pptx-canvas"   // v0.2 spike-gated
              | "data-table",   // v0.2 spike-gated

  "skill_meta":      { /* 同 v0.1, 字段不变 */ },
  "input_schema":    [ /* 同 v0.1 */ ],

  "llm_pipeline":    [ /* 数组化，详见 §6.2 */ ],

  "browser_runtime": {
    "llm_adapter":       "openai-chat-compat" | "anthropic-chat" | ...,
    "image_adapter":     "openai-images-compat" | null,   // 仅 image-deck / png-canvas 用
    "default_endpoints": { ... },
    "concurrency":       3,
    "timeout_ms":        { "llm": 120000, "image": 180000 },
    "retry":             { "llm": 0, "image": 1 },
    "extra_libs":        []        // 例: ["pptxgenjs@3"]，仅 spike-gated kind 用
  },

  "error_ux":    { /* 同 v0.1, 增加 cors / json_parse / kind_unsupported */ },
  "attribution": { /* 同 v0.1, 强制 */ },

  "render":      { /* polymorphic — shape 取决于 ir_kind, 详见 §6.3-§6.5 */ }
}
```

### 6.2 `llm_pipeline` 线性约束

```jsonc
[
  {
    "id":                     "intake",         // kebab-case, 唯一
    "model_hint":             "deepseek-chat",
    "temperature":            0.4,
    "json_mode":              "prompt-only",
    "system_prompt_template": "...",
    "user_prompt_template":   "【内容】{{input.content}}",
    "uses":                   [],               // 第一步必空
    "expected_output_schema": { /* JSON Schema */ }
  },
  {
    "id":                     "plan",
    "uses":                   ["intake"],       // 只允许引用更早的 step
    "user_prompt_template":   "前序结果：{{steps.intake.output.summary}}\n规划 N 张幻灯片...",
    /* ... */
  }
]
```

**硬约束（composer 强制校验）**：
- `uses` 只能包含**严格在前**的 step id（拓扑序由数组顺序决定，禁止显式拓扑排序需求）
- 同一 step 内 `uses` 数组**禁止循环**
- 每个 step 的 `expected_output_schema` 必须填，前端做 JSON 解析失败时落到 `error_ux.json_parse`
- 任意一步失败：默认整条 pipeline 终止；UI 显示"第 N 步失败 + 看 prompt + 重试本步"按钮（不向上重试）
- 1 step 是合法的，等价于 v0.1 的 `llm_phase` 单对象

**禁止的**：`uses` 引用兄弟 step 之间分叉 / 合流 / 条件跳转。任何这种需求一律视为 agent-shaped，由 analyzer 在 Phase 2 拒绝。

### 6.3 `render.kind = "image-deck"`（沿用 v0.1）

```jsonc
"render": {
  "static_assets": {
    "style_lock":       "...",
    "role_locks":       { "cover": "...", "body": "..." },
    "reference_clauses":[ "..." ],
    "archetypes":       [ "..." ],
    "theme_tokens":     { "paper", "ink", "size_by_role" }
  },
  "iterator":           "$.steps.plan.output.slides",   // ★ 路径从 LLM 输出根改为 steps.<id>.output
  "per_item": {
    "prompt_template":  "...",
    "size_by_role":     { ... },
    "api":              "openai-images-compat",
    "endpoint_mode":    "generations" | "edits"
  }
}
```

**与 v0.1 的差异**：
- `iterator` 路径前缀从 `$.slides` 改为 `$.steps.<id>.output.slides`，因为 llm_pipeline 数组化后输出有命名空间
- 其它字段保持 byte-equivalent，已存档的 `ian-handdrawn-ppt.ir.json` 走自动 migration

### 6.4 `render.kind = "template-html"`（新）

```jsonc
"render": {
  "output_form":   "markdown" | "html-fragment" | "full-document",
  "template_html": "<article>\n  <h1>{{steps.plan.output.title}}</h1>\n  {{#steps.plan.output.sections}}\n    <section>\n      <h2>{{title}}</h2>\n      <div data-md>{{body}}</div>\n    </section>\n  {{/steps.plan.output.sections}}\n</article>",
  "css_lock":      "/* skill 作者已经调好的 CSS，verbatim inline */",
  "data_binding":  "$.steps.plan.output",         // 模板上下文根
  "sanitizer":     "dompurify-strict" | "dompurify-relaxed" | "none-trust",
  "features":     {                              // 可选能力开关
    "toc":            false,
    "footnotes":      false,
    "syntax_highlight": false,
    "print_css":      true,
    "export_pdf":     false                       // v0.2 暂不实现，flag 占位
  }
}
```

**设计决策**：
- `output_form` 是 discriminator：composer 据此决定是否需要 inline `marked.js`（12KB gzip）
- `sanitizer` 必须显式选择，**没有默认值**。LLM 输出直插 DOM 是 XSS 路径；composer 在 USER GATE 3 之外加一个 sanitizer-choice 子提问
- `features` 字段允许后续扩展，v0.2 只承诺 `print_css`；其它 flag 列出但**只生成占位 UI**（按钮 disabled + 提示"v0.3"）

### 6.5 `render.kind = "png-canvas"`（新）

```jsonc
"render": {
  "canvas_size":     "1024x1536",        // 单图固定尺寸
  "static_assets": {                     // 比 image-deck 简化：无 role_locks / archetypes
    "style_lock":        "...",
    "reference_clauses": [ "..." ]
  },
  "prompt_template": "套用 style_lock + reference_clauses + 用户输入 → 单图 prompt",
  "api":             "openai-images-compat",
  "endpoint_mode":   "generations" | "edits",
  "compositing":     "none" | "text-overlay" | "image-merge",  // v0.2 只支持 "none"
  "fonts":           []                  // 仅 compositing != "none" 时使用，v0.2 不实现
}
```

**与 image-deck 的关键差异**：
- 无 `iterator` / `per_item` —— png-canvas **只产一张图**
- 无 `role_locks` / `archetypes` —— 不需要"页间一致性"概念
- `compositing="text-overlay"` 是 codex Q2 指出的扩展点（v0.2 暂不做，flag 占位）

### 6.6 `render.kind = "pptx-canvas"` / `"data-table"`（spike-gated，schema 草案）

**仅在 §11.S1 / §11.S2 spike 通过后才落 schema 终稿。** 当前先列形状草案，但**不进 SKILL.md / examples/**：

```jsonc
// pptx-canvas 草案（spike 未过前 freeze）
"render": {
  "pptx_layout":    { "size": "16:9", "master": {...} },
  "iterator":       "$.steps.plan.output.slides",
  "slide_mapper": [
    { "match": { "role": "cover" }, "ops": [ {"type":"text", "text":"{{title}}", "x":0.5, "y":0.3, /* ... */} ] }
  ],
  "extra_libs":     ["pptxgenjs@3"]
}

// data-table 草案（spike 未过前 freeze）
"render": {
  "schema":   [ {"key":"date","type":"date"}, {"key":"title","type":"string"} ],
  "iterator": "$.steps.plan.output.items",
  "exports":  ["csv","json"],
  "transform":{ "kind":"none" }   // 严禁 "sql" 模式进 v0.2 — duckdb-wasm 太重
}
```

---

## 7. Templates 拆分

```
skill/
├── SKILL.md                          # 重写 Phase 3 / Phase 5 / Status 三节
├── references/
│   ├── analyzer-checklist.md         # 解除 kind 锁；新增 step 9 运行环境等价性；新 refusal 文案
│   ├── compiler-workflow.md          # 重写 Phase 5（组装器，不再是单模板填充）
│   ├── ir-core.md                    # 新：universal 字段（§6.1 + §6.2）
│   ├── ir-kinds/
│   │   ├── image-deck.md             # 从现 ir-schema.md 抽出 image-deck 专属内容
│   │   ├── template-html.md          # 新（§6.4）
│   │   ├── png-canvas.md             # 新（§6.5）
│   │   ├── pptx-canvas.md            # spike-gated 草案（spike 通过才 release）
│   │   └── data-table.md             # spike-gated 草案
│   ├── adapters.md                   # 新：API 调用契约（CORS / auth），从 lib-mapper 拆出
│   └── render-libs.md                # 新：inline JS lib（marked.js / pptxgenjs / 等），从 lib-mapper 拆出
├── templates/
│   ├── skeleton.html                 # 新：header / settings / footer / mustache-lite / loadSettings / pipeline runner
│   ├── blocks/
│   │   ├── image-deck.html           # 从现 base.html 抽 slide-grid + image API
│   │   ├── template-html.html        # 新：marked.js inline + DOMPurify inline + 单/多段渲染区 + 打印
│   │   ├── png-canvas.html           # 新：canvas + image API + 下载 PNG
│   │   ├── pptx-canvas.html          # spike 通过后才落
│   │   └── data-table.html           # spike 通过后才落
│   └── adapters/
│       ├── openai-chat-compat.js     # callLLM() ~25 行，组装时 inline
│       ├── anthropic-chat.js
│       └── openai-images-compat.js
└── examples/
    ├── ian-handdrawn-ppt.ir.json     # v0.1 IR，保留作为 image-deck 范例 + migration 测试输入
    ├── nature-polishing.ir.json      # 新（手工 hero case 输出）
    └── guizang-cover.ir.json         # 新
```

**Composer 的新职责**：不再是"单模板 + Mustache 填空"，而是**三步组装**：
1. 取 `skeleton.html` 为骨架
2. 按 `ir_kind` 选 `blocks/<kind>.html` 替换 skeleton 的 `<!-- BLOCK -->` 标记
3. 按 `browser_runtime.{llm,image}_adapter` 选 `adapters/*.js` inline 到 skeleton 的 `<script>` 段

---

## 8. Phase 顺序（按 codex Q4 调整）

> 关键变化：F0（analyzer 解锁）放最前；spike 在主线之前或与主线并行；第二个 hero case 不能跳过。

### Phase F0 — Analyzer kind router + 运行环境等价性检查（0.5-1 天）

**先做的理由**：B-E 任何一步加新 kind，analyzer 都需要解锁。若放最后，期间每加一 kind 都要临时改硬锁，引入 throwaway code。

- 解除 `analyzer-checklist.md:79-88` 的"仅 image-per-slide"硬锁
- 加 step 9：运行环境等价性（合并 `TODO.md` v0.1.1）
- 加 refusal 类型：`needs-headless-browser` / `needs-fs` / `needs-third-party-fetch` / `layout-too-complex` / `private-api`
- 验收：手动跑 analyzer 对以下 skill 给出正确判定
  - ✅ compilable：nature-polishing → template-html、guizang-ppt 封面 → png-canvas、ian-handdrawn-ppt → image-deck
  - ❌ refuse：neat-freak / nature-figure / nature-academic-search / aihot

### Phase A — Refactor core，**不增加 kind**（1-2 天）

- 抽 `ir-core.md` + `ir-kinds/image-deck.md`
- 把 `templates/base.html` 拆成 `skeleton.html` + `blocks/image-deck.html` + `adapters/*.js`
- composer 改为组装器
- 写 v0.1 → v0.2 IR migration（详见附录 A）
- 验收：`ian-handdrawn-ppt` 用 v0.2 重编译，输出 JS 语义等价（diff 容忍空白/注释，但 inline 函数名 / 行为不变）

### Hero Case 2 — 手工编译 template-html skill（0.5-1 天，**不写 compiler 代码**）

候选：`nature-polishing`（最小 LLM 调用次数，验证 IR 通用性）或 `khazix-writer`（多步 LLM，验证 pipeline 数组）。**默认选 nature-polishing**。

- 在 `hero-cases/<skill-name>/` 手工写一份单文件 HTML，跑通端到端
- 输出 `LESSONS.md`：哪些字段确实通用、哪些是 template-html 专属
- 该 LESSONS.md 是 Phase B 的设计输入

### Phase B — template-html plugin（2-3 天）

- 写 `ir-kinds/template-html.md`、`blocks/template-html.html`
- inline marked.js + DOMPurify（约 30KB gzip 合计）
- 实现 `sanitizer` 三种模式
- 实现 `features.print_css`；其它 features flag 仅占位
- 验收：自动编译 nature-polishing + guizang-ppt 主流程，与 hero case 2 手工版本语义等价

### Phase C — png-canvas plugin（0.5-1 天）

- 写 `ir-kinds/png-canvas.md`、`blocks/png-canvas.html`
- 复用 `adapters/openai-images-compat.js`
- 验收：自动编译 guizang-ppt 封面分支，跑通端到端

### Phase D-spike — pptx-canvas feasibility（**1 天 spike，过了才进 §8.D-impl**）

- 用 nature-paper2ppt 真实 2-3 页 PPTX 输出，**手工** 写 pptxgenjs 代码复刻
- 判定标准见 §11.S1
- 不过：把 pptx-canvas 从 v0.2 移出，添加 `refusal: pptx-too-complex` 模板，nature-paper2ppt 转 refuse 但建议"改 SKILL.md 让 LLM 输出 image-deck 风格 deck"

### Phase E-minimal — data-table 最小形态（1 天）

- 构造一个不依赖外部 SaaS 的 mock skill（"输入要点列表 → LLM 整理成表格 → 渲染 + CSV/JSON 导出"）
- 写 `ir-kinds/data-table.md`（仅 `transform.kind = "none"` 分支）、`blocks/data-table.html`
- 判定标准见 §11.S2
- aihot 直接 refuse: `private-api`

### Phase D-impl — pptx-canvas 实装（仅 D-spike 通过才执行，3-5 天）

- 落 `ir-kinds/pptx-canvas.md` 终稿、`blocks/pptx-canvas.html`
- inline pptxgenjs（~340KB gzip）
- 实现 slide_mapper DSL（仅 text / image / shape 三种 op；layout primitives 受限）
- 验收：自动编译 nature-paper2ppt，输出 .pptx 在 PowerPoint / Keynote 中能打开且不丢失主要内容

---

## 9. 配套非代码变更

- `lib-mapper.md` 拆分为 `adapters.md` + `render-libs.md`（Phase A）
- `ir-schema.md` 拆分为 `ir-core.md` + `ir-kinds/*.md`（Phase A）
- `TODO.md`：v0.1.1 analyzer 加强条目合并到 Phase F0；v0.2 第二个 hero case 改为 §8 Hero Case 2 指定路径
- `SKILL.md`：重写 Status 节、Phase 3 / 5 描述
- `compiler-workflow.md`：Phase 5 composer 描述改为"skeleton + block + adapters 三步组装"
- `examples/` 每个**完整支持**的 kind 至少一份 ref IR

---

## 10. 与 v0.1 的兼容策略

**断 v0.1 IR**，写一次性 migration。理由（codex Q3）：保留双 schema 会让 composer 长期维护两套模板语义，得不偿失。

迁移规则见附录 A。`examples/ian-handdrawn-ppt.ir.json` 在 Phase A 通过 migration 升到 v0.2，作为 regression 基线。

---

## 11. Spike 判定标准（v0.2 完成定义的硬门槛）

### 11.S1 pptx-canvas spike 判定（Phase D-spike）

**Pass 条件（全满足才进入 D-impl）**：
- 用 nature-paper2ppt 的真实 2-3 页输出作为基准（含 1 张封面 + 1-2 张正文 + 至少 1 张图片插入）
- 手写 pptxgenjs 代码（不超过 200 行）复刻这些页，导出的 .pptx 在 **PowerPoint** 与 **Keynote** 两个 viewer 中：
  - 主要文字 / 标题 / 图片位置不丢
  - 字体回退在中文文本上可接受（允许字体替换，但不允许乱码或字号崩坏）
  - 用户可以在 PowerPoint 中**继续编辑**（不是死图）

**Fail 处置**：
- pptx-canvas 从 §5.1 移到 §5.3（明确不做）
- 加 `refusal: pptx-too-complex`
- 给上游 skill 作者一份"如何把 PPTX skill 改成 image-deck-shape"的建议（写进 `references/refusal-recipes.md`，新文件）

### 11.S2 data-table minimal spike 判定（Phase E-minimal）

**Pass 条件**：
- 构造 mock skill 完整跑通：用户填要点列表 → 1 次 LLM 调用 → 输出 JSON array → 渲染 sortable table → 一键导出 CSV + JSON
- 全程 inline 实现，无外部 JS lib（手写 ~50 行 table + ~30 行 CSV）
- HTML 总大小 < 60KB

**Fail 处置**：
- data-table 从 §5.1 移到 §5.3
- 在 analyzer 加 `kind-not-yet-supported: data-table` 的 v0.3 ETA 文案

---

## 12. Open Questions（v0.2 实施期间需要回答）

1. **Hero Case 2 选 nature-polishing 还是 khazix-writer？** 默认 nature-polishing；若 Phase A 完成时发现 1-step pipeline 表达力够不上"真实 template-html skill"，切到 khazix-writer 验证多步 pipeline。
2. **template-html 的 sanitizer 默认值？** 提议 `dompurify-strict`，但 guizang-ppt 主流程的模板里含交互 JS（翻页），strict 会破。需要在 Phase B 实测后定。
3. **是否给 v0.2 加一个"compile preview 模式"？** 让 skill 作者先看 IR + 拼出的 HTML 草图，再走完整 4 个 user gate？codex 没提，但 Phase B 期间预计会撞到——留待 Phase B 中后期决定。
4. **png-canvas 与 image-deck 共用 image_adapter，但 endpoint_mode 选择策略是否要按 kind 区分默认值？** 当前 image-deck 默认 `edits`（因为 token-recyclebin.com 不支持 generations）；png-canvas 单图建议默认 `generations`。需在 §6.5 sub-schema 终稿前确认。

---

## 13. Success Criteria

**v0.2 ship 条件**：
- 至少 3 个上游 skill 通过 v0.2 编译并跑通端到端：1 个 image-deck（回归）+ 1 个 template-html（新）+ 1 个 png-canvas（新）
- analyzer 正确拒掉至少 3 个 agent-shaped / browser-incompatible skill
- 至少 1 个不懂 agent 的测试者打开 template-html 输出，5 分钟内用起来

**v0.2 "成功但有妥协" 条件**：
- 上述 ship 条件全部满足
- pptx-canvas spike fail，明确转 refusal（不算失败，是诚实）
- data-table 最小形态做出来（即使没有真实上游 skill 验证）

**v0.2 "失败" 条件**（要回头反思）：
- Phase A 重构破坏 ian-handdrawn-ppt 回归
- Phase B 自动编译输出与 hero case 2 手工版本语义不等价（IR 抽错了）
- Phase D-spike 通过了，但 D-impl 落地时发现复杂度超估 2x

---

## 14. Codex Review 反馈消化记录

Session: `019e2743-1b49-7851-9015-c1aef7b7b645`（同一 session 续接 v0.1 init review）

| Codex Q | 原文要点 | 是否采纳 | 落地位置 |
|---|---|---|---|
| Q1 跳过 hero case 风险 | 风险排序 pptx > template-html > data-table > png-canvas > image-deck；可以跳过但不能五个一起抽 | ✅ 完全采纳 | §8 加入 Hero Case 2；§5.2 pptx / data-table 改 spike-gated |
| Q2 sub-shape 字段够不够 | template-html 缺 TOC/sanitizer/CSS；pptx-canvas DSL 必经 spike；pptxgenjs 真问题是语义不等价 | ✅ 完全采纳 | §6.4 加 sanitizer 与 features；§6.5 加 compositing 占位；§11.S1 spike 判定标准 |
| Q3 llm_pipeline DAG 代价 | DAG = 偷偷做 agent runtime；建议线性 + uses 只引前序；直接断 v0.1 IR | ✅ 完全采纳 | §6.2 硬约束；§10 断 v0.1 IR + migration；附录 A |
| Q4 Phase 顺序 | F (analyzer) 必须 F0 最前；新顺序 F0 → A → B → C → E-minimal → D-spike | ✅ 完全采纳 | §8 重排 Phase 顺序 |
| Q5 更简单方案 | "首批五 kind 全要"范围失控；建议 3 硬模板覆盖 80% | 🟡 部分采纳 | §4 完成定义改为 3 完整 + 2 spike-gated；保留 png-canvas 与 image-deck 分立（codex 想合成 single-image，我们保留区分） |

---

## 附录 A — v0.1 → v0.2 IR Migration

迁移规则（执行于 Phase A）：

| v0.1 字段 | v0.2 字段 | 转换规则 |
|---|---|---|
| `ir_version: "0.1"` | `ir_version: "0.2"` | 直接改 |
| `ir_kind: "image-deck"` | 同名保留 | 不变 |
| `skill_meta`, `input_schema`, `browser_runtime`, `error_ux`, `attribution` | 同名保留 | 字段完全不变 |
| `static_assets.*` (top-level) | `render.static_assets.*` | 整块移到 `render` 下 |
| `llm_phase: { ... }` | `llm_pipeline: [ { id: "plan", ...llm_phase } ]` | 包成单元素数组，自动赋 `id: "plan"`, `uses: []` |
| `render_phase: { kind, iterator, per_item }` | `render: { iterator, per_item }` | 整块改名；`kind` 字段消失（已经升到 top-level `ir_kind`） |
| `render_phase.iterator: "$.slides"` | `render.iterator: "$.steps.plan.output.slides"` | 路径前缀加 `steps.plan.output.`（因为 pipeline 输出有命名空间） |
| 其它 `$.xxx` 引用 | `$.steps.plan.output.xxx` | 同上 |

`ian-handdrawn-ppt.ir.json` 走完 migration 后必须通过：
1. JSON Schema 验证（against `ir-core.md` + `ir-kinds/image-deck.md`）
2. v0.2 composer 输出与 v0.1 base.html 输出在 JS 行为上语义等价（手工 diff，容忍空白）

---

## 附录 B — 与 DESIGN.md (v0.1) 的关系

- §11 (Security & Privacy) — **不变**，沿用 v0.1
- §错误处理 — **不变**，error_ux 字段保留
- §Distribution Plan — **不变**
- §"Approach B (Composed)" 中"组合 frontend-design skill" — **推迟到 v0.3**，v0.2 仍不接 frontend-design
- §"build-time agent / run-time not agent" 核心哲学 — **强化**（线性 pipeline 拒绝 DAG 就是这个哲学的延伸）

---

## 附录 C — 未在本文档展开的细节

以下属于实施期决策，不在本 design 文档锁定，留给 Phase 内的 user gate：

- 具体 LLM provider 默认值（v0.1 unverified 状态保留到第一次 verification log 写入）
- adapter 实现细节（`callLLM()` / `callImageAPI()` 行数与 v0.1 一致即可，无需 v0.2 重写）
- skeleton.html 的样式 token（v0.1 的 `#FBFAF5` paper / `#111` ink 沿用）
- error_ux 文案逐字（沿用 v0.1）
