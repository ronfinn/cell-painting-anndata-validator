# Limitations (v0.2)

This page documents known gaps deliberately deferred out of current scope, so
users and contributors don't mistake them for bugs. Package version
(`0.2.0b1`) and built-in schema versions (`0.2.0`) are independent.

## Backed-mode coverage is a documented subset, not complete

- Structural and metadata checks (index uniqueness, shape agreement,
  schema/licence/provenance/aggregation presence) touch only `.obs`,
  `.var`, and `.uns`, all of which `anndata` loads eagerly even in
  `backed="r"` mode — these run identically for in-memory, sparse, and
  backed input.
- Numeric checks (`MATRIX002` non-finite values, `AI001`/`AI002`
  constant/missing-value features) never call `.toarray()`/`.todense()` on
  the full matrix. For sparse input they inspect `.data` directly; for
  backed or very large input they operate on a bounded random row sample
  (`--sample-rows`, default 5000) rather than the full matrix.
- Dense, CSR, and CSC matrices are all supported in-memory and backed; Zarr
  input is not.
- This means numeric checks on very large backed datasets are
  **statistical, not exhaustive** — a rare non-finite value or a
  near-constant column outside the sample could be missed. This is a
  deliberate precision/completeness trade-off, not an oversight.
- If a check cannot run at all in a given mode, it is recorded as
  `CheckExecution(status="skipped", reason=...)` in the report rather than
  silently omitted or crashing the run.

## Alias resolution is exact, not fuzzy

Schema field aliases are matched case-insensitively after trimming
whitespace, in declaration order. There is no fuzzy/typo-tolerant matching,
regex aliasing, or column-content-based inference. A misspelled
column name that isn't listed as an alias will not resolve, and will
correctly surface as a missing-field issue rather than a silent guess.

## `.uns` metadata blocks are checked for presence, not deep schema

Checks like `META002`, `PROVIMG001`, `PROVSEG001`, `PROVFEAT001`, and
`AGG001`/`AGG002`/`AGG003` verify that the expected `.uns` key exists and has
a plausible shape (for example, a dict with a non-empty value for a specific
sub-key). They do not validate an exhaustive nested schema for those blocks.
`AGG001` is a warning for a missing aggregation method: normal validation
does not fail for that alone, but `--strict` does. Incomplete aggregation
blocks still raise `AGG002`/`AGG003`; this is not a licence to omit
provenance on reusable aggregated products.

## Embedding feature names are not specially handled

DeepProfiler-style embedding columns (for example `efficientnet_0`) have no
CellProfiler compartment prefix, so `FEAT001` still warns on every such
feature. Changing that behaviour is deferred; see
[false-positives.md](false-positives.md).

## Custom schema authoring has no wizard

Loading a user-supplied schema YAML file is fully supported (`--schema
path/to/file.yaml`); an interactive schema-authoring tool/wizard is not
part of the current release.

## No mutation, no fixing

`cp-anndata-validator` never writes to, mutates, or "auto-fixes" the input
`.h5ad` file. It is read-only by design, including in backed mode.

## Synthetic fixtures are not a substitute for external validation

Programmatic "realistic" builders model public CellProfiler / pycytominer /
JUMP conventions. They are regression fixtures, not a replacement for
validating real laboratory or consortium datasets.

## No PyPI publishing commitment yet

`uv build` producing an installable wheel/sdist locally is a release
acceptance criterion; publishing that artifact to PyPI is a separate,
deliberate decision.
