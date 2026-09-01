from __future__ import annotations

import ast
import hashlib
import inspect
import json
import os
import select
import subprocess
import sys
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from experiment.v4.feasibility import providers as provider_module
from experiment.v4.feasibility import run as run_module
from experiment.v4.feasibility.run import (
    ARTIFACT_SCHEMA,
    AUDIT_SCHEMA,
    CODE_SCHEMA,
    CODE_TASKS,
    LEDGER_REVIEW_SCHEMA,
    CallRunner,
    Journal,
    audit_gate,
    build_freeze_core,
    call_cost,
    evaluate_code_artifact,
    make_freeze,
    normalise_usage,
    planned_calls,
    run_study,
    validate_freeze_document,
    verify_freeze_committed_and_pushed,
)
from experiment.v4.feasibility.tasks import TASKS, clean_control, validate_artifact


@dataclass(frozen=True)
class FakeProvider:
    vendor: str
    model: str
    cli: str = "fake"

    def _task(self, prompt: str):
        return next(task for task in TASKS if task.task_id in prompt or task.brief in prompt)

    def call(self, *, prompt: str, schema: dict[str, Any], role: str,
             timeout: int = 300) -> dict[str, Any]:
        if schema == ARTIFACT_SCHEMA:
            task = self._task(prompt)
            value = clean_control(task, {})
        elif schema == AUDIT_SCHEMA:
            task = self._task(prompt)
            raw = prompt.split("Artefact:\n", 1)[1]
            artifact = ast.literal_eval(raw)
            defects = validate_artifact(task, artifact)
            findings = [
                {
                    "severity": "BLOCKER", "rule_id": f"F-{d['class'].upper()}-001",
                    "location": d["location"], "description": d["description"],
                    "confidence": 0.95,
                }
                for d in defects
            ]
            value = {
                "verdict": "BLOCK" if findings else "PASS", "confidence": 0.95,
                "checks_performed": ["deterministic recomputation"], "findings": findings,
            }
        elif schema == CODE_SCHEMA:
            if "F-CODE-01" in prompt:
                code = "def final_change(values):\n    return abs(values[-1] - values[-2])"
            else:
                code = (
                    "def exact_slope(points):\n"
                    "    return (points[-1][1] - points[0][1]) / "
                    "(points[-1][0] - points[0][0])"
                )
            value = {"code": code, "explanation": "direct formula",
                     "checks": ["visible fixture"], "limitations": []}
        elif schema == LEDGER_REVIEW_SCHEMA:
            # Structural mock only. The scoring test verifies ITT denominators,
            # not that this deliberately simple proxy is a good reviewer.
            value = {
                "accept": False, "origin_round": 1,
                "rule_version": "v4-feasibility-C2", "tamper_detected": False,
                "insufficient_evidence": "\"interface\":\"E0\"" in prompt,
                "confidence": 0.6,
            }
        else:  # pragma: no cover - a new schema must update the mock explicitly
            raise AssertionError("unexpected schema")
        response = {
            "status": "valid", "value": value,
            "usage": {"input_tokens": 10, "output_tokens": 5,
                      "cached_input_tokens": 0, "reasoning_tokens": 0},
            "models_observed": [self.model],
        }
        if self.vendor == "anthropic":
            response["list_cost_usd"] = 0.0001
            response["model_usage"] = {
                self.model: {"inputTokens": 10, "outputTokens": 5}
            }
        return response


def price_table(*providers: FakeProvider) -> dict[str, Any]:
    return {
        "currency": "USD",
        "prices": {
            f"{p.vendor}/{p.model}": {
                "input_per_million": 0.0,
                "cached_input_per_million": 0.0,
                "output_per_million": 0.0,
            }
            for p in providers
        },
    }


def frozen_one_task(providers: tuple[FakeProvider, FakeProvider]) -> dict[str, Any]:
    core = build_freeze_core(
        n_tasks=1, constitution_subset=1, seed=17, timeout=2,
        cost_cap_usd=10.0, per_call_reserve_usd=1.0,
        price_table=price_table(*providers), provider_list=providers,
        provider_caps_usd={p.vendor: 10.0 for p in providers},
        cli_versions={f"{p.vendor}/{p.model}": {"exit_code": 0, "stdout": "fake 1"}
                      for p in providers},
        runtime_bindings={
            f"{p.vendor}/{p.model}": {"test_runtime_binding": p.vendor}
            for p in providers
        },
    )
    return make_freeze(core)


def test_complete_mocked_feasibility_schedule_is_resumable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    providers = (
        FakeProvider("anthropic", "fake-a"),
        FakeProvider("openai", "fake-b"),
    )
    freeze = frozen_one_task(providers)
    monkeypatch.setattr(run_module, "rebuild_live_freeze_core", lambda frozen, _: frozen)
    monkeypatch.setattr(run_module, "verify_freeze_committed_and_pushed", lambda *_: None)
    monkeypatch.setattr(run_module, "verify_provider_runtime_binding", lambda *_: None)
    run_dir = tmp_path / "run"
    summary = run_study(
        freeze_doc=freeze, provider_list=providers, output_dir=run_dir,
    )

    events = [json.loads(line) for line in (run_dir / "events.jsonl").read_text().splitlines()]
    core_artifacts = [e for e in events if e.get("kind") == "artifact"
                      and e.get("module") == "core"]
    assert {e["artifact_type"] for e in core_artifacts} == {
        "natural", "clean", "seeded", "ambiguous",
    }
    assert len(core_artifacts) == 8  # four strata × two generator vendors

    c2_calls = [e for e in events if e.get("kind") == "call_complete"
                and e.get("role") == "auditor"
                and e["metadata"].get("constitution") == "C2"]
    assert len(c2_calls) == 48  # 8 artefacts × two auditors × three repeats
    assert {e["metadata"]["repeat"] for e in c2_calls} == {0, 1, 2}

    decisions = [e for e in events if e.get("kind") == "audit_decision"]
    assert {e["dcl_mode"] for e in decisions} == {
        "D0_OFF", "D1_ONLY", "D2_COMBINED_BLIND",
    }
    loops = [e for e in events if e.get("kind") == "whole_loop_end"]
    assert len(loops) == 4  # seeded output from two generators × same/cross branches
    assert {e["assignment"] for e in loops} == {"same", "cross"}
    assert all(e["final_acceptable"] == 1 for e in loops)
    assert all(e["revisions"] == 1 for e in loops)

    text_arms = [e for e in events if e.get("kind") == "defensive_loop_end"]
    assert {e["policy"] for e in text_arms} == {"P0", "P1", "P2"}
    code_arms = [e for e in events if e.get("kind") == "defensive_code_loop_end"]
    assert {e["policy"] for e in code_arms} == {"P0", "P1", "P2"}
    assert all(e["final_held_out_correct"] for e in code_arms)

    ledger = [e for e in events if e.get("kind") == "ledger_outcome"]
    assert len(ledger) == 12  # two episodes × 3 surfaces × 2 configurations
    seen = Counter((e["episode_id"], e["reviewer_session"]) for e in ledger)
    assert set(seen.values()) == {1}
    for episode_id in {e["episode_id"] for e in ledger}:
        for vendor in {e["reviewer_vendor"] for e in ledger}:
            assert {e["interface"] for e in ledger
                    if e["episode_id"] == episode_id and e["reviewer_vendor"] == vendor} \
                   == {"E0", "E1", "E2"}

    assert summary["claim_status"].startswith("execution-feasibility")
    assert summary["schedule_finished"] is True
    assert summary["journal_integrity"]["hash_chain_validated"] is True
    assert summary["journal_integrity"]["final_event_sha256"]
    assert summary["whole_loop_seeded_same_cross"]["n_seeded_branches"] == 4
    assert summary["core_2x2_and_ablations"]["finding_location_match_proxy"]
    before = (run_dir / "events.jsonl").read_bytes()
    second = run_study(
        freeze_doc=freeze, provider_list=providers, output_dir=run_dir,
    )
    assert (run_dir / "events.jsonl").read_bytes() == before
    assert second["event_counts"] == summary["event_counts"]

    tampered = events
    tampered[1]["kind"] = "changed"
    (run_dir / "events.jsonl").write_text(
        "".join(json.dumps(e, sort_keys=True) + "\n" for e in tampered)
    )
    with pytest.raises(ValueError, match="invalid event hash"):
        __import__("experiment.v4.feasibility.score", fromlist=["score_run"]).score_run(run_dir)


def test_generated_code_is_never_run_in_parent_and_fails_closed() -> None:
    spec = CODE_TASKS[0]
    valid = {"code": "def final_change(values):\n    return abs(values[-1] - values[-2])",
             "explanation": "formula", "checks": [], "limitations": []}
    assert evaluate_code_artifact(spec, valid)["held_out_correct"] is True

    started = time.monotonic()
    hanging = {"code": "def final_change(values):\n    while True:\n        pass",
               "explanation": "", "checks": [], "limitations": []}
    report = evaluate_code_artifact(spec, hanging)
    assert time.monotonic() - started < 1.0
    assert report["static_ok"] is False
    assert any("While" in error for error in report["errors"])

    importing = {"code": "import os\ndef final_change(values):\n    return 0",
                 "explanation": "", "checks": [], "limitations": []}
    assert any("Import" in error for error in evaluate_code_artifact(spec, importing)["errors"])


def test_usage_does_not_double_count_and_claude_list_cost_wins() -> None:
    response = {
        "usage": {"input_tokens": 10, "output_tokens": 4},
        "model_usage": {
            "main": {"inputTokens": 10, "outputTokens": 4},
            "helper": {"inputTokens": 3, "outputTokens": 2},
        },
        "list_cost_usd": 0.123,
    }
    usage = normalise_usage(response)
    assert usage["input_tokens"] == 10
    assert usage["output_tokens"] == 4
    assert usage["provenance"] == "top_level_usage"
    provider = FakeProvider("anthropic", "fake-a")
    cost, source = call_cost(provider, response, usage, price_table(provider))
    assert cost == 0.123
    assert source == "provider_list_cost_usd"


def test_unknown_cost_blocks_entire_cohort_and_keeps_itt_records(tmp_path: Path) -> None:
    class UnknownCost(FakeProvider):
        def call(self, **kwargs):
            return {"status": "valid", "value": {}, "usage": None}

    other_dispatches: list[dict[str, Any]] = []

    class MustNotDispatch(FakeProvider):
        def call(self, **kwargs):
            other_dispatches.append(kwargs)
            return super().call(**kwargs)

    a = UnknownCost("anthropic", "a")
    b = MustNotDispatch("openai", "b")
    prices = price_table(a, b)
    journal = Journal(tmp_path / "events.jsonl", "f" * 64)
    calls = CallRunner(journal, prices, cap=5, reserve=0.1, timeout=1,
                       provider_caps={"anthropic": 5, "openai": 5})
    first = calls.call(call_id="a1", provider=a, prompt="x", schema={}, role="x", metadata={})
    assert first["cost_usd"] is None
    same_vendor = calls.call(
        call_id="a2", provider=a, prompt="x", schema={}, role="x", metadata={},
    )
    other_vendor = calls.call(
        call_id="b1", provider=b, prompt="x", schema=LEDGER_REVIEW_SCHEMA,
        role="ledger_proxy_reviewer", metadata={},
    )

    for blocked in (same_vendor, other_vendor):
        assert blocked["status"] == "budget_unverifiable"
        assert blocked["provider_invoked"] is False
        assert blocked["cost_unverifiable"] is True
        assert blocked["budget_scope"] == "combined_cohort"
        assert blocked["blocking_unknown_cost_providers"] == ["anthropic"]
    assert other_dispatches == []
    assert journal.get("schedule:b1") is not None
    assert journal.get("complete:b1") == other_vendor


def test_secret_output_is_discarded_and_identity_drift_stops_dispatch(tmp_path: Path) -> None:
    class SecretProvider(FakeProvider):
        def call(self, **kwargs):
            return {
                "status": "valid", "value": {"leak": "sk-ant-abcdefghijklmnopqrstuvwxyz"},
                "usage": {"input_tokens": 1, "output_tokens": 1},
                "list_cost_usd": 0.01, "models_observed": [self.model],
            }

    secret = SecretProvider("anthropic", "a")
    other = FakeProvider("openai", "b")
    journal = Journal(tmp_path / "secret.jsonl", "a" * 64)
    calls = CallRunner(journal, price_table(secret, other), cap=5, reserve=0.1, timeout=1,
                       provider_caps={"anthropic": 5, "openai": 5})
    leaked = calls.call(call_id="leak", provider=secret, prompt="x", schema={}, role="x",
                        metadata={})
    assert leaked["status"] == "secret_output_quarantined"
    persisted = (tmp_path / "secret.jsonl").read_text()
    assert "sk-ant-abcdefghijklmnopqrstuvwxyz" not in persisted
    assert leaked["response"]["secret_pattern_labels"] == ["anthropic_key"]
    stopped = calls.call(call_id="later", provider=other, prompt="x", schema={}, role="x",
                         metadata={})
    assert stopped["status"] == "safety_stop_blocked"

    class DriftProvider(FakeProvider):
        def call(self, **kwargs):
            return {"status": "valid", "value": {},
                    "usage": {"input_tokens": 1, "output_tokens": 1},
                    "models_observed": ["unexpected-model"]}

    drift = DriftProvider("openai", "wanted-model")
    journal2 = Journal(tmp_path / "drift.jsonl", "b" * 64)
    calls2 = CallRunner(journal2, price_table(drift), cap=5, reserve=0.1, timeout=1,
                        provider_caps={"openai": 5})
    event = calls2.call(call_id="drift", provider=drift, prompt="x", schema={}, role="x",
                        metadata={})
    assert event["status"] == "model_identity_drift"
    assert event["identity_verified"] is False


def test_freeze_and_call_plan_are_fail_closed() -> None:
    providers = (FakeProvider("anthropic", "a"), FakeProvider("openai", "b"))
    freeze = frozen_one_task(providers)
    assert validate_freeze_document(freeze, freeze["frozen"]) == freeze["freeze_sha256"]
    changed = json.loads(json.dumps(freeze["frozen"]))
    changed["design"]["primary_audit_repeats"] = 2
    with pytest.raises(RuntimeError, match="differ"):
        validate_freeze_document(freeze, changed)
    assert planned_calls(6, 2)["maximum_total"] == 598
    assert freeze["frozen"]["claim_status"].startswith("execution-feasibility")
    assert set(freeze["frozen"]["protocol_document_hashes"]) == {
        "experiment/v4/FEASIBILITY-REGISTRATION.md",
        "experiment/v4/feasibility/CANARY-RECEIPT.json",
    }
    assert set(freeze["frozen"]["provider_runtime_bindings"]) == {
        "anthropic/a", "openai/b",
    }
    assert "enforce_git_freeze" not in inspect.signature(run_study).parameters


def test_run_rebuilds_complete_live_core_before_git_or_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    providers = (FakeProvider("anthropic", "a"), FakeProvider("openai", "b"))
    freeze = frozen_one_task(providers)
    changed = json.loads(json.dumps(freeze["frozen"]))
    changed["providers"][0]["model"] = "drifted"
    git_checks: list[bool] = []
    monkeypatch.setattr(run_module, "rebuild_live_freeze_core", lambda *_: changed)
    monkeypatch.setattr(
        run_module, "verify_freeze_committed_and_pushed", lambda *_: git_checks.append(True),
    )
    with pytest.raises(RuntimeError, match="differ"):
        run_study(
            freeze_doc=freeze, provider_list=providers, output_dir=tmp_path / "never-created",
        )
    assert git_checks == []
    assert not (tmp_path / "never-created").exists()


def test_cli_version_uses_restricted_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    cli = tmp_path / "cli"
    cli.write_bytes(b"binary")
    captured: dict[str, Any] = {}

    def fake_run(cmd, **kwargs):
        captured.update({"cmd": cmd, **kwargs})
        return SimpleNamespace(returncode=0, stdout="v1\n", stderr="")

    monkeypatch.setattr(run_module, "resolved_cli_path", lambda _: cli)
    monkeypatch.setattr(run_module, "safe_subprocess_env", lambda: {"PATH": "/bound"})
    monkeypatch.setattr(run_module.subprocess, "run", fake_run)
    assert run_module._cli_version(FakeProvider("anthropic", "a"))["stdout"] == "v1"
    assert captured["cmd"] == [str(cli), "--version"]
    assert captured["env"] == {"PATH": "/bound"}


def test_runtime_binding_hashes_paths_bytes_and_route_without_plaintext(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    cli = tmp_path / "codex.js"
    native = tmp_path / "codex-native"
    cli.write_bytes(b"launcher-v1")
    native.write_bytes(b"native-v1")
    monkeypatch.setattr(provider_module, "resolved_cli_path", lambda _: cli)
    monkeypatch.setattr(provider_module, "codex_native_binary", lambda _: native)
    monkeypatch.setenv("HTTPS_PROXY", "https://private-route.invalid:8443")
    provider = provider_module.Provider("openai", "m", "codex")
    binding = provider_module.provider_runtime_binding(provider)
    rendered = json.dumps(binding, sort_keys=True)
    assert "private-route.invalid" not in rendered
    assert binding["executables"]["cli"]["resolved_path"] == str(cli)
    assert binding["executables"]["cli"]["sha256"] == hashlib.sha256(b"launcher-v1").hexdigest()
    assert binding["executables"]["native"]["sha256"] == hashlib.sha256(b"native-v1").hexdigest()
    route = binding["security_route_environment"]["variables"]["HTTPS_PROXY"]
    assert route == {
        "present": True,
        "value_sha256": hashlib.sha256(b"https://private-route.invalid:8443").hexdigest(),
    }
    cli.write_bytes(b"launcher-v2")
    with pytest.raises(RuntimeError, match="runtime binding drift"):
        provider_module.verify_provider_runtime_binding(provider, binding)


def test_every_actual_dispatch_rechecks_runtime_binding(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = FakeProvider("openai", "b")
    checks: list[tuple[Any, Any]] = []
    monkeypatch.setattr(
        run_module, "verify_provider_runtime_binding",
        lambda observed, expected: checks.append((observed, expected)),
    )
    journal = Journal(tmp_path / "events.jsonl", "e" * 64)
    calls = CallRunner(
        journal, price_table(provider), cap=5, reserve=0.1, timeout=1,
        provider_caps={"openai": 5},
        provider_runtime_bindings={"openai/b": {"frozen": True}},
    )
    for call_id in ("one", "two"):
        result = calls.call(
            call_id=call_id, provider=provider, prompt='"interface":"E0"',
            schema=LEDGER_REVIEW_SCHEMA, role="ledger_proxy_reviewer", metadata={},
        )
        assert result["provider_invoked"] is True
    assert checks == [(provider, {"frozen": True}), (provider, {"frozen": True})]


def test_network_upstream_is_required_and_ls_remote_is_authoritative(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    freeze_path = tmp_path / "FREEZE.json"
    freeze_path.write_text("{}\n")
    monkeypatch.setattr(run_module, "REPO_ROOT", tmp_path)
    freeze_commit = "a" * 40
    remote_tip = "b" * 40
    calls: list[list[str]] = []
    remote_url = {"value": "file:///tmp/not-a-network-remote"}

    def completed(cmd, returncode=0, stdout="", stderr=""):
        return SimpleNamespace(returncode=returncode, stdout=stdout, stderr=stderr)

    def fake_run(cmd, **kwargs):
        argv = [str(x) for x in cmd]
        calls.append(argv)
        args = argv[1:]
        if args[:1] == ["ls-files"]:
            return completed(argv)
        if args[:2] == ["status", "--porcelain"]:
            return completed(argv)
        if args[:2] == ["log", "-1"]:
            return completed(argv, stdout=freeze_commit + "\n")
        if args[:2] == ["rev-parse", "--verify"]:
            return completed(argv, stdout=remote_tip + "\n")
        if args[:1] == ["merge-base"] or args[:1] == ["cat-file"]:
            return completed(argv)
        if args[:2] == ["symbolic-ref", "--quiet"]:
            return completed(argv, stdout="main\n")
        if args[:3] == ["config", "--get", "branch.main.remote"]:
            return completed(argv, stdout="origin\n")
        if args[:3] == ["config", "--get", "branch.main.merge"]:
            return completed(argv, stdout="refs/heads/main\n")
        if args[:3] == ["remote", "get-url", "origin"]:
            return completed(argv, stdout=remote_url["value"] + "\n")
        if args[:2] == ["ls-remote", "--exit-code"]:
            return completed(argv, stdout=f"{remote_tip}\trefs/heads/main\n")
        raise AssertionError(f"unexpected subprocess: {argv}")

    monkeypatch.setattr(run_module.subprocess, "run", fake_run)
    with pytest.raises(RuntimeError, match="non-file network"):
        verify_freeze_committed_and_pushed(freeze_path)
    assert not any(cmd[1:3] == ["ls-remote", "--exit-code"] for cmd in calls)

    calls.clear()
    remote_url["value"] = "https://github.com/example/crossaudit.git"
    verify_freeze_committed_and_pushed(freeze_path)
    network_calls = [cmd for cmd in calls if cmd[1:3] == ["ls-remote", "--exit-code"]]
    assert network_calls == [[
        "git", "ls-remote", "--exit-code", remote_url["value"], "refs/heads/main",
    ]]


def test_provider_commands_enforce_empty_tools_and_no_subprocess(monkeypatch, tmp_path: Path) -> None:
    captured: list[list[str]] = []

    def fake_run(cmd, **kwargs):
        captured.append([str(x) for x in cmd])
        if "claude" in str(cmd[0]):
            stdout = json.dumps({"structured_output": {}, "usage": {}, "modelUsage": {}})
        else:
            stdout = "\n".join([
                json.dumps({"type": "thread.started", "thread_id": "t"}),
                json.dumps({"type": "item.completed",
                            "item": {"type": "agent_message", "text": "{}"}}),
                json.dumps({"type": "turn.completed",
                            "usage": {"input_tokens": 1, "output_tokens": 1}}),
            ])
        return SimpleNamespace(returncode=0, stdout=stdout, stderr="")

    monkeypatch.setattr(provider_module.subprocess, "run", fake_run)
    anthropic = provider_module.Provider("anthropic", "m", "claude")
    anthropic._anthropic(tmp_path, "p", {}, "r", 1)
    anthropic_cmd = captured[-1]
    assert anthropic_cmd[anthropic_cmd.index("--tools") + 1] == ""
    assert anthropic_cmd[anthropic_cmd.index("--max-budget-usd") + 1] == "1.0"
    assert "--strict-mcp-config" in anthropic_cmd
    assert anthropic_cmd[anthropic_cmd.index("--mcp-config") + 1] == '{"mcpServers":{}}'

    native = tmp_path / "codex-native"
    native.write_text("")
    monkeypatch.setattr(provider_module, "codex_native_binary", lambda _: native)
    monkeypatch.setattr(provider_module.Path, "is_file", lambda self: True)
    openai = provider_module.Provider("openai", "m", "codex")
    openai._openai(tmp_path, "p", {}, "r", 1)
    openai_cmd = captured[-1]
    assert openai_cmd[0] == "/usr/bin/sandbox-exec"
    profile = openai_cmd[openai_cmd.index("-p") + 1]
    assert "(deny process-exec)" in profile
    assert f'(allow process-exec (literal "{native}"))' in profile
    assert openai_cmd[openai_cmd.index("--sandbox") + 1] == "read-only"


def test_second_process_cannot_open_or_dispatch_same_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A process holding the output flock excludes a complete second runner."""
    run_dir = tmp_path / "locked-run"
    repo = Path(__file__).resolve().parents[1]
    holder = (
        "import sys\n"
        "from pathlib import Path\n"
        "from experiment.v4.feasibility.run import exclusive_output_lock\n"
        "with exclusive_output_lock(Path(sys.argv[1])):\n"
        "    print('LOCKED', flush=True)\n"
        "    sys.stdin.readline()\n"
    )
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(
        [str(repo), str(repo / "src"), env.get("PYTHONPATH", "")]
    )
    proc = subprocess.Popen(
        [sys.executable, "-c", holder, str(run_dir)], cwd=repo, env=env,
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True,
    )
    try:
        ready, _, _ = select.select([proc.stdout], [], [], 5)
        assert ready, proc.stderr.read()
        assert proc.stdout.readline().strip() == "LOCKED"

        @dataclass(frozen=True)
        class NoDispatchProvider(FakeProvider):
            def call(self, **kwargs):  # pragma: no cover - lock must prevent this
                raise AssertionError("provider dispatch occurred while output was locked")

        providers = (
            NoDispatchProvider("anthropic", "fake-a"),
            NoDispatchProvider("openai", "fake-b"),
        )
        freeze = frozen_one_task(providers)
        monkeypatch.setattr(run_module, "rebuild_live_freeze_core", lambda frozen, _: frozen)
        monkeypatch.setattr(run_module, "verify_freeze_committed_and_pushed", lambda *_: None)
        with pytest.raises(RuntimeError, match="locked by another feasibility process"):
            run_study(
                freeze_doc=freeze, provider_list=providers, output_dir=run_dir,
            )
        assert not (run_dir / "run_manifest.json").exists()
        assert not (run_dir / "events.jsonl").exists()
    finally:
        if proc.stdin:
            proc.stdin.write("\n")
            proc.stdin.flush()
        proc.communicate(timeout=5)
    assert proc.returncode == 0
