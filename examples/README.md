# Examples

`generate_examples.py` writes three small, synthetic `.h5ad` files into this
directory. They are **not** committed to version control (see
`.gitignore`) — regenerate them locally with:

```bash
uv run python examples/generate_examples.py
```

Each is a few tens of KiB (10-16 rows, 8-9 features) — enough to demonstrate
every category of check without shipping binary fixtures in the repository.

## `valid_single_cell.h5ad`

A clean single-cell profile: plate/well/site/cell identifiers, a
control/treatment column, batch and source identifiers, compartment- and
measurement-family-prefixed feature names, and every `uns` provenance/
licence/schema block populated.

```bash
uv run cp-validate examples/valid_single_cell.h5ad
```

Expect **exit code `0`** (`Status: PASS`, zero issues — auto-detected as
`single-cell`).

## `valid_well_level.h5ad`

A clean, aggregated well-level profile: one row per plate/well, a
perturbation identifier and modality, aggregation provenance
(`uns['aggregation']`), and the same metadata completeness as above.

```bash
uv run cp-validate examples/valid_well_level.h5ad
uv run cp-validate examples/valid_well_level.h5ad --schema jump-cp --profile-level well
```

Expect **exit code `0`** for both invocations (zero issues either way — every
column is named so it resolves under both the `generic-cell-painting` and
`jump-cp` schemas).

## `invalid_example.h5ad`

A single-cell-shaped profile with several independent, deliberately
introduced problems, so a single validation run demonstrates most of the
package's check categories at once:

| Problem | Rule code(s) fired | Severity |
|---|---|---|
| No `plate` column | `IDENT001`, `PROFILE001` | error |
| No `cell_id` column | `IDENT004`, `PROFILE001` | error |
| Two rows share the same `obs_names` value | `INDEX001` | error |
| Two rows share the same identifier-column tuple | `OBS001` | error |
| No control/treatment annotation column | `CTRL001` | warning |
| Feature names lack a compartment prefix | `FEAT001` | warning |
| No `uns['licence']` | `LICENSE001` | warning |
| No `uns['schema_id']` / `uns['schema_version']` | `SCHEMA001`, `SCHEMA002` | warning |
| No `uns['processing_stage']` | `SLOT001` | warning |
| No `uns['experiment']` | `META002` | warning |
| No image/segmentation/feature-extraction provenance | `PROVIMG001`, `PROVSEG001`, `PROVFEAT001` | warning |
| One `NaN` value in `.X` | `MATRIX002` | warning |
| No `batch`/`source` column | `META001`, `META003` | information |

```bash
uv run cp-validate examples/invalid_example.h5ad --profile-level single-cell
```

Expect **exit code `1`** (`Status: FAIL`: 5 errors, 11 warnings, 2
information issues).

`plate`/`cell_id` are declared missing on purpose, which also makes
auto-detection structurally inconclusive; `--profile-level single-cell` is
passed explicitly above so the identifier-completeness checks run against a
concrete profile level, exactly as a user validating a known dataset shape
would do. Omitting `--profile-level` still fails (`exit 1`, via `OBS001`/
`INDEX001`/metadata/provenance issues), just without the profile-specific
`IDENT001`/`IDENT004`/`PROFILE001` issues.

## Generating reports

```bash
# Self-contained, escaped HTML report:
uv run cp-validate examples/invalid_example.h5ad --profile-level single-cell \
    --report examples/invalid_example.html

# Deterministic JSON report:
uv run cp-validate examples/valid_single_cell.h5ad --report examples/valid_single_cell.json
```

Both refuse to overwrite an existing file unless `--force` is also passed.

## Strict mode

```bash
uv run cp-validate examples/invalid_example.h5ad --profile-level single-cell --strict
```

Expect **exit code `1`** here too (it already has error-severity issues);
`--strict` additionally turns warning-only reports into failures — see
`tests/test_cli.py::test_validate_command_strict_turns_warnings_into_failures`
for a case built specifically to demonstrate that (a dataset with only a
missing-licence warning: exit `0` normally, exit `1` under `--strict`).
