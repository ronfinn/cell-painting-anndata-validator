"""Tests for aggregation provenance checks (well/treatment profile levels only)."""

from __future__ import annotations

from pathlib import Path

import anndata as ad

from cp_anndata_validator.checks.aggregation import (
    check_aggregation_provenance,
    has_adequate_aggregation_provenance,
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


def test_applies_only_to_well_and_treatment_levels() -> None:
    from cp_anndata_validator.checks.aggregation import _applies_to_aggregated_levels

    single_cell_ctx = make_context(make_single_cell_adata(), declared=ProfileLevel.SINGLE_CELL)
    well_ctx = make_context(make_well_level_adata(), declared=ProfileLevel.WELL)
    treatment_ctx = make_context(make_treatment_level_adata(), declared=ProfileLevel.TREATMENT)

    assert _applies_to_aggregated_levels(single_cell_ctx) is False
    assert _applies_to_aggregated_levels(well_ctx) is True
    assert _applies_to_aggregated_levels(treatment_ctx) is True


def test_passes_for_valid_well_fixture() -> None:
    ctx = make_context(make_well_level_adata(), declared=ProfileLevel.WELL)
    assert check_aggregation_provenance(ctx) == []


def test_passes_for_valid_treatment_fixture() -> None:
    ctx = make_context(make_treatment_level_adata(), declared=ProfileLevel.TREATMENT)
    assert check_aggregation_provenance(ctx) == []


def test_flags_missing_aggregation_method() -> None:
    adata = make_well_level_adata()
    del adata.uns["aggregation"]
    ctx = make_context(adata, declared=ProfileLevel.WELL)

    issues = check_aggregation_provenance(ctx)

    assert [issue.code for issue in issues] == ["AGG001"]
    assert issues[0].severity.value == "error"


def test_flags_missing_replicate_count() -> None:
    adata = make_treatment_level_adata()
    adata.uns["aggregation"] = {"method": "median"}
    ctx = make_context(adata, declared=ProfileLevel.TREATMENT)

    issues = check_aggregation_provenance(ctx)

    assert [issue.code for issue in issues] == ["AGG002"]


def test_flags_missing_source_level() -> None:
    adata = make_treatment_level_adata()
    adata.uns["aggregation"] = {"method": "median", "replicate_count": 4}
    ctx = make_context(adata, declared=ProfileLevel.TREATMENT)

    issues = check_aggregation_provenance(ctx)

    assert [issue.code for issue in issues] == ["AGG003"]
    assert issues[0].severity.value == "warning"


def test_has_adequate_aggregation_provenance_true_for_valid_fixtures() -> None:
    well_ctx = make_context(make_well_level_adata(), declared=ProfileLevel.WELL)
    treatment_ctx = make_context(make_treatment_level_adata(), declared=ProfileLevel.TREATMENT)

    assert has_adequate_aggregation_provenance(well_ctx) is True
    assert has_adequate_aggregation_provenance(treatment_ctx) is True


def test_has_adequate_aggregation_provenance_false_when_source_level_missing() -> None:
    adata = make_treatment_level_adata()
    adata.uns["aggregation"] = {"method": "median", "replicate_count": 4}
    ctx = make_context(adata, declared=ProfileLevel.TREATMENT)

    assert has_adequate_aggregation_provenance(ctx) is False


def test_has_adequate_aggregation_provenance_false_when_missing_entirely() -> None:
    adata = make_treatment_level_adata()
    del adata.uns["aggregation"]
    ctx = make_context(adata, declared=ProfileLevel.TREATMENT)

    assert has_adequate_aggregation_provenance(ctx) is False
