# Changelog

All notable changes to `cp-anndata-validator` are documented here. Format
follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/); versioning
follows [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.2.0b1] - 2026-07-26

First public beta. Package version `0.2.0b1` is independent of the built-in
schema versions (`schema_version: "0.2.1"` for both built-ins after
batch-alias calibration).

### Added

- **MkDocs Material documentation site** with Diátaxis-style navigation,
  mkdocstrings API pages, ADRs, and GitHub Pages deploy workflow. Published
  at https://ronfinn.github.io/cell-painting-anndata-validator/.
- **Professional repository presentation.** Concise README landing page,
  `project.urls`, community-health files (issue forms, PR template, Code of
  Conduct, Security, Support), and typed-package marker (`py.typed`).
- **Public-data pilot documentation.** `docs/pilots/` records genuine Cell
  Painting Gallery pilots for LINCS (`cpg0004-lincs`) and JUMP
  (`cpg0000-jump-pilot`): Zenodo LFS pitfall, CPG prefixes, truthful conversion
  mapping, JUMP `*_feature_select_batch*` naming, and expected governance
  warnings.
- **Realistic Cell Painting fixtures and baseline tests.** Programmatic
  CellProfiler/CytoTable single-cell, pycytominer well, and JUMP treatment
  builders (`tests/fixtures/realistic.py`) with pinned bare-pipeline issue
  baselines (`tests/test_realistic_baselines.py`).
- **Container and loading-mode parity.** End-to-end tests asserting identical
  issue-code sets across dense / CSR / CSC × in-memory / backed for the same
  logical dataset (`tests/test_realistic_parity.py`).
- **`cp-validate --version`.** Prints the installed package version and exits
  0.
- **`IDENT000` documentation and coverage.** Documents the custom-schema
  fallback rule code and tests that it is emitted when a custom schema
  requires an additional identifier field.
- **False-positive documentation.** `docs/how-to/false-positives.md` records,
  for every validation category, whether real pipeline output can trigger it
  and whether that is governance signalling or a likely false positive.
- **Release smoke coverage.** Package/schema version assertions and an
  isolated-wheel smoke script (`scripts/smoke_wheel.sh`).

### Changed

- **Built-in schemas → `0.2.1`.** Both `generic-cell-painting` and `jump-cp`
  accept `Metadata_Batch_Number` as a `batch` alias (LINCS-style), appended
  after existing aliases so first-alias-wins precedence is preserved.
- **`Metadata_pert_type` semantics documented.** Remains a `control_type`
  alias only; not mapped to `perturbation_modality`. `IDENT007` unchanged.

### Validated

- Real LINCS Level 4b well profile (`SQ00014812`, 384 × 493) from
  `s3://cellpainting-gallery/cpg0004-lincs/broad/workspace/` validates with
  normal exit 0, strict exit 1 (warnings only), correct well auto-detection,
  and in-memory/`--backed` parity. No `ENGINE001`; no feature-family false
  positives on that plate.
- Real JUMP pilot well profile (`BR00116991`, 384 × 838) from
  `s3://cellpainting-gallery/cpg0000-jump-pilot/` validates under `jump-cp`
  0.2.1 with the same pass/strict/backed/auto-detect pattern; identical issue
  set under `generic-cell-painting`. No release-blocking defects.

### Fixed

- **String `profile_level` in the public API.** `validate(..., profile_level="well")`
  is coerced to `ProfileLevel` before checks run; unsupported values raise
  `ValueError` immediately instead of producing `ENGINE001`.
- **Defensive profile-level formatting.** Checks and the console renderer no
  longer crash if an accidentally unvalidated `model_copy` leaves a raw
  string on `ProfileLevelResult`.

### Also in this beta (schema vocabulary from the `0.2.0` cut)

- Built-in schemas first advanced to `0.2.0` with expanded measurement
  families (`ObjectSkeleton`, `Math`, `Overlap`, `SizeShape`,
  `AreaOccupied`, `ImageQuality`), JUMP `perturbation_id` alias precedence,
  and case-insensitive `poscon_` / `negcon_` control-label prefixes.
- **`AGG001` warning policy.** Missing aggregation provenance on well- or
  treatment-level data still emits `AGG001`, but as a **warning**. Normal
  validation does not fail for `AGG001` alone; `--strict` does. Incomplete
  aggregation blocks still emit `AGG002` / `AGG003`. `IDENT006` remains an
  error when treatment rows cannot be traced.
- Remaining pilot findings were expected governance or source-metadata
  warnings (for example `AGG001`, `IDENT007`, licence/schema/provenance
  gaps, and missing batch/source columns on the JUMP profile table).

### Known limitations

- **`FEAT001` on embedding-style feature names.** DeepProfiler-style names
  such as `efficientnet_0` have no CellProfiler compartment prefix, so
  `FEAT001` still warns on every such feature. Changing that behaviour is
  deferred.
- **Sampled numeric checks.** Non-finite / AI-readiness checks on large or
  backed matrices use bounded row sampling (`--sample-rows`, default 5000),
  not an exhaustive scan of every value.
- **No Zarr support.** Only `.h5ad` input is accepted.
- **No automatic repair.** The validator never modifies, converts, or
  "fixes" the input AnnData file.
- **Synthetic fixtures are not a substitute for external validation.** The
  realistic builders model public pipeline conventions; they do not replace
  testing against real laboratory or consortium datasets.

## [0.1.0a1] - 2026-07-19

Initial public alpha release.

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
