"""Aggregation provenance checks for well- and treatment-level profiles."""

from __future__ import annotations

from cp_anndata_validator.checks.registry import CheckContext, register_check
from cp_anndata_validator.models.issue import Category, Issue, Severity
from cp_anndata_validator.profiles import ProfileLevel

_AGGREGATED_LEVELS = (ProfileLevel.WELL, ProfileLevel.TREATMENT)


def _applies_to_aggregated_levels(ctx: CheckContext) -> bool:
    return ctx.profile.effective in _AGGREGATED_LEVELS


@register_check(
    name="aggregation_provenance",
    category=Category.AGGREGATION,
    applies=_applies_to_aggregated_levels,
)
def check_aggregation_provenance(ctx: CheckContext) -> list[Issue]:
    """Well/treatment profiles must declare their aggregation method and replicate count."""
    uns = ctx.handle.adata.uns
    aggregation = uns.get("aggregation") if hasattr(uns, "get") else None
    level = ctx.profile.effective
    level_name = level.value if level else "aggregated"

    if not isinstance(aggregation, dict) or not aggregation.get("method"):
        return [
            Issue(
                code="AGG001",
                severity=Severity.ERROR,
                category=Category.AGGREGATION,
                location="uns.aggregation",
                message=(
                    "No aggregation method is declared (uns['aggregation']['method']), but "
                    f"this dataset is a {level_name} profile."
                ),
                evidence=None,
                remediation="Record how rows were aggregated in uns['aggregation']['method'].",
                check_name="aggregation_provenance",
            )
        ]

    if not (aggregation.get("replicate_count") or aggregation.get("n_replicates")):
        return [
            Issue(
                code="AGG002",
                severity=Severity.WARNING,
                category=Category.AGGREGATION,
                location="uns.aggregation",
                message="No replicate count is declared for this aggregated profile.",
                evidence=None,
                remediation=(
                    "Record the number of replicates aggregated per row in "
                    "uns['aggregation']['replicate_count']."
                ),
                check_name="aggregation_provenance",
            )
        ]

    return []
