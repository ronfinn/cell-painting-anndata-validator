"""Tests for basic AI-readiness checks: constant features and missing-value fraction."""

from __future__ import annotations

from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd
import pytest
from scipy import sparse

from cp_anndata_validator.checks.ai_readiness import (
    check_constant_features,
    check_missing_value_fraction,
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


@pytest.mark.parametrize("sparse_x", [False, True])
def test_constant_features_passes_for_varied_fixture(sparse_x: bool) -> None:
    ctx = make_context(make_single_cell_adata(sparse_x=sparse_x))
    assert check_constant_features(ctx) == []


def test_constant_features_flags_zero_variance_column() -> None:
    adata = make_single_cell_adata(n_obs=10, n_vars=4, sparse_x=False)
    adata.X[:, 1] = 5.0
    ctx = make_context(adata)

    issues = check_constant_features(ctx)

    assert [issue.code for issue in issues] == ["AI001"]
    assert issues[0].severity.value == "information"
    assert adata.var_names[1] in issues[0].evidence


def test_missing_value_fraction_passes_for_clean_fixture() -> None:
    ctx = make_context(make_single_cell_adata())
    assert check_missing_value_fraction(ctx) == []


def test_missing_value_fraction_flags_high_missingness() -> None:
    obs = pd.DataFrame(index=[f"o{i}" for i in range(10)])
    var = pd.DataFrame(index=[f"f{i}" for i in range(4)])
    x = np.full((10, 4), np.nan, dtype=np.float32)
    x[:, 0] = 1.0  # keep one clean column so it isn't 100% NaN
    adata = ad.AnnData(X=x, obs=obs, var=var)
    ctx = make_context(adata)

    issues = check_missing_value_fraction(ctx)

    assert [issue.code for issue in issues] == ["AI002"]


def test_missing_value_fraction_skips_non_floating_dtype() -> None:
    obs = pd.DataFrame(index=["a", "b"])
    var = pd.DataFrame(index=["f1"])
    adata = ad.AnnData(X=np.array([[1], [2]], dtype=np.int32), obs=obs, var=var)
    ctx = make_context(adata)
    assert check_missing_value_fraction(ctx) == []


def test_constant_features_dense_and_sparse_agree() -> None:
    dense = np.zeros((10, 3), dtype=np.float32)
    dense[:, 0] = np.arange(10)
    obs = pd.DataFrame(index=[f"o{i}" for i in range(10)])
    var = pd.DataFrame(index=[f"f{i}" for i in range(3)])

    dense_adata = ad.AnnData(X=dense.copy(), obs=obs, var=var)
    sparse_adata = ad.AnnData(X=sparse.csr_matrix(dense), obs=obs, var=var)

    dense_codes = [i.code for i in check_constant_features(make_context(dense_adata))]
    sparse_codes = [i.code for i in check_constant_features(make_context(sparse_adata))]

    assert dense_codes == sparse_codes == ["AI001"]
