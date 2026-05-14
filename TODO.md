# TODO — skill2web v0.1.x backlog

跟踪 v0.1 release 之后必须做、但今天没做的事。来源：codex review session
`019e2743-1b49-7851-9015-c1aef7b7b645` (2026-05-15)，可 `/codex` 续聊。

每条 TODO 标了 **trigger condition**——做这件事的"时机"，不是日历，是"什么发生时"。

---

## v0.1.1 — Analyzer 加运行环境等价性检查（Codex Issue 3）

**Trigger**: 在准备第二个 hero case **之前**，或第一次有人提交 PR 想加新 skill kind 时。

**问题描述**：当前 `skill/references/analyzer-checklist.md` 决策树太偏"流程形状"，不够偏"运行环境等价性"。Codex 指出会被误判为 compilable 但实际浏览器跑不动的 5 类 skill：

1. **headless-browser 渲染型**——用 Playwright / Chromium 截图的海报 skill（浏览器里没有第二个 Chromium 给它驱动）
2. **filesystem 缓存型**——多文件模板 / 中间产物缓存的文档 skill
3. **重 layout 的 PPTX/Docx**——`python-pptx` 复杂模板继承在 `pptxgenjs` 里不等价
4. **SaaS 私 API 自动化型**——表面是"用户拿自己 key"，实际供应商不支持浏览器 direct (CORS / auth header)
5. **第三方 URL fetch + 处理型**——从随机 URL 拉图再处理（CORS 没保证）

**修复方向**：

- analyzer-checklist.md 加一步"步骤 9：运行环境等价性"
  - 每个浏览器映射 lib，必须证明**源 skill 用到的具体 feature** 在浏览器侧验证过
  - `partial` 默认 → refuse；只有 user gate 显式接受降级才继续
- 增加新的 refusal 类型：
  - `refusal: needs-headless-browser`
  - `refusal: needs-filesystem-cache`
  - `refusal: needs-third-party-fetch`（CORS 不可控）
  - `refusal: layout-too-complex`（pptx layout 不能在 pptxgenjs 复现时）

**验收**：选 1 个上面 5 类中的真实公开 skill（候选：能用 Playwright 渲染社交卡片的 skill），让 v0.1.1 的 analyzer **正确拒绝**它。

---

## v0.1.1 — Gate 重构：mapper 与 provider 拆开（Codex 建议）

**Trigger**: 第二次 compile 跑通后；或当前 gate 3 用户体验显示混乱时。

**当前 4 gates**：
1. Analyzer verdict
2. IR confirm
3. Mapper + provider（**两件事混在一起**）
4. Emit confirm

**Codex 建议的 4 gates**：
1. Analyzer verdict（不变）
2. IR + 降级确认
3. Provider + CORS / 安全确认（独立的安全决策点）
4. 最终产物 + license 确认

**修复方向**：
- `skill/SKILL.md` Phase 4 拆成 4a (lib map) + 4b (provider choice + CORS risk)
- `compiler-workflow.md` 同步更新
- gate 3 (provider) 必须强制 surface 一段 CORS 风险话术（已在 SKILL.md 写好草稿，但跟 mapper 仍在一起）

---

## v0.1.x — Lib-mapper Verification log 至少填 1 行

**Trigger**: 第一次有人真的把 hero case 跑通时。

**问题描述**：`skill/references/lib-mapper.md` 的 Verification log 现在是空的——所有 provider 都是 `unverified`。这是诚实的，但没有可用的"已知工作"基线，下次 compile 选 provider 时仍然全是赌博。

**修复方向**：

- 选 1 个 provider（建议 DeepSeek，国内便宜、文档健康）实测：
  1. `cd hero-cases/ian-handdrawn-ppt && python3 -m http.server 8765`
  2. 浏览器打开，填 DeepSeek key + base URL
  3. 跑一次端到端
  4. DevTools Network 复制成功的 fetch 调用 → `verification/2026-MM-DD-deepseek.md`
  5. lib-mapper.md DeepSeek 行 `unverified` → `verified-full`，填 `Last verified`
- 同样对 image provider（OpenAI 官方比 `image.token-recyclebin.com` 更可能成）做一次

**验收**：v0.1.x 至少有 2 行 `verified-full` —— 1 个 LLM、1 个 image。

---

## v0.2 — 第二个 hero case（非 image-deck）

**Trigger**: v0.1 验证日志填了≥2 行 + 至少 1 个外部用户用 hero case 成功生成内容。

**问题描述**：当前 IR 是 `ir_kind: image-deck` shape。要不要泛化、怎么泛化，必须靠数据决定——做第二个手工 hero case，看 IR 哪些字段保留、哪些挪到 kind-specific。

候选第二个 hero case（按"差异大、能验证 generalization"排序）：

1. **markdown-report skill**（kind: `template-html`）—— 完全不同的 render shape，没有 slides 数组，单输出文件。能暴露 IR 的"按 N 项迭代"假设是否能用 N=1 优雅退化。
2. **single-image poster skill**（kind: `png-canvas`）—— 一次 LLM 出 prompt，一次图像调用，无 archetype 概念。能暴露 `static_assets` 字段对"多页一致性"的依赖。
3. **editable pptx skill**（kind: `pptx-canvas`）—— 用 pptxgenjs 真正生成可编辑 PPTX。能暴露 `extra_libs` inline 路径是否能撑住 ~340KB gzip 的 pptxgenjs。

**验收**：
- 第二个 hero case 跑通
- 写新一份 LESSONS.md
- 根据两份 LESSONS.md，**决定**：是 IR 单文件加 kind-discriminator，还是拆成 `image-deck-ir-schema.md` + `template-html-ir-schema.md`...
- 抽出真正通用的 IR top-level 字段（`skill_meta` / `attribution` / `error_ux` 几乎一定通用；`browser_runtime` 大概率通用；其余存疑）

---

## v0.2 — frontend-design skill 集成（原 DESIGN.md plan）

**Trigger**: v0.2 第二个 hero case 通过后，且用户实测了"当前 base.html 的视觉够用 / 不够用"。

**问题描述**：当前 `templates/base.html` 是手写 CSS。原 DESIGN.md plan B 是"靠组合：compiler 调 frontend-design skill 现场生成 UI"。这个集成被推迟了——但**只有真正有第二个 hero case，UI 多样性需求才出现**。在那之前先不动。

---

## v0.3 — Local Python reverse proxy mode

**Trigger**: 一次实际撞 CORS 的端到端用户反馈后。

**问题描述**：v0.1 承诺"单文件源码 + HTTP server"。如果某个 provider 的 CORS 死活不通，用户的 fallback 是"自己写 30 行 Python 代理"——这是真实可行的，但很多用户写不来。

**修复方向**：

- `emitter` 阶段在 `dist/` 多写一个 `<skill-name>-proxy.py`（可选）：
  - 30 行 BaseHTTPServer
  - 把 `localhost:8000/api/*` 转发到配置的真 endpoint
  - 默认关闭；用户撞 CORS 后告诉他"加 `--with-proxy` 重编"
- HTML 加一个 settings 开关 "如果 base_url 是 localhost，加 `/api/` 前缀"

---

## Codex review session continuation

如果后续想就具体 issue 跟 codex 继续讨论：

```bash
codex exec resume 019e2743-1b49-7851-9015-c1aef7b7b645 "..."
# 或在 Claude Code 里直接：/codex consult <follow-up question>
```

session 在 `.context/codex-session-id`（gitignored）。
