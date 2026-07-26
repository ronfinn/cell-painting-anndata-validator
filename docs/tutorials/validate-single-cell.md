# Validate a single-cell dataset

Single-cell profiles normally require plate, well, site and cell/object
identifiers (schema `required_for` for `single-cell`).

```bash
uv run python examples/generate_examples.py
uv run cp-validate examples/valid_single_cell.h5ad --profile-level single-cell
```

```python
from cp_anndata_validator import ProfileLevel, validate

report = validate(
    "examples/valid_single_cell.h5ad",
    profile_level=ProfileLevel.SINGLE_CELL,
)
assert report.profile_level.effective == ProfileLevel.SINGLE_CELL
```

If detection is ambiguous, pass `--profile-level single-cell` explicitly —
see [Resolve profile-level ambiguity](../how-to/profile-level-ambiguity.md).

For realistic CellProfiler/CytoTable-shaped fixtures without committing
binaries, see `tests/fixtures/realistic.py` and the
[realistic pipeline tutorial](validate-realistic-pipeline.md).
