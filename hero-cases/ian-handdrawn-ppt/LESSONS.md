# LESSONS — 手工把 ian-handdrawn-ppt 转成单文件 HTML

> 写在做完手工 hero case (Day 1) 之后。这份文档是 **skill2web v0.1 compiler 的设计输入**——记录"我手动做了哪些事 / 哪些可以自动化 / 哪些做不到"。

---

## 一、原 skill 的核心抽象（在手工过程中被"反向工程"出来）

ian-handdrawn-ppt 的 SKILL.md 看着像一个 7 步流程，但**真正可执行的核心**只有三层：

| 层级 | 内容 | 在 hero case 里的位置 |
|---|---|---|
| **A. 静态资产** | deck style lock / page role lock / reference match clause / archetype 列表 / theme tokens | `index.html` 顶部的 `DECK_STYLE_LOCK` 等常量 |
| **B. 一次 LLM 拆解** | 把用户内容 → 一份 deck spine JSON（含每张 slide 的 title/role/archetype/composition/required_text） | `planDeck()` 函数 |
| **C. N 次图像生成** | 对每张 slide：套用 A + B 的字段，拼成完整 image prompt，调图像 API 拿 PNG | `processSlide()` / `buildImagePrompt()` |

**关键发现**：原 SKILL.md 的"步骤 2: intake gap diagnosis"、"步骤 3: narrative planning"、"步骤 4: archetype mapping"、"步骤 7: verify" 在手工 HTML 里**全部塌缩成 step B 的同一次 LLM 调用**。这是因为：

- intake / planning / archetype 三步本质都是"读文本 → 输出结构化决策"，没必要分三次 LLM 调用
- verify 步骤在浏览器端只能做**最浅的检查**（图片是否返回、dimension 是否对），深度 verify（视觉一致性、Chinese text accuracy）是人眼的事，UI 给出"重试此页"按钮即可

**对 IR 的意义**：v0.1 compiler 的 IR 不需要表达 SKILL.md 的"7 步"，只需要捕获三层资产/输入/输出。

---

## 二、IR Schema 的初步定型（在 DESIGN.md 草稿基础上修正）

DESIGN.md 给的 IR draft 偏 generic（input_schema / llm_calls / render_spec / lib_deps），手工跑下来发现它**对图像生成型 skill 缺关键字段**：

```jsonc
{
  "skill_meta": { "name", "source", "license", "author" },

  // ===== 新增：静态资产 =====
  // 这是图像生成型 skill 的"灵魂"。compiler 必须把这些原文 inline 到 HTML 里，
  // 不能改写、不能"用 LLM 总结"——风格锚就是要逐字一致。
  "static_assets": {
    "style_lock":      "string (raw text from references/)",
    "role_locks":      { "<role>": "string" },   // 例 cover / body
    "reference_clauses": [ "string" ],            // 0-N 条
    "archetypes":      [ "string" ],
    "theme_tokens":    { /* canvas / colors / sizes */ }
  },

  // ===== 输入表单 =====
  "input_schema": [
    { "key", "type", "label", "default?", "options?", "required" }
  ],

  // ===== LLM 拆解阶段(可能 1-3 次) =====
  // 多数流程化 skill 只需要 1 次。
  "llm_phase": {
    "system_prompt_template": "string (Mustache-like {{...}})",
    "user_prompt_template":   "string",
    "expected_output_schema": { /* JSON schema for the spine */ },
    "model_hint":             "gpt-4o-mini | step-3.5-flash | deepseek-chat | ...",
    "json_mode_required":     true | false
  },

  // ===== 渲染阶段 =====
  "render_phase": {
    "kind":         "image-per-slide | template-html | pptx | png-canvas | ...",
    "iterator":     "spine.slides",        // 在 LLM 输出 JSON 里迭代哪个数组
    "per_item": {
      "prompt_template":  "string (静态资产 + iterator item 字段填空)",
      "size_by_role":     { "cover": "1536x1024", "body": "1536x1024" },
      "api":              "openai-images-generations | openai-images-edits | ..."
    }
  },

  // ===== 浏览器映射（lib_mapper 的产出）=====
  "browser_runtime": {
    "image_api":        "openai-images-compat",
    "llm_api":          "openai-chat-compat",
    "extra_libs":       [ /* 在这个 skill 里：空。其他 skill 可能要 pptxgenjs 等 */ ],
    "concurrency":      3,
    "timeout_ms":       { "llm": 120000, "image": 180000 },
    "retry":            { "image": 1 }
  },

  // ===== 错误 UX =====
  "error_ux": {
    "missing_key":   "string",
    "llm_4xx":       "string",
    "image_4xx":     "string",
    "image_timeout": "string",
    "cors":          "string"   // ← 新增：CORS 失败的引导
  },

  // ===== 输出归属 =====
  "attribution": {
    "source_skill_link":  "string",
    "source_author":      "string",
    "source_license":     "string",
    "footer_html":        "string (compiler 必须强制注入页脚)"
  }
}
```

**和 DESIGN.md 的差异**：
1. **`static_assets` 是新的核心字段**。原 draft 没有这一层，因为它没预想"风格锚是 prompt 的 60% 内容"。
2. **`llm_calls` 从数组改成 `llm_phase` 单对象**。手工经验：流程化 skill 99% 只需一次 LLM。多次 LLM 调用应作为 v0.3 的扩展，不在 MVP IR 里。
3. **`render_spec` 改成 `render_phase`，明确区分"模板渲染"和"图像生成"两种 kind**。原 draft 的 `pptxgenjs` engine 字段假设了"模板渲染"路径，但 ian-handdrawn-ppt 是"image-per-slide"路径，根本不沾 pptxgenjs。**对 IR 的意义**：`render_phase.kind` 是 compiler 选 inline lib / API adapter 的开关。
4. **新增 `browser_runtime.concurrency` / `timeout_ms` / `retry`**。手工经验：图像 API 是慢的、不可靠的、要并发的——这些不能写死在 compiler 里，必须随 skill 可配。

---

## 三、能自动化 vs 不能自动化（v0.1 compiler 的 scope）

### ✅ v0.1 可以自动化

| 工作 | 怎么做 |
|---|---|
| 解析 SKILL.md + references/ 抽出"静态资产" | analyzer：读 SKILL.md frontmatter、grep references/ 里带 ` ```text ` 围栏的代码块 → inline 进 HTML |
| 抽出 theme-tokens.json | 直接复制 + 在 HTML 里 expose 给 prompt 模板 |
| 决定 LLM phase 的 system prompt | 用一个 meta-LLM 调用：传给 LLM 整个 SKILL.md，让它生成"compiler 内部 system prompt 模板"。这一步是 build-time 才做的，**run-time 是结果固化在 HTML 里** |
| 决定 archetype 列表 | 直接从 slide-archetypes.md 抽 |
| 决定 size_by_role | 从 theme-tokens.json 的 canvas 字段读 |
| 拼 HTML 骨架 | 用一份 template HTML（本 hero case 的 index.html 简化版），把 IR 字段填进去 |
| 注入页脚 attribution | 从 LICENSE / NOTICE.md / README.md 抽署名信息 |

### ❓ v0.1 必须问用户 / 半自动

| 工作 | 原因 |
|---|---|
| `input_schema` 字段（要让用户填什么） | SKILL.md 不显式声明输入字段。需要 meta-LLM 推断 + 用户确认 |
| 选哪家图像 API、什么 size | 不同供应商支持的 size 不同；compiler 默认给一个 candidate list，用户改 |
| 选哪个 LLM provider | 同上 |
| `error_ux` 文案 | 不同 skill 风格不同（"翻译错误"和"PPT 生成失败"语气应不同）。meta-LLM 生成草稿 + 用户改 |

### ❌ v0.1 做不到 / 主动拒绝

| 情况 | 拒绝理由 | 给用户的 message |
|---|---|---|
| skill 里有 bash / python script 不能在浏览器替换 | lib_mapper 找不到映射 | "该 skill 依赖 `<lib>`，目前没有浏览器等价物。可考虑提交 lib_mapper 映射 PR。" |
| skill 是多轮 agent（条件分支 / 工具调用循环） | 不是流程化 | "该 skill 包含 N 轮 agent 决策分支，不能编译为无 runtime 网页。建议看 Agent37 路线。" |
| skill 依赖私有 API / 需要复杂鉴权 | 浏览器端无法管理 | "该 skill 调用 `<api>`，需要服务端鉴权。MVP 不支持。" |
| skill 输入是大文件（视频、PDF 几十 MB） | 浏览器内存有限 | "输入文件大小 > 10MB，建议在桌面端处理后再上传。" |
| skill 风格锚是图片（reference image） | 无法分发（license 风险） | "该 skill 依赖一张风格锚图，本编译产物以文字 reference clause 替代——视觉一致性会有损失。" ← **本 hero case 就是这种情况** |

---

## 四、本 hero case 里遗留的"自动化 TODO"

这些是手工写时偷懒 / 简化的地方，v0.1 必须修：

1. **input_schema 是 hard-coded 的**（content/audience/scenario/length/output-style 五个字段写死在 HTML）。v0.1 应让 IR 声明 input_schema → compiler 生成对应 form。
2. **没接 frontend-design skill**（DESIGN.md 说 Week 2-3 接）。当前 UI 是我自己写的 minimal CSS。v0.1 也不接，v0.2 接。
3. **gpt-image-2 size 21:9 不原生支持**——cover 用 1536×1024 代替（≈3:2）。后期 v0.2 在浏览器端用 canvas crop 出真 21:9。
4. **zip 打包暂时不做**。当前是"循环触发单文件下载"的简化方案。后期可考虑用一个极小的纯 JS zip 实现（~30KB inline）。
5. **错误 UX 文案是固定的英文/中文混杂**。v0.1 由 IR 的 `error_ux` 字段驱动。
6. **没有 "fallback to text-only" 模式**——如果用户根本没有图像 API key，本 hero case 完全跑不动。原 SKILL.md 支持 "planning-only output（blueprint without images）"，v0.1 应当支持这个降级模式。
7. **没有视觉一致性 verification pass**。原 SKILL.md 的 "Multi-Page Consistency Pass" check list 没在浏览器实现。v0.1 可以加一个"看 prompt 一致性"的 prompt diff 视图。

---

## 五、CORS 与运行环境的实战记录

> 这一节会在用户首次实际运行 hero case 时补充。当前为 placeholder，待实测。

### 待验证

- `https://api.stepfun.com/v1/chat/completions` 是否允许浏览器跨域 `Authorization: Bearer ...`？
- `https://image.token-recyclebin.com/v1/images/generations` 是否存在并返回 OpenAI 兼容 JSON？
- `https://image.token-recyclebin.com/v1/images/edits` 浏览器 multipart 上传是否被 CORS 接受？

### 如果 CORS 不通，对照表

| 现象 | 处理 |
|---|---|
| `CORS preflight ... Access-Control-Allow-Origin` 报错 | 加 `mode: "no-cors"` 不行（响应不可读）。必须用本地 Python 反向代理（参考 explorecipe `server.py` 模式）。**对 compiler 的影响**：MVP 输出从"单文件 HTML"退化为"HTML + 50 行 Python proxy"。这是 DESIGN.md Day 0 spike 想避免的情况。 |
| 401/403 | API key 错或 endpoint 不支持 `/images/generations`。切到 `/images/edits` 模式 |
| 429 | 加并发限制（已有 IMAGE_CONCURRENCY=3）+ 指数 backoff |

### 备选 endpoint 调研结果

| Endpoint | 端点 mode | 状态 | 备注 |
|---|---|---|---|
| `image.token-recyclebin.com` | generations | 未验证 | 主端点，explorecipe 实际用 edits |
| `image.token-recyclebin.com` | edits | 已被 explorecipe 验证可用（但只在 Python 后端） | 浏览器 CORS 未知 |
| `dm-fox.rjj.cc/gptapi` | edits | explorecipe 备用 | 浏览器 CORS 未知 |
| `api.stepfun.com/v1` (image?) | 未知 | step-3.6 模型理论上支持图像 | 未在邻居项目中作为图像端点使用 |
| OpenAI 官方 | generations | CORS 友好（业内已验证） | 但 OAI 中国大陆访问难、价格高 |

---

## 六、对 skill2web 项目本身的学习

1. **"单文件 HTML"原则比想象的难守**——但守住了。本 hero case 真的没有任何外部 CDN：CSS 自写，没有 Tailwind；JS 自写，没有 React/JSZip。代价是 1125 行 HTML（43 KB）。**对项目的意义**：v0.1 compiler 的输出 size 预估 30-80 KB / skill 是合理范围。
2. **手工写一个 hero case 让"compiler 该长啥样"清晰得多**。如果一开始就动 compiler 代码，会陷入"先抽象什么"的瘫痪。**这印证了 DESIGN.md 的第一周 assignment 的智慧**。
3. **静态资产 inline 量很大**——本 hero case 里 prompt 模板字符串占了 ~3KB。这意味着 compiler 的 bundler 步骤主要是**字符串 inline + escape**，不需要复杂的 bundler 框架（不需要 esbuild / Vite）。
4. **没用 frontend-design skill 也能做到能看**。Tailwind 那套定制美学的依赖确实可以推到 v0.2。**对 IR 的意义**：UI 部分的 IR 字段可以非常薄（color tokens + 几个 layout enum），靠 frontend-design skill 在 build time 补齐。

---

## 七、第二周 Week 2 之前的下一步（具体动作）

1. **本地 http server 跑通本 hero case**：`cd hero-cases/ian-handdrawn-ppt && python3 -m http.server 8765 && open http://localhost:8765/`。第一次的实测会暴露 CORS 真相，**马上回填本文件第五节**。
2. **跑出第一份成功的 8 页 deck**：把那个"卧槽时刻"截图存到 `hero-cases/ian-handdrawn-ppt/screenshots/first-success.png`。
3. **拿这份成功结果给至少 1 个不懂 agent 的人看**：观察他的"网页能不能直接用"反应。这是 DESIGN.md Success Criteria 里"5 个外部测试者"的第一个。
4. **以本文档为输入，开始动 v0.1 compiler 的 skeleton**：先写 `skill/` 目录下的 SKILL.md（让 skill2web 本身是个 Claude Code skill），定义 analyzer / extractor / bundler 的接口。**不写实现**，先写接口和验收用例。
5. **第二个 skill 候选**：DESIGN.md 推荐 guizang-ppt-skill。在动 compiler 前先**手动**跑一遍它（重复本 hero case 流程），看本文档的 IR 假设是否成立。**如果第二个手工 case 需要给 IR 加 > 30% 新字段，说明 IR 设计还没收敛，多做 1-2 个手工 case 再动 compiler。**
