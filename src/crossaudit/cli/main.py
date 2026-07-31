"""The CLI. Verbs mirror the loop; exit codes are the contract.

Every verb prints human text by default and a versioned object under --json.
Nothing here writes to a remote without an explicit --apply, and no verb
invents a default when configuration is missing: absent config denies.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

from .. import RECEIPT_SCHEMA, __version__, _selfid
from ..auditor import dcl_source_digest, run_audit
from ..config import CONFIG_NAME, Config, heterogeneity, load
from ..controller import StateStore
from ..dcl import run_checks
from ..errors import (EXIT_BLOCKED, EXIT_CONFIG, EXIT_ESCALATED, EXIT_INTEGRITY,
                      EXIT_OK, ConfigDenial, Denial)
from ..gitio import git, is_repo, materialise, parent, resolve
from ..receipt import build as build_receipt
from ..receipt import digest as receipt_digest
from ..receipt import load as load_receipt
from ..receipt import verify as verify_receipt
from ..receipt.verify import admit as admit_receipt
from . import wizard

GETTING_STARTED = """\
CrossAudit {version} — cross-vendor audit loop for agentic science

Nothing is configured yet in this directory. One command sets it up; it will
ask for the auditing model, the two API keys, and your rules markdown, and it
writes keys to a 0600 file outside the repository.

    crossaudit init              guided setup, right here
    crossaudit init --github     the same, plus the two-repository plan

Then, in order:

    crossaudit doctor            preflight: offline, read-only, tells you what is missing
    crossaudit check <dir>       the deterministic layer alone, no model involved
    crossaudit audit --sha HEAD  a full cycle: checks, model audit, report, receipt
    crossaudit verify <receipt>  re-derive every binding from the git trees
    crossaudit status            where each cycle stands

Docs: installer-design/ in the repository.
"""


def _emit(obj: dict, as_json: bool, human: str = "") -> None:
    if as_json:
        print(json.dumps({"crossaudit": __version__, **obj}, indent=2, sort_keys=True))
    elif human:
        print(human)


def _state(cfg: Config) -> StateStore:
    """The state store lives beside the configuration, never in site-packages."""
    return StateStore(cfg.root / cfg.state_dir / "state.json")


# ----------------------------------------------------------------- doctor
def cmd_doctor(args: argparse.Namespace) -> int:
    checks: list[dict] = []
    ok = True

    def add(name: str, passed: bool, detail: str, fix: str = "") -> None:
        nonlocal ok
        ok = ok and passed
        checks.append({"check": name, "ok": passed, "detail": detail, "fix": fix})

    ident = _selfid.identity()
    add("python", sys.version_info >= (3, 10),
        f"{sys.version.split()[0]}", "CrossAudit requires Python 3.10+")
    add("install", ident["install_mode"] != "unknown",
        f"{ident['install_mode']}, code digest {ident['code_digest_sha256'][:12]}",
        "reinstall from a wheel if this says unknown")
    if ident["install_mode"] not in _selfid.ADMISSIBLE_MODES:
        checks.append({"check": "admission-capable", "ok": False,
                       "detail": f"install mode {ident['install_mode']} may verify but "
                                 f"never admit",
                       "fix": "install the built wheel to admit receipts"})
    add("git", shutil.which("git") is not None, shutil.which("git") or "not found",
        "install git")

    try:
        cfg = load()
    except ConfigDenial as exc:
        add("config", False, exc.reason, f"run `crossaudit init` to write {CONFIG_NAME}")
        _emit({"ok": False, "checks": checks}, args.json,
              _render_doctor(checks, False))
        return EXIT_CONFIG

    add("config", True, str(cfg.path))
    const = cfg.root / cfg.constitution
    add("constitution", const.is_file(), str(const),
        "point `constitution:` at your rules markdown")
    if const.is_file():
        from ..auditor import known_rules
        rules = known_rules(const.read_text())
        add("constitution rules", bool(rules),
            f"{len(rules)} rule IDs parsed" if rules else "no CA-* rule headings found",
            "each rule needs a '### CA-AREA-NNN' heading, or every citation is unknown")

    het_ok, why = heterogeneity(cfg)
    add("heterogeneity (I1)", het_ok, why,
        "declare generator.vendor, and make it differ from auditor.vendor")

    key_present = bool(os.environ.get(cfg.auditor.key_env, "").strip())
    add("auditor key", key_present,
        f"${cfg.auditor.key_env} " + ("is set" if key_present else "is empty"),
        f"source {wizard.KEYS_FILE} or export {cfg.auditor.key_env}")

    add("provider", cfg.auditor.provider in ("anthropic", "openai_compat", "replay"),
        f"{cfg.auditor.provider}:{cfg.auditor.model}", "check auditor.provider")

    state_dir = cfg.root / cfg.state_dir
    writable = os.access(state_dir.parent, os.W_OK)
    add("state store", writable, str(state_dir / "state.json"),
        "the controller must be able to persist consumed receipts")

    add("science repo is git", is_repo(cfg.root), str(cfg.root),
        "run `git init` — the ledger is git, not a directory")

    if args.online:
        gh_ok, gh_detail = wizard.gh_available()
        add("gh cli", gh_ok, gh_detail, "install gh and run `gh auth login`")

    _emit({"ok": ok, "checks": checks, "verifier": ident}, args.json,
          _render_doctor(checks, ok))
    return EXIT_OK if ok else EXIT_CONFIG


def _render_doctor(checks: list[dict], ok: bool) -> str:
    lines = ["crossaudit doctor", "=" * 60]
    for c in checks:
        mark = "PASS" if c["ok"] else "FAIL"
        lines.append(f"[{mark}] {c['check']:22s} {c['detail']}")
        if not c["ok"] and c["fix"]:
            lines.append(f"       -> {c['fix']}")
    lines.append("=" * 60)
    lines.append("ready" if ok else "not ready — fix the FAIL lines above")
    return "\n".join(lines)


# ------------------------------------------------------------------ check
def cmd_check(args: argparse.Namespace) -> int:
    cfg = load()
    root = Path(args.path or cfg.root).resolve()
    if args.sha:
        sha, _tree = resolve(cfg.root, args.sha)
        files, notes = materialise(cfg.root, sha, args.scope or "")
        where = f"{sha[:12]} (from the git tree)"
    else:
        files, notes = {}, []
        for p in sorted(root.rglob("*")):
            if p.is_symlink():
                raise ConfigDenial(f"refusing to read through a symlink: {p}")
            if p.is_file():
                files[str(p.relative_to(root))] = p.read_bytes()
        where = f"{root} (working tree)"
    result = run_checks(files, cfg.checks, notes).as_dict()
    human = [f"deterministic layer over {where}",
             f"verdict: {result['verdict']}  ({result['total_hard_failures']} hard failures)"]
    for f in result["findings"]:
        human.append(f"  [{f['severity']}] {f['rule']} {f['artifact']}: {f['observation']}")
    _emit(result, args.json, "\n".join(human))
    return EXIT_BLOCKED if result["total_hard_failures"] else EXIT_OK


# ------------------------------------------------------------------ audit
def cmd_audit(args: argparse.Namespace) -> int:
    cfg = load()
    if not is_repo(cfg.root):
        raise ConfigDenial(f"{cfg.root} is not a git repository")
    sha, tree = resolve(cfg.root, args.sha or "HEAD")

    # Local mode writes the ledger into the audited repository, so HEAD moves
    # when a report is committed. Auditing that commit would audit the audit —
    # a self-referential cycle that inflates the ledger and audits nothing.
    changed = git("diff-tree", "--no-commit-id", "--name-only", "-r", sha,
                  cwd=cfg.root, check=False).splitlines()
    if changed and all(p.startswith(cfg.ledger_dir.rstrip("/") + "/") for p in changed):
        raise ConfigDenial(
            f"{sha[:12]} only touches the ledger ({cfg.ledger_dir}/): this is an audit "
            f"artefact, not an increment. Audit the science commit instead, or move the "
            f"ledger to the audit repository (github-pair mode).")

    store = _state(cfg)
    cycle = store.open_or_advance(cfg.science_repo, sha, parent(cfg.root, sha))
    if cycle.get("already_admitted"):
        raise ConfigDenial(f"{sha[:12]} was already admitted; open a new increment")

    files, notes = materialise(cfg.root, sha, args.scope or "")
    const_path = cfg.root / cfg.constitution
    if not const_path.is_file():
        raise ConfigDenial(f"constitution not found: {const_path}")
    constitution = const_path.read_text()
    const_commit = git("log", "-1", "--format=%H", "--", cfg.constitution,
                       cwd=cfg.root, check=False) or ""
    if not const_commit:
        raise ConfigDenial(
            f"{cfg.constitution} is not committed: an audit must cite the commit that "
            f"versioned the rules (I3). Commit it first.")

    outcome = run_audit(cfg=cfg, sha=sha, round_=cycle["round"], files=files, notes=notes,
                        constitution=constitution, constitution_commit=const_commit,
                        escalation_lock=bool(cycle.get("blocked_by_escalation")),
                        offline=args.offline,
                        allow_custom_endpoint=args.allow_custom_endpoint,
                        retention=args.retention)

    # Ledger write, in the only order that can be honest: report first, then a
    # receipt that binds the report's commit.
    ledger = cfg.root / cfg.ledger_dir / f"{sha[:12]}-r{cycle['round']}"
    if ledger.exists() and not args.force:
        raise ConfigDenial(f"cycle directory {ledger} already exists; append-only")
    ledger.mkdir(parents=True, exist_ok=True)
    report_path = ledger / "report.md"
    report_path.write_text(outcome.report)
    (ledger / "checks.json").write_text(json.dumps(outcome.dcl, indent=2))

    report_commit = ""
    if args.write_ledger:
        git("add", "--", str(report_path.relative_to(cfg.root)), cwd=cfg.root)
        git("commit", "-q", "-m", f"audit report {sha[:12]} r{cycle['round']}", cwd=cfg.root)
        report_commit = git("rev-parse", "HEAD", cwd=cfg.root)

    manifest = {path: __import__("hashlib").sha256(data).hexdigest()
                for path, data in files.items()}
    receipt = build_receipt(
        cfg=cfg, subject={"sha": sha, "tree": tree, "scope": args.scope or ""},
        cycle=cycle, manifest=manifest, constitution_path=cfg.constitution,
        constitution_bytes=const_path.read_bytes(), constitution_commit=const_commit,
        dcl_source_sha256=dcl_source_digest(), prompt_sha256=outcome.prompt_sha256,
        checks=cfg.checks, verdict=outcome.verdict, exchange=outcome.exchange,
        retention=args.retention, report_bytes=report_path.read_bytes(),
        report_commit=report_commit, cycle_path=str(ledger.relative_to(cfg.root)),
        audit_repo=cfg.audit_repo or "local", mode=args.mode,
        integrity=outcome.integrity)
    (ledger / "receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True))

    status = store.record_verdict(cycle["cycle_id"], sha, outcome.verdict,
                                  receipt_digest(receipt), cfg.max_rounds)
    result = {"verdict": outcome.verdict, "cycle_status": status,
              "cycle_id": cycle["cycle_id"], "round": cycle["round"],
              "integrity": outcome.integrity, "receipt": str(ledger / "receipt.json"),
              "report": str(report_path),
              "invalid_reason": outcome.invalid_reason}
    human = (f"{outcome.verdict}  (cycle {cycle['cycle_id']} round {cycle['round']}"
             f" -> {status})\n  report:  {report_path}\n  receipt: {ledger}/receipt.json")
    if outcome.invalid_reason:
        human += f"\n  audit rejected: {outcome.invalid_reason}"
    _emit(result, args.json, human)
    # The cycle's status outranks the round's verdict: a BLOCKED round that
    # exhausted the budget has escalated, and a caller scripting the loop needs
    # to hear that rather than plan another revision.
    if status == "ESCALATED":
        return EXIT_ESCALATED
    return {"PASS": EXIT_OK, "BLOCKED": EXIT_BLOCKED}.get(outcome.verdict, EXIT_ESCALATED)


# ----------------------------------------------------------------- verify
def cmd_verify(args: argparse.Namespace) -> int:
    cfg = load()
    path = Path(args.receipt).resolve()
    receipt = load_receipt(path)
    evidence = verify_receipt(
        receipt, science_root=Path(args.science_root or cfg.root).resolve(),
        audit_root=Path(args.audit_root or cfg.root).resolve(),
        expect_repo=args.expect_repo or cfg.science_repo,
        expect_sha=args.expect_sha or receipt["subject"]["sha"], cfg=cfg)
    out = {"verified": True, **evidence, "admitted": False}
    if args.admit:
        out.update(admit_receipt(receipt, _state(cfg), evidence))
    human = (f"VERIFIED  receipt {evidence['receipt_digest'][:16]} for "
             f"{evidence['sha'][:12]}"
             + ("\nADMITTED  consumed once; the cycle is closed" if args.admit
                else "\n(dry run: nothing consumed)"))
    _emit(out, args.json, human)
    return EXIT_OK


# ----------------------------------------------------------------- status
def cmd_status(args: argparse.Namespace) -> int:
    cfg = load()
    snap = _state(cfg).snapshot()
    cycles = snap.get("cycles", {})
    rows = [{"cycle_id": cid, "status": c["status"], "round": c["round"],
             "active_sha": c["active_sha"][:12], "consumed": len(c.get("consumed", []))}
            for cid, c in sorted(cycles.items())]
    human = ["cycle            status     round  sha           consumed",
             "-" * 60]
    human += [f"{r['cycle_id']:16s} {r['status']:10s} {r['round']:5d}  "
              f"{r['active_sha']}  {r['consumed']}" for r in rows] or ["(no cycles yet)"]
    _emit({"cycles": rows}, args.json, "\n".join(human))
    return EXIT_OK


# ------------------------------------------------------------------- init
def cmd_init(args: argparse.Namespace) -> int:
    summary = wizard.run(Path(args.path or "."), mode="github" if args.github else "local",
                         force=args.force)
    _emit(summary, args.json)
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="crossaudit", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--version", action="version",
                   version=f"crossaudit {__version__} (receipt schema {RECEIPT_SCHEMA})")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    sub = p.add_subparsers(dest="verb")

    i = sub.add_parser("init", help="guided setup: keys, rules, configuration")
    i.add_argument("path", nargs="?", help="directory to set up (default: here)")
    i.add_argument("--github", action="store_true", help="also plan the repository pair")
    i.add_argument("--force", action="store_true", help="overwrite an existing config")
    i.set_defaults(func=cmd_init)

    d = sub.add_parser("doctor", help="preflight: offline and read-only by default")
    d.add_argument("--online", action="store_true", help="also probe gh")
    d.set_defaults(func=cmd_doctor)

    c = sub.add_parser("check", help="run the deterministic layer, no model involved")
    c.add_argument("path", nargs="?", help="directory to check")
    c.add_argument("--sha", help="check a commit's tree instead of the working directory")
    c.add_argument("--scope", help="path prefix within the tree")
    c.set_defaults(func=cmd_check)

    a = sub.add_parser("audit", help="one full cycle: checks, model audit, report, receipt")
    a.add_argument("--sha", help="commit to audit (default HEAD)")
    a.add_argument("--scope", help="path prefix within the tree")
    a.add_argument("--offline", action="store_true",
                   help="deterministic layer only; yields DCL_ONLY, never PASS")
    a.add_argument("--write-ledger", action="store_true",
                   help="commit the report so the receipt can bind its commit")
    a.add_argument("--allow-custom-endpoint", action="store_true",
                   help="permit a non-builtin provider origin (sends your key there)")
    a.add_argument("--retention", choices=("sealed", "redacted", "no-raw"),
                   default="sealed")
    a.add_argument("--mode", choices=("local", "github-pair"), default="local")
    a.add_argument("--force", action="store_true", help="reuse an existing cycle directory")
    a.set_defaults(func=cmd_audit)

    v = sub.add_parser("verify", help="re-derive every binding; --admit to consume")
    v.add_argument("receipt")
    v.add_argument("--admit", action="store_true", help="consume the receipt, once")
    v.add_argument("--science-root")
    v.add_argument("--audit-root")
    v.add_argument("--expect-repo")
    v.add_argument("--expect-sha")
    v.set_defaults(func=cmd_verify)

    s = sub.add_parser("status", help="where each cycle stands")
    s.set_defaults(func=cmd_status)
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "verb", None):
        print(GETTING_STARTED.format(version=__version__))
        return EXIT_OK
    try:
        return args.func(args)
    except Denial as exc:
        if getattr(args, "json", False):
            print(json.dumps(exc.as_dict(), indent=2, sort_keys=True))
        else:
            print(f"DENIED ({exc.kind}): {exc.reason}", file=sys.stderr)
        return exc.exit_code
    except KeyboardInterrupt:
        print("\ninterrupted", file=sys.stderr)
        return EXIT_CONFIG


if __name__ == "__main__":
    raise SystemExit(main())
