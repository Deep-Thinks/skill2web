# Compiler Workflow

The full step-by-step playbook for a `skill2web` compile run. Read this when you (the main agent) are actively compiling — `SKILL.md` is the high-level entry; this is the operational detail.

The workflow is **conversational**. There are four mandatory user gates. Skipping a gate is a defect — most hand-compile failures were caused by *not asking*.

## Phase 0 — Receive the request

The user typically says one of:

- "把 `<github-url>` 编译成单文件网页"
- "把这个 skill 做成网页让朋友用"
- "compile this skill to HTML: `<github-url>`"

If they didn't give a URL/path, ask:

> 你要编译哪个 skill？提供 GitHub URL 或本地路径都行。

Confirm the **output destination**. Default `./dist/`. If `./dist/` doesn't exist, create it (`mkdir -p ./dist`).

## Phase 1 — Loader

```bash
# 1. ensure scratch directory exists
mkdir -p /tmp/skill2web-refs

# 2. clone (shallow)
cd /tmp/skill2web-refs && git clone --depth=1 <repo-url>

# 3. find SKILL.md — there may be more than one
find /tmp/skill2web-refs/<repo-name>/ -name SKILL.md
```

If `find` returns 0 results: refuse with `not-a-skill`.

If `find` returns >1 result: ask the user which one is the target. Sometimes a repo bundles multiple skills (`<repo>/skill-a/SKILL.md`, `<repo>/skill-b/SKILL.md`).

Read the chosen `SKILL.md`. Note the `name`/`description` from frontmatter — they go into IR.skill_meta.

Read `LICENSE`, `NOTICE.md` if present. If no LICENSE: stop and ask (per `ir-schema.md §8`). Do not invent one.

Quick scan of the directory:

```bash
ls -la /tmp/skill2web-refs/<repo>/<skill-path>/
find /tmp/skill2web-refs/<repo>/<skill-path>/ -type f -not -path '*/\.git/*'
```

Note any:
- `references/` — these are static_asset goldmines
- `assets/` — theme tokens, style anchors
- `*.py` / `*.sh` / `Dockerfile` — dependency signals
- `requirements.txt` / `pyproject.toml` — dependency declarations
- `examples/` — useful for understanding intent

## Phase 2 — Analyzer

Read `analyzer-checklist.md`. Run the 8-step decision tree. Stop at the first refusal trigger.

If you reach the bottom: surface **USER GATE 1** with the verdict.

After USER GATE 1, **save your analysis** to `<output-dir>/<skill-name>.analyzer.md` (a short markdown with the verdict, the trigger evidence quoted from source SKILL.md, and the caveats list). This is build-time documentation; it is useful if you re-compile later and want to remember why you made each call.

## Phase 3 — Extractor

Read `ir-schema.md`. Build the IR step by step. **Order matters** — later fields reference earlier ones.

### 3.1 `skill_meta`

- `name`: from SKILL.md frontmatter
- `display_name`: friendly title; usually the SKILL.md first `# Heading`
- `description`: usually the frontmatter `description`, trimmed to ≤ 200 chars
- `source.url`: the git URL the user provided
- `source.path_inside_repo`: the relative path you found SKILL.md in (often `<skill-name>/`)
- `license`, `author`, `author_links`: from LICENSE + NOTICE.md + README.md links

### 3.2 `static_assets`

This is the most failure-prone step. The hand-compile experience: **do not paraphrase. Copy strings verbatim.**

For prompt-shaped skills (image-per-slide kind):

```bash
# find the prompt patterns file
find /tmp/skill2web-refs/<repo>/ -iname 'prompt*' -o -iname '*prompt*'
```

Inside that file, look for fenced text blocks (` ```text ` … ` ``` `). Each major block is a static asset. Common names:

- "Deck Style Lock" / "Style Lock" → `static_assets.style_lock`
- "Page Role: cover image" → `static_assets.role_locks.cover`
- "Page Role: body illustration" → `static_assets.role_locks.body`
- "Reference Match Clause" → `static_assets.reference_clauses[0]`

For each block, copy the **entire contents between the fence markers** as a JS string. Preserve newlines exactly (`\n`). The composer will pass them through unmodified into the output HTML.

For `archetypes`:

```bash
# usually in references/slide-archetypes.md or similar
grep -i 'archetype\|layout\|category' /tmp/skill2web-refs/<repo>/.../references/*.md
```

Pull the canonical names (usually from a table or bullet list with one short identifier per row). They become an array of strings.

For `theme_tokens`:

```bash
# check for a tokens file
find /tmp/skill2web-refs/<repo>/ -name '*tokens*.json' -o -name '*theme*.json'
```

If present, read it. **Subset, don't copy whole**: the IR field only carries what the output template references. Typical subset:
- `paper` / `ink` colors (for CSS variables in output HTML)
- `size_by_role` map (for image-API size parameter)

If the original tokens use ratios (`"cover_ratio": "21:9"`), translate to concrete pixel sizes the image API supports. **Note the substitution as a caveat for USER GATE 2** — the user may want to crop client-side instead.

### 3.3 `input_schema`

This is **not in SKILL.md**. You must infer. Read the SKILL.md "Workflow" section and "Defaults" section. Look for:

- Lines like "the user provides X" / "input: X"
- Defaults the user might want to override (length, audience, format)

Draft a **first guess** of 3-6 fields. Then ask the user at USER GATE 2 to confirm.

Common patterns:

| Skill type | Likely input_schema fields |
|---|---|
| Article → PPT | `content` (textarea), `audience` (text), `scenario` (select), `length` (select) |
| Topic → poster | `topic` (text), `style` (select), `aspect` (select) |
| Recipe → image | `dish` (text), `cuisine` (select), `mood` (select) |
| Markdown → document | `content` (textarea), `format` (select: docx/pdf), `font_family` (select) |

### 3.4 `llm_phase`

Draft the `system_prompt_template`. Start from the source SKILL.md's "Workflow" section — quote it as guidance to the LLM. Then add **strict JSON output rules**:

```text
You are the planner for <DISPLAY_NAME>. Read the user's content and output a deck spine JSON ...

Output schema (strict):
{{LLM_OUTPUT_SCHEMA_INLINE}}

Rules:
1. Output ONLY JSON. No prose, no markdown.
2. Field <X> must be one of: <enum>.
3. <Skill-specific rule, e.g. titles ≤ 12 chars>.
```

Draft `user_prompt_template` referencing `{{...}}` placeholders for every input_schema key.

Draft `expected_output_schema` (JSON Schema). This is the contract the LLM must satisfy; the output HTML validates against it. Be permissive on optional fields, strict on required ones.

`json_mode`: default `prompt-only` (most compatible). Only set `response-format` if you've verified the LLM provider supports it for this model.

### 3.5 `render_phase`

- `kind`: pick one from analyzer phase 8 (v0.1: only `image-per-slide`)
- `iterator`: the JSONPath-lite expression for which array in the LLM output to iterate. Usually `$.slides`.
- `per_item.prompt_template`: this is the **per-slide image prompt**. Most of its body is `{{static_assets.X}}` substitutions; the variable part is `{{item.composition}}`, `{{item.title}}`, `{{item.required_text}}`. Mirror the source skill's "Complete Page Image Prompt" template (e.g. `references/prompt-patterns.md`).
- `per_item.size_by_role`: from `static_assets.theme_tokens.size_by_role`, or fresh defaults if absent
- `per_item.api`: matches an adapter from `lib-mapper.md`
- `per_item.endpoint_mode`: `generations` for from-scratch generation; `edits` when the API only supports edits (e.g. `image.token-recyclebin.com`)

### 3.6 `browser_runtime`

- `llm_adapter`: from mapper (default `openai-chat-compat`)
- `image_adapter`: from mapper (default `openai-images-compat`)
- `default_endpoints`: the providers you chose at USER GATE 3
- `concurrency`: default `3` (per hero case)
- `timeout_ms`: defaults are fine; only change if skill is known slow
- `retry`: default `{ llm: 0, image: 1 }`
- `extra_libs`: empty for v0.1 image-per-slide skills

### 3.7 `error_ux`

Start from `ir-schema.md §7` defaults; adapt language to the skill (e.g. say "slide" or "page" or "card" appropriately).

### 3.8 `attribution`

Direct from LICENSE/NOTICE. The `footer_html` should be a one-line snippet that links to:

- source skill repo
- source skill author (GitHub profile)
- this `skill2web` project

### 3.9 USER GATE 2

Surface the IR JSON to the user. Format like:

```text
IR 草稿（ir_version: 0.1）

▸ skill_meta:     <name> · <license> · @<author>
▸ static_assets:  style_lock (XXX chars), role_locks: [cover, body], archetypes: [N items]
▸ input_schema:   content/audience/scenario/length
▸ llm_phase:      model=<deepseek-chat>, json_mode=prompt-only, output: deck_type+slides[]
▸ render_phase:   kind=image-per-slide, iterator=$.slides, api=openai-images-compat
▸ browser_runtime:llm=https://api.deepseek.com/v1, image=<image-endpoint>
▸ attribution:    <Author> · <License> · <link>

Open questions before I lock IR:
1. input_schema 字段 X 你觉得需要吗？
2. <other specific caveat>

可以了我就继续 mapper 阶段，或者你想改哪里？
```

Save IR to `<output-dir>/<skill-name>.ir.json` after user confirms.

## Phase 4 — Mapper

Read `lib-mapper.md`. For every external dependency in the source skill, find the row.

For each unfound row, run USER GATE 3 to either:
- add a new row (with verification status noted)
- accept a fallback / stub
- refuse compile

**Also choose providers** at this gate. Even if defaults are fine, restate them so the user can override:

> 默认 provider:
> - LLM: `https://api.deepseek.com/v1` + `deepseek-chat`
> - 图像: `https://image.token-recyclebin.com/v1` + `gpt-image-2`
>
> 这两个 endpoint 在浏览器端的 CORS 还**没经过严格验证**（DESIGN.md Day 0 spike 跳过了）。最终用户第一次跑可能会撞 CORS 错。你可以现在切到一个已知 CORS 友好的（如官方 OpenAI），或者接受这个风险。

Lock the user's answers into IR.browser_runtime.default_endpoints.

## Phase 5 — Composer

Read `templates/base.html`. It contains `{{…}}` placeholders that map 1:1 to IR fields.

Composer is a **pure template-fill operation**. For each placeholder:

1. Look up the value in IR.
2. JSON-stringify (for JS const) or HTML-escape (for HTML attribute) as appropriate — the placeholder name tells you which (see `base.html` comments).
3. Substitute.

Common placeholder forms (full list in `base.html`):

- `{{IR.skill_meta.display_name}}` → HTML-escaped string
- `{{IR.skill_meta.source.url}}` → URL (HTML-escaped, in `href`)
- `{{IR.static_assets.style_lock|js-string}}` → JS string literal (backtick-wrapped, no escaping of newlines)
- `{{IR.input_schema|render-form}}` → composer generates `<input>`/`<select>`/`<textarea>` markup
- `{{IR.llm_phase.system_prompt_template|js-string}}` → JS string literal
- `{{IR.attribution.footer_html|raw}}` → raw HTML (with `{{source_skill_name}}` etc. inside already substituted)

If any placeholder is missing in IR (i.e. composer would substitute `undefined`): **emit a warning and ask the user**. Do not produce a broken HTML silently.

Output the composed HTML to `<output-dir>/<skill-name>.html`.

## Phase 6 — Emitter

Write the README:

```markdown
# <Display Name> — single-file web tool

Compiled by [skill2web](<url>) from [<source-name>](<source-url>) (© <author> · <license>).

## How to use

`<skill-name>.html` is **single-file source** but must be served over HTTP — `file://` is **not supported** (browsers restrict `fetch()` and some providers' CORS rejects `file://` origins). Pick one:

```bash
# Option A: local quick test
cd <path-to-html>
python3 -m http.server 8765
# Then open http://localhost:8765/<skill-name>.html

# Option B: deploy permanently
# Upload <skill-name>.html anywhere that serves static files over HTTP:
#  · GitHub Pages, Surge, Cloudflare Pages, Netlify, your own nginx.
```

Once served:

1. Click **设置 / Settings** top-right. Paste your API keys. Save (stored in your browser's `localStorage`; never sent anywhere except to the providers you configure).
2. Fill the form and click **生成 / Generate**.

> ⚠️ **Provider CORS may not work on first try.** v0.1 ships with `unverified` provider defaults — meaning the maintainer believes they should work but has not browser-tested them end-to-end. If you get a CORS error in DevTools Console, either switch providers (the **设置** panel accepts any OpenAI-compatible endpoint) or run a 30-line local Python reverse proxy. PRs adding verified providers to `lib-mapper.md` are welcome.

## API keys

You need:
- **LLM key** (default endpoint: `<endpoint>`). Get one from <provider link>.
- **Image key** (default endpoint: `<endpoint>`). Get one from <provider link>.

Keys are stored in your browser's `localStorage`. They never leave your machine except to the API endpoints you configure.

## License & attribution

This compiled artifact is derived from `<source-name>` by `<author>` (<license>). Source license text included below.

The `skill2web` compiler is MIT.

---

[Verbatim source LICENSE text here]
```

### Verification

Run before announcing success:

```bash
# 1. file exists and is reasonable size
ls -la <output-dir>/<skill-name>.html

# 2. script syntax check
node -e "
const fs = require('fs');
const html = fs.readFileSync('<output-dir>/<skill-name>.html','utf8');
const m = html.match(/<script>([\s\S]*?)<\/script>/);
if (!m) { console.error('no <script>'); process.exit(1); }
try { new Function(m[1]); console.log('JS syntax OK', m[1].split('\n').length, 'lines'); }
catch (e) { console.error('JS error:', e.message); process.exit(2); }
"

# 3. footer attribution present
grep -i '<footer' <output-dir>/<skill-name>.html | head -1
grep -i '<author>' <output-dir>/<skill-name>.html | head -1
```

### USER GATE 4

```text
✅ 编译完成。

文件:
- <output-dir>/<skill-name>.html  (XX,XXX bytes, NNNN lines)
- <output-dir>/<skill-name>.README.md
- <output-dir>/<skill-name>.ir.json    ← 已 commit 用

验证:
- JS 语法 OK (716 行 JS)
- 页脚署名: "本网页由 skill2web 从 <name>（<author> · MIT）编译"
- README 含 LICENSE 全文 + key 获取指引

建议测试:
  cd <output-dir> && python3 -m http.server 8765
  浏览器打开 http://localhost:8765/<skill-name>.html

要 git add 这个 dist 目录吗？还是先本地试一下再决定？
```

Do **not** auto-commit. The user decides.

## Re-compile / Update flows

If the user runs `skill2web` again on the same skill:

1. Look for an existing IR at `<output-dir>/<skill-name>.ir.json`. If found, **load it and ask**: "上次编译的 IR 在这里。要 diff 上游变化、还是从头来？"
2. Diff mode: re-run loader, re-run analyzer, compare static_assets text against saved IR. Flag any drift. The user reviews diffs and merges into a new IR.
3. From scratch: same workflow, but mention to the user that prior IR has been backed up to `<skill-name>.ir.json.bak.<ts>`.

## Known limitations of v0.1 compiler

These are intentional (per DESIGN.md):

- **No frontend-design integration**. UI is whatever `base.html` provides. v0.2.
- **Only image-per-slide kind**. v0.2 adds template-html / pptx-canvas.
- **No automated provider CORS verification**. Composer warns the user, doesn't probe.
- **No zip emit**. Compiled output is single HTML; users download per-file.
- **No multi-skill compile in one run**. One source skill → one HTML per invocation.

If any of these blocks a real compile, the user should be told now (USER GATE 1 or 3) — not at emit time.
