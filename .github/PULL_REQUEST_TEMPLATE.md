<!--
  Thanks for the PR! A few asks before a maintainer looks at this.

  - Atomic commits with Conventional-Commit prefixes (`feat:`, `fix:`, `docs:`, `chore:`).
  - PR title in the same style as `git log` on `main`.
  - If the IR changes shape, bump MINOR and ship a migration script. See CONTRIBUTING §Versioning.
-->

## What this PR does

<!-- One-paragraph summary. The "why" matters more than the "what". -->

## Type of change

- [ ] New hero case
- [ ] Provider CORS verification (`unverified` → `verified-partial` / `verified-full`)
- [ ] Compiler / IR fix (no IR shape change)
- [ ] IR shape change (MINOR bump + migration script attached)
- [ ] Docs only
- [ ] Other: <!-- describe -->

## Evidence

> Pick the rows that apply and fill them in. Empty rows can be deleted.

### If this is a new hero case

- Analyzer transcript:
  ```
  <!-- paste your `analyzer-checklist.md` walkthrough here -->
  ```
- IR file: `skill/examples/<your-case>.ir.json`
- Compiled artifact: `dist/<your-case>.html` (regenerable from the IR — not committed)
- E2E screenshot: `docs/screenshots/e2e-<your-case>.png`
- `dist/<your-case>.README.md`: <!-- created? -->
- `degradation_log` (if §4.6 taken): <!-- entries listed in the IR -->
- Hero table updated in **both** `README.md` and `README.zh-CN.md`: <!-- yes/no -->

### If this is a provider CORS verification

- Provider + endpoint: <!-- e.g. DeepSeek `https://api.deepseek.com/v1` -->
- Model used: <!-- e.g. `deepseek-chat` -->
- Browser: <!-- Chrome 12x / Firefox 12x / Safari 17 -->
- DevTools preflight result: <!-- 200/204 + Access-Control-Allow-* headers — attach screenshot if possible -->
- Verification log entry appended to `adapters.md` (and/or `render-libs.md`): <!-- yes/no -->
- Coverage promotion: <!-- unverified → verified-partial / verified-full -->

### If this changes the compiler / IR

- Composer ran on at least one example IR without regression:
  ```
  python3 skill/compose.py skill/examples/<some>.ir.json /tmp/check.html
  ```
- Tests / smoke runs:
  <!-- e.g. `node --check` on the generated `<script>` block; opened in browser; etc. -->

## Spike-gating check (only for new `ir_kind`)

- [ ] N/A — this PR does not add a new `ir_kind`.
- [ ] This PR adds `<ir_kind>` and ships **with** the §11 spike pass evidence (per `TODO.md` activation criteria). Spike pass details:
      <!-- paste the spike's pass conditions and how they were met -->

## Related issues

<!-- Closes #N, Refs #N. -->
