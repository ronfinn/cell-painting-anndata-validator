# False-positive analysis and expected baselines

This page answers a question every user of a validator eventually asks: *"my
data is fine — why is this thing complaining?"*

For each validation category it records what the category is meant to catch,
whether **valid, real-world** Cell Painting output can trigger it, and how to
read that signal. Three verdicts are used throughout:

| Verdict | Meaning |
|---|---|
| **Governance signalling** | The dataset really is missing something a publisher should add. Working as intended, even though the data itself is scientifically fine. |
| **Likely false positive** | The finding reflects a gap in this package's vocabulary or heuristics, not a problem with the dataset. Under review for calibration. |
| **Genuine defect** | A bug in `cp-anndata-validator`. Should never be observed; please report it. |

Every claim below was derived by running the current implementation against
the fixtures in `tests/fixtures/realistic.py`, and the baselines are pinned by
`tests/test_realistic_baselines.py` so they cannot drift unnoticed.

## The three reference fixtures

| Fixture | Models | Schema used |
|---|---|---|
| `make_cellprofiler_single_cell` | CellProfiler/CytoTable single-cell export, one row per segmented object | `generic-cell-painting` |
| `make_pycytominer_well_profile` | pycytominer well-level profile, one aggregated row per plate/well | `generic-cell-painting` |
| `make_jump_treatment_profile` | JUMP-style treatment profile, one row per perturbation | `jump-cp` |

Each builder takes `with_provenance`. With `True` it declares the full `.uns`
metadata set; with `False` it models **bare pipeline output**, which carries no
`.uns` blocks at all — the realistic default for a fresh export.

## Expected baselines for bare pipeline output

A fully-documented fixture reports **nothing at all** (`status="pass"`, zero
issues) at every profile level. The bare variants report exactly this:

| Fixture | Status | Codes |
|---|---|---|
| single-cell | `pass` (9 warnings) | `LICENSE001`, `META002`, `PROVFEAT001`, `PROVIMG001`, `PROVSEG001`, `SCHEMA001`, `SCHEMA002`, `SLOT001`, `SLOT003` |
| well | `fail` (1 error, 8 warnings) | `AGG001`, `LICENSE001`, `META002`, `PROVFEAT001`, `PROVIMG001`, `PROVSEG001`, `SCHEMA001`, `SCHEMA002`, `SLOT001` |
| treatment | `fail` (2 errors, 8 warnings) | `AGG001`, `IDENT006`, `LICENSE001`, `META002`, `PROVFEAT001`, `PROVIMG001`, `PROVSEG001`, `SCHEMA001`, `SCHEMA002`, `SLOT001` |

Three things are worth internalising from that table. The single-cell baseline
is **warning-only**, so it passes by default and only fails under `--strict`.
`SLOT003` appears solely because the single-cell fixture carries a realistic
`raw` layer whose own processing stage is undeclared. And the aggregated
profiles **fail**, because `AGG001` is an error — see below. The bare fixtures
deliberately use only schema-declared measurement families, so they do **not**
emit `FEAT001`/`FEAT002`; those false positives are demonstrated separately
below with real CellProfiler / embedding names.

## Categories that valid real output can trigger

### Schema, licence, metadata and provenance — governance signalling

Codes: `SCHEMA001`, `SCHEMA002`, `LICENSE001`, `META002`, `SLOT001`,
`SLOT003`, `PROVIMG001`, `PROVSEG001`, `PROVFEAT001`. Demonstrated by all
three bare fixtures. Closely related, and informational rather than part of
the bare baseline when the columns are present: `META001` (missing batch
identifier) and `META003` (missing source/site identifier).

These detect whether a dataset documents *itself*: which schema it targets,
its licence, its experiment context, what processing stage `.X` holds, and how
its images, segmentation and features were produced. Standard pipeline output
carries none of the `.uns` blocks, so eight of these fire on every bare
export (`SLOT003` is the ninth, and only when undeclared `.layers` are
present).

This is **governance signalling and the entire point of the package** — not a
false positive. CytoTable and pycytominer are not obliged to invent provenance
they were never given; recording it is the publisher's job, and this is the
tool that asks for it. Nothing here is a statement about your data's
scientific quality.

**What to do:** populate the `.uns` blocks before publishing or training —
`schema_id`, `schema_version`, `licence`, `experiment`, `processing_stage`,
`layer_processing_stages`, `image_provenance`, `segmentation_provenance`,
`feature_extraction_provenance`. Doing so clears the entire baseline, which
`test_declaring_metadata_clears_the_entire_bare_baseline` asserts. Until then,
avoid `--strict` in CI, since these warnings would fail the build.

### Aggregation — governance signalling, but with a severity worth revisiting

Codes: `AGG001` (error), `AGG002`, `AGG003` (warnings). Demonstrated by the
bare well and treatment fixtures.

This category asks an aggregated profile to declare *how* it was aggregated
(`method`), from *how many* replicates (`replicate_count`), and from *what*
level (`source_level`). The requirement is sound: a median well profile and a
mean well profile are different data, and nothing in the file distinguishes
them otherwise.

The consequence, however, is sharp: because `AGG001` is an **error**, a
standard pycytominer well profile with no `uns['aggregation']` **fails
validation and exits 1**. On the treatment fixture it compounds with
`IDENT006`, since plate/well were aggregated away and, without
`uns['aggregation']`, the rows cannot be traced back to any source data.

This is governance signalling rather than a false positive — the information
genuinely is absent — but the error severity means the most common real-world
aggregated profile fails out of the box. Whether that is the right severity is
a calibration decision, deliberately **not** taken in this milestone.

**What to do:** declare `uns['aggregation']` with at least `method` and
`source_level` (add `replicate_count` to clear `AGG002`). That single block
clears `AGG001`, `AGG002`, `AGG003` and `IDENT006` together.

### Features — likely false positive

Codes: `FEAT001`, `FEAT002` (both warnings).

`FEAT001` checks that feature names start with a schema-declared compartment
(`Cells_`, `Cytoplasm_`, `Nuclei_`, `Image_`); `FEAT002` checks that the token
after the compartment is a recognized measurement family. Two verified cases
misfire on legitimate data:

- **Real CellProfiler families the schemas do not list.** `ObjectSkeleton`,
  `Math`, `Overlap`, `SizeShape`, `AreaOccupied` and `ImageQuality` are all
  emitted by real CellProfiler pipelines but absent from
  `measurement_families`, so a name like
  `Cells_ObjectSkeleton_NumberBranchEnds_Mito` raises `FEAT002` despite being
  perfectly canonical.
- **Embedding-based features.** DeepProfiler-style names such as
  `efficientnet_0` have no compartment prefix at all, so `FEAT001` flags
  *every* feature in the matrix (verified against a 4-column embedding
  fixture: all four names raised `FEAT001`).

Both are **likely false positives**: the datasets are valid and the naming is
what the upstream tool produces. Both are warnings, so neither fails a
non-strict run.

**What to do:** for CellProfiler data, extend `measurement_families` in a
custom schema (see [`schemas.md`](schemas.md)) until the built-in vocabulary is
widened. For embeddings, expect `FEAT001` and treat it as informational — a
compartment prefix is meaningless for a neural embedding.

### Identifiers — alias gaps, partly a likely false positive

Codes: `IDENT001`–`IDENT005` (missing required identifiers), `IDENT006`
(treatment traceability), `IDENT007`/`IDENT008` (perturbation modality),
`OBS001`/`OBS002` (duplicate/missing identifier values), `IDENT000`
(custom-schema fallback).

Resolution is exact, not fuzzy, so real JUMP perturbation spellings resolve
inconsistently (verified):

| Column | `generic-cell-painting` | `jump-cp` |
|---|---|---|
| `Metadata_JCP2022` | not resolved | resolves as `perturbation_id` |
| `Metadata_broad_sample` | not resolved | not resolved |
| `Metadata_pert_iname` | not resolved | not resolved |

The practical effect is subtle rather than loud. An unresolved
`perturbation_id` does not raise a missing-identifier error at well level
(it isn't required there); instead it **silently disables** `IDENT007`/
`IDENT008` and removes `treatment` from profile detection. So the risk is a
*false negative* — checks quietly not running — more than a false positive.
Validate JUMP-style data with `--schema jump-cp`, as the treatment fixture
does.

`OBS001`/`OBS002` are low-risk: they fire only on genuinely duplicated or null
identifier tuples, which is a real data defect.

**What to do:** use `jump-cp` for JUMP-style metadata, or add your pipeline's
perturbation column as an alias in a custom schema. If `IDENT007` appears,
declare a modality column rather than ignoring it.

### Profile consistency — expected ambiguity, not a false positive

Codes: `PROFILE001` (error), `PROFILE002` (information), `PROFILE003`
(warning).

Detection uses column presence plus row cardinality. When a plate has exactly
one perturbation per well, plate/well pairs and perturbation identifiers are
*both* unique per row, so well and treatment are genuinely indistinguishable
from the data alone. Verified behaviour: `detected=None`, `candidates=(well,
treatment)`, `confidence=0.5`, and `PROFILE002` at **information** severity.

This is correct and deliberate: an honest "I cannot tell, here is why" beats a
confident guess. It is neither a false positive nor a defect, and because
`PROFILE002` is informational it never fails a run. All three realistic
fixtures detect their level unambiguously, so ambiguity is a property of
certain plate designs, not of the fixtures.

**What to do:** pass `--profile-level` (or `profile_level=` in Python) to state
the level explicitly. Note that a declared level disagreeing with detection
raises `PROFILE003`, which is the intended feedback loop.

### Annotations — likely false positive for site-specific vocabularies

Codes: `CTRL001`, `CTRL002`, `CTRL003` (all warnings).

Recognized labels are `negcon`, `poscon`, `trt`, `control`, `treatment`,
`unknown`. Verified misfires on legitimate data: JUMP's finer-grained control
vocabulary (`poscon_cp`, `poscon_diverse`) raises `CTRL002`, because the
comparison is exact rather than prefix-based. That is a **likely false
positive** — those are real, meaningful JUMP labels.

`CTRL003` ("no negative control") is different: on a compound-only plate with
no `negcon`, the warning is factually correct and worth surfacing, since
downstream normalization typically needs one. Treat it as governance
signalling about experimental design.

**What to do:** map site-specific labels onto the recognized vocabulary, or
extend a custom schema. Do not suppress `CTRL003` without checking how your
normalization obtains its baseline.

### AI readiness — informational, low risk

Codes: `AI001` (information), `AI002` (warning).

`AI001` reports constant (zero-variance) feature columns; a retained
blocklisted feature legitimately produces it (verified). `AI002` fires when
more than 20% of sampled values are NaN, alongside `MATRIX002` for the same
underlying values (verified). Neither is a false positive — the observation is
true — but `AI001` in particular is advice, not a defect, and is
informational precisely for that reason.

**What to do:** drop zero-variance columns before training; impute, mask or
document NaNs. Remember these checks run on a bounded row sample, so they are
statistical rather than exhaustive (see [`limitations.md`](limitations.md)).

## Categories that valid output should not trigger

| Category | Codes | Detects | Verdict if seen |
|---|---|---|---|
| Structure | `STRUCT001`, `STRUCT002`, `INDEX001`–`INDEX003` | Unreadable file, empty/absent `.X`, duplicate or empty `obs_names`/`var_names` | Real data defect — a valid export never has these |
| Matrix | `MATRIX001`–`MATRIX004` | Non-numeric dtype, non-finite values, `.X`/`(n_obs, n_vars)` disagreement, layer shape mismatch | Real data defect (`MATRIX002` may be legitimate if NaNs are intentional and documented) |
| Slot semantics (alignment) | `SLOT002` | `.obsm`/`.varm` first dimension disagreeing with `n_obs`/`n_vars` | Real data defect. The realistic fixtures carry `.layers` and `.obsm` entries specifically to prove correct slots stay silent |

`MATRIX003` in particular can only appear for a hand-edited or corrupted file,
since `anndata` enforces that invariant on construction.

## Engine errors must never appear

`ENGINE001` (error) means a registered check raised an unexpected exception and
its result was replaced by that issue so the run could continue. It is
**always a genuine defect in this package**, never a statement about your data.

No realistic fixture may produce it, in any matrix container (dense/CSR/CSC),
either loading mode (in-memory/backed), at any profile level, with or without
provenance. `tests/test_realistic_parity.py` asserts this across all 36
combinations, and `tests/test_realistic_baselines.py` asserts it again for the
bare exports.

This is not hypothetical. A real `ENGINE001` existed until recently: passing
`profile_level="well"` as a plain string to `validate()` left an uncoerced
`str` in the check context, which crashed the aggregation check on
`level.value`. The public API now coerces the value, and it raises `ValueError`
immediately for an unsupported one.

**What to do:** if you ever see `ENGINE001`, report it with the check name from
the issue's `check_name` field and a minimal reproducing dataset.

## Reaching a clean report

For a dataset that is scientifically sound, a completely clean report is
achievable and the realistic fixtures demonstrate it. In order of effort:

1. Declare the `.uns` metadata blocks listed above — this clears eight of the
   nine baseline codes.
2. Declare `uns['aggregation']` for any well or treatment profile.
3. Declare `uns['layer_processing_stages']` if you ship `.layers`.
4. Choose the schema that matches your metadata convention (`jump-cp` for JUMP
   spellings) or write a custom schema for your own column and feature naming.
5. Only then consider `--strict` in CI, once the warning baseline is genuinely
   empty rather than merely tolerated.
