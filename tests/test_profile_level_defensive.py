"""Regression tests: checks must tolerate an uncoerced string on ProfileLevelResult.

The public ``validate()`` API coerces strings to :class:`ProfileLevel`, but
``model_copy(update=...)`` skips validation. These tests reproduce that internal
malformation and assert checks format messages without raising or emitting
``ENGINE001``.
"""

from __future__ import annotations

from pathlib import Path

import anndata as ad

from cp_anndata_validator.checks.aggregation import check_aggregation_provenance
from cp_anndata_validator.checks.identifiers import check_identifier_completeness
from cp_anndata_validator.checks.profile_consistency import (
    check_profile_level_ambiguity,
    check_profile_level_declared_vs_detected,
    check_profile_level_requirements,
)
from cp_anndata_validator.checks.registry import CheckContext
from cp_anndata_validator.loading import AnnDataHandle
from cp_anndata_validator.orchestrator import run_checks
from cp_anndata_validator.profiles import ProfileLevel, ProfileLevelResult, profile_level_label
from cp_anndata_validator.schema.loader import load_builtin_schema
from cp_anndata_validator.schema.resolve import resolve_schema
from tests.fixtures.synthetic import make_single_cell_adata, make_well_level_adata


def _context_with_raw_declared(adata: ad.AnnData, declared: str) -> CheckContext:
    handle = AnnDataHandle(adata=adata, path=Path("fake.h5ad"), size_bytes=0, backed=False)
    resolved = resolve_schema(adata.obs, adata.var, load_builtin_schema("generic-cell-painting"))
    # model_copy skips pydantic validation, leaving declared as a raw str.
    profile = ProfileLevelResult(detected=ProfileLevel.WELL, explanation="fixture").model_copy(
        update={"declared": declared}
    )
    assert isinstance(profile.declared, str)
    assert profile.effective == declared
    return CheckContext(handle=handle, resolved_schema=resolved, profile=profile)


def test_profile_level_label_accepts_enum_and_string() -> None:
    assert profile_level_label(ProfileLevel.WELL) == "well"
    assert profile_level_label("well") == "well"
    assert profile_level_label(None, default="aggregated") == "aggregated"


def test_aggregation_check_formats_message_when_declared_is_a_raw_string() -> None:
    adata = make_well_level_adata()
    del adata.uns["aggregation"]
    ctx = _context_with_raw_declared(adata, "well")

    issues = check_aggregation_provenance(ctx)

    assert [issue.code for issue in issues] == ["AGG001"]
    assert "well" in issues[0].message


def test_identifier_completeness_formats_message_when_declared_is_a_raw_string() -> None:
    adata = make_single_cell_adata()
    adata.obs = adata.obs.drop(columns=["cell_id"])
    ctx = _context_with_raw_declared(adata, "single-cell")

    issues = check_identifier_completeness(ctx)

    assert any(issue.code == "IDENT004" for issue in issues)
    assert all("single-cell" in issue.message for issue in issues if issue.code == "IDENT004")


def test_profile_requirements_formats_message_when_declared_is_a_raw_string() -> None:
    adata = make_single_cell_adata()
    adata.obs = adata.obs.drop(columns=["cell_id"])
    ctx = _context_with_raw_declared(adata, "single-cell")

    issues = check_profile_level_requirements(ctx)

    assert [issue.code for issue in issues] == ["PROFILE001"]
    assert "single-cell" in issues[0].message


def test_profile_declared_vs_detected_formats_when_declared_is_a_raw_string() -> None:
    adata = make_single_cell_adata()
    handle = AnnDataHandle(adata=adata, path=Path("fake.h5ad"), size_bytes=0, backed=False)
    resolved = resolve_schema(adata.obs, adata.var, load_builtin_schema("generic-cell-painting"))
    profile = ProfileLevelResult(
        detected=ProfileLevel.SINGLE_CELL, explanation="detected single-cell"
    ).model_copy(update={"declared": "well"})
    ctx = CheckContext(handle=handle, resolved_schema=resolved, profile=profile)

    issues = check_profile_level_declared_vs_detected(ctx)

    assert [issue.code for issue in issues] == ["PROFILE003"]
    assert "well" in issues[0].message
    assert "single-cell" in issues[0].message


def test_profile_ambiguity_formats_when_candidates_are_raw_strings() -> None:
    adata = make_well_level_adata()
    handle = AnnDataHandle(adata=adata, path=Path("fake.h5ad"), size_bytes=0, backed=False)
    resolved = resolve_schema(adata.obs, adata.var, load_builtin_schema("generic-cell-painting"))
    profile = ProfileLevelResult(explanation="ambiguous").model_copy(
        update={"candidates": ("well", "treatment")}
    )
    assert profile.is_ambiguous is True
    ctx = CheckContext(handle=handle, resolved_schema=resolved, profile=profile)

    issues = check_profile_level_ambiguity(ctx)

    assert [issue.code for issue in issues] == ["PROFILE002"]
    assert "well" in issues[0].message
    assert "treatment" in issues[0].message


def test_orchestrator_does_not_emit_engine001_for_raw_string_declared_level() -> None:
    adata = make_well_level_adata()
    del adata.uns["aggregation"]
    ctx = _context_with_raw_declared(adata, "well")

    issues, _executions = run_checks(ctx)

    assert all(issue.code != "ENGINE001" for issue in issues)
    assert any(issue.code == "AGG001" for issue in issues)
