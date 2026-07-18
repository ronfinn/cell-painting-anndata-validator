"""Aggregation provenance checks for well- and treatment-level profiles."""

from __future__ import annotations

from typing import Any

from cp_anndata_validator.checks.registry import CheckContext, register_check
from cp_anndata_validator.models.issue import Category, Issue, Severity
from cp_anndata_validator.profiles import ProfileLevel

_AGGREGATED_LEVELS = (ProfileLevel.WELL, ProfileLevel.TREATMENT)


def _applies_to_aggregated_levels(ctx: CheckContext) -> bool:
    return ctx.profile.effective in _AGGREGATED_LEVELS


def _aggregation_block(ctx: CheckContext) -> dict[str, Any] | None:
    uns = ctx.handle.adata.uns
    aggregation = uns.get("aggregation") if hasattr(uns, "get") else None
    return aggregation if isinstance(aggregation, dict) else None


def has_adequate_aggregation_provenance(ctx: CheckContext) -> bool:
    """Whether ``uns['aggregation']`` documents both *how* and *from what* rows were derived.

    "Adequate" means at least a declared ``method`` and a declared
    ``source_level`` (the profile level the rows were aggregated from, for
    example ``"single-cell"`` or ``"well"``). This is used by
    :mod:`cp_anndata_validator.checks.identifiers` to decide whether a
    treatment-level profile can skip requiring direct plate/well identifiers.
    """
    aggregation = _aggregation_block(ctx)
    return bool(aggregation and aggregation.get("method") and aggregation.get("source_level"))


@register_check(
    name="aggregation_provenance",
    category=Category.AGGREGATION,
    applies=_applies_to_aggregated_levels,
)
def check_aggregation_provenance(ctx: CheckContext) -> list[Issue]:
    """Well/treatment profiles must declare their aggregation method and replicate count."""
    aggregation = _aggregation_block(ctx)
    level = ctx.profile.effective
    level_name = level.value if level else "aggregated"

    if not aggregation or not aggregation.get("method"):
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

    if not aggregation.get("source_level"):
        return [
            Issue(
                code="AGG003",
                severity=Severity.WARNING,
                category=Category.AGGREGATION,
                location="uns.aggregation",
                message=(
                    "No source profile level is declared for this aggregated profile "
                    "(uns['aggregation']['source_level'])."
                ),
                evidence=None,
                remediation=(
                    "Record which profile level rows were aggregated from (for example "
                    "'single-cell' or 'well') in uns['aggregation']['source_level']."
                ),
                check_name="aggregation_provenance",
            )
        ]

    return []
