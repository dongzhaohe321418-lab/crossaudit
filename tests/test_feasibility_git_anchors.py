from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from experiment.v4.feasibility import score as score_module


def _raw_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _anchor_fixture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *,
    freeze_commit: str = "1" * 40,
    start_tip: str = "2" * 40,
    seal_commit: str = "3" * 40,
    upstream_commit: str = "4" * 40,
    remote_tip: str = "4" * 40,
    failed_ancestry: set[tuple[str, str]] | None = None,
    failed_ancestry_on_call: dict[tuple[str, str], int] | None = None,
    replacement_refs: str = "",
    shallow_repository: bool = False,
    remote_seal_history: list[str] | None = None,
    remote_seal_additions: list[str] | None = None,
) -> tuple[Path, dict[str, str]]:
    repo = tmp_path / "repo"
    run_dir = repo / "experiment/v4/feasibility/results/cohort"
    run_dir.mkdir(parents=True)
    freeze_path = repo / "experiment/v4/feasibility/FREEZE.json"
    frozen = {"design": {"n_tasks": 1}}
    freeze_doc = {"freeze_sha256": "f" * 64, "frozen": frozen}
    manifest = {
        "freeze_sha256": "f" * 64,
        "frozen_core": frozen,
        "pre_dispatch_freeze_anchor": {
            "freeze_commit": freeze_commit,
            "network_remote_tip_at_start": start_tip,
        },
    }
    freeze_path.parent.mkdir(parents=True, exist_ok=True)
    freeze_path.write_text(json.dumps(freeze_doc, sort_keys=True) + "\n")
    (run_dir / "run_manifest.json").write_text(json.dumps(manifest, sort_keys=True) + "\n")
    (run_dir / "events.jsonl").write_text("sealed journal bytes\n")
    (run_dir / score_module.SEAL_FILENAME).write_text("{}\n")
    snapshot = {
        name: _raw_sha(run_dir / name)
        for name in ("run_manifest.json", "events.jsonl", score_module.SEAL_FILENAME)
    }
    monkeypatch.setattr(score_module, "REPO_ROOT", repo)
    failed = failed_ancestry or set()
    fail_on_call = failed_ancestry_on_call or {}
    ancestry_calls: dict[tuple[str, str], int] = {}

    def proc(*, stdout: Any = "", returncode: int = 0, stderr: Any = "") -> Any:
        return SimpleNamespace(stdout=stdout, returncode=returncode, stderr=stderr)

    def fake_git(*args: str, check: bool = True) -> Any:
        if args[:2] == ("replace", "-l"):
            return proc(stdout=replacement_refs)
        if args[:2] == ("rev-parse", "--git-common-dir"):
            return proc(stdout=".git\n")
        if args[:2] == ("rev-parse", "--is-shallow-repository"):
            return proc(stdout=("true\n" if shallow_repository else "false\n"))
        if args[:2] == ("status", "--porcelain"):
            return proc(stdout="")
        if args[:3] == ("log", "-1", "--format=%H"):
            path = args[-1]
            return proc(stdout=(freeze_commit if path.endswith("FREEZE.json") else seal_commit) + "\n")
        if args[:2] == ("log", "--format=%H"):
            commits = remote_seal_history if remote_seal_history is not None else [seal_commit]
            return proc(stdout="".join(f"{commit}\n" for commit in commits))
        if args[:3] == ("log", "--diff-filter=A", "--format=%H"):
            commits = remote_seal_additions if remote_seal_additions is not None else [seal_commit]
            return proc(stdout="".join(f"{commit}\n" for commit in commits))
        if args[:2] == ("rev-parse", "--verify"):
            return proc(stdout=upstream_commit + "\n")
        if args[:3] == ("symbolic-ref", "--quiet", "--short"):
            return proc(stdout="codex/test\n")
        if args[:3] == ("config", "--get", "branch.codex/test.remote"):
            return proc(stdout="origin\n")
        if args[:3] == ("config", "--get", "branch.codex/test.merge"):
            return proc(stdout="refs/heads/codex/test\n")
        if args[:3] == ("remote", "get-url", "origin"):
            return proc(stdout="https://github.com/example/crossaudit.git\n")
        if args[:2] == ("merge-base", "--is-ancestor"):
            pair = (args[2], args[3])
            ancestry_calls[pair] = ancestry_calls.get(pair, 0) + 1
            should_fail = pair in failed and ancestry_calls[pair] >= fail_on_call.get(pair, 1)
            return proc(returncode=1 if should_fail else 0)
        if args[:2] == ("cat-file", "-e"):
            # Scientific outputs must be absent from the seal commit; commit
            # existence probes have the ^{commit} suffix.
            return proc(returncode=0 if args[2].endswith("^{commit}") else 1)
        return proc()

    def fake_subprocess_run(args: list[str], **kwargs: Any) -> Any:
        if args[:2] == ["git", "show"]:
            revision, relative = args[2].split(":", 1)
            path = repo / relative
            if revision == seal_commit and relative.endswith((
                "run_manifest.json", "events.jsonl", score_module.SEAL_FILENAME,
            )):
                return proc(stdout=path.read_bytes())
            if revision == freeze_commit and relative.endswith("FREEZE.json"):
                return proc(stdout=path.read_bytes())
            return proc(stdout=b"", returncode=1, stderr=b"missing")
        if args[:2] == ["git", "ls-remote"]:
            return proc(stdout=f"{remote_tip}\trefs/heads/codex/test\n")
        raise AssertionError(f"unexpected subprocess call: {args}")

    monkeypatch.setattr(score_module, "_git", fake_git)
    monkeypatch.setattr(score_module.subprocess, "run", fake_subprocess_run)
    return run_dir, snapshot


def test_anchor_rejects_freeze_and_seal_in_same_commit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    same = "1" * 40
    run_dir, snapshot = _anchor_fixture(
        tmp_path, monkeypatch, freeze_commit=same, seal_commit=same,
    )
    with pytest.raises(RuntimeError, match="distinct commits"):
        score_module.verify_cohort_seal_committed_and_pushed(run_dir, snapshot)


def test_anchor_rejects_local_replace_objects(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    run_dir, snapshot = _anchor_fixture(
        tmp_path, monkeypatch, replacement_refs="deadbeef\n",
    )
    with pytest.raises(RuntimeError, match="replace objects are forbidden"):
        score_module.verify_cohort_seal_committed_and_pushed(run_dir, snapshot)
    assert score_module.git_verification_env()["GIT_NO_REPLACE_OBJECTS"] == "1"


def test_anchor_rejects_shallow_history(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    run_dir, snapshot = _anchor_fixture(
        tmp_path, monkeypatch, shallow_repository=True,
    )
    with pytest.raises(RuntimeError, match="complete non-shallow Git history"):
        score_module.verify_cohort_seal_committed_and_pushed(run_dir, snapshot)


def test_anchor_requires_start_tip_strictly_before_seal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    same = "3" * 40
    run_dir, snapshot = _anchor_fixture(
        tmp_path, monkeypatch, start_tip=same, seal_commit=same,
    )
    with pytest.raises(RuntimeError, match="strictly before"):
        score_module.verify_cohort_seal_committed_and_pushed(run_dir, snapshot)


def test_anchor_rejects_seal_absent_from_advertised_remote(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    seal, remote = "3" * 40, "4" * 40
    run_dir, snapshot = _anchor_fixture(
        tmp_path, monkeypatch, seal_commit=seal, remote_tip=remote,
        failed_ancestry={(seal, remote)},
        failed_ancestry_on_call={(seal, remote): 2},
    )
    with pytest.raises(RuntimeError, match="does not contain the cohort seal"):
        score_module.verify_cohort_seal_committed_and_pushed(run_dir, snapshot)


def test_anchor_rejects_tracking_tip_divergence_from_network(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    run_dir, snapshot = _anchor_fixture(
        tmp_path, monkeypatch, upstream_commit="4" * 40, remote_tip="5" * 40,
    )
    with pytest.raises(RuntimeError, match="tracking tip differs"):
        score_module.verify_cohort_seal_committed_and_pushed(run_dir, snapshot)


def test_anchor_rejects_postseal_remote_mutation_even_after_byte_restore(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    seal, remote = "3" * 40, "4" * 40
    run_dir, snapshot = _anchor_fixture(
        tmp_path, monkeypatch, seal_commit=seal, upstream_commit=remote,
        remote_tip=remote, remote_seal_history=[remote, seal],
    )
    with pytest.raises(RuntimeError, match="advertised remote history"):
        score_module.verify_cohort_seal_committed_and_pushed(run_dir, snapshot)


def test_score_detects_snapshot_race_before_building_or_writing_analysis(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    run_dir = tmp_path / "cohort"
    run_dir.mkdir()
    for name, raw in (
        ("run_manifest.json", b"{}\n"),
        ("events.jsonl", b"original\n"),
        (score_module.SEAL_FILENAME, b"{}\n"),
    ):
        (run_dir / name).write_bytes(raw)
    initial = {
        "run_manifest.json": _raw_sha(run_dir / "run_manifest.json"),
        "events.jsonl": _raw_sha(run_dir / "events.jsonl"),
    }
    monkeypatch.setattr(
        score_module, "load_event_snapshot", lambda _: ({}, [], dict(initial)),
    )
    monkeypatch.setattr(score_module, "_validate_local_seal", lambda *a, **k: {})

    def verify_then_mutate(*_args: Any, **_kwargs: Any) -> dict[str, str]:
        (run_dir / "events.jsonl").write_bytes(b"changed after verification\n")
        return {
            "freeze_commit": "1" * 40,
            "network_remote_tip_at_start": "2" * 40,
            "seal_commit": "3" * 40,
            "network_remote_tip": "4" * 40,
        }

    monkeypatch.setattr(
        score_module, "verify_cohort_seal_committed_and_pushed", verify_then_mutate,
    )
    monkeypatch.setattr(
        score_module, "build_summary",
        lambda *_: pytest.fail("scientific endpoints built after snapshot race"),
    )
    with pytest.raises(RuntimeError, match="sealed input changed during scoring"):
        score_module.score_run(run_dir)
    assert not (run_dir / "summary.json").exists()
    assert not (run_dir / score_module.ANALYSIS_RECEIPT_FILENAME).exists()
