# Provenance of the `jump-cp` schema

`jump-cp` is a **compatibility preset** shipped by `cp-anndata-validator`.
It is **not** an official schema endorsed by, or produced in cooperation
with, the JUMP Cell Painting Consortium. It exists so that AnnData files
converted from JUMP-style CellProfiler/CytoTable outputs resolve their
columns out of the box, without requiring every user to hand-write a custom
schema YAML file.

## Sources

- **Column-naming conventions** (`Metadata_Plate`, `Metadata_Well`,
  `Metadata_Site`, `Metadata_Source`, `Metadata_JCP2022`,
  `Metadata_Batch`, `Metadata_pert_type`, `Metadata_perturbation_modality`,
  `Metadata_ObjectNumber`) are taken from the public metadata README of the
  [`jump-cellpainting/datasets`](https://github.com/jump-cellpainting/datasets)
  repository:
  <https://github.com/jump-cellpainting/datasets/blob/main/metadata/README.md>
- **Feature compartment prefixes** (`Cells_`, `Cytoplasm_`, `Nuclei_`,
  `Image_`) follow the naming convention documented by
  [`pycytominer`](https://github.com/cytomining/pycytominer), the
  feature-aggregation library used throughout the JUMP pipeline and widely
  adopted across Cell Painting analyses more generally.

## What was and wasn't carried over

The schema (`src/cp_anndata_validator/schema/resources/jump-cp.yaml`) maps
each JUMP metadata column to the same canonical fields used by
`generic-cell-painting`, so that the rest of the package (checks, profile
detection, reports) treats a JUMP-style dataset identically to any other:

| Canonical field | JUMP alias | Notes |
|---|---|---|
| `plate` | `Metadata_Plate` | |
| `well` | `Metadata_Well` | |
| `site` | `Metadata_Site` | single-cell only |
| `cell_id` | `Metadata_ObjectNumber` | single-cell only |
| `perturbation_id` | `Metadata_JCP2022` | JUMP's perturbation code |
| `control_type` | `Metadata_pert_type` | JUMP's `poscon`/`negcon`/`trt` convention |
| `perturbation_modality` | `Metadata_perturbation_modality` | compound/orf/crispr/unknown |
| `batch` | `Metadata_Batch` | |
| `source` | `Metadata_Source` | JUMP's multi-site data-generation identifier |

Every field also keeps its `generic-cell-painting`-style alias (for example
`plate_id`, `well_id`) so a dataset that mixes conventions, or that has
already been partially renamed, still resolves.

## Explicitly not claimed

- This preset does not imply JUMP has reviewed, endorsed, or published this
  package.
- It does not attempt to encode every JUMP metadata column (see the two
  README/pycytominer sources above for the complete, authoritative list) —
  only the subset relevant to this package's validation categories.
- "Compatibility" refers to column-name aliasing convenience only; it makes
  no claim about compatibility with any specific JUMP data release version.
