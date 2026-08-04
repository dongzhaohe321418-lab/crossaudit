# Reference integrity audit — 2026-08-03

Every entry in `crossaudit.tex`'s bibliography, checked against its source page
this session. Recorded because a paper arguing that claims should be checkable
owes its own citations the same treatment.

Cross-check first: **20 entries defined, 20 cited, no orphans in either
direction** (no entry sits in the list uncited, no citation lacks an entry).

| # | Key | Verified against | Result |
|---|---|---|---|
| 1 | lu2024aiscientist | arXiv:2408.06292 abstract page | title and venue confirmed; author list shortened to `et al.` — the printed list repeats "C. Lu", which conflates Chris Lu and Cong Lu |
| 2 | yamada2025aisv2 | arXiv:2504.08066 | title and first three authors confirmed (Yamada, Lange, Lu); same conflation removed |
| 3 | lu2026nature | *Nature* 651:914–919 (2026) | as previously verified; author list shortened for the same reason |
| 4 | gottweis2025coscientist | arXiv:2502.18864 | confirmed; retitling noted in the entry itself |
| 5 | panickssery2024 | arXiv:2404.13076 | title and full author list confirmed verbatim (Panickssery, Bowman, Feng) |
| 6 | zheng2023 | NeurIPS 2023 | confirmed |
| 7 | norman2026reliability | arXiv:2606.19544 | title and authors confirmed; marked `(preprint)` — it is not peer-reviewed and the entry now says so |
| 8 | boiko2023 | *Nature* 624:570–578 | confirmed |
| 9 | szymanski2023 | *Nature* 624:86–91 | confirmed |
| 10 | skarlinski2024 | arXiv:2409.13740 | title and first four authors confirmed |
| 11 | baker2016 | *Nature* 533:452–454 | confirmed |
| 12 | naturenews2026 | *Nature* 651:853–854 | confirmed |
| 13 | kon2025curie | arXiv:2502.16069 | title and first three authors confirmed |
| 14 | schmidgall2025agentlab | arXiv:2501.04227 | title and first author confirmed |
| 15 | edison2025kosmos | vendor announcement | already labelled an announcement, not a paper; the text calls it a commercial platform claim |
| 16 | verga2024poll | arXiv:2404.18796 | title and full author order confirmed; fourth author added |
| 17 | nuijten2016statcheck | *Behavior Research Methods* 48:1205–1226 | confirmed |
| 18 | cabanac2022pps | arXiv:2210.04895 | title and authors confirmed via arXiv listing and Semantic Scholar |
| 19 | sharma2023sycophancy | arXiv:2310.13548 | title and first three authors confirmed |
| 20 | bai2022constitutional | arXiv:2212.08073 | confirmed |

## What was corrected

Three author lists printed "C. Lu" twice, which reads as one person cited
twice rather than as two different people (Chris Lu and Cong Lu both appear on
these papers). Truncating to `et al.` after the third name states less and
misstates nothing. One entry gained its fourth author. The 2026 preprint is
now labelled as such, since it carries an argument the paper leans on three
times and a reader should know it has not been refereed.

## What was already right

No fabricated entry, no invented venue, no citation without a bibliography
entry, and no entry in the list that the text never uses. Two non-paper
sources (a vendor announcement, a consortium website) are cited in footnotes
and described as what they are rather than dressed as literature.


## A note on the abstract

The abstract carries no citation markers, which is the convention: an abstract
is indexed and read on its own, where a bracketed number resolves to nothing.
Both abstracts we checked as style references (Lu et al. 2024, Panickssery et
al. 2024) cite nothing either, and the arXiv abstract field is plain text, so a
marker there would print literally.

The convention has a condition attached, and checking it found a real defect.
An uncited abstract may state established findings as background, but it may
not state the authors' own conjecture as though it were established. Ours did:
it said models trained together *tend to* share blind spots, while §1 and §2
say they *may*, and call the generalisation a hypothesis. The abstract now
separates the two. Self-preference is reported as the demonstrated finding it
is; shared blind spots are named as a conjecture, with the consequence stated
conditionally.
