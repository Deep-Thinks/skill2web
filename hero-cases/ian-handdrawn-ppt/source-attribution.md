# Source Attribution — ian-handdrawn-ppt

本目录的 hero case 是 [Ian Handdrawn PPT](https://github.com/helloianneo/ian-handdrawn-ppt) skill 的**单文件 HTML 版本**，由 [skill2web](../../) 项目手工编译。

## 上游 skill

- **名称**：Ian Handdrawn PPT
- **作者**：Ian ([@helloianneo](https://github.com/helloianneo) · <https://ianneo.xyz>)
- **源仓库**：<https://github.com/helloianneo/ian-handdrawn-ppt>
- **License**：MIT (Copyright (c) 2026 Ian)
- **本地参考副本**：克隆于 `/tmp/skill2web-refs/ian-handdrawn-ppt/`（Day 1 hero case 制作期间）

## 本目录与上游的关系

| 文件 | 关系 |
| --- | --- |
| `index.html` | 编译产物：把上游 `SKILL.md` + `references/` + `assets/theme-tokens.json` 的关键内容内联（inline）成可在浏览器跑的工作流 |
| `LESSONS.md` | skill2web 项目自身的设计文档；记录"我手动做了哪些事 / 哪些可以自动化"。**不是上游 skill 的副本**。 |

## 内联的上游内容

`index.html` 内联了以下来自上游的内容（已注明出处）：

1. **Deck style lock**（来自 `references/prompt-patterns.md`）—— 完整原文嵌入图像 prompt 模板。
2. **Page role locks: cover image / body illustration**（来自 `references/prompt-patterns.md`）—— 按 page role 套用。
3. **Slide archetype 列表**（来自 `references/slide-archetypes.md`）—— 给 LLM 选 archetype 用。
4. **Visual DNA 关键约束**（来自 `references/visual-dna-v6.md`）—— 通过 prompt 传递。
5. **Theme tokens**（来自 `assets/theme-tokens.json`）—— 仅作为参考；浏览器端只用其中的尺寸 / 色板字段。

**没有**内联的内容：

- `assets/reference-handdrawn-article-illustration-style.png` —— 上游 NOTICE.md 标注由 Ian 生成。本 hero case 不嵌入此图（避免二次分发争议）。`index.html` 用 prompt 中的 "reference match clause" 文字描述来替代图像锚。
- `LICENSE` 全文 —— 仅在 `index.html` 页脚和本文件标注。

## 编译产物的 license

`index.html` 本身遵循上游 MIT license。任何用户在分享 / 二次分发本 hero case 时，必须保留：

- 对 Ian 的署名（在网页页脚链接 `https://github.com/helloianneo`）
- 对 `skill2web` 项目的署名（链接本仓库）

## 上游 SKILL.md 摘录（reference）

供检查 IR 抽象是否覆盖上游核心流程：

> **Workflow**:
> 1. Ingest material
> 2. Run intake and gap diagnosis
> 3. Plan the deck narrative
> 4. Map each slide to an archetype
> 5. Apply visual DNA
> 6. Build output (image generation)
> 7. Verify

`index.html` 的浏览器端流程对应：
- 步骤 1-2 由用户填表单 + LLM 一次性合并完成
- 步骤 3-4 由 LLM 一次"slide spine 生成"完成
- 步骤 5-6 由前端 prompt 拼装 + 调用图像 API 完成（每张 slide 一次）
- 步骤 7 仅做最小检查：图像 dimension 是否符合 page role，错误重试一次
