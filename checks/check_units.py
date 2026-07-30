"""Unit/dimension sanity check (backs CA-DATA-001, CA-DOM-001).

A deliberately small dimensional registry: enough to catch the classic
silent errors (unknown units, energy fields carrying length units) without
pulling in a full units library. Extend UNIT_DIMENSIONS for your field, or
replace with pint if you prefer.
"""
from __future__ import annotations

import json
from pathlib import Path

UNIT_DIMENSIONS = {
    # energy
    "hartree": "energy", "ev": "energy", "kcal/mol": "energy",
    "kj/mol": "energy", "cm^-1": "energy",
    # length
    "angstrom": "length", "bohr": "length", "nm": "length", "pm": "length",
    # misc
    "debye": "dipole", "kelvin": "temperature", "gpa": "pressure",
    "dimensionless": "dimensionless", "unitless": "dimensionless",
    "electrons": "charge", "e": "charge", "degrees": "angle",
}

NAME_HINTS = (
    ("energy", "energy"), ("enthalpy", "energy"), ("gap", "energy"),
    ("barrier", "energy"), ("distance", "length"), ("length", "length"),
    ("radius", "length"), ("dipole", "dipole"), ("temperature", "temperature"),
)


def _blocker(rule: str, message: str) -> dict:
    return {"severity": "BLOCKER", "rule": rule, "message": message}


def run(experiment_dir: Path) -> list[dict]:
    findings: list[dict] = []
    results_path = experiment_dir / "results.json"
    if not results_path.is_file():
        return findings  # check_schema already reports the absence

    try:
        results = json.loads(results_path.read_text())
    except json.JSONDecodeError:
        return findings  # ditto

    for i, q in enumerate(results.get("quantities", [])):
        if not isinstance(q, dict):
            continue
        unit = str(q.get("unit", "")).strip().lower()
        name = str(q.get("name", f"quantities[{i}]"))
        if not unit:
            continue  # schema check owns missing units
        dim = UNIT_DIMENSIONS.get(unit)
        if dim is None:
            findings.append(_blocker(
                "CA-DATA-001",
                f"'{name}': unknown unit '{q.get('unit')}' — add it to the "
                f"registry or fix the record"))
            continue
        for hint, expected in NAME_HINTS:
            if hint in name.lower() and dim != expected:
                findings.append(_blocker(
                    "CA-DOM-001",
                    f"'{name}' looks like {expected} but carries {dim} "
                    f"unit '{unit}' — dimensional inconsistency"))
                break
    return findings
