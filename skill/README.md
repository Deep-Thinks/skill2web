# skill2web — the skill itself (v0.2)

This directory **is** the `skill2web` Claude Code skill. Drop it into `~/.claude/skills/` (or this project's `.claude/skills/`) and Claude Code will load it when triggered.

## Files

```
skill/
├── SKILL.md                              # entry — main agent reads this first
├── README.md                             # you are here
├── compose.py                            # 三步组装 composer (python3 compose.py <ir.json> <out.html>)
├── migrate_v01_to_v02.py                 # v0.1 → v0.2 IR 一次性迁移
├── references/                           # 详细 playbook, 按需 load
│   ├── ir-core.md                        # universal IR (8 字段)
│   ├── ir-kinds/
│   │   ├── image-deck.md                 # render shape (per-kind)
│   │   ├── template-html.md
│   │   └── png-canvas.md
│   ├── compiler-workflow.md              # 6 阶段 + 4 user gate operational playbook
│   ├── analyzer-checklist.md             # 9-step compilability decision tree + refusal templates
│   ├── adapters.md                       # API 调用契约 (LLM / image)
│   └── render-libs.md                    # inline JS lib (markdown / sanitizer / pptxgenjs ...)
├── templates/
│   ├── skeleton.html                     # 通用骨架 (header / settings / pipeline runner / mustache-lite)
│   ├── blocks/
│   │   ├── image-deck.html               # slide-grid + image API
│   │   ├── template-html.html            # article + sanitizer
│   │   └── png-canvas.html               # single poster
│   └── adapters/
│       ├── openai-chat-compat.js         # callLLM (~25 行)
│       ├── anthropic-chat.js             # 同名 callLLM, Anthropic 协议
│       └── openai-images-compat.js       # callImageAPI + makeBlankPng
└── examples/
    ├── ian-handdrawn-ppt.ir.v0.1.json    # 归档(v0.1 IR, 走 migration 升 v0.2)
    ├── ian-handdrawn-ppt.ir.json         # v0.2 IR (image-deck)
    ├── synthetic-essay-polisher.ir.json  # v0.2 IR (template-html, hero case 2)
    └── guizang-cover.ir.json             # v0.2 IR (png-canvas)
```

## When the main agent loads this skill

1. `SKILL.md` frontmatter 描述匹配 → Claude Code load `SKILL.md`
2. Operating rule + workflow + defaults 立即进 context
3. 每个 `references/*.md` 是 **load-on-demand** — `SKILL.md` 说 "进 phase Y 时读 X", 不预加载所有
4. `templates/skeleton.html` + `blocks/<ir_kind>.html` + `adapters/*.js` 在 phase 5 (composer) 时由 `compose.py` 读
5. `examples/*.ir.json` 是 extractor 的灵感来源,源 skill 形态相近时直接借鉴

## User gates (不可跳)

| Gate | Phase | 问什么 |
|---|---|---|
| 1 | analyzer | "我判 compilable / refuse, 理由是…, 继续吗?" |
| 2 | extractor | "IR 草稿如下…input_schema 字段你看可以吗? sanitizer 选哪档(template-html only)?" |
| 3a | mapper | "默认 provider X / Y, CORS 没验证过, 接受风险还是切换?" |
| 3b | mapper | "依赖 `<lib>` 不在 mapper 里, 要加 row 还是拒绝?" |
| 4 | emitter | "编译完, 文件在这里。要 git add 吗?" |

## Out of v0.2 scope (留 v0.3+)

- `frontend-design` 集成
- `pptx-canvas` 实装(spike-gated, DESIGN §11.S1)
- `data-table` 实装(spike-gated, DESIGN §11.S2)
- DAG `llm_pipeline`(分叉/合流)
- Single IR 多 kind 输出
- Provider CORS 自动 verify(仍是 user gate 手工)
- zip-emit / streaming LLM / local proxy mode

如果源 skill 需要这些, analyzer phase 2 早期拒绝(见 `references/analyzer-checklist.md`)。

## How this skill 演化

- Day 1 (v0.1): 手工编译 `hero-cases/ian-handdrawn-ppt/` 作为 image-deck 形态的设计输入
- Day N (v0.2, 2026-05-15): 拆 IR core/kinds + skeleton/blocks/adapters,加两个新 kind (template-html / png-canvas), 加 hero case 2 (`hero-cases/synthetic-essay-polisher/`) 作为 template-html 形态的设计输入

如果某处实现与对应 hero case 输出冲突,**hero case 是 source of truth** —— 修 skill 而非 hero case。

## License

MIT。见 `../LICENSE`。
