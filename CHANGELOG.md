# Changelog

All notable changes to **skill2web** are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project (best-effort) adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html). Until v1.0, `0.MINOR.PATCH` is the public surface — `MINOR` bumps may rewrite the IR or analyzer; `PATCH` adds verified hero cases without breaking IRs.

## [Unreleased]

See [`TODO.md`](TODO.md) for the v0.2.x backlog (spike-gated kinds, lib-mapper verification log, etc.).

## [0.2.1] — 2026-05-15

### Added
- **Analyzer §4.5** — SOP-shape vs tool-shape agent decision (distinguishes by "is the next edge of the skill's flow decided at design time or at runtime?").
- **Analyzer §4.6** — explicit downgrade path for skills that look like `needs-fs` / multi-phase agents but are actually SOP-shaped: user input substitutes agent exploration; multi-phase memory collapses into a single LLM call; implementation phases get dropped.
- **IR top-level `degradation_log`** — required when §4.6 is taken; surfaced at USER GATE 1 so the user explicitly accepts the downgrade.
- **Hero case: `prompt-master`** — direct-compile baseline for pure SOP-shape skills. Source: [nidhinjs/prompt-master](https://github.com/nidhinjs/prompt-master). End-to-end verified against StepFun `step-3.5-flash` in 25s.
- **Hero case: `app-onboarding-blueprint`** — downgrade-path verification case. Source: [adamlyttleapps/claude-skill-app-onboarding-questionnaire](https://github.com/adamlyttleapps/claude-skill-app-onboarding-questionnaire). 3 entries in `degradation_log`, end-to-end verified in 36s.
- `adapters.md` — `openai-chat-compat` promoted to **verified-partial** (StepFun + xiaomimimo confirmed browser CORS OK on 2026-05-15). StepFun reasoning-model `max_tokens >= 1000` quirk documented.

### Changed
- Analyzer Step 5 now routes `needs-fs` / `needs-shell` through §4.6 instead of rejecting outright.
- USER GATE 1 copy now communicates the downgrade in plain language.

### Why this matters
First-round triage of 5 high-star GitHub skills under the strict v0.2 analyzer admitted only 1 (prompt-master) — hit rate ~20%. The user insight: *"giving the agent tools (Playwright / Context7) is not the goal; giving the agent a step-by-step SOP is."* §4.5 + §4.6 raise hit rate to ~25–40% (2–3×) without compromising the run-time-is-not-an-agent invariant.

## [0.2.0] — 2026-05-15

### Added
- **Universal IR core** (`ir-core.md`) + per-kind plugin schemas (`ir-kinds/{image-deck,template-html,png-canvas}.md`). v0.1's image-deck-shaped IR is now one plugin among three.
- **`llm_pipeline` array** — 1–3 strictly linear steps; `uses` may only reference earlier steps.
- **Three-step composer** — `skill/compose.py` replaces v0.1's monolithic `base.html`: `skeleton + blocks/<kind> + adapters/<name>`.
- **`adapters.md`** (API contracts) and **`render-libs.md`** (inline JS libraries) split from v0.1's `lib-mapper.md`.
- **Analyzer kind router** (step 9 — runtime-environment equivalence) + **5 new refusal templates**.
- **Hero case: `synthetic-essay-polisher`** — `template-html` design input (no upstream; synthetic).
- **Hero case: `guizang-cover`** — `png-canvas` synthetic reference (shape from [op7418/guizang-ppt-skill](https://github.com/op7418/guizang-ppt-skill)).
- **`ian-handdrawn-ppt-v0.2/`** — regression baseline showing the v0.2 composer regenerates the v0.1 hand-authored hero case.
- **Migration script** `skill/migrate_v01_to_v02.py` — automatic v0.1 IR → v0.2 IR upgrade.

### Changed
- `.gitignore` now `dist/* + !dist/*.README.md + !dist/*.REFUSAL.md` (the directory-level ignore was overriding the exceptions).
- `dist/` ships per-artifact README docs and a sample REFUSAL; compiled `.html` artifacts stay out of git — users regenerate them with `compose.py`.

### Removed
- v0.1's monolithic `skill/templates/base.html` (replaced by `templates/skeleton.html` + `templates/blocks/` + `templates/adapters/`).

## [0.1.1] — 2026-05-15

OpenAI Codex independent review (session `019e2743-1b49-7851-9015-c1aef7b7b645`) surfaced three issues; #1 and #2 are fixed here, #3 is tracked in TODO.

### Changed
- **Issue 1 — IR honesty.** The v0.1 IR is image-deck-shaped (`style_lock`, `role_locks`, `archetypes`, `per_item.prompt_template`); the old top-level "what's coming in v0.2" promise was over-claiming. Added required top-level `ir_kind` field (v0.1 accepts only `image-deck`), corrected `DESIGN.md` and `SKILL.md` "Status" sections, and marked `template-html` / `pptx-canvas` / `png-canvas` as speculation, not a plan.
- **Issue 2 — provider verification honesty.** `lib-mapper.md` introduced coverage levels `verified-full` / `verified-partial` / `unverified` / `stub` / `none`. Every row previously marked `full` was demoted to `unverified` (evidence was Python-backend integration, not browser-CORS smoke tests). Added a Verification log + a documented promotion procedure.
- **`SKILL.md` Operating Rule** — clarified single-file SOURCE that **must be served over HTTP** (not `file://`); names localhost / GitHub Pages / Surge / etc. as supported deployments.
- **Phase 4 + emitter README template** — provider gate now surfaces the `unverified` CORS risk in plain language; emitter README leads with "must be served over HTTP" and the CORS-may-fail-on-first-try caveat.

### Tracked (issue #3 + follow-ups, in `TODO.md`)
- v0.1.1: analyzer environment-equivalence step + 4 new refusal types
- v0.1.1: gate restructure (lib mapper vs provider+CORS split)
- v0.1.x: fill ≥2 rows of the lib-mapper Verification log
- v0.2: second hero case (non-image-deck) to validate IR generalization
- v0.2: frontend-design skill integration
- v0.3: optional local Python reverse-proxy emit mode for CORS-hostile endpoints

## [0.1.0] — 2026-05-14

### Added
- **Design doc** `DESIGN.md` (APPROVED, quality 7/10, 7 critical issues fixed in independent review).
- **Hand-authored hero case** `hero-cases/ian-handdrawn-ppt/index.html` — 1125-line single-file HTML with zero external CDN dependency. Upstream: [helloianneo/ian-handdrawn-ppt](https://github.com/helloianneo/ian-handdrawn-ppt) (MIT, attributed in `source-attribution.md`).
  - Upstream static assets inlined verbatim (deck style lock / role locks / archetypes)
  - Single LLM call for deck spine (OpenAI-compatible chat completions)
  - Concurrent 3-way image API calls (gpt-image-2 compatible `/generations` or `/edits`)
  - API keys live only in browser `localStorage`; never on URL/query
- **Skill itself** `skill/SKILL.md` — entry point with 6-phase workflow and 4 user gates.
- `skill/references/ir-schema.md`, `compiler-workflow.md`, `analyzer-checklist.md`, `lib-mapper.md`.
- `skill/templates/base.html` — 870-line HTML template with 37 `{{IR.*}}` placeholders and modifiers `|js-string`, `|js-object`, `|html`, `|attr`, `|raw`.
- `skill/examples/ian-handdrawn-ppt.ir.json` — full IR reconstruction of the Day-1 hero case (compiler regression target).

### Key design decisions
1. The compiler is **conversational**, not a CLI — the main agent must consult the user at 4 explicit gates.
2. `static_assets` is the "soul" of image-generating skills; it must be inlined verbatim, never paraphrased.
3. `render_phase.kind` is a single field that selects the entire inline-lib path (v0.1 supports only `image-per-slide`); other kinds are refused with an ETA.
4. Default providers DeepSeek + token-recyclebin are pre-wired, but their browser-CORS behavior is unverified; gate 3 surfaces the risk to the user.

### Verified
- Template substitution against `examples/ir.json` + `base.html`: 0 unresolved placeholders, 0 leftovers, 46KB / 1109-line HTML output, 679-line `<script>` block, `node --check` syntax pass.

[Unreleased]: https://github.com/Deep-Thinks/skill2web/compare/v0.2.1...HEAD
[0.2.1]: https://github.com/Deep-Thinks/skill2web/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/Deep-Thinks/skill2web/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/Deep-Thinks/skill2web/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/Deep-Thinks/skill2web/releases/tag/v0.1.0
