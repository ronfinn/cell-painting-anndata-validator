"""Identifier completeness, and missing/duplicate observation checks."""

from __future__ import annotations

from typing import cast

import pandas as pd

from cp_anndata_validator.checks.aggregation import has_adequate_aggregation_provenance
from cp_anndata_validator.checks.registry import CheckContext, register_check
from cp_anndata_validator.models.issue import Category, Issue, Severity
from cp_anndata_validator.profiles import ProfileLevel

_IDENTIFIER_RULE_CODES: dict[str, str] = {
    "plate": "IDENT001",
    "well": "IDENT002",
    "site": "IDENT003",
    "cell_id": "IDENT004",
    "perturbation_id": "IDENT005",
}

_CANDIDATE_IDENTIFIER_FIELDS = ("plate", "well", "site", "cell_id", "perturbation_id")


def _identifier_completeness_applies(ctx: CheckContext) -> bool:
    return ctx.profile.effective is not None


@register_check(
    name="identifier_completeness",
    category=Category.IDENTIFIERS,
    applies=_identifier_completeness_applies,
)
def check_identifier_completeness(ctx: CheckContext) -> list[Issue]:
    """Every canonical identifier required for the effective profile level must resolve."""
    level = ctx.profile.effective
    if level is None:  # pragma: no cover - guarded by `applies`
        return []

    issues: list[Issue] = []
    for field_name in ctx.resolved_schema.missing_required_fields(level):
        spec = ctx.resolved_schema.schema.fields.get(field_name)
        code = _IDENTIFIER_RULE_CODES.get(field_name, "IDENT000")
        issues.append(
            Issue(
                code=code,
                severity=Severity.ERROR,
                category=Category.IDENTIFIERS,
                location=f"obs.{field_name}",
                message=(
                    f"No column matched the canonical field {field_name!r}, which is "
                    f"required for the {level.value} profile level."
                ),
                evidence=(f"checked aliases: {', '.join(spec.aliases)}" if spec else None),
                remediation=(
                    f"Add an .obs column for {field_name!r} using one of the schema's "
                    "declared aliases, or choose a schema/profile level that matches this "
                    "dataset."
                ),
                check_name="identifier_completeness",
            )
        )
    return issues


def _resolved_identifier_columns(ctx: CheckContext) -> list[str]:
    level = ctx.profile.effective
    relevant = (
        set(ctx.resolved_schema.schema.fields_required_for(level))
        if level is not None
        else set(_CANDIDATE_IDENTIFIER_FIELDS)
    )
    columns = []
    for field_name in _CANDIDATE_IDENTIFIER_FIELDS:
        if field_name in relevant:
            column = ctx.resolved_schema.column_for(field_name)
            if column is not None:
                columns.append(column)
    return columns


@register_check(name="observation_completeness", category=Category.IDENTIFIERS)
def check_observation_completeness(ctx: CheckContext) -> list[Issue]:
    """Missing and duplicated observations, based on resolved identifier columns."""
    obs = cast(pd.DataFrame, ctx.handle.adata.obs)
    columns = _resolved_identifier_columns(ctx)
    issues: list[Issue] = []

    for column in columns:
        n_missing = int(obs[column].isna().sum())
        if n_missing > 0:
            issues.append(
                Issue(
                    code="OBS002",
                    severity=Severity.ERROR,
                    category=Category.IDENTIFIERS,
                    location=f"obs.{column}",
                    message=(
                        f"{n_missing} of {len(obs)} row(s) have a missing value in {column!r}."
                    ),
                    evidence=None,
                    remediation=(
                        f"Populate {column!r} for every observation, or remove incomplete rows."
                    ),
                    check_name="observation_completeness",
                )
            )

    if columns:
        duplicated_mask = obs[columns].duplicated(keep=False)
        n_duplicated_rows = int(duplicated_mask.sum())
        if n_duplicated_rows > 0:
            issues.append(
                Issue(
                    code="OBS001",
                    severity=Severity.ERROR,
                    category=Category.IDENTIFIERS,
                    location="obs." + ",".join(columns),
                    message=(
                        f"{n_duplicated_rows} observation(s) share an identical "
                        f"({', '.join(columns)}) identifier tuple with at least one other row."
                    ),
                    evidence=None,
                    remediation=(
                        "Ensure each observation's identifier columns uniquely identify it, "
                        "or remove/merge duplicated rows."
                    ),
                    check_name="observation_completeness",
                )
            )

    return issues


def _applies_to_treatment_level(ctx: CheckContext) -> bool:
    return ctx.profile.effective == ProfileLevel.TREATMENT


@register_check(
    name="treatment_traceability",
    category=Category.IDENTIFIERS,
    applies=_applies_to_treatment_level,
)
def check_treatment_traceability(ctx: CheckContext) -> list[Issue]:
    """A treatment-level profile must be traceable back to its source wells.

    Plate/well identifiers are not required directly on treatment-level rows
    (they were aggregated away), *provided* ``uns['aggregation']`` documents
    both how (``method``) and from what (``source_level``) the aggregation
    was performed -- see
    :func:`cp_anndata_validator.checks.aggregation.has_adequate_aggregation_provenance`.
    Without direct plate/well columns *and* without that provenance, a
    treatment-level profile cannot be traced back to any source data at all.
    """
    has_plate = ctx.resolved_schema.is_resolved("plate")
    has_well = ctx.resolved_schema.is_resolved("well")
    if has_plate and has_well:
        return []
    if has_adequate_aggregation_provenance(ctx):
        return []

    return [
        Issue(
            code="IDENT006",
            severity=Severity.ERROR,
            category=Category.IDENTIFIERS,
            location="obs.plate,obs.well",
            message=(
                "This treatment-level profile has neither direct plate/well identifiers "
                "nor adequate aggregation provenance (uns['aggregation']['method'] and "
                "['source_level']), so its rows cannot be traced back to source data."
            ),
            evidence=f"plate resolved={has_plate}, well resolved={has_well}",
            remediation=(
                "Either keep plate/well identifier columns on treatment-level rows, or "
                "declare uns['aggregation'] with both 'method' and 'source_level'."
            ),
            check_name="treatment_traceability",
        )
    ]


_RECOGNIZED_PERTURBATION_MODALITIES = {"compound", "orf", "crispr", "crispr_ko", "crispr_a"}


def _perturbation_modality_applies(ctx: CheckContext) -> bool:
    return ctx.resolved_schema.is_resolved("perturbation_id")


@register_check(
    name="perturbation_modality",
    category=Category.IDENTIFIERS,
    applies=_perturbation_modality_applies,
)
def check_perturbation_modality(ctx: CheckContext) -> list[Issue]:
    """Whenever a perturbation identifier resolves, its modality should also be declared."""
    column = ctx.resolved_schema.column_for("perturbation_modality")
    if column is None:
        return [
            Issue(
                code="IDENT007",
                severity=Severity.WARNING,
                category=Category.IDENTIFIERS,
                location="obs.perturbation_modality",
                message="No perturbation modality column was resolved.",
                evidence=None,
                remediation=(
                    "Add a perturbation modality column (for example "
                    "Metadata_perturbation_modality) with a value such as "
                    "compound/orf/crispr."
                ),
                check_name="perturbation_modality",
            )
        ]

    obs = cast(pd.DataFrame, ctx.handle.adata.obs)
    values = set(obs[column].dropna().astype(str).str.strip().str.lower().unique())
    unrecognized = sorted(values - _RECOGNIZED_PERTURBATION_MODALITIES - {"unknown"})
    if not unrecognized:
        return []

    return [
        Issue(
            code="IDENT008",
            severity=Severity.WARNING,
            category=Category.IDENTIFIERS,
            location=f"obs.{column}",
            message=f"{len(unrecognized)} unrecognized perturbation modality value(s).",
            evidence=", ".join(unrecognized[:5]),
            remediation=(
                "Use a recognized modality (compound, orf, crispr, crispr_ko, crispr_a, "
                "unknown), or extend the schema/documentation to cover this value."
            ),
            check_name="perturbation_modality",
        )
    ]
