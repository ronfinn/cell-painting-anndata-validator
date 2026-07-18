"""Profile levels and explainable auto-detection.

Detection combines two signals:

1. Which profile levels have all of their schema-required canonical fields
   resolved (a purely column-presence signal).
2. For levels that share the same required columns (well vs. treatment both
   only need a resolved ``perturbation_id``/``plate``/``well``), row-level
   cardinality is used to disambiguate: a well-level profile has one row per
   distinct plate/well pair, a treatment-level profile has one row per
   distinct perturbation identifier.

When these signals do not uniquely resolve a single level, detection returns
an ambiguous result (multiple candidates, no single ``detected`` level) --
callers must always be able to override this with a declared profile level.
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from cp_anndata_validator.schema.resolve import ResolvedSchema


class ProfileLevel(StrEnum):
    """The granularity at which observations in an AnnData object are profiled."""

    SINGLE_CELL = "single-cell"
    WELL = "well"
    TREATMENT = "treatment"


class ProfileLevelResult(BaseModel):
    """The declared and/or auto-detected profile level for a dataset."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    declared: ProfileLevel | None = None
    detected: ProfileLevel | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    candidates: tuple[ProfileLevel, ...] = ()
    explanation: str = ""

    @property
    def is_ambiguous(self) -> bool:
        return self.declared is None and self.detected is None and len(self.candidates) > 1

    @property
    def effective(self) -> ProfileLevel | None:
        """The profile level checks should actually run against."""
        if self.declared is not None:
            return self.declared
        if self.detected is not None:
            return self.detected
        return None


def _structurally_satisfied_levels(resolved: ResolvedSchema) -> dict[ProfileLevel, list[str]]:
    return {level: resolved.missing_required_fields(level) for level in ProfileLevel}


def detect_profile_level(obs: pd.DataFrame, resolved: ResolvedSchema) -> ProfileLevelResult:
    """Auto-detect the profile level of a resolved AnnData/schema pairing.

    This never considers a CLI-declared override; callers combine this
    result with a declared level (if any) themselves, so the report can show
    both what was declared and what would have been detected.
    """
    missing_by_level = _structurally_satisfied_levels(resolved)
    reasons = [
        f"{level.value}: all required fields resolved"
        if not missing
        else f"{level.value}: missing required field(s) {', '.join(sorted(missing))}"
        for level, missing in missing_by_level.items()
    ]
    structurally_satisfied = [level for level, missing in missing_by_level.items() if not missing]

    if not structurally_satisfied:
        return ProfileLevelResult(
            detected=None, confidence=0.0, candidates=(), explanation="; ".join(reasons)
        )

    has_cell_granularity = resolved.is_resolved("cell_id") or resolved.is_resolved("site")

    if ProfileLevel.SINGLE_CELL in structurally_satisfied and has_cell_granularity:
        reasons.append("resolved cell/site identifiers indicate single-cell granularity")
        return ProfileLevelResult(
            detected=ProfileLevel.SINGLE_CELL,
            confidence=1.0,
            candidates=(ProfileLevel.SINGLE_CELL,),
            explanation="; ".join(reasons),
        )

    remaining = [level for level in structurally_satisfied if level != ProfileLevel.SINGLE_CELL]
    n_rows = len(obs)

    well_matches_rows = False
    plate_col, well_col = resolved.column_for("plate"), resolved.column_for("well")
    if ProfileLevel.WELL in remaining and plate_col and well_col:
        n_unique_wells = obs[[plate_col, well_col]].drop_duplicates().shape[0]
        well_matches_rows = n_unique_wells == n_rows
        reasons.append(f"well: {n_unique_wells} unique plate/well pairs across {n_rows} row(s)")

    treatment_matches_rows = False
    pert_col = resolved.column_for("perturbation_id")
    if ProfileLevel.TREATMENT in remaining and pert_col:
        n_unique_pert = int(obs[pert_col].nunique(dropna=True))
        treatment_matches_rows = n_unique_pert == n_rows
        reasons.append(
            f"treatment: {n_unique_pert} unique perturbation identifier(s) across {n_rows} row(s)"
        )

    if well_matches_rows and not treatment_matches_rows:
        return ProfileLevelResult(
            detected=ProfileLevel.WELL,
            confidence=1.0,
            candidates=(ProfileLevel.WELL,),
            explanation="; ".join(reasons),
        )
    if treatment_matches_rows and not well_matches_rows:
        return ProfileLevelResult(
            detected=ProfileLevel.TREATMENT,
            confidence=1.0,
            candidates=(ProfileLevel.TREATMENT,),
            explanation="; ".join(reasons),
        )

    candidates = tuple(remaining) if remaining else tuple(structurally_satisfied)
    confidence = 1.0 / len(candidates) if candidates else 0.0
    reasons.append(
        "row-level cardinality of plate/well vs. perturbation identifiers did not "
        "uniquely resolve the profile level"
    )
    return ProfileLevelResult(
        detected=None,
        confidence=confidence,
        candidates=candidates,
        explanation="; ".join(reasons),
    )
