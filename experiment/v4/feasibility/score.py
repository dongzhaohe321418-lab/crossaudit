#!/usr/bin/env python3
"""Score one v4 execution-feasibility journal without confirmatory claims.

Repeated calls, artefact variants and the two pinned configurations are first
collapsed inside task.  Intervals resample tasks, never individual findings or
model calls.  With at most six convenience tasks the output is diagnostic and
descriptive; it must not be presented as evidence for a population of vendors.
"""
from __future__ import annotations

import argparse
import errno
import fcntl
import hashlib
import itertools
import json
import math
import os
import random
import re
import statistics
import subprocess
import tempfile
from contextlib import contextmanager
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import NormalDist
from typing import Any, Callable, Iterable

try:
    from .estimands import fixed_weight_2x2, natural_available_gold_2x2
    from .providers import git_verification_env, network_git_remote_allowed
    from .structure import validate_structure
except ImportError:  # pragma: no cover - documented direct-script execution
    from estimands import fixed_weight_2x2, natural_available_gold_2x2
    from providers import git_verification_env, network_git_remote_allowed
    from structure import validate_structure


USAGE_TOKEN_FIELDS = (
    "input_tokens", "output_tokens", "cached_input_tokens",
    "cache_creation_input_tokens", "cache_write_input_tokens",
    "reasoning_tokens",
)
LEDGER_DECISION_TIME_CAP_SECONDS = 300.0
LEDGER_ATTACKS = (
    "none", "stale_receipt", "wrong_commit", "changed_constitution",
    "missing_round", "altered_report", "unsupported_identity",
)
REPO_ROOT = Path(__file__).resolve().parents[3]
REQUIRED_FROZEN_CODE_PATHS = frozenset({
    "experiment/v4/feasibility/tasks.py",
    "experiment/v4/feasibility/providers.py",
    "experiment/v4/feasibility/run.py",
    "experiment/v4/feasibility/score.py",
    "experiment/v4/feasibility/schema.py",
    "experiment/v4/feasibility/runtime.py",
    "experiment/v4/feasibility/structure.py",
    "experiment/v4/feasibility/semantics.py",
    "experiment/v4/feasibility/estimands.py",
    "experiment/v4/feasibility/canary.py",
})
SEAL_FILENAME = "COHORT-SEAL.json"
ANALYSIS_RECEIPT_FILENAME = "ANALYSIS-RECEIPT.json"
SEAL_FORMAT_VERSION = "v4-feasibility-outcome-free-seal-1"
SEAL_FIELDS = frozenset({
    "format_version", "created_utc", "freeze_sha256",
    "manifest_bytes_sha256", "journal_bytes_sha256", "final_event_sha256",
    "event_count", "scheduled_call_count", "completed_call_count",
    "structural_semantic_integrity_valid", "summary_absent_at_creation",
    "claim_boundary", "next_required_step", "seal_sha256",
})
ANALYSIS_RECEIPT_FIELDS = frozenset({
    "format_version", "created_utc", "freeze_sha256",
    "cohort_seal_bytes_sha256", "summary_bytes_sha256",
    "pre_analysis_freeze_commit", "pre_dispatch_network_tip",
    "pre_analysis_seal_commit",
    "network_remote_tip_at_analysis", "schedule_finished",
    "scientific_outputs_withheld", "claim_boundary", "note", "receipt_sha256",
})


def _digest(value: Any) -> str:
    raw = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    ).encode()
    return hashlib.sha256(raw).hexdigest()


def _validate_manifest_and_live_code(manifest: dict[str, Any]) -> dict[str, Any]:
    """Refuse to score with a manifest header or scorer dependency that drifted."""
    if not isinstance(manifest, dict):
        raise ValueError("run_manifest.json must contain an object")
    if set(manifest) != {
        "format_version", "freeze_sha256", "claim_status", "journal",
        "frozen_core", "pre_dispatch_freeze_anchor",
    }:
        raise ValueError("run manifest has unexpected or missing fields")
    frozen = manifest.get("frozen_core")
    if not isinstance(frozen, dict) or _digest(frozen) != manifest.get("freeze_sha256"):
        raise ValueError("run manifest frozen_core does not match freeze_sha256")
    expected_header = {
        "format_version": frozen.get("format_version"),
        "claim_status": frozen.get("claim_status"),
        "journal": "events.jsonl",
    }
    for field, expected in expected_header.items():
        if manifest.get(field) != expected:
            raise ValueError(f"run manifest {field} differs from the frozen core")
    anchor = manifest.get("pre_dispatch_freeze_anchor")
    if not isinstance(anchor, dict) or set(anchor) != {
        "freeze_commit", "network_remote_tip_at_start",
    } or any(
        not isinstance(anchor.get(field), str)
        or not re.fullmatch(r"[0-9a-fA-F]{40,64}", anchor[field])
        for field in ("freeze_commit", "network_remote_tip_at_start")
    ):
        raise ValueError("run manifest lacks a valid pre-dispatch freeze anchor")
    code_hashes = frozen.get("code_hashes")
    if not isinstance(code_hashes, dict) or not REQUIRED_FROZEN_CODE_PATHS.issubset(code_hashes):
        raise ValueError("frozen core lacks required scoring dependency hashes")
    for relative in sorted(REQUIRED_FROZEN_CODE_PATHS):
        path = (REPO_ROOT / relative).resolve()
        try:
            path.relative_to(REPO_ROOT)
        except ValueError as exc:  # pragma: no cover - constants are source controlled
            raise ValueError(f"unsafe frozen code path: {relative}") from exc
        if not path.is_file():
            raise ValueError(f"frozen scoring dependency is missing: {relative}")
        observed = hashlib.sha256(path.read_bytes()).hexdigest()
        if code_hashes.get(relative) != observed:
            raise ValueError(f"live scoring dependency differs from freeze: {relative}")
    return frozen


def _mean(values: Iterable[float]) -> float | None:
    xs = [float(x) for x in values]
    return statistics.fmean(xs) if xs else None


def _quantile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    xs = sorted(values)
    if len(xs) == 1:
        return xs[0]
    pos = (len(xs) - 1) * q
    lo, hi = math.floor(pos), math.ceil(pos)
    if lo == hi:
        return xs[lo]
    return xs[lo] * (hi - pos) + xs[hi] * (pos - lo)


def _descriptive(values: Iterable[float]) -> dict[str, Any]:
    xs = [float(x) for x in values]
    if not xs:
        return {"n": 0, "mean": None, "median": None, "minimum": None, "maximum": None}
    return {
        "n": len(xs), "mean": statistics.fmean(xs), "median": statistics.median(xs),
        "minimum": min(xs), "maximum": max(xs),
    }


def task_cluster_estimate(task_values: dict[str, float], *, seed: int = 2608,
                          draws: int = 5000) -> dict[str, Any]:
    """Describe one pre-collapsed value per task with a task bootstrap."""
    ids = sorted(task_values)
    xs = [float(task_values[x]) for x in ids]
    if not xs:
        return {"n_tasks": 0, "estimate": None, "se": None,
                "ci95_normal": None, "ci95_task_bootstrap": None,
                "task_values": {}}
    estimate = statistics.fmean(xs)
    se = statistics.stdev(xs) / math.sqrt(len(xs)) if len(xs) > 1 else None
    normal = None
    if se is not None:
        z = NormalDist().inv_cdf(0.975)
        normal = [estimate - z * se, estimate + z * se]
    bootstrap = None
    if draws and len(xs) > 1:
        rng = random.Random(seed)
        samples = [
            statistics.fmean(xs[rng.randrange(len(xs))] for _ in xs)
            for _ in range(draws)
        ]
        bootstrap = [_quantile(samples, 0.025), _quantile(samples, 0.975)]
    return {
        "n_tasks": len(xs), "estimate": estimate, "se": se,
        "ci95_normal": normal, "ci95_task_bootstrap": bootstrap,
        "task_values": dict(sorted(task_values.items())),
        "warning": "descriptive feasibility interval; <=6 convenience tasks" if len(xs) <= 6 else None,
    }


def task_cluster_ratio(task_counts: dict[str, tuple[float, float]], *, seed: int,
                       draws: int = 5000) -> dict[str, Any]:
    usable = {k: (float(v[0]), float(v[1])) for k, v in task_counts.items() if v[1] >= 0}
    numerator = sum(v[0] for v in usable.values())
    denominator = sum(v[1] for v in usable.values())
    estimate = numerator / denominator if denominator else None
    interval = None
    if draws and len(usable) > 1 and denominator:
        ids = sorted(usable)
        rng = random.Random(seed)
        boot = []
        for _ in range(draws):
            picks = [ids[rng.randrange(len(ids))] for _ in ids]
            den = sum(usable[x][1] for x in picks)
            if den:
                boot.append(sum(usable[x][0] for x in picks) / den)
        interval = [_quantile(boot, 0.025), _quantile(boot, 0.975)] if boot else None
    return {
        "n_tasks": len(usable), "numerator": numerator, "denominator": denominator,
        "estimate": estimate, "ci95_task_bootstrap": interval,
        "task_counts": {k: list(v) for k, v in sorted(usable.items())},
        "warning": "deterministic location-match proxy; no human finding adjudication",
    }


def _paired_task_contrast(rows: list[dict[str, Any]], *, factor: str, low: str,
                          high: str, outcome: str, seed: int,
                          cluster_field: str = "task_id",
                          expected_clusters: Iterable[str] | None = None,
                          required_rows_per_level: int | None = None) -> dict[str, Any]:
    grouped: dict[str, dict[str, list[Any]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        if row.get(factor) not in {low, high}:
            continue
        cluster_id = row.get(cluster_field)
        if cluster_id is None:
            continue
        grouped[str(cluster_id)][row[factor]].append(row.get(outcome))
    contrasts: dict[str, float] = {}
    incomplete: list[str] = []
    missing_by_level: dict[str, dict[str, int]] = {}
    cluster_ids = set(grouped)
    if expected_clusters is not None:
        cluster_ids.update(str(value) for value in expected_clusters)
    for task_id in sorted(cluster_ids):
        levels = grouped.get(task_id, {})
        low_rows, high_rows = levels.get(low, []), levels.get(high, [])
        low_values = [float(value) for value in low_rows
                      if isinstance(value, (int, float)) and not isinstance(value, bool)]
        high_values = [float(value) for value in high_rows
                       if isinstance(value, (int, float)) and not isinstance(value, bool)]
        complete = bool(low_values) and bool(high_values)
        if required_rows_per_level is not None:
            complete = complete and all((
                len(low_rows) == required_rows_per_level,
                len(high_rows) == required_rows_per_level,
                len(low_values) == required_rows_per_level,
                len(high_values) == required_rows_per_level,
            ))
        if not complete:
            incomplete.append(task_id)
            missing_by_level[task_id] = {
                low: len(low_rows) - len(low_values),
                high: len(high_rows) - len(high_values),
            }
            continue
        contrasts[task_id] = statistics.fmean(high_values) - statistics.fmean(low_values)
    report = task_cluster_estimate(contrasts, seed=seed)
    report.update({"contrast": f"{high}_minus_{low}", "outcome": outcome,
                   "incomplete_tasks": incomplete, "incomplete_clusters": incomplete,
                   "cluster_field": cluster_field,
                   "n_clusters": report["n_tasks"],
                   "cluster_values": report["task_values"],
                   "required_rows_per_level": required_rows_per_level,
                   "missing_observations_by_cluster_level": missing_by_level})
    return report


def _cross_same(rows: list[dict[str, Any]], outcome: str, seed: int) -> dict[str, Any]:
    enriched = []
    for row in rows:
        if row.get("auditor_vendor") is None:
            continue
        copy = dict(row)
        copy["assignment"] = (
            "cross" if row["generator_vendor"] != row["auditor_vendor"] else "same"
        )
        enriched.append(copy)
    return _paired_task_contrast(
        enriched, factor="assignment", low="same", high="cross", outcome=outcome,
        seed=seed,
    )


def _parse_event_snapshot(manifest_raw: bytes, events_raw: bytes) \
        -> tuple[dict[str, Any], list[dict[str, Any]]]:
    try:
        manifest = json.loads(manifest_raw.decode("utf-8"))
        lines = events_raw.decode("utf-8").splitlines()
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("manifest or journal is not valid UTF-8 JSON") from exc
    _validate_manifest_and_live_code(manifest)
    events: list[dict[str, Any]] = []
    seen: set[str] = set()
    previous_hash = manifest.get("freeze_sha256")
    for lineno, line in enumerate(lines, 1):
        if not line.strip():
            continue
        event = json.loads(line)
        if event.get("freeze_sha256") != manifest.get("freeze_sha256"):
            raise ValueError(f"events.jsonl:{lineno}: freeze hash mismatch")
        recorded_hash = event.get("event_sha256")
        unsigned = {k: v for k, v in event.items() if k != "event_sha256"}
        if event.get("previous_event_sha256") != previous_hash:
            raise ValueError(f"events.jsonl:{lineno}: broken event hash chain")
        if not isinstance(recorded_hash, str) or _digest(unsigned) != recorded_hash:
            raise ValueError(f"events.jsonl:{lineno}: invalid event hash")
        event_id = event.get("event_id")
        if not isinstance(event_id, str) or event_id in seen:
            raise ValueError(f"events.jsonl:{lineno}: duplicate or missing event_id")
        seen.add(event_id)
        events.append(event)
        previous_hash = recorded_hash
    starts = [event for event in events if event.get("kind") == "study_start"]
    if len(starts) != 1 or starts[0].get("pre_dispatch_freeze_anchor") \
            != manifest.get("pre_dispatch_freeze_anchor"):
        raise ValueError("study_start does not bind the manifest pre-dispatch freeze anchor")
    return manifest, events


def load_event_snapshot(run_dir: Path) \
        -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, str]]:
    manifest_path, events_path = run_dir / "run_manifest.json", run_dir / "events.jsonl"
    if not manifest_path.is_file() or not events_path.is_file():
        raise ValueError("run directory must contain run_manifest.json and events.jsonl")
    if manifest_path.is_symlink() or events_path.is_symlink():
        raise ValueError("manifest and journal must be regular non-symlink files")
    manifest_raw, events_raw = manifest_path.read_bytes(), events_path.read_bytes()
    manifest, events = _parse_event_snapshot(manifest_raw, events_raw)
    return manifest, events, {
        "run_manifest.json": hashlib.sha256(manifest_raw).hexdigest(),
        "events.jsonl": hashlib.sha256(events_raw).hexdigest(),
    }


def load_events(run_dir: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    manifest, events, _ = load_event_snapshot(run_dir)
    return manifest, events


def _bytes_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _assert_snapshot_unchanged(run_dir: Path, snapshot_hashes: dict[str, str]) -> None:
    for name, expected in snapshot_hashes.items():
        path = run_dir / name
        if not path.is_file() or path.is_symlink() or _bytes_sha256(path) != expected:
            raise RuntimeError(f"sealed input changed during scoring: {name}")


def _atomic_bytes(path: Path, raw: bytes) -> None:
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent,
    )
    temporary_path = Path(temporary)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise


def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    raw = (json.dumps(
        value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False,
    ) + "\n").encode("utf-8")
    _atomic_bytes(path, raw)


def _seal_static(run_dir: Path, manifest: dict[str, Any],
                 events: list[dict[str, Any]],
                 snapshot_hashes: dict[str, str] | None = None) -> dict[str, Any]:
    hashes = snapshot_hashes or {
        "run_manifest.json": _bytes_sha256(run_dir / "run_manifest.json"),
        "events.jsonl": _bytes_sha256(run_dir / "events.jsonl"),
    }
    return {
        "format_version": SEAL_FORMAT_VERSION,
        "freeze_sha256": manifest.get("freeze_sha256"),
        "manifest_bytes_sha256": hashes["run_manifest.json"],
        "journal_bytes_sha256": hashes["events.jsonl"],
        "final_event_sha256": events[-1].get("event_sha256") if events else None,
        "event_count": len(events),
        "scheduled_call_count": sum(e.get("kind") == "call_scheduled" for e in events),
        "completed_call_count": sum(e.get("kind") == "call_complete" for e in events),
        "structural_semantic_integrity_valid": True,
        "summary_absent_at_creation": True,
        "claim_boundary": manifest.get("claim_status"),
        "next_required_step": (
            "Commit and push this seal with the exact manifest and journal to the "
            "network upstream before invoking score.py without --seal-only."
        ),
    }


def _validate_local_seal(run_dir: Path, manifest: dict[str, Any],
                         events: list[dict[str, Any]], *, seal_raw: bytes | None = None,
                         snapshot_hashes: dict[str, str] | None = None) -> dict[str, Any]:
    path = run_dir / SEAL_FILENAME
    try:
        raw = seal_raw if seal_raw is not None else path.read_bytes()
        seal = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise ValueError(f"{SEAL_FILENAME} is missing or unreadable") from exc
    if not isinstance(seal, dict) or set(seal) != SEAL_FIELDS:
        raise ValueError(f"{SEAL_FILENAME} has unexpected or missing fields")
    unsigned = {key: value for key, value in seal.items() if key != "seal_sha256"}
    if seal.get("seal_sha256") != _digest(unsigned):
        raise ValueError(f"{SEAL_FILENAME} self-hash is invalid")
    expected = _seal_static(run_dir, manifest, events, snapshot_hashes)
    observed = {key: seal.get(key) for key in expected}
    if observed != expected:
        raise ValueError(f"{SEAL_FILENAME} differs from the current immutable run bytes")
    if not isinstance(seal.get("created_utc"), str) or not seal["created_utc"]:
        raise ValueError(f"{SEAL_FILENAME} lacks its creation time")
    return seal


@contextmanager
def _result_lock(run_dir: Path):
    """Use the same retained lock inode as the runner and standalone scorer."""
    run_dir.mkdir(parents=True, exist_ok=True)
    handle = (run_dir / ".crossaudit-feasibility.lock").open("a+")
    try:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            if exc.errno not in {errno.EACCES, errno.EAGAIN}:
                raise
            raise RuntimeError(f"result directory is locked: {run_dir}") from exc
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    finally:
        handle.close()


def _seal_run_locked(run_dir: Path) -> dict[str, Any]:
    manifest, events, snapshot_hashes = load_event_snapshot(run_dir)
    frozen = manifest["frozen_core"]
    structure = validate_structure(events, frozen)
    if not structure.get("valid"):
        raise ValueError(
            "refusing outcome-free seal because structural/semantic validation failed: "
            + "; ".join(str(error) for error in structure.get("errors", [])[:20])
        )
    seal_path = run_dir / SEAL_FILENAME
    if seal_path.exists():
        seal_raw = seal_path.read_bytes()
        return _validate_local_seal(
            run_dir, manifest, events, seal_raw=seal_raw,
            snapshot_hashes=snapshot_hashes,
        )
    forbidden = [run_dir / "summary.json", run_dir / ANALYSIS_RECEIPT_FILENAME]
    if any(path.exists() for path in forbidden):
        raise ValueError("refusing first seal after scientific analysis artefacts exist")
    seal = {
        **_seal_static(run_dir, manifest, events, snapshot_hashes),
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    seal["seal_sha256"] = _digest(seal)
    _atomic_json(seal_path, seal)
    return seal


def seal_run(run_dir: Path, *, _lock_held: bool = False) -> dict[str, Any]:
    """Validate and seal a terminal journal without calculating any endpoint."""
    resolved = run_dir.resolve()
    if _lock_held:
        return _seal_run_locked(resolved)
    with _result_lock(resolved):
        return _seal_run_locked(resolved)


def _non_file_remote_url(url: str) -> bool:
    return network_git_remote_allowed(url)


def _git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True,
        timeout=45, env=git_verification_env(),
    )
    if check and proc.returncode:
        raise RuntimeError(proc.stderr.strip() or f"git {' '.join(args)} failed")
    return proc


def verify_cohort_seal_committed_and_pushed(
    run_dir: Path, snapshot_hashes: dict[str, str],
) -> dict[str, str]:
    """Prove the raw terminal cohort was on a network remote before scoring."""
    resolved = run_dir.resolve()
    try:
        relative_dir = resolved.relative_to(REPO_ROOT)
    except ValueError as exc:
        raise RuntimeError("the live result directory must be inside the repository") from exc
    relative_paths = [
        relative_dir / "run_manifest.json",
        relative_dir / "events.jsonl",
        relative_dir / SEAL_FILENAME,
    ]
    freeze_relative = Path("experiment/v4/feasibility/FREEZE.json")
    freeze_path = REPO_ROOT / freeze_relative
    replacements = _git("replace", "-l", check=False)
    if replacements.returncode or replacements.stdout.strip():
        raise RuntimeError("local Git replace objects are forbidden for anchor verification")
    common_dir = _git("rev-parse", "--git-common-dir", check=False)
    if common_dir.returncode or not common_dir.stdout.strip():
        raise RuntimeError("could not resolve the Git common directory")
    common_path = Path(common_dir.stdout.strip())
    if not common_path.is_absolute():
        common_path = (REPO_ROOT / common_path).resolve()
    if (common_path / "info/grafts").exists():
        raise RuntimeError("legacy Git grafts are forbidden for anchor verification")
    try:
        freeze_doc = json.loads(freeze_path.read_text())
        manifest = json.loads((resolved / "run_manifest.json").read_text())
    except Exception as exc:
        raise RuntimeError("freeze or run manifest is unreadable during anchor verification") from exc
    if freeze_doc.get("freeze_sha256") != manifest.get("freeze_sha256") \
            or freeze_doc.get("frozen") != manifest.get("frozen_core"):
        raise RuntimeError("tracked FREEZE.json does not bind the sealed run manifest")
    expected_hashes = dict(snapshot_hashes)
    if set(expected_hashes) != {"run_manifest.json", "events.jsonl", SEAL_FILENAME}:
        raise RuntimeError("scorer did not provide one complete immutable snapshot")
    for relative in relative_paths:
        _git("ls-files", "--error-unmatch", str(relative))
    _git("ls-files", "--error-unmatch", str(freeze_relative))
    if _git(
        "status", "--porcelain", "--", str(freeze_relative),
        *(str(p) for p in relative_paths),
    ).stdout.strip():
        raise RuntimeError("freeze, cohort seal, manifest or journal has uncommitted changes")
    shallow = _git("rev-parse", "--is-shallow-repository", check=False)
    if shallow.returncode or shallow.stdout.strip() != "false":
        raise RuntimeError("a complete non-shallow Git history is required for seal verification")
    seal_relative = relative_paths[-1]
    seal_commit = _git("log", "-1", "--format=%H", "--", str(seal_relative)).stdout.strip()
    if not seal_commit:
        raise RuntimeError("cohort seal has no containing commit")
    for relative in relative_paths:
        raw = subprocess.run(
            ["git", "show", f"{seal_commit}:{relative}"], cwd=REPO_ROOT,
            capture_output=True, timeout=45, env=git_verification_env(),
        )
        expected = expected_hashes[relative.name]
        if _bytes_sha256(REPO_ROOT / relative) != expected:
            raise RuntimeError(f"live {relative} changed after the scorer snapshot")
        if raw.returncode or hashlib.sha256(raw.stdout).hexdigest() != expected:
            raise RuntimeError(f"seal commit does not contain the current bytes of {relative}")
    for forbidden_name in ("summary.json", ANALYSIS_RECEIPT_FILENAME):
        forbidden = relative_dir / forbidden_name
        if _git("cat-file", "-e", f"{seal_commit}:{forbidden}", check=False).returncode == 0:
            raise RuntimeError("the pre-analysis seal commit already contains scientific output")

    freeze_commit = _git(
        "log", "-1", "--format=%H", "--", str(freeze_relative),
    ).stdout.strip()
    if not freeze_commit:
        raise RuntimeError("FREEZE.json has no containing commit")
    pre_dispatch = manifest["pre_dispatch_freeze_anchor"]
    if pre_dispatch.get("freeze_commit") != freeze_commit:
        raise RuntimeError("manifest pre-dispatch commit differs from the tracked freeze commit")
    start_tip = str(pre_dispatch.get("network_remote_tip_at_start"))
    if _git("cat-file", "-e", f"{start_tip}^{{commit}}", check=False).returncode:
        raise RuntimeError("pre-dispatch network tip is not available in the local object database")
    frozen_blob = subprocess.run(
        ["git", "show", f"{freeze_commit}:{freeze_relative}"], cwd=REPO_ROOT,
        capture_output=True, timeout=45, env=git_verification_env(),
    )
    if frozen_blob.returncode or frozen_blob.stdout != freeze_path.read_bytes():
        raise RuntimeError("freeze commit does not contain the current FREEZE.json bytes")
    if freeze_commit == seal_commit:
        raise RuntimeError("freeze and post-run seal must be in distinct commits")
    if _git("merge-base", "--is-ancestor", freeze_commit, start_tip, check=False).returncode:
        raise RuntimeError("pre-dispatch network tip does not contain the freeze commit")
    if start_tip == seal_commit or _git(
        "merge-base", "--is-ancestor", start_tip, seal_commit, check=False,
    ).returncode:
        raise RuntimeError("pre-dispatch network tip is not strictly before the seal commit")
    if _git("merge-base", "--is-ancestor", freeze_commit, seal_commit, check=False).returncode:
        raise RuntimeError("pre-dispatch freeze commit is not an ancestor of the seal commit")

    upstream = _git("rev-parse", "--verify", "@{upstream}", check=False)
    if upstream.returncode:
        raise RuntimeError("current branch has no upstream containing the cohort seal")
    upstream_commit = upstream.stdout.strip()
    if _git("merge-base", "--is-ancestor", seal_commit, upstream_commit, check=False).returncode:
        raise RuntimeError("the cohort seal commit is not present on upstream")
    branch = _git("symbolic-ref", "--quiet", "--short", "HEAD", check=False).stdout.strip()
    if not branch:
        raise RuntimeError("detached HEAD has no verifiable network upstream")
    remote = _git("config", "--get", f"branch.{branch}.remote", check=False).stdout.strip()
    merge_ref = _git("config", "--get", f"branch.{branch}.merge", check=False).stdout.strip()
    if not remote or remote == "." or not merge_ref.startswith("refs/heads/"):
        raise RuntimeError("upstream is not a real remote branch")
    remote_url = _git("remote", "get-url", remote, check=False).stdout.strip()
    if not _non_file_remote_url(remote_url):
        raise RuntimeError("upstream must use the registered GitHub network host")
    advertised = subprocess.run(
        ["git", "ls-remote", "--exit-code", remote_url, merge_ref],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=45,
        env=git_verification_env(),
    )
    if advertised.returncode:
        raise RuntimeError("network git ls-remote could not verify the cohort seal")
    remote_tips = [
        sha for sha, ref in (
            line.split("\t", 1) for line in advertised.stdout.splitlines() if "\t" in line
        ) if ref == merge_ref
    ]
    if len(remote_tips) != 1 or not re.fullmatch(r"[0-9a-fA-F]{40,64}", remote_tips[0]):
        raise RuntimeError("network git ls-remote returned no unique upstream tip")
    remote_tip = remote_tips[0]
    if _git("cat-file", "-e", f"{remote_tip}^{{commit}}", check=False).returncode:
        raise RuntimeError("network upstream advanced to an unknown commit; fetch and retry")
    if _git("merge-base", "--is-ancestor", seal_commit, remote_tip, check=False).returncode:
        raise RuntimeError("network-advertised upstream does not contain the cohort seal")
    if upstream_commit != remote_tip:
        raise RuntimeError("local upstream tracking tip differs from network-advertised tip")
    seal_history = [
        line for line in _git(
            "log", "--format=%H", remote_tip, "--", str(seal_relative),
        ).stdout.splitlines() if line.strip()
    ]
    seal_additions = [
        line for line in _git(
            "log", "--diff-filter=A", "--format=%H", remote_tip, "--",
            str(seal_relative),
        ).stdout.splitlines() if line.strip()
    ]
    if seal_history != [seal_commit] or seal_additions != [seal_commit]:
        raise RuntimeError(
            "cohort seal is not an add-once immutable path in the advertised remote history"
        )
    return {
        "freeze_commit": freeze_commit,
        "network_remote_tip_at_start": start_tip,
        "seal_commit": seal_commit,
        "network_remote_tip": remote_tip,
    }


def _execution_summary(events: list[dict[str, Any]]) -> dict[str, Any]:
    scheduled = [e for e in events if e.get("kind") == "call_scheduled"]
    completed = [e for e in events if e.get("kind") == "call_complete"]
    by_cell: dict[str, dict[str, Any]] = {}
    for event in completed:
        key = f"{event.get('provider')}/{event.get('role')}"
        bucket = by_cell.setdefault(key, {
            "scheduled_completions": 0, "provider_invocations": 0,
            "statuses": Counter(),
            **{field: 0 for field in USAGE_TOKEN_FIELDS},
            "usage_available_provider_invocations": 0,
            "usage_unavailable_provider_invocations": 0,
            "usage_provenance": Counter(),
            "known_cost_usd": 0.0, "unknown_cost_calls": 0, "latencies": [],
            "cost_sources": Counter(), "identity_states": Counter(),
        })
        bucket["scheduled_completions"] += 1
        bucket["provider_invocations"] += int(bool(event.get("provider_invoked")))
        bucket["statuses"][event.get("status", "missing")] += 1
        usage = event.get("usage") or {}
        for field in USAGE_TOKEN_FIELDS:
            bucket[field] += int(usage.get(field, 0) or 0)
        if event.get("provider_invoked"):
            availability = "available" if usage.get("available") else "unavailable"
            bucket[f"usage_{availability}_provider_invocations"] += 1
            bucket["usage_provenance"][str(usage.get("provenance", "missing"))] += 1
        if isinstance(event.get("cost_usd"), (int, float)):
            bucket["known_cost_usd"] += float(event["cost_usd"])
        elif event.get("provider_invoked"):
            bucket["unknown_cost_calls"] += 1
        if event.get("provider_invoked"):
            bucket["latencies"].append(float(event.get("elapsed_seconds", 0.0)))
            bucket["cost_sources"][str(event.get("cost_source", "missing"))] += 1
            identity = event.get("identity_verified")
            bucket["identity_states"]["verified" if identity is True else
                                      "drift" if identity is False else "unverified"] += 1
    rendered: dict[str, Any] = {}
    for key, bucket in sorted(by_cell.items()):
        latency = _descriptive(bucket.pop("latencies"))
        bucket["statuses"] = dict(sorted(bucket["statuses"].items()))
        bucket["cost_sources"] = dict(sorted(bucket["cost_sources"].items()))
        bucket["identity_states"] = dict(sorted(bucket["identity_states"].items()))
        bucket["usage_provenance"] = dict(sorted(bucket["usage_provenance"].items()))
        bucket["known_cost_usd"] = round(bucket["known_cost_usd"], 9)
        bucket["latency_seconds"] = latency
        rendered[key] = bucket
    status_counts = Counter(e.get("status", "missing") for e in completed)
    failures = sum(n for status, n in status_counts.items() if status != "valid")
    invoked = [e for e in completed if e.get("provider_invoked")]
    usage_provenance = Counter(
        str((e.get("usage") or {}).get("provenance", "missing")) for e in invoked
    )
    return {
        "n_scheduled": len(scheduled), "n_completed": len(completed),
        "uncompleted_schedule_events": len({e["call_id"] for e in scheduled}
                                           - {e["call_id"] for e in completed}),
        "provider_invocations": len(invoked),
        "usage_available_provider_invocations": sum(
            bool((e.get("usage") or {}).get("available")) for e in invoked
        ),
        "usage_unavailable_provider_invocations": sum(
            not bool((e.get("usage") or {}).get("available")) for e in invoked
        ),
        "usage_provenance": dict(sorted(usage_provenance.items())),
        "status_counts": dict(sorted(status_counts.items())),
        "failed_or_unavailable_ITT_calls": failures,
        "token_totals": {
            field: sum(int((e.get("usage") or {}).get(field, 0) or 0) for e in completed)
            for field in USAGE_TOKEN_FIELDS
        },
        "known_cost_usd": round(sum(float(e.get("cost_usd", 0.0) or 0.0) for e in completed), 9),
        "unknown_cost_calls": sum(e.get("provider_invoked") and e.get("cost_usd") is None
                                  for e in completed),
        "cost_cap_overshoot_calls": sum(
            bool(e.get("global_cap_overshoot") or e.get("provider_cap_overshoot"))
            for e in completed
        ),
        "by_provider_and_role": rendered,
    }


def _group_rates(rows: list[dict[str, Any]], factors: tuple[str, ...],
                 outcome: str) -> dict[str, Any]:
    grouped: dict[tuple[Any, ...], list[float]] = defaultdict(list)
    missing: Counter[tuple[Any, ...]] = Counter()
    for row in rows:
        key = tuple(row.get(f) for f in factors)
        if row.get(outcome) is None:
            missing[key] += 1
        else:
            grouped[key].append(float(row[outcome]))
    out = {}
    for key in sorted(set(grouped) | set(missing), key=lambda x: repr(x)):
        label = "/".join(str(x) for x in key)
        values = grouped.get(key, [])
        out[label] = {"n_rows": len(values), "n_missing_gold": missing[key],
                      "mean": _mean(values)}
    return out


def _task_interaction(
    rows: list[dict[str, Any]], *, outcome: str, constitution_low: str,
    constitution_high: str, seed: int,
) -> dict[str, Any]:
    grouped: dict[str, dict[tuple[str, str], list[float]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for row in rows:
        value = row.get(outcome)
        key = (row.get("constitution"), row.get("dcl_mode"))
        if key[0] not in {constitution_low, constitution_high} \
                or key[1] not in {"D0_OFF", "D2_COMBINED_BLIND"} \
                or value is None:
            continue
        grouped[str(row.get("task_id"))][key].append(float(value))
    values: dict[str, float] = {}
    incomplete: list[str] = []
    required = {
        (constitution_low, "D0_OFF"), (constitution_low, "D2_COMBINED_BLIND"),
        (constitution_high, "D0_OFF"), (constitution_high, "D2_COMBINED_BLIND"),
    }
    for task_id, cells in sorted(grouped.items()):
        if not required.issubset(cells):
            incomplete.append(task_id)
            continue
        mean = {key: statistics.fmean(cells[key]) for key in required}
        values[task_id] = (
            mean[(constitution_high, "D2_COMBINED_BLIND")]
            - mean[(constitution_high, "D0_OFF")]
            - mean[(constitution_low, "D2_COMBINED_BLIND")]
            + mean[(constitution_low, "D0_OFF")]
        )
    report = task_cluster_estimate(values, seed=seed)
    report.update({
        "contrast": (
            f"({constitution_high}:D2-D0)-({constitution_low}:D2-D0)"
        ),
        "outcome": outcome,
        "incomplete_tasks": incomplete,
    })
    return report


def _channel_decomposition(events: list[dict[str, Any]]) -> dict[str, Any]:
    artifacts = {
        row.get("artifact_id"): row for row in events if row.get("kind") == "artifact"
    }
    dcl = {
        row.get("artifact_id"): {
            str(finding.get("location")) for finding in row.get("findings", [])
            if isinstance(finding, dict)
        }
        for row in events if row.get("kind") == "dcl_result"
    }
    calls = {
        row.get("call_id"): row for row in events
        if row.get("kind") == "call_complete" and row.get("role") == "auditor"
    }
    decisions = [
        row for row in events if row.get("kind") == "audit_decision"
        and row.get("dcl_mode") == "D0_OFF" and row.get("constitution") == "C2"
    ]
    channel_counts: Counter[str] = Counter()
    false_positive_counts: Counter[str] = Counter()
    by_task: dict[str, Counter[str]] = defaultdict(Counter)
    audits = 0
    for row in decisions:
        call = calls.get(row.get("call_id")) or {}
        value = (call.get("response") or {}).get("value") if call.get("status") == "valid" else {}
        llm_locations = {
            str(finding.get("location")) for finding in value.get("findings", [])
            if isinstance(finding, dict) and finding.get("severity") == "BLOCKER"
        } if isinstance(value, dict) else set()
        dcl_locations = dcl.get(row.get("artifact_id"), set())
        artifact = artifacts.get(row.get("artifact_id")) or {}
        gold_locations = {
            str(defect.get("location")) for defect in artifact.get("defects", [])
            if isinstance(defect, dict)
        }
        audits += 1
        for location in gold_locations:
            channel = (
                "overlap" if location in llm_locations and location in dcl_locations
                else "llm_only" if location in llm_locations else "dcl_only"
                if location in dcl_locations else "neither"
            )
            channel_counts[channel] += 1
            by_task[str(row.get("task_id"))][channel] += 1
        llm_false = llm_locations - gold_locations
        dcl_false = dcl_locations - gold_locations
        for location in llm_false | dcl_false:
            source = (
                "both" if location in llm_false and location in dcl_false
                else "llm_only" if location in llm_false else "dcl_only"
            )
            false_positive_counts[source] += 1
            by_task[str(row.get("task_id"))][f"false_positive_{source}"] += 1
    return {
        "gold_defect_channel_counts": dict(sorted(channel_counts.items())),
        "false_positive_location_burden": dict(sorted(false_positive_counts.items())),
        "by_task": {task: dict(sorted(counts.items())) for task, counts in sorted(by_task.items())},
        "n_C2_D0_audits": audits,
        "unit": (
            "Each deterministic gold defect location per C2 D0 audit is classified as overlap, "
            "LLM-only, DCL-only or neither; non-gold locations are separate false-positive burden."
        ),
        "warning": "DCL uses the same deterministic checker as feasibility gold (ceiling proxy).",
    }


def _core_summary(events: list[dict[str, Any]], design: dict[str, Any]) -> dict[str, Any]:
    rows = [e for e in events if e.get("kind") == "audit_decision"]
    c2 = [e for e in rows if e.get("constitution") == "C2"]
    task_ids = [str(value) for value in design.get("task_ids", [])]
    vendors = [str(value) for value in design.get("generator_vendors", [])]
    primary = {}
    for mode in ("D0_OFF", "D2_COMBINED_BLIND"):
        selected = [e for e in c2 if e.get("dcl_mode") == mode]
        primary[mode] = {
            "controlled_correct_gate_fixed_2x2": fixed_weight_2x2(
                selected, task_ids=task_ids, vendors=vendors,
                strata=("clean", "seeded", "ambiguous"), outcome="correct_gate",
                seed=410 + len(mode),
            ),
            "negative_control_false_block_fixed_2x2": fixed_weight_2x2(
                [e for e in selected if e.get("false_block") is not None],
                task_ids=task_ids, vendors=vendors, strata=("clean", "ambiguous"),
                outcome="false_block", seed=510 + len(mode),
            ),
            "natural_available_gold_fixed_2x2": natural_available_gold_2x2(
                [e for e in selected if e.get("correct_gate") is not None],
                task_ids=task_ids, vendors=vendors, outcome="correct_gate",
                seed=560 + len(mode),
            ),
            "rates_by_assignment_and_artifact_type": _group_rates(
                [{**e, "assignment": "cross" if e["generator_vendor"] != e["auditor_vendor"] else "same"}
                 for e in selected],
                ("assignment", "artifact_type"), "correct_gate",
            ),
        }

    dcl_rows = [e for e in rows if e.get("dcl_mode") == "D1_ONLY"]
    dcl_contrast_rows = [
        e for e in rows if e.get("dcl_mode") in {
            "D0_OFF", "D1_ONLY", "D2_COMBINED_BLIND",
        } and (e.get("constitution") == "C2" or e.get("dcl_mode") == "D1_ONLY")
    ]
    dcl_contrasts: dict[str, Any] = {}
    for outcome in ("correct_gate", "false_block", "escalation"):
        dcl_contrasts[outcome] = {
            "D2_minus_D0": _paired_task_contrast(
                dcl_contrast_rows, factor="dcl_mode", low="D0_OFF",
                high="D2_COMBINED_BLIND", outcome=outcome, seed=620 + len(outcome),
            ),
            "D2_minus_D1": _paired_task_contrast(
                dcl_contrast_rows, factor="dcl_mode", low="D1_ONLY",
                high="D2_COMBINED_BLIND", outcome=outcome, seed=650 + len(outcome),
            ),
        }
    dcl_ablation = {
        "D1_ONLY_accuracy_by_artifact_type": _group_rates(dcl_rows, ("artifact_type",), "correct_gate"),
        "paired_contrasts": dcl_contrasts,
        "catch_channel_decomposition": _channel_decomposition(events),
        "interpretation_limit": (
            "The offline checker also defines gold on these microtasks, so D1 is a plumbing "
            "ceiling check, not an unbiased DCL effectiveness estimate."
        ),
    }

    subset_ids = set(str(value) for value in design.get("constitution_subset_task_ids", []))
    constitution_rows = [e for e in rows if e.get("task_id") in subset_ids
                         and e.get("constitution") in {"C0", "C1", "C2"}
                         and e.get("repeat") == 0
                         and e.get("artifact_type") in {"clean", "seeded"}]
    constitution: dict[str, Any] = {
        "frozen_subset_task_ids": sorted(subset_ids),
        "subset_scope_note": "Only the frozen subset is eligible; other C2 tasks are not missing ablation cells.",
    }
    for outcome in ("correct_gate", "false_block", "escalation"):
        by_mode: dict[str, Any] = {}
        for mode in ("D0_OFF", "D2_COMBINED_BLIND"):
            arm = [row for row in constitution_rows if row.get("dcl_mode") == mode]
            by_mode[mode] = {
                "C1_minus_C0": _paired_task_contrast(
                    arm, factor="constitution", low="C0", high="C1",
                    outcome=outcome, seed=701 + len(outcome) + len(mode),
                ),
                "C2_minus_C1": _paired_task_contrast(
                    arm, factor="constitution", low="C1", high="C2",
                    outcome=outcome, seed=731 + len(outcome) + len(mode),
                ),
                "C2_minus_C0": _paired_task_contrast(
                    arm, factor="constitution", low="C0", high="C2",
                    outcome=outcome, seed=761 + len(outcome) + len(mode),
                ),
            }
        constitution[outcome] = {
            "mechanism_primary": "D0_OFF",
            "by_dcl_mode": by_mode,
            "weighting_note": (
                "Within each mode the frozen artifact×generator×auditor cells are balanced; "
                "D0 and D2 are never pooled for a Constitution estimand."
            ),
        }
        constitution.setdefault("C_by_D_interactions", {})[outcome] = {
            "C1_vs_C0": _task_interaction(
                constitution_rows, outcome=outcome, constitution_low="C0",
                constitution_high="C1", seed=791 + len(outcome),
            ),
            "C2_vs_C1": _task_interaction(
                constitution_rows, outcome=outcome, constitution_low="C1",
                constitution_high="C2", seed=821 + len(outcome),
            ),
            "C2_vs_C0": _task_interaction(
                constitution_rows, outcome=outcome, constitution_low="C0",
                constitution_high="C2", seed=851 + len(outcome),
            ),
        }

    repeat_groups: dict[tuple[str, str], list[tuple[str, str]]] = defaultdict(list)
    for row in c2:
        if row.get("dcl_mode") == "D0_OFF":
            repeat_groups[(row["artifact_id"], row["auditor_vendor"])].append((
                str(row.get("call_status")), str(row.get("gate")),
            ))
    valid_flips: list[int] = []
    availability_patterns: Counter[str] = Counter()
    gate_flips_including_error: list[int] = []
    for repeats in repeat_groups.values():
        valid = [gate for status, gate in repeats if status == "valid" and gate in {"PASS", "BLOCK"}]
        if len(valid) == 3:
            availability_patterns["all_three_valid"] += 1
            valid_flips.append(int(len(set(valid)) > 1))
        elif not valid:
            availability_patterns["no_valid_verdict"] += 1
        else:
            availability_patterns["mixed_validity"] += 1
        gate_flips_including_error.append(int(len({gate for _, gate in repeats}) > 1))
    finding_proxy = _finding_proxy(events)
    by_kind = Counter(e.get("artifact_type") for e in events
                      if e.get("kind") == "artifact" and e.get("module") == "core")
    gold = Counter(e.get("gold_status") for e in events
                   if e.get("kind") == "artifact" and e.get("module") == "core")
    return {
        "n_decision_rows": len(rows), "artefacts_by_type": dict(sorted(by_kind.items())),
        "gold_status_counts": dict(sorted(gold.items())), "primary_pairing": primary,
        "dcl_ablation": dcl_ablation, "constitution_ablation": constitution,
        "C2_three_repeat_stability": {
            "n_artifact_auditor_cells_ITT": len(repeat_groups),
            "availability_patterns": dict(sorted(availability_patterns.items())),
            "valid_verdict_flip_rate_among_all_three_valid": _mean(valid_flips),
            "n_all_three_valid_cells": len(valid_flips),
            "gate_flip_rate_including_ERROR_diagnostic": _mean(gate_flips_including_error),
            "note": (
                "Each cell is one artefact-auditor pair. Verdict reliability is estimated only "
                "when all three D0 replies are valid PASS/BLOCK; repeated failures are reported "
                "as availability patterns and never counted as stable verdicts."
            ),
        },
        "finding_location_match_proxy": finding_proxy,
        "all_rates_by_constitution_dcl": _group_rates(
            rows, ("constitution", "dcl_mode"), "correct_gate"
        ),
    }


def _finding_proxy(events: list[dict[str, Any]]) -> dict[str, Any]:
    artifacts = {e["artifact_id"]: e for e in events if e.get("kind") == "artifact"}
    decisions = {
        e.get("call_id"): e for e in events
        if e.get("kind") == "audit_decision" and e.get("dcl_mode") == "D0_OFF"
    }
    calls = [
        e for e in events if e.get("kind") == "call_complete"
        and e.get("role") == "auditor"
        and (e.get("metadata") or {}).get("constitution") == "C2"
    ]
    precision_by_task: dict[str, list[float]] = defaultdict(list)
    recall_by_task: dict[str, list[float]] = defaultdict(list)
    finding_confidence_pairs: list[tuple[float, int]] = []
    audit_confidence_pairs: list[tuple[float, int]] = []
    audit_confidence_brier_itt: list[float] = []
    finding_sets: dict[tuple[str, str], list[tuple[bool, set[str]]]] = defaultdict(list)
    no_precision_reply_count = 0
    for call in calls:
        metadata = call.get("metadata") or {}
        artifact = artifacts.get(metadata.get("artifact_id"))
        if not artifact or artifact.get("requires_block") is None:
            continue
        task_id = artifact["task_id"]
        # Initialise every eligible task even when the reviewer emits no
        # blockers, so the cluster universe is not conditioned on a finding.
        precision_by_task[task_id]
        recall_by_task[task_id]
        gold_locations = {str(d.get("location")) for d in artifact.get("defects", [])}
        value = ((call.get("response") or {}).get("value")
                 if call.get("status") == "valid" else None)
        findings = value.get("findings", []) if isinstance(value, dict) else []
        blockers = [f for f in findings
                    if isinstance(f, dict) and f.get("severity") == "BLOCKER"]
        matched_locations: set[str] = set()
        for finding in blockers:
            location = str(finding.get("location"))
            valid = int(location in gold_locations)
            if valid:
                matched_locations.add(location)
            confidence = finding.get("confidence")
            if isinstance(confidence, (int, float)) and not isinstance(confidence, bool):
                finding_confidence_pairs.append((float(confidence), valid))
        if blockers:
            precision_by_task[task_id].append(len(matched_locations) / len(blockers))
        else:
            no_precision_reply_count += 1
        if gold_locations:
            recall_by_task[task_id].append(
                len(gold_locations & matched_locations) / len(gold_locations)
            )
        finding_sets[(artifact["artifact_id"], call["provider"])].append((
            call.get("status") == "valid", set(matched_locations),
        ))
        confidence = value.get("confidence") if isinstance(value, dict) else None
        decision = decisions.get(call["call_id"])
        if isinstance(confidence, (int, float)) and not isinstance(confidence, bool) and decision:
            target = int(decision.get("correct_gate") or 0)
            pair = (float(confidence), target)
            audit_confidence_pairs.append(pair)
            audit_confidence_brier_itt.append((pair[0] - pair[1]) ** 2)
        else:
            audit_confidence_brier_itt.append(1.0)
    overlaps: list[float] = []
    invalid_repeat_pairs = 0
    for repeats in finding_sets.values():
        for left, right in itertools.combinations(repeats, 2):
            if not left[0] or not right[0]:
                invalid_repeat_pairs += 1
                continue
            left_hits, right_hits = left[1], right[1]
            overlaps.append(
                len(left_hits & right_hits) / len(left_hits | right_hits)
                if left_hits | right_hits else 1.0
            )
    precision_task_values = {
        task: statistics.fmean(values) for task, values in precision_by_task.items() if values
    }
    recall_task_values = {
        task: statistics.fmean(values) for task, values in recall_by_task.items() if values
    }
    return {
        "blocker_finding_precision_reply_then_task_equal": task_cluster_estimate(
            precision_task_values, seed=730,
        ),
        "blocker_location_recall_reply_then_task_equal_ITT": task_cluster_estimate(
            recall_task_values, seed=731,
        ),
        "replies_without_declared_blocker_precision_undefined": no_precision_reply_count,
        "repeat_matched_gold_location_jaccard_valid_pairs": {
            **_descriptive(overlaps),
            "invalid_or_missing_reply_pairs_excluded": invalid_repeat_pairs,
        },
        "finding_confidence_brier_emitted_findings_only": {
            "n": len(finding_confidence_pairs),
            "brier": _mean((p - y) ** 2 for p, y in finding_confidence_pairs),
        },
        "audit_confidence_brier": {
            "ITT_invalid_or_missing_equals_one": _mean(audit_confidence_brier_itt),
            "n_ITT": len(audit_confidence_brier_itt),
            "valid_confidence_only": _mean((p - y) ** 2 for p, y in audit_confidence_pairs),
            "n_valid_confidence": len(audit_confidence_pairs),
        },
        "scope": (
            "A blocker counts only when its declared location exactly matches a deterministic "
            "gold location. Recall is calculated per reply before equal task weighting; invalid "
            "replies contribute zero recall on defective artefacts. Repeat Jaccard uses matched "
            "gold locations only and reports invalid pairs separately. This is a feasibility "
            "proxy, not semantic adjudication."
        ),
    }


TEXT_METRICS = (
    "bytes", "words", "method_words", "evidence_count", "checks_count",
    "limitations_count", "disclaimer_count", "wrapper_count", "assertion_count",
    "exception_retry_count", "objective_correct", "held_out_correct",
    "method_novelty_vs_P0",
)


def _arm_task_means(rows: list[dict[str, Any]], metric_getter: Callable[[dict[str, Any], str], Any],
                    metrics: Iterable[str]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for metric in metrics:
        by_arm: dict[str, list[float]] = defaultdict(list)
        for row in rows:
            value = metric_getter(row, metric)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                by_arm[row["policy"]].append(float(value))
        out[metric] = {arm: _descriptive(values) for arm, values in sorted(by_arm.items())}
    return out


def _defensive_contrasts(rows: list[dict[str, Any]], getter: Callable[[dict[str, Any], str], Any],
                         metrics: Iterable[str], seed: int) -> dict[str, Any]:
    result: dict[str, Any] = {}
    expected_tasks = sorted({str(row.get("task_id")) for row in rows})
    required_rows = len({str(row.get("generator_vendor")) for row in rows})
    for offset, metric in enumerate(metrics):
        simple = [{"task_id": row["task_id"], "policy": row["policy"],
                   "value": getter(row, metric)} for row in rows]
        result[metric] = {
            "P1_minus_P0": _paired_task_contrast(
                simple, factor="policy", low="P0", high="P1", outcome="value",
                seed=seed + offset * 3, expected_clusters=expected_tasks,
                required_rows_per_level=required_rows,
            ),
            "P2_minus_P0": _paired_task_contrast(
                simple, factor="policy", low="P0", high="P2", outcome="value",
                seed=seed + offset * 3 + 1, expected_clusters=expected_tasks,
                required_rows_per_level=required_rows,
            ),
            "P2_minus_P1": _paired_task_contrast(
                simple, factor="policy", low="P1", high="P2", outcome="value",
                seed=seed + offset * 3 + 2, expected_clusters=expected_tasks,
                required_rows_per_level=required_rows,
            ),
        }
    return result


def _policy_resources(events: list[dict[str, Any]], module: str) -> dict[str, Any]:
    rows = [e for e in events if e.get("kind") == "call_complete"
            and (e.get("metadata") or {}).get("module") == module]
    out: dict[str, Any] = {}
    for policy in ("P0", "P1", "P2"):
        arm = [e for e in rows if (e.get("metadata") or {}).get("policy") == policy]
        out[policy] = {
            "scheduled_calls": len(arm),
            "provider_invocations": sum(bool(e.get("provider_invoked")) for e in arm),
            "known_cost_usd": round(sum(float(e.get("cost_usd", 0.0) or 0.0) for e in arm), 9),
            "unknown_cost_calls": sum(
                bool(e.get("provider_invoked")) and e.get("cost_usd") is None for e in arm
            ),
            "latency_seconds_sum": sum(float(e.get("elapsed_seconds", 0.0)) for e in arm),
            **{
                field: sum(int((e.get("usage") or {}).get(field, 0) or 0) for e in arm)
                for field in USAGE_TOKEN_FIELDS
            },
            "failure_count_ITT": sum(e.get("status") != "valid" for e in arm),
        }
    return out


def _ratio_endpoint(rows: list[dict[str, Any]], eligible: Callable[[dict[str, Any]], bool],
                    success: Callable[[dict[str, Any]], bool]) -> dict[str, Any]:
    denominator = [row for row in rows if eligible(row)]
    numerator = sum(bool(success(row)) for row in denominator)
    return {
        "numerator": numerator,
        "denominator": len(denominator),
        "rate": numerator / len(denominator) if denominator else None,
    }


def _bounded_loop_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for policy in ("P0", "P1", "P2"):
        arm = [row for row in rows if row.get("policy") == policy]
        out[policy] = {
            "n_sessions_ITT": len(arm),
            "repair_among_initial_wrong": _ratio_endpoint(
                arm, lambda row: not bool(row.get("initial_objective_correct")),
                lambda row: bool(row.get("final_objective_correct")),
            ),
            "regression_among_initial_correct": _ratio_endpoint(
                arm, lambda row: bool(row.get("initial_objective_correct")),
                lambda row: not bool(row.get("final_objective_correct")),
            ),
            "unnecessary_revision_among_initial_correct_revision_eligible": _ratio_endpoint(
                arm,
                lambda row: policy == "P2" and bool(row.get("initial_objective_correct")),
                lambda row: int(row.get("revisions", 0)) > 0,
            ),
            "final_objective_correct_rate_ITT": _mean(
                int(bool(row.get("final_objective_correct"))) for row in arm
            ),
            "revisions": _descriptive(int(row.get("revisions", 0)) for row in arm),
        }
    return out


def _change_label_summary(rows: list[dict[str, Any]], *, seed: int) -> dict[str, Any]:
    out: dict[str, Any] = {}
    expected_tasks = sorted({str(row.get("task_id")) for row in rows})
    conditional_task_rows: list[dict[str, Any]] = []
    for policy in ("P1", "P2"):
        arm = [row for row in rows if row.get("policy") == policy]
        counts = Counter(str(row.get("change_label_vs_P0", "missing")) for row in arm)
        changed = sum(count for label, count in counts.items() if label not in {"neutral", "missing"})
        defensive = counts.get("compliance_only", 0) + counts.get("defensive_disclaimer", 0)
        task_values: dict[str, float] = {}
        for task_id in expected_tasks:
            task_arm = [row for row in arm if str(row.get("task_id")) == task_id]
            task_changed = [
                row for row in task_arm
                if str(row.get("change_label_vs_P0", "missing")) not in {"neutral", "missing"}
            ]
            task_defensive = sum(
                str(row.get("change_label_vs_P0"))
                in {"compliance_only", "defensive_disclaimer"}
                for row in task_changed
            )
            value = task_defensive / len(task_changed) if task_changed else None
            conditional_task_rows.append({
                "task_id": task_id, "policy": policy, "value": value,
            })
            if value is not None:
                task_values[task_id] = value
        out[policy] = {
            "label_counts": dict(sorted(counts.items())),
            "changed_vs_P0_n": changed,
            "total_paired_outputs": len(arm),
            "compliance_or_disclaimer_among_changed": {
                "numerator": defensive,
                "denominator": changed,
                "rate": defensive / changed if changed else None,
            },
            "task_equal_conditional_rate": task_cluster_estimate(
                task_values, seed=seed + (1 if policy == "P1" else 2),
            ),
        }
    out["P2_minus_P1_task_clustered"] = _paired_task_contrast(
        conditional_task_rows, factor="policy", low="P1", high="P2",
        outcome="value", seed=seed + 3, expected_clusters=expected_tasks,
        required_rows_per_level=1,
    )
    out["estimand_note"] = (
        "The primary proxy conditions on a session being changed versus its paired P0. "
        "Session labels are collapsed to an equal-weight task rate before the descriptive "
        "P2-minus-P1 contrast; tasks with no changed session in either arm are explicit "
        "incomplete clusters, not silently reweighted."
    )
    return out


def _defensive_summary(events: list[dict[str, Any]]) -> dict[str, Any]:
    text_initial = [e for e in events if e.get("kind") == "defensive_metrics" and e.get("round") == 0]
    text_get = lambda row, key: (row.get("metrics") or {}).get(key)
    text_loops = [e for e in events if e.get("kind") == "defensive_loop_end"]
    text_metrics_by_artifact = {row.get("artifact_id"): row for row in events
                                if row.get("kind") == "defensive_metrics"}
    text_final = [
        {**text_metrics_by_artifact.get(loop.get("final_artifact_id"), {}),
         "task_id": loop.get("task_id"), "generator_vendor": loop.get("generator_vendor"),
         "policy": loop.get("policy")}
        for loop in text_loops
    ]

    code_initial = [e for e in events if e.get("kind") == "defensive_code_artifact" and e.get("round") == 0]
    def code_get(row: dict[str, Any], key: str) -> Any:
        evaluation = row.get("evaluation") or {}
        metrics = evaluation.get("metrics") or {}
        if key == "static_ok":
            return int(bool(evaluation.get("static_ok")))
        if key == "visible_correct":
            return int(bool(evaluation.get("visible_correct")))
        if key == "held_out_correct":
            return int(bool(evaluation.get("held_out_correct")))
        if key == "exception_retry_count":
            return int(metrics.get("exception_count", 0)) + int(metrics.get("retry_count", 0))
        if key == "checks_count":
            value = row.get("value") or {}
            return len(value.get("checks", [])) if isinstance(value.get("checks"), list) else 0
        if key == "limitations_count":
            value = row.get("value") or {}
            return len(value.get("limitations", [])) if isinstance(value.get("limitations"), list) else 0
        return metrics.get(key)

    def code_change_label(row: dict[str, Any], baseline: dict[str, Any]) -> str:
        current_eval, baseline_eval = row.get("evaluation") or {}, baseline.get("evaluation") or {}
        names = ("static_ok", "visible_correct", "held_out_correct")
        current_quality = tuple(bool(current_eval.get(name)) for name in names)
        baseline_quality = tuple(bool(baseline_eval.get(name)) for name in names)
        if current_quality != baseline_quality and all(
            current >= prior for current, prior in zip(current_quality, baseline_quality)
        ):
            return "functional_improvement"
        if current_quality != baseline_quality and all(
            current <= prior for current, prior in zip(current_quality, baseline_quality)
        ):
            return "harmful"
        if current_quality != baseline_quality:
            # A mixed quality trade-off is neither compliance-only nor neutral.
            # Keep it visible without inventing a scalar ordering over the
            # three prospectively frozen correctness components.
            return "quality_changed"
        current_metrics = current_eval.get("metrics") or {}
        baseline_metrics = baseline_eval.get("metrics") or {}
        if int(current_metrics.get("disclaimer_count", 0) or 0) \
                > int(baseline_metrics.get("disclaimer_count", 0) or 0):
            return "defensive_disclaimer"
        current_value = row.get("value") if isinstance(row.get("value"), dict) else {}
        baseline_value = baseline.get("value") if isinstance(baseline.get("value"), dict) else {}
        compliance_growth = any((
            len(current_value.get("checks", [])) > len(baseline_value.get("checks", [])),
            len(current_value.get("limitations", [])) > len(baseline_value.get("limitations", [])),
            int(current_metrics.get("wrapper_count", 0) or 0)
            > int(baseline_metrics.get("wrapper_count", 0) or 0),
            int(current_metrics.get("assertion_count", 0) or 0)
            > int(baseline_metrics.get("assertion_count", 0) or 0),
            int(current_metrics.get("exception_count", 0) or 0)
            + int(current_metrics.get("retry_count", 0) or 0)
            > int(baseline_metrics.get("exception_count", 0) or 0)
            + int(baseline_metrics.get("retry_count", 0) or 0),
        ))
        if compliance_growth:
            return "compliance_only"
        return "neutral"

    baseline_by_cell = {
        (row.get("task_id"), row.get("generator_vendor")): row
        for row in code_initial if row.get("policy") == "P0"
    }

    def add_code_change_labels(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                **row,
                "change_label_vs_P0": code_change_label(
                    row, baseline_by_cell.get(
                        (row.get("task_id"), row.get("generator_vendor")), {}
                    ),
                ),
            }
            for row in rows
        ]

    code_initial = add_code_change_labels(code_initial)
    code_metrics = (
        "loc", "wrapper_count", "assertion_count", "exception_retry_count",
        "checks_count", "limitations_count", "disclaimer_count", "words", "bytes",
        "static_ok", "visible_correct", "held_out_correct",
    )
    code_loops = [e for e in events if e.get("kind") == "defensive_code_loop_end"]
    code_by_artifact = {row.get("artifact_id"): row for row in events
                        if row.get("kind") == "defensive_code_artifact"}
    code_final = [
        {**code_by_artifact.get(loop.get("final_artifact_id"), {}),
         "task_id": loop.get("task_id"), "generator_vendor": loop.get("generator_vendor"),
         "policy": loop.get("policy")}
        for loop in code_loops
    ]
    code_final = add_code_change_labels(code_final)
    code_final_by_policy: dict[str, Any] = {}
    for policy in ("P0", "P1", "P2"):
        arm = [row for row in code_loops if row.get("policy") == policy]
        code_final_by_policy[policy] = {
            "n_sessions_ITT": len(arm),
            "held_out_correct_rate_ITT": _mean(int(bool(row.get("final_held_out_correct"))) for row in arm),
            "visible_correct_rate_ITT": _mean(int(bool(row.get("final_visible_correct"))) for row in arm),
            "static_ok_rate_ITT": _mean(int(bool(row.get("final_static_ok"))) for row in arm),
            "revisions": _descriptive(int(row.get("revisions", 0)) for row in arm),
        }
    return {
        "research_artefact_policy_arms": {
            "initial_anticipatory": {
                "arm_descriptives": _arm_task_means(text_initial, text_get, TEXT_METRICS),
                "task_clustered_policy_contrasts": _defensive_contrasts(
                    text_initial, text_get, TEXT_METRICS, 800,
                ),
                "change_labels_vs_P0": _change_label_summary(text_initial, seed=820),
            },
            "delivered_final_primary": {
                "arm_descriptives": _arm_task_means(text_final, text_get, TEXT_METRICS),
                "task_clustered_policy_contrasts": _defensive_contrasts(
                    text_final, text_get, TEXT_METRICS, 850,
                ),
                "change_labels_vs_P0": _change_label_summary(text_final, seed=870),
            },
            "bounded_loop_by_policy": _bounded_loop_summary(text_loops),
            "label_note": (
                "P0 self-comparisons are excluded. Labels are deterministic proxies in this cohort; confirmatory "
                "compliance-only and harmful labels require blinded human change adjudication."
            ),
            "resource_use_by_policy": _policy_resources(events, "defensive_text"),
        },
        "scientific_python_policy_arms": {
            "initial_anticipatory": {
                "arm_descriptives": _arm_task_means(code_initial, code_get, code_metrics),
                "task_clustered_policy_contrasts": _defensive_contrasts(
                    code_initial, code_get, code_metrics, 900,
                ),
            },
            "delivered_final_primary": {
                "arm_descriptives": _arm_task_means(code_final, code_get, code_metrics),
                "task_clustered_policy_contrasts": _defensive_contrasts(
                    code_final, code_get, code_metrics, 950,
                ),
                "quality_by_policy": code_final_by_policy,
                "change_labels_vs_P0": _change_label_summary(code_final, seed=970),
            },
            "bounded_loop_by_policy": _bounded_loop_summary(code_loops),
            "initial_change_labels_vs_P0": _change_label_summary(code_initial, seed=920),
            "resource_use_by_policy": _policy_resources(events, "defensive_code"),
            "safety_note": (
                "Generated code is accepted by a strict AST allow-list before execution against "
                "deterministic visible and held-out fixtures; imports, attributes, dynamic calls, "
                "classes and exception wrappers fail closed."
            ),
        },
        "registered_interpretation": (
            "Defensive production requires compliance/disclaimer/wrapper overhead without a "
            "commensurate held-out quality gain; length alone is not evidence."
        ),
    }


def _whole_loop_summary(events: list[dict[str, Any]], design: dict[str, Any]) -> dict[str, Any]:
    rows = [dict(e) for e in events if e.get("kind") == "whole_loop_end"]
    calls_by_branch: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        metadata = event.get("metadata") or {}
        if event.get("kind") == "call_complete" and metadata.get("module") == "whole_loop":
            calls_by_branch[str(metadata.get("branch_id"))].append(event)
    for row in rows:
        row["fraction_initial_resolved_ITT"] = float(
            row.get("fraction_initial_resolved_ITT", 0.0)
        )
        row["new_defect_any"] = (
            int(row["new_defect_count"] > 0)
            if isinstance(row.get("new_defect_count"), int) else None
        )
        row["unnecessary_change_any"] = (
            int(bool(row["unnecessary_changed_fields"]))
            if isinstance(row.get("unnecessary_changed_fields"), list) else None
        )
        branch_calls = calls_by_branch.get(row["branch_id"], [])
        row["incremental_calls"] = len(branch_calls)
        row["known_incremental_cost_usd"] = sum(
            float(e["cost_usd"]) for e in branch_calls
            if isinstance(e.get("cost_usd"), (int, float))
        )
        row["unknown_cost_calls"] = sum(
            bool(e.get("provider_invoked")) and e.get("cost_usd") is None
            for e in branch_calls
        )
        row["incremental_total_cost_usd"] = (
            row["known_incremental_cost_usd"]
            if row["unknown_cost_calls"] == 0 else None
        )
        row["incremental_latency_seconds"] = sum(
            float(e.get("elapsed_seconds", 0.0)) for e in branch_calls
        )
    metrics = (
        "fraction_initial_resolved_ITT", "final_acceptable", "new_defect_any",
        "unnecessary_change_any", "revisions", "incremental_calls",
        "known_incremental_cost_usd", "unknown_cost_calls",
        "incremental_total_cost_usd", "incremental_latency_seconds",
    )
    by_assignment: dict[str, Any] = {}
    for assignment in ("same", "cross"):
        arm = [r for r in rows if r.get("assignment") == assignment]
        by_assignment[assignment] = {
            "n_branches": len(arm),
            **{
                metric: {
                    **_descriptive(r[metric] for r in arm if r.get(metric) is not None),
                    "n_missing": sum(r.get(metric) is None for r in arm),
                }
                for metric in metrics
            },
        }
    expected_tasks = [str(value) for value in design.get("task_ids", [])]
    required_per_assignment = len(design.get("generator_vendors", []))
    contrasts = {
        metric: _paired_task_contrast(
            rows, factor="assignment", low="same", high="cross", outcome=metric,
            seed=1200 + i, expected_clusters=expected_tasks,
            required_rows_per_level=required_per_assignment,
        ) for i, metric in enumerate(metrics)
    }
    return {
        "by_assignment": by_assignment,
        "cross_minus_same_task_clustered": contrasts,
        "n_seeded_branches": len(rows),
        "expected_complete_branches": (
            len(design.get("task_ids", []))
            * len(design.get("generator_vendors", []))
            * len(design.get("auditor_vendors", []))
        ),
        "warning": (
            "Every seeded sibling enters both same and cross branches, but repair/new-change "
            "labels use deterministic micro-task fields rather than blinded human adjudication. "
            "Unavailable seeded/final artefacts score zero repair and final acceptability under "
            "ITT; new-defect and unnecessary-change harm are explicitly unknown. Contrasts "
            "require every frozen generator branch in both assignments, so partial cells are "
            "never silently reweighted. Resource totals are incremental after the C2 repeat-0 "
            "audit reused from the core."
        ),
    }


def _ledger_review_value(event: dict[str, Any]) -> dict[str, Any] | None:
    """Read only a runner-validated, complete ledger review value."""
    required = {
        "accept", "accept_probability", "tamper_detected", "tamper_probability",
        "origin_round", "first_defective_round", "rule_version",
        "insufficient_evidence",
    }
    value = event.get("review")
    if (event.get("status") != "valid"
            or event.get("review_schema_valid") is not True
            or not isinstance(value, dict)):
        return None
    if set(value) != required:
        return None
    if type(value["accept"]) is not bool:
        return None
    if type(value["tamper_detected"]) is not bool:
        return None
    if type(value["insufficient_evidence"]) is not bool:
        return None
    for field in ("accept_probability", "tamper_probability"):
        probability = value[field]
        if type(probability) not in (int, float):
            return None
        if not math.isfinite(float(probability)) or not 0 <= probability <= 1:
            return None
    for field in ("origin_round", "first_defective_round"):
        round_no = value[field]
        if round_no is not None and (type(round_no) is not int or round_no < 0):
            return None
    if value["rule_version"] is not None and type(value["rule_version"]) is not str:
        return None
    return value


def _ledger_cell_summary(
    rows: list[dict[str, Any]], truth: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    reviews = [(row, review) for row in rows
               if (review := _ledger_review_value(row)) is not None]

    def brier(probability_field: str, truth_field: str) -> float | None:
        values: list[float] = []
        for row in rows:
            review = _ledger_review_value(row)
            episode_truth = truth.get(str(row.get("episode_id")))
            if review is None or not isinstance(episode_truth, dict):
                values.append(1.0)
            else:
                target = int(bool(episode_truth[truth_field]))
                values.append((float(review[probability_field]) - target) ** 2)
        return _mean(values)

    raw_latency = [float(row.get("elapsed_seconds", 0.0)) for row in rows]
    invoked_latency = [
        float(row.get("elapsed_seconds", 0.0)) for row in rows
        if row.get("provider_invoked") is True
    ]
    decision_time = [
        float(row.get("elapsed_seconds", 0.0))
        if _ledger_review_value(row) is not None and row.get("correct_accept") == 1
        else LEDGER_DECISION_TIME_CAP_SECONDS
        for row in rows
    ]
    summary = {
        "n_proxy_reviews_ITT": len(rows),
        "n_schema_valid_review_values": len(reviews),
        "n_missing_or_invalid_review_values": len(rows) - len(reviews),
        "provider_failure_rate_ITT": _mean(int(row.get("status") != "valid") for row in rows),
        "accept_accuracy_ITT": _mean(int(row.get("correct_accept") == 1) for row in rows),
        "tamper_accuracy_ITT": _mean(int(row.get("correct_tamper") == 1) for row in rows),
        "origin_round_accuracy_ITT": _mean(
            int(row.get("correct_origin") == 1) for row in rows
        ),
        "first_defective_round_accuracy_ITT": _mean(
            int(row.get("correct_first_defective") == 1) for row in rows
        ),
        "round_pair_accuracy_ITT": _mean(
            int(row.get("correct_rounds") == 1) for row in rows
        ),
        "rule_accuracy_ITT": _mean(int(row.get("correct_rule") == 1) for row in rows),
        "insufficient_evidence_rate_ITT": _mean(
            int(review["insufficient_evidence"]) if review is not None else 0
            for row in rows for review in [_ledger_review_value(row)]
        ),
        "insufficient_evidence_rate_valid_reviews": _mean(
            int(review["insufficient_evidence"]) for _, review in reviews
        ),
        "accept_probability_brier_ITT": brier("accept_probability", "accept"),
        "tamper_probability_brier_ITT": brier("tamper_probability", "tamper_truth"),
        "reported_accept_rate_valid_reviews": _mean(
            int(review["accept"]) for _, review in reviews
        ),
        "reported_tamper_rate_valid_reviews": _mean(
            int(review["tamper_detected"]) for _, review in reviews
        ),
        "accept_probability_valid_reviews": _descriptive(
            review["accept_probability"] for _, review in reviews
        ),
        "tamper_probability_valid_reviews": _descriptive(
            review["tamper_probability"] for _, review in reviews
        ),
        "raw_latency_seconds_ITT_including_blocked_zero": _descriptive(raw_latency),
        "provider_invoked_latency_seconds": _descriptive(invoked_latency),
        "decision_time_capped_seconds": _descriptive(decision_time),
        "resources": {
            "provider_invocations": sum(row.get("provider_invoked") is True for row in rows),
            "known_cost_usd": round(sum(
                float(row["cost_usd"]) for row in rows
                if isinstance(row.get("cost_usd"), (int, float))
            ), 9),
            "unknown_cost_calls": sum(
                row.get("provider_invoked") is True and row.get("cost_usd") is None
                for row in rows
            ),
            **{
                field: sum(int((row.get("usage") or {}).get(field, 0) or 0) for row in rows)
                for field in USAGE_TOKEN_FIELDS
            },
        },
    }
    # Compatibility label retained for the attack-by-interface matrix.  The
    # canonical key above makes the ITT zero convention explicit.
    summary["raw_latency_seconds"] = summary[
        "raw_latency_seconds_ITT_including_blocked_zero"
    ]
    return summary


def _ledger_summary(events: list[dict[str, Any]]) -> dict[str, Any]:
    raw_outcomes = [e for e in events if e.get("kind") == "ledger_outcome"]
    completions = {
        e.get("call_id"): e for e in events if e.get("kind") == "call_complete"
    }
    truth = {e["episode_id"]: e["truth"] for e in events if e.get("kind") == "ledger_truth"}
    outcomes: list[dict[str, Any]] = []
    for raw in raw_outcomes:
        row = dict(raw)
        completion = completions.get(row.get("call_id")) or {}
        row.update({
            "provider_invoked": completion.get("provider_invoked"),
            "usage": completion.get("usage"),
            "cost_usd": completion.get("cost_usd"),
            "invoked_elapsed_seconds": (
                completion.get("elapsed_seconds")
                if completion.get("provider_invoked") is True else None
            ),
        })
        review = _ledger_review_value(row)
        episode_truth = truth.get(str(row.get("episode_id")), {})
        row["decision_time_capped"] = (
            float(row.get("elapsed_seconds", 0.0))
            if review is not None and row.get("correct_accept") == 1
            else LEDGER_DECISION_TIME_CAP_SECONDS
        )
        row["accept_probability_brier"] = (
            (float(review["accept_probability"]) - int(bool(episode_truth.get("accept")))) ** 2
            if review is not None and episode_truth else 1.0
        )
        row["tamper_probability_brier"] = (
            (float(review["tamper_probability"]) - int(bool(episode_truth.get("tamper_truth")))) ** 2
            if review is not None and episode_truth else 1.0
        )
        outcomes.append(row)
    metrics = (
        "correct_accept", "correct_tamper", "correct_origin",
        "correct_first_defective", "correct_rounds", "correct_rule",
    )
    by_interface: dict[str, Any] = {}
    for interface in ("E0", "E1", "E2"):
        rows = [e for e in outcomes if e.get("interface") == interface]
        cell = _ledger_cell_summary(rows, truth)
        # Keep the earlier interface-level names while the detailed keys make
        # the ITT and valid-review denominators explicit.
        cell.update({
            **{metric: _mean(e.get(metric, 0) for e in rows) for metric in metrics},
            "n_proxy_reviews": len(rows),
            "latency_seconds_ITT_including_blocked_zero": (
                cell["raw_latency_seconds_ITT_including_blocked_zero"]
            ),
            "insufficient_evidence_rate": cell["insufficient_evidence_rate_valid_reviews"],
            "reported_accept_rate": cell["reported_accept_rate_valid_reviews"],
            "reported_tamper_detected_rate": cell["reported_tamper_rate_valid_reviews"],
        })
        by_interface[interface] = cell
    by_attack_and_interface: dict[str, Any] = {}
    for attack in LEDGER_ATTACKS:
        episode_ids = {
            episode_id for episode_id, episode_truth in truth.items()
            if episode_truth.get("attack") == attack
        }
        by_attack_and_interface[attack] = {
            interface: _ledger_cell_summary(
                [e for e in outcomes if e.get("episode_id") in episode_ids
                 and e.get("interface") == interface],
                truth,
            )
            for interface in ("E0", "E1", "E2")
        }
    contrasts = {}
    for metric in (
        *metrics, "decision_time_capped", "elapsed_seconds", "invoked_elapsed_seconds",
        "accept_probability_brier", "tamper_probability_brier",
    ):
        contrast_kwargs = {
            "cluster_field": "episode_id",
            "expected_clusters": truth.keys(),
            "required_rows_per_level": 2,
        }
        contrasts[metric] = {
            "E2_minus_E0": _paired_task_contrast(
                outcomes, factor="interface", low="E0", high="E2", outcome=metric,
                seed=1000 + len(metric), **contrast_kwargs,
            ),
            "E2_minus_E1": _paired_task_contrast(
                outcomes, factor="interface", low="E1", high="E2", outcome=metric,
                seed=1100 + len(metric), **contrast_kwargs,
            ),
            "E1_minus_E0": _paired_task_contrast(
                outcomes, factor="interface", low="E0", high="E1", outcome=metric,
                seed=1200 + len(metric), **contrast_kwargs,
            ),
        }
    attacks = Counter(v["attack"] for v in truth.values())
    per_session_episode = Counter((e.get("reviewer_session"), e.get("episode_id")) for e in outcomes)
    interface_by_config = {
        vendor: dict(sorted(Counter(e["interface"] for e in outcomes
                                    if e.get("reviewer_vendor") == vendor).items()))
        for vendor in sorted({str(e.get("reviewer_vendor")) for e in outcomes})
    }
    return {
        "interfaces": by_interface,
        "episode_clustered_proxy_contrasts": contrasts,
        "by_attack_and_interface_ITT": by_attack_and_interface,
        "attack_counts": dict(sorted(attacks.items())),
        "decision_time_cap_seconds": LEDGER_DECISION_TIME_CAP_SECONDS,
        "review_value_note": (
            "All correctness and Brier cells are intention-to-treat. Invalid/missing reviews "
            "score zero correctness and Brier 1.0; their absent insufficient-evidence flag "
            "scores zero and is also reported separately from the valid-review rate. Raw "
            "ITT raw latency includes deterministic zeroes for non-invoked blocked cells and is "
            "therefore never presented as provider speed; provider-invoked latency is separate. "
            "Decision time uses elapsed seconds only for a schema-valid "
            "correct accept/reject decision and otherwise uses the frozen 300-second cap."
        ),
        "allocation_check": {
            "proxy_session_episode_cells_with_multiple_surfaces": sum(
                count > 1 for count in per_session_episode.values()
            ),
            "interface_counts_by_pinned_configuration": interface_by_config,
            "note": (
                "Each named proxy block receives one surface per episode. Three fresh blocks "
                "replicate each pinned configuration, so configuration is not treated as a "
                "persistent reviewer identity."
            ),
        },
        "warning": (
            "These are fresh model sessions acting as reviewer proxies over deterministic "
            "episodes. They do not replace the registered blinded human ledger study; provider "
            "latency is only a reconstruction-time proxy. Each attack has one episode and is "
            "therefore confounded with its episode/task; attack-specific cells are descriptive "
            "diagnostics and cannot estimate an attack-class effect."
        ),
    }


def build_summary(manifest: dict[str, Any], events: list[dict[str, Any]]) -> dict[str, Any]:
    kinds = Counter(e.get("kind", "missing") for e in events)
    frozen_core = manifest.get("frozen_core")
    frozen_core_valid = (
        isinstance(frozen_core, dict) and _digest(frozen_core) == manifest.get("freeze_sha256")
    )
    if not frozen_core_valid:
        frozen_core = {}
    design = frozen_core.get("design", {})
    structure = validate_structure(events, frozen_core if frozen_core_valid else None)
    summary: dict[str, Any] = {
        "format_version": manifest.get("format_version"),
        "freeze_sha256": manifest.get("freeze_sha256"),
        "claim_status": manifest.get("claim_status"),
        "schedule_finished": structure["valid"],
        "structural_completion": structure,
        "journal_integrity": {
            "hash_chain_validated": True,
            "manifest_frozen_core_hash_validated": frozen_core_valid,
            "final_event_sha256": events[-1].get("event_sha256") if events else None,
        },
        "event_counts": dict(sorted(kinds.items())),
        "execution": _execution_summary(events),
        "scientific_outputs_withheld": not structure["valid"],
        "mandatory_caveats": [
            "This is an execution-feasibility cohort, not the registered confirmatory v4 sample.",
            "At most six deterministic convenience tasks cannot support general product or vendor claims.",
            "The two labels refer to pinned CLI/model configurations, not random samples of vendors.",
            "Natural outputs, deterministic clean repairs, single seeded defects and unusual-but-correct controls have different construction mechanisms and are reported separately.",
            "Provider/parse/timeout/interruption/upstream/budget failures remain incorrect intention-to-treat observations.",
            "The micro-task gold checker and offline DCL are the same implementation, so DCL-only accuracy is a harness ceiling check.",
            "Ledger reviewers are model proxies and provider latency is not human review time.",
            "All task-cluster intervals are descriptive and highly unstable at this sample size.",
        ],
    }
    if not structure["valid"]:
        summary["withholding_reason"] = (
            "Scientific endpoints are omitted because fail-closed structural/semantic "
            "validation did not pass. Execution health remains available for diagnosis."
        )
        return summary
    summary.update({
        "core_2x2_and_ablations": _core_summary(events, design),
        "whole_loop_seeded_same_cross": _whole_loop_summary(events, design),
        "defensive_production": _defensive_summary(events),
        "ledger_proxy_pilot": _ledger_summary(events),
    })
    return summary


def _analysis_static(summary_raw: bytes, summary: dict[str, Any],
                     anchors: dict[str, str], snapshot_hashes: dict[str, str]) -> dict[str, Any]:
    return {
        "format_version": "v4-feasibility-analysis-receipt-1",
        "freeze_sha256": summary.get("freeze_sha256"),
        "cohort_seal_bytes_sha256": snapshot_hashes[SEAL_FILENAME],
        "summary_bytes_sha256": hashlib.sha256(summary_raw).hexdigest(),
        "pre_analysis_freeze_commit": anchors["freeze_commit"],
        "pre_dispatch_network_tip": anchors["network_remote_tip_at_start"],
        "pre_analysis_seal_commit": anchors["seal_commit"],
        "schedule_finished": bool(summary.get("schedule_finished")),
        "scientific_outputs_withheld": bool(summary.get("scientific_outputs_withheld")),
        "claim_boundary": summary.get("claim_status"),
    }


def _validate_analysis_receipt(
    receipt: dict[str, Any], static: dict[str, Any], current_remote_tip: str,
) -> None:
    if not isinstance(receipt, dict) or set(receipt) != ANALYSIS_RECEIPT_FIELDS:
        raise ValueError("analysis receipt has unexpected or missing fields")
    unsigned = {key: value for key, value in receipt.items() if key != "receipt_sha256"}
    if receipt.get("receipt_sha256") != _digest(unsigned):
        raise ValueError("analysis receipt self-hash is invalid")
    if {key: receipt.get(key) for key in static} != static:
        raise ValueError("analysis receipt differs from the current sealed analysis")
    if not isinstance(receipt.get("created_utc"), str) or not receipt["created_utc"]:
        raise ValueError("analysis receipt lacks its creation time")
    historical_tip = receipt.get("network_remote_tip_at_analysis")
    if not isinstance(historical_tip, str) or not re.fullmatch(
        r"[0-9a-fA-F]{40,64}", historical_tip,
    ):
        raise ValueError("analysis receipt has an invalid historical remote tip")
    if historical_tip != current_remote_tip:
        if _git("cat-file", "-e", f"{historical_tip}^{{commit}}", check=False).returncode:
            raise ValueError("analysis receipt historical remote tip is unavailable locally")
        seal_commit = static["pre_analysis_seal_commit"]
        if _git("cat-file", "-e", f"{seal_commit}^{{commit}}", check=False).returncode:
            raise ValueError("analysis receipt seal commit is unavailable locally")
        if _git(
            "merge-base", "--is-ancestor", seal_commit, historical_tip, check=False,
        ).returncode:
            raise ValueError("first-analysis remote tip does not contain the cohort seal")
        if _git(
            "merge-base", "--is-ancestor", historical_tip, current_remote_tip,
            check=False,
        ).returncode:
            raise ValueError("current remote tip does not descend from the first-analysis tip")


def score_run(run_dir: Path) -> dict[str, Any]:
    resolved = run_dir.resolve()
    with _result_lock(resolved):
        manifest, events, snapshot_hashes = load_event_snapshot(resolved)
        seal_path = resolved / SEAL_FILENAME
        if not seal_path.is_file() or seal_path.is_symlink():
            raise ValueError(f"{SEAL_FILENAME} must be a regular non-symlink file")
        seal_raw = seal_path.read_bytes()
        snapshot_hashes[SEAL_FILENAME] = hashlib.sha256(seal_raw).hexdigest()
        _validate_local_seal(
            resolved, manifest, events, seal_raw=seal_raw,
            snapshot_hashes=snapshot_hashes,
        )
        # This network check occurs before build_summary, so the process cannot
        # calculate or print scientific endpoints from an unanchored journal.
        anchors = verify_cohort_seal_committed_and_pushed(resolved, snapshot_hashes)
        _assert_snapshot_unchanged(resolved, snapshot_hashes)
        summary_path = resolved / "summary.json"
        receipt_path = resolved / ANALYSIS_RECEIPT_FILENAME
        if summary_path.is_symlink() or receipt_path.is_symlink():
            raise ValueError("analysis artefacts must be regular non-symlink files")
        if summary_path.exists() and not receipt_path.exists():
            raise ValueError(
                "orphan summary without an analysis receipt; remove the untrusted "
                "deterministic orphan before scoring"
            )
        summary = build_summary(manifest, events)
        summary_raw = (json.dumps(
            summary, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False,
        ) + "\n").encode("utf-8")
        static = _analysis_static(summary_raw, summary, anchors, snapshot_hashes)

        if summary_path.exists() and summary_path.read_bytes() != summary_raw:
            raise ValueError("existing summary differs; refusing to overwrite it")
        if receipt_path.exists():
            _validate_analysis_receipt(
                json.loads(receipt_path.read_text()), static,
                anchors["network_remote_tip"],
            )
        else:
            receipt = {
                **static,
                "network_remote_tip_at_analysis": anchors["network_remote_tip"],
                "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "note": (
                    "Scientific analysis was generated only after the outcome-free cohort seal, "
                    "manifest and journal were verified on the network upstream."
                ),
            }
            receipt["receipt_sha256"] = _digest(receipt)
            # Receipt-first ordering makes a crash resumable without ever
            # accepting a summary that lacks evidence of post-anchor scoring.
            _atomic_json(receipt_path, receipt)
        _assert_snapshot_unchanged(resolved, snapshot_hashes)
        if not summary_path.exists():
            _atomic_bytes(summary_path, summary_raw)
        _assert_snapshot_unchanged(resolved, snapshot_hashes)
        return summary


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("run_dir", type=Path)
    ap.add_argument(
        "--seal-only", action="store_true",
        help="validate and write an outcome-free seal without calculating endpoints",
    )
    args = ap.parse_args(argv)
    if args.seal_only:
        seal = seal_run(args.run_dir)
        print(json.dumps({
            "seal_path": str(args.run_dir / SEAL_FILENAME),
            "seal_sha256": seal["seal_sha256"],
            "next": "commit and push the seal, manifest and journal before scoring",
        }, indent=2, sort_keys=True, ensure_ascii=False))
        return 0
    print(json.dumps(score_run(args.run_dir), indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
