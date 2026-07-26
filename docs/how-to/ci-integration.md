# Integrate with CI

Minimal GitHub Actions fragment (after installing the package):

```yaml
- name: Validate AnnData
  run: |
    cp-validate dataset.h5ad --strict --quiet --report report.json
```

Notes:

- Exit `0` / `1` / `2` semantics match the CLI reference.
- Prefer `--quiet` in CI logs when you also write `--report`.
- Do not commit large public-data downloads; generate or fetch them in the job
  if needed, or validate synthetic fixtures checked into the workflow via a
  generator script.
- This repository’s own CI runs the test suite and a docs build; it does not
  publish to PyPI.
