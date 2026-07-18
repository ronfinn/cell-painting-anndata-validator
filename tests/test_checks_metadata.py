"""Tests for batch/experiment metadata checks."""

from __future__ import annotations

from pathlib import Path

import anndata as ad

from cp_anndata_validator.checks.metadata import (
    check_batch_identifier_declared,
    check_experiment_metadata_declared,
    check_source_identifier_declared,
)
from cp_anndata_validator.checks.registry import CheckContext
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


def test_batch_identifier_passes_for_valid_fixture() -> None:
    ctx = make_context(make_single_cell_adata())
    assert check_batch_identifier_declared(ctx) == []


def test_batch_identifier_flags_when_missing() -> None:
    adata = make_single_cell_adata()
    adata.obs = adata.obs.drop(columns=["batch_id"])
    ctx = make_context(adata)

    issues = check_batch_identifier_declared(ctx)

    assert [issue.code for issue in issues] == ["META001"]
    assert issues[0].severity.value == "information"


def test_experiment_metadata_passes_for_valid_fixture() -> None:
    ctx = make_context(make_single_cell_adata())
    assert check_experiment_metadata_declared(ctx) == []


def test_experiment_metadata_flags_when_missing() -> None:
    adata = make_single_cell_adata()
    del adata.uns["experiment"]
    ctx = make_context(adata)

    issues = check_experiment_metadata_declared(ctx)

    assert [issue.code for issue in issues] == ["META002"]


def test_source_identifier_flags_when_missing() -> None:
    ctx = make_context(make_single_cell_adata())
    issues = check_source_identifier_declared(ctx)

    assert [issue.code for issue in issues] == ["META003"]
    assert issues[0].severity.value == "information"


def test_source_identifier_passes_when_resolved() -> None:
    adata = make_single_cell_adata()
    adata.obs["source_id"] = "site-1"
    ctx = make_context(adata)

    assert check_source_identifier_declared(ctx) == []
