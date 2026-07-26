# Schema and package versioning

| Artifact | Current | Where |
|---|---|---|
| Package / distribution | `0.2.0b1` | `pyproject.toml`, `cp_anndata_validator.__version__`, CLI `--version` |
| `generic-cell-painting` schema | `0.2.1` | `src/.../schema/resources/generic-cell-painting.yaml` |
| `jump-cp` schema | `0.2.1` | `src/.../schema/resources/jump-cp.yaml` |

These version lines are **independent**. A schema vocabulary change can ship
without a package major bump when behaviour remains compatible, and the
package can advance while schemas stay put.

`uns['schema_id']` / `uns['schema_version']` on a dataset, when present, are
compared by schema-meta checks; they describe the **dataset’s declared
schema**, not the validator package version.

See [ADR-0004](../decisions/ADR-0004-independent-versioning.md).
