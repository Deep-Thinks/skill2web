# TODO — skill2web v0.3.x backlog

跟踪 v0.3 release 之后必须做的事。来源:DESIGN-v0.2.md §5.2 (spike-gated)、
§5.3 (明确不做)、§12 (Open Questions)、DESIGN-v0.3.md、原 v0.1 codex review session
`019e2743-1b49-7851-9015-c1aef7b7b645` 中未落地的条目。

每条标了 **trigger condition** — 做这件事的"时机"。

---

## v0.2 已交付 (本 release 完成项, 不再列为 TODO)

✅ Phase F0 — analyzer kind router + 运行环境等价性 (step 9) + 5 类新 refusal 模板
✅ Phase A — 拆 ir-schema → ir-core + ir-kinds/image-deck;拆 lib-mapper → adapters + render-libs;拆 base.html → skeleton + blocks/image-deck + adapters/{openai-chat-compat,anthropic-chat,openai-images-compat}.js;`skill/compose.py` 三步组装 + `skill/migrate_v01_to_v02.py`
✅ Hero Case 2 — `hero-cases/synthetic-essay-polisher/` 手工 template-html
✅ Phase B — `ir-kinds/template-html.md` + `blocks/template-html.html` + sanitizer 三模式 + features.print_css 实装 + `examples/synthetic-essay-polisher.ir.json`
✅ Phase C — `ir-kinds/png-canvas.md` + `blocks/png-canvas.html` + `examples/guizang-cover.ir.json`
✅ ian-handdrawn-ppt v0.2 重编 (`hero-cases/ian-handdrawn-ppt-v0.2/`)
✅ 三个 dist 产物 (Node.js JS 语法检查通过)

---

## v0.3 已交付 (本 release 完成项)

✅ 静态 DAG `llm_pipeline` — `uses` 多父(合流)+ step `when` 结构化分支(分叉);compose.py `js-pipeline` 输出 `when`;skeleton runner `evalWhen()` + 跳过传播(全父跳过才跳)+ `skip` 进度态。Node 模拟两条分支路径验证通过。
✅ 强制 frontend-design pass (Phase 5.0) — SKILL.md Hard rule 7-8;`IR.theme_overrides` (ir-core.md §8) raw CSS 注入 skeleton。
✅ Analyzer §4 改写 — DAG 不再一刀切拒;分界改为"控制流图编译期是否完全已知且有限"。
✅ 文档死引用修复 — `lib-mapper.md` → `adapters.md`/`render-libs.md`;`ir-schema.md` → `ir-core.md`;compiler-workflow.md Phase 3 从 v0.1 IR 迁移到 v0.2/v0.3。

---

## ✅ 静态 DAG hero case — v0.3 已交付

`teams-channel-post-writer`(daymade/claude-code-skills,MIT)—— 真实 GitHub skill,其
`writing-guidelines.md` 定义两种结构不同的帖子范式(功能公告 5 段 / 技巧 6 段),如实编译为
`classify → draft_feature | draft_tip → polish` 静态 DAG。产物在 `dist/teams-channel-post-writer.{html,ir.json,README.md}`。

端到端实测(StepFun `step-3.5-flash`,浏览器真实跑):
- feature 路径:`draft_feature` RUN、`draft_tip` SKIP、`polish` RUN ✓
- tip 路径:`draft_feature` SKIP、`draft_tip` RUN、`polish` RUN ✓
- 截图:`docs/screenshots/e2e-teams-dag-{feature,tip}.png`

**剩余 backlog**:把它补成完整 `hero-cases/teams-channel-post-writer/`(LESSONS.md +
source-attribution.md);把它列进 README hero 表。

---

## v0.2.x — pptx-canvas spike (DESIGN §8 D-spike, §11.S1)

**Trigger**: 有真实 nature-paper2ppt 之类用户实际等 pptx 输出, 或自行验证欲望出现时。

**判定 (DESIGN §11.S1 Pass 条件全满足才进入 D-impl)**:
- 用 nature-paper2ppt 真实 2-3 页输出 (1 张封面 + 1-2 张正文 + 1 张图片插入) 作基准
- 手写 pptxgenjs 代码 (≤ 200 行) 复刻。导出 .pptx 在 PowerPoint **与** Keynote 都:
  - 主要文字 / 标题 / 图片位置不丢
  - 字体回退在中文文本上可接受 (允许字体替换, 但不允许乱码 / 字号崩坏)
  - 用户可在 PowerPoint 中**继续编辑**(不是死图)

**Fail 处置**:
- pptx-canvas 从 DESIGN §5.1 移到 §5.3 (明确不做)
- 加 `refusal: pptx-too-complex` (analyzer-checklist.md 已有占位文案)
- 给上游 skill 作者一份"如何把 PPTX skill 改成 image-deck shape"的建议 (写进 `references/refusal-recipes.md` 新文件)

---

## v0.2.x — data-table minimal spike (DESIGN §8 E-minimal, §11.S2)

**Trigger**: 用户提交了一个数据-表格-导出形态的真实 skill, 或 v0.2 用户说"这是个明显缺口"。

**判定 (DESIGN §11.S2 Pass 条件)**:
- 构造 mock skill 完整跑通: 用户填要点列表 → 1 次 LLM 调用 → 输出 JSON array → 渲染 sortable table → 一键导出 CSV + JSON
- 全程 inline 实现, 无外部 JS lib (手写 ~50 行 table + ~30 行 CSV)
- HTML 总大小 < 60 KB

**Fail 处置**:
- data-table 从 DESIGN §5.1 移到 §5.3
- analyzer 加 `kind-not-yet-supported: data-table` 的 v0.3 ETA 文案

---

## v0.2.x — Provider verification (lib-mapper / adapters Verification log)

**Trigger**: 第一次有人实际把任一 hero case 跑通时。

`references/adapters.md` 的 Verification log 还是空。所有 endpoint 是 `unverified`。
建议先验:
- DeepSeek `https://api.deepseek.com/v1` (LLM, 国内便宜文档健康)
- OpenAI 官方 `https://api.openai.com/v1` (LLM + 图像, CORS 友好但价格高)

流程见 `references/adapters.md` "如何把 unverified → verified-full"。

---

## v0.2.x — Open Questions (DESIGN §12, 实施期需回答)

### Q1. Hero Case 2 选 nature-polishing 还是 khazix-writer?

✅ **已答**: 用户决定不联网,构造 `synthetic-essay-polisher` 合成示例 (单 step pipeline 已验证)。
若未来发现 1-step 表达力不够, 再做一个 multi-step 合成或 clone khazix-writer 验证。

### Q2. template-html 默认 sanitizer?

⏸️ v0.2 强制显式选择, 没有默认值 (DESIGN §6.4 决议)。`synthetic-essay-polisher` 用 `dompurify-strict`。
**待验证**: guizang-ppt 主流程含交互 JS (翻页) 时 strict 会破; Phase B 实测后再定 (推迟到该真实 skill 编译时)。

### Q3. 加 "compile preview 模式"?

🔁 v0.2 没加。trigger: Phase B 中后期实际编译时若有用户反馈"想先看 IR + HTML 草图再走 user gate" 才考虑。

### Q4. png-canvas / image-deck 的 endpoint_mode 默认?

✅ **已答**:
- image-deck 默认 `edits` (因 token-recyclebin.com 不支持 generations)
- png-canvas 默认 `generations` (单图无需 reference)
两个值已写进 ir-kinds/{image-deck,png-canvas}.md。

---

## v0.3 — Local Python reverse proxy mode (从 v0.1 留)

**Trigger**: 一次实际撞 CORS 的端到端用户反馈后。

修复方向:
- emitter 阶段在 dist/ 多写一个 `<skill-name>-proxy.py` (可选, 30 行 BaseHTTPServer)
- HTML 加 settings 开关 "如果 base_url 是 localhost,加 /api/ 前缀"

---

## ✅ frontend-design skill 集成 — v0.3 已交付

v0.3 把它实装为 Phase 5.0 强制 pass:每次编译在 composer 前必须调 `frontend-design`
skill,产出收进 `IR.theme_overrides`(raw CSS,inline 到 `<style>` 末尾)。见
SKILL.md Hard rule 7-8、compiler-workflow.md §5.0、ir-core.md §8。

---

## v0.3 — Streaming LLM responses

**Trigger**: 用户反馈 "等几十秒看不到内容很焦虑" (大概率发生在 template-html 长输出场景)。

修复方向: adapters/openai-chat-compat.js 加 SSE / chunked 支持; skeleton pipeline runner 把流式片段实时推到 `state.steps[id].partial`; render block 可选订阅。

---

## v0.3 — Single IR 多 kind 输出

**Trigger**: 真实 skill (例 guizang-ppt 主输出 + 旁挂封面) 用户痛诉"我想一次编出两个 HTML"。

DESIGN §5.3 明确 v0.2 不做。v0.3 可考虑 IR 顶层加 `outputs: [{ ir_kind, render }, ...]`,但这是大改。

---

## Codex review session continuation

```bash
codex exec resume 019e2743-1b49-7851-9015-c1aef7b7b645 "..."
# 或 Claude Code: /codex consult <follow-up question>
```

session id 在 `.context/codex-session-id` (gitignored)。
