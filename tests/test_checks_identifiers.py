"""Tests for identifier completeness and observation completeness checks."""

from __future__ import annotations

from pathlib import Path

import anndata as ad
import numpy as np

from cp_anndata_validator.checks.identifiers import (
    check_identifier_completeness,
    check_observation_completeness,
    check_perturbation_modality,
    check_treatment_traceability,
)
from cp_anndata_validator.checks.registry import CheckContext
from cp_anndata_validator.loading import AnnDataHandle
from cp_anndata_validator.profiles import ProfileLevel, detect_profile_level
from cp_anndata_validator.schema.loader import load_builtin_schema
from cp_anndata_validator.schema.resolve import resolve_schema
from tests.fixtures.synthetic import (
    make_single_cell_adata,
    make_treatment_level_adata,
    make_well_level_adata,
)


def make_context(adata: ad.AnnData, *, declared: ProfileLevel | None = None) -> CheckContext:
    handle = AnnDataHandle(adata=adata, path=Path("fake.h5ad"), size_bytes=0, backed=False)
    schema = load_builtin_schema("generic-cell-painting")
    resolved = resolve_schema(adata.obs, adata.var, schema)
    detection = detect_profile_level(adata.obs, resolved)
    profile = detection.model_copy(update={"declared": declared}) if declared else detection
    return CheckContext(handle=handle, resolved_schema=resolved, profile=profile)


def test_identifier_completeness_passes_for_valid_single_cell_fixture() -> None:
    ctx = make_context(make_single_cell_adata())
    assert check_identifier_completeness(ctx) == []


def test_identifier_completeness_flags_missing_site_and_cell_id() -> None:
    adata = make_single_cell_adata()
    adata.obs = adata.obs.drop(columns=["site_id", "cell_id"])
    ctx = make_context(adata, declared=ProfileLevel.SINGLE_CELL)

    issues = check_identifier_completeness(ctx)

    codes = {issue.code for issue in issues}
    assert codes == {"IDENT003", "IDENT004"}
    for issue in issues:
        assert issue.check_name == "identifier_completeness"
        assert issue.evidence is not None


def test_identifier_completeness_skipped_when_ambiguous_and_undeclared() -> None:
    adata = make_single_cell_adata(n_obs=4)
    adata.obs = adata.obs.drop(columns=["plate_id", "well_id", "site_id", "cell_id"])
    ctx = make_context(adata)
    assert ctx.profile.effective is None
    assert check_identifier_completeness(ctx) == []


def test_identifier_completeness_passes_for_well_level_fixture() -> None:
    ctx = make_context(make_well_level_adata(), declared=ProfileLevel.WELL)
    assert check_identifier_completeness(ctx) == []


def test_identifier_completeness_does_not_require_cell_id_for_well_level() -> None:
    adata = make_well_level_adata()
    assert "cell_id" not in adata.obs.columns
    ctx = make_context(adata, declared=ProfileLevel.WELL)

    issues = check_identifier_completeness(ctx)

    assert "IDENT004" not in [issue.code for issue in issues]


def test_identifier_completeness_flags_missing_perturbation_for_treatment() -> None:
    adata = make_treatment_level_adata()
    adata.obs = adata.obs.drop(columns=["perturbation_id"])
    ctx = make_context(adata, declared=ProfileLevel.TREATMENT)

    issues = check_identifier_completeness(ctx)

    assert [issue.code for issue in issues] == ["IDENT005"]


def test_observation_completeness_passes_for_valid_fixture() -> None:
    ctx = make_context(make_single_cell_adata(), declared=ProfileLevel.SINGLE_CELL)
    assert check_observation_completeness(ctx) == []


def test_observation_completeness_detects_missing_values() -> None:
    adata = make_single_cell_adata(n_obs=4)
    adata.obs.loc[adata.obs.index[0], "plate_id"] = np.nan
    ctx = make_context(adata, declared=ProfileLevel.SINGLE_CELL)

    issues = check_observation_completeness(ctx)

    obs002 = [issue for issue in issues if issue.code == "OBS002"]
    assert len(obs002) == 1
    assert "plate_id" in obs002[0].location


def test_observation_completeness_detects_duplicate_identifier_tuples() -> None:
    adata = make_single_cell_adata(n_obs=4)
    adata.obs.loc[adata.obs.index[1], ["plate_id", "well_id", "site_id", "cell_id"]] = (
        adata.obs.loc[adata.obs.index[0], ["plate_id", "well_id", "site_id", "cell_id"]].to_numpy()
    )
    ctx = make_context(adata, declared=ProfileLevel.SINGLE_CELL)

    issues = check_observation_completeness(ctx)

    assert "OBS001" in [issue.code for issue in issues]


def test_treatment_traceability_passes_with_direct_plate_and_well() -> None:
    adata = make_treatment_level_adata()
    adata.obs["plate_id"] = "Plate1"
    adata.obs["well_id"] = "A01"
    ctx = make_context(adata, declared=ProfileLevel.TREATMENT)

    assert check_treatment_traceability(ctx) == []


def test_treatment_traceability_passes_with_adequate_aggregation_provenance() -> None:
    # make_treatment_level_adata() has no plate/well columns, but does declare
    # adequate uns['aggregation'] (method + source_level) provenance.
    ctx = make_context(make_treatment_level_adata(), declared=ProfileLevel.TREATMENT)
    assert check_treatment_traceability(ctx) == []


def test_treatment_traceability_flags_missing_plate_well_and_provenance() -> None:
    adata = make_treatment_level_adata()
    del adata.uns["aggregation"]
    ctx = make_context(adata, declared=ProfileLevel.TREATMENT)

    issues = check_treatment_traceability(ctx)

    assert [issue.code for issue in issues] == ["IDENT006"]
    assert issues[0].severity.value == "error"


def test_treatment_traceability_flags_inadequate_aggregation_provenance() -> None:
    adata = make_treatment_level_adata()
    adata.uns["aggregation"] = {"method": "median"}  # no source_level
    ctx = make_context(adata, declared=ProfileLevel.TREATMENT)

    issues = check_treatment_traceability(ctx)

    assert [issue.code for issue in issues] == ["IDENT006"]


def test_treatment_traceability_does_not_apply_outside_treatment_level() -> None:
    from cp_anndata_validator.checks.identifiers import _applies_to_treatment_level

    ctx = make_context(make_single_cell_adata(), declared=ProfileLevel.SINGLE_CELL)
    assert _applies_to_treatment_level(ctx) is False


def test_perturbation_modality_not_applicable_without_perturbation_id() -> None:
    ctx = make_context(make_single_cell_adata(), declared=ProfileLevel.SINGLE_CELL)
    from cp_anndata_validator.checks.identifiers import _perturbation_modality_applies

    assert _perturbation_modality_applies(ctx) is False


def test_perturbation_modality_flags_missing_column() -> None:
    ctx = make_context(make_treatment_level_adata(), declared=ProfileLevel.TREATMENT)

    issues = check_perturbation_modality(ctx)

    assert [issue.code for issue in issues] == ["IDENT007"]
    assert issues[0].severity.value == "warning"


def test_perturbation_modality_passes_for_recognized_values() -> None:
    adata = make_treatment_level_adata()
    adata.obs["perturbation_modality"] = "compound"
    ctx = make_context(adata, declared=ProfileLevel.TREATMENT)

    assert check_perturbation_modality(ctx) == []


def test_perturbation_modality_flags_unrecognized_values() -> None:
    adata = make_treatment_level_adata()
    adata.obs["perturbation_modality"] = ["not-a-real-modality"] * adata.n_obs
    ctx = make_context(adata, declared=ProfileLevel.TREATMENT)

    issues = check_perturbation_modality(ctx)

    assert [issue.code for issue in issues] == ["IDENT008"]
    assert "not-a-real-modality" in issues[0].evidence
