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

`hero-cases/ian-handdrawn-ppt/index.html` 是一个**单文件**网页，但**不能从 `file://` 协议直接打开**（浏览器对 file:// 的 fetch 有限制）。请在 hero-case 目录下起一个本地 http server：

```bash
cd hero-cases/ian-handdrawn-ppt/
python3 -m http.server 8765
# 访问 http://localhost:8765/
```

首次打开会要求填两个 API key（仅存浏览器 localStorage，永不上传任何第三方）：
- LLM 推理 key（用于内容拆解 / slide spine 生成）
- 图像生成 key（用于生成手绘风 PNG）

## License

MIT。详见 `LICENSE`。
编译产物保留原 skill 的 license / 作者署名（详见各 hero case 目录下的 `source-attribution.md`）。
