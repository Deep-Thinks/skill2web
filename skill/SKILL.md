---
name: skill2web
description: Compile a flow-shaped Claude skill (input → 1-3 LLM calls, linear or static-DAG → render → output) into a single-file HTML web tool that non-agent users can open and use directly. v0.2 supports three ir_kinds — image-deck (per-page images), template-html (markdown / report), png-canvas (single poster). Use when the user asks to "make this skill into a web page", "compile a skill to HTML", "package a skill so my friend without Claude Code can use it", "turn this PPT/poster/recipe/document skill into a website", "build a no-agent runtime for a skill", or shares a GitHub URL of a Claude skill and asks for a shareable web link. Output is a self-contained `.html` file users can drop on GitHub Pages / Surge / WeChat. Build-time uses agent + LLM; run-time is pure browser, no agent.
---

# skill2web

Compile a flow-shaped Claude skill into a single-file HTML web tool. The user this skill talks to is a **skill author** (already comfortable with Claude Code); the eventual user of the compiled output is a **non-agent person** who just opens the HTML.

## Core thesis

**Build-time is agent, run-time is not.** The skill being compiled may contain LLM calls and rendering; this skill moves all `agent`-shaped complexity into compile time and emits a static, single-file artifact.

If a skill cannot be reduced to `inputs → N LLM calls → templated render → output`, it is **not compilable today** — refuse early with a friendly explanation rather than producing a broken page.

## Operating Rule

This skill produces exactly **one `.html` file** plus **one `.README.md` file** per compile. The `.html` is **single-file source** — no build pipeline, no bundler config, no `node_modules`, no run-time CDN dependency. The end user pastes their own LLM/image API key on first open (stored in `localStorage`).

**Important caveat (not optional)**: the `.html` should be **served over `http://`** (localhost / GitHub Pages / Surge / Cloudflare Pages — anything HTTP). Most modern browsers block `fetch()` from `file://` origins, and a number of provider CORS configurations treat `file://` differently from `http://`. The README emitted in Phase 6 must tell the user this; the compiler must not pretend "double-click and it works."

The compile run-time **is** an LLM agent (this skill's caller). It is expected to:

1. read source skill files,
2. judge compilability and *refuse loudly* when unsure rather than produce a broken artifact,
3. pause for user input at the four user gates listed below (GATE 3 splits into 3a/3b in the mapper phase), and
4. write outputs only after the user confirms the IR.

This skill is **not** a CLI; it is conversational. Treat user pushback at any gate as authoritative.

## Compile workflow

Six phases. Read the matching `references/` file when entering a phase — do not preload all references.

```
1. loader     ── clone / read source skill           (mechanical)
2. analyzer   ── decide: compilable or refuse?       (LLM judgment + USER GATE 1)
3. extractor  ── pull IR (intermediate representation)(LLM + USER GATE 2: confirm IR)
4. mapper     ── map python libs → browser libs      (lookup + USER GATE 3: pick adapters)
5. composer   ── frontend-design pass + compose HTML  (强制设计 + 模板填充)
6. emitter    ── write dist/<name>.html + README     (mechanical + USER GATE 4: license check)
```

Each phase is detailed in `references/compiler-workflow.md`. Do not skip the user gates — they exist because most failures in hand-compiling were avoidable confusions that user input would have caught immediately.

### Phase 1 — loader

Inputs: a GitHub URL, a local path, or a zip. Default is GitHub URL.

```bash
# clone to a scratch dir outside the project
mkdir -p /tmp/skill2web-refs
cd /tmp/skill2web-refs
git clone --depth=1 <repo-url>
```

Locate `SKILL.md`. Source skills sometimes nest it (e.g. `<repo>/<skill-name>/SKILL.md`); use `find . -name SKILL.md` to confirm exactly one match. If multiple, ask the user which.

### Phase 2 — analyzer

Read `references/analyzer-checklist.md`.

Outputs one of:

- **compilable** (无降级): proceed to phase 3
- **compilable WITH 降级** (v0.2.1, 见 checklist §4.5 / §4.6): 列出每一条降级 (原 skill 的 X 步 → IR 替换为 Y), 在 USER GATE 1 让用户**明确接受**才进 phase 3
- **refuse**: write a refusal message using a template from the checklist. **Stop.** Do not try to "make it work anyway."

**USER GATE 1**: After your judgment but before extraction, surface the analyzer verdict in plain language:

> 我判定这个 skill 是 **可编译的（`<ir_kind>`，<是否降级>）**。理由：…。
>
> 若走了降级路径 (§4.6),逐条列:
> - 原 skill step / phase: <X>
> - IR 替换: <Y> (例: 改为 user 上传 README + 截屏列表)
> - 这块**损失**: <Z> (例: 失去了从代码自动推断 benefit 的能力)
>
> 接下来我会抽 IR。继续吗?(y / 改判定 / **不接受这个降级**)

The user may override your verdict. If they say "refuse anyway" or "but try this anyway" or "不接受降级", trust them — 用户说不接受降级 = 等价 refuse。

### Phase 3 — extractor

Read `references/ir-core.md` 与 `references/ir-kinds/<ir_kind>.md`. Your job is to fill the v0.2 IR JSON. IR 顶层 8 字段(universal: skill_meta / input_schema / llm_pipeline / browser_runtime / error_ux / attribution / render + meta: ir_version / ir_kind),最难的是 `render.static_assets` (raw text 来自 source `references/`) 与 `llm_pipeline[*].system_prompt_template` (由你起草, 用户确认)。

Extraction sources:

| IR field | Where to look in source skill |
|---|---|
| `skill_meta` | `SKILL.md` frontmatter + `LICENSE` + `NOTICE.md` + `README.md` |
| `input_schema` | Inferred. Not declared in SKILL.md → **ask the user what fields make sense** |
| `llm_pipeline[*].system_prompt_template` | You draft, citing the source skill's "Workflow" section verbatim where possible. Default to **single step**(id="plan");仅当 source skill 有"两轮 LLM(intake → spine)"形态再拆 2-3 step。每个 step 的 `uses` 只能引前序 step。v0.3:若 skill 有**编译期已知的有限分支**,可用静态 DAG(分类 step + 带 `when` 的分支 step + 总执行的 merge step,见 `references/ir-core.md §3.4`)。 |
| `llm_pipeline[*].expected_output_schema` | You draft based on what the render phase needs |
| `browser_runtime.llm_adapter` / `image_adapter` | Defaults from `references/adapters.md`; user picks providers at USER GATE 3a |
| `browser_runtime.image_adapter` | **null** if `ir_kind=template-html`; `openai-images-compat` for image-deck / png-canvas |
| `render` (kind-specific shape) | 见 `references/ir-kinds/<ir_kind>.md`: |
| ↳ `image-deck` | `render.static_assets.{style_lock, role_locks, reference_clauses, archetypes, theme_tokens}` + `render.iterator` + `render.per_item.{prompt_template, size_by_role, api, endpoint_mode}` |
| ↳ `template-html` | `render.{output_form, template_html?, css_lock?, data_binding, sanitizer, features}` |
| ↳ `png-canvas` | `render.{canvas_size, static_assets.{style_lock, reference_clauses}, prompt_template, data_binding?, api, endpoint_mode, compositing="none", fonts}` |
| `error_ux` | You draft, user edits |
| `attribution` | Direct from `LICENSE` + `NOTICE.md` |

**USER GATE 2**: When the IR JSON is ready, show it to the user (formatted, foldable sections) and ask:

> IR 草稿如下。`input_schema` 的字段你看合理吗？`llm_pipeline[*].system_prompt_template` 我用了 skill 的 Workflow 第 X 段作为骨架，你想改吗？`error_ux` 我起草了中文版，要不要换语气？

Iterate until the user says "可以" (or equivalent). Save the confirmed IR to `dist/<skill-name>.ir.json` for future re-compiles.

### Phase 4 — mapper

Read `references/adapters.md` (API 调用契约) 与 `references/render-libs.md` (inline JS lib)。

For every `lib_deps` entry in the source skill (look at imports in any bundled scripts, plus any `pip install` hints in SKILL.md / README.md), find a row in either file. If a library is **not in either file**, you have three choices:

1. Refuse compile (back to phase 2 with refusal reason).
2. Add a new row — but只有当你能自信确认 coverage。**USER GATE 3b**: 加 row 前问用户; 这两个文件都是 project canon。
3. Ask the user if they'll provide a fallback (e.g. "this skill calls `python-magic`; we have no browser equivalent. Want to use a dumb MIME guess instead?").

Also pick **providers** at this gate. **All v0.1 defaults are `unverified` for browser CORS** (see `references/adapters.md`). State this risk explicitly:

| Choice | Default | Status | Why |
|---|---|---|---|
| LLM provider | `https://api.deepseek.com/v1` + `deepseek-chat` | unverified | Cheap, OpenAI-compatible. Used in sibling project's **Python backend** but not browser-tested. |
| Image provider | `https://image.token-recyclebin.com/v1` + `gpt-image-2` | unverified | Best Chinese-text rendering in known options; chosen as hero-case default. **Browser CORS untested.** |

Word the gate to the user as:

> 默认 provider 是 X / Y。但**两者的浏览器端 CORS 还没实测过**——只在 Python 后端跑过。第一次跑 hero case 时撞 CORS 错的概率不低；遇到了要么换 endpoint，要么本地 Python 反向代理一下。你接受这个风险，还是想现在切到一个已知 CORS 友好的 (OpenAI 官方 / Anthropic direct-browser)？

Lock the user's answer into IR.browser_runtime.default_endpoints. If the user **does verify** a provider end-to-end during this compile, ask them to add an entry to the Verification log in `references/adapters.md` before phase 6.

### Phase 5 — design pass + composer

#### 5.0 frontend-design pass (v0.3 — 强制,不可跳过)

在跑 `compose.py` **之前**,必须调用 `frontend-design` skill,为本次编译产出一套与源 skill 主题相称的视觉方案。给 frontend-design 的上下文:`IR.skill_meta`(主题 / 受众)、`IR.ir_kind`(决定主视觉区形态)、`IR.input_schema`(表单字段)、skeleton 默认皮肤 + 对应 `blocks/<kind>.html` 的 kind 样式。

要它产出**一段覆盖型 raw CSS**(不是整页重写),收进 `IR.theme_overrides`(见 `references/ir-core.md §8`,composer 会 inline 到 `<style>` 末尾)。硬约束:只放 CSS,不引远程字体 / CDN / `<script>` / `url(http...)` —— 违反单文件 + 无运行时依赖规则的产出,编译 agent 必须 inline 化或剔除。

把方案向用户简述(配色 / 字体走向 / 与 skill 主题的关系)。用户可改可跳过具体条目,但**不能跳过这一步本身**。frontend-design 若判定默认皮肤已合适,可返回空 `theme_overrides` —— 但那必须是它**看过之后的判断**,不是省略掉这一步。

#### 5.1 composer (三步组装)

v0.2 把单模板 `base.html` 拆成 `templates/skeleton.html` (通用骨架) + `templates/blocks/<kind>.html` (per-kind UI/render) + `templates/adapters/<name>.js` (API wrapper)。Composer 三步组装:

1. **取骨架**: 读 `templates/skeleton.html`
2. **注入 block**: 按 `IR.ir_kind` 选 `blocks/<kind>.html`,替换 skeleton 的 BLOCK 标记
3. **注入 adapter**: 按 `IR.browser_runtime.{llm,image}_adapter` inline `adapters/*.js`
4. **placeholder 替换**: 所有 `{{IR.X.Y|filter}}` 用 IR 值替换

实际跑:

```bash
python3 skill/compose.py <ir.json> dist/<skill-name>.html
```

详见 `references/compiler-workflow.md` Phase 5。v0.3 起 composer 本身仍是纯模板填充,但 UI 质量由 skeleton + block + **5.0 强制 frontend-design pass 产出的 `theme_overrides`** 共同决定。

未解析的 placeholder 会在 stderr 报警 — agent 必须把警告 surface 给用户。

### Phase 6 — emitter

Write two files into `<project>/dist/`:

1. `<skill-name>.html` — the compiled single-file artifact.
2. `<skill-name>.README.md` — short user-facing instructions: how to open, how to get API keys, attribution, license.

Verify:

- File is < 100 KB (unless it carries large inlined libs from mapper).
- `<html>` element is well-formed (run a syntax check on the script block via `node -e 'new Function(...)'` like the hero-case Day 1 commit did).
- Attribution to source author appears in the footer of the HTML and in the README.

**USER GATE 4**: Print the file path, line count, and footer attribution text. Ask:

> 编译完成：`dist/<skill-name>.html`（N 行）。署名页脚是：…。看一下，OK 我就结束。

## Defaults

Use these unless the user says otherwise:

- **Output directory**: `<project-root>/dist/`
- **Scratch directory** (cloned source skills): `/tmp/skill2web-refs/`
- **HTML skeleton**: `skill/templates/skeleton.html`(三步组装的骨架)
- **HTML blocks**: `skill/templates/blocks/<ir_kind>.html`(per-kind UI/render)
- **HTML adapters**: `skill/templates/adapters/<adapter>.js`(API 调用 wrapper)
- **LLM provider**: `https://api.deepseek.com/v1` model `deepseek-chat`
- **Image provider**: `https://image.token-recyclebin.com/v1` model `gpt-image-2` (only when `ir_kind` is `image-deck` / `png-canvas`)
- **Concurrency** for batched API calls in output: `3`
- **Timeouts** in output: LLM `120s`, image `180s`
- **Retry** in output: 1 retry per failed item
- **Key storage** in output: `localStorage` only, never URL/query/hash

## Hard rules (do not violate without user override)

1. **Never** ship API keys in the compiled HTML. The output asks the user to paste their own.
2. **Never** put API keys in URL/query/hash — only `localStorage`.
3. **Never** add a run-time CDN dependency to the output. Inline everything.
4. **Always** preserve the source skill's license file and author attribution in the output footer and README.
5. **Never** silently widen scope: if a skill needs anything outside the IR's known fields, surface it as a user question, not a guess.
6. **Always** refuse early when phase 2 is uncertain — broken HTML wastes more time than a clean refusal.
7. **Always** run the frontend-design pass (Phase 5.0) before composing — invoke the `frontend-design` skill and feed its result into `IR.theme_overrides`. Never skip the pass; an empty `theme_overrides` is only valid as frontend-design's considered verdict, not as an omission.
8. **`theme_overrides` is CSS-only** — no `<script>`, no remote `@import` / CDN / web-font URL. It must not breach hard rule 3.

## Status

**v0.3 honest scope** (2026-05-18, ship per DESIGN-v0.3.md):

- ✅ Supports three `ir_kind` values:
  - `image-deck` — per-page image deck (例: ian-handdrawn-ppt, wuman-brief-to-poster)
  - `template-html` — markdown / report 输出 (例: synthetic-essay-polisher, prompt-master)
  - `png-canvas` — 单图封面 (例: guizang-cover)
- ✅ `llm_pipeline` 是**静态 DAG** (v0.3): `uses` 可多父(合流), step 可带 `when` 结构化分支条件(分叉); 图必须编译期完全已知且有限; runtime 按拓扑序执行 + 条件跳过(skip 传播 = 全父跳过才跳)
- ✅ Skeleton + block + adapter 三步组装 composer (`skill/compose.py`); 同时接受 `ir_version` 0.2 / 0.3
- ✅ **强制 frontend-design pass** (Phase 5.0): 编译前必须调 `frontend-design` skill, 产出收进 `IR.theme_overrides`
- ✅ v0.1 → v0.2 IR migration (`skill/migrate_v01_to_v02.py`); v0.2 → v0.3 无需迁移(严格超集)
- ✅ Analyzer kind router + step 9 运行环境等价性 + §4 "静态 DAG vs agent-shape" 判定
- 🔬 Spike-gated (per DESIGN §11): `pptx-canvas` / `data-table` 仅 schema 草案
- ❌ Does **not** support unbounded / dynamic control flow (循环 / 轮数 / 图形状运行时才定 = agent-shaped, analyzer §4 拒)
- ⚠️ Provider endpoint browser CORS 仍 `unverified` (见 `references/adapters.md` Verification log)。USER GATE 3a 必须 surface 该风险。

输出 `.html` 是 **single-file source** (无 run-time CDN), 但需要 HTTP 服务 (浏览器对 `file://` 的 `fetch()` 限制)。用 `python3 -m http.server` / GitHub Pages / Surge / Cloudflare Pages。

详见 `../DESIGN.md` (v0.1) + `../DESIGN-v0.2.md` (v0.2 演化) + `../DESIGN-v0.3.md` (v0.3 演化) + `../hero-cases/*/LESSONS.md`。

## Final response (when finishing a compile)

Report:

- Source skill name + URL + license
- Output file path + size
- IR decisions worth flagging (e.g. "用了 gpt-image-2 兼容 endpoint，21:9 cover 用 1536×1024 代")
- Any rows you added to `references/adapters.md` / `references/render-libs.md`
- Verification done (syntax check, footer check, manual smoke test status)
- Whether the user should `git add` the output (default: yes, since `dist/` is meant to be sharable)
