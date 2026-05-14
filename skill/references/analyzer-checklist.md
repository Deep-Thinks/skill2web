# Analyzer Checklist

Decide whether a source skill is compilable. **Refuse early** — a clean refusal is more valuable than a half-working artifact.

## The compilability question, in one sentence

> Can this skill be reduced to: **inputs → exactly one (1-3) LLM call → templated render → output**, where every step has a clean browser equivalent?

If the answer is yes, compile. If no, refuse with a specific reason.

## Decision tree (run in order; first stop wins)

### 1. Is it a Claude Code skill at all?

Required: a `SKILL.md` exists (anywhere in the repo), with valid YAML frontmatter (`name`, `description`).

- **No** → `refusal: not-a-skill` — "我没找到 SKILL.md。这不是一个 Claude Code skill。"

### 2. Is there a runnable workflow described?

Read `SKILL.md` → "Workflow" or "Steps" section.

- Multi-section, prose-only, no clear sequence → `refusal: unclear-workflow`
- One clean linear sequence (1, 2, 3 ...) → continue

### 3. How many LLM-shaped steps in the workflow?

Count steps that involve:
- Generating natural language
- Reasoning / planning / classifying
- Producing an image / audio / structured output

- **0** (pure deterministic transform like file convert) → `compilable, but trivial` — proceed; question to user: "这个 skill 其实不需要 LLM，确认要做成网页吗？"
- **1-3** → continue
- **4+ distinct LLM steps with different prompts** → `compilable but bloated` — ask the user if the steps can be collapsed (often they can; e.g. intake + planning + spine → one call). If not, this is borderline.
- **N where N depends on intermediate state** (agent-shaped) → `refusal: agent-shaped`

### 4. Are there conditional branches that need agent judgment?

Look for SKILL.md text like "if X, do Y else Z" where X is something the LLM must observe at run-time (not at form-input time).

- Found → can the branch be expressed in the **system prompt** ("decide X and pick A or B accordingly") instead of as separate LLM calls? If yes, fold and proceed. If no → `refusal: agent-branching`
- Not found → continue

### 5. Tool calls / external API calls / scripts?

Search the source skill for:
- `bash`, `python` script invocations in workflow
- `import` statements in any `.py` files bundled
- "use the X plugin/skill" references

For each external dependency, check `references/lib-mapper.md`:

- Has a `coverage: full` row → continue
- Has `coverage: partial` → continue with USER GATE warning ("`<lib>` is partially supported — features X work, Y don't")
- Has `coverage: stub` → user gate; ask if they accept a no-op stub
- Not in mapper at all → **add it to mapper** (USER GATE 3) or `refusal: unmapped-dep`
- Calls a private API needing server-side auth → `refusal: private-api`
- Reads filesystem (other than user upload) → `refusal: needs-fs`

### 6. Style anchors?

If the skill ships a binary style-anchor image (PNG/JPG referenced in prompts):

- Has `NOTICE.md` or LICENSE making the image freely redistributable → inline as base64 OK
- License-ambiguous OR LICENSE excludes asset → **do not inline**; use text-only `reference_clauses`. Warn user this lowers visual fidelity.
- Skill semantics require pixel-exact match → `refusal: needs-binary-anchor`

### 7. Input size & complexity?

- All inputs fit in textareas / small files (< 5MB) → continue
- Requires video, audio > 30s, PDF > 50 pages → `refusal: large-input` (v0.2 may add streaming uploads)
- Requires user to upload a folder → `refusal: folder-input`

### 8. Output format?

Map the source skill's output to one of these `render_phase.kind` values:

| Source output | `render_phase.kind` | v0.1 status |
|---|---|---|
| Per-page image (PNG/JPG) | `image-per-slide` | ✅ supported |
| Markdown / HTML report | `template-html` | ❌ v0.2 |
| Editable PPTX | `pptx-canvas` | ❌ v0.2 |
| Canvas-rendered single PNG | `png-canvas` | ❌ v0.3 |
| Audio (MP3) | — | ❌ refuse |
| Multiple files in zip | — | ❌ v0.2 (zip emit) |

- v0.1 only: kind must be `image-per-slide`. Anything else → `refusal: kind-not-yet-supported` with the v0.2/v0.3 ETA.

---

## Refusal templates

When refusing, **always**:

1. State the specific category from the list below.
2. Quote the exact line/section in the source skill that triggered the refusal.
3. Suggest a viable alternative (Agent37, manual usage, wait for v0.2, etc.) when one exists.
4. Offer the user a **manual override**: "If you believe I'm wrong, type 'compile anyway' and I'll proceed."

### `refusal: agent-shaped`

> 这个 skill 包含 **multi-turn agent 决策**：[SKILL.md line X 引用]。它在每次运行时根据中间结果决定下一步走什么 prompt — 这不是流程化 skill 的形态，无法编译成无 agent runtime 的网页。
>
> 替代方案：
> - 跑在 Claude Code 里（原始用法）
> - 试试 Agent37 这类 agent-runtime 托管服务
> - 如果 N 轮 agent 其实是固定的 N 步流程，可以重写 SKILL.md 把它写成线性 workflow，然后再来编译

### `refusal: unmapped-dep`

> 这个 skill 依赖 `<library>`（在 [文件路径] 用到），但我的 `lib-mapper.md` 里没有浏览器等价物。
>
> 你的选项：
> 1. 加一行到 `lib-mapper.md` —— 但你要确认这个浏览器库真的覆盖 skill 用到的特性。
> 2. 等 v0.2 我们扩展映射表。
> 3. 如果这个 lib 在 skill 里其实只是装饰性的（比如打印日志），可以从 source 里删掉再重试。

### `refusal: private-api`

> 这个 skill 调用 `<API>`，需要服务端鉴权才能调。浏览器单文件 HTML 没有"服务端"——key 一旦放进 HTML 就泄露了。
>
> 替代方案：
> - 用户自己的 API key 改成走他们自己的浏览器（OpenAI 兼容 endpoint 可以）
> - 不支持的 SaaS 私 API：等 v0.2 的 "local proxy mode"
> - 完全跳过这一步：如果这个 API 调用是装饰性的，可以重写 skill 跳过它

### `refusal: needs-binary-anchor`

> 这个 skill 严格依赖一张 binary 风格锚图片（`<file>`）来保证视觉一致。但 LICENSE 不明确允许二次分发这个图片。
>
> 替代方案：
> - 联系 skill 作者拿到分发授权 → 加进 IR.static_assets.reference_image
> - 接受视觉降级：用 text-only reference clause（v0.1 默认走这个）。注意：视觉会"像但不完全像"。

### `refusal: kind-not-yet-supported`

> 这个 skill 的输出是 `<kind>`，v0.1 还不支持。
>
> v0.2 计划支持：template-html, pptx-canvas。
> v0.3 计划支持：png-canvas, zip-bundle。
>
> 现在能做的：
> - 等版本升级
> - 如果 skill 其实可以降级成 image-per-slide（比如 markdown 报告可以渲染成 PNG），告诉我你愿意降级，我们继续。

### `refusal: not-a-skill` / `unclear-workflow` / `agent-branching` / `large-input` / `folder-input` / `needs-fs`

短消息即可，说明原因 + 给一个具体建议。

---

## After a successful judgment (compilable)

Surface the verdict in plain language at USER GATE 1:

> ✅ 这个 skill 可以编译。
>
> 我的判断：
> - 类型：流程化、image-per-slide
> - LLM 调用次数：1 次（intake + planning + spine 合并）
> - 渲染：N 张 PNG（N = 用户输入的页数）
> - 浏览器依赖：openai-images-compat + openai-chat-compat（都在 mapper 里）
> - 风格锚：text-only reference clause（不内嵌图片，因为 LICENSE 模糊）
> - 已知 caveat：21:9 cover 用 1536×1024 代（gpt-image-2 不原生支持 21:9）
>
> 继续抽 IR 吗？（y / 改判定 / 还有什么我没想到的）
