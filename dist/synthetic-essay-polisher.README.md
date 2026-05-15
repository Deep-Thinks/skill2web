# 长文润色 (合成) — single-file web tool

由 [skill2web](https://github.com/xuejia-mq/skill2web) v0.2 编译。
合成 hero case (`synthetic-essay-polisher`) — 不绑任何上游 skill, MIT。

## 用途

把粗稿 / 大纲润色为结构化 markdown 文章。单次 LLM 调用,template-html 渲染,
sanitizer = `dompurify-strict` (内置白名单 sanitizer)。

## 怎么跑

```bash
cd dist/
python3 -m http.server 8765
# 浏览器开 http://localhost:8765/synthetic-essay-polisher.html
```

打开后:
1. 设置面板填 LLM key (默认 https://api.deepseek.com/v1 + deepseek-chat)。本 skill **不需要**图像 key。
2. 表单填: 原文 / 草稿 (必填) + 受众 / 文体 / 语言 → 点 **开始润色**。
3. 等 LLM 出 JSON (10-30s) → 内置 markdown 渲染 + 白名单 sanitize → article 显示。
4. 操作按钮: **打印** (走 `@media print`, 自动隐藏 settings/input/progress/footer 仅留正文) · **复制 markdown** · **下载 .md** · **看 prompt**。

## License

skill2web MIT。本 skill 是 v0.2 Phase B (template-html plugin) 的设计验证 hero case,
不绑任何上游 skill 的 license。
