## Summary

<!-- What does this PR change, and why? -->

## Related

<!-- Link issues or ADRs (docs/decisions/ADR-XXXX). -->

## Checklist

- [ ] `uv run pytest` passes
- [ ] `uv run ruff check .` and `uv run ruff format --check .` pass
- [ ] `uv run mypy src` passes
- [ ] `uv run mkdocs build --strict` passes when docs change
- [ ] Rule catalogue / CHANGELOG updated for user-visible behaviour
- [ ] No private datasets, generated `.h5ad`, or Gallery downloads committed
- [ ] Does not convert source formats into AnnData or fabricate metadata
