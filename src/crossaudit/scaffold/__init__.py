"""Templates `init` instantiates. The Constitution is a template here, never law."""
from __future__ import annotations

from pathlib import Path

TEMPLATES = Path(__file__).parent / "templates"


def read(name: str) -> str:
    path = TEMPLATES / name
    if not path.is_file():
        raise FileNotFoundError(f"packaged template {name!r} is missing")
    return path.read_text()


CONFIG_TEMPLATE = """\
# crossaudit.yml — the one configuration file.
# Credentials are NOT here: each role names the environment variable that
# carries its key, and the value is read at call time.
version: 1

science_repo: {science_repo}
{audit_repo_line}
constitution: {constitution}
max_rounds: {max_rounds}

auditor:
  vendor: {auditor_vendor}
  provider: {auditor_provider}
  model: {auditor_model}
  key_env: CROSSAUDIT_AUDITOR_KEY
{base_url_line}
generator:
  # Declared so I1 (heterogeneity) can be asserted from configuration.
  # CrossAudit does not drive your generator; it audits what the generator committed.
  vendor: {generator_vendor}

isolation:
  # Refuse to admit a receipt whose isolation evidence is weaker than this.
  # permissive: true means the two roles' credentials were never both reachable
  # by one process — a single machine holding both keys cannot evidence it.
  minimum:
    parametric: true
    contextual: true
    permissive: {permissive_minimum}

state:
  dir: {state_dir}

checks: [schema, units, convergence, provenance]
"""
