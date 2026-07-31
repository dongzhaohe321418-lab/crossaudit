# 03 · Auditing generated code | 审计生成的代码

Companion to `experiment/v3-ABLATION-REGISTRATION.md` (Amendment 2) and
`templates/AUDIT_RULES_CODE.md`. 对应注册文档修正案 2 与 CA-CODE 规则模板。

## 1. The asymmetry | 不对称性

**EN** — A data defect corrupts one increment; a defective analysis script
corrupts **every increment it touches**. Code is simultaneously where the
deterministic layer is weakest, where semantic ambiguity is largest, and
where same-source bias is most dangerous — both vendors trained on the same
public code corpus and share its idiomatic bugs. The operator's point in one
line: the ambiguous zone is exactly the zone that most needs cross-checking.

**中文** — 数据缺陷污染一个增量；有缺陷的分析脚本污染**它触及的每一个
增量**。代码同时是确定性检查最弱、语义歧义最大、同源偏差最危险的地带 ——
两家模型读过同一批公开代码语料，共享同样的惯用 bug。操作者的洞察一句话：
最歧义的地带恰是最需要交叉核验的地带。

## 2. Method: mutation testing as seeded defects | 方法：变异测试即代码版注入缺陷

**EN** — Correct, tested analysis scripts in the reference-increment style
are mutated deterministically: dropped unit conversions, inverted
convergence predicates, off-by-one column selections, silenced exceptions,
boundary flips. The mutation log is the sealed defect key — exact ground
truth, same escrow rule as Part A. Equivalent-mutant risk is handled before
any arm runs: each mutant must change behaviour on a toy fixture, or it is
discarded and logged.

**中文** — 对正确且带测试的分析脚本做确定性变异：丢单位换算、收敛判据
取反、列选择差一、静默异常、边界翻转。变异日志就是密封的缺陷密钥 ——
精确 ground truth，托管规则与 Part A 相同。等价变异体风险在跑臂前处理：
每个变异必须在 toy fixture 上确实改变行为，否则剔除并留痕。

## 3. Five channels, one measurement target | 五级通道与唯一测量目标

| Channel 通道 | Instrument 工具 | Example 例 |
|---|---|---|
| syntactic 语法 | linter | unused/shadowed variable 未用/遮蔽变量 |
| type-level 类型 | type checker | unit-carrying type dropped 带单位类型被丢 |
| test-killable 测试可杀 | test suite 测试套件 | inverted predicate a test exercises 测试覆盖的判据取反 |
| tool-verifiable 工具可验 | dry-run + output contract 干跑+输出契约 | schema drift in results 结果 schema 漂移 |
| **review-only 仅评审可捕** | none of the above 以上皆无 | type-safe, test-surviving, semantically wrong 类型安全、测试存活、语义错误 |

**EN** — The review-only stratum is *the* measurement: the fraction of
seeded semantic bugs that survive every deterministic instrument but are
caught by model review, per rung of the isolation ladder (L1–L5 reused
verbatim). That number is the operator's "ambiguity", quantified — the
measured value of cross-vendor code audit. Pre-registered directional
hypothesis: isolation effects are larger for code than for data.

**中文** — "仅评审可捕"层就是**唯一的测量目标**：逃过全部确定性工具、
按隔离梯度各档被模型评审捕获的语义 bug 份额。这个数字就是"歧义"的量化 ——
跨厂代码审计的实测价值。预注册方向性假设：隔离效应在代码上大于数据。

## 4. Protocol artefacts gained | 协议侧新增件

**EN** — New DCL members for code (lint, type check, test execution,
dry-run-on-fixture with contract comparison, diff-coverage) and a draft
CA-CODE rule family: six decidable BLOCKERs (contract header; every numeric
transform tested against a hand-computed example; no bare except / silent
NaN; pinned deps; explicit seeds; output-contract validation) plus three
ADVISORY semantic rules (implementation matches stated method; explicit
units end-to-end; numerical-stability hazards). Design principle: when a
101-class judgment call keeps recurring undisputed, tighten the decidable
rules instead of promoting the opinion — *encode the lesson, not the
opinion*. Promotion runs through the shadow-mode ratchet, never through this
experiment.

**中文** — 代码域新增 DCL 成员（lint、类型检查、测试执行、fixture 干跑 +
契约比对、diff-coverage），以及 CA-CODE 规则族草案：六条可判定 BLOCKER
（契约头；每个数值变换配手算例测试；禁裸 except / 静默 NaN；依赖钉版本；
显式种子；输出契约校验）+ 三条 ADVISORY 语义规则（实现与声明方法一致；
单位显式贯穿；数值稳定性隐患）。设计原则：当 101 类判断题反复无争议命中
时，应收紧可判定规则而非把意见升格为法律 —— **把教训编码成规则，而不是把
判断变成法律**。规则晋级只走影子模式棘轮，绝不经由本实验。

## 5. What the paper gains | 论文所得

**EN** — CrossAudit extends from a data-increment protocol to a
data-plus-code protocol; §9's litmus test ("can you write ten decidable
rules about your outputs?") gets a ready-made answer in the code domain; and
the review-only fraction gives the Discussion a measured, not asserted,
answer to "what do LLM auditors add beyond scripts?"

**中文** — CrossAudit 从数据增量协议扩展为数据+代码双域协议；§9 的检验
标准（"你的领域能写出十条可判定规则吗"）在代码域有了现成答案；
"仅评审可捕"份额让 Discussion 里"LLM 审计在脚本之外增加了什么"从主张
变成实测。
