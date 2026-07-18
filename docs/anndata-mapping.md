# AnnData slot semantics

`cp-anndata-validator` assumes the following conventions when validating an
`.h5ad` file. It never writes to any of these slots.

| Slot | Expected content | Checked by |
|---|---|---|
| `.X` | The primary feature matrix: one row per observation (cell/well/treatment), one column per feature. Must be numeric; sparse or dense; NaN/Inf are flagged but not rejected outright; its shape must equal `(n_obs, n_vars)`. | `checks/matrix.py` (`MATRIX001`, `MATRIX002`, `MATRIX003`), `checks/structure.py` (`STRUCT002`) |
| `.obs` | One row per observation, with identifier columns (plate/well/site/cell/perturbation/perturbation modality) and annotation columns (control type, batch, source). Matched via schema aliases, not fixed names. | `checks/identifiers.py`, `checks/annotations.py`, `checks/metadata.py` |
| `.var` | One row per feature; `var_names` are expected to be prefixed by a declared compartment (`Cells_`, `Cytoplasm_`, `Nuclei_`, `Image_`, ...) followed by a recognized measurement family (`AreaShape_`, `Intensity_`, `Texture_`, ...). | `checks/features.py`, `checks/structure.py` (`INDEX002`) |
| `.uns` | Free-form, dataset-level metadata: `schema_id`, `schema_version`, `processing_stage`, `layer_processing_stages`, `licence`/`license`, `experiment`, `image_provenance`, `segmentation_provenance`, `feature_extraction_provenance`, `aggregation` (for well/treatment profiles). | `checks/schema_meta.py`, `checks/metadata.py`, `checks/provenance.py`, `checks/aggregation.py`, `checks/matrix.py` (`SLOT001`, `SLOT003`) |
| `.obsm` | Per-observation arrays (embeddings, spatial coordinates, ...). First dimension must equal `n_obs`. | `checks/matrix.py` (`SLOT002`) |
| `.varm` | Per-feature arrays (loadings, ...). First dimension must equal `n_vars`. | `checks/matrix.py` (`SLOT002`) |
| `.layers` | Alternative versions of `.X` (raw counts, normalized values, ...). Every layer's shape must equal `.X`'s shape, and each layer should have its own declared processing stage (see below) since `uns['processing_stage']` alone only describes `.X`. | `checks/matrix.py` (`MATRIX004`, `SLOT003`) |

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

# only if .layers holds data at a different processing stage than .X:
adata.uns["layer_processing_stages"] = {"counts": "raw"}

# well-level / treatment-level profiles only. `source_level` is the profile
# level rows were aggregated *from* (what makes plate/well optional at
# treatment level -- see IDENT006 in checks.md):
adata.uns["aggregation"] = {
    "method": "median",
    "replicate_count": 4,
    "source_level": "well",
}
```

See [checks.md](checks.md) for exactly which rule code each block's absence
triggers, and [schemas.md](schemas.md) for how `.obs`/`.var` columns are
resolved via aliases (a separate mechanism from these `.uns` blocks).
