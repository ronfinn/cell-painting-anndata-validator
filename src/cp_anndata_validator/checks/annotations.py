"""Control and treatment annotation checks."""

from __future__ import annotations

from typing import cast

import pandas as pd

from cp_anndata_validator.checks.registry import CheckContext, register_check
from cp_anndata_validator.models.issue import Category, Issue, Severity

_RECOGNIZED_CONTROL_LABELS = {"negcon", "poscon", "trt", "control", "treatment", "unknown"}
_NEGATIVE_CONTROL_LABELS = {"negcon", "negative_control", "control"}
_MAX_EVIDENCE_EXAMPLES = 5


@register_check(name="control_annotations", category=Category.ANNOTATIONS)
def check_control_annotations(ctx: CheckContext) -> list[Issue]:
    """A control/treatment column should exist, use recognized labels, and include a negcon."""
    column = ctx.resolved_schema.column_for("control_type")
    if column is None:
        return [
            Issue(
                code="CTRL001",
                severity=Severity.WARNING,
                category=Category.ANNOTATIONS,
                location="obs.control_type",
                message="No control/treatment annotation column was resolved.",
                evidence=None,
                remediation=(
                    "Add a control/treatment annotation column (for example "
                    "Metadata_pert_type) with values such as negcon/poscon/trt."
                ),
                check_name="control_annotations",
            )
        ]

    obs = cast(pd.DataFrame, ctx.handle.adata.obs)
    values = obs[column].dropna().astype(str).str.strip().str.lower()
    unique_values = set(values.unique())
    issues: list[Issue] = []

    unrecognized = sorted(unique_values - _RECOGNIZED_CONTROL_LABELS)
    if unrecognized:
        issues.append(
            Issue(
                code="CTRL002",
                severity=Severity.WARNING,
                category=Category.ANNOTATIONS,
                location=f"obs.{column}",
                message=f"{len(unrecognized)} unrecognized control/treatment label value(s).",
                evidence=", ".join(unrecognized[:_MAX_EVIDENCE_EXAMPLES]),
                remediation=(
                    "Use one of the recognized labels (negcon, poscon, trt, control, "
                    "treatment), or extend the schema/documentation to cover this label."
                ),
                check_name="control_annotations",
            )
        )

    if not (unique_values & _NEGATIVE_CONTROL_LABELS):
        issues.append(
            Issue(
                code="CTRL003",
                severity=Severity.WARNING,
                category=Category.ANNOTATIONS,
                location=f"obs.{column}",
                message="No negative control annotation was found.",
                evidence=None,
                remediation=(
                    "Include at least one negative control (for example labeled 'negcon') "
                    "to support downstream normalization and QC."
                ),
                check_name="control_annotations",
            )
        )

    return issues
