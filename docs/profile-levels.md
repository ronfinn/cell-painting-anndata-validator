# Profile levels

Cell Painting AnnData objects are commonly stored at one of three
granularities:

| Level | One row per... | Typically requires |
|---|---|---|
| `single-cell` | segmented cell/object | plate, well, site, cell/object identifier |
| `well` | plate + well | plate, well identifier |
| `treatment` | perturbation | perturbation identifier, aggregation provenance |

Required fields for each level are declared per-schema in `required_for`
(see [schemas.md](schemas.md)); the table above reflects the built-in
`generic-cell-painting`/`jump-cp` schemas.

## Declaring vs. detecting

You can always declare the profile level explicitly:

```bash
cp-validate experiment.h5ad --profile-level well
```

If you don't, `cp-anndata-validator` auto-detects it. Detection is
**explainable** — every `Report.profile_level` (a `ProfileLevelResult`)
records `declared`, `detected`, `candidates`, `confidence`, and a
human-readable `explanation` string, so you can always see *why* a level was
(or wasn't) chosen. A declared level always wins for which checks actually
run (`ProfileLevelResult.effective`), but the detected level is still
computed and reported for transparency; a mismatch between the two raises
`PROFILE003` (warning).

## How detection works

1. **Column presence.** For each level, are all of its schema-required
   fields resolved? Levels that fail this are eliminated immediately.
2. **Cell granularity.** If `single-cell` passed step 1 *and* a `site` or
   `cell_id` column resolved, the dataset is confidently `single-cell` —
   per-cell columns are a strong, unambiguous signal.
3. **Row cardinality (well vs. treatment).** Otherwise, `well` and
   `treatment` both only require a handful of columns that can coexist
   (well-level data almost always also carries a perturbation identifier).
   To disambiguate, detection compares `n_obs` against:
   - the number of unique `(plate, well)` pairs (well-level: these should
     be equal), and
   - the number of unique `perturbation_id` values (treatment-level: these
     should be equal).

   If exactly one of those cardinalities matches `n_obs`, that level is
   detected with confidence `1.0`. If neither or both match, the result is
   **ambiguous**: `detected` is `None`, `candidates` lists every level that
   is still plausible, and `PROFILE002` (information) is emitted.

Ambiguity is a legitimate, expected outcome for some designs (for example, a
plate map with exactly one perturbation per well) — it is surfaced, not
silently guessed away. Pass `--profile-level` to resolve it explicitly.
