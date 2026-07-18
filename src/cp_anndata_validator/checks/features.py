"""Feature name and compartment checks."""

from __future__ import annotations

from cp_anndata_validator.checks.registry import CheckContext, register_check
from cp_anndata_validator.models.issue import Category, Issue, Severity

_MAX_EVIDENCE_EXAMPLES = 5


@register_check(name="feature_compartments", category=Category.FEATURES)
def check_feature_compartments(ctx: CheckContext) -> list[Issue]:
    """Feature names should be prefixed with one of the schema's declared compartments."""
    compartments = ctx.resolved_schema.schema.compartments
    if not compartments:
        return []

    var_names = [str(name) for name in ctx.handle.adata.var_names]
    unmatched = [
        name for name in var_names if not any(name.startswith(f"{c}_") for c in compartments)
    ]
    if not unmatched:
        return []

    return [
        Issue(
            code="FEAT001",
            severity=Severity.WARNING,
            category=Category.FEATURES,
            location="var.index",
            message=(
                f"{len(unmatched)} of {len(var_names)} feature name(s) do not start with any "
                f"of the schema's declared compartments ({', '.join(compartments)})."
            ),
            evidence=", ".join(unmatched[:_MAX_EVIDENCE_EXAMPLES]),
            remediation=(
                "Prefix feature names with a declared compartment (for example "
                "'Cells_'), or add the compartment to the schema."
            ),
            check_name="feature_compartments",
        )
    ]
