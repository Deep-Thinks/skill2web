# Guizang 风格封面 (合成 IR) — single-file web tool

由 [skill2web](https://github.com/xuejia-mq/skill2web) v0.2 编译。
形态参照 [guizang-ppt-skill](https://github.com/op7418/guizang-ppt-skill) 封面分支
(© op7418 · MIT),IR 与渲染逻辑由 skill2web 合成。

## 用途

把"主题 + 比例 + 风格关键词"扩成一段 image prompt → 调一次图像 API → 输出**一张** PNG 封面。
v0.2 `ir_kind = png-canvas` 的参考实现, `compositing = none`。

## 怎么跑

```bash
cd dist/
python3 -m http.server 8765
# 浏览器开 http://localhost:8765/guizang-cover.html
```

1. 设置面板填 LLM key (默认 DeepSeek) + 图像 key (默认 token-recyclebin.com)。
2. 表单填: 主题 (必填) / 主标题 / 副标题 / 比例 / 风格 → 点 **开始生成**。
3. 等 LLM 出 prompt_body (10-30s) + 图像 API 出图 (30-90s)。
4. 操作: **下载 PNG** / **重试** / **看 prompt** / **从头开始**。

> ⚠️ 默认图像 endpoint (`image.token-recyclebin.com`) 浏览器端 CORS 仍 unverified。
> 撞 CORS 可在设置面板换 OpenAI 官方 endpoint。

## License

合成 IR + 渲染 MIT (skill2web)。形态参照 guizang-ppt-skill (op7418, MIT)。
