# Changelog

All notable changes to `cp-anndata-validator` are documented here. Format
follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/); versioning
follows [Semantic Versioning](https://semver.org/).

## [Unreleased]

Initial v0.1 line. Nothing has been tagged or published to PyPI yet — see
[`docs/limitations.md`](docs/limitations.md).

### Added

- **Public API and CLI.** `cp_anndata_validator.validate()` and the
  `cp-validate` console script, both wired to the same validation engine.
  Supports `--schema`, `--profile-level`, `--report {json,html}`,
  `--strict`, `--backed`/`--no-backed`, `--sample-rows`, `--quiet`,
  `--force`, and `schema list`/`schema show`.
- **Structured results.** Typed, frozen `Issue` and `Report` Pydantic
  models with stable rule codes, severities (`error`/`warning`/
  `information`), categories, AnnData locations, evidence, and remediation.
- **Versioned, data-driven schemas.** YAML schema loader with strict
  validation (semver `schema_version`, no unknown keys, no ambiguous
  aliases). Ships `generic-cell-painting` and `jump-cp` (a *compatibility
  preset* based on public JUMP conventions — not an official JUMP standard;
  see `docs/jump-cp-derivation.md`) at schema version `0.1.0`.
- **Explainable profile-level detection.** Auto-detects `single-cell`/
  `well`/`treatment` granularity from column presence and row cardinality,
  with an explicit `--profile-level` override and a human-readable
  explanation for every decision, including ambiguous outcomes.
- **30+ built-in checks** emitting **45+ permanent, stable rule codes**
  across **15 categories** — structure, index uniqueness, identifier
  completeness, profile consistency, control annotations, feature
  names/compartments/measurement families, matrix/slot semantics, batch/
  source/experiment metadata, image/segmentation/feature-extraction
  provenance, schema/licence declarations, aggregation provenance, and
  basic AI-readiness. Counts as of this release; a check can emit more
  than one rule code — see `docs/checks.md` for the full, current
  catalogue.
- **Sparse- and backed-safe execution.** Numeric checks never densify a
  full sparse matrix; large/backed files are validated via bounded,
  deterministic row sampling (`--sample-rows`, default 5000).
- **Three renderers**, independent of validation logic: a Rich console
  summary, deterministic JSON, and self-contained, escaped HTML.
- **Runnable examples.** `examples/generate_examples.py` generates a clean
  single-cell dataset, a clean well-level dataset, and a dataset with
  several deliberate, documented failures — see `examples/README.md`.
- **Documentation set** under `docs/`: CLI reference, Python API, schema
  format, AnnData slot mapping, profile-level detection, rule-code
  catalogue, `jump-cp` provenance, limitations, and contributing guide.
- **CI**: lint (`ruff check`), format check (`ruff format --check`),
  type-check (`mypy --strict`), tests with coverage, `uv build`, and an
  end-to-end smoke test against the generated examples, on every supported
  Python version (3.12-3.14).
- Licensed under Apache-2.0 (see `README.md` for why).
