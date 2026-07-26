# Cell Painting AnnData Validator

Validate the semantic correctness, metadata completeness, provenance and
basic AI readiness of Cell Painting datasets that are already stored as
[AnnData](https://anndata.readthedocs.io/) (`.h5ad`) objects.

!!! warning "Beta status"
    Package version **`0.2.0b1`**. Built-in schemas
    (`generic-cell-painting`, `jump-cp`) are at **`0.2.1`**. APIs and rule
    codes are intended to be stable within this beta line, but the project
    may still calibrate schemas and documentation before a final `0.2.0`.

## What this package does

- Reads an existing `.h5ad` file (in-memory or backed)
- Resolves canonical fields via versioned YAML schemas and declared aliases
- Detects or accepts a profile level (`single-cell`, `well`, `treatment`)
- Runs independent checks that return structured issues
- Renders console, JSON and HTML reports

## What it does not do

- Convert CellProfiler, DeepProfiler, CytoTable or CSV profiles into AnnData
- Mutate or “fix” the input file
- Judge biological suitability, assay quality or scientific correctness of
  a phenotype

## Quick links

| | |
|---|---|
| Install | [Getting started → Installation](getting-started/installation.md) |
| Five-minute path | [Quickstart](getting-started/quickstart.md) |
| CLI | [CLI reference](reference/cli.md) |
| Python | [Python API](reference/python-api.md) |
| Rules | [Rule catalogue](schemas/rule-catalogue.md) |
| Pilots | [Public-data pilots](pilots/index.md) |
| Source | [GitHub repository](https://github.com/ronfinn/cell-painting-anndata-validator) |
