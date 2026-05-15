---
name: Bug report
about: A reproducible failure in the compiler, a compiled artifact, or a hero case.
title: "bug: <short description>"
labels: bug
---

## Summary

<!-- One sentence: what broke? -->

## What you did

<!-- The exact command, IR file path, or hero case you used. Paste if short, link if long. -->

```bash
# e.g.
python3 skill/compose.py skill/examples/<your.ir.json> dist/out.html
```

## What you expected

<!-- The behavior you thought you'd get. -->

## What actually happened

<!-- Error message, stack trace, screenshot, or "the page rendered but the LLM call returned X". -->

## Environment

- skill2web commit: <!-- `git rev-parse --short HEAD` -->
- Python version: <!-- `python3 --version` -->
- Browser (if relevant): <!-- e.g. Chrome 124 / Firefox 128 / Safari 17 -->
- Provider (if relevant): <!-- e.g. DeepSeek `deepseek-chat`, StepFun `step-3.5-flash` -->
- How you served the HTML: <!-- e.g. `python3 -m http.server 8765`, GitHub Pages, file:// (note: file:// is unsupported) -->

## Anything else

<!-- DevTools network screenshot, console logs, or "happens 1 in 3 runs" — useful detail goes here. -->
