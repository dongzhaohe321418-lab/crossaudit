"""Small fail-closed validator for the frozen feasibility JSON schemas.

The provider's structured-output mode is transport assistance, not an
integrity boundary.  This dependency-free subset is deliberately limited to
the JSON Schema features present in the frozen protocol.
"""
from __future__ import annotations

import math
from typing import Any


SUPPORTED_KEYWORDS = {
    "type", "properties", "required", "additionalProperties", "items",
    "enum", "minimum", "maximum",
}


def _finite_number(value: Any) -> bool:
    if type(value) not in (int, float):
        return False
    try:
        return math.isfinite(float(value))
    except (OverflowError, TypeError, ValueError):
        return False


def validate_schema_definition(schema: Any, path: str = "$") -> list[str]:
    """Validate the frozen schema language itself, recursively and outcome-free."""
    if not isinstance(schema, dict):
        return [f"{path}: schema is not an object"]
    errors: list[str] = []
    unknown = set(schema) - SUPPORTED_KEYWORDS
    if unknown:
        errors.append(f"{path}: unsupported schema keyword(s): {', '.join(sorted(unknown))}")
    declared = schema.get("type")
    kinds = declared if isinstance(declared, list) else [declared]
    allowed = {"object", "array", "string", "boolean", "null", "integer", "number"}
    if not kinds or not all(isinstance(kind, str) and kind in allowed for kind in kinds):
        errors.append(f"{path}: schema type is missing or unsupported")
    if "enum" in schema and not isinstance(schema["enum"], list):
        errors.append(f"{path}: enum must be an array")
    for name in ("minimum", "maximum"):
        if name in schema and (
            not _finite_number(schema[name])
        ):
            errors.append(f"{path}: {name} must be finite numeric")
    if "object" in kinds:
        properties = schema.get("properties")
        required = schema.get("required")
        additional = schema.get("additionalProperties")
        if not isinstance(properties, dict):
            errors.append(f"{path}: object properties must be an object")
        else:
            for name, child in properties.items():
                errors.extend(validate_schema_definition(child, f"{path}.properties.{name}"))
        if not isinstance(required, list) or not all(isinstance(name, str) for name in required):
            errors.append(f"{path}: object required must be a string array")
        elif isinstance(properties, dict) and not set(required).issubset(properties):
            errors.append(f"{path}: required names must exist in properties")
        if additional not in (True, False):
            errors.append(f"{path}: additionalProperties must be explicit boolean")
    if "array" in kinds:
        if not isinstance(schema.get("items"), dict):
            errors.append(f"{path}: array items must be a schema object")
        else:
            errors.extend(validate_schema_definition(schema["items"], f"{path}.items"))
    return errors


def _matches_type(value: Any, kind: str) -> bool:
    if kind == "object":
        return isinstance(value, dict)
    if kind == "array":
        return isinstance(value, list)
    if kind == "string":
        return isinstance(value, str)
    if kind == "boolean":
        return type(value) is bool
    if kind == "null":
        return value is None
    if kind == "integer":
        return type(value) is int
    if kind == "number":
        return _finite_number(value)
    return False


def validate_json_schema(value: Any, schema: dict[str, Any], path: str = "$") -> list[str]:
    """Return validation errors; unknown schema features fail closed."""
    if not isinstance(schema, dict):
        return [f"{path}: schema is not an object"]
    unknown = set(schema) - SUPPORTED_KEYWORDS
    if unknown:
        return [f"{path}: unsupported schema keyword(s): {', '.join(sorted(unknown))}"]

    declared = schema.get("type")
    kinds = declared if isinstance(declared, list) else [declared]
    if not kinds or not all(isinstance(kind, str) for kind in kinds):
        return [f"{path}: schema type is missing or invalid"]
    unsupported_types = set(kinds) - {
        "object", "array", "string", "boolean", "null", "integer", "number",
    }
    if unsupported_types:
        return [f"{path}: unsupported schema type(s): {', '.join(sorted(unsupported_types))}"]
    if not any(_matches_type(value, kind) for kind in kinds):
        return [f"{path}: value does not match type {declared!r}"]

    errors: list[str] = []
    if "enum" in schema:
        enum = schema["enum"]
        if not isinstance(enum, list) or not any(type(value) is type(item) and value == item for item in enum):
            errors.append(f"{path}: value is not in the frozen enum")
    if type(value) in (int, float):
        try:
            number = float(value)
        except (OverflowError, TypeError, ValueError):
            number = math.inf
        if not math.isfinite(number):
            errors.append(f"{path}: number is not finite")
        minimum = schema.get("minimum")
        maximum = schema.get("maximum")
        if minimum is not None and number < float(minimum):
            errors.append(f"{path}: number is below minimum {minimum}")
        if maximum is not None and number > float(maximum):
            errors.append(f"{path}: number is above maximum {maximum}")

    if isinstance(value, dict):
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        additional = schema.get("additionalProperties", True)
        if not isinstance(properties, dict) or not isinstance(required, list) \
                or not all(isinstance(name, str) for name in required):
            return errors + [f"{path}: object schema properties/required are invalid"]
        for name in required:
            if name not in value:
                errors.append(f"{path}: missing required property {name!r}")
        unknown_properties = set(value) - set(properties)
        if additional is False and unknown_properties:
            errors.append(
                f"{path}: additional properties forbidden: "
                + ", ".join(sorted(str(name) for name in unknown_properties))
            )
        elif additional not in (True, False):
            errors.append(f"{path}: only boolean additionalProperties is supported")
        for name, child in value.items():
            if name in properties:
                errors.extend(validate_json_schema(child, properties[name], f"{path}.{name}"))

    if isinstance(value, list):
        items = schema.get("items")
        if not isinstance(items, dict):
            errors.append(f"{path}: array schema lacks supported items object")
        else:
            for index, child in enumerate(value):
                errors.extend(validate_json_schema(child, items, f"{path}[{index}]"))
    return errors
