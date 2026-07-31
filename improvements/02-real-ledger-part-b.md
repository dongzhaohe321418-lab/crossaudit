# 02 · The real deployment ledger as labelled data | 真实部署账本作为带标签数据

Companion to `experiment/v3-ABLATION-REGISTRATION.md` (Part B). Mined
artifacts: `experiment/v3/real-ledger/`. 对应注册文档 Part B；挖掘产物见
`experiment/v3/real-ledger/`。

## 1. What the ledger contains | 账本里有什么

**EN** — The operator's live pipeline (`perovskite-screening` +
`perovskite-screening-audit`, frozen at `af0dc587` / `88b92429`) produced a
complete, real supervision chain: 7 audited cycles across two days; decisions
BLOCK ×5 → PASS_WITH_CAVEATS → PASS; findings per cycle decaying
**7-4-3-2-1-1-0**; 14 distinct findings, of which **12 behaviourally
confirmed real** — every revise leg is a science-repo commit naming the
finding IDs it closes, verified closed by the next cycle. Auditor models:
gpt-5 / gpt-5.6 / gpt-5.6-sol via codex-cli. The absent CYCLE-000003 exists
science-side as a "Tier-0 follow-up" (a deterministic-tier leg without a
model audit) and is reported as-is.

**中文** — 操作者的真实管线（`perovskite-screening` 与其 audit 仓，冻结于
`af0dc587` / `88b92429`）留下了一条完整的真实监督链：两天内 7 个审计周期；
裁定 BLOCK×5 → PASS_WITH_CAVEATS → PASS；每周期发现数衰减
**7-4-3-2-1-1-0**；14 条独立发现中 **12 条被行为确认为真** —— 每条修订腿
都是 science 仓一个点名关闭哪些 F-编号的 commit，并由下一周期 verified
closed 复核。审计模型：gpt-5 / gpt-5.6 / gpt-5.6-sol（codex-cli）。缺失的
CYCLE-000003 在 science 侧是 "Tier-0 follow-up"（无模型审计的确定性层跟
进），如实报告。

## 2. Why this matters: labels for free | 为什么重要：标签是免费的

**EN** — The frozen label rule: CONFIRMED_REAL = the finding appears in a
later cycle's `verified_closed_findings`, or a science-repo commit subject
names it as fixed; UNRESOLVED findings are excluded from precision metrics.
Behavioural confirmation means **nobody has to re-judge the science** to get
ground truth — the loop labelled itself. Division of labour with Part A:
the synthetic corpus measures *recall* (known denominators); the real ledger
measures *precision and ecological validity* (real distribution, real
unknowing defects). Neither alone survives review; together they do.

**中文** — 冻结的标签规则：CONFIRMED_REAL = 该发现出现在后续周期的
`verified_closed_findings`，或被 science 仓某个 commit 标题点名修复；
未决发现不进精确率统计。行为确认意味着**无需任何人重新评判科学内容**
就能得到 ground truth —— 循环自己给自己打了标签。与 Part A 的分工：
合成语料测**查全率**（分母已知），真实账本测**精确率与生态效度**
（真实分布、真实的"不自知"缺陷）。两者单独都过不了审稿，合在一起可以。

## 3. Re-audit arms and endpoints | 重审臂与终点

**EN** — Over the seven pinned commits: B4 same-vendor without Constitution;
B5 same-vendor with the deployment's own audit instructions; B6 cross-vendor
replication (the historical codex reports are themselves the natural L5
arm). Endpoints: (i) precision proxy per arm against the 12 confirmed items
(matching rule frozen); (ii) pooled novel findings adjudicated by the
principal, blinded to arm, shuffled — the harness performs no scientific
judgment; (iii) the mechanisability fraction of confirmed findings — the
measured size of "the DCL you should have written", feeding the
standards-ratchet argument; (iv) convergence economics — the decay curve is
the deployment's own livelock counter-evidence.

**中文** — 对七个钉死的 commit：B4 同厂无宪法；B5 同厂 + 部署自己的审计
指令；B6 异厂复测（历史 codex 报告本身即天然 L5 臂）。终点：(i) 各臂对
12 条确认项的精确率代理（匹配规则已冻结）；(ii) 新发现合并去重后由本人
**盲评**（隐去臂名、打乱顺序）—— 评分系统不做任何科学判断；(iii) 确认项
的**可机械化比例** —— "你本该写的 DCL 有多大"的实测值，直接支撑标准棘轮
论证；(iv) **收敛经济学** —— 衰减曲线就是部署自己的 livelock 反证。

## 4. Two free sentences for the paper | 白送论文的两句话

**EN** — The counterfactual: *absent the loop, all 12 confirmed defects ship
downstream unchallenged.* And the negative discovery: an in-context
self-review arm is impossible on real data because the generator's session
state was never committed — which is not a limitation but *evidence for
invariant I2*: supervision state that lives only in model context is
unrecoverable afterwards.

**中文** — 反事实句：**没有这条环，12 条已确认缺陷将无阻碍下行。**
以及一个反向发现：真实数据做不了 in-context 自审臂，因为生成者的会话状态
从未入库 —— 这不是局限，而是 **I2 的实证**：只存在于模型上下文里的监督
状态，事后不可复原。

## 5. Compliance & status | 合规与状态

**EN** — Both science repositories are read-only inputs; committed artifacts
are Level-B redacted (structure verbatim, free text hashed). Mining is done
and key-less; re-audit arms await the shared blockers; the operator's only
hands-on step is the 1–2 h blinded adjudication.

**中文** — 两个科学仓库只读；入库产物按 Level-B 脱敏（结构原样，自由文本
哈希化）。挖掘已完成且无需密钥；重审臂等共同阻塞项；操作者唯一亲手环节
是 1–2 小时盲评。
