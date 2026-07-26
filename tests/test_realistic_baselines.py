"""Pinned baselines for "bare pipeline output" — realistic datasets with no `.uns` metadata.

A CellProfiler/CytoTable/pycytominer export normally carries no provenance,
schema, licence or aggregation metadata at all: those blocks are exactly what
this validator asks a publisher to add. These tests pin what such an export
reports *today*, so any future change to that baseline has to be acknowledged
deliberately rather than drifting silently.

Each expected code set below was derived by running the current
implementation against the fixture (see docs/false-positives.md for the
category-by-category interpretation), not copied from a design document.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import anndata as ad
import pytest

from cp_anndata_validator import ProfileLevel, Severity, validate
from tests.fixtures.realistic import (
    make_cellprofiler_single_cell,
    make_jump_treatment_profile,
    make_pycytominer_well_profile,
)
from tests.fixtures.synthetic import write_h5ad

# Emitted by every bare export, whatever its profile level: nothing about the
# schema, licence, experiment, processing stage or provenance is declared.
UNDECLARED_METADATA_CODES = (
    "LICENSE001",
    "META002",
    "PROVFEAT001",
    "PROVIMG001",
    "PROVSEG001",
    "SCHEMA001",
    "SCHEMA002",
    "SLOT001",
)


@dataclass(frozen=True)
class BareBaseline:
    """The exact report a bare (metadata-free) realistic export produces."""

    name: str
    build: Callable[..., ad.AnnData]
    schema: str
    expected_codes: tuple[str, ...]
    expected_status: Literal["pass", "fail"]
    expected_level: ProfileLevel
    expected_severities: dict[Severity, int]


BARE_BASELINES: tuple[BareBaseline, ...] = (
    BareBaseline(
        name="cellprofiler-single-cell",
        build=make_cellprofiler_single_cell,
        schema="generic-cell-painting",
        # SLOT003 too: this fixture carries a realistic `raw` layer whose own
        # processing stage is likewise undeclared. No aggregation codes -- a
        # single-cell profile was never aggregated.
        expected_codes=(*UNDECLARED_METADATA_CODES, "SLOT003"),
        expected_status="pass",
        expected_level=ProfileLevel.SINGLE_CELL,
        expected_severities={Severity.WARNING: 9},
    ),
    BareBaseline(
        name="pycytominer-well",
        build=make_pycytominer_well_profile,
        schema="generic-cell-painting",
        # AGG001 is an *error*: an aggregated profile that does not say how it
        # was aggregated fails, so standard pycytominer output exits non-zero.
        expected_codes=(*UNDECLARED_METADATA_CODES, "AGG001"),
        expected_status="fail",
        expected_level=ProfileLevel.WELL,
        expected_severities={Severity.ERROR: 1, Severity.WARNING: 8},
    ),
    BareBaseline(
        name="jump-treatment",
        build=make_jump_treatment_profile,
        schema="jump-cp",
        # IDENT006 as well: plate/well were aggregated away, and without
        # uns['aggregation'] the rows cannot be traced back to source data.
        expected_codes=(*UNDECLARED_METADATA_CODES, "AGG001", "IDENT006"),
        expected_status="fail",
        expected_level=ProfileLevel.TREATMENT,
        expected_severities={Severity.ERROR: 2, Severity.WARNING: 8},
    ),
)


@pytest.mark.parametrize("baseline", BARE_BASELINES, ids=lambda baseline: baseline.name)
def test_bare_realistic_export_reports_its_pinned_baseline(
    baseline: BareBaseline, tmp_path: Path
) -> None:
    adata = baseline.build(with_provenance=False)
    path = write_h5ad(adata, tmp_path)

    report = validate(path, schema=baseline.schema)

    assert sorted(issue.code for issue in report.issues) == sorted(baseline.expected_codes)
    assert report.status == baseline.expected_status
    assert report.profile_level.detected == baseline.expected_level
    assert report.counts.by_severity == baseline.expected_severities


@pytest.mark.parametrize("baseline", BARE_BASELINES, ids=lambda baseline: baseline.name)
def test_bare_realistic_export_never_produces_an_engine_error(
    baseline: BareBaseline, tmp_path: Path
) -> None:
    """Missing metadata is a finding about the dataset; it must never crash a check."""
    adata = baseline.build(with_provenance=False)
    path = write_h5ad(adata, tmp_path)

    report = validate(path, schema=baseline.schema)

    engine_issues = [issue for issue in report.issues if issue.code == "ENGINE001"]
    assert engine_issues == [], [(issue.check_name, issue.evidence) for issue in engine_issues]


@pytest.mark.parametrize("baseline", BARE_BASELINES, ids=lambda baseline: baseline.name)
def test_declaring_metadata_clears_the_entire_bare_baseline(
    baseline: BareBaseline, tmp_path: Path
) -> None:
    """Every code in the bare baseline is remediable purely by declaring metadata.

    This is what makes the baseline governance signalling rather than noise: the
    same dataset, with its `.uns` blocks filled in, reports nothing at all.
    """
    documented = write_h5ad(baseline.build(with_provenance=True), tmp_path)

    report = validate(documented, schema=baseline.schema)

    assert report.status == "pass"
    assert [issue.code for issue in report.issues] == []


def test_bare_single_cell_export_passes_but_fails_under_strict(tmp_path: Path) -> None:
    """The single-cell baseline is warning-only, so `--strict` is what turns it into a failure."""
    path = write_h5ad(make_cellprofiler_single_cell(with_provenance=False), tmp_path)

    lenient = validate(path)
    strict = validate(path, strict=True)

    assert lenient.status == "pass"
    assert strict.status == "fail"
    assert [issue.code for issue in lenient.issues] == [issue.code for issue in strict.issues]
