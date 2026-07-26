"""Builders for AnnData objects shaped like real Cell Painting pipeline output.

These complement :mod:`tests.fixtures.synthetic`, which stays deliberately
minimal for unit tests. The builders here model the conventions that
CellProfiler, CytoTable, pycytominer and the JUMP Cell Painting Consortium
publicly document: ``Metadata_``-prefixed ``.obs`` columns,
``<compartment>_<measurement family>_<measurement>_<channel>`` feature names,
the five standard Cell Painting channels, and realistic ``.layers``/``.obsm``
entries.

Every builder is deterministic, returns an **in-memory** ``AnnData`` (callers
write to ``tmp_path`` themselves, only when an actual ``.h5ad`` file is
needed, for example to exercise backed mode), and defaults to a small shape so
it remains usable in the normal test suite.

Two deliberate constraints keep these fixtures *valid* rather than
adversarial:

- Feature names use only measurement families the built-in schemas already
  declare. Real CellProfiler families that the schemas do not yet list (for
  example ``ObjectSkeleton`` or ``Math``) are a false-positive-analysis
  concern, not a fixture concern.
- ``Metadata_broad_sample`` is included where a real pipeline would emit it
  even though ``generic-cell-painting`` does not list it as a
  ``perturbation_id`` alias; that alias gap is likewise tracked separately.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from itertools import product
from typing import Any, Literal

import anndata as ad
import numpy as np
import pandas as pd
from scipy import sparse

from cp_anndata_validator.profiles import ProfileLevel

MatrixContainer = Literal["dense", "csr", "csc"]

MATRIX_CONTAINERS: tuple[MatrixContainer, ...] = ("dense", "csr", "csc")
"""Every matrix container a realistic dataset may be stored in."""

CHANNELS = ("DNA", "RNA", "AGP", "ER", "Mito")
"""The five standard Cell Painting stains."""

COMPARTMENTS = ("Cells", "Cytoplasm", "Nuclei")

_FEATURE_TEMPLATES = (
    "{compartment}_AreaShape_Zernike_0_0",
    "{compartment}_AreaShape_Area",
    "{compartment}_Intensity_MeanIntensity_{channel}",
    "{compartment}_Intensity_IntegratedIntensity_{channel}",
    "{compartment}_Texture_Contrast_{channel}_3_00_256",
    "{compartment}_Correlation_Correlation_{channel}_{other_channel}",
    "{compartment}_Granularity_1_{channel}",
    "{compartment}_RadialDistribution_FracAtD_{channel}_1of4",
    "{compartment}_Neighbors_NumberOfNeighbors_Adjacent",
    "{compartment}_Location_Center_X",
)

_SEGMENTATION_TOOL = {"tool": "CellProfiler", "version": "4.2.6", "method": "Otsu global"}
_FEATURE_EXTRACTION_TOOL = {"tool": "CellProfiler", "version": "4.2.6"}
_IMAGE_PROVENANCE = {
    "microscope": "ImageXpress Micro Confocal",
    "illumination_correction": True,
    "channels": list(CHANNELS),
}
_EXPERIMENT = {
    "instrument": "ImageXpress Micro Confocal",
    "protocol": "Cell Painting v3",
    "date": "2020-11-04",
}
_LICENCE = "CC0-1.0"


def well_names(n_wells: int) -> list[str]:
    """384-well-plate style well names (``A01``, ``A02``, ... ``P24``)."""
    names = [f"{row}{column:02d}" for row in "ABCDEFGHIJKLMNOP" for column in range(1, 25)]
    if n_wells > len(names):
        raise ValueError(f"n_wells must be at most {len(names)}, got {n_wells}")
    return names[:n_wells]


def cell_painting_feature_names(n_features: int) -> list[str]:
    """Realistic CellProfiler feature names, using only schema-declared families."""
    names: list[str] = []
    seen: set[str] = set()
    for template, compartment, index in product(
        _FEATURE_TEMPLATES, COMPARTMENTS, range(len(CHANNELS))
    ):
        name = template.format(
            compartment=compartment,
            channel=CHANNELS[index],
            other_channel=CHANNELS[(index + 1) % len(CHANNELS)],
        )
        if name in seen:
            continue
        seen.add(name)
        names.append(name)
        if len(names) == n_features:
            return names
    raise ValueError(f"n_features must be at most {len(names)}, got {n_features}")


def _feature_matrix(n_obs: int, n_features: int, container: MatrixContainer, seed: int) -> Any:
    """A float32 matrix with deterministic structural zeros, in the requested container.

    Zeros follow a fixed diagonal band rather than a random mask, so sparse
    containers really do carry structural zeros (exercising the stored-values
    code path in :mod:`cp_anndata_validator.sampling`) while no column becomes
    constant.
    """
    rng = np.random.default_rng(seed)
    dense = rng.normal(size=(n_obs, n_features)).astype(np.float32)
    rows = np.arange(n_obs)[:, None]
    columns = np.arange(n_features)[None, :]
    dense[(rows + columns) % 3 == 0] = 0.0

    if container == "csr":
        return sparse.csr_matrix(dense)
    if container == "csc":
        return sparse.csc_matrix(dense)
    return dense


def _add_pipeline_metadata(
    adata: ad.AnnData,
    *,
    schema_id: str,
    processing_stage: str,
    layer_stages: dict[str, str] | None = None,
    aggregation: dict[str, Any] | None = None,
) -> None:
    """Populate the ``.uns`` blocks a fully-documented dataset would carry.

    A raw pipeline export typically has *none* of these; builders expose that
    case through ``with_provenance=False``.
    """
    adata.uns["schema_id"] = schema_id
    adata.uns["schema_version"] = "0.1.0"
    adata.uns["processing_stage"] = processing_stage
    adata.uns["image_provenance"] = dict(_IMAGE_PROVENANCE)
    adata.uns["segmentation_provenance"] = dict(_SEGMENTATION_TOOL)
    adata.uns["feature_extraction_provenance"] = dict(_FEATURE_EXTRACTION_TOOL)
    adata.uns["experiment"] = dict(_EXPERIMENT)
    adata.uns["licence"] = _LICENCE
    if layer_stages:
        adata.uns["layer_processing_stages"] = dict(layer_stages)
    if aggregation:
        adata.uns["aggregation"] = dict(aggregation)


def make_cellprofiler_single_cell(
    *,
    n_plates: int = 2,
    n_wells: int = 4,
    n_sites: int = 2,
    n_cells_per_site: int = 3,
    n_features: int = 12,
    container: MatrixContainer = "dense",
    with_provenance: bool = True,
    seed: int = 0,
) -> ad.AnnData:
    """A CellProfiler/CytoTable-style single-cell table: one row per segmented object.

    Identifier cardinality genuinely multiplies out (plate x well x site x
    object), so plate/well/site/cell tuples are unique by construction. Also
    carries a raw intensity ``.layers`` entry next to the normalized ``X``, and
    per-object centroid coordinates in ``.obsm['spatial']``.
    """
    records = list(
        product(
            [f"BR0011{plate:04d}" for plate in range(n_plates)],
            well_names(n_wells),
            range(1, n_sites + 1),
            range(1, n_cells_per_site + 1),
        )
    )
    plates, wells, sites, objects = (list(column) for column in zip(*records, strict=True))
    n_obs = len(records)
    first_well = well_names(n_wells)[0]

    obs = pd.DataFrame(
        {
            "Metadata_Plate": plates,
            "Metadata_Well": wells,
            "Metadata_Site": sites,
            "Metadata_ObjectNumber": objects,
            # JUMP/pycytominer spell the control annotation Metadata_pert_type.
            "Metadata_pert_type": ["negcon" if well == first_well else "trt" for well in wells],
            "Metadata_Batch": "2020_11_04_CPJUMP1",
            "Metadata_Source": "source_4",
        },
        index=[
            f"{plate}_{well}_{site}_{obj}"
            for plate, well, site, obj in zip(plates, wells, sites, objects, strict=True)
        ],
    )
    var = pd.DataFrame(index=cell_painting_feature_names(n_features))

    x = _feature_matrix(n_obs, n_features, container, seed)
    adata = ad.AnnData(X=x, obs=obs, var=var)
    adata.layers["raw"] = _feature_matrix(n_obs, n_features, container, seed + 1)
    rng = np.random.default_rng(seed)
    adata.obsm["spatial"] = rng.uniform(0, 1080, size=(n_obs, 2)).astype(np.float32)

    if with_provenance:
        _add_pipeline_metadata(
            adata,
            schema_id="generic-cell-painting",
            processing_stage="normalized",
            layer_stages={"raw": "raw"},
        )
    return adata


def make_pycytominer_well_profile(
    *,
    n_plates: int = 2,
    n_wells: int = 6,
    n_features: int = 12,
    container: MatrixContainer = "dense",
    with_provenance: bool = True,
    seed: int = 0,
) -> ad.AnnData:
    """A pycytominer-style well profile: one aggregated row per plate/well.

    Includes ``Metadata_broad_sample`` (as a real profile would) and a PCA
    embedding in ``.obsm``, plus the ``uns['aggregation']`` provenance an
    aggregated profile is expected to declare.
    """
    records = list(
        product([f"BR0011{plate:04d}" for plate in range(n_plates)], well_names(n_wells))
    )
    plates, wells = (list(column) for column in zip(*records, strict=True))
    n_obs = len(records)
    first_well = well_names(n_wells)[0]

    obs = pd.DataFrame(
        {
            "Metadata_Plate": plates,
            "Metadata_Well": wells,
            "Metadata_broad_sample": [f"BRD-K{index:05d}" for index in range(n_obs)],
            "Metadata_pert_type": ["negcon" if well == first_well else "trt" for well in wells],
            "Metadata_Batch": "2020_11_04_CPJUMP1",
            "Metadata_Source": "source_4",
        },
        index=[f"{plate}_{well}" for plate, well in zip(plates, wells, strict=True)],
    )
    var = pd.DataFrame(index=cell_painting_feature_names(n_features))

    adata = ad.AnnData(X=_feature_matrix(n_obs, n_features, container, seed), obs=obs, var=var)
    rng = np.random.default_rng(seed)
    adata.obsm["X_pca"] = rng.normal(size=(n_obs, 5)).astype(np.float32)

    if with_provenance:
        _add_pipeline_metadata(
            adata,
            schema_id="generic-cell-painting",
            processing_stage="aggregated",
            aggregation={
                "method": "median",
                "replicate_count": 6,
                "source_level": "single-cell",
            },
        )
    return adata


def make_jump_treatment_profile(
    *,
    n_perturbations: int = 6,
    n_features: int = 12,
    container: MatrixContainer = "dense",
    with_provenance: bool = True,
    seed: int = 0,
) -> ad.AnnData:
    """A JUMP-style treatment profile: one row per perturbation, aggregated across wells.

    Uses JUMP metadata spellings (``Metadata_JCP2022``,
    ``Metadata_broad_sample``, ``Metadata_perturbation_modality``) and so is
    intended to be validated against the ``jump-cp`` schema. Plate/well columns
    are deliberately absent -- they were aggregated away -- which is why
    ``uns['aggregation']`` must document ``method`` and ``source_level``.
    """
    modalities = ("compound", "orf", "crispr")
    control_types = ("negcon", "poscon", "trt")
    perturbations = [f"JCP2022_{index:06d}" for index in range(n_perturbations)]

    obs = pd.DataFrame(
        {
            "Metadata_JCP2022": perturbations,
            "Metadata_broad_sample": [f"BRD-K{index:05d}" for index in range(n_perturbations)],
            "Metadata_pert_type": [
                control_types[index % len(control_types)] for index in range(n_perturbations)
            ],
            "Metadata_perturbation_modality": [
                modalities[index % len(modalities)] for index in range(n_perturbations)
            ],
            "Metadata_Batch": "2020_11_04_CPJUMP1",
            "Metadata_Source": "source_4",
        },
        index=perturbations,
    )
    var = pd.DataFrame(index=cell_painting_feature_names(n_features))

    adata = ad.AnnData(
        X=_feature_matrix(n_perturbations, n_features, container, seed), obs=obs, var=var
    )
    rng = np.random.default_rng(seed)
    adata.obsm["X_pca"] = rng.normal(size=(n_perturbations, 5)).astype(np.float32)

    if with_provenance:
        _add_pipeline_metadata(
            adata,
            schema_id="jump-cp",
            processing_stage="treatment_aggregated",
            aggregation={"method": "median", "replicate_count": 4, "source_level": "well"},
        )
    return adata


@dataclass(frozen=True)
class RealisticDataset:
    """One realistic dataset, together with how it is meant to be validated."""

    name: str
    build: Callable[..., ad.AnnData]
    schema: str
    expected_level: ProfileLevel


REALISTIC_DATASETS: tuple[RealisticDataset, ...] = (
    RealisticDataset(
        name="cellprofiler-single-cell",
        build=make_cellprofiler_single_cell,
        schema="generic-cell-painting",
        expected_level=ProfileLevel.SINGLE_CELL,
    ),
    RealisticDataset(
        name="pycytominer-well",
        build=make_pycytominer_well_profile,
        schema="generic-cell-painting",
        expected_level=ProfileLevel.WELL,
    ),
    RealisticDataset(
        name="jump-treatment",
        build=make_jump_treatment_profile,
        schema="jump-cp",
        expected_level=ProfileLevel.TREATMENT,
    ),
)
"""Every realistic dataset, for parametrizing parity tests over all three levels."""
