# 05 — Packaging: `pip install crossaudit` | 打包设计

> **Superseded in part by AMENDMENT 1 (2026-08-01, end of file): the v2 text
> there is the operative contract.** The v1 body below stands unedited as the
> record of what was first frozen. （本文下方正文为 v1 首次冻结记录，操作
> 合同以文末修正案一之 v2 全文为准。）

**Status 状态**: design v1 frozen 2026-08-01 morning; v2 adopted via
Amendment 1 same day, implementation not started
（设计冻结，实现未启动）. Merged from the cloud session's framework (layout,
constraints 1–5, CLI verbs, release engineering, roadmap skeleton) and the
local session's review (constraints 6–7, the provider layer, the GitHub
wizard and its platform limits, receipt fields). PyPI name `crossaudit`
verified unclaimed (404) 2026-08-01. Where this document disagrees with
`experiment/v3-ABLATION-REGISTRATION.md` or the paper's frozen claims, those
win.

**Product surface 产品面**: a user brings exactly two things — a Constitution
markdown and two model API keys — and gets a running audit loop. "UI" at this
stage means CLI clarity, not a graphical console (the supervision console
remains an R4-candidate with its own iron rule: it writes nothing of its own).
（用户只带两样东西：一份宪法 markdown、两个模型 API key。本阶段的"UI"指
CLI 清晰度，不是图形界面。）

## 1. Design constraints 设计约束

Constraints 1–5 are the protocol's own, not engineering taste; 6–7 come from
the packaging review. （前五条由协议自身决定，后两条来自打包评审。）

1. **Zero heavy dependencies in core 核心零重依赖.** The paper says
   "stdlib-plus-PyYAML" and packaging must keep it true: core depends on
   PyYAML only. Vendor SDKs are not merely relegated to extras — they are
   **absent entirely**; the provider layer speaks HTTP via stdlib `urllib`
   (§5), as `experiment/run_arm.py` already proves is enough. Domain tools go
   in extras.
2. **Verifier self-identification 验证器自我指认 (I7 completion).** Every
   receipt records the `crossaudit` package version and its own distribution
   hash. The machine that admits is itself pinned in the ledger — promised in
   the paper's §6 roadmap, delivered here (§7).
3. **Fail-closed defaults 缺省即拒.** Anything missing — tool, key, config
   field, schema check — denies and names the missing thing. R2's lesson is
   institutionalised as the `doctor` verb: preflight is a first-class command,
   not a habit.
4. **The Constitution is not in the package 宪法不入包.** It is each
   deployment's human-written law. The package carries only templates that
   `init` instantiates.
5. **Frozen paths do not move 冻结路径不搬 (R9 principle).** The paper and
   registration documents cite `controller/` and `checks/`; those paths remain
   importable as thin shims forwarding to `src/crossaudit/` with a deprecation
   note. Existing tests keep passing before, during, and after migration.
6. **Honest isolation tiering 诚实隔离分级.** A local CLI run collapses
   *permissive* isolation: both vendors' keys sit in one process environment
   (parametric and contextual isolation survive). This is a protocol-fidelity
   fact, not an implementation detail, so it is **recorded, not narrated**:
   receipts carry `isolation_mode: local | github-pair` and the wizard-
   provisioned variant records `provisioned_by: single-operator-wizard`
   (§6–7). Documentation states plainly what each tier guarantees.
7. **`pip install` has zero side effects 安装零副作用.** No network, no auth,
   no filesystem writes beyond the package itself. Installs run in CI,
   containers, and resolvers with no terminal attached — and an *audit tool*
   that phones home at install time forfeits exactly the trust it exists to
   provide. Everything interactive lives behind an explicit `crossaudit init`.

## 2. Package layout 包布局 (src-layout)

```text
src/crossaudit/
├── controller/      # state machine, deadletter (from controller/)
├── receipt/         # verify.py + schema v2 (verifier_version, dist_hash, isolation_mode)
├── dcl/             # check framework + builtin checks (schema/units/convergence/provenance)
│   └── code/        # Part C four channels, productised (extra [code])
├── auditor/         # audit runner + reply validator + prompt assembly (core, no SDKs)
├── providers/       # urllib adapters: openai_compat.py, anthropic.py, gemini.py (§5)
├── scaffold/        # init templates: workflows, crossaudit.yml, AUDIT_RULES template
├── cli/             # verb implementations (§4)
└── _selfid.py       # version + own distribution hash, consumed by receipt/
tests/               # the 41 existing tests migrate here and run against the installed package
controller/ checks/  # ← compatibility shims: import-forward + deprecation note (constraint 5)
```

**Dual-existence rule for Part C 双份共存规则**: `experiment/v3/partC/` stays
frozen as the registered experiment's harness — the A5 run uses *that* copy
under the registration's authority. `crossaudit.dcl.code` is the living,
productised descendant. Divergence is legal and expected; the registration
copy never chases the package. （实验目录里的四通道为注册实验冻结件；包内
副本是活工具。允许分叉，注册件永不追包。）

**Not in the wheel 不进 wheel**: `paper/`, `experiment/`, `audits/`,
`improvements/`, `ledger-mirror/`, `diagrams/`, `articles/`. The package is
the execution machine; the repository is the research record. The sdist
carries `examples/` only.

## 3. CLI surface 命令面

Verbs mirror the loop itself. All verbs: `--json` for machine consumption,
exit codes fail-closed (0 = the good outcome, specific nonzero per denial
class), no colour-only signals (severity is always also a word).

| Verb | Does | Ships in |
|---|---|---|
| `init` | Interactive wizard. First question is the tier: `--local` (one machine, weak isolation, ten-minute start) or `--github` (two-repo full fidelity, §6). Generates `crossaudit.yml` + Constitution from template or from the user's markdown. | 0.1 local / 0.3 github |
| `doctor` | Preflight everything: tools, keys present (never printed), config schema, git state, branch-protection reality (§6). Prints actionable fixes. R2, institutionalised. | 0.1 |
| `check` | Run the DCL locally over an increment. | 0.1 |
| `verify RECEIPT [--admit]` | Full receipt verification; `--admit` consumes via the controller. | 0.1 |
| `audit --sha` | Full cycle: DCL → model auditor → validated reply → report + receipt into the ledger. | 0.2 |
| `status` | Cycle/round state from the controller ledger. | 0.2 |
| `dispute F-ID` | Open the one-shot dispute lane for a finding. | 0.2 |
| `mirror` | Structurally redacted public mirror (today's `tools/redact_mirror.py`, promoted). | 0.3 |

Configuration is exactly one `crossaudit.yml` (schema-validated by `doctor`
and at load); credentials live in environment variables only — never in the
file, never in argv, never echoed. （配置只认一个 crossaudit.yml；密钥只走
环境变量，永不回显。）

## 4. Provider layer 模型接入层

Three thin stdlib-`urllib` adapters, no vendor SDKs anywhere (constraint 1):

- **`openai_compat`** — one adapter covers OpenAI, DeepSeek, Qwen, Mistral,
  Groq, xAI, Ollama and the rest of the OpenAI-compatible world;
- **`anthropic`** — native Messages API (already written in `run_arm.py`,
  promoted);
- **`gemini`** — native `generateContent`.

`crossaudit.yml` names `provider`, `model`, and optional `base_url` per role
(generator-side checks never call models; only the auditor role does). The
long tail is `openai_compat` + `base_url`. Keys via `CROSSAUDIT_AUDITOR_KEY`
(and, for tooling that needs it, `CROSSAUDIT_GENERATOR_KEY`), resolved at call
time, absent = `doctor` failure. Adapter tests run against recorded fixtures;
CI never holds a live key. deliberately rejected: `litellm` — instant breadth
at the price of a large fast-moving dependency tree inside an audit tool whose
credibility rests on being small enough to read. （拒绝 litellm：广度换来
巨大依赖树，审计工具的可信恰恰建立在小到可通读之上。）

## 5. `init --github` wizard 向导

The onboarding friction between tiers is what decides which one users live
in; the wizard exists to make the *full-fidelity* tier the easy one.

Sequence: (1) auth — prefer an existing `gh` CLI login (credentials stay in
gh's keychain, the package touches none), else GitHub OAuth device flow, else
guided fine-grained PAT paste; (2) create or adopt `<name>` +
`<name>-audit`; (3) push scaffolds (the three workflows, `crossaudit.yml`,
Constitution); (4) write model keys as encrypted Actions secrets via API;
(5) enable branch protection with `crossaudit/admission` as a required check —
the deployer toggle of Table 2/I8, automated; (6) run a Tier-0 smoke cycle and
print the first verdict. Ten minutes to a first committed audit.

Three platform truths the wizard must disclose, not paper over:

1. **Branch protection is paid on private repos.** Free-plan private science
   repos cannot enforce the admission check. The wizard detects the plan and
   says the paper's own sentence: post-push summaries are notifications, never
   admission. `doctor` re-checks this forever after.
2. **Fine-grained PATs cannot be created by API** (GitHub's deliberate
   choice). For the asymmetric token pair (`SCIENCE_TO_AUDIT_TOKEN` /
   `AUDIT_TO_SCIENCE_TOKEN`), the wizard's ceiling is deep links with
   pre-filled scopes; the user clicks Generate twice; the wizard uploads the
   results as secrets. Full automation would require operating a central
   GitHub App — new trust surface, rejected for now.
3. **One login provisioned everything.** Acceptable for a single researcher,
   but it is a fact about the deployment's trust posture, so it goes in the
   ledger: `provisioned_by: single-operator-wizard` in receipt metadata. The
   strict path (two identities, hand-provisioned) stays documented.

## 6. Receipt schema v2 回执模式 v2

Adds, next to the v1 bindings: `verifier_version`, `verifier_dist_sha256`
(from `_selfid.py`), `isolation_mode`, `provisioned_by`. Schema changes
follow the registration discipline — dated amendment sections, never silent
edits; `verify` refuses receipts whose schema version it does not know
(fail-closed, constraint 3). （回执模式改动走注册式的注日期修正案；验证器
拒绝未知模式版本。）

## 7. Extension points 扩展点

Entry-point group `crossaudit.checks`: domain check packs distribute as
plugins — first-party extras (`crossaudit[compchem]`, `crossaudit[code]`) or
third-party (`crossaudit-checks-ml`). The DCL's reach becomes a community
good, aligned with the paper's argument that the Constitution should become a
community object. Plugin checks are still DCL: deterministic, no learned
component, or they do not belong in the group.

## 8. Release engineering 发布工程

- **Typing**: `py.typed`, full annotations; the Part C lesson (typing moves
  contract drift left) applied to ourselves. `ruff` + `mypy` join the
  existing CI tests job.
- **Publishing**: git tag → CI → **PyPI Trusted Publishing (OIDC, no
  long-lived token)**, TestPyPI first, PyPI attestations on. The operator owns
  the PyPI account and the one-time publisher registration; nothing else
  about release is manual.
- **Supply chain, both ends**: generated workflow templates pin
  `pip install crossaudit==X.Y.Z --require-hashes`; receipts record the
  verifier's own version + hash (constraint 2). Pinned from outside, attested
  from inside.
- **Versioning**: SemVer; `0.x` may break CLI flags with a changelog entry,
  receipt schema only ever via amendment.

## 9. Roadmap 路线

| Version | Contents | Gate |
|---|---|---|
| **0.1.0** | src migration + shims, `init --local`, `check`, `verify`, `doctor`, tests migrated and green, TestPyPI pipeline live | 41 tests green through the move; paper-cited paths still resolve |
| **0.2.0** | provider layer + auditor runner, `audit`/`status`/`dispute`, receipt v2 self-identification | the minimum product promise holds: one markdown + two keys = running local loop |
| **0.3.0** | `init --github` wizard (auth ladder, secrets, branch protection with plan detection, smoke cycle), `mirror` | a fresh GitHub account reaches a committed first verdict in ten minutes |
| **0.4.0** | plugin group + `[compchem]` first pack + `[code]` channels | third-party check pack installs and registers cleanly |
| **1.0** | after the v3 experiment lands and branch-protection binding is field-tested | paper's Table 2 statuses updated in an arXiv revision |

（相对云端草案的一处改动：github 向导独立为 0.3.0——它是把用户引向完整
保真档的杠杆，值得整个版本位；插件生态后移到 0.4.0。）

## 10. Operator-only items 操作者项

PyPI account + Trusted Publisher registration (one-time, needs your login);
the name `crossaudit` is unclaimed as of 2026-08-01 — 0.1.0 to TestPyPI then
PyPI claims it; GitHub OAuth device-flow needs no app registration (uses
GitHub's public client flow via gh).

---

## AMENDMENT 1 (2026-08-01) — v2 adopted, two boundary resolutions, operator product directive

**EN summary.** A same-day external review found seven P0 trust gaps in the v1
text above and supplied a v2 one-pager; the cloud session independently
reviewed v1 (four P1s, one P1.5, six P2s). All P0/P1 findings are accepted;
v2 below is the operative contract, with the cloud deltas folded in. Boundary
resolutions: milestone 0.2 is audit-only (one auditor key suffices), but per
the operator's product directive the full two-key loop with a controlled
Generator adapter is the product north star, delivered at a named milestone
rather than promised early; the enforced GitHub tier requires a user-owned
GitHub App plus an independent, persistent, atomic controller. v1 stands
unedited above as the first-freeze record.

### 评审记录与核验

同日两份评审：

1. **外部严谨复核**（P0×7、P1×7、附 v2 一页稿）。P0 全部接受。抽验属实：
   `pyproject.toml` 现为 `packages = []` 的环境清单，不可发布；参考实现确为
   push-to-main 后置审计（`on-push-trigger-audit.yml`）；GitHub status 确可被
   任意具写权限者同名伪造；wheel 哈希无法从解压后的安装自证。
2. **云端会话对 v1 的评审**（P1×4、P1.5×1、P2×6，结论"通过"）。评审对象为
   v1，时序上早于 v2 到达；其全部条目与 v2 兼容，并入见下文增量清单。

一处核验纠偏：复核称 `str | None` 语法需 Python 3.10 —— 实情是
`controller/state.py` 带 `from __future__ import annotations`，注解层面 3.9
可运行；但 `c | {...}` dict 合并本就要求 ≥3.9，且 3.9 已于 2025-10 EOL，故
`requires-python >= 3.10` 照采，理由记为版本生命周期而非语法必需。

### 两项边界决议

**决议一（含 2026-08-01 操作者产品指令）。** 协议事实不变：CrossAudit 是
审计器与控制器，Generator 是用户自己的研究 agent，部署中其厂商在
`crossaudit.yml` 里申明以供 I1 断言。因此**里程碑 0.2 为 audit-only：一份
Constitution + 一个 Auditor key 即可开始审计**，`CROSSAUDIT_GENERATOR_KEY`
不属于 0.2 的环境变量契约。但操作者在裁定期间下达产品指令：最终产品形态为
"一份总体审计 markdown + 两个 API key + 向导自动创建双仓 = 稳定运行的完整
循环"。二者的合并方式是**排序而非取舍**：

- 0.3 的向导从第一天起就收两个 key（都写成加密 secrets），并明说当前只有
  auditor key 在用；
- **受控 Generator adapter 是 0.5 的具名交付物**（受版本控制的 adapter 契约
  + 独立验收 gate），到位后"两 key 完整循环"承诺才生效——在那之前所有文案
  不得提前宣称。P0-1 的红线（不能把尚不存在的 Generator 功能伪装成输入契约）
  由此满足，产品北极星也不被砍掉。

**决议二。** enforced 档接受"用户自有 GitHub App + 独立持久原子 controller"
为前提。0.3 交付 notification-only 与 gated-permissive 两档、doctor 实测
探针与三态措辞；enforced-app-bound 须通过 BLOCKED-不可-merge /
PASS-可-merge 实测烟测后方可声称，目标 0.5–1.0。前提不满足时，产品措辞
封顶为 gated-permissive。操作者"loop 一定要稳定"的要求落点即持久原子
controller 后端——它同时是稳定性与 admission 语义的地基。

### v2 之上的增量（云端 P1/P1.5/P2 并入）

1. **跨档准入策略**：`crossaudit.yml` 增 `isolation.minimum`；
   `verify --admit` 拒绝隔离证据弱于部署最低档的回执。回执在 v2 的五维
   操作证据（execution/credential/provider/provisioner/admission）之上导出
   论文 I1 术语的三维布尔 `{parametric, contextual, permissive}`；向导单人
   开通即 `permissive: false`。
2. 回执字段清单补 `receipt_schema: 2` 字段本身。
3. `CROSSAUDIT_GENERATOR_KEY` 自 0.x 契约移除，随 0.5 的 adapter 契约回归
   （决议一）。
4. 测试迁移措辞精确化：**40** 个 controller/verifier/validator 测试迁入
   `tests/`；partC 种子测试留在冻结 harness，包内副本另计；CI 与第六轮
   dispositions 中的引用同步更新。
5. （P1.5）fine-grained PAT 新建页的参数预填支持有限，0.3 实现时先实测再
   收窄措辞，不承诺 GitHub 未提供的表单。
6. （P2 批量）`requires-python >= 3.10`（随本修正案提交生效）；CI 矩阵加
   macOS/Windows；兼容垫片的死亡条件：不早于 1.0，且拆除须随论文修订版
   同步更新引用；`--local` 档账本落点 `.crossaudit/cycles/`；插件必须声明
   `dcl_api_version`，错代 fail-closed；TestPyPI 与 PyPI 是**两次**独立的
   Trusted Publisher 注册。

### 取代关系

v1 正文的 §1 产品面、§2–§9 全部由下文 v2 取代；v1 的约束 6/7 在 v2 中重述
并给出可验收定义。v1 全文一字未改，保留为首次冻结记录。

### 路线图（合并后）

| 版本 | 交付 | 不可跳过 gate |
|---|---|---|
| 0.1.0 | src 迁移、CLI（init --local/check/verify/doctor）、显式 state store、脚本级垫片 | wheel/sdist/source 三路径安装、Python 矩阵、无网络 import、旧路径与 receipt 语义兼容 |
| 0.2.0 | providers、audit/status/dispute、receipt v2 自指认 | audit-only 承诺兑现：一 markdown + 一 auditor key = 本地环跑通；provider fixtures、egress/超时/密钥红删、持久单次消费 controller |
| 0.3.0 | gh 为硬前提的 GitHub bootstrap（plan → --apply）、双 key 收纳、mirror | PR/merge-queue head-SHA gate、callback 仅定位、BLOCKED/PASS 合并烟测、可恢复 bootstrap、三态措辞如实 |
| 0.4.0 | check 插件组 + 首方包 | allowlist、子进程隔离（无 key 无网络）、插件 lock/digest 入回执 |
| 0.5.0 | **受控 Generator adapter** → 两 key 完整循环承诺生效；enforced-app-bound 若 App+controller 就绪 | adapter 契约版本化 + 独立验收；enforced 烟测 |
| 1.0 | 稳定 schema/API | v3 实验落地、独立安全复核、真实部署 gate 证据、支持期承诺 |

### v2 全文（操作合同，as received 2026-08-01）

见本次修正案提交中随附的 `05a-packaging-v2.md`——v2 一页稿逐字保存，含
产品契约三档表、七条可验收约束、CLI 契约与退出码、receipt v2 与 controller
transaction 落账顺序、GitHub 三态、打包/插件/发布工程、逐版本 gate。该文件
与本修正案同权：v2 全文为合同正文，本修正案为其决议与增量记录。
