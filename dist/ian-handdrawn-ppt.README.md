# Ian Handdrawn PPT — single-file web tool

Compiled by [skill2web](https://github.com/xuejia-mq/skill2web) v0.2 from
[ian-handdrawn-ppt](https://github.com/helloianneo/ian-handdrawn-ppt) (© Ian · MIT).

## How to use

`ian-handdrawn-ppt.html` 是 **single-file source** 但必须通过 HTTP 服务 — `file://`
**不支持** (浏览器 `fetch()` 限制 + 部分 provider CORS 拒 file 源)。

```bash
# 本地快速试
cd dist/
python3 -m http.server 8765
# 浏览器开 http://localhost:8765/ian-handdrawn-ppt.html

# 永久部署: 上传 ian-handdrawn-ppt.html 到任何 HTTP 静态托管
# (GitHub Pages / Surge / Cloudflare Pages / Netlify / 自家 nginx)
```

打开后:
1. 点右上 **设置**, 粘 LLM key (默认 `https://api.deepseek.com/v1` + `deepseek-chat`) + 图像 key (默认 `https://image.token-recyclebin.com/v1` + `gpt-image-2`). 保存到 `localStorage`。
2. 填表单 (内容 / 受众 / 场景 / 页数 / 视觉组合) → 点 **开始生成**。
3. 等 LLM 拆 spine (10-30s) + 并发生成 N 张图 (每张 10-60s)。
4. 失败的卡片可以单张 / 全部重试。点"看 prompt"看到本张实际拼出的 prompt 字符串。

> ⚠️ **Provider CORS 第一次跑可能不通**。v0.2 默认 endpoint 在
> `references/adapters.md` 仍 `unverified`。撞 CORS 时:
> - 浏览器 DevTools Console 看具体 preflight 报错
> - 设置面板换 OpenAI 官方 endpoint (CORS 友好但价格高)
> - 或起 30 行本地 Python 反向代理 (v0.3 计划自动出 `<name>-proxy.py`)

## API keys

需要:
- **LLM key** — 默认 https://api.deepseek.com/v1 (DeepSeek)
- **图像 key** — 默认 https://image.token-recyclebin.com/v1 (gpt-image-2 兼容代理)

key 仅存浏览器 `localStorage`, 永不发到 skill2web 作者的任何服务器,只去你配置的 endpoint。

## License & attribution

本编译产物源自 `ian-handdrawn-ppt` (Ian · MIT)。
源 LICENSE 全文见 [hero-cases/ian-handdrawn-ppt/source-attribution.md](../hero-cases/ian-handdrawn-ppt/source-attribution.md)。

skill2web 本身 MIT。
