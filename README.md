# Cell Painting AnnData Validator

Validate the semantic correctness, metadata completeness, provenance and basic
AI readiness of Cell Painting datasets stored as
[AnnData](https://anndata.readthedocs.io/) (`.h5ad`) objects.

[Documentation](https://ronfinn.github.io/cell-painting-anndata-validator/) ·
[Quickstart](https://ronfinn.github.io/cell-painting-anndata-validator/getting-started/quickstart/) ·
[CLI](https://ronfinn.github.io/cell-painting-anndata-validator/reference/cli/) ·
[Python API](https://ronfinn.github.io/cell-painting-anndata-validator/reference/python-api/) ·
[Issues](https://github.com/ronfinn/cell-painting-anndata-validator/issues) ·
[Discussions](https://github.com/ronfinn/cell-painting-anndata-validator/discussions)

[![CI](https://github.com/ronfinn/cell-painting-anndata-validator/actions/workflows/ci.yml/badge.svg)](https://github.com/ronfinn/cell-painting-anndata-validator/actions/workflows/ci.yml)
[![Documentation](https://img.shields.io/badge/docs-GitHub%20Pages-teal)](https://ronfinn.github.io/cell-painting-anndata-validator/)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://github.com/ronfinn/cell-painting-anndata-validator)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.2.0b1-orange.svg)](https://github.com/ronfinn/cell-painting-anndata-validator/blob/main/CHANGELOG.md)

> **Beta (`0.2.0b1`).** Built-in schemas `generic-cell-painting` and `jump-cp`
> are at **`0.2.1`**. Rule codes and the public `validate()` surface are
> intended to stay stable within this beta line; schema aliases may still be
> calibrated from public evidence before a final `0.2.0`.

## Current capabilities

- Validate existing `.h5ad` files (dense, sparse, in-memory or backed)
- Versioned YAML schemas with ordered, exact alias resolution
- Profile levels: `single-cell`, `well`, `treatment` (detect or override)
- Structured issues with stable rule codes, severities and remediations
- Console, JSON and HTML reports
- CLI (`cp-validate`) and Python API (`validate`)

## Boundaries

| In scope | Out of scope |
|---|---|
| Structural validity of AnnData slots | Converting CellProfiler / DeepProfiler / CSV → AnnData |
| Semantic completeness vs a schema | Mutating or “fixing” the input file |
| Basic AI-readiness signals (sampled) | Biological or scientific suitability of a phenotype |
| Provenance / licence *presence* checks | Official JUMP-endorsed AnnData standardisation |

`jump-cp` is a **compatibility preset** from public JUMP metadata conventions,
not an official JUMP AnnData standard.

## Names

| Role | Name |
|---|---|
| Distribution | `cp-anndata-validator` |
| Import | `cp_anndata_validator` |
| CLI | `cp-validate` |
| Repository | [`ronfinn/cell-painting-anndata-validator`](https://github.com/ronfinn/cell-painting-anndata-validator) |

## Installation

From a local clone (recommended while beta):

```bash
git clone https://github.com/ronfinn/cell-painting-anndata-validator.git
cd cell-painting-anndata-validator
uv sync
uv run cp-validate --version
```

From a local wheel:

```bash
uv build
uv pip install dist/cp_anndata_validator-*.whl
cp-validate --version
```

## CLI example

```bash
uv run python examples/generate_examples.py
uv run cp-validate examples/valid_well_level.h5ad
uv run cp-validate examples/valid_well_level.h5ad --schema jump-cp --profile-level well
uv run cp-validate examples/valid_well_level.h5ad --report report.json
```

## Python example

```python
from cp_anndata_validator import validate

report = validate("examples/valid_well_level.h5ad")
print(report.status)
for issue in report.issues:
    print(issue.code, issue.severity.value, issue.message)
```

## Schemas (summary)

| Schema | Version | Role |
|---|---|---|
| `generic-cell-painting` | `0.2.1` | Vendor-neutral Cell Painting expectations |
| `jump-cp` | `0.2.1` | JUMP-oriented alias compatibility preset |

Custom schema YAML files are supported via `--schema path/to/schema.yaml`.
Unknown schema keys are rejected. See the
[schemas documentation](https://ronfinn.github.io/cell-painting-anndata-validator/schemas/).

## Normal vs strict

| Mode | Warnings fail? | Typical use |
|---|---|---|
| Normal (default) | No | Exploration; bare pipeline exports |
| `--strict` / `strict=True` | Yes | Publishing CI; governance enforcement |

Exit codes: `0` pass, `1` validation failures, `2` could not execute.

## Public-data evidence

Real Cell Painting Gallery well-level profiles were validated outside this
repository (binaries not committed):

- **LINCS** (`cpg0004-lincs`, plate `SQ00014812`, 384 × 493) under
  `generic-cell-painting`
- **JUMP pilot** (`cpg0000-jump-pilot`, plate `BR00116991`, 384 × 838) under
  `jump-cp`

Both passed normal validation (exit `0`), failed under `--strict` on expected
governance warnings only, and matched in-memory / `--backed` behaviour. Details:
[Public-data pilots](https://ronfinn.github.io/cell-painting-anndata-validator/pilots/).

## Documentation

| Topic | Link |
|---|---|
| Full docs site | https://ronfinn.github.io/cell-painting-anndata-validator/ |
| Installation & quickstart | [Getting started](https://ronfinn.github.io/cell-painting-anndata-validator/getting-started/) |
| Rule catalogue | [Schemas and checks](https://ronfinn.github.io/cell-painting-anndata-validator/schemas/rule-catalogue/) |
| Limitations | [Known limitations](https://ronfinn.github.io/cell-painting-anndata-validator/project/limitations/) |
| Changelog | [CHANGELOG.md](CHANGELOG.md) |

## Development

```bash
uv sync --all-groups
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run mkdocs build --strict
uv build
bash scripts/smoke_wheel.sh
```

## Contributing, licence, citation

- [Contributing](CONTRIBUTING.md) · [Code of Conduct](CODE_OF_CONDUCT.md) ·
  [Support](SUPPORT.md) · [Security](SECURITY.md)
- Licence: [Apache-2.0](LICENSE)
- Citation: [CITATION.cff](CITATION.cff)
