#!/usr/bin/env python3
"""Run the CrossAudit v4 results-independent confirmatory freeze preflight."""
from __future__ import annotations

import argparse
import json
import sys

from schema import DataValidationError
from validate_dataset import validate_freeze_configuration


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("freeze_root", help="v4 directory or repository root")
    args = parser.parse_args()
    try:
        report = validate_freeze_configuration(args.freeze_root)
    except DataValidationError as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
