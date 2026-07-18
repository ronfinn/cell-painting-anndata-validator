"""AnnData structure and index-uniqueness checks.

File readability itself (rule ``STRUCT001``) is handled one layer down, by
:class:`cp_anndata_validator.loading.LoadError`: an unreadable/corrupt file
can never reach the point of having a :class:`CheckContext` built for it, so
there is no corresponding registered check here -- it is surfaced directly
as a CLI/API error (exit code 2), not as a report issue.
"""

from __future__ import annotations

from cp_anndata_validator.checks.registry import CheckContext, register_check
from cp_anndata_validator.models.issue import Category, Issue, Severity


@register_check(name="matrix_structure", category=Category.STRUCTURE)
def check_matrix_structure(ctx: CheckContext) -> list[Issue]:
    """The AnnData object must have a non-empty, present .X matrix."""
    handle = ctx.handle
    x_missing = handle.adata.X is None
    if handle.n_obs > 0 and handle.n_vars > 0 and not x_missing:
        return []

    return [
        Issue(
            code="STRUCT002",
            severity=Severity.ERROR,
            category=Category.STRUCTURE,
            location="X",
            message="The AnnData object has no observations, no features, or no X matrix.",
            evidence=f"n_obs={handle.n_obs}, n_vars={handle.n_vars}, X is None={x_missing}",
            remediation="Provide a non-empty X matrix with at least one observation and feature.",
            check_name="matrix_structure",
        )
    ]


@register_check(name="index_uniqueness", category=Category.STRUCTURE)
def check_index_uniqueness(ctx: CheckContext) -> list[Issue]:
    """obs_names and var_names must be unique and non-empty."""
    adata = ctx.handle.adata
    issues: list[Issue] = []

    for axis_name, index in (("obs", adata.obs.index), ("var", adata.var.index)):
        duplicated = index[index.duplicated()].unique()
        if len(duplicated) > 0:
            code = "INDEX001" if axis_name == "obs" else "INDEX002"
            issues.append(
                Issue(
                    code=code,
                    severity=Severity.ERROR,
                    category=Category.STRUCTURE,
                    location=f"{axis_name}.index",
                    message=f"{axis_name}_names contains {len(duplicated)} duplicated value(s).",
                    evidence=", ".join(map(str, duplicated[:5])),
                    remediation=f"Ensure every {axis_name}_names value is unique.",
                    check_name="index_uniqueness",
                )
            )

        empty_mask = index.astype(str).str.strip() == ""
        if bool(empty_mask.any()):
            issues.append(
                Issue(
                    code="INDEX003",
                    severity=Severity.ERROR,
                    category=Category.STRUCTURE,
                    location=f"{axis_name}.index",
                    message=(f"{axis_name}_names contains {int(empty_mask.sum())} empty value(s)."),
                    evidence=None,
                    remediation=f"Assign a non-empty identifier to every {axis_name} entry.",
                    check_name="index_uniqueness",
                )
            )

    return issues
