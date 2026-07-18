"""Basic AI-readiness checks: constant features and missing-value fraction.

Both checks operate on the same bounded, deterministic row sample used by
:mod:`cp_anndata_validator.checks.matrix` -- a small sample is materialized
(never the full matrix), which is an acceptable, explicit exception to
"never densify a sparse matrix" since the *sample itself* is already bounded
in size before densification.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from scipy import sparse

from cp_anndata_validator.checks.registry import CheckContext, register_check
from cp_anndata_validator.models.issue import Category, Issue, Severity
from cp_anndata_validator.sampling import sample_row_indices

_MAX_EVIDENCE_EXAMPLES = 5
_MISSING_FRACTION_THRESHOLD = 0.2
_FLOATING_DTYPE_KINDS = "fc"


def _dense_sample(ctx: CheckContext) -> np.ndarray | None:
    x: Any = ctx.handle.adata.X
    if x is None:
        return None
    row_indices = sample_row_indices(int(x.shape[0]), ctx.sample_rows)
    sampled = x[row_indices]
    dense: np.ndarray = sampled.toarray() if sparse.issparse(sampled) else np.asarray(sampled)
    return dense


@register_check(name="constant_features", category=Category.AI_READINESS)
def check_constant_features(ctx: CheckContext) -> list[Issue]:
    """Zero-variance feature columns rarely help model training."""
    dense = _dense_sample(ctx)
    if dense is None or dense.size == 0:
        return []

    variances = np.nanvar(dense, axis=0)
    constant_mask = variances == 0
    n_constant = int(np.count_nonzero(constant_mask))
    if n_constant == 0:
        return []

    var_names = [str(name) for name in ctx.handle.adata.var_names]
    example_names = [var_names[i] for i in np.flatnonzero(constant_mask)[:_MAX_EVIDENCE_EXAMPLES]]

    return [
        Issue(
            code="AI001",
            severity=Severity.INFORMATION,
            category=Category.AI_READINESS,
            location="X",
            message=(
                f"{n_constant} of {dense.shape[1]} feature column(s) are constant across "
                "the sampled rows."
            ),
            evidence=", ".join(example_names),
            remediation="Consider removing zero-variance features before model training.",
            check_name="constant_features",
        )
    ]


@register_check(name="missing_value_fraction", category=Category.AI_READINESS)
def check_missing_value_fraction(ctx: CheckContext) -> list[Issue]:
    """A high fraction of NaN feature values usually needs an explicit imputation strategy."""
    x = ctx.handle.adata.X
    dtype = getattr(x, "dtype", None)
    if x is None or dtype is None or dtype.kind not in _FLOATING_DTYPE_KINDS:
        return []

    dense = _dense_sample(ctx)
    if dense is None or dense.size == 0:
        return []

    fraction_missing = float(np.isnan(dense).mean())
    if fraction_missing <= _MISSING_FRACTION_THRESHOLD:
        return []

    return [
        Issue(
            code="AI002",
            severity=Severity.WARNING,
            category=Category.AI_READINESS,
            location="X",
            message=f"{fraction_missing:.0%} of sampled feature values are missing (NaN).",
            evidence=f"threshold: {_MISSING_FRACTION_THRESHOLD:.0%}",
            remediation="Impute, mask, or document missing feature values before model training.",
            check_name="missing_value_fraction",
        )
    ]
