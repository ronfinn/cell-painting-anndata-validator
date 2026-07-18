"""Tests for image/segmentation/feature-extraction provenance checks."""

from __future__ import annotations

from pathlib import Path

import anndata as ad

from cp_anndata_validator.checks.provenance import (
    check_feature_extraction_provenance,
    check_image_provenance,
    check_segmentation_provenance,
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


def test_image_provenance_passes_for_valid_fixture() -> None:
    ctx = make_context(make_single_cell_adata())
    assert check_image_provenance(ctx) == []


def test_image_provenance_flags_when_missing() -> None:
    adata = make_single_cell_adata()
    del adata.uns["image_provenance"]
    ctx = make_context(adata)
    assert [issue.code for issue in check_image_provenance(ctx)] == ["PROVIMG001"]


def test_segmentation_provenance_passes_for_valid_fixture() -> None:
    ctx = make_context(make_single_cell_adata())
    assert check_segmentation_provenance(ctx) == []


def test_segmentation_provenance_flags_when_missing_method_and_tool() -> None:
    adata = make_single_cell_adata()
    adata.uns["segmentation_provenance"] = {"notes": "no method or tool recorded"}
    ctx = make_context(adata)
    assert [issue.code for issue in check_segmentation_provenance(ctx)] == ["PROVSEG001"]


def test_feature_extraction_provenance_passes_for_valid_fixture() -> None:
    ctx = make_context(make_single_cell_adata())
    assert check_feature_extraction_provenance(ctx) == []


def test_feature_extraction_provenance_flags_when_missing() -> None:
    adata = make_single_cell_adata()
    del adata.uns["feature_extraction_provenance"]
    ctx = make_context(adata)
    assert [issue.code for issue in check_feature_extraction_provenance(ctx)] == ["PROVFEAT001"]
