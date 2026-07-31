# CrossAudit 投稿计划 — NeurIPS 2026 Workshop

汇总日期：2026-07-31（关键事实当日经官方页面核实，链接见文末）。
骨架位置：`paper/submissions/neurips2026/`（两版均可直接 `pdflatex` 编译）。

## 一、赛道判断

Workshop 是这篇的正确去处：协议 + 探索性实验的组合不够主会实证门槛，
而两个目标 workshop 均为**非存档**（non-archival）——投了不烧任何后路，
之后仍可扩成主会/期刊投稿，arXiv 也照挂。

## 二、目标（两家截稿同为 2026-08-29）

| | AI-Native Academia | Agentic Systems for Molecular Sciences |
|---|---|---|
| 会址/日期 | Atlanta, 12/12–13 | Paris, 12/12–13 |
| 页限 | 短文 4 页 / 长文 9 页（不含参考文献） | 5 content pages（不含参考文献与附录） |
| 评审 | 未写明，按双盲准备 | **明确双盲** |
| 存档 | 非存档（已在其他 ML venue 发表的除外） | 非存档，明确欢迎 concurrent submission |
| 契合点 | 主题清单直接列出 audit trails、AI 辅助评审、citation integrity、governance | 真实钙钛矿管线部署；CFP 明确欢迎 negative results 与 rigorous evaluation |
| 骨架 | `academia-long.tex`（建议投 9 页长文） | `molecular-5p.tex`（部署优先重构） |
| 推荐度 | ★★★（第一目标） | ★★☆（可双投） |

双投合规：Molecular 明说欢迎 under review elsewhere；两家都非存档。
注意两家在同两天、分别巴黎/亚特兰大——都中了只能到场讲一个。

ICLR 2027 workshop 的 CFP 冬季才出，作为后手；再后手 AAAI-27 workshops。

## 三、改稿路线（正文 14 页 → 9 页 / 5 页）

### Academia 长文（9 页）——逐节预算已写进 `academia-long.tex` 注释
- §1 1.6→1.2 页：四条 contributions 原样保留；开头即打"本文被它自己提出的协议审过"（audits/ 五轮链）
- §2 1.6→1.0 页：前两段合并；Table 1 下沉附录 B，正文留一句引用
- §3 3.2→2.2 页：每条不变量的 rationale 砍半；§3.3 并入 §3.4；Figure 1 保全宽
- §4 3.5→2.4 页：status-vs-invariants 叙述改表格进附录 C；试验保 Design / What-the-audit-found / vendor-split 三段；scorecard 表进附录 D
- §5 1.2→0.8 页：五个 bullet 全留，删展开句
- §6 2.2→0.9 页：只留 CI 类比、ledger-as-data-asset、management-by-exception；平台关系/社区宪法/棘轮/打包/控制台各删或压成一句
- §7 0.4→0.3 页

### Molecular 短文（5 页）——重心翻转，结构提案在 `molecular-5p.tex` 注释
1. 从部署反推动机（0.8）→ 2. 协议压缩版+Fig 1（1.5）→ 3. 部署观察：
letter-vs-intent 规则分歧、算力解耦、升级经济学（1.0）→ 4. 试验诚实报告：
双档分数、置换底线、constant-BLOCKED 告诫（1.2）→ 5. 相关工作+要点（0.5）。
摘要需重写为 deployment-first，不要照搬 position-paper 摘要。

## 四、双盲清单（两版都过一遍）

- [ ] 删作者块、致谢、资助；`\hypersetup` 的 pdfauthor 置空（骨架已置空）
- [ ] 正文 "the first author's computational-chemistry pipeline" → "a live computational-chemistry pipeline"
- [ ] 脚注 repo URL → **anonymous.4open.science 匿名镜像**（导入 GitHub repo 生成匿名链接，有效期设到 2026-12 之后）
- [ ] 检查镜像内容本身：audits/、CITATION.cff、LICENSE、README 里的姓名/邮箱/Cambridge/Wisconsin 字样（匿名镜像工具不会自动打码）
- [ ] graphical abstract 不随投稿（含 repo 地址与作者名）
- [ ] arXiv：NeurIPS 惯例允许预印本存在；如求稳可等 9/29 录取后再挂

## 五、时间线（倒排至 8/29；提交时区以 OpenReview 页面为准，通常 AoE）

| 窗口 | 动作 |
|---|---|
| 8/1–8/4 | 定 venue（单投/双投）；决定 v2 实验是否赶截稿（要赶：本周配齐新 API keys + 密钥托管） |
| 8/5–8/15 | 改稿：先 academia-long，若双投再派生 molecular-5p |
| 8/16–8/20 | 冷读 + 照本 repo 传统跑一轮跨厂审计，处置表照旧入 audits/ |
| 8/21–8/24 | 双盲清单逐项过；生成匿名镜像并全文替换链接 |
| 8/25–8/28 | 在两家 CFP 页找到 OpenReview 入口并注册（用 cam.ac.uk 邮箱）；提前 48h 试提交 |
| **8/29** | 截稿 |
| 9/29 | NeurIPS 官方 workshop 贡献最终通知节点 |

## 六、策略要点

- 一句话卖点：**the paper was audited under the protocol it proposes**（audits/ 五轮跨厂审计与逐条处置——对手没有的证据形态）
- Academia 用词靠 governance / audit trail / integrity / accountability；Molecular 用词靠 closed-loop / deployment / negative results / rigorous evaluation
- 诚实的 corrected trial 在两家都是加分项，不要淡化"我们的密封失败被审计抓出"这段——那是协议在工作的展示
- 官方 style：两家 CFP 页会给 NeurIPS 2026 workshop 模板；下载 `neurips_2026.sty` 放进 `paper/submissions/neurips2026/` 即自动生效（骨架内置 `\IfFileExists` 开关，缺失时用同尺寸后备版编译）

## 核实来源

- NeurIPS 2026 Call for Workshops（三城 12/11–13；workshop 贡献建议截稿 8/29；最终通知 9/29）：https://neurips.cc/Conferences/2026/CallForWorkshops
- Agentic Systems for Molecular Sciences（Paris；8/29；5 页；双盲；非存档）：https://moleculediscovery.github.io/workshop2026/
- AI-Native Academia（Atlanta；8/29；4/9 页；非存档）：https://ai-native-academia.github.io/
