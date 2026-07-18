"""Batch, plate and experiment metadata checks."""

from __future__ import annotations

from cp_anndata_validator.checks.registry import CheckContext, register_check
from cp_anndata_validator.models.issue import Category, Issue, Severity


@register_check(name="batch_identifier_declared", category=Category.METADATA)
def check_batch_identifier_declared(ctx: CheckContext) -> list[Issue]:
    """A batch identifier is not strictly required, but its absence is worth noting."""
    if ctx.resolved_schema.is_resolved("batch"):
        return []

    return [
        Issue(
            code="META001",
            severity=Severity.INFORMATION,
            category=Category.METADATA,
            location="obs.batch",
            message="No batch identifier column was resolved.",
            evidence=None,
            remediation=(
                "Add a batch identifier column if this dataset spans multiple experimental batches."
            ),
            check_name="batch_identifier_declared",
        )
    ]


@register_check(name="experiment_metadata_declared", category=Category.METADATA)
def check_experiment_metadata_declared(ctx: CheckContext) -> list[Issue]:
    """Experiment-level metadata should be recorded in uns['experiment']."""
    uns = ctx.handle.adata.uns
    experiment = uns.get("experiment") if hasattr(uns, "get") else None
    if isinstance(experiment, dict) and experiment:
        return []

    return [
        Issue(
            code="META002",
            severity=Severity.WARNING,
            category=Category.METADATA,
            location="uns.experiment",
            message="No experiment metadata block (uns['experiment']) was found.",
            evidence=None,
            remediation=(
                "Record experiment-level metadata (for example instrument, protocol, date) "
                "in uns['experiment']."
            ),
            check_name="experiment_metadata_declared",
        )
    ]
