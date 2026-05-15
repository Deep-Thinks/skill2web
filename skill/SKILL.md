---
name: skill2web
description: Compile a flow-shaped Claude skill (input → 1-3 linear LLM calls → render → output) into a single-file HTML web tool that non-agent users can open and use directly. v0.2 supports three ir_kinds — image-deck (per-page images), template-html (markdown / report), png-canvas (single poster). Use when the user asks to "make this skill into a web page", "compile a skill to HTML", "package a skill so my friend without Claude Code can use it", "turn this PPT/poster/recipe/document skill into a website", "build a no-agent runtime for a skill", or shares a GitHub URL of a Claude skill and asks for a shareable web link. Output is a self-contained `.html` file users can drop on GitHub Pages / Surge / WeChat. Build-time uses agent + LLM; run-time is pure browser, no agent.
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
3. pause for user input at six decision gates listed below, and
4. write outputs only after the user confirms the IR.

This skill is **not** a CLI; it is conversational. Treat user pushback at any gate as authoritative.

## Compile workflow

Six phases. Read the matching `references/` file when entering a phase — do not preload all references.

```
1. loader     ── clone / read source skill           (mechanical)
2. analyzer   ── decide: compilable or refuse?       (LLM judgment + USER GATE 1)
3. extractor  ── pull IR (intermediate representation)(LLM + USER GATE 2: confirm IR)
4. mapper     ── map python libs → browser libs      (lookup + USER GATE 3: pick adapters)
5. composer   ── compose HTML from template + IR     (template fill — fixed in v0.1)
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
| `llm_pipeline[*].system_prompt_template` | You draft, citing the source skill's "Workflow" section verbatim where possible. Default to **single step**(id="plan");仅当 source skill 有"两轮 LLM(intake → spine)"形态再拆 2-3 step。每个 step 的 `uses` 只能引前序 step。 |
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

> IR 草稿如下。`input_schema` 的字段你看合理吗？`llm_phase.system_prompt_template` 我用了 skill 的 Workflow 第 X 段作为骨架，你想改吗？`error_ux` 我起草了中文版，要不要换语气？

Iterate until the user says "可以" (or equivalent). Save the confirmed IR to `dist/<skill-name>.ir.json` for future re-compiles.

### Phase 4 — mapper

Read `references/adapters.md` (API 调用契约) 与 `references/render-libs.md` (inline JS lib)。

For every `lib_deps` entry in the source skill (look at imports in any bundled scripts, plus any `pip install` hints in SKILL.md / README.md), find a row in either file. If a library is **not in either file**, you have three choices:

1. Refuse compile (back to phase 2 with refusal reason).
2. Add a new row — but只有当你能自信确认 coverage。**USER GATE 3b**: 加 row 前问用户; 这两个文件都是 project canon。
3. Ask the user if they'll provide a fallback (e.g. "this skill calls `python-magic`; we have no browser equivalent. Want to use a dumb MIME guess instead?").

Also pick **providers** at this gate. **All v0.1 defaults are `unverified` for browser CORS** (see `references/lib-mapper.md`). State this risk explicitly:

| Choice | Default | Status | Why |
|---|---|---|---|
| LLM provider | `https://api.deepseek.com/v1` + `deepseek-chat` | unverified | Cheap, OpenAI-compatible. Used in sibling project's **Python backend** but not browser-tested. |
| Image provider | `https://image.token-recyclebin.com/v1` + `gpt-image-2` | unverified | Best Chinese-text rendering in known options; chosen as hero-case default. **Browser CORS untested.** |

Word the gate to the user as:

> 默认 provider 是 X / Y。但**两者的浏览器端 CORS 还没实测过**——只在 Python 后端跑过。第一次跑 hero case 时撞 CORS 错的概率不低；遇到了要么换 endpoint，要么本地 Python 反向代理一下。你接受这个风险，还是想现在切到一个已知 CORS 友好的 (OpenAI 官方 / Anthropic direct-browser)？

Lock the user's answer into IR.browser_runtime.default_endpoints. If the user **does verify** a provider end-to-end during this compile, ask them to add an entry to the Verification log in `references/lib-mapper.md` before phase 6.

### Phase 5 — composer (v0.2 三步组装)

v0.2 把单模板 `base.html` 拆成 `templates/skeleton.html` (通用骨架) + `templates/blocks/<kind>.html` (per-kind UI/render) + `templates/adapters/<name>.js` (API wrapper)。Composer 三步组装:

1. **取骨架**: 读 `templates/skeleton.html`
2. **注入 block**: 按 `IR.ir_kind` 选 `blocks/<kind>.html`,替换 skeleton 的 BLOCK 标记
3. **注入 adapter**: 按 `IR.browser_runtime.{llm,image}_adapter` inline `adapters/*.js`
4. **placeholder 替换**: 所有 `{{IR.X.Y|filter}}` 用 IR 值替换

实际跑:

```bash
python3 skill/compose.py <ir.json> dist/<skill-name>.html
```

详见 `references/compiler-workflow.md` Phase 5。v0.2 composer 仍**不**调 frontend-design;UI 质量由 skeleton + block 决定(同 v0.1 哲学,frontend-design 集成推迟到 v0.3)。

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
- **Image provider**: `https://image.token-recyclebin.com/v1` model `gpt-image-2` (only when render_phase.kind needs images)
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

## Status

**v0.2 honest scope** (2026-05-15, ship per DESIGN-v0.2.md):

- ✅ Supports three `ir_kind` values:
  - `image-deck` — per-page image deck (例: ian-handdrawn-ppt; 通过回归编译验证)
  - `template-html` — markdown / report 输出 (例: synthetic-essay-polisher hero case 2 → composer 自动版本)
  - `png-canvas` — 单图封面 (例: guizang-cover 合成 IR)
- ✅ `llm_pipeline` 数组化 (1-3 step, 严格线性, `uses` 只能引前序)
- ✅ Skeleton + block + adapter 三步组装 composer (`skill/compose.py`)
- ✅ v0.1 → v0.2 IR migration (`skill/migrate_v01_to_v02.py`)
- ✅ Analyzer kind router + step 9 运行环境等价性检查; 5 类新 refusal 模板 (needs-headless-browser / needs-fs / needs-third-party-fetch / layout-too-complex / private-api 等)
- 🔬 Spike-gated (per DESIGN §11):
  - `pptx-canvas` — 仅 schema 草案; D-spike 通过才进 v0.2 实装,否则推 v0.3 / 转 refusal
  - `data-table` — 仅 schema 草案; E-minimal spike 同上
- ❌ Does **not** integrate `frontend-design` skill (推迟到 v0.3, 同 v0.1 哲学)
- ❌ Does **not** support DAG `llm_pipeline` (分叉 / 合流 = agent-shaped, analyzer 拒)
- ⚠️ Provider endpoint browser CORS 仍 `unverified` (见 `references/adapters.md` Verification log)。USER GATE 3a 必须 surface 该风险。

输出 `.html` 是 **single-file source** (无 run-time CDN), 但需要 HTTP 服务 (浏览器对 `file://` 的 `fetch()` 限制)。用 `python3 -m http.server` / GitHub Pages / Surge / Cloudflare Pages。

详见 `../DESIGN.md` (v0.1) + `../DESIGN-v0.2.md` (v0.2 演化) + `../hero-cases/*/LESSONS.md`。

## Final response (when finishing a compile)

Report:

- Source skill name + URL + license
- Output file path + size
- IR decisions worth flagging (e.g. "用了 gpt-image-2 兼容 endpoint，21:9 cover 用 1536×1024 代")
- Any rows you added to `lib-mapper.md`
- Verification done (syntax check, footer check, manual smoke test status)
- Whether the user should `git add` the output (default: yes, since `dist/` is meant to be sharable)
