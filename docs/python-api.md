# Python API

The entire public surface is importable directly from the top-level
package:

```python
from cp_anndata_validator import (
    validate,       # the one function that runs everything
    Report,         # what validate() returns
    Issue,          # a single structured finding
    Severity,       # error | warning | information
    Category,       # e.g. identifiers, matrix, provenance, ...
    ProfileLevel,   # single-cell | well | treatment
    LoadError,      # raised if the dataset can't be opened
    SchemaError,    # raised if the schema can't be loaded
)
```

## `validate()`

```python
def validate(
    path: str | Path,
    *,
    schema: str | Path = "generic-cell-painting",
    profile_level: ProfileLevel | None = None,
    backed: bool | None = None,
    sample_rows: int = 5000,
    strict: bool = False,
) -> Report: ...
```

```python
from cp_anndata_validator import ProfileLevel, validate

report = validate(
    "experiment.h5ad",
    schema="jump-cp",
    profile_level=ProfileLevel.SINGLE_CELL,
)

print(report.status)                 # "pass" or "fail"
print(report.counts.by_severity)     # {Severity.ERROR: 2, Severity.WARNING: 1}
for issue in report.issues:
    print(issue.code, issue.severity, issue.location, issue.message)
```

Raises `cp_anndata_validator.LoadError` if the file can't be safely opened,
and `cp_anndata_validator.SchemaError` if the requested schema can't be
loaded — both before any checks run.

## Rendering a report

Renderers are pure functions, independent of validation logic — you can
call them on any `Report`, including ones you constructed yourself (for
example in a test):

```python
from cp_anndata_validator.reporting import render_console, render_html, render_json

print(render_console(report))
Path("report.json").write_text(render_json(report))
Path("report.html").write_text(render_html(report))
```

## Working with `Issue` and `Report`

Both are frozen Pydantic models (`model_config = ConfigDict(frozen=True, extra="forbid")`),
so they serialize/deserialize losslessly:

```python
payload = report.model_dump_json()
restored = Report.model_validate_json(payload)
assert restored == report
```

See [checks.md](checks.md) for the full field list on `Issue`, and
`src/cp_anndata_validator/models/report.py` for `Report`'s complete shape
(`profile_level`, `counts`, `checks`, `input_file`, etc.).

## Advanced: running the check registry directly

Most users only need `validate()`. If you need lower-level access (for
example, to run a custom subset of checks), the building blocks are all
independently importable:

```python
from cp_anndata_validator.loading import load_anndata
from cp_anndata_validator.schema.loader import load_schema
from cp_anndata_validator.schema.resolve import resolve_schema
from cp_anndata_validator.profiles import detect_profile_level
from cp_anndata_validator.checks.registry import CheckContext
from cp_anndata_validator.orchestrator import run_checks, build_report
import cp_anndata_validator.checks  # registers all built-in checks

handle = load_anndata("experiment.h5ad")
schema = load_schema("generic-cell-painting")
resolved = resolve_schema(handle.adata.obs, handle.adata.var, schema)
profile = detect_profile_level(handle.adata.obs, resolved)

ctx = CheckContext(handle=handle, resolved_schema=resolved, profile=profile)
issues, checks = run_checks(ctx)
```

See [contributing.md](contributing.md#adding-a-check) for how to register a
new check.
