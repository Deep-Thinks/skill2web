# skill2web

把任意 Claude skill 编译成单文件 HTML 工具网站。

**核心哲学**：build-time 是 agent，run-time **不是** agent。让普通用户拿到的是一个无 agent runtime 的轻量网页。

## 这是什么

AI 从业者写了大量高质量 Claude Code skill（PPT、海报、菜谱、文档生成），但**只有装了 Claude Code 的开发者才能用**。普通人——不懂"什么是 agent"的朋友、亲戚、协会成员——无法体验。`skill2web` 把流程化 skill（输入 → N 次 LLM 调用 → 模板渲染 → 输出）编译为一个单文件 HTML，让任何人点开即用。

适用范围：流程化 skill（输入 → 1-3 次 LLM 调用 → 模板渲染 → 输出）。多轮 agent 分支 / 不可拆 skill 由 compiler 主动拒绝。

## 当前状态

- 设计文档：见 `DESIGN.md`
- 第一周任务：**手动**把 `ian-handdrawn-ppt` 转成单文件 HTML（hero case），见 `hero-cases/ian-handdrawn-ppt/`
- v0.1 compiler 代码：未开始（Week 1 末以前不写）

## 项目结构

```
skill2web/
├── README.md
├── LICENSE                       # MIT
├── DESIGN.md                     # 完整设计文档（office-hours 输出）
├── hero-cases/
│   └── ian-handdrawn-ppt/        # 手工 hero case
│       ├── index.html            # 单文件 HTML
│       ├── LESSONS.md            # 手工过程的设计沉淀
│       └── source-attribution.md # 原 skill 归属与 license
└── (skill/ — v0.1 compiler 代码，未开始)
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
