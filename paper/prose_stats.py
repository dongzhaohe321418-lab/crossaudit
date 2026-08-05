#!/usr/bin/env python3
"""Measure the prose signals the humanization standard sets thresholds on.

The standard (improvements/06-humanization-standard.md) is only enforceable if
its numbers can be produced by a command rather than an impression. This is
that command. It reuses check_splices.prose() so both instruments read the
same text: body prose with floats, maths, citations and macros removed.

Usage: python3 prose_stats.py [--tex crossaudit.tex] [--json out.json]
"""
from __future__ import annotations
import argparse, json, re, statistics
from collections import Counter
from pathlib import Path

from check_splices import prose

# Rationed connectives and intensifiers. The threshold column lives in the
# standard; this tool just counts, so the two cannot drift apart silently.
RATIONED = ["moreover", "furthermore", "additionally", "notably", "importantly",
            "crucially", "indeed", "namely", "precisely", "not only",
            "in essence", "ultimately", "fundamentally", "essentially",
            "it is worth", "delve", "leverage", "seamless", "pivotal",
            "landscape", "underscore", "showcase", "comprehensive", "robust"]
CONTRAST = ["rather than", "instead of", ", not ", "as opposed to"]


def sentences(text: str) -> list[str]:
    # Good enough splitting for statistics; the splice checker owns parsing.
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z\(])", text)
    return [s.strip() for s in parts if len(s.split()) >= 2]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tex", default="crossaudit.tex")
    ap.add_argument("--json")
    a = ap.parse_args()

    text = re.sub(r"\s+", " ", prose(Path(a.tex)))
    low = text.lower()
    sents = sentences(text)
    lens = [len(s.split()) for s in sents]
    mean = statistics.fmean(lens)
    sd = statistics.pstdev(lens)
    openers = Counter(s.split()[0].lower().strip("\"'(") for s in sents)
    kw = len(low.split()) / 1000.0   # per-1000-word normaliser

    report = {
        "words": len(low.split()),
        "sentences": len(sents),
        "sentence_length": {
            "mean": round(mean, 1), "sd": round(sd, 1),
            "burstiness_sd_over_mean": round(sd / mean, 2),
            "short_lt8_pct": round(100 * sum(l < 8 for l in lens) / len(lens), 1),
            "long_ge35_pct": round(100 * sum(l >= 35 for l in lens) / len(lens), 1),
        },
        "top_sentence_openers": openers.most_common(8),
        "rationed_per_1000w": {w: round(low.count(w) / kw, 2)
                               for w in RATIONED if low.count(w)},
        "contrast_constructions": {w.strip(): low.count(w) for w in CONTRAST},
        "triads_x_y_and_z": len(re.findall(r"\w+, \w+,? and \w+", low)),
        "semicolons": text.count(";"),
        "note": "thresholds live in improvements/06-humanization-standard.md",
    }
    print(json.dumps(report, indent=1))
    if a.json:
        Path(a.json).write_text(json.dumps(report, indent=1) + "\n")


if __name__ == "__main__":
    main()
