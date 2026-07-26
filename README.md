# Cell Painting AnnData Validator

**Validate the semantic correctness, metadata completeness, provenance and basic
AI readiness of Cell Painting datasets stored as
[AnnData](https://anndata.readthedocs.io/) (`.h5ad`) objects.**

[Documentation](https://ronfinn.github.io/cell-painting-anndata-validator/) ·
[Quickstart](https://ronfinn.github.io/cell-painting-anndata-validator/getting-started/quickstart/) ·
[CLI](https://ronfinn.github.io/cell-painting-anndata-validator/reference/cli/) ·
[Python API](https://ronfinn.github.io/cell-painting-anndata-validator/reference/python-api/) ·
[Report a bug](https://github.com/ronfinn/cell-painting-anndata-validator/issues/new/choose) ·
[Discussions](https://github.com/ronfinn/cell-painting-anndata-validator/discussions)

[![CI](https://github.com/ronfinn/cell-painting-anndata-validator/actions/workflows/ci.yml/badge.svg)](https://github.com/ronfinn/cell-painting-anndata-validator/actions/workflows/ci.yml)
[![Documentation](https://github.com/ronfinn/cell-painting-anndata-validator/actions/workflows/docs.yml/badge.svg)](https://github.com/ronfinn/cell-painting-anndata-validator/actions/workflows/docs.yml)
[![Python](https://img.shields.io/badge/python-3.12%20%7C%203.13%20%7C%203.14-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.2.0b1-orange)](CHANGELOG.md)
[![Documentation](https://img.shields.io/badge/docs-GitHub%20Pages-teal)](https://ronfinn.github.io/cell-painting-anndata-validator/)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://github.com/ronfinn/cell-painting-anndata-validator)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.2.0b1-orange.svg)](https://github.com/ronfinn/cell-painting-anndata-validator/blob/main/CHANGELOG.md)
<p align="center">
  <img
    src="docs/assets/cp-anndata-validator-social-preview.png"
    alt="Cell Painting AnnData Validator — semantic validation for Cell Painting AnnData files"
    width="100%"
  >
</p>

> [!IMPORTANT]
> **Beta (`0.2.0b1`).** The built-in `generic-cell-painting` and `jump-cp`
> schemas are at version **`0.2.1`**. Rule codes and the public `validate()`
> interface are intended to remain stable within this beta line, while schema
> aliases may still be calibrated from public evidence before the final
> `0.2.0` release.

## Current capabilities

- Validate existing `.h5ad` files using dense or sparse matrices
- Validate AnnData files in memory or in backed mode
- Detect or explicitly declare `single-cell`, `well` or `treatment` profiles
- Resolve metadata through versioned YAML schemas and ordered aliases
- Report structured findings with stable rule codes and suggested remediation
- Check identifiers, controls, feature naming, matrix values, metadata and provenance
- Generate console, JSON and self-contained HTML reports
- Use the validator through the `cp-validate` CLI or Python API
- Supply custom validation schemas without changing package source code

## Scope and boundaries

| In scope | Out of scope |
|---|---|
| Structural validity of AnnData slots | Converting CellProfiler, DeepProfiler or tabular output into AnnData |
| Semantic completeness against a schema | Mutating, repairing or rewriting the input file |
| Identifier and profile-level consistency | Automatically normalising or aggregating profiles |
| Basic sampled AI-readiness signals | Assessing the biological significance of a phenotype |
| Presence of licence and provenance metadata | Confirming that provenance claims are scientifically correct |
| Generic and JUMP-oriented compatibility schemas | Defining an official JUMP-endorsed AnnData standard |

The `jump-cp` schema is a **compatibility preset** based on publicly documented
JUMP metadata conventions. It is not an official JUMP AnnData standard.

## Installation

The package has not yet been published to PyPI.

### Requirements

- Python 3.12, 3.13 or 3.14
- [`uv`](https://docs.astral.sh/uv/) is recommended

### Install from source

```bash
git clone https://github.com/ronfinn/cell-painting-anndata-validator.git
cd cell-painting-anndata-validator

uv sync
uv run cp-validate --version
```

Expected version:

```text
0.2.0b1
```

### Install a locally built wheel

Build the package:

```bash
uv build
```

Install the wheel into the current environment:

```bash
uv pip install dist/cp_anndata_validator-*.whl
```

Confirm that the command is available:

```bash
cp-validate --version
```

See the full
[installation guide](https://ronfinn.github.io/cell-painting-anndata-validator/getting-started/installation/)
for additional details.

## CLI quickstart

### Generate the synthetic examples

```bash
uv run python examples/generate_examples.py
```

This creates:

```text
examples/valid_single_cell.h5ad
examples/valid_well_level.h5ad
examples/invalid_example.h5ad
```

The generated files are ignored by Git and are not committed to the repository.

### Validate a well-level profile

```bash
uv run cp-validate \
  examples/valid_well_level.h5ad \
  --profile-level well
```

Expected result:

```text
No issues found.

Counts: 0 issue(s)
Status: PASS
```

Expected exit code:

```text
0
```

### Use the JUMP compatibility schema

```bash
uv run cp-validate \
  examples/valid_well_level.h5ad \
  --schema jump-cp \
  --profile-level well
```

### Generate an HTML report

```bash
uv run cp-validate \
  examples/valid_well_level.h5ad \
  --profile-level well \
  --report validation-report.html
```

### Generate a JSON report

```bash
uv run cp-validate \
  examples/valid_well_level.h5ad \
  --profile-level well \
  --report validation-report.json
```

Existing reports are not overwritten unless `--force` is supplied:

```bash
uv run cp-validate \
  examples/valid_well_level.h5ad \
  --profile-level well \
  --report validation-report.json \
  --force
```

### Validate the deliberately invalid example

The repository includes an intentionally invalid dataset for demonstrating
structured validation failures:

```bash
uv run cp-validate \
  examples/invalid_example.h5ad \
  --schema generic-cell-painting \
  --profile-level single-cell \
  --strict
```

Expected result:

```text
Status: FAIL
```

The command is expected to exit with code `1`. This means validation completed
successfully and found dataset problems; it does not mean that the validator
crashed.

You may also see an AnnData warning stating that observation names are not
unique. The validator reports the same condition as the structured `INDEX001`
finding.

The example intentionally demonstrates problems including:

- missing plate and cell identifiers;
- duplicate observation identifiers;
- unresolved single-cell profile requirements;
- missing control annotations;
- invalid feature-name conventions;
- a non-finite matrix value;
- missing licence, schema and processing-stage metadata;
- missing image, segmentation and feature-extraction provenance.

## Python quickstart

The following block is Python code. Do not paste it directly into `zsh` or
another shell.

Save it as `validate_example.py`:

```python
from cp_anndata_validator import validate

report = validate(
    "examples/valid_well_level.h5ad",
    profile_level="well",
)

print(report.status)

for issue in report.issues:
    print(
        issue.code,
        issue.severity.value,
        issue.message,
    )
```

Run it with:

```bash
uv run python validate_example.py
```

You can also run the example directly from the shell without creating a file:

```bash
uv run python - <<'PY'
from cp_anndata_validator import validate

report = validate(
    "examples/valid_well_level.h5ad",
    profile_level="well",
)

print(report.status)

for issue in report.issues:
    print(
        issue.code,
        issue.severity.value,
        issue.message,
    )
PY
```

## Normal and strict validation

| Mode | Do warnings fail validation? | Typical use |
|---|---:|---|
| Normal | No | Exploration, development and inspection of pipeline exports |
| `--strict` / `strict=True` | Yes | Publishing gates, governed workflows and CI enforcement |

Run strict validation against the generated valid example:

```bash
uv run cp-validate \
  examples/valid_well_level.h5ad \
  --schema generic-cell-painting \
  --profile-level well \
  --strict
```

This valid example should pass in both normal and strict modes.

Do not copy placeholder paths such as `experiment.h5ad` unless you have a file
with that name. Replace paths in examples with the actual location of the
AnnData file you want to validate.

## Exit codes

| Exit code | Meaning |
|---:|---|
| `0` | Validation completed and passed |
| `1` | Validation completed and found failures |
| `2` | Validation could not be executed |

Exit code `1` represents a completed validation run whose result was `FAIL`.
It is distinct from an internal execution failure.

See the
[CLI reference](https://ronfinn.github.io/cell-painting-anndata-validator/reference/cli/)
for all commands and options.

## Built-in schemas

| Schema | Version | Purpose |
|---|---:|---|
| `generic-cell-painting` | `0.2.1` | Vendor-neutral Cell Painting AnnData expectations |
| `jump-cp` | `0.2.1` | JUMP-oriented metadata and alias compatibility preset |

List the installed schemas:

```bash
uv run cp-validate schema list
```

Inspect a built-in schema:

```bash
uv run cp-validate schema show generic-cell-painting
```

```bash
uv run cp-validate schema show jump-cp
```

Custom YAML schemas can also be supplied:

```bash
uv run cp-validate \
  examples/valid_well_level.h5ad \
  --schema path/to/custom-schema.yaml \
  --profile-level well
```

Unknown schema keys are rejected rather than silently ignored.

See:

- [Schemas and checks](https://ronfinn.github.io/cell-painting-anndata-validator/schemas/)
- [Rule catalogue](https://ronfinn.github.io/cell-painting-anndata-validator/schemas/rule-catalogue/)

## Profile levels

The validator supports three profile levels:

| Profile level | One observation represents | Typical identifiers |
|---|---|---|
| `single-cell` | One segmented cell or object | Plate, well, site and cell/object identifier |
| `well` | One aggregated plate-well profile | Plate and well identifier |
| `treatment` | One aggregated perturbation profile | Perturbation identifier and aggregation provenance |

The profile level can be detected automatically:

```bash
uv run cp-validate examples/valid_well_level.h5ad
```

It can also be declared explicitly:

```bash
uv run cp-validate \
  examples/valid_well_level.h5ad \
  --profile-level well
```

Automatic detection may return an ambiguous result instead of guessing.
Use `--profile-level` or the Python `profile_level=` argument to resolve the
ambiguity.

## AnnData mapping

The validator interprets the main AnnData elements as follows:

| AnnData element | Expected content |
|---|---|
| `.X` | Primary numeric Cell Painting feature matrix |
| `.obs` | Profile identifiers, controls, treatments, batch and source metadata |
| `.var` | Feature-level metadata and feature names |
| `.uns` | Schema, licence, processing stage, experiment and provenance metadata |
| `.obsm` | Observation-aligned arrays such as embeddings |
| `.varm` | Feature-aligned arrays |
| `.layers` | Alternative feature matrices or processing stages |

The validator does not require every dataset to use one exact column name.
Canonical semantic fields are resolved through schema-defined aliases.

## Package names

| Role | Name |
|---|---|
| Python distribution | `cp-anndata-validator` |
| Python import package | `cp_anndata_validator` |
| Command-line interface | `cp-validate` |
| GitHub repository | [`ronfinn/cell-painting-anndata-validator`](https://github.com/ronfinn/cell-painting-anndata-validator) |

## Public-data validation

The validator has been exercised against genuine well-level profiles from the
public Cell Painting Gallery. Dataset binaries and generated `.h5ad` files were
not committed to this repository.

| Dataset | Plate | Shape | Schema | Result |
|---|---|---:|---|---|
| LINCS `cpg0004-lincs` | `SQ00014812` | 384 × 493 | `generic-cell-painting` | Passed normal validation |
| JUMP pilot `cpg0000-jump-pilot` | `BR00116991` | 384 × 838 | `jump-cp` | Passed normal validation |

For both pilots:

- the profile level was correctly detected as `well`;
- normal validation returned exit code `0`;
- strict validation failed only on expected governance warnings;
- in-memory and backed validation produced the same rule-code set;
- no `ENGINE001` internal execution error was reported;
- no broad feature-family false positives were observed.

See the
[public-data pilot documentation](https://ronfinn.github.io/cell-painting-anndata-validator/pilots/)
for methodology, conversion boundaries and detailed findings.

## Documentation

| Topic | Documentation |
|---|---|
| Full documentation | [Documentation home](https://ronfinn.github.io/cell-painting-anndata-validator/) |
| Installation and first validation | [Getting started](https://ronfinn.github.io/cell-painting-anndata-validator/getting-started/) |
| Five-minute introduction | [Quickstart](https://ronfinn.github.io/cell-painting-anndata-validator/getting-started/quickstart/) |
| Complete workflows | [Tutorials](https://ronfinn.github.io/cell-painting-anndata-validator/tutorials/) |
| Task-oriented guidance | [How-to guides](https://ronfinn.github.io/cell-painting-anndata-validator/how-to/) |
| AnnData mapping and profile levels | [Concepts](https://ronfinn.github.io/cell-painting-anndata-validator/concepts/) |
| Schemas and validation checks | [Schemas and checks](https://ronfinn.github.io/cell-painting-anndata-validator/schemas/) |
| CLI commands and options | [CLI reference](https://ronfinn.github.io/cell-painting-anndata-validator/reference/cli/) |
| Python interface | [Python API](https://ronfinn.github.io/cell-painting-anndata-validator/reference/python-api/) |
| Public LINCS and JUMP pilots | [Public-data pilots](https://ronfinn.github.io/cell-painting-anndata-validator/pilots/) |
| Known constraints | [Limitations](https://ronfinn.github.io/cell-painting-anndata-validator/project/limitations/) |
| Planned development | [Roadmap](https://ronfinn.github.io/cell-painting-anndata-validator/project/roadmap/) |
| Release history | [Changelog](CHANGELOG.md) |

Build and serve the documentation locally:

```bash
uv run mkdocs serve
```

The local documentation site will be available at:

```text
http://127.0.0.1:8000/
```

Run the strict documentation build used by CI:

```bash
uv run mkdocs build --strict
```

## Development

Set up all dependency groups:

```bash
uv sync --all-groups
```

Run the test suite:

```bash
uv run pytest
```

Run linting and formatting checks:

```bash
uv run ruff check .
uv run ruff format --check .
```

Run static type checking:

```bash
uv run mypy src
```

Build the documentation:

```bash
uv run mkdocs build --strict
```

Build the source distribution and wheel:

```bash
uv build
```

Test the built wheel in an isolated environment:

```bash
bash scripts/smoke_wheel.sh
```

The complete local release check is:

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

## Contributing

Contributions, schema discussions and public evidence for metadata aliases are
welcome.

Before contributing, read:

- [Contributing guidelines](CONTRIBUTING.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Support policy](SUPPORT.md)
- [Security policy](SECURITY.md)

Please do not commit:

- private, proprietary or sensitive datasets;
- downloaded Cell Painting Gallery payloads;
- generated `.h5ad` files;
- generated validation reports;
- credentials, tokens or local configuration.

Prefer synthetic fixtures or publicly redistributable metadata examples.

Use:

- [Discussions](https://github.com/ronfinn/cell-painting-anndata-validator/discussions)
  for questions, ideas and design conversations;
- [Issues](https://github.com/ronfinn/cell-painting-anndata-validator/issues/new/choose)
  for reproducible defects, documentation problems and evidence-supported
  schema requests;
- [GitHub Security Advisories](https://github.com/ronfinn/cell-painting-anndata-validator/security/advisories/new)
  for suspected security vulnerabilities.

## Licence

Cell Painting AnnData Validator is released under the
[Apache License 2.0](LICENSE).

## Citation

When using this project, cite it using the metadata in
[CITATION.cff](CITATION.cff).
