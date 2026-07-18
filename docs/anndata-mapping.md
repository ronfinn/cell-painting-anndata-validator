# AnnData slot semantics

`cp-anndata-validator` assumes the following conventions when validating an
`.h5ad` file. It never writes to any of these slots.

| Slot | Expected content | Checked by |
|---|---|---|
| `.X` | The primary feature matrix: one row per observation (cell/well/treatment), one column per feature. Must be numeric; sparse or dense; NaN/Inf are flagged but not rejected outright. | `checks/matrix.py` (`MATRIX001`, `MATRIX002`), `checks/structure.py` (`STRUCT002`) |
| `.obs` | One row per observation, with identifier columns (plate/well/site/cell/perturbation) and annotation columns (control type, batch). Matched via schema aliases, not fixed names. | `checks/identifiers.py`, `checks/annotations.py`, `checks/metadata.py` |
| `.var` | One row per feature; `var_names` are expected to be prefixed by a declared compartment (`Cells_`, `Cytoplasm_`, `Nuclei_`, `Image_`, ...). | `checks/features.py`, `checks/structure.py` (`INDEX002`) |
| `.uns` | Free-form, dataset-level metadata: `schema_id`, `schema_version`, `processing_stage`, `licence`/`license`, `experiment`, `image_provenance`, `segmentation_provenance`, `feature_extraction_provenance`, `aggregation` (for well/treatment profiles). | `checks/schema_meta.py`, `checks/metadata.py`, `checks/provenance.py`, `checks/aggregation.py`, `checks/matrix.py` (`SLOT001`) |
| `.obsm` | Per-observation arrays (embeddings, spatial coordinates, ...). First dimension must equal `n_obs`. | `checks/matrix.py` (`SLOT002`) |
| `.varm` | Per-feature arrays (loadings, ...). First dimension must equal `n_vars`. | `checks/matrix.py` (`SLOT002`) |
| `.layers` | Alternative versions of `.X` (raw counts, normalized values, ...). Every layer's shape must equal `.X`'s shape. | `checks/matrix.py` (`MATRIX004`) |

## Suggested `.uns` metadata block shapes

None of these are enforced beyond presence/basic shape (v0.1 does not
validate arbitrary nested schemas for `.uns` sub-blocks), but checks look
for these specific shapes:

```python
adata.uns["schema_id"] = "generic-cell-painting"
adata.uns["schema_version"] = "0.1.0"
adata.uns["processing_stage"] = "normalized"  # raw | normalized | aggregated | ...
adata.uns["licence"] = "CC0-1.0"

adata.uns["experiment"] = {"instrument": "...", "protocol": "..."}
adata.uns["image_provenance"] = {"microscope": "...", "illumination_correction": True}
adata.uns["segmentation_provenance"] = {"tool": "CellProfiler", "version": "4.2.6"}
adata.uns["feature_extraction_provenance"] = {"tool": "CellProfiler", "version": "4.2.6"}

# well-level / treatment-level profiles only:
adata.uns["aggregation"] = {"method": "median", "replicate_count": 4}
```

See [checks.md](checks.md) for exactly which rule code each block's absence
triggers, and [schemas.md](schemas.md) for how `.obs`/`.var` columns are
resolved via aliases (a separate mechanism from these `.uns` blocks).
