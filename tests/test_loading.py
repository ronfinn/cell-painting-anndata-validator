"""Tests for AnnData loading and safe inspection."""

from __future__ import annotations

from pathlib import Path

import pytest

from cp_anndata_validator.loading import LoadError, load_anndata
from tests.fixtures.synthetic import make_single_cell_adata, write_h5ad


def test_load_dense_in_memory(tmp_path: Path) -> None:
    path = write_h5ad(make_single_cell_adata(sparse_x=False), tmp_path)
    handle = load_anndata(path)
    try:
        assert handle.backed is False
        assert handle.n_obs == 12
        assert handle.x_is_sparse is False
        assert handle.x_shape == (12, 6)
    finally:
        handle.close()


def test_load_sparse_in_memory(tmp_path: Path) -> None:
    path = write_h5ad(make_single_cell_adata(sparse_x=True), tmp_path)
    handle = load_anndata(path)
    try:
        assert handle.x_is_sparse is True
        assert handle.n_vars == 6
    finally:
        handle.close()


def test_load_backed_mode_does_not_require_full_read(tmp_path: Path) -> None:
    path = write_h5ad(make_single_cell_adata(n_obs=40, n_vars=6, sparse_x=True), tmp_path)
    handle = load_anndata(path, backed=True)
    try:
        assert handle.backed is True
        assert handle.adata.isbacked is True
        # Shape/dtype metadata must be available without materializing X.
        assert handle.x_shape == (40, 6)
        assert handle.x_dtype.startswith("float")
    finally:
        handle.close()


def test_auto_backed_selection_uses_size_threshold(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import cp_anndata_validator.loading as loading_module

    monkeypatch.setattr(loading_module, "DEFAULT_BACKED_THRESHOLD_BYTES", 1)
    path = write_h5ad(make_single_cell_adata(), tmp_path)
    handle = load_anndata(path, backed=None)
    try:
        assert handle.backed is True
    finally:
        handle.close()


def test_load_missing_file_raises_load_error(tmp_path: Path) -> None:
    with pytest.raises(LoadError, match="does not exist"):
        load_anndata(tmp_path / "missing.h5ad")


def test_load_wrong_extension_raises_load_error(tmp_path: Path) -> None:
    bogus = tmp_path / "dataset.csv"
    bogus.write_text("not an h5ad file")
    with pytest.raises(LoadError, match="Unsupported file extension"):
        load_anndata(bogus)


def test_load_corrupt_file_raises_load_error(tmp_path: Path) -> None:
    bogus = tmp_path / "dataset.h5ad"
    bogus.write_bytes(b"not a real hdf5 file")
    with pytest.raises(LoadError, match="Failed to read AnnData file"):
        load_anndata(bogus)


def test_load_directory_raises_load_error(tmp_path: Path) -> None:
    directory = tmp_path / "dataset.h5ad"
    directory.mkdir()
    with pytest.raises(LoadError, match="not a file"):
        load_anndata(directory)
