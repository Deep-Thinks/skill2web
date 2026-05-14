# skill2web — the skill itself

This directory **is** the `skill2web` Claude Code skill. Drop it into `~/.claude/skills/` (or this project's `.claude/skills/`) and Claude Code will load it when triggered.

## Files

```
skill/
├── SKILL.md                          # entry — main agent reads this first
├── README.md                         # you are here
├── references/                       # detailed playbooks; loaded on demand
│   ├── ir-schema.md                  # IR JSON contract (the "constitution")
│   ├── compiler-workflow.md          # the 6-phase compile playbook
│   ├── analyzer-checklist.md         # compilability decision tree + refusal templates
│   └── lib-mapper.md                 # python → browser library mapping table
├── templates/
│   └── base.html                     # canonical output HTML skeleton with {{IR.X}} placeholders
└── examples/
    └── ian-handdrawn-ppt.ir.json     # reverse-engineered IR for the hero case (regression target)
```

## When the main agent loads this skill

1. `SKILL.md` frontmatter description matches → Claude Code loads `SKILL.md`.
2. Operating rule + workflow + defaults are immediately in context.
3. Each `references/*.md` is **load-on-demand** — `SKILL.md` says "read X when entering phase Y", not "preload everything".
4. `templates/base.html` is read at phase 5 (composer).
5. `examples/*.ir.json` is read by extractor for inspiration when the source skill resembles a known case.

## User gates (do not skip)

| Gate | Phase | What you ask |
|---|---|---|
| 1 | analyzer | "我判定 compilable 还是 refuse，理由是…，继续吗？" |
| 2 | extractor | "IR 草稿如下…input_schema 字段你看可以吗？" |
| 3 | mapper | "默认 provider 是 X，要换吗？CORS 没验证过，你接受这个风险吗？" |
| 4 | emitter | "编译完，文件在这里。要 git add 吗？" |

These are not optional. They exist because hand-compiling without them produced a worse artifact each time the user wasn't asked.

## Out of v0.1 scope

- `frontend-design` integration (v0.2)
- `template-html` / `pptx-canvas` / `png-canvas` kinds (v0.2 / v0.3)
- Provider CORS automated verification (manual user gate today)
- Multi-skill bundle in one run
- zip-emit
- Streaming LLM responses

If the source skill needs any of these, refuse early (see `analyzer-checklist.md`).

## How this skill was built

Day 1 of the broader `skill2web` project hand-compiled one hero case (`hero-cases/ian-handdrawn-ppt/`). That hand-compile **was** the prototype run of this skill — the workflow, IR schema, and template here are the formalized version of what happened by hand.

If anything in this skill conflicts with the hero-case output, **the hero case is the source of truth** — fix the skill, not the hero case. The hero case has been validated by a real `python3 -m http.server` smoke test (see project root `DESIGN.md` and `hero-cases/ian-handdrawn-ppt/LESSONS.md`).

## License

MIT. See `../LICENSE`.
