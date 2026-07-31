# Improvements | 改进方案专辑

**EN** — This folder holds the detailed, bilingual expositions of the three
operator-proposed improvements that upgrade CrossAudit's evidence from
"protocol claims plus one exploratory trial" to "dose-response evidence,
real-deployment labels, and two-domain coverage". These documents explain and
guide; the **frozen source of truth remains**
`experiment/v3-ABLATION-REGISTRATION.md` (with its amendments) and
`experiment/v3/RUNBOOK.md`. Where any document here disagrees with the
registration, the registration wins.

**中文** — 本文件夹存放三项改进的详细中英对照说明。这三项改进把 CrossAudit
的证据形态从"协议主张 + 一次探索性试验"升级为"梯度证据 + 真实部署标签 +
双域覆盖"。本处文档负责解释与引导；**冻结的权威文本始终是**
`experiment/v3-ABLATION-REGISTRATION.md`（含修正案）与
`experiment/v3/RUNBOOK.md`。若此处任何表述与注册文档冲突，以注册文档为准。

| # | Document 文档 | Improvement 改进 | Status 状态 |
|---|---|---|---|
| 01 | [01-independence-ablation.md](01-independence-ablation.md) | Isolation-ladder ablation: does independence work, and through which channel 隔离梯度消融：独立性是否有效、通过哪条通道 | Frozen, blocked on keys 已冻结，等密钥 |
| 02 | [02-real-ledger-part-b.md](02-real-ledger-part-b.md) | Real-deployment ledger as labelled data 真实部署账本作为带标签数据 | Mined & frozen 已挖掘并冻结 |
| 03 | [03-code-audit-part-c.md](03-code-audit-part-c.md) | Auditing generated code via mutation testing 用变异测试审计生成代码 | Frozen, blocked on keys 已冻结，等密钥 |
| 04 | [04-repo-hygiene-and-reproducibility.md](04-repo-hygiene-and-reproducibility.md) | Sixth-audit findings R1–R11: repository hygiene and reproducibility 第六轮审计 R1–R11：仓库卫生与可复现性 | All closed 2026-07-31 全部关闭 |
| 05 | [05-packaging-design.md](05-packaging-design.md) | `pip install crossaudit`: packaging design, CLI, GitHub wizard, release engineering 打包设计：CLI、GitHub 向导、发布工程 | Design frozen 2026-08-01, unimplemented 设计冻结，未实现 |

Shared blockers 共同阻塞项：fresh API keys for both vendors + third-party
escrow of the defect key（双厂新密钥 + 缺陷密钥第三方托管）；operator's
blinded adjudication, 1–2 h（操作者盲评 1–2 小时）。
Execution 执行入口：`experiment/v3/RUNBOOK.md`.
