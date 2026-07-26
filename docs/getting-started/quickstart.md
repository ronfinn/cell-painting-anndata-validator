# Five-minute quickstart

Generate the small synthetic examples (not committed as binaries):

```bash
uv run python examples/generate_examples.py
```

Validate a well-level example:

```bash
uv run cp-validate examples/valid_well_level.h5ad
```

Or from Python:

```python
from cp_anndata_validator import validate

report = validate("examples/valid_well_level.h5ad")
print(report.status)
for issue in report.issues:
    print(issue.code, issue.severity.value, issue.message)
```

Exit code `0` means no error-severity issues (warnings alone do not fail a
normal run). Use `--strict` when warnings should fail the process — see
[Run strict validation](../how-to/strict-validation.md).
