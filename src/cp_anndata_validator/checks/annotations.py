"""Control and treatment annotation checks."""

from __future__ import annotations

from typing import cast

import pandas as pd

from cp_anndata_validator.checks.registry import CheckContext, register_check
from cp_anndata_validator.models.issue import Category, Issue, Severity

_RECOGNIZED_CONTROL_LABELS = {"negcon", "poscon", "trt", "control", "treatment", "unknown"}
# JUMP-style finer-grained labels (poscon_cp, negcon_cpjump, ...) — prefix match
# after lowercasing, not arbitrary substring match.
_RECOGNIZED_CONTROL_PREFIXES = ("negcon_", "poscon_")
_NEGATIVE_CONTROL_LABELS = {"negcon", "negative_control", "control"}
_NEGATIVE_CONTROL_PREFIXES = ("negcon_",)
_MAX_EVIDENCE_EXAMPLES = 5


def _is_recognized_control_label(value: str) -> bool:
    return value in _RECOGNIZED_CONTROL_LABELS or value.startswith(_RECOGNIZED_CONTROL_PREFIXES)


def _has_negative_control(values: set[str]) -> bool:
    return bool(values & _NEGATIVE_CONTROL_LABELS) or any(
        value.startswith(_NEGATIVE_CONTROL_PREFIXES) for value in values
    )


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

    unrecognized = sorted(
        value for value in unique_values if not _is_recognized_control_label(value)
    )
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
                    "treatment), a JUMP-style prefix (negcon_..., poscon_...), or extend "
                    "the schema/documentation to cover this label."
                ),
                check_name="control_annotations",
            )
        )

    if not _has_negative_control(unique_values):
        issues.append(
            Issue(
                code="CTRL003",
                severity=Severity.WARNING,
                category=Category.ANNOTATIONS,
                location=f"obs.{column}",
                message="No negative control annotation was found.",
                evidence=None,
                remediation=(
                    "Include at least one negative control (for example labeled 'negcon' "
                    "or 'negcon_...') to support downstream normalization and QC."
                ),
                check_name="control_annotations",
            )
        )

    return issues
