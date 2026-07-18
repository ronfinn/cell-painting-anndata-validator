# cp-anndata-validator

`cp-anndata-validator` validates the semantic correctness, metadata
completeness, provenance, and AI-readiness of Cell Painting datasets that
have already been converted into [AnnData](https://anndata.readthedocs.io/)
(`.h5ad`) objects — for example by [CytoTable](https://github.com/cytomining/CytoTable).

It does **not** convert raw CellProfiler/DeepProfiler outputs into AnnData;
that is CytoTable's job. This package only reads and reports on AnnData
files that already exist.

## Why

An AnnData file can be structurally valid (opens fine, has a matrix, has an
index) while still being unusable for downstream Cell Painting analysis
because plate/well/site identifiers are inconsistent, control annotations
are missing, provenance for segmentation/feature-extraction isn't recorded,
or the profile level (single-cell vs. well vs. treatment) is ambiguous.
`cp-anndata-validator` turns those silent problems into a structured,
actionable report.

## Quick start

```bash
uv add cp-anndata-validator   # or: pip install cp-anndata-validator
cp-validate experiment.h5ad
```

```python
from cp_anndata_validator import validate

report = validate("experiment.h5ad")
print(report.status)   # "pass" or "fail"
```

## Documentation map

- [`cli.md`](cli.md) — every CLI command, flag, and exit code.
- [`python-api.md`](python-api.md) — the `validate()` function and renderers.
- [`schemas.md`](schemas.md) — schema YAML format, aliasing, custom schemas.
- [`profile-levels.md`](profile-levels.md) — single-cell/well/treatment detection.
- [`anndata-mapping.md`](anndata-mapping.md) — how this package interprets
  `.X`/`.obs`/`.var`/`.uns`/`.obsm`/`.varm`/`.layers`.
- [`checks.md`](checks.md) — the full, stable rule-code catalogue.
- [`jump-cp-derivation.md`](jump-cp-derivation.md) — provenance of the
  `jump-cp` compatibility preset.
- [`limitations.md`](limitations.md) — known v0.1 gaps and caveats.
- [`contributing.md`](contributing.md) — dev workflow, how to add a check
  or schema.
