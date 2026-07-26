"""The public, programmatic entry point: :func:`validate`.

Importing this module has the side effect of importing every built-in check
module, which registers them (via ``@register_check``) in the global check
registry used by :func:`cp_anndata_validator.orchestrator.run_checks`.
"""

from __future__ import annotations

from pathlib import Path
from typing import cast

import pandas as pd

import cp_anndata_validator.checks  # noqa: F401 -- imported for its check-registration side effect
from cp_anndata_validator.checks.registry import CheckContext
from cp_anndata_validator.loading import LoadError, load_anndata
from cp_anndata_validator.models.report import InputFileInfo, Report
from cp_anndata_validator.orchestrator import build_report, run_checks
from cp_anndata_validator.profiles import ProfileLevel, detect_profile_level
from cp_anndata_validator.sampling import DEFAULT_SAMPLE_ROWS
from cp_anndata_validator.schema.loader import SchemaError, load_schema
from cp_anndata_validator.schema.resolve import resolve_schema

__all__ = ["LoadError", "SchemaError", "validate"]


def _coerce_profile_level(profile_level: ProfileLevel | str | None) -> ProfileLevel | None:
    """Coerce a caller-supplied profile level to a :class:`ProfileLevel` member.

    ``ProfileLevel`` is a ``StrEnum``, so a plain string like ``"well"``
    compares equal to a member and would otherwise flow untouched into
    :class:`~cp_anndata_validator.checks.registry.CheckContext` -- checks that
    use enum-only attributes (``level.value``) would then fail at runtime.
    Coercing here guarantees no check ever receives a raw string, and rejects
    an unsupported value immediately instead of reporting it as a check
    failure.
    """
    if profile_level is None:
        return None
    try:
        return ProfileLevel(profile_level)
    except ValueError as exc:
        supported = ", ".join(repr(level.value) for level in ProfileLevel)
        raise ValueError(
            f"Unsupported profile_level {profile_level!r}; expected one of {supported}, "
            "or a ProfileLevel member"
        ) from exc


def validate(
    path: str | Path,
    *,
    schema: str | Path = "generic-cell-painting",
    profile_level: ProfileLevel | str | None = None,
    backed: bool | None = None,
    sample_rows: int = DEFAULT_SAMPLE_ROWS,
    strict: bool = False,
) -> Report:
    """Validate one AnnData dataset and return a structured :class:`Report`.

    Parameters:
        path: Path to an ``.h5ad`` file.
        schema: A built-in schema name (for example ``"jump-cp"``) or a path
            to a custom schema YAML file.
        profile_level: Declare the profile level explicitly, overriding
            auto-detection (the report still records what was detected).
            Accepts a :class:`ProfileLevel` member or its string value (for
            example ``"well"``).
        backed: Force backed (``True``) or in-memory (``False``) loading;
            ``None`` (default) auto-selects based on file size.
        sample_rows: Maximum number of rows sampled for numeric validity and
            AI-readiness checks.
        strict: Treat warnings as failures when computing the report status.

    Raises:
        ValueError: If ``profile_level`` is not a supported profile level.
        LoadError: If the dataset cannot be safely opened.
        SchemaError: If the requested schema cannot be loaded.
    """
    declared_level = _coerce_profile_level(profile_level)

    handle = load_anndata(path, backed=backed)
    try:
        obs = cast(pd.DataFrame, handle.adata.obs)
        var = cast(pd.DataFrame, handle.adata.var)
        schema_definition = load_schema(schema)
        resolved = resolve_schema(obs, var, schema_definition)
        detection = detect_profile_level(obs, resolved)
        profile = (
            detection.model_copy(update={"declared": declared_level})
            if declared_level is not None
            else detection
        )

        ctx = CheckContext(
            handle=handle, resolved_schema=resolved, profile=profile, sample_rows=sample_rows
        )
        issues, checks = run_checks(ctx)

        input_file = InputFileInfo(
            path=str(handle.path),
            size_bytes=handle.size_bytes,
            format="h5ad",
            backed=handle.backed,
        )
        return build_report(
            schema_id=schema_definition.schema_id,
            schema_version=schema_definition.schema_version,
            input_file=input_file,
            profile_level=profile,
            issues=issues,
            checks=checks,
            strict=strict,
        )
    finally:
        handle.close()
