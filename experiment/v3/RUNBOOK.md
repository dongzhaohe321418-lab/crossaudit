# v3 消融实验操作手册（RUNBOOK）

给操作者（你）的逐步指南。协议与冻结规则见 `../v3-ABLATION-REGISTRATION.md`
（含 AMENDMENT 1 的隔离梯度）；本手册只讲怎么跑。标注【代码待生成】的脚本
由 Claude 按本手册生成后入库；已存在的脚本直接给路径。

---

## 0. 你在测什么（30 秒版）

- **Q1 独立性梯度**：L0 无审计 → L1 同会话自省 → L2 同模型+transcript →
  L3 同模型裸审 → L4 同模型+宪法 → L4b 同厂异模型 → L5 异厂。
  主分析：梯度趋势（Cochran's Q + 相邻档 McNemar）。
- **Q2 通道分解**：A1 通用脚本 / A2 科学工具 / LLM+宪法，各自边际贡献。
- **Part B 真实账本**：你的 7 个真实周期做精确率与生态效度（12 条已确认发现
  是天然标签，已挖掘完成，无需重跑）。

预算参考：约 420 次 LLM 调用（temperature 0），数十美元级；
你本人的时间投入集中在两处 —— 配钥匙（半小时）与盲评（1–2 小时）。

---

## 1. 阶段 0 —— 前置条件（阻塞项，先做）

- [ ] **撤销旧密钥**（必须）：之前暴露过的 OpenAI key 与 GitHub PAT 全部 revoke。
- [ ] **新钥匙 ×3**：OpenAI（gpt-5 系）、Anthropic（claude 系）各一把；
      若跑 L4b，同厂第二个模型无需新钥匙，只是配置项。
- [ ] **钥匙托管（v2 规则）**：钥匙只进 GitHub Actions Secrets 或本地
      `~/.crossaudit-keys.env`（已在 .gitignore），**永不入 repo**。
- [ ] **密封的第三方托管**（上次的失败点）：缺陷密钥生成后，
      `sha256(key file)` 公开发在 registration 的 amendment 里，
      **key 文件本体**放一个你无写权限的地方（选一）：
      (a) 合作者私仓；(b) OSF registration；(c) 加密 zip 发给 Yuhao，密码开箱时公布。
- [ ] 环境：`python3 -m pip install pyyaml numpy scipy --break-system-packages`；
      克隆三个 repo（crossaudit、两个 perovskite，后两个只读）。

## 2. 阶段 1 —— 语料生成（Part A）

目标：~60 增量 / ~100 缺陷，每个缺陷预打"最便宜捕获通道"标签
（script / domain-tool / LLM-only），含可工具核验工件（伪 SCF log、
自相矛盾 CIF、量纲错误表）。

1. 【代码待生成】`v3/generate_corpus_v3.py`
   —— 在 v1 `generate_corpus.py` 基础上加：通道标签、工具核验工件、
   厂商各写一半干净增量（先由两家模型各生成 30 个干净增量，
   再由确定性 mutator 注入缺陷；mutation 日志即缺陷密钥）。
2. 生成后**立刻**执行密封（阶段 0 的第三方托管），再做任何别的事。
3. Sanity：`python3 checks/run_checks.py` 对 D 类缺陷应 100% 命中，
   干净增量 0 误报；不满足则修 mutator（此时还没跑模型臂，允许改）。
4. L1/L2 需要"生成会话"：干净增量由模型会话产出时，
   保存会话（L1 直接在该会话续问自审），并让模型另写 transcript
   风格说明书（L2 用）。【代码待生成】`v3/gen_sessions.py`。

## 3. 阶段 2 —— 跑臂（顺序固定，跑完前不看结果）

先跑不花钱的：
- [ ] A0 桩（constant-BLOCK）与 L0（无审计）——纯记账，脚本直接产结果。
- [ ] A1 = `checks/run_checks.py` 全语料。
- [ ] A2 =【代码待生成】`v3/tool_checks.py`（cclib/ASE 风格解析回检）。

再跑 LLM 梯度（每臂一遍、temperature 0、逐增量 fail-fast，
输出两阶段提交进 `v3/results/<arm>/`，含 provenance digest —— 复用
`run_arm.py` 骨架，【代码待生成】梯度配置）：
- [ ] L1（同会话自省）→ L2（transcript）→ L3（裸审）→ L4（+宪法）
      → L4b（同厂异模型）→ L5（异厂+宪法）。
- **纪律**：任何臂的输出在全部臂完成前不打开看（防止无意识调参）；
  中断恢复：重跑该臂脚本会跳过已有增量结果续跑。

## 4. 阶段 3 —— Part B 重审臂（真实数据）

对 7 个钉死 SHA（见 `real-ledger/cycles.jsonl`）各跑：
- [ ] B4 同厂裸审；B5 同厂+你部署自己的审计指令
      （`pv-science/EXPERIMENT_AUDIT.md`）；B6 异厂复测。
【代码待生成】`v3/run_partB.py`（只读 checkout 各 SHA，产出同格式结果）。
历史 codex 报告本身就是天然 L5 臂，不用重跑。

## 5. 阶段 4 —— 你的盲评（唯一需要你判断的环节）

1. 【代码待生成】`v3/build_blind_sheet.py`：把 Part B 各臂新发现去重、
   打乱、去臂名，生成 `adjudication/BLIND-SHEET.md`（每条：证据路径+主张，
   无来源标识）。
2. 你逐条填 `valid / invalid / unclear`（只判科学与事实，不猜来源）。
3. 同表附 12 条已确认发现的**可机械化草评**（脚本能否抓住），
   你逐条确认 —— 这个数字就是论文里"你本该写的 DCL 有多大"。
4. 填完提交，脚本才揭盲并计分。

## 6. 阶段 5 —— 评分与分析（全自动）

- 【代码待生成】`v3/score_v3.py`：按注册的冻结映射逐缺陷计
  catch 矩阵 → Cochran's Q 趋势 + 相邻档 McNemar（Holm）；
  干净增量误拦率（梯度同表）；通道边际；每档 cost（调用数、美元、
  每误拦换多少捕获，L0 为锚）。
- 置换底线：复用 `experiment/score_nullcheck.py`。
- 产出三件套：`RESULTS-ladder.md`（剂量响应表+图）、
  `RESULTS-channels.md`、`RESULTS-partB.md`。
  梯度图（x=隔离档，y=catch 率与误拦率双线）就是 workshop 版主图。

## 7. 阶段 6 —— 写回论文

- Molecular 5 页版：§4 直接换成梯度图+通道表（这正是该 CFP 要的
  rigorous evaluation）。主论文 §4.3 的"测分歧不测判别力"告诫升级为
  "v3 已测判别力"。Part B 反事实一句话进 §4.2：
  "没有这条环，12 条已确认缺陷将无阻碍下行"。

## 8. 红线（违反任何一条，结果作废）

1. 输出存在后，评分映射与标签规则**不可再改**（改 = 出 AMENDMENT 且旧分照报）。
2. 全臂完成前不看任何臂输出。
3. 密钥不入 repo；缺陷密钥先密封后跑臂。
4. perovskite 两仓只读；科学判断只在你的盲评里发生。
5. 语料、prompt、模型名、温度全部入库；每臂记 provenance digest。

## 9. 故障速查

- 某臂中途 API 挂：重跑同命令，续跑不重算；连续失败 3 次 → 记 FAILED，
  该增量按 missing 处理（进 registration 的 deviations 表），不许手补。
- 限流：臂内串行即可（60 增量不值得并发）。
- 模型拒答/格式坏：validator 记 invalid-reply，按 ESCALATE 计，不重试改写。

## 9b. 现状（2026-08-04）

不需要密钥的部分**全部建好并跑通**，清单见 `READY.md`：语料生成器、工具通道、
梯度 runner、冻结评分器、密封工具、CI 工作流。评分器已用三个已知质量的合成臂
干跑验证，能复现内置的强弱顺序。

**执行路径改了一处**：实验臂**在 GitHub Actions 里跑**，不在助手的沙箱里 ——
密钥进 repository secrets，模型 ID 进 repository variables（模型 ID 不是秘密，
公开钉住它是溯源的一部分）。理由见 `KEY-HANDLING.md`：这些臂产出的是注册研究的
证据，跑在哪里本身就是记录的一部分；CI 留下带时间戳、runner 身份、commit 与
解析后模型 ID 的日志，沙箱只留下助手的说法。

红线不再靠记忆：工作流的 dispatch 表单要求填入已提交 SEAL 的摘要，对不上就拒跑。

## 10. 一页总检查单

阶段 0 钥匙+托管 → 阶段 1 语料+密封+sanity → 阶段 2 A0/A1/A2 → L1..L5 →
阶段 3 B4/B5/B6 → 阶段 4 你盲评+确认可机械化 → 阶段 5 自动评分 →
阶段 6 写回论文。你亲手做的只有：钥匙、密封选项、盲评。
其余每一步说"开工"我就生成对应脚本并跑通示例。
