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


@register_check(name="feature_measurement_families", category=Category.FEATURES)
def check_feature_measurement_families(ctx: CheckContext) -> list[Issue]:
    """Feature names should encode a recognized measurement family after their compartment.

    For example ``Cells_AreaShape_Area`` encodes the ``AreaShape`` family.
    Feature names whose compartment prefix doesn't match anything are
    skipped here -- ``check_feature_compartments`` (``FEAT001``) already
    flags those, and reporting both would be redundant.
    """
    compartments = ctx.resolved_schema.schema.compartments
    families = ctx.resolved_schema.schema.measurement_families
    if not compartments or not families:
        return []

    var_names = [str(name) for name in ctx.handle.adata.var_names]
    unmatched: list[str] = []
    for name in var_names:
        compartment = next((c for c in compartments if name.startswith(f"{c}_")), None)
        if compartment is None:
            continue
        remainder = name[len(compartment) + 1 :]
        family = remainder.split("_", 1)[0]
        if family not in families:
            unmatched.append(name)

    if not unmatched:
        return []

    return [
        Issue(
            code="FEAT002",
            severity=Severity.WARNING,
            category=Category.FEATURES,
            location="var.index",
            message=(
                f"{len(unmatched)} of {len(var_names)} feature name(s) do not encode a "
                f"recognized measurement family ({', '.join(families)}) after their "
                "compartment prefix."
            ),
            evidence=", ".join(unmatched[:_MAX_EVIDENCE_EXAMPLES]),
            remediation=(
                "Name features as '<compartment>_<measurement family>_...' using one of "
                "the schema's declared measurement families, or add the family to the schema."
            ),
            check_name="feature_measurement_families",
        )
    ]
