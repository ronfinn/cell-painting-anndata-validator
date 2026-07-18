# Schemas

A schema is a versioned, data-driven YAML document describing:

- which **canonical semantic fields** a dataset is expected to have (for
  example `plate`, `well`, `perturbation_id`),
- which **column-name aliases** satisfy each canonical field,
- which fields are **required for which profile level**,
- which feature-name **compartment prefixes** are expected, and
- which feature-name **measurement families** are expected (for example
  `AreaShape`, `Intensity`, `Texture`).

Schemas never contain code, and are parsed with `yaml.safe_load` only.
Unknown top-level or per-field keys are rejected (not silently ignored) so a
typo in a schema file surfaces immediately rather than being ignored.

## Built-in schemas

| Name | Description |
|---|---|
| `generic-cell-painting` | Vendor-neutral schema; does not assume any single upstream pipeline's exact column names. |
| `jump-cp` | A compatibility preset based on public [JUMP Cell Painting Consortium](https://jump-cellpainting.broadinstitute.org/) metadata conventions. **Not** an official JUMP-endorsed AnnData schema — see [jump-cp-derivation.md](jump-cp-derivation.md). |

Inspect them with the CLI:

```bash
cp-validate schema list
cp-validate schema show jump-cp
```

## File format

```yaml
schema_id: my-lab-schema
schema_version: "1.0.0"
description: >
  A short, optional description.

fields:
  plate:
    aliases: [plate_id, Plate, Metadata_Plate]
    location: obs                 # "obs" or "var"
    required_for: [single-cell, well]   # subset of: single-cell, well, treatment
    description: Plate identifier.
  # ... more fields ...

compartments: [Cells, Cytoplasm, Nuclei, Image]
measurement_families: [AreaShape, Intensity, Texture]
```

- `fields` maps a **canonical field name** (used internally and in issue
  codes/messages) to a `FieldSpec`.
- `aliases` is checked **in order**; the first alias that matches an actual
  `.obs`/`.var` column (case-insensitive, exact after trimming whitespace)
  wins. There is no regex or fuzzy matching in v0.1 — see
  [limitations.md](limitations.md).
- Because matching is case-insensitive, the same alias (case-insensitively)
  cannot appear twice within one field's `aliases` list, nor be reused
  across two different fields in the same schema — both are rejected at
  load time with a descriptive `SchemaError`, since either would make
  resolution ambiguous.
- `schema_version` must be a semantic version (`MAJOR.MINOR.PATCH`, with
  optional pre-release/build metadata, e.g. `"0.1.0"` or `"2.0.0-rc.1"`);
  anything else is rejected at load time.
- `required_for` controls both the `IDENTxxx` completeness checks and
  profile-level auto-detection (see [profile-levels.md](profile-levels.md)).
- `compartments` drives the `FEAT001` check: every feature name should start
  with `"<compartment>_"` for one of the listed compartments.
- `measurement_families` drives the `FEAT002` check: every feature name that
  *did* match a compartment should be followed by `"<family>_"` for one of
  the listed measurement families (for example `Cells_AreaShape_Area`).
  Both `compartments` and `measurement_families` are optional; either check
  is skipped entirely if its list is empty.

## Using a custom schema

Any YAML file on disk can be used in place of a built-in name:

```bash
cp-validate experiment.h5ad --schema ./my-lab-schema.yaml
```

```python
from cp_anndata_validator import validate

report = validate("experiment.h5ad", schema="./my-lab-schema.yaml")
```

A malformed or missing custom schema raises
`cp_anndata_validator.SchemaError` with an actionable message (unknown key
name, invalid profile level in `required_for`, missing file, etc.) — this is
mapped to CLI exit code 2, before any checks run.

## Adding a new built-in schema

See [contributing.md](contributing.md#adding-a-schema).
