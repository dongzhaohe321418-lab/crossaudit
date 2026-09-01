#!/usr/bin/env python3
"""Fail-closed checks for the minimal arXiv upload source."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper"
SOURCE = PAPER / "submissions" / "arxiv2026" / "source"
EXPECTED = {
    Path("main.tex"),
    Path("figures/figure5-v4-configuration-effects.pdf"),
    Path("figures/figure6-v4-operational-tradeoffs.pdf"),
}
FORBIDDEN = re.compile(
    r"/Users/|/home/|file:|\\today|\\pdfoutput|shell-escape|"
    r"minted|write18|\\input\{|\\include\{|\\bibliography\{"
)


def collapse(text: str) -> str:
    return " ".join(text.split())


def paper_abstract(tex: str) -> str:
    match = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", tex, re.S)
    if not match:
        raise SystemExit("paper abstract not found")
    abstract = match.group(1)
    abstract = abstract.replace(r"\noindent", "")
    abstract = re.sub(r"\\textbf\{([^{}]*)\}", r"\1", abstract)
    if "\\" in abstract:
        raise SystemExit("unsupported TeX command remains in abstract metadata")
    return collapse(abstract)


def metadata_abstract(checklist: str) -> str:
    match = re.search(
        r"ASCII-normalised abstract.*?```text\n(.*?)\n```", checklist, re.S
    )
    if not match:
        raise SystemExit("arXiv metadata abstract block not found")
    abstract = collapse(match.group(1))
    try:
        abstract.encode("ascii")
    except UnicodeEncodeError as error:
        raise SystemExit("arXiv metadata abstract is not ASCII") from error
    return abstract


def main() -> None:
    canonical = (PAPER / "crossaudit.tex").read_bytes()
    bundled = (SOURCE / "main.tex").read_bytes()
    if canonical != bundled:
        raise SystemExit("arXiv main.tex differs from paper/crossaudit.tex")

    actual = {
        path.relative_to(SOURCE) for path in SOURCE.rglob("*") if path.is_file()
    }
    if actual != EXPECTED:
        raise SystemExit(
            f"arXiv source file set drifted: expected {sorted(map(str, EXPECTED))}, "
            f"found {sorted(map(str, actual))}"
        )

    tex = bundled.decode("utf-8")
    forbidden = FORBIDDEN.search(tex)
    if forbidden:
        raise SystemExit(f"forbidden arXiv source construct: {forbidden.group(0)}")

    paper_text = paper_abstract(tex)
    metadata_text = metadata_abstract((PAPER / "ARXIV.md").read_text("utf-8"))
    if paper_text != metadata_text:
        raise SystemExit("paper and arXiv metadata abstracts differ")
    if len(metadata_text) > 1920:
        raise SystemExit(
            f"arXiv metadata abstract is {len(metadata_text)} characters (limit 1920)"
        )

    print(
        "arXiv bundle preflight: PASS; "
        f"{len(actual)} source files; abstract {len(metadata_text)}/1920 characters"
    )


if __name__ == "__main__":
    main()
