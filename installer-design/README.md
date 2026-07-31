# 安装程序设计（Installer Design）— v1

Operator directive 2026-08-01: packaging/installer work lives in this
dedicated folder, isolated from the main research record so the two never
interfere; all design progress syncs through GitHub. (Folder path is ASCII
because macOS and Linux normalise non-ASCII paths differently, NFD vs NFC,
which breaks cross-platform git and CI; the Chinese name lives here in the
title.) （操作者指令：安装程序内容独立于主库存放于本文件夹；路径用 ASCII
是因 macOS/Linux 对中文路径的 Unicode 规范化不一致，跨平台 git/CI 会出错。）

## What "v1" means v1 的含义

**安装程序设计 v1** = the operative bundle below, frozen 2026-08-01:

| File | Role |
|---|---|
| [05-packaging-design.md](05-packaging-design.md) | Design history: first-freeze text + **Amendment 1** (review dispositions, the two boundary resolutions, operator product directive, merged roadmap) |
| [05a-packaging-v2.md](05a-packaging-v2.md) | The operative contract (v2 one-pager, verbatim): product tiers, seven testable constraints, CLI contract and exit codes, receipt v2 + controller transaction ordering, GitHub three-state honesty, packaging/plugin/release engineering, per-version gates |

Implementation has not started. Numbering note: "v1" names this design
bundle; inside 05, "v1/v2" name successive drafts of the design text —
different axes. （"v1"指本设计包整体；05 文内的 v1/v2 是设计文本的两稿。）

## Product north star 产品北极星（operator, 2026-08-01）

One overall audit markdown + two API keys + wizard-created repo pair = a
**stable** running loop. Sequenced honestly: 0.2 delivers audit-only (one
auditor key suffices and that is the whole truth of what runs); the wizard
(0.3) accepts both keys from day one and says which is active; the controlled
Generator adapter is a named 0.5 deliverable, and only then does the two-key
full-loop promise switch on. Stability is anchored by the persistent atomic
controller (Amendment 1, Resolution 2).

## Distribution without PyPI 无 PyPI 账号的发行方式

The operator has no PyPI account yet, so `pip install` is served from GitHub
directly — pip needs no PyPI for either of these:

```bash
# tag-pinned VCS install (primary channel for 0.x)
pip install "crossaudit @ git+https://github.com/dongzhaohe321418-lab/crossaudit@v0.1.0"
```

```bash
# release-wheel install: CI builds wheel+sdist on tag, attaches them plus
# SHA256SUMS to the GitHub Release; the lock pins URL + hash
pip install --require-hashes -r requirements-crossaudit.lock
```

- Release engineering otherwise unchanged from 05a: build and publish stay
  separate jobs; artifacts carry digests; the generated science/audit-repo
  workflow templates pin the exact version and hashes.
- **PyPI / TestPyPI deferred** until the operator creates an account (two
  separate Trusted Publisher registrations when that happens). The name
  `crossaudit` was unclaimed as of 2026-08-01; it is not reserved by anything
  and could be taken meanwhile — claim it whenever the account exists, and if
  it is lost, GitHub installs above remain the canonical channel.

## Kept-open future surfaces 保留的未来形态（operator, 2026-08-01）

A graphical **UI** and an **agent dialog box** remain on the table. Both
inherit the supervision-console iron rule from the paper's roadmap: the
front-end writes nothing of its own — every action it takes materialises as
commits through the same CLI verbs and authenticated paths, or it does not
happen. An agent dialog is a conversational front-end over `init / doctor /
audit / verify / status / dispute`, never a second, unauditable control path.
（UI 与 agent 对话框保留；铁规矩继承监督台：前端自己不写任何东西，一切
动作经由同一套 CLI 动词落为 commit，否则不发生。）
