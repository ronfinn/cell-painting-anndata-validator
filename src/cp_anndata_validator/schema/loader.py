"""Loading of built-in and custom schema YAML files.

Schema files are treated as untrusted input: they are parsed with
``yaml.safe_load`` only (never ``yaml.unsafe_load``, ``eval`` or ``exec``),
and validated against :class:`SchemaDefinition`, which rejects unknown keys.
"""

from __future__ import annotations

from importlib import resources
from pathlib import Path

import yaml
from pydantic import ValidationError

from cp_anndata_validator.schema.models import SchemaDefinition

_BUILTIN_SCHEMA_RESOURCES: dict[str, str] = {
    "generic-cell-painting": "generic-cell-painting.yaml",
    "jump-cp": "jump-cp.yaml",
}


class SchemaError(Exception):
    """Raised when a schema (built-in or custom) cannot be loaded or is invalid."""


def list_builtin_schema_names() -> list[str]:
    """The names of all built-in schemas, sorted for stable CLI output."""
    return sorted(_BUILTIN_SCHEMA_RESOURCES)


def _parse_yaml_mapping(raw_text: str, *, source: str) -> dict[str, object]:
    try:
        data = yaml.safe_load(raw_text)
    except yaml.YAMLError as exc:
        raise SchemaError(f"Schema {source} is not valid YAML: {exc}") from exc

    if not isinstance(data, dict):
        raise SchemaError(f"Schema {source} must contain a YAML mapping at the top level")
    return data


def _validate_schema(data: dict[str, object], *, source: str) -> SchemaDefinition:
    try:
        return SchemaDefinition.model_validate(data)
    except ValidationError as exc:
        raise SchemaError(f"Schema {source} is invalid: {exc}") from exc


def load_builtin_schema(name: str) -> SchemaDefinition:
    """Load one of the schemas packaged as ``cp_anndata_validator`` resources."""
    try:
        filename = _BUILTIN_SCHEMA_RESOURCES[name]
    except KeyError as exc:
        available = ", ".join(list_builtin_schema_names())
        raise SchemaError(
            f"Unknown built-in schema {name!r}; available schemas: {available}"
        ) from exc

    resource = resources.files("cp_anndata_validator.schema.resources").joinpath(filename)
    try:
        raw_text = resource.read_text(encoding="utf-8")
    except (FileNotFoundError, OSError) as exc:
        raise SchemaError(
            f"Built-in schema {name!r} is registered but its packaged resource "
            f"file {filename!r} is missing or unreadable: {exc}"
        ) from exc
    data = _parse_yaml_mapping(raw_text, source=f"'{name}' (built-in)")
    return _validate_schema(data, source=f"'{name}' (built-in)")


def load_schema_from_path(path: str | Path) -> SchemaDefinition:
    """Load a custom schema from a user-supplied YAML file path."""
    resolved = Path(path).expanduser().resolve()
    if not resolved.exists():
        raise SchemaError(f"Schema file does not exist: {resolved}")
    if not resolved.is_file():
        raise SchemaError(f"Schema path is not a file: {resolved}")

    try:
        raw_text = resolved.read_text(encoding="utf-8")
    except OSError as exc:
        raise SchemaError(f"Could not read schema file {resolved}: {exc}") from exc

    data = _parse_yaml_mapping(raw_text, source=str(resolved))
    return _validate_schema(data, source=str(resolved))


def load_schema(name_or_path: str | Path) -> SchemaDefinition:
    """Load a schema by built-in name (for example ``"jump-cp"``) or file path.

    A bare name that matches a built-in schema always takes precedence;
    anything else is treated as a path to a custom schema YAML file.
    """
    if isinstance(name_or_path, str) and name_or_path in _BUILTIN_SCHEMA_RESOURCES:
        return load_builtin_schema(name_or_path)
    return load_schema_from_path(name_or_path)
