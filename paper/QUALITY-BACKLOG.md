# 论文质量提升清单（完整版）

汇总本会话全部已议定的提升点。状态：✅ 已完成 / ⬜ 待做 / 🔒 有阻塞。
每条注明谁执行与出处。改完一条勾一条；新点子加在对应分区，不删旧条目。

## A. 实证升级（对论文档次影响最大）

> 三项实证改进的详细中英对照说明见 `improvements/`（01 梯度消融 / 02 真实账本 / 03 代码审计）。

- 🔒 **A1. 跑 v3 消融（隔离梯度 L0–L5 + 通道分解）** —— 设计已冻结：
  `experiment/v3-ABLATION-REGISTRATION.md`（含 AMENDMENT 1），操作手册
  `experiment/v3/RUNBOOK.md`。阻塞：双厂新 API keys + 缺陷密钥第三方托管。
  执行：Claude 生成代码并跑，你只做钥匙/密封/盲评。
- ⬜ **A2. 真实部署数据写进 §4.2** —— 已挖掘完毕（`experiment/v3/real-ledger/`）：
  7 周期、裁定 BLOCK×5→PASS_WITH_CAVEATS→PASS、发现数 7-4-3-2-1-1-0、
  12/14 行为确认。§4.2 目前只有定性描述，应加这组数字 + 反事实一句：
  "没有这条环，12 条已确认缺陷将无阻碍下行"。执行：Claude，随时可做。
- ⬜ **A3. v3 跑完后改写 §4.3 定位** —— 把"本试验测分歧、不测判别力"的
  告诫升级为"v3 测了判别力"；梯度图成为主证据图。执行：Claude，依赖 A1。
- ⬜ **A4. （第四轮审计 EIC 建议）以 audits/ 自审链为实证重心** ——
  合成试验降级为可行性附录。决策点在你：主论文改不改由你定；
  workshop 两版按各自 CFP 口味取舍（Academia 版建议采纳）。

- 🔒 **A5. Part C 代码审计消融（变异测试法）** —— 设计已冻结：
  registration AMENDMENT 2；规则模板 `templates/AUDIT_RULES_CODE.md`。
  ground truth 来自密封的变异日志；测量目标 = 逃过全部确定性工具、
  仅评审可捕获的语义 bug 份额（"歧义"的量化）。阻塞同 A1（keys+托管）。
  预注册方向性假设：隔离效应在代码上大于数据。

## B. 图与表

- ✅ B1. Figure 1 重画（顺时针环、白话标注、300dpi 逐区查重叠）
- ✅ B2. Table 1 相关工作对比表（●/~/– 三档 + 诚实图注）
- ✅ B3. Graphical abstract（论文图同款视觉标准）+ Figure 1 独立导出
- ⬜ **B4. 不变量参考卡**：I1–I8 × 一句话保证 × 执行机制 × 实现状态表，
  放 §3.2，同时替掉 §4.1 部分重复叙述。执行：Claude。
- ✅ **B5. §4.3 结果表加 permutation chance-floor 列**（4.8/22.4/31.8 of 43，
  frozen map、lenient 层；strict 层地板为 4.2/16.3/24.4）。
  **门槛：gated on R1** —— 数字必须取自 `experiment/results/NULLCHECK.json`
  的重算产物，不得再引用旧值 4.7/22.4/31.9（其生成实现从未入库，见
  `improvements/04-repo-hygiene-and-reproducibility.md` R1）。
  执行：Claude，10 分钟。
- ⬜ **B6. §3.4 终止状态机小图**（OPEN→BLOCKED→revise/dispute→PASSED/ESCALATED，
  round ≤ 3）。执行：Claude。
- ⬜ **B7. 真实周期轨迹图**：数据已备（real-ledger），画 7 周期时间线
  （commit→报告→裁定→修复，双仓交替）。只用过程元数据，不含科学内容。
  执行：Claude。可与 A2 一起进 §4.2。

## C. 行文（第四、五轮审计遗留）

- ⬜ **C1. 逗号拼接人工通读**：~67 处候选点（清单在
  `paper/reviews/STYLE_DEAI_2026-07-31.md`，由你本地 agent 生成）。
  执行：你通读定夺，Claude 批量执行修改。
- ⬜ **C2. §5 要点节奏变化**（bullet 句式过齐）与 **§6 段落合并**。
  执行：Claude；此前定为 Major Revision 项，可与 A3 一起做。
- ⬜ **C3. Keywords 行插入摘要下方**（主选 8 个已定：agentic science,
  AI scientist, scalable oversight, cross-vendor auditing, LLM-as-a-judge,
  self-preference bias, research integrity, human-in-the-loop）。执行：Claude。

## D. 投稿工程（详见 `paper/submissions/SUBMISSION-PLAN.md`）

- ✅ D1. 两家 NeurIPS 2026 workshop 骨架 + 逐节砍稿预算（8/29 截稿）
- ⬜ **D2. 9 页 Academia 版实际压缩**（骨架注释里的 map 逐节执行）
- ⬜ **D3. 5 页 Molecular 版重构**（deployment-first；A1 跑完则梯度图当主图）
- ⬜ **D4. 双盲清单执行**：匿名镜像、作者信息剥离、pdfauthor 清空、
  镜像内姓名邮箱自查（清单在 SUBMISSION-PLAN §四）
- ⬜ **D5. 官方 neurips_2026.sty 下载放入** `paper/submissions/neurips2026/`
  （沙盒下不了，你从 CFP 页下载，丢进目录即自动生效）

## E. 阻塞项汇总（都在你手里）

1. 🔑 双厂新 API keys + 撤销全部旧密钥（A1 前置）
2. 🔏 缺陷密钥第三方托管方式三选一（RUNBOOK 阶段 0）
3. 👁 v3 Part B 盲评 1–2 小时（臂跑完后）
4. 📖 C1 的通读定夺
5. 🗳 A4 的重心决策（主论文层面）

## 推荐执行顺序

B5 → C3 → A2+B7（一次提交）→ B4 → B6 → D2 →（keys 到位）A1 → A3+C2 → D3 → D4。
其中 B5/C3/A2/B7/B4/B6 全部无阻塞，说"开工"即可连续完成。
