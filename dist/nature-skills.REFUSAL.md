# skill2web 编译拒绝说明：nature-skills

- **源仓库**：https://github.com/Yuan1z0825/nature-skills
- **License**：MIT © 2026 Yuan Yizhe
- **判定时间**：2026-05-15
- **skill2web 版本**：v0.1
- **结论**：**拒绝编译**（整仓 9 个 skill 全部不在 v0.1 scope 内）

---

## 一句话原因

`nature-skills` 是一个 monorepo，包含 9 个独立 skill。skill2web v0.1 当前只支持 `render_phase.kind = image-per-slide`（参考 hero case [`ian-handdrawn-ppt`](../hero-cases/ian-handdrawn-ppt/)）；这 9 个 skill 的输出形态没有一个是 image-per-slide。

按 `references/analyzer-checklist.md` 决策树，**第 8 步（输出格式）和第 5 步（依赖映射）**先后命中拒绝条件。

---

## 逐 skill 判定

| skill 路径 | 输出形态 | 预测 `render_phase.kind` | 拒绝类别 | 触发理由 |
|---|---|---|---|---|
| `skills/nature-academic-search/` | MCP 工具调用 + 引文文件 | （不适用） | `refusal: agent-shaped` + `refusal: private-api` | 调用 PubMed / CrossRef / arXiv MCP server，需要外部服务端鉴权，无法编译为无 agent runtime 的浏览器单文件 |
| `skills/nature-citation/` | 引文标注后的文本 / Markdown | `template-html` | `refusal: kind-not-yet-supported` | v0.2 才支持 `template-html` |
| `skills/nature-data/` | Nature 风格 Data Availability 声明（Markdown 段落） | `template-html` | `refusal: kind-not-yet-supported` | v0.2 才支持 `template-html` |
| `skills/nature-figure/` | matplotlib / ggplot2 渲染的 PDF / SVG / TIFF | `png-canvas`（理论） | `refusal: unmapped-dep` | 依赖 server-side Python 数据可视化栈（matplotlib / ggplot2），`lib-mapper.md` 无对应浏览器 lib，且 R/ggplot2 无浏览器等价物 |
| `skills/nature-paper2ppt/` | `.pptx` 文件 | `pptx-canvas` | `refusal: kind-not-yet-supported` | v0.2 才支持 `pptx-canvas`；同时依赖 server-side PyMuPDF / python-pptx / Pillow（unmapped-dep） |
| `skills/nature-polishing/` | 润色后的英文段落 | `template-html` | `refusal: kind-not-yet-supported` | v0.2 才支持 `template-html` |
| `skills/nature-reader/` | 中英对照 Markdown（保留图表位） | `template-html` | `refusal: kind-not-yet-supported` | v0.2 才支持 `template-html` |
| `skills/nature-response/` | Point-by-point 回复信（Markdown） | `template-html` | `refusal: kind-not-yet-supported` | v0.2 才支持 `template-html` |
| `skills/nature-writing/` | Nature 风格 manuscript 段落（Markdown） | `template-html` | `refusal: kind-not-yet-supported` | v0.2 才支持 `template-html` |

---

## 替代方案

按拒绝类别给出可行路径：

### 路径 A：等 skill2web 版本升级
- **v0.2 计划支持** `template-html`（覆盖 7 个 skill：citation / data / polishing / reader / response / writing / 部分 figure）和 `pptx-canvas`（覆盖 paper2ppt）。
- **v0.3 计划支持** `png-canvas`（可能覆盖 figure，但仍需解决 matplotlib/ggplot2 浏览器替代问题）。
- 当前 v0.2 / v0.3 timeline 未排期，见 [`TODO.md`](../TODO.md)。

### 路径 B：在 Claude Code 里继续用（原始用法）
9 个 skill 在 Claude Code 装载后均可直接使用，无需编译为网页。这是它们设计的目标 runtime。

### 路径 C：手动重写某个 skill 为 image-per-slide 形态
如果你想强行套用 v0.1 编译能力，**最接近**的是把 `nature-paper2ppt` 降级为 image-per-slide——即用 `gpt-image-2` 把每张幻灯片渲染为 PNG 而不是生成可编辑 `.pptx`。代价：
- 成品是 PNG 序列而非 `.pptx`，背离 skill 原意。
- 文字不可编辑、不可复制、不可排版调整。
- 中文学术 PPT 在 `gpt-image-2` 上的字体/排版稳定性未实测。

如需走这条路径，请明确告知主 agent："compile anyway, 降级 nature-paper2ppt 为 image-per-slide"。

### 路径 D：试 Agent37 等 agent-runtime 托管服务
对 `nature-academic-search` 这类 agent-shaped skill，托管 agent runtime 才能跑——skill2web 设计上明确不覆盖 agent runtime 场景。

---

## 手动覆盖（manual override）

按 `analyzer-checklist.md` 约定，如果你认为以上判定错误，可以告诉主 agent "compile anyway" 并指定要强行编译的单个 skill 路径。本编译器**会**继续推进到 Phase 3，但**不保证**产物可用——超出 v0.1 安全范围。

---

## 附：决策依据文件

- skill2web SKILL.md：`skill/SKILL.md`（参见 "Status" 与 "Hard rules"）
- 分析 checklist：`skill/references/analyzer-checklist.md`
- v0.1 唯一支持的 kind 的参考实现：`hero-cases/ian-handdrawn-ppt/`
- 源 skill 本地克隆：判定时位于本地 `/tmp/skill2web-refs/nature-skills/`（不入仓）
