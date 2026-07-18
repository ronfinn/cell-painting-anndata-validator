"""Tests for feature name/compartment checks."""

from __future__ import annotations

from pathlib import Path

import anndata as ad
import pandas as pd

from cp_anndata_validator.checks.features import check_feature_compartments
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


def test_passes_for_compartment_prefixed_features() -> None:
    ctx = make_context(make_single_cell_adata())
    assert check_feature_compartments(ctx) == []


def test_flags_features_without_a_known_compartment_prefix() -> None:
    adata = make_single_cell_adata(n_vars=4)
    adata.var_names = pd.Index(["Cells_Area", "weird_feature", "Nuclei_Radius", "another_bad"])
    ctx = make_context(adata)

    issues = check_feature_compartments(ctx)

    assert [issue.code for issue in issues] == ["FEAT001"]
    assert "weird_feature" in issues[0].evidence
    assert "another_bad" in issues[0].evidence
