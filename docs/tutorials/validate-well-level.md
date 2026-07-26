# Validate a well-level profile

Well-level profiles normally require plate and well identifiers, but not
cell identifiers. Aggregation provenance is recommended; missing
`uns['aggregation']` emits warning `AGG001` (fails only under `--strict`).

```bash
uv run python examples/generate_examples.py
uv run cp-validate examples/valid_well_level.h5ad --profile-level well
```

Public LINCS and JUMP well-level Gallery pilots are documented in
[Public-data pilots](../pilots/index.md). Those binaries are **not** stored
in this repository.
