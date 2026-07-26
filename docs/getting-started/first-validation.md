# First validation

## Console report

```bash
uv run cp-validate path/to/experiment.h5ad
```

The console summary shows package version, schema, profile level,
pass/fail status, counts by severity, and ordered issues.

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Validation completed; no failing issues |
| `1` | Validation completed; failing issues found |
| `2` | Could not execute (bad file, schema, or configuration) |

Under normal mode, only **error** severity fails the run. Under `--strict`,
**warnings** also fail (exit `1`).

## Declare schema and profile level

```bash
uv run cp-validate experiment.h5ad --schema jump-cp --profile-level well
```

Auto-detection is explainable and recorded on the report even when you
override the level — see [Profile levels](../concepts/profile-levels.md).

## Write a report file

```bash
uv run cp-validate experiment.h5ad --report report.json
uv run cp-validate experiment.h5ad --report report.html
```

Existing report paths are refused unless `--force` is also given.
