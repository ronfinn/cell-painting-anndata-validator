# Alias resolution and precedence

Schema field aliases are matched **case-insensitively** after trimming
whitespace, **in declaration order**. The first exact match wins. There is no
regex or fuzzy matching, and no inference from column contents.

Because matching is case-insensitive, the same alias (case-insensitively)
cannot appear twice within one field's `aliases` list, nor be reused across
two different fields in the same schema — both are rejected at load time with
a descriptive `SchemaError`.

## `batch` alias precedence (schema v0.2.1)

| Schema | Order |
|---|---|
| `generic-cell-painting` | `batch_id` → `batch` → `Metadata_Batch` → `Metadata_Batch_Number` |
| `jump-cp` | `Metadata_Batch` → `batch_id` → `Metadata_Batch_Number` |

`Metadata_Batch_Number` is the LINCS-style batch field observed on Cell
Painting Gallery Level 4b profiles.

## `perturbation_id` alias precedence (schema v0.2.0+)

| Schema | Order |
|---|---|
| `jump-cp` | `Metadata_JCP2022` → `Metadata_broad_sample` → `Metadata_pert_iname` → `perturbation_id` → `pert_id` → `treatment_id` |
| `generic-cell-painting` | `perturbation_id` → `pert_id` → `treatment_id` → `Metadata_broad_sample` → `Metadata_pert_iname` → `Metadata_JCP2022` |

## `Metadata_pert_type` vs perturbation modality

`Metadata_pert_type` is an alias of **`control_type`** only (control vs
treatment / poscon / negcon / trt). It is **not** an alias of
`perturbation_modality`. In LINCS exports that column commonly means control
status, not chemical/genetic modality — see [Public-data pilots](../pilots/index.md).

## Implementation

- Resolution: `src/cp_anndata_validator/schema/resolve.py`
- Schema load validation: `src/cp_anndata_validator/schema/loader.py`
- Tests: `tests/test_schema_resolution.py`, `tests/test_batch_alias_lincs.py`

See also [ADR-0005](../decisions/ADR-0005-alias-resolution.md) and
[Known limitations](../project/limitations.md).
