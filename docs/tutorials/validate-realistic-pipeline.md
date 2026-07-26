# Validate realistic public pipeline output

The test suite includes programmatic builders that model public
CellProfiler/CytoTable single-cell, pycytominer well, and JUMP treatment
shapes (`tests/fixtures/realistic.py`). They are regression fixtures, not
committed `.h5ad` files.

```python
from cp_anndata_validator import validate
from tests.fixtures.realistic import make_pycytominer_well_profile

adata, path = ...  # write the fixture AnnData to a temporary .h5ad in your script
report = validate(path, schema="generic-cell-painting", profile_level="well")
print(sorted({i.code for i in report.issues}))
```

Pinned bare-pipeline baselines live in `tests/test_realistic_baselines.py`.
How to read governance warnings versus likely false positives is covered in
[Expected findings and false positives](../how-to/false-positives.md).

For genuine Gallery plates (LINCS / JUMP), keep downloads outside the repo
and follow [Public-data pilots](../pilots/index.md). Do not commit downloaded
profiles or generated pilot `.h5ad` files.
