# Rule-code catalogue

Every validation issue carries a stable `code` (for example `IDENT001`).
Codes are permanent: once shipped, a code is never renumbered or reused for
a different meaning, even if the underlying check is later refined. If a
check is removed, its code is retired, not recycled. (Two codes in this
catalogue — `MATRIX003` and `FEAT002` — were sketched with a different
meaning in an early design draft but never shipped that way, so they were
free to be assigned their current, shipped meaning; see the note at the
bottom of this page.)

Each row lists the default severity (`error`, `warning`, or `information`),
the check module that emits it, and the exact remediation text a user sees
in the issue's `remediation` field. Every check reports `location` using
the *physical* AnnData column it resolved (for example `obs.Metadata_Plate`)
wherever a column was actually resolved; when nothing resolved, `location`
names the canonical field instead (for example `obs.plate`).

## Structure (`checks/structure.py`)

| Code | Severity | Meaning | Remediation |
|---|---|---|---|
| `STRUCT001` | error | Reserved. An unreadable/corrupt file never reaches check execution — it is raised as `LoadError` and surfaces as CLI exit code 2, not as a report issue. | Fix or re-export the source file so it is a valid, readable `.h5ad`. |
| `STRUCT002` | error | The AnnData object has no observations, no features, or no `.X` matrix. | Provide a non-empty X matrix with at least one observation and feature. |
| `INDEX001` | error | `obs_names` contains duplicate values. | Ensure every obs_names value is unique. |
| `INDEX002` | error | `var_names` contains duplicate values. | Ensure every var_names value is unique. |
| `INDEX003` | error | `obs_names` or `var_names` contains an empty value. | Assign a non-empty identifier to every obs/var entry. |

## Identifiers (`checks/identifiers.py`)

| Code | Severity | Meaning | Remediation |
|---|---|---|---|
| `IDENT001` | error | No column resolved for the canonical `plate` field, required for the effective profile level. | Add an `.obs` column for `plate` using one of the schema's declared aliases, or choose a schema/profile level that matches this dataset. |
| `IDENT002` | error | No column resolved for the canonical `well` field. | Same as `IDENT001`, for `well`. |
| `IDENT003` | error | No column resolved for the canonical `site` field (single-cell). | Same as `IDENT001`, for `site`. |
| `IDENT004` | error | No column resolved for the canonical `cell_id` field (single-cell only — **not** required at well or treatment level). | Same as `IDENT001`, for `cell_id`. |
| `IDENT005` | error | No column resolved for the canonical `perturbation_id` field (treatment). | Same as `IDENT001`, for `perturbation_id`. |
| `IDENT006` | error | A treatment-level profile has neither direct plate+well identifiers nor adequate `uns['aggregation']` provenance (both `method` and `source_level`), so its rows cannot be traced back to source data. | Either keep plate/well identifier columns on treatment-level rows, or declare `uns['aggregation']` with both `'method'` and `'source_level'`. |
| `IDENT007` | warning | A perturbation identifier resolved, but no perturbation modality column did. | Add a perturbation modality column (for example `Metadata_perturbation_modality`) with a value such as compound/orf/crispr. |
| `IDENT008` | warning | The perturbation modality column contains an unrecognized value. | Use a recognized modality (compound, orf, crispr, crispr_ko, crispr_a, unknown), or extend the schema/documentation to cover this value. |
| `OBS001` | error | Two or more observations share an identical identifier-column tuple. | Ensure each observation's identifier columns uniquely identify it, or remove/merge duplicated rows. |
| `OBS002` | error | An identifier column has one or more missing (null) values. | Populate the column for every observation, or remove incomplete rows. |

## Profile consistency (`checks/profile_consistency.py`)

| Code | Severity | Meaning | Remediation |
|---|---|---|---|
| `PROFILE001` | error | The effective (declared or detected) profile level's required fields are not all resolved. | Add the missing identifier column(s), or select a different `--profile-level`. |
| `PROFILE002` | information | Auto-detection could not settle on a single profile level (see [profile-levels.md](profile-levels.md)). | Pass `--profile-level` explicitly to disambiguate. |
| `PROFILE003` | warning | A declared `--profile-level` disagrees with what auto-detection found. | Confirm the declared level is correct, or drop `--profile-level` to use auto-detection. |

## Matrix and slot semantics (`checks/matrix.py`)

| Code | Severity | Meaning | Remediation |
|---|---|---|---|
| `MATRIX001` | error | `.X` has a non-numeric dtype. | Store feature values as a numeric dtype (integer or floating point). |
| `MATRIX002` | warning | `.X` contains NaN/Inf values (checked via bounded, sparse-safe sampling — never `.toarray()`). | Investigate and either impute, mask, or document non-finite values. |
| `MATRIX003` | error | `.X`'s shape does not equal `(n_obs, n_vars)`. A real `anndata.AnnData` enforces this on construction, so this only fires for a hand-edited or corrupted `.h5ad` file. | Ensure X has exactly one row per observation and one column per feature. |
| `MATRIX004` | error | A `.layers` entry's shape does not match `.X`'s shape. | Ensure every layer has the same shape as X. |
| `SLOT001` | warning | No processing stage is declared for `.X` (`uns['processing_stage']`). | Set `uns['processing_stage']` (for example `'raw'`, `'normalized'`, or `'aggregated'`). |
| `SLOT002` | error | An `.obsm`/`.varm` entry's first dimension does not match `n_obs`/`n_vars`. | Ensure every `obsm`/`varm` entry's first dimension matches `n_obs`/`n_vars`. |
| `SLOT003` | warning | One or more `.layers` entries have no declared processing stage. | Declare each layer's processing stage in `uns['layer_processing_stages'][<layer name>]`. |

## Annotations (`checks/annotations.py`)

| Code | Severity | Meaning | Remediation |
|---|---|---|---|
| `CTRL001` | warning | No control/treatment annotation column resolved. | Add a control/treatment annotation column (for example `Metadata_pert_type`) with values such as negcon/poscon/trt. |
| `CTRL002` | warning | The control/treatment column contains an unrecognized label. | Use one of the recognized labels (negcon, poscon, trt, control, treatment), or extend the schema/documentation to cover this label. |
| `CTRL003` | warning | No negative control (`negcon`) annotation was found. | Include at least one negative control (for example labeled `'negcon'`) to support downstream normalization and QC. |

## Features (`checks/features.py`)

| Code | Severity | Meaning | Remediation |
|---|---|---|---|
| `FEAT001` | warning | One or more feature names do not start with a schema-declared compartment prefix. | Prefix feature names with a declared compartment (for example `'Cells_'`), or add the compartment to the schema. |
| `FEAT002` | warning | One or more feature names (that *did* match a compartment) don't encode a recognized measurement family (for example `AreaShape`, `Intensity`, `Texture`) right after their compartment prefix. | Name features as `'<compartment>_<measurement family>_...'` using one of the schema's declared measurement families, or add the family to the schema. |

## Metadata (`checks/metadata.py`)

| Code | Severity | Meaning | Remediation |
|---|---|---|---|
| `META001` | information | No batch identifier column resolved. | Add a batch identifier column if this dataset spans multiple experimental batches. |
| `META002` | warning | No experiment metadata block (`uns['experiment']`). | Record experiment-level metadata (for example instrument, protocol, date) in `uns['experiment']`. |
| `META003` | information | No data-generating source/site identifier column resolved. | Add a source identifier column if this dataset spans multiple data-generating sites or laboratories. |

## Provenance (`checks/provenance.py`)

| Code | Severity | Meaning | Remediation |
|---|---|---|---|
| `PROVIMG001` | warning | No image provenance block (`uns['image_provenance']`). | Record source image and illumination-correction provenance in `uns['image_provenance']`. |
| `PROVSEG001` | warning | No segmentation method/tool declared (`uns['segmentation_provenance']`). | Record the segmentation method/tool and version in `uns['segmentation_provenance']`. |
| `PROVFEAT001` | warning | No feature-extraction tool/version declared (`uns['feature_extraction_provenance']`). | Record the feature-extraction tool and version in `uns['feature_extraction_provenance']`. |

## Schema and licence (`checks/schema_meta.py`)

| Code | Severity | Meaning | Remediation |
|---|---|---|---|
| `SCHEMA001` | warning | No schema identifier declared (`uns['schema_id']`). | Record `uns['schema_id']` so downstream tools know which schema this dataset targets. |
| `SCHEMA002` | warning | No schema version declared (`uns['schema_version']`). | Record `uns['schema_version']` alongside `uns['schema_id']`. |
| `LICENSE001` | warning | No dataset licence declared (`uns['licence']`/`uns['license']`). | Record the dataset's licence in `uns['licence']`. |

## Aggregation (`checks/aggregation.py`, well/treatment profiles only)

| Code | Severity | Meaning | Remediation |
|---|---|---|---|
| `AGG001` | error | No aggregation method declared (`uns['aggregation']['method']`). | Record how rows were aggregated in `uns['aggregation']['method']`. |
| `AGG002` | warning | No replicate count declared (`uns['aggregation']['replicate_count']`). | Record the number of replicates aggregated per row in `uns['aggregation']['replicate_count']`. |
| `AGG003` | warning | No source profile level declared (`uns['aggregation']['source_level']`) — the level rows were aggregated *from* (for example `single-cell` or `well`). | Record which profile level rows were aggregated from in `uns['aggregation']['source_level']`. |

## AI readiness (`checks/ai_readiness.py`)

| Code | Severity | Meaning | Remediation |
|---|---|---|---|
| `AI001` | information | One or more feature columns are constant (zero-variance) across the sampled rows. | Consider removing zero-variance features before model training. |
| `AI002` | warning | More than 20% of sampled feature values are missing (NaN). | Impute, mask, or document missing feature values before model training. |

## Engine (`orchestrator.py`)

| Code | Severity | Meaning | Remediation |
|---|---|---|---|
| `ENGINE001` | error | A registered check raised an unexpected exception. The rest of the run continues; this issue replaces that check's (missing) result. Never emitted by an individual check itself. | Report this as a bug in `cp-anndata-validator`, including the check name and a minimal reproducing dataset if possible. |

## Cross-cutting design notes

- **Physical column reporting.** Whenever a check resolves an actual
  `.obs`/`.var` column for a canonical field, its `location` (and often its
  `evidence`) names that physical column, not the canonical name — see
  `CTRL002`/`CTRL003`, `OBS001`/`OBS002`, `IDENT008`. Only when *nothing*
  resolved does an issue fall back to the canonical field name (`IDENT001`
  through `IDENT005`, `IDENT007`, `META001`, `META003`, `CTRL001`).
- **Bounded evidence, never raw sensitive dumps.** Any check that could
  otherwise list an unbounded number of values (duplicate identifiers,
  unrecognized labels, unmatched feature names, undeclared layers) truncates
  `evidence` to at most 5 examples and never dumps a full per-row value
  table. `Report`/console/JSON/HTML renderers never re-expand these lists.
- **Profile-level-dependent requirements.** `IDENT001`–`IDENT005` only fire
  for fields required by the *effective* profile level (declared, or
  detected when not declared) — see [profile-levels.md](profile-levels.md).
  In particular: a well-level profile never requires `cell_id` (`IDENT004`),
  and a treatment-level profile never requires `plate`/`well` directly
  (`IDENT001`/`IDENT002`) as long as `IDENT006` doesn't fire instead.

## Notes on earlier drafts

The original design brainstorm also sketched an early `MATRIX003` meaning
("dtype vs. declared processing stage") and `FEAT002` (duplicate feature
name — already covered by `INDEX002`). Neither was ever shipped, so both
codes were free to reassign without violating the "never renumber or
reuse" rule: `MATRIX003` was later shipped with its current meaning
(`.X` shape vs. `(n_obs, n_vars)`); `FEAT002` was later shipped with its
current meaning (unrecognized measurement family).
