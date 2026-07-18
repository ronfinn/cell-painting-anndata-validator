# cp-anndata-validator engineering instructions

## Product objective

Build a production-quality, open-source Python package and CLI for validating the semantic correctness, metadata completeness, provenance and AI readiness of Cell Painting datasets represented as AnnData objects.

The package validates AnnData. It does not convert CellProfiler, DeepProfiler or other source formats into AnnData.

## Development workflow

* Use `uv` for environments, dependencies, commands and builds.
* Use a `src/` package layout.
* Use Python 3.11 or newer.
* Use type annotations throughout the public API.
* Use small, cohesive modules with clear responsibilities.
* Prefer dependency injection and explicit configuration over global state.
* Do not introduce dependencies without explaining why they are necessary.
* Do not rewrite unrelated files.
* Before making substantial changes, explain the files that will be changed.
* Implement one independently testable milestone at a time.
* Run the complete quality suite after every milestone.
* Never claim tests pass unless the commands were actually executed successfully.

## Required quality commands

Run these before considering a task complete:

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv build
```

## Architecture

Use these conceptual layers:

1. AnnData loading and safe inspection.
2. Versioned schema definitions.
3. Independent validation checks.
4. Validation orchestration.
5. Structured issue and report models.
6. Console, JSON and HTML renderers.
7. Typer CLI.
8. Public Python API.

Validation checks must not print directly. They return structured results.

## Validation result model

Every issue must contain:

* stable rule code
* severity: error, warning or information
* category
* AnnData location such as `obs.plate_id`, `var.index` or `uns.provenance`
* concise message
* supporting evidence where safe and useful
* actionable remediation
* check name

A report must contain:

* package version
* selected schema and schema version
* input file information
* detected or declared profile level
* execution timestamp
* pass/fail status
* issue counts by severity and category
* ordered issues
* checks executed and checks skipped

## Schema principles

* Schemas must be versioned and data-driven.
* Built-in schemas must be stored as package resources, preferably YAML.
* Support canonical semantic fields with aliases rather than requiring one exact column spelling.
* Initially implement `generic-cell-painting` and `jump-cp`.
* Describe `jump-cp` as a compatibility preset based on public JUMP metadata conventions, not as an official JUMP AnnData standard.
* Make it possible to add custom schemas later without editing validation engine code.
* Reject unknown schema keys rather than silently ignoring configuration mistakes.

## Profile levels

Support:

* `single-cell`
* `well`
* `treatment`

Requirements vary by profile level.

Single-cell profiles normally require plate, well, site and cell or object identifiers.

Well-level profiles normally require plate and well identifiers, but not cell identifiers.

Treatment-level profiles require a perturbation identifier, aggregation provenance and information describing how the treatment profile was derived.

Auto-detection must be explainable and may return an ambiguous result. A CLI override must always be available.

## AnnData semantics

* Treat `.X` as the declared primary feature matrix.
* Treat `.obs` as profile-level identifiers and annotations.
* Treat `.var` as feature-level metadata.
* Treat `.uns` as schema, licence, provenance and experiment metadata.
* Treat `.obsm` as observation-aligned multidimensional data such as embeddings or coordinates.
* Treat `.layers` as alternative matrices whose shapes must match `.X`.
* Do not assume raw or normalised data must always occupy one fixed slot; require the processing stage to be declared.
* Never densify a sparse matrix merely to validate it.
* Do not read a complete large matrix when metadata or bounded sampling is sufficient.
* Ensure backed and sparse AnnData objects fail gracefully even if full support is deferred.

## Initial validation categories

* file readability and AnnData structure
* observation and feature index uniqueness
* missing and duplicate observations
* identifier completeness
* profile-level consistency
* control and treatment annotations
* feature names and compartments
* matrix shape and numeric validity
* slot semantics
* batch, plate and experiment metadata
* image provenance
* segmentation provenance
* feature-extraction provenance
* schema identifier and version
* dataset licence
* aggregation provenance
* basic AI-readiness checks

## CLI requirements

Expose the command:

```bash
cp-validate DATASET
```

Support at least:

```bash
cp-validate experiment.h5ad
cp-validate experiment.h5ad --schema jump-cp
cp-validate experiment.h5ad --profile-level single-cell
cp-validate experiment.h5ad --report report.html
cp-validate experiment.h5ad --report report.json
cp-validate schema list
cp-validate schema show jump-cp
```

Use these exit codes:

* `0`: validation completed with no errors
* `1`: validation completed and validation errors were found
* `2`: the validator could not execute because of an invalid file, configuration or runtime failure

Warnings alone must not produce exit code 1 unless strict mode is selected.

## Testing

* Generate small synthetic AnnData fixtures programmatically.
* Do not commit large binary fixtures.
* Include valid and deliberately invalid examples.
* Test individual checks separately from orchestration and presentation.
* Test CLI exit codes with Typer's test runner.
* Test dense and sparse matrices.
* Test malformed schema files.
* Test deterministic report ordering.
* Ensure tests do not rely on network access.
* Add regression tests for every fixed defect.

## Security and privacy

* Never send dataset contents to external services.
* Reports must avoid dumping large or sensitive metadata values.
* Escape all user-controlled values in HTML reports.
* Treat file paths and schema files as untrusted input.
* Do not execute code contained in configuration files.
* Do not overwrite an existing report unless explicitly permitted.

## Documentation

Document:

* supported checks
* rule codes
* schema design
* AnnData mapping
* profile-level definitions
* CLI examples
* Python API examples
* limitations
* contribution instructions
* how the JUMP compatibility preset was derived

Keep scientific claims precise and cite primary public sources in the documentation.
