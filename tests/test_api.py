"""Tests for the public cp_anndata_validator.validate() entry point."""

from __future__ import annotations

from pathlib import Path

import pytest

from cp_anndata_validator import LoadError, ProfileLevel, SchemaError, validate
from tests.fixtures.synthetic import make_single_cell_adata, make_well_level_adata, write_h5ad


def test_validate_passes_for_a_clean_single_cell_dataset(tmp_path: Path) -> None:
    path = write_h5ad(make_single_cell_adata(), tmp_path)
    report = validate(path)

    assert report.status == "pass"
    assert report.profile_level.effective == ProfileLevel.SINGLE_CELL
    assert report.schema_id == "generic-cell-painting"
    assert any(c.status == "executed" for c in report.checks)


def test_validate_reports_errors_for_incomplete_identifiers(tmp_path: Path) -> None:
    adata = make_single_cell_adata()
    adata.obs = adata.obs.drop(columns=["cell_id"])
    path = write_h5ad(adata, tmp_path)

    report = validate(path, profile_level=ProfileLevel.SINGLE_CELL)

    assert report.status == "fail"
    assert any(issue.code == "IDENT004" for issue in report.issues)


def test_validate_uses_jump_cp_schema(tmp_path: Path) -> None:
    path = write_h5ad(make_well_level_adata(), tmp_path)
    report = validate(path, schema="jump-cp", profile_level=ProfileLevel.WELL)
    assert report.schema_id == "jump-cp"


def test_validate_raises_load_error_for_missing_file(tmp_path: Path) -> None:
    with pytest.raises(LoadError):
        validate(tmp_path / "missing.h5ad")


def test_validate_raises_schema_error_for_unknown_schema(tmp_path: Path) -> None:
    path = write_h5ad(make_single_cell_adata(), tmp_path)
    with pytest.raises(SchemaError):
        validate(path, schema="not-a-real-schema")


def test_validate_strict_turns_warnings_into_failures(tmp_path: Path) -> None:
    adata = make_single_cell_adata()
    del adata.uns["licence"]
    path = write_h5ad(adata, tmp_path)

    lenient = validate(path)
    strict = validate(path, strict=True)

    assert lenient.status == "pass"
    assert strict.status == "fail"


def test_validate_respects_declared_profile_level_override(tmp_path: Path) -> None:
    path = write_h5ad(make_single_cell_adata(), tmp_path)
    report = validate(path, profile_level=ProfileLevel.WELL)

    assert report.profile_level.declared == ProfileLevel.WELL
    assert report.profile_level.detected == ProfileLevel.SINGLE_CELL
    assert report.profile_level.effective == ProfileLevel.WELL


def test_validate_is_deterministic_across_repeated_runs(tmp_path: Path) -> None:
    """Re-validating the same, unchanged dataset must produce identical issues/checks/counts."""
    path = write_h5ad(make_single_cell_adata(), tmp_path)

    first = validate(path)
    second = validate(path)

    assert [issue.model_dump() for issue in first.issues] == [
        issue.model_dump() for issue in second.issues
    ]
    assert [check.model_dump() for check in first.checks] == [
        check.model_dump() for check in second.checks
    ]
    assert first.counts == second.counts
    assert first.status == second.status


def test_validate_forced_backed_mode_produces_same_result_as_in_memory(tmp_path: Path) -> None:
    path = write_h5ad(make_single_cell_adata(), tmp_path)

    in_memory = validate(path, backed=False)
    backed = validate(path, backed=True)

    assert in_memory.status == backed.status
    assert [i.code for i in in_memory.issues] == [i.code for i in backed.issues]
    assert backed.input_file.backed is True
