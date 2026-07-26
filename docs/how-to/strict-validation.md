# Run strict validation

```bash
cp-validate experiment.h5ad --strict
```

```python
from cp_anndata_validator import validate

report = validate("experiment.h5ad", strict=True)
```

In strict mode, **warning** severity issues (including `AGG001` for missing
aggregation provenance) cause `report.status == "fail"` and CLI exit code
`1`. Information-severity issues never fail the report.

Use strict mode in publishing CI when you want governance gaps to block a
merge. Use normal mode for exploratory work where warnings are informative
but not fatal.
