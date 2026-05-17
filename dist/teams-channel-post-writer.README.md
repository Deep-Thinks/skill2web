# Teams 频道帖子助手 — single-file web tool

由 [skill2web](https://github.com/Deep-Thinks/skill2web) **v0.3** 从
[teams-channel-post-writer](https://github.com/daymade/claude-code-skills/tree/main/teams-channel-post-writer)
编译。原作者 **daymade**，MIT License，著作权归原作者所有。

## 用途

填一个主题 + 你已核实的事实 → 工具先**判断帖子范式**（功能发布公告 / 最佳实践技巧），
再走对应结构起草，最后统一润色 → 直出一篇结构化的内部 Teams 知识分享帖。

## 这是一个 v0.3「静态 DAG」示例

本网页是 skill2web 第一个**静态 DAG** 编译产物，用来验证 v0.3 的分叉/合流能力：

```
classify ──┬── draft_feature  (when archetype == "feature")  ──┐
           └── draft_tip      (when archetype == "tip")      ──┴── polish
```

- `classify` 一次 LLM 调用判断范式，输出 `{archetype}`。
- `draft_feature` / `draft_tip` 带 `when` 条件，**同一次运行只跑命中的那一条**，
  另一条在进度条上标灰（skip）。
- `polish` 是合流（merge）节点 —— 它的父没有全部 skip，所以总会执行；它读取
  被选中分支的初稿，落选分支的引用解析为空串。

单次执行路径是 `classify → draft_X → polish` 共 3 次 LLM 调用。

## 怎么跑

`.html` 是**单文件源码**（无运行时 CDN 依赖），但必须用 HTTP 服务打开 ——
浏览器对 `file://` 的 `fetch()` 行为不稳定。**不支持双击打开 .html**。

```bash
cd dist/
python3 -m http.server 8765
# 浏览器开 http://localhost:8765/teams-channel-post-writer.html
```

也可部署到 GitHub Pages / Surge / Cloudflare Pages / Netlify。

1. 设置面板填 LLM key（默认 DeepSeek `deepseek-chat`，任何 OpenAI 兼容 endpoint 都行）。
   key 只存浏览器 `localStorage`，不发往任何第三方。
2. 表单填：帖子主题（必填）/ 已核实的事实（必填）/ 目标读者 / 帖子范式（默认自动判断）。
3. 点 **开始生成**，看进度条 —— 会看到 `classify` 跑完后,两个 draft 里一个 RUN 一个 SKIP。
4. 结果区出最终帖子，可复制 markdown / 打印。

## 已知降级（相对上游 skill）

本网页是上游 skill 的**降级编译版**，浏览器形态下损失了一项能力：

- 上游 skill 的 Workflow Step 1 让 agent **联网查官方文档 / changelog** 核实发布日期与
  版本 → 改为用户在 `已核实的事实` 字段自己粘贴查证过的事实。**事实核查的责任移交给用户。**

「判断范式 → 按结构起草 → 润色」的核心流程完整保留，且如实表达为 DAG。

## ⚠️ Provider CORS 风险

默认 LLM endpoint（DeepSeek）的浏览器端 CORS 未在本产物上实测。第一次跑可能撞 preflight
错误 —— 可在设置面板切到已知 CORS 友好的 endpoint（OpenAI 官方等），或起本地反向代理。

## License / 署名

源仓库 [claude-code-skills](https://github.com/daymade/claude-code-skills) 为 **MIT License**
（© 2025 daymade）。著作权归原作者 **daymade** 所有。编译器 skill2web 自身为 MIT。
