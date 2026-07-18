"""Tests for canonical field resolution against AnnData obs/var columns."""

from __future__ import annotations

import pandas as pd

from cp_anndata_validator.profiles import ProfileLevel
from cp_anndata_validator.schema.loader import load_builtin_schema
from cp_anndata_validator.schema.resolve import resolve_schema


def test_resolve_schema_matches_case_insensitively() -> None:
    obs = pd.DataFrame({"METADATA_PLATE": ["P1"], "metadata_well": ["A01"]})
    var = pd.DataFrame(index=["f1"])
    schema = load_builtin_schema("jump-cp")

    resolved = resolve_schema(obs, var, schema)

    assert resolved.is_resolved("plate") is True
    assert resolved.column_for("plate") == "METADATA_PLATE"
    assert resolved.is_resolved("well") is True
    assert resolved.column_for("well") == "metadata_well"


def test_resolve_schema_reports_unresolved_fields() -> None:
    obs = pd.DataFrame({"Metadata_Plate": ["P1"]})
    var = pd.DataFrame(index=["f1"])
    schema = load_builtin_schema("jump-cp")

    resolved = resolve_schema(obs, var, schema)

    assert resolved.is_resolved("well") is False
    assert resolved.column_for("well") is None


def test_resolve_schema_first_matching_alias_wins() -> None:
    obs = pd.DataFrame({"plate_id": ["P1"], "Metadata_Plate": ["P1"]})
    var = pd.DataFrame(index=["f1"])
    schema = load_builtin_schema("jump-cp")  # Metadata_Plate listed before plate_id

    resolved = resolve_schema(obs, var, schema)

    assert resolved.column_for("plate") == "Metadata_Plate"


def test_jump_cp_resolves_perturbation_modality_from_generic_alias() -> None:
    """Regression test: jump-cp's perturbation_modality field must keep its
    generic-cell-painting-style alias, not just the Metadata_-prefixed one.

    jump-cp-derivation.md documents that every jump-cp field keeps its
    generic-cell-painting-style alias so mixed-convention datasets still
    resolve. This field briefly regressed to only listing
    ``Metadata_perturbation_modality`` (see docs/checks.md / IDENT007-008),
    which this test guards against reintroducing.
    """
    obs = pd.DataFrame({"perturbation_modality": ["compound"]})
    var = pd.DataFrame(index=["f1"])
    schema = load_builtin_schema("jump-cp")

    resolved = resolve_schema(obs, var, schema)

    assert resolved.is_resolved("perturbation_modality") is True
    assert resolved.column_for("perturbation_modality") == "perturbation_modality"


def test_missing_required_fields_for_level() -> None:
    obs = pd.DataFrame({"Metadata_Plate": ["P1"], "Metadata_Well": ["A01"]})
    var = pd.DataFrame(index=["f1"])
    schema = load_builtin_schema("jump-cp")

    resolved = resolve_schema(obs, var, schema)

    assert resolved.missing_required_fields(ProfileLevel.WELL) == []
    assert sorted(resolved.missing_required_fields(ProfileLevel.SINGLE_CELL)) == [
        "cell_id",
        "site",
    ]
    assert resolved.missing_required_fields(ProfileLevel.TREATMENT) == ["perturbation_id"]
