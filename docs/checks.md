# Rule-code catalogue

Every validation issue carries a stable `code` (for example `IDENT001`).
Codes are permanent: once shipped, a code is never renumbered or reused for
a different meaning, even if the underlying check is later refined. If a
check is removed, its code is retired, not recycled.

Each row lists the default severity (`error`, `warning`, or `information`),
the category, and which registered check (`checks/<module>.py`) emits it.

## Structure (`checks/structure.py`)

| Code | Severity | Meaning |
|---|---|---|
| `STRUCT001` | error | Reserved. An unreadable/corrupt file never reaches check execution — it is raised as `LoadError` and surfaces as CLI exit code 2, not as a report issue. |
| `STRUCT002` | error | The AnnData object has no observations, no features, or no `.X` matrix. |
| `INDEX001` | error | `obs_names` contains duplicate values. |
| `INDEX002` | error | `var_names` contains duplicate values. |
| `INDEX003` | error | `obs_names` or `var_names` contains an empty value. |

## Identifiers (`checks/identifiers.py`)

| Code | Severity | Meaning |
|---|---|---|
| `IDENT001` | error | No column resolved for the canonical `plate` field, required for the effective profile level. |
| `IDENT002` | error | No column resolved for the canonical `well` field. |
| `IDENT003` | error | No column resolved for the canonical `site` field (single-cell). |
| `IDENT004` | error | No column resolved for the canonical `cell_id` field (single-cell). |
| `IDENT005` | error | No column resolved for the canonical `perturbation_id` field (treatment). |
| `OBS001` | error | Two or more observations share an identical identifier-column tuple. |
| `OBS002` | error | An identifier column has one or more missing (null) values. |

## Profile consistency (`checks/profile_consistency.py`)

| Code | Severity | Meaning |
|---|---|---|
| `PROFILE001` | error | The effective (declared or detected) profile level's required fields are not all resolved. |
| `PROFILE002` | information | Auto-detection could not settle on a single profile level (see [profile-levels.md](profile-levels.md)). |
| `PROFILE003` | warning | A declared `--profile-level` disagrees with what auto-detection found. |

## Matrix and slot semantics (`checks/matrix.py`)

| Code | Severity | Meaning |
|---|---|---|
| `MATRIX001` | error | `.X` has a non-numeric dtype. |
| `MATRIX002` | warning | `.X` contains NaN/Inf values (checked via bounded, sparse-safe sampling). |
| `MATRIX004` | error | A `.layers` entry's shape does not match `.X`'s shape. |
| `SLOT001` | warning | No processing stage is declared (`uns['processing_stage']`). |
| `SLOT002` | error | An `.obsm`/`.varm` entry's first dimension does not match `n_obs`/`n_vars`. |

## Annotations (`checks/annotations.py`)

| Code | Severity | Meaning |
|---|---|---|
| `CTRL001` | warning | No control/treatment annotation column resolved. |
| `CTRL002` | warning | The control/treatment column contains an unrecognized label. |
| `CTRL003` | warning | No negative control (`negcon`) annotation was found. |

## Features (`checks/features.py`)

| Code | Severity | Meaning |
|---|---|---|
| `FEAT001` | warning | One or more feature names do not start with a schema-declared compartment prefix. |

## Metadata (`checks/metadata.py`)

| Code | Severity | Meaning |
|---|---|---|
| `META001` | information | No batch identifier column resolved. |
| `META002` | warning | No experiment metadata block (`uns['experiment']`). |

## Provenance (`checks/provenance.py`)

| Code | Severity | Meaning |
|---|---|---|
| `PROVIMG001` | warning | No image provenance block (`uns['image_provenance']`). |
| `PROVSEG001` | warning | No segmentation method/tool declared (`uns['segmentation_provenance']`). |
| `PROVFEAT001` | warning | No feature-extraction tool/version declared (`uns['feature_extraction_provenance']`). |

## Schema and licence (`checks/schema_meta.py`)

| Code | Severity | Meaning |
|---|---|---|
| `SCHEMA001` | warning | No schema identifier declared (`uns['schema_id']`). |
| `SCHEMA002` | warning | No schema version declared (`uns['schema_version']`). |
| `LICENSE001` | warning | No dataset licence declared (`uns['licence']`/`uns['license']`). |

## Aggregation (`checks/aggregation.py`, well/treatment profiles only)

| Code | Severity | Meaning |
|---|---|---|
| `AGG001` | error | No aggregation method declared (`uns['aggregation']['method']`). |
| `AGG002` | warning | No replicate count declared (`uns['aggregation']['replicate_count']`). |

## AI readiness (`checks/ai_readiness.py`)

| Code | Severity | Meaning |
|---|---|---|
| `AI001` | information | One or more feature columns are constant (zero-variance) across the sampled rows. |
| `AI002` | warning | More than 20% of sampled feature values are missing (NaN). |

## Engine (`orchestrator.py`)

| Code | Severity | Meaning |
|---|---|---|
| `ENGINE001` | error | A registered check raised an unexpected exception. The rest of the run continues; this issue replaces that check's (missing) result. Never emitted by an individual check itself. |

## Notes on earlier drafts

The original design brainstorm also sketched `MATRIX003` (dtype vs.
declared processing stage) and `FEAT002` (duplicate feature name — already
covered by `INDEX002`). Both were consolidated away before implementation
to avoid overlapping meanings; the codes were never shipped, so no
renumbering was required.
