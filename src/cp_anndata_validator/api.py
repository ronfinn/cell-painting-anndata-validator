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


def validate(
    path: str | Path,
    *,
    schema: str | Path = "generic-cell-painting",
    profile_level: ProfileLevel | None = None,
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
        backed: Force backed (``True``) or in-memory (``False``) loading;
            ``None`` (default) auto-selects based on file size.
        sample_rows: Maximum number of rows sampled for numeric validity and
            AI-readiness checks.
        strict: Treat warnings as failures when computing the report status.

    Raises:
        LoadError: If the dataset cannot be safely opened.
        SchemaError: If the requested schema cannot be loaded.
    """
    handle = load_anndata(path, backed=backed)
    try:
        obs = cast(pd.DataFrame, handle.adata.obs)
        var = cast(pd.DataFrame, handle.adata.var)
        schema_definition = load_schema(schema)
        resolved = resolve_schema(obs, var, schema_definition)
        detection = detect_profile_level(obs, resolved)
        profile = (
            detection.model_copy(update={"declared": profile_level})
            if profile_level is not None
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
