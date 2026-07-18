# cp-anndata-validator

A Python package and CLI that validates the semantic correctness, metadata
completeness, provenance, and AI-readiness of **Cell Painting datasets
stored as [AnnData](https://anndata.readthedocs.io/)** (`.h5ad`) objects.

`cp-anndata-validator` is read-only: it never converts other formats into
AnnData and never mutates the file it validates.

[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

<!-- Add a CI badge here once this repository has a GitHub remote, e.g.:
[![CI](https://github.com/<org>/<repo>/actions/workflows/ci.yml/badge.svg)](https://github.com/<org>/<repo>/actions/workflows/ci.yml) -->

## Problem statement

Cell Painting pipelines (CellProfiler/DeepProfiler → CytoTable → AnnData)
produce files that are almost always *structurally* valid — they open fine,
they have a matrix, they have an index — while still being unusable for
downstream analysis or model training for reasons no file format can catch
on its own:

- Plate/well/site/cell identifiers are missing, inconsistent, or ambiguous
  across a merged multi-batch dataset.
- Control annotations are absent or use unrecognized labels, silently
  breaking normalization and QC.
- Segmentation, feature-extraction, and image-acquisition provenance was
  never recorded, so results can't be reproduced or audited.
- It's unclear whether a dataset is single-cell, well-aggregated, or
  treatment-aggregated, and whether `.X` holds raw, normalized, or
  aggregated values.
- Feature columns are constant, mostly missing, or non-finite in ways that
  silently degrade a downstream model, and nobody notices until training
  fails or produces garbage.

These are exactly the kind of silent, structurally-invisible problems that
turn into wasted compute, retracted results, or a frustrating multi-hour
debugging session three pipeline stages downstream. `cp-anndata-validator`
turns them into an explicit, structured, actionable report *before* that
happens — as a five-second CI gate, not a manual audit.

## How this complements CytoTable

[CytoTable](https://github.com/cytomining/CytoTable) is a data-harmonization
and serialization tool: it takes image-based profiling outputs — CellProfiler
(`.csv`/`.sqlite`), cytominer-database (`.sqlite`), DeepProfiler (`.npz`), or
other sources such as IN Carta — and writes them into analysis-ready Parquet
or AnnData files, typically for use with [Pycytominer](https://github.com/cytomining/pycytominer)
or other downstream tooling.

`cp-anndata-validator` picks up *after* that step: it validates an AnnData
object that already exists — including, but not limited to, one CytoTable
produced — for semantic correctness, metadata completeness, provenance, and
AI-readiness. It is read-only and never writes, converts, or "fixes" a file;
it returns a structured, renderable report (`Issue`/`Report` objects;
console/JSON/HTML) instead.

The two tools address different, complementary problems and are meant to be
used together, not as alternatives: CytoTable answers "can I get this data
into AnnData?"; `cp-anndata-validator` answers "is this AnnData file actually
trustworthy and complete enough to build on?" A CytoTable-produced file can
be perfectly well-formed AnnData and still fail several
`cp-anndata-validator` checks — for example, if provenance metadata wasn't
carried through the conversion, or a control-annotation column uses an
unrecognized label — which is exactly the gap this package exists to close.

## Install

```bash
uv add cp-anndata-validator
# or
pip install cp-anndata-validator
```

(Not yet published to PyPI — see [Limitations](#limitations). Until then,
install from a local clone: `uv sync` then `uv run cp-validate ...`, or
`uv build && pip install dist/cp_anndata_validator-*.whl`.)

## Five-minute quick start

```bash
# 1. Get a real dataset, or generate three small synthetic ones to try
#    right now (valid single-cell, valid well-level, and a deliberately
#    broken example) -- see examples/README.md for what's in each.
uv run python examples/generate_examples.py

# 2. Validate one. Profile level and schema auto-detect by default.
uv run cp-validate examples/valid_single_cell.h5ad
# cp-anndata-validator v0.1.0
# ...
# No issues found.
# Status: PASS   (exit code 0)

# 3. Try the broken one -- several independent, understandable problems at once.
uv run cp-validate examples/invalid_example.h5ad --profile-level single-cell
# ... a table of IDENT001/INDEX001/CTRL001/LICENSE001/... issues ...
# Status: FAIL   (exit code 1)

# 4. Get a shareable, self-contained HTML report (safe to open, escapes
#    all dataset-derived content), or a deterministic JSON report for CI.
uv run cp-validate examples/invalid_example.h5ad --profile-level single-cell \
    --report report.html
uv run cp-validate examples/valid_single_cell.h5ad --report report.json

# 5. Point it at your own dataset. If it's JUMP-style, use the compatibility preset.
uv run cp-validate your_experiment.h5ad --schema jump-cp
```

Or, from Python:

```python
from cp_anndata_validator import validate

report = validate("examples/valid_single_cell.h5ad")
print(report.status)          # "pass" or "fail"
print(len(report.issues))     # 0
```

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
- **30+ built-in checks** emitting **45+ permanent, stable rule codes**
  across **15 categories** — structure, identifiers, profile consistency,
  annotations, features, matrix/slot semantics, metadata, provenance,
  schema/licence declarations, aggregation, and AI-readiness. Counts as of
  this release; see [`docs/checks.md`](docs/checks.md) for the current,
  definitive catalogue (a check can emit more than one rule code).

## AnnData mapping

`cp-anndata-validator` interprets AnnData slots as follows (never writing
to any of them — see [`docs/anndata-mapping.md`](docs/anndata-mapping.md)
for the complete table and suggested `uns` metadata shapes):

| Slot | Expected content |
|---|---|
| `.X` | The primary feature matrix: one row per observation, one column per feature; numeric; sparse or dense; shape must equal `(n_obs, n_vars)`. |
| `.obs` | Identifier columns (plate/well/site/cell/perturbation/modality) and annotations (control type, batch, source), matched via schema aliases, not fixed names. |
| `.var` | One row per feature; names expected to be `<compartment>_<measurement family>_...` (for example `Cells_AreaShape_Area`). |
| `.uns` | Dataset-level metadata: `schema_id`/`schema_version`, `processing_stage`, `licence`, `experiment`, `image_provenance`, `segmentation_provenance`, `feature_extraction_provenance`, `aggregation` (well/treatment profiles). |
| `.obsm` / `.varm` | Per-observation/per-feature arrays; first dimension must match `n_obs`/`n_vars`. |
| `.layers` | Alternative matrices; shape must match `.X`, and each layer should declare its own processing stage. |

## Profile levels

Cell Painting AnnData objects are commonly stored at one of three
granularities (full detection algorithm in
[`docs/profile-levels.md`](docs/profile-levels.md)):

| Level | One row per... | Typically requires |
|---|---|---|
| `single-cell` | segmented cell/object | plate, well, site, cell/object identifier |
| `well` | plate + well | plate, well identifier |
| `treatment` | perturbation | perturbation identifier, aggregation provenance |

You can declare it explicitly (`--profile-level well`) or let
`cp-anndata-validator` auto-detect it from column presence and row
cardinality; detection can legitimately come back **ambiguous**
(`PROFILE002`) rather than silently guessing, and always reports *why* a
level was or wasn't chosen.

## Supported checks and rule codes

**30+ checks** across **15 categories**: structure/index-uniqueness,
identifiers, profile consistency, annotations, features, matrix/slot
semantics, metadata, image/segmentation/feature-extraction provenance,
schema/licence declarations, aggregation, and AI-readiness. Every check
emits one or more permanent, stable rule codes (`IDENT001`, `MATRIX002`,
`AGG003`, ...) — **45+ codes** are currently defined. See the complete,
current catalogue with exact severities, meanings, and remediation text in
[`docs/checks.md`](docs/checks.md) — that page, not this README, is the
definitive source for exact counts as checks are added over time. A few
representative examples:

| Code | Severity | Meaning |
|---|---|---|
| `IDENT001`-`IDENT005` | error | A canonical identifier field (plate/well/site/cell_id/perturbation_id) required by the effective profile level didn't resolve. |
| `PROFILE002` | information | Profile-level auto-detection was ambiguous; pass `--profile-level` to disambiguate. |
| `MATRIX002` | warning | `.X` contains non-finite values (checked without densifying). |
| `CTRL003` | warning | No negative control (`negcon`) annotation was found. |
| `AGG001`/`AGG003` | error/warning | Aggregation method / source profile level not declared for a well- or treatment-level profile. |
| `ENGINE001` | error | A check raised unexpectedly; the run continues, isolated to this one issue. |

## Schemas

A schema is a versioned, data-driven YAML document mapping canonical
semantic fields (`plate`, `well`, `perturbation_id`, ...) to column-name
aliases, per-profile-level requirements, and expected feature-name
compartments/measurement families. Full format in
[`docs/schemas.md`](docs/schemas.md).

- **`generic-cell-painting`** (v0.1.0) — vendor-neutral; doesn't assume any
  single upstream pipeline's exact column spelling.
- **`jump-cp`** (v0.1.0) — a **compatibility preset based on public [JUMP
  Cell Painting Consortium](https://jump-cellpainting.broadinstitute.org/)
  metadata conventions** (`Metadata_Plate`, `Metadata_JCP2022`, ...) and
  [`pycytominer`](https://github.com/cytomining/pycytominer) feature-naming
  conventions. **It is not an official JUMP-endorsed AnnData schema** — see
  [`docs/jump-cp-derivation.md`](docs/jump-cp-derivation.md) for exactly
  which public sources it was derived from and what wasn't carried over.

Bring your own schema with `--schema ./my-lab-schema.yaml` — no code
changes required.

```bash
cp-validate schema list
cp-validate schema show jump-cp
```

## Python API

```python
from cp_anndata_validator import validate, ProfileLevel

report = validate(
    "experiment.h5ad",
    schema="jump-cp",                        # or "generic-cell-painting", or a path
    profile_level=ProfileLevel.SINGLE_CELL,   # or None to auto-detect
    strict=False,                             # True: warnings also fail
)

print(report.status)                 # "pass" or "fail"
print(report.counts.by_severity)     # {Severity.ERROR: 2, Severity.WARNING: 1}
for issue in report.issues:
    print(issue.code, issue.severity, issue.location, issue.message)
```

```python
from cp_anndata_validator.reporting import render_console, render_html, render_json

print(render_console(report))
open("report.html", "w").write(render_html(report))   # self-contained, escaped
open("report.json", "w").write(render_json(report))   # deterministic
```

Raises `LoadError` (unreadable/corrupt file) or `SchemaError` (bad schema)
before any checks run. Full reference, including running individual checks
directly: [`docs/python-api.md`](docs/python-api.md).

## CLI examples

```bash
cp-validate experiment.h5ad
cp-validate experiment.h5ad --schema jump-cp
cp-validate experiment.h5ad --profile-level single-cell
cp-validate experiment.h5ad --report report.html      # self-contained, escaped HTML
cp-validate experiment.h5ad --report report.json      # deterministic JSON
cp-validate experiment.h5ad --strict                  # warnings also fail
cp-validate experiment.h5ad --report report.json --force   # allow overwrite
cp-validate schema list
cp-validate schema show jump-cp
```

Exit codes: `0` no errors found, `1` validation errors found (or, under
`--strict`, warnings found), `2` the validator couldn't run at all (bad
file, bad schema, bad arguments, or an unexpected execution failure — no
report is produced). Full flag reference:
[`docs/cli.md`](docs/cli.md).

## Limitations

v0.1 deliberately defers some things — see
[`docs/limitations.md`](docs/limitations.md) for full detail. Headlines:

- Numeric checks on very large **backed** datasets are statistical (bounded
  row sampling), not exhaustive, by design — never full-matrix.
- Schema alias matching is exact (case-/whitespace-insensitive), not fuzzy;
  no typo tolerance.
- `.uns` metadata blocks are checked for presence and plausible shape, not
  validated against an exhaustive nested schema.
- No custom-schema authoring wizard yet — hand-write the YAML.
- Not yet published to PyPI (installable locally via `uv build`).

## Architecture

Eight conceptual layers, each independently testable:

```
1. AnnData loading & safe inspection    loading.py, sampling.py, profiles.py
2. Versioned schema definitions         schema/  (models, loader, alias resolution)
3. Independent validation checks        checks/  (one module per category)
4. Validation orchestration             orchestrator.py
5. Structured issue & report models     models/  (Issue, Report, ...)
6. Console/JSON/HTML renderers          reporting/  (pure functions, no validation logic)
7. Typer CLI                            cli/  (delegates to api.py + reporting/)
8. Public Python API                    api.py  (validate() -- the one integration point)
```

Checks never print or raise for expected validation failures — they return
`list[Issue]`; the orchestrator isolates a check's unexpected exception
into a single `ENGINE001` issue rather than crashing the whole run. Full
layout and how to add a check/schema:
[`docs/contributing.md`](docs/contributing.md).

## Roadmap

Beyond v0.1 (not committed to a timeline; see
[`docs/limitations.md`](docs/limitations.md) for the authoritative current
gaps):

- Publish to PyPI.
- Fuzzy/typo-tolerant alias matching, with a confidence score surfaced on
  the resolved field.
- An interactive schema-authoring helper (suggest aliases from an existing
  `.obs`/`.var`).
- Deeper `.uns` provenance-block schema validation (beyond presence/shape).
- Additional built-in schemas for other common Cell Painting conventions,
  each with its own derivation doc (see `docs/jump-cp-derivation.md` as the
  template).
- Optional parallel check execution for very wide/backed datasets.

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for ground rules and PR
expectations, and [`docs/contributing.md`](docs/contributing.md) for the
detailed dev workflow, repository layout, and step-by-step instructions for
adding a check or schema. Quick version:

```bash
uv sync
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv build
```

## Documentation

Full set in [`docs/`](docs/index.md): [CLI reference](docs/cli.md),
[Python API](docs/python-api.md), [schema format](docs/schemas.md),
[rule-code catalogue](docs/checks.md),
[profile-level detection](docs/profile-levels.md),
[AnnData mapping](docs/anndata-mapping.md),
[`jump-cp` provenance](docs/jump-cp-derivation.md), and
[known limitations](docs/limitations.md).

## License

Apache License 2.0 — see [`LICENSE`](LICENSE).

We chose Apache-2.0 over BSD-3-Clause for its explicit patent grant and
termination clause (§3), which matters more for a validation tool likely to
be embedded in institutional/pharma CI pipelines than for a typical small
library: it gives downstream users of the check engine an explicit,
reciprocal patent license from every contributor, reducing legal ambiguity
for organizations that would otherwise need to review that risk themselves
before adopting it. Both licenses are permissive and OSI-approved; either
would have been a reasonable choice for a project with no strong copyleft
requirement.
