# 吴熳 · 文章直出海报 — single-file web tool

由 [skill2web](https://github.com/Deep-Thinks/skill2web) v0.2 从
[wuman-brief-to-poster](https://github.com/Rosiawu/wuman-brief-to-poster) 编译。
原作者 **吴熳 (Rosiawu)**，著作权归原作者所有。

## 用途

粘贴一篇文章 / brief / 活动通知 → 一次 LLM 提炼海报文案与信息层级 → 直出**一张或一组**
优雅的实验编辑式海报。`ir_kind = image-deck`：`series_count` 选 3 / 6 时，输出锚定海报 +
受控变体（每张换一个布局方向，文案层级与信息结构不变）。

## 怎么跑

`.html` 是**单文件源码**（无运行时 CDN 依赖），但必须用 HTTP 服务打开 ——
浏览器对 `file://` 的 `fetch()` 行为不稳定。**不支持双击打开 .html**。

```bash
cd dist/
python3 -m http.server 8765
# 浏览器开 http://localhost:8765/wuman-brief-to-poster.html
```

也可部署到 GitHub Pages / Surge / Cloudflare Pages / Netlify。

1. 设置面板填 LLM key（默认 DeepSeek）+ 图像 key（默认 `image.token-recyclebin.com` · `gpt-image-2`）。
   key 只存浏览器 `localStorage`，不发往任何第三方。
2. 表单填：文章（必填）/ 海报类型 / 锚定风格 / 出图数量 / 署名 / 必须保留信息 / 主标题 → 点 **开始生成**。
3. 等 LLM 拆解（10-40s）+ 图像 API 逐张出图（每张 30-90s，最多并发 3）。
4. 每张海报可单独 **下载 PNG** / **重试** / **看 prompt**。

## 怎么拿 API key

- LLM：DeepSeek 开放平台（`platform.deepseek.com`），或任何 OpenAI 兼容 endpoint，设置面板可改 Base URL。
- 图像：默认 `image.token-recyclebin.com`（中文海报字渲染最好），也可换 OpenAI 官方 `gpt-image-1`。

## 已知降级（相对上游 Codex skill）

本网页是上游 skill 的**降级编译版**，浏览器形态下损失了以下能力：

- 飞书 / 腾讯文档 / 钉钉文档**登录抓取** → 改为用户自己复制文档文字粘贴进来；
- 多轮**对话式追问** → 改为一次性结构化表单；
- 人像 / Logo / 参考图**像素级保真** → 从零生成，不接受上传参考图；
- 锚定海报「先出图再人工确认」的人在环 → 改为一次性生成全系列。

「粘贴文章 → 出海报（含成组出图）」的核心流程完整保留。

## ⚠️ CORS 风险

默认图像 endpoint（`image.token-recyclebin.com`）的浏览器端 CORS 未实测。
第一次跑可能撞 preflight 错误 —— 可在设置面板切到 OpenAI 官方 endpoint，或起一个本地反向代理。

## License / 署名

源仓库 [wuman-brief-to-poster](https://github.com/Rosiawu/wuman-brief-to-poster) **未声明 LICENSE 文件**。
原作者吴熳已在公开文章中明确表达开源意图，故本次经 `force_compile_no_license` 强署名编译，
著作权归原作者 **吴熳 (Rosiawu)** 所有。如需正式授权条款，请联系原作者在源仓库补充 LICENSE。

编译器 skill2web 自身为 MIT。
