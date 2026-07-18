"""Smoke tests that the package imports cleanly and exposes its public API."""

from __future__ import annotations

import cp_anndata_validator


def test_package_exposes_version() -> None:
    assert isinstance(cp_anndata_validator.__version__, str)
    assert cp_anndata_validator.__version__


def test_package_exposes_public_api_surface() -> None:
    for name in (
        "validate",
        "Report",
        "Issue",
        "Severity",
        "Category",
        "ProfileLevel",
        "LoadError",
        "SchemaError",
    ):
        assert hasattr(cp_anndata_validator, name), f"missing public export: {name}"
