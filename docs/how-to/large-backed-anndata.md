# Work with large or backed AnnData

```bash
cp-validate large.h5ad --backed --sample-rows 5000
```

- `--backed` forces `anndata` backed mode; `--no-backed` forces a full load.
- When omitted, loading mode is chosen from file size.
- Numeric and AI-readiness checks use bounded row sampling
  (`--sample-rows`, default `5000`) and never densify a full sparse matrix.
- Structural and metadata checks use `.obs` / `.var` / `.uns`, which remain
  available in backed mode.

See [ADR-0008](../decisions/ADR-0008-bounded-sampling.md) and
[Known limitations](../project/limitations.md).
