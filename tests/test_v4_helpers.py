"""Shared fixtures for the v4 statistical-contract tests."""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
V4 = REPO / "experiment" / "v4"
FIXTURE = V4 / "fixtures" / "minimal"
if str(V4) not in sys.path:
    sys.path.insert(0, str(V4))


def copy_fixture(tmp_path: Path) -> Path:
    target = tmp_path / "dataset"
    shutil.copytree(FIXTURE, target)
    return target


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row, separators=(",", ":")) + "\n" for row in rows))
