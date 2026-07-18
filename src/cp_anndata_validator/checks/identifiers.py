"""Identifier completeness, and missing/duplicate observation checks."""

from __future__ import annotations

from typing import cast

import pandas as pd

from cp_anndata_validator.checks.registry import CheckContext, register_check
from cp_anndata_validator.models.issue import Category, Issue, Severity

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
