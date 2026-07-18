"""Tests for schema identifier/version and licence checks."""

from __future__ import annotations

from pathlib import Path

import anndata as ad

from cp_anndata_validator.checks.registry import CheckContext
from cp_anndata_validator.checks.schema_meta import (
    check_dataset_licence_declared,
    check_schema_metadata_declared,
)
from cp_anndata_validator.loading import AnnDataHandle
from cp_anndata_validator.profiles import ProfileLevel, ProfileLevelResult
from cp_anndata_validator.schema.loader import load_builtin_schema
from cp_anndata_validator.schema.resolve import resolve_schema
from tests.fixtures.synthetic import make_single_cell_adata


def make_context(adata: ad.AnnData) -> CheckContext:
    handle = AnnDataHandle(adata=adata, path=Path("fake.h5ad"), size_bytes=0, backed=False)
    schema = load_builtin_schema("generic-cell-painting")
    resolved = resolve_schema(adata.obs, adata.var, schema)
    profile = ProfileLevelResult(detected=ProfileLevel.SINGLE_CELL, explanation="")
    return CheckContext(handle=handle, resolved_schema=resolved, profile=profile)


def test_schema_metadata_passes_for_valid_fixture() -> None:
    ctx = make_context(make_single_cell_adata())
    assert check_schema_metadata_declared(ctx) == []


def test_schema_metadata_flags_missing_schema_id_and_version() -> None:
    adata = make_single_cell_adata()
    del adata.uns["schema_id"]
    del adata.uns["schema_version"]
    ctx = make_context(adata)

    issues = check_schema_metadata_declared(ctx)

    assert {issue.code for issue in issues} == {"SCHEMA001", "SCHEMA002"}


def test_licence_passes_for_valid_fixture() -> None:
    ctx = make_context(make_single_cell_adata())
    assert check_dataset_licence_declared(ctx) == []


def test_licence_accepts_american_spelling() -> None:
    adata = make_single_cell_adata()
    del adata.uns["licence"]
    adata.uns["license"] = "MIT"
    ctx = make_context(adata)
    assert check_dataset_licence_declared(ctx) == []


def test_licence_flags_when_missing() -> None:
    adata = make_single_cell_adata()
    del adata.uns["licence"]
    ctx = make_context(adata)
    assert [issue.code for issue in check_dataset_licence_declared(ctx)] == ["LICENSE001"]
