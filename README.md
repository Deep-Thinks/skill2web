# skill2web

把任意 Claude skill 编译成单文件 HTML 工具网站。

**核心哲学**：build-time 是 agent，run-time **不是** agent。让普通用户拿到的是一个无 agent runtime 的轻量网页。

## 这是什么

AI 从业者写了大量高质量 Claude Code skill（PPT、海报、菜谱、文档生成），但**只有装了 Claude Code 的开发者才能用**。普通人——不懂"什么是 agent"的朋友、亲戚、协会成员——无法体验。`skill2web` 把流程化 skill（输入 → N 次 LLM 调用 → 模板渲染 → 输出）编译为一个单文件 HTML，让任何人点开即用。

适用范围：流程化 skill（输入 → 1-3 次 LLM 调用 → 模板渲染 → 输出）。多轮 agent 分支 / 不可拆 skill 由 compiler 主动拒绝。

## 当前状态 (v0.2, 2026-05-15)

- 设计文档: `DESIGN.md` (v0.1) + `DESIGN-v0.2.md` (v0.1 → v0.2 演化)
- v0.2 编译器: 三步组装 (skeleton + block + adapter) — `python3 skill/compose.py <ir.json> <out.html>`
- 支持三个 `ir_kind`:
  - `image-deck` — 多张相关图 (例 `ian-handdrawn-ppt`)
  - `template-html` — markdown / 报告输出 (例 `synthetic-essay-polisher`)
  - `png-canvas` — 单张封面 / 海报 (例 `guizang-cover`)
- v0.1 IR → v0.2 自动迁移: `python3 skill/migrate_v01_to_v02.py <v0.1.json> <v0.2.json>`
- spike-gated (DESIGN §11): `pptx-canvas` / `data-table` 仅 schema 草案,等真实 skill 触发实装

## 项目结构

```
skill2web/
├── README.md
├── LICENSE                            # MIT
├── DESIGN.md                          # v0.1 设计文档
├── DESIGN-v0.2.md                     # v0.2 演化文档 (本 release 实施依据)
├── TODO.md                            # v0.2.x backlog
├── hero-cases/
│   ├── ian-handdrawn-ppt/             # v0.1 手工 hero case (image-deck)
│   ├── ian-handdrawn-ppt-v0.2/        # v0.2 composer 自动重编 (回归基线)
│   └── synthetic-essay-polisher/      # v0.2 Phase B 设计输入 (template-html)
├── dist/                              # 编译产物
│   ├── ian-handdrawn-ppt.html
│   ├── synthetic-essay-polisher.html
│   ├── guizang-cover.html
│   └── nature-skills.REFUSAL.md       # v0.1 refusal 示例 (kind-not-yet-supported)
└── skill/                             # v0.2 compiler
    ├── SKILL.md                       # 主入口 (六阶段 + 四 user gate)
    ├── compose.py                     # 三步组装 composer
    ├── migrate_v01_to_v02.py          # v0.1 → v0.2 IR 迁移
    ├── examples/
    │   ├── ian-handdrawn-ppt.ir.v0.1.json   # 归档
    │   ├── ian-handdrawn-ppt.ir.json        # v0.2
    │   ├── synthetic-essay-polisher.ir.json # v0.2
    │   └── guizang-cover.ir.json            # v0.2
    ├── references/
    │   ├── analyzer-checklist.md      # 9 step + 5 类新 refusal
    │   ├── compiler-workflow.md       # 六阶段操作书
    │   ├── ir-core.md                 # universal IR (8 字段)
    │   ├── ir-kinds/
    │   │   ├── image-deck.md
    │   │   ├── template-html.md
    │   │   └── png-canvas.md
    │   ├── adapters.md                # API 调用契约
    │   └── render-libs.md             # inline JS lib
    └── templates/
        ├── skeleton.html              # 通用骨架
        ├── blocks/
        │   ├── image-deck.html
        │   ├── template-html.html
        │   └── png-canvas.html
        └── adapters/
            ├── openai-chat-compat.js
            ├── anthropic-chat.js
            └── openai-images-compat.js
```

## 运行 hero case

`hero-cases/ian-handdrawn-ppt/index.html` 是**单文件源码**（无外部 CDN 依赖），但运行时**必须通过 HTTP 协议提供**——浏览器对 `file://` 协议的 `fetch()` / `localStorage` 行为不一致，会导致请求失败或行为漂移。

承诺的精确版本：**"单文件源码 + 任何 HTTP server" = 任何浏览器开**，包括：

- `python3 -m http.server`（最简单）
- GitHub Pages / Surge / Cloudflare Pages / Netlify
- 你自己的 nginx / Caddy

不包括："双击 `.html` 文件就用"——这种用法**不稳**，不要承诺给最终用户。

最简单的方法：

```bash
cd hero-cases/ian-handdrawn-ppt/
python3 -m http.server 8765
# 访问 http://localhost:8765/
```

首次打开会要求填两个 API key（仅存浏览器 localStorage，永不上传任何第三方）：
- LLM 推理 key（用于内容拆解 / slide spine 生成）
- 图像生成 key（用于生成手绘风 PNG）

> ⚠️ **v0.1 已知风险（post-codex-review 2026-05-15）**：默认 provider（DeepSeek、StepFun、`image.token-recyclebin.com`）的浏览器端 CORS **未实测**——它们目前仅作为 Python 后端调用验证过。第一次跑撞 CORS 错的概率非真零；若遇到，请在浏览器 DevTools Network 看 preflight 响应、或换 OpenAI 官方 / Anthropic direct-browser 端点重试。`skill/references/lib-mapper.md` 的 Verification log 是空的——欢迎你的实测结果以 PR 形式回灌。

## License

MIT。详见 `LICENSE`。
编译产物保留原 skill 的 license / 作者署名（详见各 hero case 目录下的 `source-attribution.md`）。
