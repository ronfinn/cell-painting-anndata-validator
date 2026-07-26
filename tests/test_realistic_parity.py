"""End-to-end tests over realistic Cell Painting fixtures.

The central contract asserted here is *parity*: for one logical dataset, the
set of issue codes must not depend on how the matrix happens to be stored
(dense/CSR/CSC) or how the file happens to be opened (in-memory/backed). Those
are implementation details of the container and loader, never of the dataset's
validity, so any divergence is a defect.

Fixtures are built in memory and written to ``tmp_path`` only here, at the
point an actual ``.h5ad`` file is required; no dataset bytes are ever committed.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from cp_anndata_validator import Report, validate
from tests.fixtures.realistic import (
    MATRIX_CONTAINERS,
    REALISTIC_DATASETS,
    MatrixContainer,
    RealisticDataset,
    make_cellprofiler_single_cell,
)
from tests.fixtures.synthetic import write_h5ad

BaselineKey = tuple[str, bool]
Baseline = tuple[list[str], str]


def _issue_codes(report: Report) -> list[str]:
    return sorted(issue.code for issue in report.issues)


@pytest.fixture(scope="session")
def baselines(tmp_path_factory: pytest.TempPathFactory) -> dict[BaselineKey, Baseline]:
    """Dense, in-memory results per (dataset, provenance): the reference every variant matches.

    Computed once per session because it is pure reference data -- the
    per-variant tests each write and validate their own file.
    """
    directory = tmp_path_factory.mktemp("realistic-baselines")
    computed: dict[BaselineKey, Baseline] = {}
    for dataset in REALISTIC_DATASETS:
        for with_provenance in (True, False):
            adata = dataset.build(container="dense", with_provenance=with_provenance)
            path = write_h5ad(adata, directory, f"{dataset.name}-{with_provenance}.h5ad")
            report = validate(path, schema=dataset.schema, backed=False)
            computed[(dataset.name, with_provenance)] = (_issue_codes(report), report.status)
    return computed


@pytest.mark.parametrize("with_provenance", [True, False], ids=["documented", "bare"])
@pytest.mark.parametrize("backed", [False, True], ids=["in-memory", "backed"])
@pytest.mark.parametrize("container", MATRIX_CONTAINERS)
@pytest.mark.parametrize("dataset", REALISTIC_DATASETS, ids=lambda dataset: dataset.name)
def test_issue_codes_are_identical_across_containers_and_loading_modes(
    dataset: RealisticDataset,
    container: MatrixContainer,
    backed: bool,
    with_provenance: bool,
    baselines: dict[BaselineKey, Baseline],
    tmp_path: Path,
) -> None:
    expected_codes, expected_status = baselines[(dataset.name, with_provenance)]
    adata = dataset.build(container=container, with_provenance=with_provenance)
    path = write_h5ad(adata, tmp_path, f"{container}.h5ad")

    report = validate(path, schema=dataset.schema, backed=backed)

    assert _issue_codes(report) == expected_codes
    assert report.status == expected_status
    assert report.input_file.backed is backed


@pytest.mark.parametrize("with_provenance", [True, False], ids=["documented", "bare"])
@pytest.mark.parametrize("backed", [False, True], ids=["in-memory", "backed"])
@pytest.mark.parametrize("container", MATRIX_CONTAINERS)
@pytest.mark.parametrize("dataset", REALISTIC_DATASETS, ids=lambda dataset: dataset.name)
def test_realistic_fixtures_never_produce_an_engine_error(
    dataset: RealisticDataset,
    container: MatrixContainer,
    backed: bool,
    with_provenance: bool,
    tmp_path: Path,
) -> None:
    """ENGINE001 means a check crashed; no realistic dataset may ever trigger one."""
    adata = dataset.build(container=container, with_provenance=with_provenance)
    path = write_h5ad(adata, tmp_path, f"{container}.h5ad")

    report = validate(path, schema=dataset.schema, backed=backed)

    engine_issues = [issue for issue in report.issues if issue.code == "ENGINE001"]
    assert engine_issues == [], [(issue.check_name, issue.evidence) for issue in engine_issues]


@pytest.mark.parametrize("dataset", REALISTIC_DATASETS, ids=lambda dataset: dataset.name)
def test_fully_documented_realistic_fixture_validates_cleanly(
    dataset: RealisticDataset, tmp_path: Path
) -> None:
    """A realistic dataset that declares all its metadata should raise nothing at all."""
    path = write_h5ad(dataset.build(), tmp_path)

    report = validate(path, schema=dataset.schema)

    assert report.status == "pass"
    assert _issue_codes(report) == []


@pytest.mark.parametrize("dataset", REALISTIC_DATASETS, ids=lambda dataset: dataset.name)
def test_realistic_fixture_detects_its_expected_profile_level(
    dataset: RealisticDataset, tmp_path: Path
) -> None:
    path = write_h5ad(dataset.build(), tmp_path)

    report = validate(path, schema=dataset.schema)

    assert report.profile_level.detected == dataset.expected_level
    assert report.profile_level.is_ambiguous is False


@pytest.mark.parametrize("container", MATRIX_CONTAINERS)
@pytest.mark.parametrize("backed", [False, True], ids=["in-memory", "backed"])
def test_realistic_layers_and_obsm_are_well_formed(
    container: MatrixContainer, backed: bool, tmp_path: Path
) -> None:
    """The single-cell fixture's realistic .layers/.obsm entries must align with X.

    Misaligned slots would surface as MATRIX004/SLOT002/SLOT003, so their
    absence is what proves the extra slots are well-formed in every container
    and loading mode.
    """
    adata = make_cellprofiler_single_cell(container=container)
    assert [name for name in adata.layers if name] == ["raw"]
    assert sorted(adata.obsm) == ["spatial"]
    path = write_h5ad(adata, tmp_path)

    report = validate(path, backed=backed)

    assert _issue_codes(report) == []
