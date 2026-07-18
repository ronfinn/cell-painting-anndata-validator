"""Tests for matrix dtype/numeric-validity and slot-semantics checks."""

from __future__ import annotations

from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd
import pytest
from scipy import sparse

from cp_anndata_validator.checks.matrix import (
    check_layer_processing_stage_declared,
    check_layer_shape_consistency,
    check_matrix_dtype,
    check_matrix_finite_values,
    check_matrix_shape_consistency,
    check_obsm_varm_alignment,
    check_processing_stage_declared,
)
from cp_anndata_validator.checks.registry import CheckContext
from cp_anndata_validator.loading import AnnDataHandle
from cp_anndata_validator.profiles import ProfileLevel, ProfileLevelResult
from cp_anndata_validator.schema.loader import load_builtin_schema
from cp_anndata_validator.schema.resolve import resolve_schema
from tests.fixtures.synthetic import make_single_cell_adata


def make_context(adata: ad.AnnData, sample_rows: int = 5000) -> CheckContext:
    handle = AnnDataHandle(adata=adata, path=Path("fake.h5ad"), size_bytes=0, backed=False)
    schema = load_builtin_schema("generic-cell-painting")
    resolved = resolve_schema(adata.obs, adata.var, schema)
    profile = ProfileLevelResult(detected=ProfileLevel.SINGLE_CELL, explanation="")
    return CheckContext(
        handle=handle, resolved_schema=resolved, profile=profile, sample_rows=sample_rows
    )


def test_matrix_shape_consistency_passes_for_a_well_formed_adata() -> None:
    ctx = make_context(make_single_cell_adata(n_obs=6, n_vars=4))
    assert check_matrix_shape_consistency(ctx) == []


def test_matrix_shape_consistency_flags_row_count_mismatch() -> None:
    fake = _MismatchedAnnData((6, 4), n_obs=5)
    ctx = make_context(fake)  # type: ignore[arg-type]

    issues = check_matrix_shape_consistency(ctx)

    assert [issue.code for issue in issues] == ["MATRIX003"]
    assert "(6, 4)" in issues[0].message
    assert "(5, 4)" in issues[0].message


def test_matrix_shape_consistency_flags_column_count_mismatch() -> None:
    fake = _MismatchedAnnData((6, 4), n_vars=3)
    ctx = make_context(fake)  # type: ignore[arg-type]

    issues = check_matrix_shape_consistency(ctx)

    assert [issue.code for issue in issues] == ["MATRIX003"]


@pytest.mark.parametrize("sparse_x", [False, True])
def test_matrix_dtype_passes_for_numeric_matrix(sparse_x: bool) -> None:
    ctx = make_context(make_single_cell_adata(sparse_x=sparse_x))
    assert check_matrix_dtype(ctx) == []


def test_matrix_dtype_flags_object_dtype() -> None:
    obs = pd.DataFrame(index=["a", "b"])
    var = pd.DataFrame(index=["f1"])
    x = np.array([["1"], ["2"]], dtype=object)
    adata = ad.AnnData(X=x, obs=obs, var=var)
    ctx = make_context(adata)

    issues = check_matrix_dtype(ctx)

    assert [issue.code for issue in issues] == ["MATRIX001"]


@pytest.mark.parametrize("sparse_x", [False, True])
def test_matrix_finite_values_passes_for_clean_matrix(sparse_x: bool) -> None:
    ctx = make_context(make_single_cell_adata(sparse_x=sparse_x))
    assert check_matrix_finite_values(ctx) == []


def test_matrix_finite_values_detects_nan_dense() -> None:
    adata = make_single_cell_adata(n_obs=6, sparse_x=False)
    adata.X[0, 0] = np.nan
    ctx = make_context(adata)

    issues = check_matrix_finite_values(ctx)

    assert [issue.code for issue in issues] == ["MATRIX002"]


def test_matrix_finite_values_detects_inf_sparse() -> None:
    dense = np.ones((4, 3), dtype=np.float32)
    dense[1, 1] = np.inf
    obs = pd.DataFrame(index=[f"o{i}" for i in range(4)])
    var = pd.DataFrame(index=[f"f{i}" for i in range(3)])
    adata = ad.AnnData(X=sparse.csr_matrix(dense), obs=obs, var=var)
    ctx = make_context(adata)

    issues = check_matrix_finite_values(ctx)

    assert [issue.code for issue in issues] == ["MATRIX002"]


def test_matrix_finite_values_skipped_for_integer_dtype() -> None:
    obs = pd.DataFrame(index=["a", "b"])
    var = pd.DataFrame(index=["f1"])
    adata = ad.AnnData(X=np.array([[1], [2]], dtype=np.int32), obs=obs, var=var)
    ctx = make_context(adata)
    assert check_matrix_finite_values(ctx) == []


class _MismatchedAnnData:
    """A minimal AnnData stand-in that permits shapes real AnnData would reject.

    Real ``anndata.AnnData`` validates ``.layers``/``.obsm``/``.varm`` shapes
    on assignment, so a mismatch can only occur in a file that was not
    written through anndata's own API (for example a hand-edited or
    corrupted ``.h5ad``). This lightweight duck-typed stand-in lets the
    checks be exercised against exactly that scenario.
    """

    def __init__(
        self,
        x_shape: tuple[int, int],
        *,
        layers: dict[str, np.ndarray] | None = None,
        obsm: dict[str, np.ndarray] | None = None,
        varm: dict[str, np.ndarray] | None = None,
        n_obs: int | None = None,
        n_vars: int | None = None,
    ) -> None:
        self.X = np.zeros(x_shape, dtype=np.float32)
        self.layers = layers or {}
        self.obsm = obsm or {}
        self.varm = varm or {}
        self.uns: dict[str, object] = {}
        self.n_obs = n_obs if n_obs is not None else x_shape[0]
        self.n_vars = n_vars if n_vars is not None else x_shape[1]
        self.obs = pd.DataFrame(index=[f"o{i}" for i in range(self.n_obs)])
        self.var = pd.DataFrame(index=[f"f{i}" for i in range(self.n_vars)])


def test_layer_shape_consistency_passes_when_layers_match_x() -> None:
    adata = make_single_cell_adata(n_obs=6, n_vars=4)
    adata.layers["counts"] = adata.X.copy()
    ctx = make_context(adata)
    assert check_layer_shape_consistency(ctx) == []


def test_layer_shape_consistency_flags_mismatched_layer() -> None:
    fake = _MismatchedAnnData((6, 4), layers={"bad": np.zeros((6, 2), dtype=np.float32)})
    ctx = make_context(fake)  # type: ignore[arg-type]

    issues = check_layer_shape_consistency(ctx)

    assert [issue.code for issue in issues] == ["MATRIX004"]
    assert "layers.bad" in issues[0].location


def test_obsm_varm_alignment_passes_when_aligned() -> None:
    adata = make_single_cell_adata(n_obs=6)
    adata.obsm["X_pca"] = np.zeros((6, 2))
    ctx = make_context(adata)
    assert check_obsm_varm_alignment(ctx) == []


def test_obsm_varm_alignment_flags_misaligned_obsm() -> None:
    fake = _MismatchedAnnData((6, 4), obsm={"X_pca": np.zeros((5, 2))})
    ctx = make_context(fake)  # type: ignore[arg-type]

    issues = check_obsm_varm_alignment(ctx)

    assert [issue.code for issue in issues] == ["SLOT002"]
    assert "obsm.X_pca" in issues[0].location


def test_obsm_varm_alignment_flags_misaligned_varm() -> None:
    fake = _MismatchedAnnData((6, 4), varm={"loadings": np.zeros((5, 2))})
    ctx = make_context(fake)  # type: ignore[arg-type]

    issues = check_obsm_varm_alignment(ctx)

    assert [issue.code for issue in issues] == ["SLOT002"]
    assert "varm.loadings" in issues[0].location


def test_processing_stage_declared_passes_when_set() -> None:
    ctx = make_context(make_single_cell_adata())
    assert check_processing_stage_declared(ctx) == []


def test_processing_stage_declared_flags_missing_stage() -> None:
    adata = make_single_cell_adata()
    del adata.uns["processing_stage"]
    ctx = make_context(adata)

    issues = check_processing_stage_declared(ctx)

    assert [issue.code for issue in issues] == ["SLOT001"]


def test_layer_processing_stage_declared_passes_without_layers() -> None:
    ctx = make_context(make_single_cell_adata())
    assert check_layer_processing_stage_declared(ctx) == []


def test_layer_processing_stage_declared_passes_when_declared() -> None:
    adata = make_single_cell_adata()
    adata.layers["counts"] = adata.X.copy()
    adata.uns["layer_processing_stages"] = {"counts": "raw"}
    ctx = make_context(adata)

    assert check_layer_processing_stage_declared(ctx) == []


def test_layer_processing_stage_declared_flags_undeclared_layer() -> None:
    adata = make_single_cell_adata()
    adata.layers["counts"] = adata.X.copy()
    ctx = make_context(adata)

    issues = check_layer_processing_stage_declared(ctx)

    assert [issue.code for issue in issues] == ["SLOT003"]
    assert "counts" in issues[0].evidence


def test_layer_processing_stage_declared_flags_partially_declared_layers() -> None:
    adata = make_single_cell_adata()
    adata.layers["counts"] = adata.X.copy()
    adata.layers["normalized"] = adata.X.copy()
    adata.uns["layer_processing_stages"] = {"counts": "raw"}
    ctx = make_context(adata)

    issues = check_layer_processing_stage_declared(ctx)

    assert [issue.code for issue in issues] == ["SLOT003"]
    assert issues[0].evidence == "normalized"
