# Use a custom schema

Author a YAML schema (see [Custom schema format](../schemas/custom.md)), then
point the CLI or API at the file:

```bash
cp-validate experiment.h5ad --schema ./my-lab-schema.yaml
```

```python
from cp_anndata_validator import validate

report = validate("experiment.h5ad", schema="./my-lab-schema.yaml")
```

Malformed schemas raise `SchemaError` before any check runs (CLI exit `2`).
Unknown keys are rejected — they are never silently ignored.

When requesting new aliases for a built-in schema, open a
[schema/alias request](https://github.com/ronfinn/cell-painting-anndata-validator/issues/new/choose)
with public evidence and precedence implications.
