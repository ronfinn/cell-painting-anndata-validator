# What the validator assesses

`cp-anndata-validator` assesses four layers. Keep them separate when reading
a report.

| Layer | Assessed? | Examples |
|---|---|---|
| **Structural validity** | Yes | File opens; indices unique; matrix shape matches `n_obs` × `n_vars`; layers/obsm align |
| **Semantic completeness** | Yes | Required identifiers for the profile level; control annotations; feature naming conventions |
| **Basic AI readiness** | Yes (bounded) | Non-finite values; constant or heavily missing features on a row sample |
| **Biological / scientific suitability** | **No** | Phenotype quality, assay validity, hit calling, biological interpretation |

Provenance and licence checks ask whether expected `.uns` metadata is
*present and plausibly shaped*. They do not verify that a microscope log is
scientifically correct.
