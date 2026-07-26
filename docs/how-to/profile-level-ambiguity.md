# Resolve profile-level ambiguity

When auto-detection cannot choose a single level, the report records
candidates and an explanation (`PROFILE002` information). A mismatch between
a declared level and detection emits `PROFILE003` (warning).

Always override explicitly when you know the product:

```bash
cp-validate experiment.h5ad --profile-level well
```

```python
from cp_anndata_validator import validate

report = validate("experiment.h5ad", profile_level="well")
print(report.profile_level.explanation)
```

Detection rules are documented under
[Profile levels](../concepts/profile-levels.md) and
[ADR-0006](../decisions/ADR-0006-profile-level-detection.md).
