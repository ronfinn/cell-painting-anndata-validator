"""Builders for small, synthetic Cell-Painting-style AnnData objects."""

from __future__ import annotations

from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd
from scipy import sparse

COMPARTMENTS = ("Cells", "Cytoplasm", "Nuclei")


def _feature_names(n_vars: int) -> list[str]:
    return [f"{COMPARTMENTS[i % len(COMPARTMENTS)]}_Intensity_Feature{i}" for i in range(n_vars)]


def _add_provenance_metadata(adata: ad.AnnData) -> None:
    """Populate every uns-level provenance/schema/licence block a check looks for."""
    adata.uns["image_provenance"] = {"microscope": "generic", "illumination_correction": True}
    adata.uns["segmentation_provenance"] = {"tool": "CellProfiler", "version": "4.2.6"}
    adata.uns["feature_extraction_provenance"] = {"tool": "CellProfiler", "version": "4.2.6"}
    adata.uns["experiment"] = {"instrument": "generic-scope", "protocol": "cell-painting-v1"}
    adata.uns["licence"] = "CC0-1.0"


def _add_aggregation_metadata(
    adata: ad.AnnData,
    *,
    method: str = "median",
    replicate_count: int = 4,
    source_level: str = "single-cell",
) -> None:
    adata.uns["aggregation"] = {
        "method": method,
        "replicate_count": replicate_count,
        "source_level": source_level,
    }


def make_single_cell_adata(
    n_obs: int = 12,
    n_vars: int = 6,
    *,
    sparse_x: bool = False,
    seed: int = 0,
) -> ad.AnnData:
    """A small, valid single-cell profile AnnData fixture.

    Includes plate/well/site/cell identifiers, a control/treatment
    annotation column, generic Cell Painting compartment-prefixed feature
    names, and minimal ``uns`` schema metadata.
    """
    rng = np.random.default_rng(seed)
    half = n_obs // 2

    obs = pd.DataFrame(
        {
            "plate_id": np.repeat(["Plate1", "Plate2"], [half, n_obs - half]),
            "well_id": np.tile(["A01", "A02"], n_obs // 2 + 1)[:n_obs],
            "site_id": np.tile(np.arange(1, 4), n_obs // 3 + 1)[:n_obs],
            "cell_id": np.arange(1, n_obs + 1),
            "control_type": ["negcon"] * half + ["trt"] * (n_obs - half),
            "batch_id": ["batch1"] * n_obs,
        },
        index=[f"cell_{i}" for i in range(n_obs)],
    )
    var = pd.DataFrame(index=_feature_names(n_vars))

    dense = rng.normal(size=(n_obs, n_vars)).astype(np.float32)
    dense[dense < 0] = 0.0
    x = sparse.csr_matrix(dense) if sparse_x else dense

    adata = ad.AnnData(X=x, obs=obs, var=var)
    adata.uns["schema_id"] = "generic-cell-painting"
    adata.uns["schema_version"] = "1.0.0"
    adata.uns["processing_stage"] = "normalized"
    _add_provenance_metadata(adata)
    return adata


def make_well_level_adata(
    n_wells: int = 8,
    n_vars: int = 6,
    *,
    sparse_x: bool = False,
    seed: int = 0,
) -> ad.AnnData:
    """A small, valid well-level profile AnnData fixture: one row per well.

    Each perturbation is replicated across two wells, so unique perturbation
    identifiers (``n_wells // 2``) outnumber neither wells nor rows -- this
    keeps well-vs-treatment cardinality unambiguous for detection.
    """
    rng = np.random.default_rng(seed)

    obs = pd.DataFrame(
        {
            "plate_id": np.repeat(["Plate1", "Plate2"], n_wells // 2 + n_wells % 2)[:n_wells],
            "well_id": [f"A{i + 1:02d}" for i in range(n_wells)],
            "perturbation_id": [f"JCP_{1000 + i // 2}" for i in range(n_wells)],
            "control_type": ["negcon"] + ["trt"] * (n_wells - 1),
        },
        index=[f"well_{i}" for i in range(n_wells)],
    )
    var = pd.DataFrame(index=_feature_names(n_vars))

    dense = rng.normal(size=(n_wells, n_vars)).astype(np.float32)
    x = sparse.csr_matrix(dense) if sparse_x else dense

    adata = ad.AnnData(X=x, obs=obs, var=var)
    adata.uns["schema_id"] = "generic-cell-painting"
    adata.uns["schema_version"] = "1.0.0"
    adata.uns["processing_stage"] = "aggregated"
    _add_provenance_metadata(adata)
    _add_aggregation_metadata(adata)
    return adata


def make_treatment_level_adata(
    n_treatments: int = 5,
    n_vars: int = 6,
    *,
    sparse_x: bool = False,
    seed: int = 0,
) -> ad.AnnData:
    """A small, valid treatment-level profile AnnData fixture: one row per perturbation."""
    rng = np.random.default_rng(seed)

    obs = pd.DataFrame(
        {
            "perturbation_id": [f"JCP_{2000 + i}" for i in range(n_treatments)],
            "control_type": ["negcon"] + ["trt"] * (n_treatments - 1),
        },
        index=[f"treatment_{i}" for i in range(n_treatments)],
    )
    var = pd.DataFrame(index=_feature_names(n_vars))

    dense = rng.normal(size=(n_treatments, n_vars)).astype(np.float32)
    x = sparse.csr_matrix(dense) if sparse_x else dense

    adata = ad.AnnData(X=x, obs=obs, var=var)
    adata.uns["schema_id"] = "generic-cell-painting"
    adata.uns["schema_version"] = "1.0.0"
    adata.uns["processing_stage"] = "treatment_aggregated"
    _add_provenance_metadata(adata)
    _add_aggregation_metadata(adata, source_level="well")
    return adata


def write_h5ad(adata: ad.AnnData, directory: Path, name: str = "dataset.h5ad") -> Path:
    """Write an AnnData object to a temporary ``.h5ad`` file and return its path."""
    path = directory / name
    adata.write_h5ad(path)
    return path
