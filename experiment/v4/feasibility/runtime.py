"""Host-runtime binding for reproducible and safe feasibility execution."""
from __future__ import annotations

import ast
import hashlib
import json
import platform
import random
import resource
import sys
from pathlib import Path
from typing import Any


def _identity(path: str | Path) -> dict[str, Any]:
    resolved = Path(path).resolve(strict=True)
    if not resolved.is_file():
        raise RuntimeError(f"runtime dependency is not a regular file: {resolved}")
    return {
        "resolved_path": str(resolved),
        "sha256": hashlib.sha256(resolved.read_bytes()).hexdigest(),
        "size_bytes": resolved.stat().st_size,
    }


def execution_runtime_binding() -> dict[str, Any]:
    """Bind Python, platform and local safety dependencies without secrets."""
    dependencies: dict[str, Any] = {
        "python_executable": _identity(sys.executable),
        "stdlib_ast": _identity(ast.__file__),
        "stdlib_random": _identity(random.__file__),
    }
    if getattr(resource, "__file__", None):
        dependencies["stdlib_resource"] = _identity(resource.__file__)
    sandbox_exec = Path("/usr/bin/sandbox-exec")
    dependencies["macos_sandbox_exec"] = (
        _identity(sandbox_exec) if sandbox_exec.is_file() else None
    )
    return {
        "python": {
            "version": sys.version,
            "version_info": list(sys.version_info),
            "implementation": platform.python_implementation(),
            "implementation_cache_tag": sys.implementation.cache_tag,
        },
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "mac_ver": list(platform.mac_ver()),
        },
        "dependencies": dependencies,
    }


def verify_execution_runtime_binding(expected: dict[str, Any]) -> None:
    observed = execution_runtime_binding()
    if json.dumps(observed, sort_keys=True, separators=(",", ":")) != json.dumps(
        expected, sort_keys=True, separators=(",", ":")
    ):
        raise RuntimeError("execution runtime binding drift; refusing feasibility execution")
