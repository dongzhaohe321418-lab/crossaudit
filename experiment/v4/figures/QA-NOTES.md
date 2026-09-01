# Figure QA notes

Inspection date: 2026-09-01. The plotted values were regenerated from the sealed
Amendment 2 summary, then checked at the 183 mm target width and again inside the
compiled paper at `\linewidth`.

## Automated gates

- The Python source preflight passed all 21 checks with zero warnings or failures.
- Both figures passed the 1.5 pt panel-alignment gate with zero warnings or failures.
- Both rendered PDFs passed the strict collision audit with zero warnings or
  failures.
- The minimum detected text size was 6.0 pt in each figure; no text was below the
  required 5.0 pt floor.
- Exact machine-readable reports, including alignment overlays, are committed in
  `qa/`; `qa/qa-summary.json` is the aggregate record.

## Human panel audit

### Figure 5

- Panel a: all four heat-map values and row/column labels are legible; no color is
  required to recover a value.
- Panel b: point estimates, descriptive intervals, zero reference, and the
  improvement-positive false-block sign convention are visible without overlap.
- Panel c: D2-minus-D0 and D2-minus-D1 remain visually distinct; the adverse
  D2-minus-D1 result is not suppressed.
- Panel d: natural and controlled strata are separated, and the D1 100% line is
  labelled as a checker-defined ceiling rather than an independent benchmark.
- The Constitution contrast is absent by design because its frozen scorer uses
  repeat 0 while the registration specifies a three-repeat C2 collapse.

### Figure 6

- Panel a: initial and final rates are distinguishable, including the null P0/P1
  changes and the 2/9 P2 repairs with 0/3 regressions.
- Panel b: calls, cost, and provider-time ratios share a P0=1 reference without
  implying that the three resources are interchangeable.
- Panel c: same and cross points remain separately visible despite identical
  observed endpoint rates; the display does not imply equivalence.
- Panel d: E1 and E2 ties on accept/tamper accuracy and the adverse E2
  first-round-reconstruction result are all retained.

## Paper-level inspection

The complete 24-page PDF was rendered to images and inspected as a contact sheet.
Figure 5 on page 16 and Figure 6 on page 18 were also inspected at full rendered
resolution. Neither figure is clipped; captions are complete; panel order matches
the captions; and the float barrier keeps both evidence figures before the threat
model. These checks assess presentation, not the validity of the underlying proxy
labels or the confirmatory status of the cohort.
