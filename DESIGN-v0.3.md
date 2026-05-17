# Design v0.3 — 静态 DAG `llm_pipeline` + 强制 frontend-design pass

> 状态:已实施 (2026-05-18)。本文档记录 v0.2 → v0.3 的演化。
> 前序:[`DESIGN.md`](DESIGN.md) (v0.1) · [`DESIGN-v0.2.md`](DESIGN-v0.2.md) (v0.2)。

---

## 1. 升级目标(用户原话)

两件事,一次 release:

1. **"运行时按中间结果分叉/合流的控制流图(DAG)也是一种 workflow,理论上也可以变成
   工作流"** —— 把 v0.2 一刀切拒掉的 DAG 形态纳入可编译范围。
2. **"给这个 skill 里塞一个 frontend-design skill,要求生成 HTML 之前必须看。"**

---

## 2. v0.2 为什么拒 DAG —— 一个不诚实的边界

v0.2 的 `analyzer-checklist.md §4` 与 `ir-core.md §3.4` 把**所有** DAG / 分叉 / 合流 /
条件跳转判为 `agent-shaped` 拒绝。理由写的是"这不是流程化 skill 的形态"。

这个理由经不起推敲。区分两种东西:

| | 编译期可知性 | 是否需要 agent runtime |
|---|---|---|
| **静态 DAG**:图有限、编译期完全已知,分支条件 = 前序输出的纯函数 | ✅ 完全已知 | ❌ 不需要 |
| **动态控制流**:循环次数运行时定、"调工具直到满意"、工具序列开放 | ❌ 不可知 | ✅ 需要 |

静态 DAG 在浏览器里就是一个**状态机**:跑节点 → 用纯函数求值分支条件 → 选下一条固定
的边。它从不"决策",只是"哪条固定的边被走"会变。**这不是 agent。**

v2 的拒绝把**实现限制**(composer 的 `llm_pipeline` 是扁平数组、runner 顺序执行)
冒充成了**根本限制**。v0.3 的任务:把边界重新画在诚实的位置。

**新边界一句话**:可编译性取决于"控制流图在编译期是否完全已知且有限",不取决于
"流程里有没有判断"。

---

## 3. v0.3 完成定义

### 3.1 必须做(v0.3 ship 条件)

- F1 — `llm_pipeline` 升级为**静态 DAG**:`uses` 多父(合流)+ step `when` 结构化
  分支(分叉);composer 与 runtime 都支持。
- F2 — **强制 frontend-design pass**:编译流程里加一个不可跳过的 gate,composer 前
  必须调 `frontend-design` skill。
- F3 — analyzer §4 / refusal 模板 / 各 references 的 DAG 措辞按新边界改写。
- F4 — 版本号、CHANGELOG、README、本设计文档同步。

### 3.2 明确不做(留给 v0.3.x / v0.4)

- **无界循环展开** —— 即便循环有运行时上界,也不自动展开;要求 skill 作者改写成
  固定上界的 N 个 step(refusal 文案已提示)。
- **DAG 可视化编辑器 / IR 作图工具** —— IR 仍是手写 JSON。
- **render 端分叉** —— `render` 仍是单一 `ir_kind`、单一输出。DAG 只作用于
  `llm_pipeline`;pipeline 可中段分叉,但必须在 render 前合流。
- **frontend-design 整页重写** —— pass 只产出覆盖型 CSS(`theme_overrides`),不替换
  skeleton / block。skeleton 的结构稳定性优先于视觉自由度。
- **真实 DAG hero case** —— v0.3 的 runner 只过了 Node 逻辑模拟;端到端真实编译列为
  v0.3.x backlog(见 `TODO.md`)。

---

## 4. F1 — 静态 DAG `llm_pipeline`

### 4.1 三层能力分级

讨论中识别出三档,v0.3 解锁前两档:

1. **无条件 fan-in(合流,所有 step 都跑)** —— 完全静态,拓扑序执行即可。v0.2 连这个
   都拒了,最该解锁。
2. **条件分叉(`when` 边,部分 step 跳过)** —— 仍是静态图,需要 IR 表达条件 + runner
   支持跳过。v0.3 解锁。
3. **无界循环 / 运行时决定图形状** —— 真 agent,**永远拒**。

### 4.2 IR 变化

`llm_pipeline` 每个 step:

- `uses` —— v0.2 是"引前序 step",语义不变,但 v0.3 起允许**多个**父(合流)。
- `when` —— **新增可选字段**。结构化条件对象,不是自由 JS 表达式:

  ```jsonc
  "when": { "path": "steps.classify.output.kind", "op": "eq", "value": "A" }
  ```

  `op`:`eq` / `ne` / `in` / `gt` / `gte` / `lt` / `lte` / `exists` / `truthy`。
  `path` 是对 `{ steps, input }` 的 dotted lookup。

  **为什么结构化而非自由表达式**:`when` 是 build-time 数据,baked 进产物。结构化
  → runtime 只做比较,**永不 `eval`**;analyzer / extractor 也能校验。自由表达式
  会更灵活,但 YAGNI + 安全权衡下不值得。

完整 schema 见 `references/ir-core.md §3.4`。

### 4.3 Runtime 语义(skeleton.html)

pipeline 数组按拓扑序(= 数组顺序)遍历。每个 step:

- **skip 判定**:`when` 不命中 → skip;或**所有父都被 skip** → skip。
- **skip 传播规则的关键点**:是"**全部**父 skip 才 skip",不是"任一父 skip 就 skip"。
  这样 **merge / fan-in 节点只要有一个分支跑过就执行**。
  (实现时第一版写成了"任一父 skip",merge 被误跳;Node 模拟立刻抓到,已修。)
- skip 的 step:`state.steps[id] = { skipped:true, output:null, raw:"" }`,进度条标灰
  (`skip` 态),pipeline 继续。skip ≠ fail。
- merge step 的 prompt 引用被 skip 分支的输出(`{{steps.path_b.output.text}}`)时,
  Mustache-lite 解析为空串 —— prompt 模板需写得能容忍"其中一支为空"。

**强约束**:`render` 读取的终端 step 必须**无条件执行**(无 `when`,且不会因上游全
skip 被跳过)。否则 render 拿不到数据。analyzer §4 负责检查。

### 4.4 标准形状

```jsonc
{ "id": "classify", "uses": [] },
{ "id": "path_a",   "uses": ["classify"],
  "when": { "path": "steps.classify.output.kind", "op": "eq", "value": "A" } },
{ "id": "path_b",   "uses": ["classify"],
  "when": { "path": "steps.classify.output.kind", "op": "eq", "value": "B" } },
{ "id": "merge",    "uses": ["classify", "path_a", "path_b"] }
```

`classify` 跑完 → `path_a` / `path_b` 按 `when` 二选一 → `merge` 合流(父没全 skip,
执行)→ `render` 读 `merge.output`。

### 4.5 验证

无真实 skill 时,用 Node 模拟 runner:对 `kind=A` 与 `kind=B` 两条路径分别跑,断言
"被选中的分支执行、另一支 skip、merge 始终执行"。两条路径都 PASS。compose.py 对既有
v0.2 example 回归编译 + JS 语法检查通过。

---

## 5. F2 — 强制 frontend-design pass

### 5.1 为什么是"强制 gate"而不是"代码集成"

v0.1 / v0.2 一直把 frontend-design 集成推迟,理由是"预防性 over-engineering"。但用户
明确要求"生成 HTML 之前必须看"。"必须"= 硬规则 = 流程 gate。

skill2web 本身是一个**由 agent 运行的 skill**。"看 frontend-design" 的最自然实现:
编译 agent 在 composer 前**调用 `frontend-design` skill**。这不需要改 composer 代码,
是工作流约束。

### 5.2 落点:Phase 5.0

在 Phase 5(composer)前插入 **5.0 frontend-design pass**:

- 输入给 frontend-design:`IR.skill_meta`(主题/受众)、`IR.ir_kind`、`IR.input_schema`、
  skeleton 默认皮肤 + `blocks/<kind>.html` kind 样式。
- 产出:一段**覆盖型 raw CSS**,收进新 IR 字段 `IR.theme_overrides`。
- composer 把 `theme_overrides` inline 到 `<style>` **末尾**(skeleton 基础样式与
  `BLOCK:HEAD` 之后),因此能覆盖二者。

写进 `SKILL.md` Hard rule 7-8,`compiler-workflow.md §5.0`。

### 5.3 为什么是"覆盖型 CSS"而不是整页重写

skeleton + block 的**结构**(pipeline runner、settings 面板、进度条、mustache-lite)
是 skill2web 正确性的载体,不能让 frontend-design 自由改写。`theme_overrides` 把设计
自由度限制在**视觉层**(配色 / 字体 / 间距 / 圆角 / 阴影),结构不动。这是
"build-time is agent, run-time is not" 哲学在 UI 上的延伸。

### 5.4 硬约束

`theme_overrides` **只放 CSS**:无 `<script>`、无远程 `@import` / CDN / web-font URL、
无 `url(http...)`。否则违反"单文件 + 无运行时 CDN 依赖"(Hard rule 3)。frontend-design
产出若含这些,编译 agent 必须 inline 化或剔除。写进 Hard rule 8。

`theme_overrides` 可以为空 —— 但那必须是 frontend-design **看过之后**判定默认皮肤已够
好的结论,不是省略掉这一步。

---

## 6. 与 v0.2 的兼容策略

v0.3 是 v0.2 的**严格超集**:

- `when` 可选、`uses` 多父只是放宽约束、`theme_overrides` 可选。
- 一份合法的 v0.2 IR 直接就是合法的 v0.3 IR。
- composer 同时接受 `ir_version` 为 `"0.2"` 或 `"0.3"`。
- **无需迁移脚本**(对比 v0.1 → v0.2 需要 `migrate_v01_to_v02.py`)。

新编译建议 `ir_version` 写 `"0.3"` 并补 `theme_overrides`。

---

## 7. Success Criteria

- ✅ compose.py 对 v0.2 example 回归编译,JS 语法检查通过。
- ✅ 一份带 `when` 分叉的 v0.3 IR 能编译;Node 模拟 runner,两条分支路径选择正确、
  merge 始终执行。
- ✅ analyzer §4 不再一刀切拒 DAG;边界改为"编译期已知且有限"。
- ✅ `refusal: agent-shaped` 文案明确"分叉/合流本身不是拒绝理由"。
- ✅ SKILL.md Hard rule 7-8 写入强制 frontend-design pass;Phase 5.0 落地。
- ✅ `ir-core.md` 文档化 `when` / 多父 `uses` / `theme_overrides`。
- ⏳ 真实 DAG skill 端到端编译 —— 列为 v0.3.x backlog(`TODO.md`)。

---

## 附录 — 本 release 一并修复的 v0.2 文档债

v0.3 动 references 时一并修了 v0.2 遗留的死引用 / 失迁移:

- `lib-mapper.md`(v0.2 已拆分、不存在)→ `adapters.md` / `render-libs.md`,
  `SKILL.md` + `compiler-workflow.md` 共 6 处。
- `ir-schema.md`(v0.2 已删)→ `ir-core.md`,`compiler-workflow.md` 多处。
- `compiler-workflow.md` Phase 3 整段仍是 v0.1 IR 形态(`llm_phase` 单对象 /
  `render_phase` / `image-per-slide`)→ 迁移到 v0.2/v0.3。
- `SKILL.md` "six decision gates" → 实为 four user gates(GATE 3 分 3a/3b)。
- README hero 表补 `wuman-brief-to-poster`。
