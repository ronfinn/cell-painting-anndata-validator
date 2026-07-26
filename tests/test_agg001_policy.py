"""Focused tests for the AGG001 warning policy on missing aggregation provenance."""

from __future__ import annotations

from pathlib import Path

from cp_anndata_validator import ProfileLevel, validate
from cp_anndata_validator.checks.aggregation import check_aggregation_provenance
from cp_anndata_validator.checks.registry import CheckContext
from cp_anndata_validator.loading import AnnDataHandle
from cp_anndata_validator.profiles import detect_profile_level
from cp_anndata_validator.schema.loader import load_builtin_schema
from cp_anndata_validator.schema.resolve import resolve_schema
from tests.fixtures.synthetic import make_treatment_level_adata, make_well_level_adata, write_h5ad


def _context(adata, *, declared: ProfileLevel) -> CheckContext:
    handle = AnnDataHandle(adata=adata, path=Path("fake.h5ad"), size_bytes=0, backed=False)
    resolved = resolve_schema(adata.obs, adata.var, load_builtin_schema("generic-cell-painting"))
    detection = detect_profile_level(adata.obs, resolved)
    profile = detection.model_copy(update={"declared": declared})
    return CheckContext(handle=handle, resolved_schema=resolved, profile=profile)


def test_missing_aggregation_block_emits_agg001_as_warning() -> None:
    adata = make_well_level_adata()
    del adata.uns["aggregation"]
    issues = check_aggregation_provenance(_context(adata, declared=ProfileLevel.WELL))

    assert [issue.code for issue in issues] == ["AGG001"]
    assert issues[0].severity.value == "warning"
    assert issues[0].category.value == "aggregation"


def test_well_level_missing_aggregation_passes_normally_and_fails_strict(
    tmp_path: Path,
) -> None:
    adata = make_well_level_adata()
    del adata.uns["aggregation"]
    path = write_h5ad(adata, tmp_path)

    lenient = validate(path, profile_level=ProfileLevel.WELL)
    strict = validate(path, profile_level=ProfileLevel.WELL, strict=True)

    assert any(issue.code == "AGG001" for issue in lenient.issues)
    assert all(
        issue.severity.value != "error" or issue.code != "AGG001" for issue in lenient.issues
    )
    assert lenient.status == "pass"
    assert strict.status == "fail"
    assert [issue.code for issue in lenient.issues] == [issue.code for issue in strict.issues]


def test_complete_aggregation_block_emits_no_agg001() -> None:
    issues = check_aggregation_provenance(
        _context(make_well_level_adata(), declared=ProfileLevel.WELL)
    )
    assert issues == []


def test_incomplete_aggregation_still_emits_agg002_as_warning() -> None:
    adata = make_treatment_level_adata()
    adata.uns["aggregation"] = {"method": "median"}
    issues = check_aggregation_provenance(_context(adata, declared=ProfileLevel.TREATMENT))

    assert [issue.code for issue in issues] == ["AGG002"]
    assert issues[0].severity.value == "warning"


def test_incomplete_aggregation_still_emits_agg003_as_warning() -> None:
    adata = make_treatment_level_adata()
    adata.uns["aggregation"] = {"method": "median", "replicate_count": 4}
    issues = check_aggregation_provenance(_context(adata, declared=ProfileLevel.TREATMENT))

    assert [issue.code for issue in issues] == ["AGG003"]
    assert issues[0].severity.value == "warning"
