# CrossAudit 打包设计框架 v2（操作合同）

> As received 2026-08-01, adopted verbatim by Amendment 1 of
> [05-packaging-design.md](05-packaging-design.md); the amendment records the
> two boundary resolutions (0.2 audit-only with the full loop as a named 0.5
> deliverable; enforced tier gated on a user-owned GitHub App plus a
> persistent atomic controller) and the deltas folded in on top of this text.
> 逐字保存；两项边界决议与增量见修正案。

状态：拟议修正案，未改写 2026-08-01 冻结的研究记录。以 dated amendment 追加
到 improvements/05，而不是静默重写历史文本。

审阅基准：main@06310d0。本版保留原有的轻依赖、宪法外置、兼容垫片与显式
GitHub 向导方向，但修正了产品输入、可验证身份、真正准入、插件隔离和发布
供应链的定义。

## 产品契约

CrossAudit 是审计器与控制器，不是科学 Generator。因而不能把尚未存在的
Generator 功能伪装成安装包的输入契约。

| 档位 | 最小输入 | CrossAudit 实际做什么 | 准入语义 |
|---|---|---|---|
| audit-only，0.2 主线 | Constitution、被审 Git 仓、Auditor provider/model/key | DCL、模型审计、receipt、controller | 本地可复核；不能宣称强制合并/部署准入 |
| full-loop，未来扩展 | 上述内容，加明确的 Generator provider/model/key 和受版本控制的 generator adapter 契约 | 才能实际驱动两模型环 | 另行验收，不能提前写进 0.2 承诺 |
| github-paired | audit-only 的输入，加 GitHub 管理权限、双仓和受保护 PR 路径 | 远端 ledger 与候选 admission check | 默认只是 verified notification；只有另有持久 controller 且 doctor 验证为 app-bound 才可称 enforced |

因此宣传语改为：一份 Constitution 加一个已配置的 Auditor key 可启动审计；
当 Generator 由本包实际接入时，完整循环才需要两个明确的模型角色与凭据。
模型名、provider、endpoint、Git/Python 环境也是显式前提，不能从 key 推断。

## 七条设计约束

| # | 约束 | 可验收定义 |
|---|---|---|
| 1 | 核心依赖预算为 1 | 运行时只依赖 PyYAML；GitHub 向导的 gh 是外部工具，模型适配器只用 stdlib urllib。构建依赖和 optional extras 不计入核心运行时。 |
| 2 | 验证器可复核地自指认 | receipt 写 project、规范 version、canonical installed-code digest、install mode、lock digest；只有外部 lock 可证明时才写 artifact SHA-256。不可把运行中包声称的 distribution hash 当作已验证 wheel hash。 |
| 3 | fail-closed 可区分 | 缺配置、未知 schema、未锁定插件、截断/符号链接、未允许的 egress、无状态持久化、未知 gate 都拒绝并给机器可读原因；doctor 默认离线、只读。 |
| 4 | Constitution 不入包 | wheel 只带模板；实际规则、policy、provider config 和允许的 plugin 清单都由部署 ledger 版本化并进入 receipt。 |
| 5 | 冻结路径可运行 | controller 和 checks 保留脚本级兼容垫片，不只是 import 转发；源码 checkout 继续支持 python 旧路径脚本。状态路径一律显式注入，绝不写 site-packages。 |
| 6 | 隔离记录证据而非标签 | receipt 分别记录 execution、credential、provider、provisioner、admission 五个维度；local 不是 github-paired 的弱同义词。 |
| 7 | 安装和导入无额外交互 | wheel 安装钩子及 import 不访问 GitHub、LLM 或遥测。pip 自己下载索引/构建依赖不属于本包可承诺的零网络。 |

## 三层结构

- 代码：`src/crossaudit/` 下有 controller、receipt、dcl、auditor、providers、
  scaffold、cli、selfid。`controller/` 与 `checks/` 留薄 CLI wrapper，带明确
  弃用周期。
- 模型：`openai_compat`、`anthropic`、`gemini` 只承诺版本化的最小非流式
  JSON 请求/回复契约。openai_compat 不是对所有 OpenAI-compatible 特性的承诺。
- 控制面：CLI 负责计划、预检、生成和验证；GitHub 模板负责可恢复的远端执行，
  不让 callback payload 成为事实来源。

Provider 的安全底线：默认只允许内置 HTTPS origin；自定义 base_url 需显式
`--allow-custom-endpoint`，记录 origin/capability digest，拒绝跨 origin
redirect，设置连接/读取超时和响应上限。HTTP 仅允许
`--allow-insecure-localhost`，receipt 必须降级网络传输保证。Provider config
位于 audit-side policy，不从被审 science tree 取值。模型请求前必须有 egress
policy；plugins 和被审文件永不与 provider key 共享进程。

## CLI 契约

| 命令 | 默认行为 | 写入/联网边界 |
|---|---|---|
| `init --local` | 生成模板和配置草案 | 无网络；拒绝覆盖非空目标 |
| `init --github --plan` | 只读 capability probe 和变更计划 | 无远端写；`--apply` 才创建仓、写 secrets 或规则 |
| `doctor` | 离线预检 Python、Git、schema、keys 是否存在、lock、状态目录 | `doctor --online` 才测试 API/GitHub，且仍不写 |
| `check` | 确定性 DCL | 不调用模型；Git blob 方式 materialize，拒绝 symlink/截断 |
| `audit --sha` | DCL 后运行模型审计，生成 report/receipt 候选 | 需 egress 已允许；失败、超时、无效回复一律非 PASS |
| `verify` | 对指定 receipt、完整 SHA、ledger commit、policy 和本机 verifier 做只读验证 | 默认无写 |
| `verify --admit` | 仅在有效、持久且独立于临时 checkout 的 controller transaction 中消费 receipt | local、editable/unlocked install、unknown gate 或无原子 state backend 直接拒绝 |
| `status` / `dispute` / `mirror` | 分别读取 cycle、提交一次受约束争议、生成可验证公开 mirror | 各自明确 `--write-ledger` 或 `--apply`；mirror 必有 redaction manifest 和可重跑命令 |

所有命令提供 versioned `--json`。稳定退出码：0 为 PASS/已验证或已消费的
良好结果；10 BLOCKED；11 ESCALATED 或 DCL_ONLY；20 配置/环境拒绝；21
receipt/integrity 拒绝；22 网络/provider 失败。不得以颜色或模糊文本表达
安全状态。

## Receipt v2 与 controller transaction

v2 是严格、版本化 JSON，不把无 version 的旧 receipt 猜作 v1；旧件只允许
`--legacy-inspect`，永不 admission。未知字段策略、路径规范化、canonical
serialization 与支持窗口写进 schema。

receipt 至少绑定：subject 的 science repo、完整 SHA、tree、审计范围；cycle
的 root/active SHA、parent receipt、round；输入的 manifest、Constitution、
DCL、prompt、provider-policy hashes；audit 的 declared provider/model、
integrity、exchange commitment 与隐私模式；ledger 的 audit repo、report
commit、cycle path、report hash；verifier 的 runtime identity、lock/install
evidence；以及 isolation evidence。

不能让 receipt 自己包含自己的 Git commit hash。正确落账顺序是：先提交
immutable report 得到 report commit P；再生成绑定 P 的 receipt 和 controller
transition，提交 receipt commit R；verifier fetches R 并校验 P 是其可验证
祖先/目标。controller 在独占锁或 compare-and-swap 下持久化 consumed receipt
hash 后，才允许写 admission check。任何仅在临时 checkout 改 state 的
`--admit` 都不算 admission。

模型原文可能含敏感研究内容。receipt 至少保存 request/response commitments、
provider request ID、时间、retention mode；policy 选择 sealed、redacted 或
no-raw。若该档位要求完整 exchange 而没有可验证保存，必须降级，而不是沉默
遗漏。

## GitHub 向导：三种诚实状态

| 状态 | 条件 | 产品文案 |
|---|---|---|
| notification-only | 无私有仓可用保护、direct push、未知规则或未通过烟测 | verdict 是通知，不是 admission |
| gated-permissive | PR gate 有效，但 status 可由任意 writer/PAT 伪造，或单管理员可绕过 | GitHub 阻断存在，管理信任仍是单点 |
| enforced-app-bound | 独立持久 controller 先原子消费 receipt；禁止 direct push 与管理员绕过；唯一 admission check 固定到已验证 GitHub App；PR head 与 merge queue 都验证；BLOCKED/PASS 实测成功 | 可称强制 admission |

GitHub App 是 check provenance，不自动替代 controller：controller 必须有
audit workflow 之外的持久、受保护且原子状态后端，例如专用 controller
repository 或经过明确威胁建模的事务性服务。science-side callback 只提供
receipt 定位信息，不可提供决定 admission 的 verdict。

0.3 不自行实现 OAuth device flow，也不手写 GitHub secret 的 Libsodium
加密。它要求已登录的 `gh`，让 `gh secret set` 写密钥；fine-grained PAT 的
人工创建只能给出深链和最小权限清单。向导必须先 plan、再在 `--apply` 获显式
确认；每次实际远端改动均写 bootstrap record。

真正的 smoke acceptance 不是打印第一份 verdict，而是：创建一个 BLOCKED PR
并证明不能 merge；在同一个 head SHA 上生成可验证 PASS receipt；只有后者能
merge。fork PR 与 secrets 的模型在 0.3 必须明确标为不支持或走单独的无
secrets 流程。

GitHub 的 branch protection 对私有仓是否可用是计划、组织策略与管理权限共同
决定的能力；doctor 应读取实际 rule/ruleset 并输出上述状态，而不是只根据
套餐文案推断。依据：GitHub protected branches 与 required checks 的官方
文档。

## 打包、插件与发布

- 当前 `pyproject.toml` 的 `packages = []` 只是环境 manifest，不能发布为
  0.1.0。迁移前将开发版本标为 prerelease，并在首次真实 wheel 通过全部 gates
  后才发行 0.1.0。
- Python 下限与源码事实一致：`requires-python >= 3.10`。
- CI 至少覆盖 source checkout、wheel、sdist 三种安装路径；在干净 venv 中
  运行 `crossaudit --help`、旧脚本 wrapper、receipt fixture 与不含研究档案
  的 artifact-content test。不得只以既有测试数量作为迁移 gate。
- 哈希安装使用带全部传递依赖 hash 的 `requirements-crossaudit.lock` 与
  `pip install --require-hashes -r ...`，不是裸
  `pip install crossaudit==X --require-hashes`。
- entry-point plugin 是任意代码执行：默认不加载；只加载 policy allowlist，
  包名/version/digest/API version 入 receipt，并在无 provider/GitHub key 的
  独立进程运行。强制 admission 不能加载未知第三方 plugin。
- PyPI Trusted Publishing 只消除长期手工 PyPI token；publish job 使用 OIDC
  短期凭据，不能证明 artifact 本身安全。build 与 publish 分离，publish 只
  下载已校验 digest 的 artifact、使用受保护 environment 与完整 commit SHA
  固定的 Actions。pending publisher 不保留项目名，发布前必须复查名称与
  owner/repo/workflow/environment。

## 路线图与不可跳过 gate

| 版本 | 交付 | 必须通过的 gate |
|---|---|---|
| 0.1.0 | src migration、CLI、doctor/check/verify、显式 state store、wrappers | wheel/sdist/source 三路径、Python matrix、无网络 import、旧路径/错误码/receipt 语义兼容 |
| 0.2.0 | providers、audit/status/dispute、receipt v2 | provider fixtures、egress/timeout/secret redaction、receipt identity/lock verification、持久化 single-use controller；audit-only 与 full-loop 区分清晰 |
| 0.3.0 | gh-based GitHub bootstrap、mirror | PR/merge-queue head-SHA gate、callback 仅定位、app-bound 或明确降级、BLOCKED/PASS 合并烟测、可恢复 bootstrap |
| 0.4.0 | check plugins 与 first-party packs | allowlist、subprocess isolation、plugin lock/digest、兼容性测试 |
| 1.0 | 稳定 schema/API | v3 实验之外，还需独立安全复核、迁移策略、真实 deployment gate 证据和支持期承诺 |

（注：合并后的路线图以 05 修正案一的表为准——0.5 增设 Generator adapter
里程碑，插件与 enforced 时点相应顺延。）

## 冻结前验收

两项边界已由修正案一裁定：0.2 为 audit-only（完整循环为 0.5 具名交付）；
enforced 档以用户自有 GitHub App + 独立持久原子 controller 为前提。
