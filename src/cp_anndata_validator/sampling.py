"""Bounded, sparse-safe sampling helpers for numeric validity checks.

These helpers back checks that must inspect matrix *values* (for example,
looking for non-finite entries) without ever calling ``.toarray()`` /
``.todense()`` on a full sparse matrix, and without reading a complete large
matrix when a bounded sample is sufficient.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy import sparse

DEFAULT_SAMPLE_ROWS = 5000


@dataclass(frozen=True)
class FiniteValueSummary:
    """Summary of how many (possibly sampled) matrix values are non-finite."""

    sampled_rows: int
    total_rows: int
    checked_values: int
    non_finite_count: int

    @property
    def was_sampled(self) -> bool:
        return self.sampled_rows < self.total_rows

    @property
    def has_non_finite(self) -> bool:
        return self.non_finite_count > 0


def sample_row_indices(n_obs: int, sample_rows: int, *, seed: int = 0) -> np.ndarray:
    """Return a deterministic, sorted sample of at most ``sample_rows`` row indices.

    Indices are sorted because backed HDF5-based matrices require
    monotonically increasing indices for fancy row indexing.
    """
    if sample_rows <= 0:
        raise ValueError("sample_rows must be a positive integer")
    if sample_rows >= n_obs:
        return np.arange(n_obs)
    rng = np.random.default_rng(seed)
    return np.sort(rng.choice(n_obs, size=sample_rows, replace=False))


def summarize_finite_values(
    matrix: Any, *, sample_rows: int = DEFAULT_SAMPLE_ROWS, seed: int = 0
) -> FiniteValueSummary:
    """Check for NaN/Inf values without densifying a sparse matrix.

    For sparse input, only the stored (non-zero) values are inspected --
    structural zeros are always finite, so this remains exact rather than
    approximate. For large inputs, only a bounded, deterministic sample of
    rows is ever materialized, whether the underlying matrix is in-memory or
    backed by an on-disk HDF5 group.
    """
    n_obs = int(matrix.shape[0])
    row_indices = sample_row_indices(n_obs, sample_rows, seed=seed)
    sampled = matrix[row_indices]

    values = np.asarray(sampled.tocsr().data) if sparse.issparse(sampled) else np.asarray(sampled)

    checked = int(np.size(values))
    non_finite = checked - int(np.count_nonzero(np.isfinite(values)))
    return FiniteValueSummary(
        sampled_rows=int(len(row_indices)),
        total_rows=n_obs,
        checked_values=checked,
        non_finite_count=non_finite,
    )
