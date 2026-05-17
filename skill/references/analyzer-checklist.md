# Analyzer Checklist

Decide whether a source skill is compilable. **Refuse early** — a clean refusal is more valuable than a half-working artifact.

> v0.2 (2026-05-15)：决策树解除了"仅 image-per-slide"硬锁。kind 现在按 §8 路由到具体的
> sub-checklist。Step 9 (运行环境等价性) 按 codex Q4 提到 F0 最前。
>
> v0.3：§4 不再一刀切拒 DAG。`llm_pipeline` 升级为**静态 DAG**(分叉 + 合流),
> 可编译性的分界改为"控制流图编译期是否完全已知且有限"。只有运行时才决定轮数 /
> 图形状的(无界循环、tool-shape agent)才拒。

## The compilability question, in one sentence

> Can this skill be reduced to: **inputs → 1-3 LLM calls (linear, no agent branching) → templated render → output**, where every step has a clean **and verified** browser equivalent?

If the answer is yes, compile. If no, refuse with a specific reason.

## Decision tree (run in order; first stop wins)

### 1. Is it a Claude Code skill at all?

Required: a `SKILL.md` exists (anywhere in the repo), with valid YAML frontmatter (`name`, `description`).

- **No** → `refusal: not-a-skill` — "我没找到 SKILL.md。这不是一个 Claude Code skill。"

### 2. Is there a runnable workflow described?

Read `SKILL.md` → "Workflow" or "Steps" section.

- Multi-section, prose-only, no clear sequence → `refusal: unclear-workflow`
- One clean linear sequence (1, 2, 3 ...) → continue

### 3. How many LLM-shaped steps in the workflow?

Count steps that involve:
- Generating natural language
- Reasoning / planning / classifying
- Producing an image / audio / structured output

- **0** (pure deterministic transform like file convert) → `compilable, but trivial` — proceed; question to user: "这个 skill 其实不需要 LLM,确认要做成网页吗?"
- **1-3** → continue
- **4+ steps** → 看**单条执行路径**上的 LLM 调用数,不是 pipeline 数组的总节点数。v0.3 静态 DAG 里互斥分支(`path_a` / `path_b`)同一次运行只跑一条,所以 `classify → path_a|path_b → merge` 总节点 4、单路径仅 3,合法。单条路径仍 > 3 → `compilable but bloated`,问用户能否合并(常常能;如 intake + planning + spine → 一次调用)。
- **N where N depends on intermediate state** (轮数 / 图形状运行时才定 = agent-shaped) → `refusal: agent-shaped`

### 4. Are there conditional branches that need agent judgment?

Look for SKILL.md text like "if X, do Y else Z" where X is something the LLM must observe at run-time (not at form-input time).

- Found → 按下面三档处理:
  1. 能折进**单个 system prompt**("你来判断 X,据此选 A 或 B")→ 折叠,继续。最简单,优先。
  2. 折不进单 prompt(两支需要**不同的下游 pipeline** / 不同步数 / 不同输出结构),但**分支图编译期完全已知且有限** → 表达为 v0.3 **静态 DAG**:一个 `classify` step + 若干带 `when` 的分支 step + 一个总执行的 `merge` step(见 `ir-core.md §3.4`)。继续。
  3. 分支图编译期**不可知**(走哪条、走几条由运行时自由决策)→ `refusal: agent-branching`
- Not found → continue

**v0.3 判定准则**: skill2web 的 `llm_pipeline` 是**静态 DAG**(v0.3 起;v0.2 是其线性子集)。可编译性的真正分界是 **"控制流图在编译期是否完全已知且有限"**:

| 形态 | 判定 |
|---|---|
| 严格线性 1-3 步 | ✅ 可编译 |
| 分叉 / 合流,但图固定、`when` 是数据比较、节点有限 | ✅ 可编译(静态 DAG) |
| 循环 / 轮数运行时定 / "调到满意为止" / 图形状运行时才决定 | ❌ `refusal: agent-shaped` |

注意:静态 DAG 仍有约束 —— `uses` 只能引前序 step(数组拓扑序),`when` 只能是 `ir-core.md §3.4` 的结构化条件(非自由表达式),`render` 读取的终端 step 必须无条件执行。

### 4.5. SOP-shape vs tool-shape agent (v0.2.1 新增)

> 这一步把 step 4 / step 5 的"看似 agent-shaped / 看似 needs-fs / needs-shell"再过一遍滤网,**避免一刀切拒掉本可降级编译的 SOP**。这是 v0.2 hero case 实测后补的关键判定 (2026-05-15)。

很多高星 skill 写成 "agent-style" 是因为**作者本来就在 Claude Code 里用**, 所以默认 agent 会"探索 codebase / 抓 URL / 调外部 skill"。但本质上这些动作是 SOP 流程的**固定一步**, 不是 agent 在运行时持续自由决策。要区分:

| 形态 | 例子 | 判定 |
|---|---|---|
| **tool-shape agent**: agent 在持续自由决策何时调用什么工具,**轮数 / 路径 / 工具序列**都依赖运行时观察 | dev-browser (持续 navigate/click)、Playwright wrapper、Context7、brainstorming (对话长度动态)、neat-freak (持续写盘) | **真 agent-shape** → 进 step 4 拒 |
| **SOP-shape agent**: 流程上 N 个固定 phase, 每 phase 有固定输入输出, 中间的"agent 动作"是**信息获取**(读 codebase / 抓 URL / 查 references)而不是**持续决策** | aso-appstore-screenshots ("Explore codebase → benefits → screenshots")、qiaomu (固定抓→上传→生成)、clinical-reports (CARE / SOAP 固定模板) | 进 step 4.6 找降级路径 |

判定问句: **"如果把这个 skill 翻译成一张流程图, 每个 phase 之间有几条边？边的数量 / 走向是否依赖运行时观察？"**
- 边数固定、走向固定 → SOP-shape
- 边数 / 走向运行时决定 → tool-shape (真 agent)

### 4.6. 降级路径 (degradation check)

对每一个 SOP-shape 的"agent 信息获取"步骤, 问:

1. **能否替换为 user-provided input?**
   - "agent 读用户本地 codebase" → "用户在网页上**粘贴 README + 主要文件清单**或上传 zip 后由 LLM 内部消化" → 改写 `IR.input_schema` 加一个 textarea / file upload 字段
   - "agent 抓任意 URL" → "用户**预先**抓好内容粘贴进去" 或者 "**白名单**少量已知 CORS 友好的 CDN, USER GATE 3a 警告" → 接受降级
   - "agent 调外部 skill (image-gen / schematic / 套模板)" → "改成 IR 里的 image API 直调 / inline 静态模板" → 必要时**拆 IR 多次编译**(image-deck 主报告 + png-canvas 配图)
   - "agent 写到用户项目源码 (implementation phase)" → **砍掉**该 phase, IR 只覆盖前半流程(输出 markdown 设计稿 / blueprint / 代码片段供用户手工粘贴)。USER GATE 1 必须告诉用户"这块降级了, 终态实施需要用户自己粘代码"

2. **能则**: 把每一个"被替换"的步骤记到 IR 顶层的 `degradation_log: [{step, original, replacement}]`(USER GATE 1 必须 surface 给用户), 然后继续走 step 5+
3. **不能**(替换后 skill 失去核心价值 / 替换后 user input 量级超出可填表范围 / 替换后 SOP 不再 SOP)→ 进 step 4 拒 (agent-shaped)

降级**不是**"魔法编译" — 它是**承认 skill 在浏览器形态下损失了一部分**, 然后让用户在 USER GATE 1 决定是否接受这个降级版本。**用户说"不接受降级"等价 refuse**。

### 5. Tool calls / external API calls / scripts?

Search the source skill for:
- `bash`, `python` script invocations in workflow
- `import` statements in any `.py` files bundled
- "use the X plugin/skill" references

For each external dependency, check `references/adapters.md`(API 调用契约) 和 `references/render-libs.md`(inline JS lib):

- Has a `verified-full` row → continue
- Has `verified-partial` → continue with USER GATE warning ("`<lib>` is partially supported — features X work, Y don't")
- Has `unverified` → continue but USER GATE 3a (provider) 必须 surface 该状态
- Has `stub` → user gate; ask if they accept a no-op stub
- Not in either file → **add it (USER GATE 3b)** or `refusal: unmapped-dep`
- Calls a private API needing server-side auth → `refusal: private-api`
- Reads filesystem (other than user upload) → **先走 step 4.6 降级检查**;只有 tool-shape 的 fs (agent 在持续自由决定读哪 / 写哪) 才直接 `refusal: needs-fs`。SOP-shape 的"agent 读固定一组文件"应当替换为 user input。
- Runs `subprocess` / shell out → **先走 step 4.6 降级检查**;同上区分 tool-shape 与 SOP-shape。无法降级才 `refusal: needs-shell`。

### 6. Style anchors?

If the skill ships a binary style-anchor image (PNG/JPG referenced in prompts):

- Has `NOTICE.md` or LICENSE making the image freely redistributable → inline as base64 OK
- License-ambiguous OR LICENSE excludes asset → **do not inline**; use text-only `reference_clauses`. Warn user this lowers visual fidelity.
- Skill semantics require pixel-exact match → `refusal: needs-binary-anchor`

### 7. Input size & complexity?

- All inputs fit in textareas / small files (< 5MB) → continue
- Requires video, audio > 30s, PDF > 50 pages → `refusal: large-input`
- Requires user to upload a folder → `refusal: folder-input`

### 8. Output format / `ir_kind` 路由

Map the source skill's output to one of these `ir_kind` values, then jump to the matching sub-checklist:

| Source output | `ir_kind` | v0.2 status | Sub-checklist |
|---|---|---|---|
| Per-page image (PNG/JPG), N>=1 with style consistency | `image-deck` | ✅ supported | §8.A |
| Markdown / HTML / 文档报告(可打印) | `template-html` | ✅ supported | §8.B |
| Single PNG / poster / cover (N=1) | `png-canvas` | ✅ supported | §8.C |
| Editable PPTX | `pptx-canvas` | 🔬 spike-gated (DESIGN §11.S1) | refuse with ETA |
| Sortable / exportable table | `data-table` | 🔬 spike-gated (DESIGN §11.S2) | refuse with ETA |
| Audio (MP3) | — | ❌ refuse | `refusal: audio-unsupported` |
| Multiple files in zip | — | ❌ refuse | `refusal: zip-unsupported` |

**重要**: 一个 skill 只能映射到一个 `ir_kind`。同一 skill 同时承载"主输出 + 旁挂资源"(例如 guizang-ppt 既出 PPT 又出封面图) → 拆成两次编译,每次锁一个 kind。

#### §8.A — image-deck sub-checklist

确保:
- LLM 输出包含一个 array(默认 `slides`),每项至少含 `role` + `title` + `archetype` + 一个 prompt-fit 字段
- `static_assets.style_lock` 必须存在(image-deck 的"灵魂");可选 `role_locks` / `archetypes` / `reference_clauses`
- `per_item.size_by_role` 必须覆盖 IR 中所有出现的 role
- 图像 API 走 `openai-images-compat`(generations 或 edits)

#### §8.B — template-html sub-checklist

确保:
- LLM 输出是单一文档结构(允许 array sections,但不是"图像 deck")
- 选定 `output_form`: `markdown` / `html-fragment` / `full-document`
- **必须显式选择 `sanitizer`**: `dompurify-strict` / `dompurify-relaxed` / `none-trust`(none-trust 必须 USER GATE 警告 XSS 风险)
- 不需要 image API
- 若 skill 需要交互 JS(例如可翻页 deck),sanitizer 不能用 strict;实测后定

#### §8.C — png-canvas sub-checklist

确保:
- N=1: LLM 输出**一段** image prompt,渲染**一张**图
- 无 `iterator` / `per_item` / `role_locks` / `archetypes`
- `compositing` 必须是 `none`(v0.2 仅支持);text-overlay / image-merge 在 v0.3 才解锁
- `endpoint_mode` 推荐 `generations`(单图无需 reference)

### 9. 运行环境等价性 (v0.2 新增, codex Q4)

> 步骤 5 只确认"有映射";步骤 9 确认"映射真的覆盖 skill 用到的具体 feature"。
> 一个 lib 在 mapper 里被标 `verified-partial`,但 skill 用的恰好是不支持的子 feature → 必须拒绝。

为每个浏览器映射的依赖,具体追问:

| 模式 | 拒绝类型 | 触发条件 |
|---|---|---|
| Headless Chromium / Playwright / Puppeteer 渲染 | `refusal: needs-headless-browser` | 浏览器里没有第二个 Chromium 给它驱动 |
| 多文件模板 / 中间产物缓存 / 写盘 | `refusal: needs-fs` | 单文件 HTML 没有持久 FS |
| `python-pptx` 复杂 layout 继承 / 母版 | `refusal: layout-too-complex` | `pptxgenjs` DSL 不能覆盖 |
| 第三方 SaaS 私 API (服务端鉴权) | `refusal: private-api` | key 一旦放进 HTML 就泄露 |
| 从随机 URL 拉资源再处理 | `refusal: needs-third-party-fetch` | 上游 URL CORS 不可控,大概率 preflight 失败 |
| 跑 shell / `subprocess` | `refusal: needs-shell` | 浏览器无 shell |
| 重型科学计算 (matplotlib + R + ggplot2) | `refusal: unmapped-dep` 或 `refusal: layout-too-complex` | 浏览器无等价物 |

**判定原则**: 不是"理论上能不能",而是"**这个具体 skill 用到的 feature 在浏览器侧实际跑过 / 能跑过吗**"。无证据时 → `unverified` → USER GATE 3 必须 surface,用户可以接受风险继续。

---

## Refusal templates

When refusing, **always**:

1. State the specific category from the list below.
2. Quote the exact line/section in the source skill that triggered the refusal.
3. Suggest a viable alternative (Agent37, manual usage, wait for v0.3, etc.) when one exists.
4. Offer the user a **manual override**: "If you believe I'm wrong, type 'compile anyway' and I'll proceed."

### `refusal: agent-shaped`

> 这个 skill 的控制流**编译期不可知**: [SKILL.md line X 引用]。它在运行时根据中间结果决定走几轮 / 走什么 prompt(无界循环 / "调到满意为止" / 图形状运行时才定)—— 这需要 agent runtime,无法编译成静态网页。
>
> 注意区分:**分叉 / 合流本身不是拒绝理由**。v0.3 的 `llm_pipeline` 是静态 DAG,只要分支图编译期完全已知且有限(`classify → path_a|path_b → merge`),就能编译。被拒的是图的**形状 / 轮数运行时才决定**。
>
> 替代方案:
> - 跑在 Claude Code 里(原始用法)
> - 试试 Agent37 这类 agent-runtime 托管服务
> - 如果"N 轮 agent"其实是**固定的有限分支**,重写 SKILL.md 把它表达成静态 DAG(一个分类 step + 带 `when` 的分支 step + 总执行的 merge step,见 `ir-core.md §3.4`),然后再来编译
> - 如果循环次数其实有**固定上界**,把它展开成上界数量的固定 step

### `refusal: unmapped-dep`

> 这个 skill 依赖 `<library>`(在 [文件路径] 用到),但 `references/adapters.md` 和 `references/render-libs.md` 里都没有浏览器等价物。
>
> 你的选项:
> 1. 加一行到对应文件 —— 但你要确认这个浏览器库真的覆盖 skill 用到的特性(参考 §9 运行环境等价性)
> 2. 等版本升级
> 3. 如果这个 lib 在 skill 里其实只是装饰性的(比如打印日志),可以从 source 里删掉再重试

### `refusal: private-api`

> 这个 skill 调用 `<API>`,需要服务端鉴权才能调。浏览器单文件 HTML 没有"服务端"——key 一旦放进 HTML 就泄露了。
>
> 替代方案:
> - 用户自己的 API key 改成走他们自己的浏览器(OpenAI 兼容 endpoint 可以)
> - 不支持的 SaaS 私 API: 等 v0.3 的 "local proxy mode"
> - 完全跳过这一步: 如果这个 API 调用是装饰性的,可以重写 skill 跳过它

### `refusal: needs-binary-anchor`

> 这个 skill 严格依赖一张 binary 风格锚图片(`<file>`)来保证视觉一致。但 LICENSE 不明确允许二次分发这个图片。
>
> 替代方案:
> - 联系 skill 作者拿到分发授权 → 加进 IR.render.static_assets.reference_image
> - 接受视觉降级: 用 text-only reference clause(v0.2 默认走这个)。注意: 视觉会"像但不完全像"

### `refusal: kind-not-yet-supported`

> 这个 skill 的输出是 `<kind>`,v0.2 还不支持。
>
> v0.2 spike-gated: pptx-canvas (DESIGN §11.S1)、data-table (DESIGN §11.S2) — 通过 spike 才进 v0.2。
> v0.3+: 流式上传、zip-bundle、local-proxy mode。
>
> 现在能做的:
> - 等版本升级
> - 如果 skill 其实可以降级到当前支持的 kind(比如 markdown 报告可以渲染成 PNG),告诉我你愿意降级,我们继续

### `refusal: needs-headless-browser` (v0.2 新增)

> 这个 skill 用 Playwright / Puppeteer / 内嵌 Chromium 截图(在 `<file>` 里调用)。浏览器里没有第二个 Chromium 给它驱动,无法在 run-time 还原。
>
> 替代方案:
> - 把渲染从"页面截图"改成"图像 API 直出"(如果视觉风格能用 image-gen 模型表达) → 改 SKILL.md 重新编
> - 改成 template-html 输出可打印 HTML,让用户自己 Cmd+P 存 PDF

### `refusal: needs-fs` (v0.2 新增)

> 这个 skill 必须读写文件系统(在 `<file>` 里出现 `open()` / `os.path` / `Path(...).write_text(...)`)。单文件 HTML 没有持久 FS。
>
> 替代方案:
> - 用 `localStorage` 替代轻量缓存(自己改 SKILL.md)
> - 用户文件输入用 `<input type="file">`,运行时仅在内存中处理
> - 如果 skill 必须聚合 FS 上多个文件 → 不在 skill2web 范围

### `refusal: needs-third-party-fetch` (v0.2 新增)

> 这个 skill 在运行时从 `<random URL>` 拉资源(图片/数据)再处理。第三方 URL 的 CORS 不可控,浏览器大概率 preflight 失败。
>
> 替代方案:
> - 让用户预先下载 → 走 `<input type="file">` 上传
> - 如果第三方 URL 是少量固定的 CDN,且确认 CORS 友好,可以用户 override "compile anyway"
> - 等 v0.3 local proxy mode

### `refusal: layout-too-complex` (v0.2 新增, 配合 pptx-canvas spike-gate)

> 这个 skill 用 `python-pptx` 的复杂 layout 继承 / 母版,`pptxgenjs` DSL 不能等价复刻(参见 DESIGN §11.S1)。
>
> 替代方案:
> - 简化模板到 pptxgenjs 支持的范围(text/shape/picture/table)
> - 改成 image-deck-shape(每张幻灯片直接出 PNG,放弃可编辑)
> - 改成 template-html 出 HTML 报告

### `refusal: not-a-skill` / `unclear-workflow` / `agent-branching` / `large-input` / `folder-input` / `needs-shell` / `audio-unsupported` / `zip-unsupported`

短消息即可,说明原因 + 给一个具体建议。

---

## After a successful judgment (compilable)

Surface the verdict in plain language at USER GATE 1:

> ✅ 这个 skill 可以编译。
>
> 我的判断:
> - 类型: 流程化、`ir_kind = <image-deck | template-html | png-canvas>`
> - LLM 调用次数: N 次(线性 pipeline,各 step 之间 `uses` 严格引前序)
> - 渲染: <按 kind 描述>
> - 浏览器依赖: <adapter list> + <render lib list>(覆盖度 status: verified-full / unverified / partial)
> - 运行环境等价性 (§9): <每个 dep 都过了吗?有 caveat 吗?>
> - 降级路径 (§4.6): <如果走了降级,逐条列出: "原 skill 的 step X (读 codebase) → IR.input_schema 加字段 Y" / "原 phase Z (写代码到项目) → 砍掉,只输出设计稿">
> - 已知 caveat: <省略 / 列出>
>
> 继续抽 IR 吗?(y / 改判定 / 还有什么我没想到的 / 不接受这个降级方案)
>
> **重要**: 若有降级路径, 必须让用户**明确接受**才能继续。用户说"不接受降级" = `refusal: agent-shaped` (与原始判定一致)。

---

## 验收 (DESIGN §8 F0)

手动跑 analyzer 对以下 skill 给出正确判定:

**应判 compilable** (无降级):
- `nature-polishing` → `template-html`(单步 LLM,markdown 输出)
- `guizang-ppt` 封面分支 → `png-canvas`(单图)
- `ian-handdrawn-ppt` → `image-deck`(回归)
- `prompt-master` (nidhinjs, 7.4k★) → `template-html`(单步 LLM, intent + tool routing → 单 prompt 文本输出)

**应判 compilable WITH 降级** (走 §4.5 / §4.6):
- `aso-appstore-screenshots` (adamlyttleapps, 1.3k★) → 降级: Phase 1 "Explore project codebase" 替换为 user 上传 README + 截屏列表 + 1-2 段功能描述; 主 SOP 编译为 `image-deck` (4-5 张截屏)。USER GATE 1 必须 surface "codebase analysis 阶段被降级为用户填表" 让用户决定。
- `app-onboarding-questionnaire` (adamlyttleapps, 1.0k★) → 降级: 砍掉 Implementation Phase (写代码到用户项目); IR 只覆盖前 4 phase (discovery → transformation → blueprint → screen content), 输出 `template-html` 的 onboarding 设计稿 markdown (每屏文案 + 设计建议), 用户拿去手工实现。
- `clinical-reports` (K-Dense-AI, 21.9k★ 集合中) → 拆两次编译: 主报告 `template-html` (CARE/SOAP/CSR 模板, 用户填患者信息); MANDATORY 配 schematic 拆出 `png-canvas` 单独编译(或降级去图, 用户接受去图)。

**应判 refuse** (真 tool-shape 或不可降级):
- `neat-freak` → `needs-fs`(持续 tool-shape 写盘, 修改本地 docs/memory; §4.5 判 tool-shape)
- `dev-browser` / `browserwing` → `needs-headless-browser` + tool-shape (持续自由 navigate/click, 不是固定 SOP)
- `brainstorming` (obra/superpowers) → `agent-shaped` (多轮自适应对话, 轮数 / 走向运行时决定, §4.5 判 tool-shape, 无降级)
- `obsidian-markdown` / `vue-best-practices` → `unclear-workflow` (reference-shaped 知识库, 无 inputs/outputs 流程; **不是 v0.2 目标形态**, 但可让用户重新包装为"输入想法 → LLM 套规则 → 输出"另开 IR)
- `nature-figure` → `unmapped-dep`(matplotlib + ggplot2)
- `nature-academic-search` → `needs-local-server` + `agent-shaped`(MCP server + 多源, tool-shape)
- `aihot` → `private-api`(私 SaaS aihot.virxact.com)
- `nature-citation` → `agent-shaped`(多轮 Crossref 检索, 轮数运行时定)
- `hv-analysis` → `agent-shaped`(双线 Deep Research, tool-shape)
- `qiaomu-anything-to-notebooklm` → `needs-third-party-fetch` + `private-api` (CORS 黑洞 + NotebookLM 服务端鉴权, 无可行降级)
