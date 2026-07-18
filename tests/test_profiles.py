"""Tests for explainable profile-level auto-detection."""

from __future__ import annotations

import pandas as pd

from cp_anndata_validator.profiles import ProfileLevel, detect_profile_level
from cp_anndata_validator.schema.loader import load_builtin_schema
from cp_anndata_validator.schema.resolve import resolve_schema
from tests.fixtures.synthetic import (
    make_single_cell_adata,
    make_treatment_level_adata,
    make_well_level_adata,
)


def test_detects_single_cell_profile() -> None:
    adata = make_single_cell_adata(n_obs=12)
    schema = load_builtin_schema("generic-cell-painting")
    resolved = resolve_schema(adata.obs, adata.var, schema)

    result = detect_profile_level(adata.obs, resolved)

    assert result.detected == ProfileLevel.SINGLE_CELL
    assert result.candidates == (ProfileLevel.SINGLE_CELL,)
    assert result.confidence == 1.0
    assert result.explanation


def test_detects_well_level_profile() -> None:
    adata = make_well_level_adata(n_wells=8)
    schema = load_builtin_schema("generic-cell-painting")
    resolved = resolve_schema(adata.obs, adata.var, schema)

    result = detect_profile_level(adata.obs, resolved)

    assert result.detected == ProfileLevel.WELL


def test_detects_treatment_level_profile() -> None:
    adata = make_treatment_level_adata(n_treatments=5)
    schema = load_builtin_schema("generic-cell-painting")
    resolved = resolve_schema(adata.obs, adata.var, schema)

    result = detect_profile_level(adata.obs, resolved)

    assert result.detected == ProfileLevel.TREATMENT


def test_ambiguous_when_no_required_fields_are_resolved() -> None:
    adata = make_single_cell_adata(n_obs=4)
    adata.obs = adata.obs.drop(columns=["plate_id", "well_id", "site_id", "cell_id"])
    schema = load_builtin_schema("generic-cell-painting")
    resolved = resolve_schema(adata.obs, adata.var, schema)

    result = detect_profile_level(adata.obs, resolved)

    assert result.detected is None
    assert result.candidates == ()
    assert result.confidence == 0.0


def test_ambiguous_when_well_and_treatment_cardinality_coincide() -> None:
    # One perturbation per well (a 1:1 design) makes well vs. treatment
    # genuinely ambiguous from column presence and row cardinality alone.
    obs = pd.DataFrame(
        {
            "plate_id": ["P1", "P1", "P2"],
            "well_id": ["A01", "A02", "A03"],
            "perturbation_id": ["JCP_1", "JCP_2", "JCP_3"],
        }
    )
    var = pd.DataFrame(index=["f1"])
    schema = load_builtin_schema("generic-cell-painting")
    resolved = resolve_schema(obs, var, schema)

    result = detect_profile_level(obs, resolved)

    assert result.detected is None
    assert set(result.candidates) == {ProfileLevel.WELL, ProfileLevel.TREATMENT}
    assert result.is_ambiguous


def test_declared_level_overrides_detected_via_effective() -> None:
    adata = make_single_cell_adata(n_obs=6)
    schema = load_builtin_schema("generic-cell-painting")
    resolved = resolve_schema(adata.obs, adata.var, schema)
    detection = detect_profile_level(adata.obs, resolved)

    declared_result = detection.model_copy(update={"declared": ProfileLevel.WELL})

    assert declared_result.effective == ProfileLevel.WELL
    assert declared_result.detected == ProfileLevel.SINGLE_CELL
    assert declared_result.is_ambiguous is False
