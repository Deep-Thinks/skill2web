# Compiler Workflow

The full step-by-step playbook for a `skill2web` compile run. Read this when you (the main agent) are actively compiling — `SKILL.md` is the high-level entry; this is the operational detail.

The workflow is **conversational**. There are four mandatory user gates (GATE 3 splits into 3a/3b in the mapper phase). Skipping a gate is a defect — most hand-compile failures were caused by *not asking*.

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

Read `LICENSE`, `NOTICE.md` if present. If no LICENSE: stop and ask (per `ir-core.md §6`). Do not invent one.

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

Read `analyzer-checklist.md`. Run the 9-step decision tree (含 §4.5 / §4.6 的 SOP-vs-tool 降级检查；step 8 路由 `ir_kind`；step 9 运行环境等价性）. Stop at the first refusal trigger.

If you reach the bottom: surface **USER GATE 1** with the verdict.

After USER GATE 1, **save your analysis** to `<output-dir>/<skill-name>.analyzer.md` (a short markdown with the verdict, the trigger evidence quoted from source SKILL.md, and the caveats list). This is build-time documentation; it is useful if you re-compile later and want to remember why you made each call.

## Phase 3 — Extractor

Read `ir-core.md`（universal 字段）与 `ir-kinds/<ir_kind>.md`（kind-specific 子 schema）. Build the v0.2 IR step by step. **Order matters** — later fields reference earlier ones.

v0.2 IR 顶层是 8 个字段 + 2 个 meta：

| 字段 | 来源 |
|---|---|
| `ir_version` | 固定 `"0.2"` |
| `ir_kind` | analyzer §8 的路由结果（`image-deck` / `template-html` / `png-canvas`） |
| `skill_meta` | SKILL.md frontmatter + `LICENSE` + `NOTICE.md` |
| `input_schema` | 推断 — 不在 SKILL.md，USER GATE 2 让用户确认（v0.2 是数组 of field objects） |
| `llm_pipeline` | 数组，1-3 个**严格线性** step（`uses` 只引前序） |
| `browser_runtime` | mapper 阶段定 |
| `error_ux` | 你起草，用户改语气 |
| `attribution` | `LICENSE` + `NOTICE.md` |
| `render` | polymorphic — shape 取决于 `ir_kind`，见 `ir-kinds/<kind>.md` |

> v0.2 变化：v0.1 的 top-level `static_assets` 已下移到 `render.static_assets`（仅 `image-deck` / `png-canvas` 有）；v0.1 的 `llm_phase` 单对象升级为 `llm_pipeline` 数组；v0.1 的 `render_phase` 改名 `render`、`kind` 升到 top-level `ir_kind`。

### 3.1 `skill_meta`

- `name`: from SKILL.md frontmatter
- `display_name`: friendly title; usually the SKILL.md first `# Heading`
- `description`: usually the frontmatter `description`, trimmed to ≤ 200 chars
- `source.url`: the git URL the user provided
- `source.path_inside_repo`: the relative path you found SKILL.md in (often `<skill-name>/`)
- `license`, `author`, `author_links`: from LICENSE + NOTICE.md + README.md links

### 3.2 `render.static_assets` (仅 `image-deck` / `png-canvas`)

> v0.2：`static_assets` 不再是 top-level，而是 `render.static_assets` 的子字段。`template-html` kind 没有这一块。kind-specific 形状见 `ir-kinds/<kind>.md`。

This is the most failure-prone step. The hand-compile experience: **do not paraphrase. Copy strings verbatim.**

For `image-deck` skills:

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

### 3.4 `llm_pipeline` (v0.2 数组化)

`llm_pipeline` 是一个数组，含 1-3 个**严格线性**的 step。**默认起草单个 step**（`id: "plan"`, `uses: []`）；仅当 source skill 明显是"两轮 LLM（intake → spine）"形态才拆 2-3 step。每个 step 的 `uses` **只能引前序 step**——任何分叉 / 合流 / 条件跳转都应在 analyzer Phase 4 被判为 agent-shaped。

每个 step 的字段：`id` / `model_hint` / `temperature` / `json_mode` / `system_prompt_template` / `user_prompt_template` / `uses` / `expected_output_schema`（详见 `ir-core.md §3`）。

Draft each step's `system_prompt_template`. Start from the source SKILL.md's "Workflow" section — quote it as guidance to the LLM. Then add **strict JSON output rules**:

```text
You are the planner for <DISPLAY_NAME>. Read the user's content and output a deck spine JSON ...

Output schema (strict):
{{LLM_OUTPUT_SCHEMA_INLINE}}

Rules:
1. Output ONLY JSON. No prose, no markdown.
2. Field <X> must be one of: <enum>.
3. <Skill-specific rule, e.g. titles ≤ 12 chars>.
```

Draft `user_prompt_template`. v0.2 模板语法有两个命名空间：
- `{{input.<key>}}` — 引用 input_schema 字段（v0.2 强制 `input.` 前缀）
- `{{steps.<step_id>.output.<dotted-path>}}` — 引用前序 step 的输出（仅多 step 时用）

Draft `expected_output_schema` (JSON Schema) for each step. This is the contract the LLM must satisfy; the output HTML validates against it. Be permissive on optional fields, strict on required ones.

`json_mode`: default `prompt-only` (most compatible). Only set `response-format` if you've verified the LLM provider supports it for this model.

### 3.5 `render` (polymorphic — shape 取决于 `ir_kind`)

v0.2 的 `render` 形状由 `ir_kind` 决定。完整 sub-schema 见 `ir-kinds/<kind>.md`，要点：

**`image-deck`** — `render.static_assets.{style_lock, role_locks?, reference_clauses?, archetypes?, theme_tokens?}` + `render.iterator` + `render.per_item.{prompt_template, size_by_role, api, endpoint_mode}`：
- `iterator`: JSONPath-lite，指向 LLM 输出里要迭代的数组。v0.2 路径带 step 前缀，如 `$.steps.plan.output.slides`。
- `per_item.prompt_template`: per-page image prompt。body 多为 `{{static_assets.X}}` 替换，变量部分是 `{{item.composition}}` / `{{item.title}}` / `{{item.required_text}}`。
- `per_item.size_by_role`: 来自 `static_assets.theme_tokens.size_by_role`，必须覆盖 IR 里出现的所有 role。
- `per_item.api`: 对应 `adapters.md` 里的 adapter（`openai-images-compat`）。
- `per_item.endpoint_mode`: `generations`（从零生成）/ `edits`（仅支持 edits 的 endpoint，如 `image.token-recyclebin.com`）。

**`png-canvas`** — `render.{canvas_size, static_assets.{style_lock, reference_clauses}, prompt_template, api, endpoint_mode, compositing: "none", fonts}`，N=1，无 `iterator` / `per_item`。

**`template-html`** — `render.{output_form, template_html?, css_lock?, data_binding, sanitizer, features}`，无 image API。`sanitizer` 必须显式选（`dompurify-strict` / `dompurify-relaxed` / `none-trust`）。

### 3.6 `browser_runtime`

- `llm_adapter`: from mapper (default `openai-chat-compat`)
- `image_adapter`: from mapper (default `openai-images-compat`)
- `default_endpoints`: the providers you chose at USER GATE 3
- `concurrency`: default `3` (per hero case)
- `timeout_ms`: defaults are fine; only change if skill is known slow
- `retry`: default `{ llm: 0, image: 1 }`
- `extra_libs`: empty for the three shipped kinds; only spike-gated kinds (`pptx-canvas`) need it

### 3.7 `error_ux`

Start from `ir-core.md §5` defaults; adapt language to the skill (e.g. say "slide" or "page" or "card" appropriately).

### 3.8 `attribution`

Direct from LICENSE/NOTICE. The `footer_html` should be a one-line snippet that links to:

- source skill repo
- source skill author (GitHub profile)
- this `skill2web` project

### 3.9 USER GATE 2

Surface the IR JSON to the user. Format like:

```text
IR 草稿（ir_version: 0.2, ir_kind: image-deck）

▸ skill_meta:     <name> · <license> · @<author>
▸ input_schema:   content/audience/scenario/length
▸ llm_pipeline:   [plan] model=<deepseek-chat>, json_mode=prompt-only, output: deck_type+slides[]
▸ browser_runtime:llm=https://api.deepseek.com/v1, image=<image-endpoint>
▸ render:         static_assets.style_lock (XXX chars), role_locks: [cover, body],
                  archetypes: [N items], iterator=$.steps.plan.output.slides, api=openai-images-compat
▸ attribution:    <Author> · <License> · <link>

Open questions before I lock IR:
1. input_schema 字段 X 你觉得需要吗？
2. <other specific caveat>

可以了我就继续 mapper 阶段，或者你想改哪里？
```

Save IR to `<output-dir>/<skill-name>.ir.json` after user confirms.

## Phase 4 — Mapper

Read `adapters.md`（API 调用契约）与 `render-libs.md`（render-time inline JS lib）. For every external dependency in the source skill, find the row.

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

## Phase 5 — Composer (v0.2 三步组装)

> v0.2 关键变化: composer 不再是"单模板 + Mustache 填空", 而是 **skeleton + block + adapters 三步组装**。
> 实现见 `skill/compose.py`(可直接 `python3 skill/compose.py <ir.json> <out.html>` 调).

### 5.0 frontend-design pass (v0.3, 强制)

跑 composer 之前**必须**先调 `frontend-design` skill。这是 v0.3 的硬规则(`SKILL.md` Hard rule 7),不可跳过。

- 输入给 frontend-design:`IR.skill_meta`(主题 / 受众)、`IR.ir_kind`、`IR.input_schema`、skeleton 默认皮肤 + `blocks/<kind>.html` 的 kind 样式。
- 产出:一段**覆盖型 raw CSS**,写进 `IR.theme_overrides`(`ir-core.md §8`)。composer 把它 inline 到 `<style>` 末尾,排在 skeleton 基础样式与 `BLOCK:HEAD` 之后,因此能覆盖二者。
- 约束:CSS only。无 `<script>`、无远程 `@import` / CDN / web-font URL —— 违反单文件 + 无运行时依赖(Hard rule 3)的产出,必须 inline 化或剔除。
- 向用户简述方案;用户可改可跳过具体条目,但不能跳过这一步本身。frontend-design 判定默认皮肤已够好 → `theme_overrides` 可留空,但那是"看过的结论"而非省略。

### 5.1 三步流程

1. **取骨架**: 读 `templates/skeleton.html`(通用 frame: header / settings / footer / pipeline runner / mustache-lite / loadSettings)
2. **注入 block**: 按 `IR.ir_kind` 选 `templates/blocks/<kind>.html`, 替换 skeleton 的 `BLOCK:HEAD` / `BLOCK:UI_SETTINGS` / `BLOCK:UI` / `BLOCK:RENDER` 段
3. **注入 adapter**: 按 `IR.browser_runtime.{llm,image}_adapter` 选 `templates/adapters/<name>.js`, inline 到 skeleton 的 `ADAPTER:LLM` / `ADAPTER:IMAGE` 段
4. **placeholder 替换**: 把所有 `{{IR.X.Y|filter}}` 用 IR 树值替换(filter: `raw`/`html`/`attr`/`url`/`js-string`/`js-number`/`js-bool`/`js-bool-non-null`/`js-object`/`js-array`/`render-form-fields`/`js-spec`/`js-pipeline`)

### 5.2 placeholder 协议要点

只有以 `IR.` 开头的 `{{...}}` 是 build-time placeholder; 其它 `{{key}}` / `{{steps.X.output.Y}}` 是 run-time mustache-lite,composer 不动。

特殊 filter:
- `|render-form-fields` (用于 `IR.input_schema`) — 展开为 `<div class="form-row">` 块
- `|js-spec` (用于 `IR.input_schema`) — 展开为 JS const 字段元数据数组
- `|js-pipeline` (用于 `IR.llm_pipeline`) — 展开为 JS const 数组,字符串字段保持 JS template literal
- `|js-bool-non-null` — 任意非 null 非空字符串视为 true(用于 `NEEDS_IMAGE` 判定 image_adapter 是否存在)

### 5.3 Block 协议

每个 `blocks/<kind>.html` 必须提供四段(用 HTML 注释标记包裹):

```html
<!-- BLOCK:HEAD --> ...kind-specific CSS... <!-- BLOCK:HEAD_END -->
<!-- BLOCK:UI_SETTINGS --> ...image-key 区块或空... <!-- BLOCK:UI_SETTINGS_END -->
<!-- BLOCK:UI --> ...kind-specific HTML(slide-grid/article/canvas)... <!-- BLOCK:UI_END -->
<!-- BLOCK:RENDER --> ...JS,定义 async function renderOutput()... <!-- BLOCK:RENDER_END -->
```

`renderOutput()` 由 skeleton 的 pipeline runner 在所有 LLM step 完成后调一次,读 `state.steps[*].output` 与 `RENDER_CONFIG`(由 IR.render 注入)。

### 5.4 输出位置与缺位置警告

```bash
python3 skill/compose.py <ir.json> dist/<skill-name>.html
```

stderr 会列任何"placeholder unresolved"或"unknown filter"警告 — agent 必须把警告 surface 给用户(可能是 IR 字段缺失)。

### 5.5 错误情况

| 错误 | 处置 |
|---|---|
| `ir_version != "0.2"` | 跑 `skill/migrate_v01_to_v02.py` 升级 |
| `ir_kind` 找不到对应 `blocks/<kind>.html` | 拒绝(spike-gated kind 还没实装) |
| `llm_adapter` 找不到对应 `adapters/<name>.js` | 拒绝(添加新 adapter 走 USER GATE 3a + adapters.md PR) |
| placeholder unresolved | 明确告诉用户 IR 缺哪个字段 |

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

> ⚠️ **Provider CORS may not work on first try.** v0.1 ships with `unverified` provider defaults — meaning the maintainer believes they should work but has not browser-tested them end-to-end. If you get a CORS error in DevTools Console, either switch providers (the **设置** panel accepts any OpenAI-compatible endpoint) or run a 30-line local Python reverse proxy. PRs adding verified providers to `references/adapters.md` are welcome.

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

## Known limitations of v0.2 compiler

These are intentional (per DESIGN.md / DESIGN-v0.2.md):

- **No frontend-design integration**. UI 由 skeleton + block 决定。推迟到 v0.3。
- **Only three `ir_kind` values shipped**: `image-deck` / `template-html` / `png-canvas`。`pptx-canvas` / `data-table` 仅 schema 草案，spike-gated（DESIGN §11）。
- **`llm_pipeline` 是静态 DAG**（v0.3）。`uses` 可多父、step 可带 `when` 分支条件，但图必须编译期完全已知且有限；无界循环 / 运行时决定图形状 → 判 agent-shaped 拒。
- **No automated provider CORS verification**. Composer warns the user, doesn't probe.
- **No zip emit**. Compiled output is single HTML; users download per-file.
- **No multi-skill compile in one run**. One source skill → one HTML per invocation（混合输出 → 拆多次编译）。

If any of these blocks a real compile, the user should be told now (USER GATE 1 or 3) — not at emit time.
