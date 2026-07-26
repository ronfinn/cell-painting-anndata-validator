# Troubleshoot common errors

| Symptom | Likely cause | What to do |
|---|---|---|
| Exit code `2`, file error | Missing/corrupt `.h5ad`, wrong path | Confirm the file opens with `anndata.read_h5ad` |
| Exit code `2`, schema error | Bad custom YAML or unknown key | Fix the schema; unknown keys are rejected |
| Exit code `2`, report path | Report exists without `--force`, or bad suffix | Use `.json`/`.html` and `--force` if overwriting |
| Many `IDENTxxx` errors | Wrong schema or profile level | Try `--schema jump-cp` or declare `--profile-level` |
| `FEAT001` on every feature | Embedding-style names without compartment prefix | Expected for DeepProfiler-style names today; see false-positives guide |
| `AGG001` warning | Missing `uns['aggregation']` on well/treatment | Add truthful aggregation provenance, or use `--strict` only when ready |
| `META001` for batch | Column name not in schema aliases | Check [alias precedence](../schemas/aliases.md); open an alias request with public evidence |
| `ENGINE001` | Unexpected exception inside a check | Report a bug with package version and a **synthetic** minimal reproduction |

Never attach private or proprietary datasets to public issues. Prefer
redacted column lists and tiny synthetic AnnData.
