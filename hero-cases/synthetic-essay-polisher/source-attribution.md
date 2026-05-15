# 合成 hero case · synthetic-essay-polisher

本 hero case **不是**外部 skill 的转换。它是一个 **合成 (synthetic)** skill —
为 skill2web v0.2 Phase B (template-html plugin) 提供设计输入而专门构造的一个
最小可信的 template-html-shape skill。

## skill 描述

把用户粘贴的粗稿(中文/英文)润色为有结构的 markdown 文章。

- **输入**: 原文 (textarea), 受众 (text, 可选), 文体 (select: academic / blog / technical), 语言 (select: zh / en)
- **LLM 调用 (1 次)**: 用户输入 → JSON `{ title, abstract, sections: [{heading, level, body_md}] }`
- **渲染**: template-html, output_form=markdown, sanitizer=dompurify-strict,
  print_css=true。提供 `下载 .md` 与 `复制 markdown` 按钮。

## 与上游真实 skill 的关系

形态上接近 `Yuan1z0825/nature-skills` 中的 `nature-polishing` 与
`KKKKhazix/khazix-skills` 中的 `khazix-writer` —— 都是
"输入文本 → 单次 LLM 拆解 → markdown 输出" 的 template-html shape。
但 **不是** 它们的反向工程,所以不背任何上游 author / license。

## License

本 hero case 全部代码与文档归档于本 repo,跟随 skill2web 项目的 MIT。
没有外部源 skill 的 license 需要传递。

`attribution.source_*` 字段在 IR 里指向本 hero case 自己。
