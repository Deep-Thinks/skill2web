---
name: skill2web
description: Compile a flow-shaped Claude skill (input → 1-3 LLM calls → render → output) into a single-file HTML web tool that non-agent users can open and use directly. Use when the user asks to "make this skill into a web page", "compile a skill to HTML", "package a skill so my friend without Claude Code can use it", "turn this PPT/poster/recipe skill into a website", "build a no-agent runtime for a skill", or shares a GitHub URL of a Claude skill and asks for a shareable web link. Output is a self-contained `.html` file users can drop on GitHub Pages / Surge / WeChat. Build-time uses agent + LLM; run-time is pure browser, no agent.
---

# skill2web

Compile a flow-shaped Claude skill into a single-file HTML web tool. The user this skill talks to is a **skill author** (already comfortable with Claude Code); the eventual user of the compiled output is a **non-agent person** who just opens the HTML.

## Core thesis

**Build-time is agent, run-time is not.** The skill being compiled may contain LLM calls and rendering; this skill moves all `agent`-shaped complexity into compile time and emits a static, single-file artifact.

If a skill cannot be reduced to `inputs → N LLM calls → templated render → output`, it is **not compilable today** — refuse early with a friendly explanation rather than producing a broken page.

## Operating Rule

This skill produces exactly **one `.html` file** plus **one `.README.md` file** per compile. No build pipeline, no bundler config, no `node_modules`, no CDN dependency at run-time. The `.html` opens in any modern browser; the end user pastes their own LLM/image API key on first open (stored in `localStorage`).

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

- **compilable**: proceed to phase 3
- **refuse**: write a refusal message using a template from the checklist. **Stop.** Do not try to "make it work anyway."

**USER GATE 1**: After your judgment but before extraction, surface the analyzer verdict in plain language:

> 我判定这个 skill 是 **可编译的（流程化、image-per-slide 类型）**。理由：…。接下来我会抽 IR。继续吗？

The user may override your verdict. If they say "refuse anyway" or "but try this anyway", trust them.

### Phase 3 — extractor

Read `references/ir-schema.md`. Your job is to fill the IR JSON. The IR has eight top-level fields; the hardest is `static_assets` (raw text blocks copied verbatim from `references/`) and `llm_phase.system_prompt_template` (built by you, with the user's confirmation).

Extraction sources:

| IR field | Where to look in source skill |
|---|---|
| `skill_meta` | `SKILL.md` frontmatter + `LICENSE` + `NOTICE.md` + `README.md` |
| `static_assets.style_lock` / `role_locks` / `reference_clauses` | Code-fenced blocks (` ```text `) in `references/prompt-patterns.md` or equivalent |
| `static_assets.archetypes` | Lists in `references/*archetypes*.md` |
| `static_assets.theme_tokens` | `assets/theme-tokens.json` if present, else inferred from text |
| `input_schema` | Inferred. Not declared in SKILL.md → **ask the user what fields make sense** |
| `llm_phase.system_prompt_template` | You draft, citing the source skill's "Workflow" section verbatim where possible |
| `llm_phase.expected_output_schema` | You draft based on what the render phase needs |
| `render_phase.kind` | One of: `image-per-slide` / `template-html` / `pptx-canvas` / `png-canvas`. Decide from `SKILL.md` "Operating Rule". |
| `render_phase.per_item.prompt_template` | Composes static_assets + iterator item fields. For image-per-slide skills, mirror the source skill's "Complete Page Image Prompt" template. |
| `browser_runtime` | Defaults from `references/lib-mapper.md`; user picks providers |
| `error_ux` | You draft, user edits |
| `attribution` | Direct from `LICENSE` + `NOTICE.md` |

**USER GATE 2**: When the IR JSON is ready, show it to the user (formatted, foldable sections) and ask:

> IR 草稿如下。`input_schema` 的字段你看合理吗？`llm_phase.system_prompt_template` 我用了 skill 的 Workflow 第 X 段作为骨架，你想改吗？`error_ux` 我起草了中文版，要不要换语气？

Iterate until the user says "可以" (or equivalent). Save the confirmed IR to `dist/<skill-name>.ir.json` for future re-compiles.

### Phase 4 — mapper

Read `references/lib-mapper.md`.

For every `lib_deps` entry in the source skill (look at imports in any bundled scripts, plus any `pip install` hints in SKILL.md / README.md), find a row in the mapper. If a library is **not in the mapper**, you have three choices:

1. Refuse compile (back to phase 2 with refusal reason).
2. Add a new row to `lib-mapper.md` — but only if you can confidently confirm coverage. **USER GATE 3**: ask the user before adding new rows; lib-mapper.md is project canon.
3. Ask the user if they'll provide a fallback (e.g. "this skill calls `python-magic`; we have no browser equivalent. Want to use a dumb MIME guess instead?").

Also pick **providers** at this gate:

| Choice | Default | Why |
|---|---|---|
| LLM provider | `https://api.deepseek.com/v1` + `deepseek-chat` | Cheap, OpenAI-compatible. StepFun (`https://api.stepfun.com/v1`) is a known working alternative. |
| Image provider | `https://image.token-recyclebin.com/v1` + `gpt-image-2` | Best Chinese text rendering in tested options. Skip if `render_phase.kind != image-per-slide`. |

Tell the user: "默认 provider 是 X。可以换吗？" Their answer locks into IR.browser_runtime.

### Phase 5 — composer

Read `templates/base.html` (the canonical HTML skeleton, distilled from the `ian-handdrawn-ppt` hero case). It contains `{{MUSTACHE}}`-style placeholders that map 1:1 to IR fields.

In v0.1, the composer **does not call frontend-design**. It just fills the template. UI quality is whatever the template gives — that is intentional per DESIGN.md (Unix composition is a v0.2 concern).

Substitute every `{{…}}` placeholder. Failure to substitute one is a bug; emit a warning and ask the user.

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
- **HTML template**: `skill/templates/base.html`
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

- v0.1 supports `render_phase.kind = image-per-slide` only (validated via the `ian-handdrawn-ppt` hero case).
- v0.2 (planned): add `template-html` (markdown / report-style skills), `pptx-canvas` (slides with editable text overlay), and `frontend-design` integration for UI variety.
- See `../DESIGN.md` for the broader plan and `../hero-cases/ian-handdrawn-ppt/LESSONS.md` for what's known to work.

## Final response (when finishing a compile)

Report:

- Source skill name + URL + license
- Output file path + size
- IR decisions worth flagging (e.g. "用了 gpt-image-2 兼容 endpoint，21:9 cover 用 1536×1024 代")
- Any rows you added to `lib-mapper.md`
- Verification done (syntax check, footer check, manual smoke test status)
- Whether the user should `git add` the output (default: yes, since `dist/` is meant to be sharable)
