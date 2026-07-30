#!/usr/bin/env python3
"""Level-B mirror redaction (mechanical, reproducible against the PRIVATE originals).

Rules: (1) 40/64-hex digests truncated to 12 chars + ellipsis; (2) all floating-point
numbers (incl. scientific notation) -> <#>; integers, rule/check IDs, dates, paths,
severities kept verbatim. NOTE: manifest hashes therefore refer to the private
originals and are then truncated — the mirror is a structural transparency preview,
NOT a hash-verifiable ledger (see ledger-mirror/REDACTION.md).

Usage: python3 tools/redact_mirror.py <src_cycle_dir> <dst_cycle_dir>
"""
import re
import sys
from pathlib import Path

def redact(text: str) -> str:
    text = re.sub(r'\b[0-9a-f]{40}\b', lambda m: m.group(0)[:12] + '…', text)
    text = re.sub(r'\b[0-9a-f]{64}\b', lambda m: m.group(0)[:12] + '…', text)
    text = re.sub(r'(?<![\w.⟩])-?\d+\.\d+(?:[eE][+-]?\d+)?(?!\d)', '⟨#⟩', text)
    return text

def main(src: str, dst: str) -> None:
    s, d = Path(src), Path(dst)
    d.mkdir(parents=True, exist_ok=True)
    for p in sorted(s.iterdir()):
        if p.is_file():
            (d / p.name).write_text(redact(p.read_text()))
            print("redacted", p.name)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
