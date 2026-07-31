# 05 — Packaging: `pip install crossaudit` | 打包设计

**Status 状态**: design frozen 2026-08-01, implementation not started
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
