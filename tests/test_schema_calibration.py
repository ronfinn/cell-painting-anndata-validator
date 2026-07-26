"""Focused regression tests for the v0.2 schema/vocabulary calibration.

Covers the three calibrated surfaces documented in docs/false-positives.md:

1. CellProfiler measurement families that used to raise FEAT002.
2. Perturbation-identifier alias precedence and the checks that become
   applicable once a column resolves.
3. JUMP-style ``poscon_`` / ``negcon_`` control-label prefixes.
"""

from __future__ import annotations

from pathlib import Path

import anndata as ad
import pandas as pd
import pytest

from cp_anndata_validator import ProfileLevel, validate
from cp_anndata_validator.checks.annotations import check_control_annotations
from cp_anndata_validator.checks.features import check_feature_measurement_families
from cp_anndata_validator.checks.identifiers import check_perturbation_modality
from cp_anndata_validator.checks.registry import CheckContext
from cp_anndata_validator.loading import AnnDataHandle
from cp_anndata_validator.profiles import ProfileLevelResult
from cp_anndata_validator.schema.loader import load_builtin_schema
from cp_anndata_validator.schema.resolve import resolve_schema
from tests.fixtures.synthetic import make_single_cell_adata, make_treatment_level_adata, write_h5ad

_CALIBRATED_FAMILIES = (
    "ObjectSkeleton",
    "Math",
    "Overlap",
    "SizeShape",
    "AreaOccupied",
    "ImageQuality",
)


def _context(
    adata: ad.AnnData, *, schema: str = "generic-cell-painting", level: ProfileLevel | None = None
) -> CheckContext:
    handle = AnnDataHandle(adata=adata, path=Path("fake.h5ad"), size_bytes=0, backed=False)
    resolved = resolve_schema(adata.obs, adata.var, load_builtin_schema(schema))
    profile = ProfileLevelResult(
        detected=level or ProfileLevel.SINGLE_CELL,
        declared=level,
        explanation="",
    )
    return CheckContext(handle=handle, resolved_schema=resolved, profile=profile)


@pytest.mark.parametrize("family", _CALIBRATED_FAMILIES)
@pytest.mark.parametrize("schema", ["generic-cell-painting", "jump-cp"])
def test_calibrated_cellprofiler_families_do_not_trigger_feat002(family: str, schema: str) -> None:
    adata = make_single_cell_adata(n_vars=2)
    adata.var_names = pd.Index([f"Cells_{family}_ExampleMeasurement", "Nuclei_AreaShape_Area"])
    ctx = _context(adata, schema=schema)

    assert check_feature_measurement_families(ctx) == []


@pytest.mark.parametrize("schema", ["generic-cell-painting", "jump-cp"])
def test_unrecognized_measurement_family_still_triggers_feat002(schema: str) -> None:
    adata = make_single_cell_adata(n_vars=1)
    adata.var_names = pd.Index(["Cells_NotARealFamily_X"])
    ctx = _context(adata, schema=schema)

    issues = check_feature_measurement_families(ctx)

    assert [issue.code for issue in issues] == ["FEAT002"]


@pytest.mark.parametrize(
    ("schema", "columns", "expected_column"),
    [
        (
            "jump-cp",
            {
                "Metadata_JCP2022": ["JCP2022_000001"],
                "Metadata_broad_sample": ["BRD-K00001"],
                "Metadata_pert_iname": ["compound-a"],
                "perturbation_id": ["generic-id"],
            },
            "Metadata_JCP2022",
        ),
        (
            "jump-cp",
            {
                "Metadata_broad_sample": ["BRD-K00001"],
                "Metadata_pert_iname": ["compound-a"],
                "perturbation_id": ["generic-id"],
            },
            "Metadata_broad_sample",
        ),
        (
            "jump-cp",
            {"Metadata_pert_iname": ["compound-a"], "perturbation_id": ["generic-id"]},
            "Metadata_pert_iname",
        ),
        (
            "generic-cell-painting",
            {
                "perturbation_id": ["generic-id"],
                "Metadata_broad_sample": ["BRD-K00001"],
                "Metadata_pert_iname": ["compound-a"],
                "Metadata_JCP2022": ["JCP2022_000001"],
            },
            "perturbation_id",
        ),
        (
            "generic-cell-painting",
            {
                "Metadata_broad_sample": ["BRD-K00001"],
                "Metadata_pert_iname": ["compound-a"],
                "Metadata_JCP2022": ["JCP2022_000001"],
            },
            "Metadata_broad_sample",
        ),
        (
            "generic-cell-painting",
            {
                "Metadata_pert_iname": ["compound-a"],
                "Metadata_JCP2022": ["JCP2022_000001"],
            },
            "Metadata_pert_iname",
        ),
        (
            "generic-cell-painting",
            {"Metadata_JCP2022": ["JCP2022_000001"]},
            "Metadata_JCP2022",
        ),
    ],
)
def test_perturbation_alias_precedence(
    schema: str, columns: dict[str, list[str]], expected_column: str
) -> None:
    obs = pd.DataFrame(columns)
    var = pd.DataFrame(index=["f1"])
    resolved = resolve_schema(obs, var, load_builtin_schema(schema))

    assert resolved.column_for("perturbation_id") == expected_column


def test_resolved_jump_perturbation_alias_enables_modality_check(tmp_path: Path) -> None:
    """Once Metadata_broad_sample resolves, IDENT007 applies instead of being skipped."""
    adata = make_treatment_level_adata(n_treatments=3)
    adata.obs = adata.obs.drop(columns=["perturbation_id"])
    adata.obs["Metadata_broad_sample"] = [f"BRD-K{i:05d}" for i in range(adata.n_obs)]
    # No modality column on purpose.
    path = write_h5ad(adata, tmp_path)

    report = validate(path, schema="jump-cp", profile_level=ProfileLevel.TREATMENT)

    assert report.profile_level.effective == ProfileLevel.TREATMENT
    assert any(issue.code == "IDENT007" for issue in report.issues)
    # And IDENT005 must not fire: the perturbation identifier did resolve.
    assert all(issue.code != "IDENT005" for issue in report.issues)


def test_resolved_generic_perturbation_alias_enables_modality_check() -> None:
    adata = make_treatment_level_adata(n_treatments=3)
    adata.obs = adata.obs.drop(columns=["perturbation_id"])
    adata.obs["Metadata_pert_iname"] = [f"compound-{i}" for i in range(adata.n_obs)]
    ctx = _context(adata, schema="generic-cell-painting", level=ProfileLevel.TREATMENT)

    assert ctx.resolved_schema.column_for("perturbation_id") == "Metadata_pert_iname"
    assert [issue.code for issue in check_perturbation_modality(ctx)] == ["IDENT007"]


@pytest.mark.parametrize(
    "label",
    ["poscon_cp", "poscon_diverse", "negcon_cpjump", "POSCON_CP", "Negcon_Extra"],
)
def test_jump_style_control_label_prefixes_are_accepted(label: str) -> None:
    adata = make_single_cell_adata(n_obs=4)
    # Keep at least one negcon_* / negcon so CTRL003 does not also fire.
    adata.obs["control_type"] = ["negcon_cpjump", label, "trt", "trt"]
    ctx = _context(adata)

    assert check_control_annotations(ctx) == []


def test_unrelated_control_label_still_triggers_ctrl002() -> None:
    adata = make_single_cell_adata(n_obs=4)
    adata.obs["control_type"] = ["negcon", "mystery_label", "trt", "trt"]
    ctx = _context(adata)

    issues = check_control_annotations(ctx)

    assert "CTRL002" in [issue.code for issue in issues]
    evidence = next(issue.evidence for issue in issues if issue.code == "CTRL002")
    assert evidence is not None
    assert "mystery_label" in evidence
    # Prefix matching must not accept arbitrary substrings.
    assert "negcon" not in evidence


def test_substring_that_is_not_a_prefix_still_triggers_ctrl002() -> None:
    adata = make_single_cell_adata(n_obs=4)
    adata.obs["control_type"] = ["negcon", "my_poscon_label", "trt", "trt"]
    ctx = _context(adata)

    issues = check_control_annotations(ctx)

    assert "CTRL002" in [issue.code for issue in issues]
    evidence = next(issue.evidence for issue in issues if issue.code == "CTRL002")
    assert evidence is not None
    assert "my_poscon_label" in evidence


def test_negcon_prefix_satisfies_negative_control_presence() -> None:
    adata = make_single_cell_adata(n_obs=4)
    adata.obs["control_type"] = ["negcon_cpjump", "trt", "trt", "trt"]
    ctx = _context(adata)

    assert check_control_annotations(ctx) == []
