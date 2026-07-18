"""Tests for bounded, sparse-safe sampling helpers."""

from __future__ import annotations

import numpy as np
import pytest
from scipy import sparse

from cp_anndata_validator.sampling import sample_row_indices, summarize_finite_values


class RecordingMatrix:
    """A matrix-like test double that records how it was accessed.

    Used to prove that ``summarize_finite_values`` never calls ``.toarray()``
    / ``.todense()`` (i.e. never densifies) and never slices with ``[:]``
    (i.e. never reads the full matrix) -- it only ever indexes with a bounded
    row-index array.
    """

    def __init__(self, data: np.ndarray) -> None:
        self._data = data
        self.shape = data.shape
        self.getitem_calls: list[object] = []
        self.densify_calls = 0

    def __getitem__(self, key: object) -> np.ndarray:
        self.getitem_calls.append(key)
        return self._data[key]

    def toarray(self) -> np.ndarray:  # pragma: no cover - must never be called
        self.densify_calls += 1
        return self._data

    def todense(self) -> np.ndarray:  # pragma: no cover - must never be called
        self.densify_calls += 1
        return self._data


def test_sample_row_indices_is_deterministic_and_sorted() -> None:
    first = sample_row_indices(1000, 10, seed=42)
    second = sample_row_indices(1000, 10, seed=42)
    assert list(first) == list(second)
    assert list(first) == sorted(first)
    assert len(first) == 10


def test_sample_row_indices_returns_full_range_when_bound_exceeds_n_obs() -> None:
    indices = sample_row_indices(5, sample_rows=100)
    assert list(indices) == [0, 1, 2, 3, 4]


def test_sample_row_indices_rejects_non_positive_sample_size() -> None:
    with pytest.raises(ValueError):
        sample_row_indices(10, 0)


def test_summarize_finite_values_never_densifies_or_reads_full_matrix() -> None:
    data = np.ones((1000, 4), dtype=np.float32)
    matrix = RecordingMatrix(data)

    summary = summarize_finite_values(matrix, sample_rows=25, seed=1)

    assert summary.was_sampled is True
    assert summary.sampled_rows == 25
    assert summary.total_rows == 1000
    assert matrix.densify_calls == 0
    assert len(matrix.getitem_calls) == 1
    accessed = matrix.getitem_calls[0]
    assert isinstance(accessed, np.ndarray)
    assert len(accessed) == 25


def test_summarize_finite_values_dense_detects_non_finite() -> None:
    data = np.ones((10, 3), dtype=np.float64)
    data[2, 1] = np.nan
    data[5, 0] = np.inf

    summary = summarize_finite_values(data, sample_rows=10)

    assert summary.was_sampled is False
    assert summary.has_non_finite is True
    assert summary.non_finite_count == 2
    assert summary.checked_values == 30


def test_summarize_finite_values_sparse_inspects_only_stored_values() -> None:
    dense = np.zeros((6, 5), dtype=np.float64)
    dense[0, 0] = 1.0
    dense[1, 1] = np.nan
    matrix = sparse.csr_matrix(dense)

    summary = summarize_finite_values(matrix, sample_rows=6)

    assert summary.has_non_finite is True
    assert summary.non_finite_count == 1
    # Only the two stored (non-zero) values are inspected, not all 30 cells.
    assert summary.checked_values == 2


def test_summarize_finite_values_sparse_all_finite() -> None:
    dense = np.eye(4, dtype=np.float64)
    matrix = sparse.csr_matrix(dense)

    summary = summarize_finite_values(matrix, sample_rows=4)

    assert summary.has_non_finite is False
