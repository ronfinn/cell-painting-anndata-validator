# cp-anndata-validator

A Python package and CLI that validates the semantic correctness, metadata
completeness, provenance, and AI-readiness of **Cell Painting datasets
stored as [AnnData](https://anndata.readthedocs.io/)** (`.h5ad`) objects —
for example, output produced by [CytoTable](https://github.com/cytomining/CytoTable)
from CellProfiler/DeepProfiler features.

`cp-anndata-validator` is read-only: it never converts other formats into
AnnData and never mutates the file it validates.

## Features

- **Structured issues, not text.** Every finding is a stable `Issue` with a
  rule code, severity, category, AnnData location, message, and
  remediation — usable programmatically or rendered as console/JSON/HTML.
- **Data-driven schemas.** Canonical fields (plate, well, perturbation, ...)
  resolve via configurable aliases, so column-naming conventions don't need
  to match exactly. Ships `generic-cell-painting` and a `jump-cp`
  compatibility preset; custom schema YAML files are also supported.
- **Explainable profile-level detection.** Auto-detects `single-cell`,
  `well`, or `treatment` granularity, with an explicit override and a
  human-readable explanation for how detection was decided.
- **Sparse- and backed-safe.** Numeric checks never densify a full sparse
  matrix; large/backed files are validated via bounded row sampling.
- **35+ built-in checks** across structure, identifiers, profile
  consistency, annotations, features, matrix/slot semantics, metadata,
  provenance, schema/licence declarations, aggregation, and AI-readiness.

## Install

```bash
uv add cp-anndata-validator
# or
pip install cp-anndata-validator
```

## Quick start

```bash
cp-validate experiment.h5ad
cp-validate experiment.h5ad --schema jump-cp --report report.html
cp-validate schema list
```

```python
from cp_anndata_validator import validate

report = validate("experiment.h5ad")
print(report.status)          # "pass" or "fail"
print(len(report.issues))
```

## Documentation

See [`docs/index.md`](docs/index.md) for the full documentation set,
including the [CLI reference](docs/cli.md), [Python API](docs/python-api.md),
[schema format](docs/schemas.md), [rule-code catalogue](docs/checks.md),
[profile-level detection](docs/profile-levels.md), and
[known limitations](docs/limitations.md).

## Development

```bash
uv sync
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv build
```

See [`docs/contributing.md`](docs/contributing.md) for the full dev
workflow and how to add a check or schema.
