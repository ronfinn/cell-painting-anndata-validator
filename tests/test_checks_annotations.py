"""Tests for control/treatment annotation checks."""

from __future__ import annotations

from pathlib import Path

import anndata as ad

from cp_anndata_validator.checks.annotations import check_control_annotations
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


def test_passes_for_valid_fixture_with_negcon() -> None:
    ctx = make_context(make_single_cell_adata())
    assert check_control_annotations(ctx) == []


def test_flags_missing_control_column() -> None:
    adata = make_single_cell_adata()
    adata.obs = adata.obs.drop(columns=["control_type"])
    ctx = make_context(adata)

    issues = check_control_annotations(ctx)

    assert [issue.code for issue in issues] == ["CTRL001"]


def test_flags_unrecognized_label() -> None:
    adata = make_single_cell_adata(n_obs=4)
    adata.obs["control_type"] = ["negcon", "mystery_label", "trt", "trt"]
    ctx = make_context(adata)

    issues = check_control_annotations(ctx)

    assert "CTRL002" in [issue.code for issue in issues]
    ctrl002 = next(issue for issue in issues if issue.code == "CTRL002")
    assert "mystery_label" in (ctrl002.evidence or "")


def test_flags_missing_negative_control() -> None:
    adata = make_single_cell_adata(n_obs=4)
    adata.obs["control_type"] = ["trt", "trt", "poscon", "trt"]
    ctx = make_context(adata)

    issues = check_control_annotations(ctx)

    assert [issue.code for issue in issues] == ["CTRL003"]
