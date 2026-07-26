# Public-data pilots

Notes from validating real public Cell Painting profiles with
`cp-anndata-validator`, without committing large binaries or fabricating
governance metadata.

## LINCS Cell Painting (cpg0004-lincs)

### Prefer the Cell Painting Gallery over the Zenodo v0.1 ZIP

The Zenodo “Initial Processed Data Release”
([10.5281/zenodo.3928744](https://doi.org/10.5281/zenodo.3928744)) ships a Git
repository tree whose Level 3/4a/4b/5 profile `.csv.gz` files are **Git LFS
pointers**, not gzip payloads. Those pointers are unsuitable for conversion.

Use the [Cell Painting Gallery](https://github.com/broadinstitute/cellpainting-gallery)
anonymous S3 bucket instead. For LINCS Pilot 1 profiles the prefix is:

```text
s3://cellpainting-gallery/cpg0004-lincs/broad/workspace/
```

(not `s3://cellpainting-gallery/cpg0004-lincs/workspace/`).

### Tested Level 4b plate

| Item | Value |
|---|---|
| Object | `profiles/2016_04_01_a549_48hr_batch1/SQ00014812/SQ00014812_normalized_feature_select.csv.gz` |
| Processing level | **Level 4b** — whole-plate normalized, feature-selected, **well-level** profiles (pycytominer) |
| Plate | `SQ00014812` |

Do **not** choose images, cell-count-only CSVs, single-cell SQLite backends, or
collection-wide consensus tables for a well-level AnnData pilot.

### Conversion mapping (truthful)

| Source | AnnData |
|---|---|
| Each profile row | one observation |
| Columns beginning with `Metadata_` | `adata.obs` |
| Cell Painting measurement columns (`Cells_` / `Cytoplasm_` / `Nuclei_`, …) | `adata.X` with names in `adata.var_names` |
| Plate + well | deterministic `obs_names` (for example `SQ00014812_A01`) |

Do **not** invent `uns.schema_id`, `uns.licence`, aggregation, image /
segmentation / feature-extraction provenance, or `processing_stage` merely to
clear warnings. A clean report is not the goal of a public-data pilot;
faithful conversion is.

### `Metadata_pert_type` is not perturbation modality

In LINCS / pycytominer-augmented exports, `Metadata_pert_type` commonly stores
**control vs treatment** status (and related control labels). Built-in schemas
map that column to canonical **`control_type`**.

It must **not** be treated as **`perturbation_modality`** (compound / ORF /
CRISPR / …). Missing modality still surfaces as `IDENT007`; that warning is
expected when the source never recorded a true modality column.

### Batch identifiers

LINCS plates often carry `Metadata_Batch_Number`. Built-in schemas (from
`schema_version` **0.2.1**) accept that name as an alias of canonical `batch`,
after the existing aliases (`batch_id` / `batch` / `Metadata_Batch`, schema-
specific order). Exact, case-insensitive matching and first-alias-wins
precedence are unchanged.

### Expected warnings for a truthful conversion

A bare Level 4b → AnnData conversion typically **passes** normal validation
(exit 0) with governance warnings only, and **fails** under `--strict`
(exit 1). Common codes:

- `AGG001` — no `uns.aggregation` (well profiles are aggregates)
- `LICENSE001`, `SCHEMA001`, `SCHEMA002`
- `META002`, `PROVFEAT001`, `PROVIMG001`, `PROVSEG001`, `SLOT001`
- `IDENT007` — no perturbation modality column
- `META003` — no source/site column (informational)

These are expected governance / completeness signals, not proof the matrix is
scientifically invalid.

### Pilot outcome (SQ00014812 Level 4b)

| Check | Result |
|---|---|
| Schema | `generic-cell-painting` |
| Shape | **384 × 493** (dense `float32`) |
| Auto-detected profile level | **well**, confidence **1.0** |
| Normal validation | **PASS** (exit 0) |
| Strict validation | **FAIL** (exit 1) due to warnings only |
| `ENGINE001` | none |
| `FEAT001` / `FEAT002` | none (CellProfiler compartment/family names) |
| In-memory vs `--backed` | identical issue codes |

## JUMP Cell Painting pilot (cpg0000-jump-pilot)

### Public source

```text
s3://cellpainting-gallery/cpg0000-jump-pilot/
```

Profiles for the tested plate live under:

```text
source_4/workspace/profiles/2020_11_04_CPJUMP1/BR00116991/
```

### Tested feature-selected profile

| Item | Value |
|---|---|
| Filename | `BR00116991_normalized_feature_select_batch.csv.gz` |
| Source / batch / plate | `source_4` / `2020_11_04_CPJUMP1` / `BR00116991` |
| Processing level | Feature-selected, **batch-normalized** well profiles |

JUMP Gallery profile names for this dataset may use
`*_normalized_feature_select_batch.csv.gz` (and a `*_negcon_batch*` sibling).
Do **not** assume every plate publishes only `*_normalized_feature_select_plate.csv.gz`
— those `*_plate*` filenames were absent for BR00116991.

Do **not** choose images, `load_data` CSVs, single-cell SQLite backends,
cell-count-only tables, or collection-wide assembled matrices.

### Profile-level evidence

- **384** rows and **384** unique `Metadata_Plate` + `Metadata_Well` pairs
- Approximately one row per well; no site or object-identifier columns
- Inferred AnnData profile level: **well**

### Conversion mapping (truthful)

Same mapping as the LINCS pilot: `Metadata_*` → `obs`, Cell Painting
measurements → `X` / `var_names`, deterministic `plate_well` `obs_names`.
Preserve genuine JUMP column names. Do **not** invent schema, licence,
aggregation, provenance, modality, **source**, or **batch** fields merely to
clear warnings.

Storage-path segments such as `source_4` or `2020_11_04_CPJUMP1` must **not**
be silently written into `obs` as `Metadata_Source` / `Metadata_Batch` unless
those columns already exist in the profile table.

### Metadata conventions observed on BR00116991

| Present in profile | Absent from profile |
|---|---|
| `Metadata_Plate`, `Metadata_Well` | `Metadata_Source` |
| `Metadata_broad_sample` (resolves `perturbation_id`) | `Metadata_Batch` / `Metadata_Batch_Number` |
| `Metadata_pert_iname` | `Metadata_JCP2022` |
| `Metadata_pert_type` = `trt` / `control` | true perturbation-modality column |

`Metadata_pert_type` here is **treatment/control** status (`control_type`),
not chemical/genetic modality. Missing modality still yields `IDENT007`.

`Metadata_Source` and `Metadata_Batch` are useful when present, but they are
**not** guaranteed on every public JUMP Gallery profile table.

### Pilot outcome (BR00116991, `jump-cp` 0.2.1)

| Check | Result |
|---|---|
| Shape | **384 × 838** (dense `float32`) |
| Auto-detected profile level | **well**, confidence **1.0** |
| Normal validation | **PASS** (exit 0) |
| Strict validation | **FAIL** (exit 1) due to warnings only |
| `--backed` | identical issue codes to in-memory |
| `generic-cell-painting` comparison | **same** issue-code set |
| Plate / well / perturbation resolution | OK (`Metadata_broad_sample`) |
| `ENGINE001` | none |
| `FEAT001` / `FEAT002` | none |
| `CTRL002` / `CTRL003` | none |

Exact issue codes (all explainable governance or source-metadata findings —
not validator defects):

`AGG001`, `IDENT007`, `LICENSE001`, `META001`, `META002`, `META003`,
`PROVFEAT001`, `PROVIMG001`, `PROVSEG001`, `SCHEMA001`, `SCHEMA002`, `SLOT001`.

## Repository hygiene

- Do **not** commit `.h5ad` files or large public dataset downloads (LINCS,
  JUMP, or otherwise).
- Keep pilot downloads and conversion outputs outside this Git repository
  (for example under `~/Downloads/cp-validator-pilot/`).
