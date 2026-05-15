# Prompt Master · 单文件网页版

把粗糙的想法编译为针对特定 AI 工具优化的可粘贴 prompt。

- 上游 skill: [nidhinjs/prompt-master](https://github.com/nidhinjs/prompt-master) (MIT, 7.4k★, 假定 MIT — 实际部署前请核对原 repo LICENSE)
- 编译: skill2web v0.2.1, ir_kind=`template-html`, **无降级路径** (纯 SOP-shape skill 的直编基线)
- 端到端实测: 2026-05-15, stepfun `step-3.5-flash` 25s 出真实 prompt (Claude 4.x XML 标签结构)

## 如何使用

### 1. 起一个本地 HTTP server (不能直接双击 .html — 浏览器对 `file://` 的 fetch 有限制)

```bash
python3 -m http.server 8765
# 然后访问 http://localhost:8765/prompt-master.html
```

或部署到 GitHub Pages / Surge / Cloudflare Pages。

### 2. 填入 LLM API Key (仅存浏览器 localStorage)

默认 endpoint `https://api.stepfun.com/v1` + `step-3.5-flash` — **CORS 已验证浏览器友好** (2026-05-15)。

兼容: 任何 OpenAI 兼容的 chat completions endpoint (DeepSeek / OpenAI / 智谱 / Qwen Cloud / ...)。换 endpoint 在「设置 → Base URL」改。

### 3. 填表 → 生成

- **你想让 AI 干什么**: 一两句话粗糙想法
- **目标 AI 工具**: Claude 4.x / GPT-5 / o3 / Gemini / Qwen3 / Midjourney / Cursor 等 10 类
- **额外约束**: 长度限制 / 格式 / 占位符要求
- 点「开始生成」，约 8-25s 后出 prompt

## 输出形态

- **Section 1 「可直接粘贴的 Prompt」**: 代码块包住的裸 prompt，一键复制
- **Section 2 「目标工具与说明」**: 目标 / 关键优化 / 使用前 setup / 占位符列表

## 隐私

- API key 仅存浏览器 `localStorage`，刷新保留，关闭浏览器不上传。
- 你的输入只在浏览器 ↔ 你选的 LLM 供应商之间流动，skill2web 作者**不接触任何 key / 任何输入**。

## License

- 源 skill: nidhinjs/prompt-master · MIT (假定; 请以 [原 repo](https://github.com/nidhinjs/prompt-master) 的 LICENSE 为准)
- 编译产物: 继承上游 MIT
- 编译器: [skill2web](https://github.com/xuejia-mq/skill2web) · MIT
