# CLI reference

## Commands

### `cp-validate <path> [OPTIONS]`

Validate one AnnData dataset and print (and optionally write) a report.
This is the default action — you don't need to type `validate` explicitly;
`cp-validate experiment.h5ad` and `cp-validate validate experiment.h5ad` are
equivalent (see [Contributing](../project/contributing.md#the-argv-shim) for why an
explicit `validate` subcommand exists at all).

| Option | Default | Meaning |
|---|---|---|
| `--version` | — | Print the installed package version and exit 0. Independent of built-in schema versions. |
| `--schema TEXT` | `generic-cell-painting` | Built-in schema name or path to a custom schema YAML file. |
| `--profile-level [single-cell\|well\|treatment]` | none (auto-detect) | Declare the profile level, overriding auto-detection. |
| `--report PATH` | none | Also write a report to this path. Format is inferred from the `.json`/`.html` suffix. Refuses to overwrite an existing file unless `--force` is also given. |
| `--backed / --no-backed` | auto (by file size) | Force backed or in-memory loading. |
| `--sample-rows INTEGER` | `5000` | Maximum rows sampled for numeric/AI-readiness checks. |
| `--strict` | off | Treat warning-severity issues as failures too. Warnings alone do not fail a normal run. |
| `--quiet, -q` | off | Suppress console output (`--report` still writes). |
| `--force` | off | Allow `--report` to overwrite an existing file. |

### `cp-validate schema list`

Print the name of every built-in schema, one per line.

### `cp-validate schema show <name>`

Print a built-in schema's canonical fields, their aliases, per-profile-level
requirements, and declared compartments.

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Validation ran and found no failing issues (`report.status == "pass"`). |
| `1` | Validation ran and the report failed (an error-severity issue, or — under `--strict` — a warning-severity issue). |
| `2` | The validator could not produce a pass/fail verdict at all: a file failure (unreadable/missing/corrupt dataset, bad `--report` path/extension, an existing `--report` file without `--force`), a schema failure (invalid/missing schema), a bad CLI argument, or an unexpected execution failure. This should be rare for execution failures specifically — every registered check's exceptions are already isolated into an `ENGINE001` issue by the orchestrator — but it is a defensive safety net at the CLI boundary. No report is produced. |

## Examples

```bash
# Installed package version (not the schema version).
cp-validate --version

# Basic validation, console report only.
cp-validate experiment.h5ad

# Built-in schemas: generic Cell Painting or the JUMP compatibility preset.
cp-validate experiment.h5ad --schema generic-cell-painting
cp-validate experiment.h5ad --schema jump-cp

# Declare the profile level instead of relying on auto-detection.
cp-validate experiment.h5ad --profile-level single-cell
cp-validate experiment.h5ad --profile-level well
cp-validate experiment.h5ad --profile-level treatment

# Write an HTML or JSON report as well.
cp-validate experiment.h5ad --report report.html
cp-validate experiment.h5ad --report report.json

# List and inspect built-in schemas.
cp-validate schema list
cp-validate schema show jump-cp

# Use in a CI pipeline: fail the build on any warning too
# (including AGG001 for missing aggregation provenance).
cp-validate experiment.h5ad --strict --quiet --report report.json
```
