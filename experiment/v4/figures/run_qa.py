#!/usr/bin/env python3
"""Run the nature-figure static and rendered QA gates for both v4 figures."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
FIGURE_DIR = REPO_ROOT / "paper/figures"
QA_DIR = SCRIPT_DIR / "qa"
STEMS = (
    "figure5-v4-configuration-effects",
    "figure6-v4-operational-tradeoffs",
)


def find_skill_root() -> Path:
    configured = os.environ.get("NATURE_FIGURE_SKILL_ROOT")
    candidates = [Path(configured).expanduser()] if configured else []
    candidates.append(Path.home() / ".codex/skills/nature-figure")
    for candidate in candidates:
        if (candidate / "scripts/validate_figure.py").is_file():
            return candidate
    raise RuntimeError(
        "nature-figure is required for QA; install it or set NATURE_FIGURE_SKILL_ROOT"
    )


def run_json(command: list[str], destination: Path) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"QA command failed ({completed.returncode}): {' '.join(command)}\n"
            f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        )
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"QA command did not return JSON: {' '.join(command)}") from exc
    destination.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return payload


def main() -> int:
    skill_root = find_skill_root()
    scripts = skill_root / "scripts"
    QA_DIR.mkdir(parents=True, exist_ok=True)

    source_report = run_json(
        [
            sys.executable,
            str(scripts / "validate_figure.py"),
            str(SCRIPT_DIR / "plot_feasibility.py"),
            "--backend",
            "python",
            "--strict",
            "--json",
        ],
        QA_DIR / "plot_feasibility.source.json",
    )
    if not source_report["summary"]["ready"]:
        raise RuntimeError("source preflight was not ready")

    summary: dict[str, Any] = {
        "source_preflight": "PASS",
        "minimum_font_pt_required": 5.0,
        "alignment_tolerance_pt": 1.5,
        "figures": {},
    }
    for stem in STEMS:
        pdf_path = FIGURE_DIR / f"{stem}.pdf"
        text_report = run_json(
            [
                sys.executable,
                str(scripts / "audit_pdf_text.py"),
                str(pdf_path),
                "--min-pt",
                "5",
                "--json",
            ],
            QA_DIR / f"{stem}.pdf-text.json",
        )
        collision_report = run_json(
            [
                sys.executable,
                str(scripts / "audit_figure_collisions.py"),
                str(pdf_path),
                "--strict",
                "--json",
            ],
            QA_DIR / f"{stem}.collisions.json",
        )
        alignment_report = json.loads(
            (QA_DIR / f"{stem}.alignment.json").read_text(encoding="utf-8")
        )
        if alignment_report["verdict"] != "PASS":
            raise RuntimeError(f"alignment gate did not pass for {stem}")
        summary["figures"][stem] = {
            "alignment": alignment_report["verdict"],
            "alignment_fail": alignment_report["summary"]["fail"],
            "alignment_warn": alignment_report["summary"]["warn"],
            "minimum_font_pt": text_report["minimum_found_pt"],
            "fonts_below_5_pt": text_report["below_minimum_count"],
            "collision_verdict": collision_report["verdict"],
            "collision_fail": collision_report["summary"]["fail"],
            "collision_warn": collision_report["summary"]["warn"],
        }

    (QA_DIR / "qa-summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
