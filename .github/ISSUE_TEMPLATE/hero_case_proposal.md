---
name: Hero case proposal
about: Propose a new end-to-end-verified hero case (highest-leverage contribution).
title: "hero-case: <skill name>"
labels: hero-case
---

## Upstream skill

- Name: <!-- e.g. helloianneo/ian-handdrawn-ppt -->
- URL: <!-- https://github.com/... -->
- License: <!-- MIT / Apache-2.0 / ... -->
- Author: <!-- @handle -->

## Analyzer transcript

> Run through `skill/references/analyzer-checklist.md` (9 steps). Paste your answers below.
> If the skill is **rejected**, that's a useful contribution too — finish the transcript and explain which refusal template applies.

```
Step 1 — input shape:                <!-- ... -->
Step 2 — LLM call count:             <!-- ... -->
Step 3 — render shape:               <!-- ... -->
Step 4 — needs-fs / needs-shell:     <!-- ... -->
Step 4.5 — SOP-shape or tool-shape:  <!-- ... -->
Step 4.6 — downgrade entries (if any):
  - <!-- ... -->
Step 5 — analyzer verdict:           <!-- accept | reject | downgrade -->
Step 6 — provider gate:              <!-- ... -->
Step 7-9 — kind router:              <!-- target ir_kind = image-deck | template-html | png-canvas | (spike-gated) -->
```

## Proposed `ir_kind`

<!-- One of the v0.2 supported kinds. If you're proposing a spike-gated kind (pptx-canvas / data-table), please file the spike pass first; see TODO.md. -->

- [ ] `image-deck`
- [ ] `template-html`
- [ ] `png-canvas`
- [ ] **(spike-gated)** `pptx-canvas` — has a passing §11.S1 spike attached
- [ ] **(spike-gated)** `data-table` — has a passing §11.S2 spike attached

## End-to-end verification plan

- Browser: <!-- which browser you'll verify in -->
- Provider you'll exercise: <!-- LLM provider + image provider if applicable -->
- API key source: <!-- your own; don't paste it -->
- Screenshot target: `docs/screenshots/e2e-<your-case>.png`

## PR readiness checklist

- [ ] IR authored at `skill/examples/<your-case>.ir.json`
- [ ] Compiled via `python3 skill/compose.py` without errors
- [ ] Opened in a real browser, run end-to-end against a real provider
- [ ] Final-state screenshot at `docs/screenshots/e2e-<your-case>.png` (≤ 2 MB)
- [ ] `dist/<your-case>.README.md` written
- [ ] `degradation_log` filled if §4.6 was taken
- [ ] Row appended to both `README.md` and `README.zh-CN.md` hero table
