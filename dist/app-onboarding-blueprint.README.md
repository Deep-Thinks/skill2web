# App Onboarding Blueprint · 单文件网页版

把你的 app 信息编译为一份高转化的 questionnaire-style onboarding 设计稿，参照 Mob / Headspace / Duolingo / Noom 的模式。

- 上游 skill: [adamlyttleapps/claude-skill-app-onboarding-questionnaire](https://github.com/adamlyttleapps/claude-skill-app-onboarding-questionnaire) (1.0k★, MIT 假定)
- 编译: skill2web v0.2.1, ir_kind=`template-html`, **降级版** (按 analyzer-checklist §4.6)
- 端到端实测: 2026-05-15, stepfun `step-3.5-flash` 36s 出 12 sections (3 fixed + 9 屏)

## ⚠️ 这是「降级版」 — 与原 skill 的差异

原 skill 是 multi-phase agent skill，在 Claude Code 里跑会自动:
1. 读你的项目代码 (CLAUDE.md / README / UI files / models / paywall code)
2. 跑 5 个 phase，跨对话保存进度
3. 最后一个 phase 自动**写代码进你的项目** (SwiftUI / Compose / RN)

skill2web 的编译产物是单文件 HTML，**没有 agent runtime**，所以做了 3 项降级:

| 原 skill 的步骤 | 降级后 | 损失 |
|---|---|---|
| Phase 1 Step 1: agent 读项目代码推断 features / permissions | 用户在 textarea 粘贴 app 描述、目标用户、核心 loop | 失去自动推断, 用户得自己描述清楚 |
| Phase 5: agent 写代码进项目 | **砍掉** — 只产 blueprint markdown | 你拿到 blueprint 后**需要手工实施** |
| 跨对话状态保存 / 断点续做 | 单次会话一气呵成 | 没有断点续做 |

**保留**: 转化策略、screen sequence、每屏文案、UX 笔记 (转化心理学解释)。

## 如何使用

### 1. 本地 HTTP server

```bash
python3 -m http.server 8765
# 访问 http://localhost:8765/app-onboarding-blueprint.html
```

### 2. 填 LLM API Key

默认 stepfun `step-3.5-flash` (CORS 已验证)。兼容任何 OpenAI compat 端点。

### 3. 填 6 个字段

- **App 是干嘛的**: 一段话描述, 类似 README + 主功能 + 核心 loop
- **目标用户 / 痛点**: 一段话
- **BEFORE / AFTER 转化故事**: 两段话
- **平台**: SwiftUI / UIKit / Compose / RN / Flutter / Web React
- **付费模式**: 免费 / 订阅+试用 / 订阅直付 / 一次性 / Freemium
- **需求权限**: 通知 / 相机 / 健康数据 / ...

### 4. 生成 → 拿到 markdown blueprint

输出结构 (约 30-90s):
- 📋 App 画像 (what / who / core loop / aha moment)
- 🔄 转化故事 (BEFORE → AFTER + 3-5 条 benefit statement)
- 🗺️ Onboarding 流程图 (8-13 屏序列)
- 📱 屏 1..N: 每屏标题 + 选项 + UX 笔记 (转化心理学解释)

实测样例: paywall 屏的 UX 笔记会明确说"第 8 屏比前 3 屏转化高 2-3 倍 / trial 钩子比 direct 转化高 1.5 倍 / 年卡 vs 月卡 anchoring"。

## License

- 源 skill: adamlyttleapps/claude-skill-app-onboarding-questionnaire (假定 MIT — 请核对原 repo LICENSE)
- 编译产物: 继承上游
- 编译器: [skill2web](https://github.com/xuejia-mq/skill2web) v0.2.1 · MIT
