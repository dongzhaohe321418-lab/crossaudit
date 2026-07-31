# 01 · The isolation-ladder ablation | 隔离梯度消融

Companion to `experiment/v3-ABLATION-REGISTRATION.md` (Part A + Amendment 1).
The registration is the frozen text; this document explains it.
对应注册文档 Part A 与修正案 1。注册文档为冻结权威文本；本文负责解释。

## 1. Questions | 研究问题

**EN** — Q1: does an *independent* audit agent find more, and more real,
defects than the executing agent reviewing its own work? Q2: how much do the
three supervision channels each contribute — the natural-language
Constitution applied by an LLM, executable generic rules (the DCL), and
scientific-tool verification?

**中文** — Q1：**独立的**审计 Agent 是否比执行 Agent 审查自己的工作发现
更多、且更真实的缺陷？Q2：三条监督通道各贡献多少 —— LLM 应用的自然语言
宪法、可执行的通用规则（DCL）、以及科学工具验证？

## 2. Design: one ladder, one rung at a time | 设计：一条梯子，每级只加一层隔离

**EN** — Instead of scattered baselines, the arms form a monotone ladder;
each rung adds exactly one layer of isolation between producer and reviewer.
The headline analysis is therefore a *trend*, not a pile of pairwise
comparisons — the paper's figure becomes a dose-response curve of
independence.

**中文** — 不做零散的 baseline 堆砌，而是把各臂排成单调梯子：每一级只在
生产者与审查者之间多加一层隔离。主分析因此是**趋势**而非一堆两两比较 ——
论文主图变成一条"独立性剂量响应曲线"。

| Rung 档 | Configuration 配置 | Adds 新增隔离 |
|---|---|---|
| L0 | no audit; increments admitted as produced 无审计，产出直接放行 | nothing (floor) 无（地板） |
| L1 | self-reflection in the generating session 同一会话内自省 | a review step 一个审查步骤 |
| L2 | same model, fresh instance, generation transcript attached 同模型新实例，附生成 transcript | a context boundary 一道上下文边界 |
| L3 | same model, fresh instance, no Constitution 同模型新实例，无宪法 | transcript removed 去掉 transcript |
| L4 | same model, fresh instance, with Constitution 同模型新实例，有宪法 | decidable rules 可判定规则 |
| L4b | same vendor, different model, with Constitution 同厂异模型，有宪法 | model separation 模型分离 |
| L5 | different vendor, with Constitution 异厂，有宪法 | vendor separation 厂商分离 |

Channel arms run beside the ladder 通道臂与梯子并行：A0 constant-BLOCK stub
（音量混淆的 null 桩）· A1 generic DCL scripts 通用脚本 · A2 domain tools
科学工具（解析回检、SCF 单调性、晶格自洽、物理键长）。

## 3. Corpus | 语料

**EN** — ~60 increments / ~100 seeded defects on the shared corpus, so every
comparison is per-defect paired. Each defect is pre-tagged with its cheapest
catching channel (script / domain-tool / LLM-only). Clean increments are
authored half by each vendor's model; a deterministic mutator injects the
defects, and the mutation log — the defect key — is sealed with a third
party *before* any arm runs (the v1 seal failure is documented in the paper
and must not repeat).

**中文** — 共享语料约 60 增量 / 约 100 个注入缺陷，一切比较逐缺陷配对。
每个缺陷预打"最便宜捕获通道"标签（脚本 / 科学工具 / 仅 LLM）。干净增量由
两家模型各写一半；确定性变异器注入缺陷，变异日志（即缺陷密钥）在任何臂
运行**之前**交第三方密封（v1 的密封失败已写进论文，不可重演）。

## 4. Analysis & safeguards | 分析与防呆

**EN** — Primary: trend across L1–L5 (Cochran's Q on the paired catch
matrix; adjacent-rung exact McNemar, Holm-corrected). Co-primary: false-block
rate on clean increments, same ladder — the Constitution's value may show up
mainly as *precision*, not recall. Channel decomposition: marginal catches of
A1/A2 over the LLM union. Cost endpoint: catches per false block and per
dollar per rung, with L0 as anchor. Pre-registered confound: corpus defects
are injected into increments the generator itself authored, so L1 retains
memory of the pre-mutation content; interpretation is one-sided — if
self-review *still* underperforms fresh-context rungs despite this advantage,
the deficit is robust; if it outperforms, no claim beyond "memory advantage
dominates".

**中文** — 主分析：L1–L5 趋势（配对捕获矩阵上的 Cochran's Q；相邻档精确
McNemar，Holm 校正）。共同主指标：干净增量误拦率（同一梯子）—— 宪法的
价值很可能主要体现在**精确率**而非查全率。通道分解：A1/A2 相对 LLM 并集
的边际捕获。成本终点：每档"每次误拦换多少捕获、每美元换多少捕获"，以 L0
为锚。预注册混杂：缺陷注入在生成者自己写的增量上，L1 保留对未变异内容的
记忆；解释因此是单侧的 —— 自审带着记忆优势**仍然**输给新上下文各档，
劣势才算坐实；若它赢了，只能说"记忆优势占主导"，不做更多主张。

## 5. Status | 状态

**EN** — Design frozen (registration + Amendment 1). Blocked on: fresh API
keys for both vendors; defect-key escrow. Operator's hands-on work: keys,
escrow choice, nothing else in Part A. Execution: RUNBOOK stages 1–2, 5–6.

**中文** — 设计已冻结（注册文档 + 修正案 1）。阻塞：双厂新 API 密钥；缺陷
密钥托管。操作者亲手环节：密钥与托管方式选择，Part A 内再无其他。执行按
RUNBOOK 阶段 1–2、5–6。
