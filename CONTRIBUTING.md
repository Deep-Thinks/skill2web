# Contributing to skill2web

Thanks for your interest in contributing. This document describes the workflow we want from external contributions.

If anything below is unclear, opening an issue first is always fine — small clarifications are better than guessing.

---

## TL;DR — what we especially want

1. **New hero cases** — real, end-to-end-verified compilations of upstream skills. Hero cases that exercise a spike-gated `ir_kind` (`pptx-canvas`, `data-table`) are the most valuable; see [`TODO.md`](TODO.md) for the activation criteria.
2. **Browser CORS verification rows** — fill in `skill/references/render-libs.md` (and `adapters.md`) by actually exercising a provider from a browser and reporting back. PRs that promote a provider from `unverified` to `verified-partial` / `verified-full` are extremely welcome.
3. **IR migration edge cases** — break `skill/migrate_v01_to_v02.py` with a real v0.1 IR that doesn't round-trip, and we'll fix the migrator.

The two things we **do not** want:

- New `ir_kind` plugins **without a real triggering skill** behind them. See `DESIGN-v0.2.md` §11 (spike-gating).
- Changes that turn the run-time into an agent. The whole point of skill2web is that the compiled HTML has **no** agent runtime. Anything that wants persistent state, autonomous tool use, or multi-turn reasoning belongs in the build-time compiler, not in the artifact.

---

## Local development

### Requirements

- Python 3.10+ (the composer is pure stdlib; no `pip install` needed).
- Any web browser. Chrome / Firefox / Safari recent versions are all fine.
- Node.js (optional) — only if you want to `node --check` generated JS during testing.

### Compile and run a hero case

```bash
# 1. Compile an example IR to a single-file HTML.
python3 skill/compose.py skill/examples/ian-handdrawn-ppt.ir.json dist/ian-handdrawn-ppt.html

# 2. Serve it (file:// will NOT work — see README "Running a hero case").
cd dist && python3 -m http.server 8765
# Open http://localhost:8765/ian-handdrawn-ppt.html
```

### Migrate a v0.1 IR

```bash
python3 skill/migrate_v01_to_v02.py path/to/old.ir.json path/to/new.ir.json
```

---

## Adding a new hero case

A hero case is a fully reproducible compilation against a real upstream skill. It is the only mechanism by which we expand `ir_kind` support.

1. **Pick a candidate skill** — see `TODO.md` for spike-gated kinds we are actively seeking. Otherwise any flow-shaped skill (input → 1–3 LLM calls → template render → output) is in scope.
2. **Run the analyzer** — work through `skill/references/analyzer-checklist.md` against the upstream skill. If the skill is rejected, that itself is a useful contribution — open an issue with the analyzer transcript so we can sharpen the refusal templates.
3. **Author an IR** — model on `skill/examples/*.ir.json`. The IR JSON lives in `skill/examples/<your-case>.ir.json`.
4. **Compile** — `python3 skill/compose.py skill/examples/<your-case>.ir.json dist/<your-case>.html`.
5. **End-to-end verify** — open the compiled HTML in a real browser, point it at a real provider, complete the flow, and **screenshot** the final delivered artifact. Drop the screenshot into `docs/screenshots/e2e-<your-case>.png` (≤ 2 MB; downsample if needed).
6. **Document** — write `dist/<your-case>.README.md` describing what the artifact does, what providers were used, and any `degradation_log` entries if the §4.6 downgrade path was taken. If the upstream is hand-authored under a real `hero-cases/<your-case>/` directory, include a `source-attribution.md` that preserves the upstream license.
7. **Append a row** to the Hero cases table in both `README.md` and `README.zh-CN.md`.
8. **Open a PR** with the analyzer transcript in the description.

The compiled HTML itself (`dist/<your-case>.html`) **stays out of git** — `dist/*` is gitignored, with exceptions only for `*.README.md` and `*.REFUSAL.md`.

---

## Verifying a provider's browser CORS

This is the highest-leverage small contribution. The current `unverified` rows in `skill/references/render-libs.md` and `adapters.md` are the largest single source of user friction.

1. Pick an `unverified` provider row.
2. From a real browser (not Node, not curl), exercise the adapter against the provider with a fresh API key.
3. In DevTools → Network, confirm the preflight (`OPTIONS`) returns `200/204` with the expected `Access-Control-Allow-*` headers.
4. Append an entry to the Verification log section of `render-libs.md` (and/or `adapters.md`):

   ```
   - 2026-MM-DD · openai-chat-compat · provider=<name>, endpoint=<URL>,
     model=<id>, browser=<Chrome 12x>, result=<OK | failed reason>.
   ```

5. Promote the coverage level if appropriate (`unverified` → `verified-partial` for one provider; `verified-full` only when ≥ 2 independent providers are verified).
6. PR with the DevTools screenshot attached.

---

## Pull request workflow

1. **Branch** off `main`. Use a short descriptive name: `feat/hero-case-<name>`, `fix/composer-<area>`, `docs/<area>`.
2. **Atomic commits.** One logical change per commit; commit messages follow the existing repo style (Conventional Commits prefix + Chinese or English body — see `git log` for examples).
3. **Reference issues** if applicable: `Closes #N`.
4. **Run the composer** on at least one example IR to confirm the change doesn't regress template substitution.
5. **Open the PR** using the template — paste the analyzer transcript or DevTools evidence as relevant.

A maintainer will review. Reviews are usually one round; expect questions on whether spike-gating is being respected and whether the IR change is plugin-local vs core.

---

## Versioning

Until v1.0:

- `0.MINOR.PATCH`
- `MINOR` bumps may rewrite the IR or the analyzer (breaking changes allowed); they always ship with a migration script in `skill/`.
- `PATCH` bumps add verified hero cases or fix bugs without touching IR shape.

If your PR breaks the IR, please bump `MINOR` and provide migration tooling.

---

## Reporting bugs / proposing features

Use the issue templates under `.github/ISSUE_TEMPLATE/` — they cover bug reports, feature requests, and new hero case proposals separately.

For security issues, please **do not** open a public issue; email the maintainer at `niuniu869@qq.com` instead.

---

## License

By contributing, you agree that your contributions will be licensed under the project's MIT license (see [LICENSE](LICENSE)).

Compiled artifacts in `dist/` and hand-authored references in `hero-cases/` preserve their upstream skill's license and attribution; new hero cases must add a `source-attribution.md` if the upstream is third-party.
