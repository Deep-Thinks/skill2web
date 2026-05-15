# LESSONS — synthetic-essay-polisher (Hero Case 2)

> 作为 skill2web v0.2 Phase B 的设计输入。手工写完后回看,标定哪些 IR 字段确实
> 通用、哪些是 template-html 专属、哪些字段在 template-html 下根本不需要。

---

## 一、IR 通用字段在 template-html 下的表现

| ir-core 字段 | 用得上吗 | 备注 |
|---|---|---|
| `skill_meta` | ✅ 同 image-deck | 完全通用 |
| `input_schema` | ✅ 同 image-deck | 字段类型(text/textarea/select)够用 |
| `llm_pipeline` | ✅ 但 1 step 是常态 | hero case 用单 step (`polish`); 5+ section 不需要拆多 step。多段 LLM (intake → 多稿 polish) 才会真正用到 N-step |
| `browser_runtime.llm_adapter` | ✅ | `openai-chat-compat` 直接复用 |
| `browser_runtime.image_adapter` | ❌ null / 不存在 | template-html **不需要** image API。NEEDS_IMAGE 必须是 false → settings 面板的 image-key 区块在 BLOCK:UI_SETTINGS 必须是空 |
| `browser_runtime.default_endpoints.image` | ❌ 不存在 | 同上 |
| `browser_runtime.concurrency` | ⚪ 不相关 | template-html 单输出, 不需要并发 |
| `browser_runtime.retry.image` | ⚪ 不相关 | 同上 |
| `browser_runtime.timeout_ms.image` | ⚪ 不相关 | 同上 |
| `error_ux` | ✅ 但少几条 | image_4xx / image_timeout / image_5xx 在 template-html 下没人调,是 dead code 但保留无害 |
| `attribution` | ✅ 同 image-deck | 完全通用 |

**结论**: `browser_runtime` schema 里 image_adapter / default_endpoints.image / image timeout / retry.image 应当**允许**为 null / 缺省;skeleton 通过 `NEEDS_IMAGE` 判定是否启用 image 路径。`error_ux` 多余字段不强删,因为有些 skill(image-deck → template-html 转化)可能两套都要。

## 二、template-html 专属字段(写到 ir-kinds/template-html.md)

按 hero case 的实际需求,Phase B 的 `render` shape 至少要表达:

```jsonc
"render": {
  "output_form":   "markdown",    // discriminator
  "template_html": "<article>...{{steps.polish.output.title}}...</article>",   // 可选, 如果非空走模板渲染; 缺省走 hero case 的 default-article 渲染
  "css_lock":      "/* 可选, inline CSS */",
  "data_binding":  "$.steps.polish.output",
  "sanitizer":     "dompurify-strict",
  "features": {
    "toc":            false,
    "footnotes":      false,
    "syntax_highlight": false,
    "print_css":      true,
    "export_pdf":     false   // v0.2 不实现, flag 占位
  }
}
```

**hero case 实际怎么决定的**:

- `output_form = "markdown"`: LLM 输出 JSON, body_md 是 markdown 字符串 — runtime 走 markdown → HTML 转换。其它两值 `html-fragment` / `full-document` Phase B 也要支持(LLM 直接输出 HTML 段或整文档)。
- `template_html`: hero case 没做模板,直接用 JS 拼 article。Phase B 应该接受**两种模式**:
  - 用户给了 `template_html` → 走 mustache-lite 替换 + sanitize
  - 缺省 → 走"标准 article 模板"(skeleton 内置: `<h1>{{title}}<p class=abstract>{{abstract}}<sections>...`)。
  - 决策: hero case 走缺省;ir-kinds/template-html.md 必须文档化两种模式。
- `css_lock`: hero case 用 skeleton 自带的 article CSS, 没单独 inline。Phase B 留出 `css_lock` 字段允许 skill 作者自己注入 CSS(就像 image-deck 的 style_lock)。缺省 = ""。
- `data_binding`: hero case 直接用 `state.steps.polish.output` — 等价于 `$.steps.polish.output`。Phase B 把它放到 IR 字段里(允许 skill 改 step 名)。
- `sanitizer`: hero case 自写白名单 sanitizer (函数 `sanitizeHtml`),效果接近 dompurify-strict (剥不在白名单的 tag, 净化 href 协议)。Phase B 必须用真的 DOMPurify(三档:strict / relaxed / none-trust)。**none-trust** 必须在 USER GATE 加 XSS 警告,只允许"完全信任 LLM 输出"的场景。
- `features.print_css`: hero case 已实现(`@media print`)。Phase B 跟着做。
- `features.toc / footnotes / syntax_highlight / export_pdf`: hero case **没做** — flag 占位即可。Phase B 在 UI 上把对应按钮 disabled + 提示"v0.3"。

## 三、render 阶段的"通用框架"vs"按 kind 定制"

hero case 的 `renderArticle(out)` 函数就是 template-html block 的 `renderOutput()`:

- 通用框架(skeleton 提供): pipeline 完成后调一次 `renderOutput()`, 块 export 这个函数
- block 提供: `renderArticle()` 实现细节 + 下载/复制/打印按钮的 onclick 绑定

实际 Phase B 的 blocks/template-html.html 应当:

1. BLOCK:UI_SETTINGS — 空(template-html 不需要 image-key)
2. BLOCK:HEAD — article CSS + @media print
3. BLOCK:UI — `<article id="article">` + 下载/复制/打印/看 prompt 按钮
4. BLOCK:RENDER — `renderOutput()` + `renderArticle()` + `renderMarkdown()` + `sanitizeHtml()` (后两个 v0.2 接 marked + DOMPurify, hero case 是手写 fallback)
5. ADAPTER:LLM — openai-chat-compat (skeleton 注入)
6. ADAPTER:IMAGE — 空(image_adapter=null)

## 四、对 ir-core 的反馈

- **skeleton 必须正确处理 NEEDS_IMAGE=false**: BLOCK:UI_SETTINGS 段允许为空(template-html 整段不出现 image-key 区块)。skeleton.html 里 `if (NEEDS_IMAGE)` 分支已做 — 但要确认编译 template-html 时,settings 区块只显示 LLM, 不出现"图像"任何字眼。已做(BLOCK:UI_SETTINGS 段是空的,blocks/template-html.html 里整段空)。
- **mustache-lite 在 template-html 下无 `{{item.X}}` 语义**: 因为没 iterator。hero case 没用到 mustache-lite render template — 走 DOM 直接拼。Phase B 实装如果走 `template_html` mode, mustache-lite 要扩展支持 `{{steps.polish.output.title}}` 这种形式(skeleton 里的 mustache-lite 已支持 dotted path,够用)。
- **error_ux.json_parse 是真实痛点**: LLM 不返回 JSON 是 template-html 最常见失败 — hero case 已用 extractJson 三段兜底(直接 parse → fenced block → first {...} slice),与 image-deck 完全相同。复用即可。

## 五、明确不在 IR 里(由 hero case 经验否决)

- ❌ "section 数量上限 / 下限" — 不在 IR, 在 LLM system_prompt 里描述就行
- ❌ "段落最大字数" — 同上
- ❌ "abstract 是否必填" — 同上
- ❌ "字体" — `css_lock` 已经覆盖
- ❌ "TOC 自动生成" — Phase B features.toc flag 占位, v0.3 实做

## 六、与 image-deck 共享但**形态不同**的字段

- `static_assets` 字段在 image-deck 是"风格锚",在 template-html 下完全不需要(LLM 输出已经是结构化文本,没有"图像风格一致性"问题)。Phase B 的 `render` 不应该为 template-html 强加 `static_assets`,让该字段缺省即可。
- `iterator` 在 image-deck 是"slides 数组",在 template-html 下**通常没有**(单文档输出)。如果 LLM 输出多 sections, sections 是数据,不是 iterator(因为不是"每段调一次外部 API")。Phase B 的 template-html 不需要 `iterator` 字段。

## 七、HTML 文件大小与单文件原则

- hero case 25 KB,与 ian-handdrawn-ppt 的 43 KB 同量级
- 完全 inline,无外部 CDN
- Phase B 实装时:inline marked.js (~12KB gzip, ~30KB unzipped) + DOMPurify (~22KB gzip, ~70KB unzipped) → 总产物预估 ~120 KB,仍在"单文件源码"承诺之内(< 2 MB)

## 八、对 v0.2 ship 条件 (DESIGN-v0.2.md §13) 的支持

- ✅ 提供 template-html 形态的"已知能跑"基线 — Phase B 自动 composer 输出可以与本 hero case 做语义对照(IR 字段抽错时这里 diff 出来)
- ✅ 验证 IR 通用字段对 template-html 适配良好 (§一)
- ✅ 给 ir-kinds/template-html.md 提供具体字段需求(§二)
- ⏳ 浏览器端到端测试待用户首次填 LLM key 后实测

## 九、复现命令

```bash
cd hero-cases/synthetic-essay-polisher/
python3 -m http.server 8765
# 浏览器开 http://localhost:8765/
# 设置 LLM key + base_url → 输入草稿 → 开始润色
```
