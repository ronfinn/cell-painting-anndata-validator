"""Tests for profile-level requirement/consistency checks."""

from __future__ import annotations

from pathlib import Path

import anndata as ad

from cp_anndata_validator.checks.profile_consistency import (
    check_profile_level_ambiguity,
    check_profile_level_declared_vs_detected,
    check_profile_level_requirements,
)
from cp_anndata_validator.checks.registry import CheckContext
from cp_anndata_validator.loading import AnnDataHandle
from cp_anndata_validator.profiles import ProfileLevel, detect_profile_level
from cp_anndata_validator.schema.loader import load_builtin_schema
from cp_anndata_validator.schema.resolve import resolve_schema
from tests.fixtures.synthetic import make_single_cell_adata, make_well_level_adata


def make_context(adata: ad.AnnData, *, declared: ProfileLevel | None = None) -> CheckContext:
    handle = AnnDataHandle(adata=adata, path=Path("fake.h5ad"), size_bytes=0, backed=False)
    schema = load_builtin_schema("generic-cell-painting")
    resolved = resolve_schema(adata.obs, adata.var, schema)
    detection = detect_profile_level(adata.obs, resolved)
    profile = detection.model_copy(update={"declared": declared}) if declared else detection
    return CheckContext(handle=handle, resolved_schema=resolved, profile=profile)


def test_requirements_pass_for_valid_single_cell_fixture() -> None:
    ctx = make_context(make_single_cell_adata())
    assert check_profile_level_requirements(ctx) == []


def test_requirements_flag_declared_level_missing_fields() -> None:
    adata = make_well_level_adata()
    ctx = make_context(adata, declared=ProfileLevel.SINGLE_CELL)

    issues = check_profile_level_requirements(ctx)

    assert [issue.code for issue in issues] == ["PROFILE001"]
    assert "site" in issues[0].message or "cell_id" in issues[0].message


def test_requirements_pass_when_no_effective_level() -> None:
    adata = make_single_cell_adata(n_obs=4)
    adata.obs = adata.obs.drop(columns=["plate_id", "well_id", "site_id", "cell_id"])
    ctx = make_context(adata)
    assert ctx.profile.effective is None
    assert check_profile_level_requirements(ctx) == []


def test_ambiguity_check_fires_when_ambiguous() -> None:
    adata = make_single_cell_adata(n_obs=4)
    adata.obs = adata.obs.drop(columns=["site_id", "cell_id"])
    ctx = make_context(adata)

    issues = check_profile_level_ambiguity(ctx)

    if ctx.profile.is_ambiguous:
        assert [issue.code for issue in issues] == ["PROFILE002"]
    else:
        assert issues == []


def test_ambiguity_check_silent_when_unambiguous() -> None:
    ctx = make_context(make_single_cell_adata())
    assert check_profile_level_ambiguity(ctx) == []


def test_declared_vs_detected_warns_on_mismatch() -> None:
    ctx = make_context(make_single_cell_adata(), declared=ProfileLevel.WELL)

    issues = check_profile_level_declared_vs_detected(ctx)

    assert [issue.code for issue in issues] == ["PROFILE003"]


def test_declared_vs_detected_silent_on_agreement() -> None:
    ctx = make_context(make_single_cell_adata(), declared=ProfileLevel.SINGLE_CELL)
    assert check_profile_level_declared_vs_detected(ctx) == []


def test_declared_vs_detected_silent_when_nothing_declared() -> None:
    ctx = make_context(make_single_cell_adata())
    assert check_profile_level_declared_vs_detected(ctx) == []
