# 06 — Humanization 标准(去 AI 化写作规范)/ The Humanization Standard

**Status.** 2026-08-05 起适用于本仓库全部对外文本(论文、README、微信稿、
workshop 版)。可测项由 `paper/prose_stats.py` 与 `paper/check_splices.py`
产出数字;凡有阈值之处,以命令输出为准,不以印象为准。
An English summary for English-only agents is at the end.

---

## 0. 三条原则(其余一切由此推出)

**原则一:目标是读者,不是检测器。** 任何 AI 检测器给出的都是概率猜测,
没有一个可靠;为检测器分数而改写是在优化一个噪声指标。本标准优化的是
真实读者的两种体验:句式重复带来的疲劳感,和"这话谁写都行"带来的不信任感。

**原则二:三层递进,内容层最重。**
词汇层(连接词、强调词)最容易修也最浅;
句法层(节奏、结构复现)其次;
**内容层(具体性、取舍、失败的痕迹)才是人类写作的不可伪造签名。**
一篇词汇干净、句式多变、但每句话"谁都能写"的文章,仍然是 AI 味的。

**原则三:humanize 绝不改变主张强度。** 每次改写后,句子的 claim 必须
与改写前逐条等价——不得顺手加强,不得顺手弱化。本项目两次引用失实
都发生在"顺手"里。改写过事实门,和新写一样。

---

## 1. 词汇层:配额表(可 grep 断言)

单位:每 1000 词。测量:`python3 prose_stats.py`。

| 类别 | 词/短语 | 配额 | 超配处理 |
|---|---|---|---|
| 公式化连接词 | moreover, furthermore, additionally, notably, importantly, crucially, indeed | **0** | 删除或换普通句间衔接 |
| 空强调 | precisely, essentially, fundamentally, ultimately, in essence, it is worth noting | **0**(技术义除外,如 "exactly two severities") | 删除;强调靠证据不靠副词 |
| 营销词 | delve, leverage, seamless, pivotal, robust, comprehensive, landscape, underscore, highlight, showcase | **0** | 换具体动词/名词 |
| 对比句式 | rather than / instead of / ", not " 合计 | **≤2.5/1000 词**,且任一单种 ≤1.5 | 混用三种以上表达;部分改为正面陈述 |
| "not only … but also" | | **0** | 拆成两句或删 "only" |
| 三联列表 "x, y, and z" | | **≤3/1000 词** | 改二联或四联,或拆句 |

**冻结项(CI 断言,修改需注明日期的修订案):**
` --- ` 计数 = 9(论文);British spelling;不新增警句(aphorism)。
em-dash 节奏(" — "插入语)是最强的 AI 签名之一,本仓库全面停用,
以逗号、冒号、括号、分号替代。

---

## 2. 句法层:分布指标

测量:`prose_stats.py`。目标值针对学术散文;微信稿短句比例应更高。

| 指标 | 目标 | 本论文实测(2026-08-05) |
|---|---|---|
| 句长均值(词) | 15–24 | 26.1(偏长,已知债务) |
| 爆发度 SD/mean | **≥0.45**(越高越像人) | 0.64 ✓ |
| 短句(<8 词)占比 | ≥8% | 10.4% ✓ |
| 长句(≥35 词)占比 | ≤20% | 28.2%(超标,合并时压) |
| 句首词最高频占比 | "The/A/It/This" 合计 ≤45% | ~44% ✓(临界) |
| 连续段落同词开头 | ≤2 段 | 人工抽查 |
| 逗号拼接 | `check_splices.py` 候选逐条人工裁决 | 工具召回 7/8、误报 1/12,零报告≠零问题 |

**节奏的操作定义**:任何一种句式结构(对比、三联、"X: Y" 冒号句、
分词尾挂 ", making/showing/highlighting …")都不得连续出现两句,
也不得独自承担全文某一功能——"rather than 34 处"的教训是:
**一种句式扛起全文所有对比,读者第 10 次见到它时就出戏了。**

**分词尾挂**(", making it clear that…" / ", highlighting the need for…")
配额为 **0**:这是 AI 最高频的因果偷懒,一律改为独立句并写明主语。

---

## 3. 修辞层:禁用模式清单

1. **警句冻结**:不新增 "X is not Y. It is Z." 式格言。已有警句
   (如首句)是遗产,不扩编。通用场景配额 ≤1/节。
2. **自我总结句**:段末"In sum / In short / Taken together / 换言之"
   一律删——段落写清楚了就不需要,写不清楚总结也救不了。
3. **对仗强迫症**:AI 爱把每个论点写成对称双联("does X, not Y;
   enables A, not B")。连续对称 ≥2 次即拆一次。
4. **修辞疑问句**:配额 0(论文);微信稿 ≤1/节。
5. **hedging 堆叠**:"could potentially"、"may possibly" → 只留一个
   限定词,且限定词必须可辩护(见原则三)。
6. **列表化倾向**:能用散文承载的不用 bullet;bullet 只给真并列。
7. **elegant variation 禁令(反向规则)**:科技写作中术语必须重复,
   不许为"避免重复"换词——increment 就是 increment,不许一会儿
   step 一会儿 unit。变化留给句法,精确留给术语。

---

## 4. 内容层:人类签名(最重要,不可工具化)

**4.1 具体性测试。** 对每个强调句问:"只有掌握这份数据/做过这个决定
的作者才写得出这句吗?"写得出→保留;谁都写得出→删或加证据。
"The results are striking" 谁都能写;"the two increments it called
contradictory are the two where its own arithmetic was worst" 只有
做过这次核对的人能写。**后者才是 humanize。**

**4.2 取舍入文。** 人类作者的痕迹是被放弃的选项:为什么是方案一
不是方案二、这个修法买到了什么又付出了什么。每个重要设计决定
至少写一次"我们没有选什么,以及代价"。

**4.3 失败的痕迹。** 修正过的错误留在文中(带日期与出处),不抹平。
本仓库的实践:审计记录、撤回声明、"the uncomfortable part"。
一篇从不出错的稿子读起来最像机器。

**4.4 数字必须带出处。** 任何统计量:值 + 定义 + n + 来源文件。
"floor-corrected agreement, (observed−floor)/(43−floor)" 是合格写法;
裸的 "0.81" 不是。

**4.5 第一人称承担。** 判断句用 "we chose / we do not claim /
this is the operator's decision",不用无主语被动("it was decided")。
责任有名字,是人写作的核心特征。

---

## 5. 反标准:五个不要

1. **不要伪装人类**:不注入错别字、口语、语气词。目标是好的书面语,
   不是表演随意。
2. **不要为变而变**:变化服务于可读性;牺牲精确性的变化一律回退。
3. **不要动 claim**(原则三的重申,值得写两遍)。
4. **不要追检测器分数**:任何"AI 率降到 x%"的说法都不进文档、
   不进承诺。可承诺的只有本标准的可测项。
5. **不要一次性大改**:每轮 ≤30 处编辑,改后全量重跑门禁
   (build、页数、破折号计数、splice、prose_stats),再改下一轮。
   本项目 48 小时内三个自引缺陷全部来自大批量改写。

---

## 6. 流程:测 → 改 → 再测

```bash
cd paper
python3 prose_stats.py                 # 分布与配额
python3 check_splices.py               # 逗号拼接候选(人工裁决)
python3 check_splices.py --selftest    # 先确认仪器本身在标定内
grep -c ' --- ' crossaudit.tex         # 必须 = 9
pdflatex -interaction=nonstopmode crossaudit.tex  # ×2,0 错误
```

改写批次提交时,commit message 写明:改了哪类、多少处、
哪些指标从多少到多少。数字不可复算的 humanize 不算完成。

---

## 7. 本项目校准数据(为什么这些阈值)

2026-08-05 去 AI 化批次实测(28 处编辑):moreover/additionally/
indeed/namely/precisely 5→0、"exactly" 9→4(存留全为技术义)、
"not only" 2→0、"rather than" 34→21(12 处改 ", not"/"instead of")。
§4.3 改写(2026-08-03):句长均值 31.6→15.9,≥35 词占比 42%→5%,
<8 词占比 →42%。逗号拼接:全文候选 13,人工裁决后真阳性 1。
这些是阈值的经验来源:阈值定在"改完之后仍自然"的水平,
不定在理论最优。

---

## English summary (for English-only agents)

Three principles: write for readers, not detectors (detector scores are
noise; never optimise them); three layers with content dominant (lexicon <
syntax < content — specificity, disclosed trade-offs, and visible corrections
are the unfakeable human signature); **rewrites never change claim strength**
(every edit passes the same fact gate as new text).

Hard quotas per 1000 words, measured by `paper/prose_stats.py`: formulaic
connectives (moreover, furthermore, notably, indeed, …) and empty
intensifiers (precisely, essentially, ultimately, …) at zero; marketing verbs
(delve, leverage, robust, seamless, …) at zero; contrast constructions
(rather than / instead of / ", not") ≤2.5 combined with no single form >1.5;
"not only" at zero; x-y-and-z triads ≤3. Frozen: ` --- ` count stays 9 in the
paper (CI-asserted), British spelling, no new aphorisms, no em-dash
interruptions anywhere, participial tails (", making it…") at zero.

Distribution targets: sentence-length SD/mean ≥0.45; short (<8w) ≥8%; long
(≥35w) ≤20%; no sentence pattern twice in a row; no single construction
carrying one rhetorical function for a whole document. Technical terms must
repeat — elegant variation is banned in scientific prose; variety lives in
syntax, never in terminology.

Content layer: every emphatic sentence must pass the specificity test
("could only this author, holding this data, have written it?"); state
rejected alternatives and their costs; leave dated corrections visible;
every statistic ships value + definition + n + source file; judgements in
first person with an owner.

Process: measure, edit ≤30 sites, re-run all gates (build, page count, dash
count, splice scan, prose stats), commit with before/after numbers. A
humanization pass whose numbers cannot be recomputed did not happen.
