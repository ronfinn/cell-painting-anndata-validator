"""Tests for LINCS-style batch alias calibration (schema v0.2.1)."""

from __future__ import annotations

from pathlib import Path

import anndata as ad
import pandas as pd
import pytest

from cp_anndata_validator.checks.metadata import check_batch_identifier_declared
from cp_anndata_validator.checks.registry import CheckContext
from cp_anndata_validator.loading import AnnDataHandle
from cp_anndata_validator.profiles import ProfileLevel, ProfileLevelResult
from cp_anndata_validator.schema.loader import list_builtin_schema_names, load_builtin_schema
from cp_anndata_validator.schema.resolve import resolve_schema
from tests.fixtures.synthetic import make_well_level_adata


def _context(adata: ad.AnnData, schema_name: str = "generic-cell-painting") -> CheckContext:
    handle = AnnDataHandle(adata=adata, path=Path("fake.h5ad"), size_bytes=0, backed=False)
    schema = load_builtin_schema(schema_name)
    resolved = resolve_schema(adata.obs, adata.var, schema)
    profile = ProfileLevelResult(detected=ProfileLevel.WELL, explanation="")
    return CheckContext(handle=handle, resolved_schema=resolved, profile=profile)


@pytest.mark.parametrize("schema_name", ["generic-cell-painting", "jump-cp"])
def test_builtin_schemas_are_at_0_2_1(schema_name: str) -> None:
    assert list_builtin_schema_names() == ["generic-cell-painting", "jump-cp"]
    assert load_builtin_schema(schema_name).schema_version == "0.2.1"


@pytest.mark.parametrize(
    ("schema_name", "expected_aliases"),
    [
        (
            "generic-cell-painting",
            ["batch_id", "batch", "Metadata_Batch", "Metadata_Batch_Number"],
        ),
        (
            "jump-cp",
            ["Metadata_Batch", "batch_id", "Metadata_Batch_Number"],
        ),
    ],
)
def test_batch_alias_precedence_includes_lincs_batch_number(
    schema_name: str,
    expected_aliases: list[str],
) -> None:
    schema = load_builtin_schema(schema_name)
    assert list(schema.fields["batch"].aliases) == expected_aliases


@pytest.mark.parametrize("schema_name", ["generic-cell-painting", "jump-cp"])
def test_metadata_batch_number_resolves_to_batch(schema_name: str) -> None:
    obs = pd.DataFrame(
        {
            "Metadata_Plate": ["SQ00014812"],
            "Metadata_Well": ["A01"],
            "Metadata_Batch_Number": ["4"],
        }
    )
    var = pd.DataFrame(index=["Cells_AreaShape_Area"])
    schema = load_builtin_schema(schema_name)

    resolved = resolve_schema(obs, var, schema)

    assert resolved.is_resolved("batch") is True
    assert resolved.column_for("batch") == "Metadata_Batch_Number"


@pytest.mark.parametrize("schema_name", ["generic-cell-painting", "jump-cp"])
def test_existing_batch_alias_still_wins_over_batch_number(schema_name: str) -> None:
    """First listed alias that matches wins; Metadata_Batch_Number is last."""
    if schema_name == "generic-cell-painting":
        obs = pd.DataFrame(
            {
                "batch_id": ["B1"],
                "Metadata_Batch_Number": ["4"],
            }
        )
        expected = "batch_id"
    else:
        obs = pd.DataFrame(
            {
                "Metadata_Batch": ["2020_11_04_CPJUMP1"],
                "Metadata_Batch_Number": ["4"],
            }
        )
        expected = "Metadata_Batch"
    var = pd.DataFrame(index=["Cells_AreaShape_Area"])
    schema = load_builtin_schema(schema_name)

    resolved = resolve_schema(obs, var, schema)

    assert resolved.column_for("batch") == expected


@pytest.mark.parametrize("schema_name", ["generic-cell-painting", "jump-cp"])
def test_meta001_absent_when_metadata_batch_number_present(schema_name: str) -> None:
    adata = make_well_level_adata()
    # Drop any pre-existing batch aliases from the synthetic fixture.
    drop = [c for c in ("batch_id", "batch", "Metadata_Batch") if c in adata.obs.columns]
    adata.obs = adata.obs.drop(columns=drop)
    adata.obs["Metadata_Batch_Number"] = 4
    ctx = _context(adata, schema_name)

    assert check_batch_identifier_declared(ctx) == []


@pytest.mark.parametrize("schema_name", ["generic-cell-painting", "jump-cp"])
def test_meta001_remains_when_no_batch_alias_exists(schema_name: str) -> None:
    adata = make_well_level_adata()
    drop = [
        c
        for c in ("batch_id", "batch", "Metadata_Batch", "Metadata_Batch_Number")
        if c in adata.obs.columns
    ]
    adata.obs = adata.obs.drop(columns=drop)
    ctx = _context(adata, schema_name)

    issues = check_batch_identifier_declared(ctx)
    assert [issue.code for issue in issues] == ["META001"]
    assert issues[0].severity.value == "information"


@pytest.mark.parametrize("schema_name", ["generic-cell-painting", "jump-cp"])
def test_metadata_pert_type_resolves_to_control_type_not_modality(
    schema_name: str,
) -> None:
    """LINCS Metadata_pert_type is control/treatment status, not modality."""
    obs = pd.DataFrame({"Metadata_pert_type": ["control"]})
    var = pd.DataFrame(index=["Cells_AreaShape_Area"])
    schema = load_builtin_schema(schema_name)

    resolved = resolve_schema(obs, var, schema)

    assert resolved.column_for("control_type") == "Metadata_pert_type"
    assert resolved.is_resolved("perturbation_modality") is False
