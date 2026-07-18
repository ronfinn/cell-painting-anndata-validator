#!/usr/bin/env python
"""Generate small demo ``.h5ad`` files for ``cp-anndata-validator``.

This produces three tiny, self-contained AnnData files, written next to this
script by default:

- ``valid_single_cell.h5ad``  -- a clean single-cell profile (expect exit 0).
- ``valid_well_level.h5ad``   -- a clean well-level (aggregated) profile (expect exit 0).
- ``invalid_example.h5ad``    -- a single-cell-shaped profile with several
  deliberate, independent problems spanning identifiers, structure,
  annotations, provenance, and matrix validity (expect exit 1).

These files are intentionally generated on demand rather than committed to
version control: they are binary HDF5 (even though small), and regenerating
them from this script keeps the examples guaranteed to match the current
schema and check set. Run it with:

    uv run python examples/generate_examples.py

Then validate the results, e.g.:

    uv run cp-validate examples/valid_single_cell.h5ad
    uv run cp-validate examples/valid_well_level.h5ad --schema jump-cp --profile-level well
    uv run cp-validate examples/invalid_example.h5ad --profile-level single-cell \
        --report examples/invalid_example.html

See ``examples/README.md`` for the exact issues the invalid example
demonstrates and the exit code each command above should produce.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd

_COMPARTMENTS = ("Cells", "Cytoplasm", "Nuclei")
_MEASUREMENT_FAMILIES = ("AreaShape", "Intensity", "Texture")


def _valid_feature_names(n: int) -> list[str]:
    """Compartment- and measurement-family-prefixed names, as ``FEAT001``/``FEAT002`` expect."""
    names = []
    for i in range(n):
        compartment = _COMPARTMENTS[i % len(_COMPARTMENTS)]
        family = _MEASUREMENT_FAMILIES[i % len(_MEASUREMENT_FAMILIES)]
        names.append(f"{compartment}_{family}_{i}")
    return names


def _shared_provenance_metadata() -> dict[str, object]:
    """The full set of ``uns`` blocks every provenance/licence/schema check looks for."""
    return {
        "schema_id": "generic-cell-painting",
        "schema_version": "0.1.0",
        "licence": "CC0-1.0",
        "experiment": {"instrument": "generic-scope", "protocol": "cell-painting-v1"},
        "image_provenance": {"microscope": "generic", "illumination_correction": True},
        "segmentation_provenance": {"tool": "CellProfiler", "version": "4.2.6"},
        "feature_extraction_provenance": {"tool": "CellProfiler", "version": "4.2.6"},
    }


def build_valid_single_cell(n_obs: int = 16, n_vars: int = 9, seed: int = 0) -> ad.AnnData:
    """A fully clean single-cell profile: every check should pass with zero issues."""
    rng = np.random.default_rng(seed)
    half = n_obs // 2

    obs = pd.DataFrame(
        {
            "plate_id": np.repeat(["Plate1", "Plate2"], [half, n_obs - half]),
            "well_id": np.tile(["A01", "A02", "B01", "B02"], n_obs // 4 + 1)[:n_obs],
            "site_id": np.tile(np.arange(1, 4), n_obs // 3 + 1)[:n_obs],
            "cell_id": np.arange(1, n_obs + 1),
            "control_type": ["negcon"] * half + ["trt"] * (n_obs - half),
            "batch_id": ["batch1"] * n_obs,
            "source_id": ["site-alpha"] * n_obs,
        },
        index=[f"cell_{i}" for i in range(n_obs)],
    )
    var = pd.DataFrame(index=_valid_feature_names(n_vars))
    x = np.clip(rng.normal(size=(n_obs, n_vars)), 0, None).astype(np.float32)

    adata = ad.AnnData(X=x, obs=obs, var=var)
    adata.uns.update(_shared_provenance_metadata())
    adata.uns["processing_stage"] = "normalized"
    return adata


def build_valid_well_level(n_wells: int = 8, n_vars: int = 9, seed: int = 0) -> ad.AnnData:
    """A fully clean, aggregated well-level profile: one row per plate/well."""
    rng = np.random.default_rng(seed)

    obs = pd.DataFrame(
        {
            "plate_id": np.repeat(["Plate1", "Plate2"], n_wells // 2),
            "well_id": [f"A{i + 1:02d}" for i in range(n_wells)],
            "perturbation_id": [f"JCP_{1000 + i // 2}" for i in range(n_wells)],
            "perturbation_modality": ["compound"] * n_wells,
            "control_type": ["negcon"] + ["trt"] * (n_wells - 1),
            "batch_id": ["batch1"] * n_wells,
            "source_id": ["site-alpha"] * n_wells,
        },
        index=[f"well_{i}" for i in range(n_wells)],
    )
    var = pd.DataFrame(index=_valid_feature_names(n_vars))
    x = np.clip(rng.normal(size=(n_wells, n_vars)), 0, None).astype(np.float32)

    adata = ad.AnnData(X=x, obs=obs, var=var)
    adata.uns.update(_shared_provenance_metadata())
    adata.uns["processing_stage"] = "aggregated"
    adata.uns["aggregation"] = {
        "method": "median",
        "replicate_count": 4,
        "source_level": "single-cell",
    }
    return adata


def build_invalid_example(n_obs: int = 10, n_vars: int = 8, seed: int = 0) -> ad.AnnData:
    """A single-cell-shaped profile with several independent, understandable problems.

    Deliberately missing/wrong, by design (see ``examples/README.md`` for the
    exact rule codes each one is expected to trigger):

    - No ``plate`` or ``cell_id`` column (only ``well``/``site`` remain).
    - Two observations share the same ``obs_names`` value.
    - No control/treatment annotation column.
    - No schema id/version, licence, or provenance ``uns`` blocks.
    - No declared processing stage for ``.X``.
    - Feature names that don't start with a recognized compartment prefix.
    - One non-finite (``NaN``) value in ``.X``.
    """
    rng = np.random.default_rng(seed)

    obs = pd.DataFrame(
        {
            "well_id": np.tile(["A01", "A02"], n_obs // 2 + 1)[:n_obs],
            "site_id": np.tile(np.arange(1, 4), n_obs // 3 + 1)[:n_obs],
        },
        index=[f"cell_{i}" for i in range(n_obs - 1)] + ["cell_0"],  # "cell_0" duplicated
    )
    var = pd.DataFrame(index=[f"feature_{i}" for i in range(n_vars)])  # no compartment prefix

    x = np.clip(rng.normal(size=(n_obs, n_vars)), 0, None).astype(np.float32)
    x[0, 0] = np.nan

    return ad.AnnData(X=x, obs=obs, var=var)  # no uns metadata at all


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).parent,
        help="Directory to write the generated .h5ad files into (default: this script's dir).",
    )
    args = parser.parse_args(argv)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    builders = {
        "valid_single_cell.h5ad": build_valid_single_cell(),
        "valid_well_level.h5ad": build_valid_well_level(),
        "invalid_example.h5ad": build_invalid_example(),
    }
    for filename, adata in builders.items():
        path = args.output_dir / filename
        adata.write_h5ad(path)
        size_kb = path.stat().st_size / 1024
        print(f"wrote {path} ({adata.n_obs} obs x {adata.n_vars} vars, {size_kb:.1f} KiB)")


if __name__ == "__main__":
    main()
