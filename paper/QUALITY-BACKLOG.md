# 论文质量提升清单（完整版）

汇总本会话全部已议定的提升点。状态：✅ 已完成 / ⬜ 待做 / 🔒 有阻塞。
每条注明谁执行与出处。改完一条勾一条；新点子加在对应分区，不删旧条目。

## A. 实证升级（对论文档次影响最大）

> 三项实证改进的详细中英对照说明见 `improvements/`（01 梯度消融 / 02 真实账本 / 03 代码审计）。

- 🔒 **A1. 跑 v3 消融（隔离梯度 L0–L5 + 通道分解）** —— 设计已冻结：
  `experiment/v3-ABLATION-REGISTRATION.md`（含 AMENDMENT 1/2/3），操作手册
  `experiment/v3/RUNBOOK.md`。阻塞：双厂新 API keys + 缺陷密钥第三方托管。
  执行：Claude 生成代码并跑，你只做钥匙/密封/盲评。
  **2026-08-04 进展**：规则手册已由你颁行为 scoped 版（AMENDMENT 3）；
  跑臂前三道闸门写进 RUNBOOK §7b，前两道由 CI 强制。语料自检 60/60 全绿
  （`check_corpus.py`）。干净集实测两个独立样本各 20 个增量：
  **有效报警 0/40**（CI [0%, 8.8%]），**引用未下发规则 3/40**（CI [1.6%, 20.4%]）。
  OpenAI 半边预检待你在 runner 上跑（`v3-preflight.yml`），沙箱不通该域名。
- ✅ **A2. 真实部署数据写进 §4.2** —— 已挖掘并写入（`experiment/v3/real-ledger/`）：
  7 周期、裁定 BLOCK×5→PASS_WITH_CAVEATS→PASS、发现数 7-4-3-2-1-1-0、
  12/14 行为确认。只报告可观察事实：这些发现均在其所门禁的下游动作之前关闭；
  该部署没有控制条件，因此不再加入“没有这条环就会全部下行”的反事实。
- ⬜ **A3. successor study 跑完后按冻结结果改写 §4.4 定位** —— 只有完整执行、
  盲评和预注册分析完成后，才以 v4 的配置级效应、误拦、净修复与成本替换旧 pilot
  的主证据位置。零结果、方向相反结果和不确定区间同样照报；不得预先写成“测了判别力”
  或暗示 cross-vendor 获胜。执行：Claude，依赖 A6 的全部结果门槛。
- ⬜ **A4. （第四轮审计 EIC 建议）以 audits/ 自审链为实证重心** ——
  合成试验降级为可行性附录。决策点在你：主论文改不改由你定；
  workshop 两版按各自 CFP 口味取舍（Academia 版建议采纳）。

- 🔒 **A5. Part C 代码审计消融（变异测试法）** —— 设计已冻结：
  registration AMENDMENT 2；规则模板 `templates/AUDIT_RULES_CODE.md`。
  ground truth 来自密封的变异日志；测量目标 = 逃过全部确定性工具、
  仅评审可捕获的语义 bug 份额（"歧义"的量化）。阻塞同 A1（keys+托管）。
  预注册方向性假设：隔离效应在代码上大于数据。

- 🔒 **A6. CrossAudit v4 Causal Successor Study** —— 2026-09-01 已注册，尚未运行，
  且本次论文修订前没有查看任何 v4 结果。权威设计为 `experiment/v4/REGISTRATION.md`，
  统计分析、功效与停止规则分别由同目录的 `SAP.md`、`POWER.md`、
  `STOPPING-RULES.md` 冻结。七条承诺逐项进入同一研究计划：
  1. 实际模型产物上的 Generator×Auditor crossed assignment，只作配置级因果估计；
  2. DCL、领域工具、规则、门禁和有界修订分别消融，不用一个 recall 代替全部作用；
  3. broad 与 corpus-scoped Constitution 的精确度对照；
  4. no-audit / shadow / hard-gate 的纵向防御性编程与 Goodhart 测量；
  5. seeded、自然发生、clean、ambiguous-but-not-wrong 四类材料；
  6. 初始产物→审核→修订→复审→最终产物的净修复与新缺陷分析；
  7. final-only / ordinary log / CrossAudit ledger 的第三方重建与篡改检出实验。
  全部比较以 task/increment 为独立单位，重复调用，盲法裁定，同时报告 recall、precision、
  clean false-block、净修复、输出膨胀、人工时间、成本和延迟。注册与 harness 只是设计证据，
  不得写成 cross-vendor、某项消融或 hard gate 已经有效。执行受冻结检查、凭据与盲评门槛约束。

## B. 图与表

- ✅ B1. Figure 1 重画（顺时针环、白话标注、300dpi 逐区查重叠）
- ✅ B2. Table 1 相关工作对比表（●/~/– 三档 + 诚实图注）
- ✅ B3. Graphical abstract（论文图同款视觉标准）+ Figure 1 独立导出
- ✅ **B4. 不变量参考卡**：I1–I8 × 一句话保证 × 执行机制 × 实现状态表，
  放 §3.2，同时替掉 §4.1 部分重复叙述。执行：Claude。
- ✅ **B5. §4.3 结果表加 permutation chance-floor 列**（4.8/22.4/31.8 of 43，
  frozen map、lenient 层；strict 层地板为 4.2/16.3/24.4）。
  **门槛：gated on R1** —— 数字必须取自 `experiment/results/NULLCHECK.json`
  的重算产物，不得再引用旧值 4.7/22.4/31.9（其生成实现从未入库，见
  `improvements/04-repo-hygiene-and-reproducibility.md` R1）。
  执行：Claude，10 分钟。
- ✅ **B6. §3.4 终止状态机小图**（OPEN→BLOCKED→revise/dispute→PASSED/ESCALATED，
  round ≤ 3）。执行：Claude。
- ✅ **B7. 真实周期轨迹图**：数据已备（real-ledger），画 7 周期时间线
  （commit→报告→裁定→修复，双仓交替）。只用过程元数据，不含科学内容。
  执行：Claude。可与 A2 一起进 §4.2。

## C. 行文（第四、五轮审计遗留）

- ✅ **C1. 逗号拼接人工通读** —— 已完成，但结论与原条目不同，故记录经过。
  原列出的"~67 处"来自本地 agent 生成、却从未入库的清单
  （`paper/reviews/STYLE_DEAI_2026-07-31.md` 不存在）——数字比它的证据活得久，
  正是本仓库反复自查出的 I2 问题。故重建工具：`paper/check_splices.py`
  用 spaCy 依存分析做结构判定（左右两侧各自能否独立成句），
  并自带 20 句标注自测（`--selftest`：召回 7/8、误报 1/12），
  因为一个未标定的仪器报出"零"毫无意义。
  在正文上跑出 13 个候选，逐条人工判读后：**真正的逗号拼接只有 1 处**，
  在 §3.3 元规则串里（`CA-META-003` 那句），已改为 "and so does not legislate
  taste"（不新增分号、不新增破折号，` --- ` 计数仍为 9）。
  其余 12 条全部是同位语、前置状语从句或括号插入语，属工具误报，正文无需改动。
  执行：Claude；工具已入库，可随时重跑。
- ✅ **C2. §5 要点节奏变化**（bullet 句式过齐）与 **§6 段落合并**。
  执行：Claude；此前定为 Major Revision 项，可与 A3 一起做。
- ✅ **C3. Keywords 行插入摘要下方**（主选 8 个已定：agentic science,
  AI scientist, scalable oversight, cross-vendor auditing, LLM-as-a-judge,
  self-preference bias, research integrity, human-in-the-loop）。执行：Claude。

## D. 投稿工程（详见 `paper/submissions/SUBMISSION-PLAN.md`）

> **2026-07-31 操作者决定：先发 arXiv，NeurIPS 投稿格式暂缓。**
> D2/D3/D4/D5 全部转入 ⏸ 暂缓（骨架保留不动，车道重开时继续）；
> 新增 D6 为当前 D 区唯一活跃项。

- ✅ D1. 两家 NeurIPS 2026 workshop 骨架 + 逐节砍稿预算（8/29 截稿）
- ⏸ **D2. 9 页 Academia 版实际压缩**（骨架注释里的 map 逐节执行；
  重开时需决定 Table 2 不变量卡与 Figure 2 终止图是否进 9 页版）
- ⏸ **D3. 5 页 Molecular 版重构**（deployment-first；A1 跑完则梯度图当主图）
- ⏸ **D4. 双盲清单执行**：匿名镜像、作者信息剥离、pdfauthor 清空、
  镜像内姓名邮箱自查（清单在 SUBMISSION-PLAN §四）
- ⏸ **D5. 官方 neurips_2026.sty 下载放入** `paper/submissions/neurips2026/`
  （沙盒下不了，你从 CFP 页下载，丢进目录即自动生效）
- ⬜ **D6. arXiv 提交**：材料与逐步清单已备齐（`paper/ARXIV.md`——
  `crossaudit.tex` 加两张外部矢量 PDF 的构建源包已做干净目录验证，并备有
  表单元数据、正文摘要、类目与许可建议）。
  执行：**你上传**（账号 + 背书路径在你手里）；拿到 id 后 Claude 回填
  CITATION.cff 与双语 README 的引用行。

## E. 阻塞项汇总（都在你手里，2026-08-04 更新）

只剩需要你的账号、凭据或科学判断的四项；其余全部已执行。

1. 🔑 **密钥**：撤销全部曾出现在对话里的旧密钥；新密钥进 repository secrets
   （`EXP_ANTHROPIC_KEY` / `EXP_OPENAI_KEY`），模型 ID 进 repository variables
   （`EXP_MODEL_ANTHROPIC` / `EXP_MODEL_ANTHROPIC_ALT` / `EXP_MODEL_OPENAI`）。
2. 🔏 **缺陷密钥托管**三选一（`seal_key.py` 的 collaborator / osf / encrypted；
   hash-only 不支持任何盲评主张），然后 `SEAL-v3.json` 入库。
3. 🌐 **跑 `v3-preflight.yml`**：OpenAI 半边预检只能在能连该域名的 runner 上跑。
   Anthropic 半边已跑完并入库（`PREFLIGHT.json`）。
4. 👁 **盲评** 1–2 小时（臂跑完后）+ 🗳 **A4 重心决策** + 📄 **arXiv 上传**（D6）。

已从本表移除：C1（已完成，见上）；scoped 规则手册的颁行（已由你 2026-08-04
指令颁行为 AMENDMENT 3）。

## 推荐执行顺序

B5 → C3 → A2+B7（一次提交）→ B4 → B6 → C1 → D2 →（keys 到位）
preflight 双厂 → 密封 → A1 → A3+C2 → D3 → D4 → D6。
截至 2026-08-04，箭头左侧到 C1 为止全部完成；下一步的第一个动作是 E 区第 1 项。
