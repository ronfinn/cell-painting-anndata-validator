"""Tests for AnnData structure and index-uniqueness checks."""

from __future__ import annotations

from pathlib import Path

import anndata as ad
import pandas as pd

from cp_anndata_validator.checks.registry import CheckContext
from cp_anndata_validator.checks.structure import check_index_uniqueness, check_matrix_structure
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


def test_matrix_structure_passes_for_valid_fixture() -> None:
    ctx = make_context(make_single_cell_adata())
    assert check_matrix_structure(ctx) == []


def test_matrix_structure_flags_zero_observations() -> None:
    adata = make_single_cell_adata()
    empty = adata[0:0].copy()
    ctx = make_context(empty)
    issues = check_matrix_structure(ctx)
    assert [i.code for i in issues] == ["STRUCT002"]


def test_index_uniqueness_passes_for_valid_fixture() -> None:
    ctx = make_context(make_single_cell_adata())
    assert check_index_uniqueness(ctx) == []


def test_index_uniqueness_detects_duplicate_obs_names() -> None:
    adata = make_single_cell_adata(n_obs=4)
    adata.obs_names = pd.Index(["a", "a", "b", "c"])
    ctx = make_context(adata)
    issues = check_index_uniqueness(ctx)
    assert "INDEX001" in [i.code for i in issues]


def test_index_uniqueness_detects_duplicate_var_names() -> None:
    adata = make_single_cell_adata(n_vars=4)
    adata.var_names = pd.Index(["f1", "f1", "f2", "f3"])
    ctx = make_context(adata)
    issues = check_index_uniqueness(ctx)
    assert "INDEX002" in [i.code for i in issues]


def test_index_uniqueness_detects_empty_obs_name() -> None:
    adata = make_single_cell_adata(n_obs=3)
    adata.obs_names = pd.Index(["a", "", "c"])
    ctx = make_context(adata)
    issues = check_index_uniqueness(ctx)
    assert "INDEX003" in [i.code for i in issues]


def test_index_uniqueness_dense_and_sparse_agree() -> None:
    dense = make_single_cell_adata(n_obs=4, sparse_x=False)
    sparse = make_single_cell_adata(n_obs=4, sparse_x=True)
    dense.obs_names = pd.Index(["a", "a", "b", "c"])
    sparse.obs_names = pd.Index(["a", "a", "b", "c"])

    dense_codes = [i.code for i in check_index_uniqueness(make_context(dense))]
    sparse_codes = [i.code for i in check_index_uniqueness(make_context(sparse))]

    assert dense_codes == sparse_codes == ["INDEX001"]


def test_matrix_structure_flags_missing_x() -> None:
    obs = pd.DataFrame(index=["a", "b"])
    var = pd.DataFrame(index=["f1"])
    adata = ad.AnnData(obs=obs, var=var)
    ctx = make_context(adata)
    issues = check_matrix_structure(ctx)
    assert [i.code for i in issues] == ["STRUCT002"]
