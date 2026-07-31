"""Fixtures for the controller regression tests.

These tests were written after the fact (2026-07-31, finding R5 of the sixth
audit) from the current behaviour of the code. They are not the "T1-T3" that
ROADMAP-R2.md and HANDOFF.md record as locally tested: those ran only inside the
session that wrote them, were never committed, and cannot be recovered. This
suite covers the same five behaviours that ROADMAP-R2 lists, plus the escalation
lock and the reply-validator negatives, but it is new work and is named as such.

Every test runs against a *copy* of controller/ in a tmp dir, because state.py
resolves its store as `Path(__file__).parent / "state.json"`: running the real
module would write cycle state into the repository.
"""
from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

CONTROLLER = Path(__file__).resolve().parent.parent
REPO = CONTROLLER.parent


def git(*args: str, cwd: Path) -> str:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True,
                          text=True, check=True).stdout.strip()


def init_repo(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    git("init", "-q", "-b", "main", cwd=path)
    git("config", "user.email", "test@example.invalid", cwd=path)
    git("config", "user.name", "CrossAudit tests", cwd=path)


@pytest.fixture()
def controller_copy(tmp_path: Path) -> Path:
    """An isolated copy of controller/, so state.json lands in tmp."""
    dst = tmp_path / "controller"
    dst.mkdir()
    for f in CONTROLLER.glob("*.py"):
        shutil.copy(f, dst / f.name)
    return dst


@pytest.fixture()
def state(controller_copy: Path):
    """The state module of the isolated copy, imported under a unique name."""
    spec = importlib.util.spec_from_file_location(
        f"state_{controller_copy.parent.name}", controller_copy / "state.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod
