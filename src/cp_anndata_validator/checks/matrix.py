"""Matrix shape/dtype/numeric-validity checks and slot-semantics checks."""

from __future__ import annotations

from cp_anndata_validator.checks.registry import CheckContext, register_check
from cp_anndata_validator.models.issue import Category, Issue, Severity
from cp_anndata_validator.sampling import summarize_finite_values

_NUMERIC_DTYPE_KINDS = "iuf"
_FLOATING_DTYPE_KINDS = "fc"


@register_check(name="matrix_dtype", category=Category.MATRIX)
def check_matrix_dtype(ctx: CheckContext) -> list[Issue]:
    """X must have a numeric dtype."""
    x = ctx.handle.adata.X
    dtype = getattr(x, "dtype", None)
    if x is None or dtype is None or dtype.kind in _NUMERIC_DTYPE_KINDS:
        return []

    return [
        Issue(
            code="MATRIX001",
            severity=Severity.ERROR,
            category=Category.MATRIX,
            location="X",
            message=f"X has a non-numeric dtype ({dtype}).",
            evidence=None,
            remediation="Store feature values as a numeric dtype (integer or floating point).",
            check_name="matrix_dtype",
        )
    ]


@register_check(name="matrix_finite_values", category=Category.MATRIX)
def check_matrix_finite_values(ctx: CheckContext) -> list[Issue]:
    """X should not contain NaN/Inf values; checked via bounded, sparse-safe sampling."""
    x = ctx.handle.adata.X
    dtype = getattr(x, "dtype", None)
    if x is None or dtype is None or dtype.kind not in _FLOATING_DTYPE_KINDS:
        return []

    summary = summarize_finite_values(x, sample_rows=ctx.sample_rows)
    if not summary.has_non_finite:
        return []

    note = " (from a bounded sample)" if summary.was_sampled else ""
    return [
        Issue(
            code="MATRIX002",
            severity=Severity.WARNING,
            category=Category.MATRIX,
            location="X",
            message=f"X contains {summary.non_finite_count} non-finite value(s){note}.",
            evidence=(
                f"checked {summary.checked_values} value(s) across "
                f"{summary.sampled_rows} of {summary.total_rows} row(s)"
            ),
            remediation="Investigate and either impute, mask, or document non-finite values.",
            check_name="matrix_finite_values",
        )
    ]


@register_check(name="layer_shape_consistency", category=Category.MATRIX)
def check_layer_shape_consistency(ctx: CheckContext) -> list[Issue]:
    """Every entry in .layers must share X's shape."""
    adata = ctx.handle.adata
    if adata.X is None:
        return []

    x_shape = ctx.handle.x_shape
    issues: list[Issue] = []
    for layer_name, layer in adata.layers.items():
        layer_shape = (int(layer.shape[0]), int(layer.shape[1]))
        if layer_shape != x_shape:
            issues.append(
                Issue(
                    code="MATRIX004",
                    severity=Severity.ERROR,
                    category=Category.MATRIX,
                    location=f"layers.{layer_name}",
                    message=(
                        f"layers[{layer_name!r}] has shape {layer_shape}, but X has shape "
                        f"{x_shape}."
                    ),
                    evidence=None,
                    remediation="Ensure every layer has the same shape as X.",
                    check_name="layer_shape_consistency",
                )
            )
    return issues


@register_check(name="obsm_varm_alignment", category=Category.SLOT_SEMANTICS)
def check_obsm_varm_alignment(ctx: CheckContext) -> list[Issue]:
    """.obsm entries must align with n_obs and .varm entries must align with n_vars."""
    adata = ctx.handle.adata
    issues: list[Issue] = []

    for name, array in adata.obsm.items():
        if int(array.shape[0]) != ctx.handle.n_obs:
            issues.append(
                Issue(
                    code="SLOT002",
                    severity=Severity.ERROR,
                    category=Category.SLOT_SEMANTICS,
                    location=f"obsm.{name}",
                    message=(
                        f"obsm[{name!r}] has {array.shape[0]} row(s), but there are "
                        f"{ctx.handle.n_obs} observation(s)."
                    ),
                    evidence=None,
                    remediation="Ensure every obsm entry's first dimension matches n_obs.",
                    check_name="obsm_varm_alignment",
                )
            )

    for name, array in adata.varm.items():
        if int(array.shape[0]) != ctx.handle.n_vars:
            issues.append(
                Issue(
                    code="SLOT002",
                    severity=Severity.ERROR,
                    category=Category.SLOT_SEMANTICS,
                    location=f"varm.{name}",
                    message=(
                        f"varm[{name!r}] has {array.shape[0]} row(s), but there are "
                        f"{ctx.handle.n_vars} feature(s)."
                    ),
                    evidence=None,
                    remediation="Ensure every varm entry's first dimension matches n_vars.",
                    check_name="obsm_varm_alignment",
                )
            )

    return issues


@register_check(name="processing_stage_declared", category=Category.SLOT_SEMANTICS)
def check_processing_stage_declared(ctx: CheckContext) -> list[Issue]:
    """X's processing stage (raw/normalized/aggregated/...) should be declared, not assumed."""
    uns = ctx.handle.adata.uns
    stage = uns.get("processing_stage") if hasattr(uns, "get") else None
    if stage:
        return []

    return [
        Issue(
            code="SLOT001",
            severity=Severity.WARNING,
            category=Category.SLOT_SEMANTICS,
            location="uns.processing_stage",
            message="No processing stage is declared for the data stored in X.",
            evidence=None,
            remediation=(
                "Set uns['processing_stage'] (for example 'raw', 'normalized', or 'aggregated')."
            ),
            check_name="processing_stage_declared",
        )
    ]
