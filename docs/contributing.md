# Contributing

## Dev workflow

This project uses [`uv`](https://docs.astral.sh/uv/) for everything —
environment management, dependencies, running commands, and building.

```bash
uv sync                          # install/lock dependencies
uv run pytest                    # run the test suite
uv run ruff check .               # lint
uv run ruff format --check .      # verify formatting (uv run ruff format . to fix)
uv run mypy src                   # type-check the package
uv build                          # build sdist + wheel into dist/
```

All four checks (`pytest`, `ruff check`, `ruff format --check`, `mypy`) and
`uv build` must pass before a change is considered done. This matches
exactly what CI (and the milestone acceptance criteria used to build this
package) run.

## Repository layout

```
src/cp_anndata_validator/
    loading.py, sampling.py, profiles.py     # layer 1: read AnnData safely
    schema/                                  # layer 2: schema model, loader, alias resolution
    models/                                  # Issue, Report, and friends
    checks/                                  # one module per validation category
    orchestrator.py                          # runs checks, assembles the Report
    api.py                                   # validate() — the one integration point
    reporting/                               # console / JSON / HTML renderers
    cli/                                     # Typer wiring only; delegates to api.py + reporting
tests/
    fixtures/synthetic.py                    # shared synthetic AnnData builders
    test_*.py                                # one test module per source module, mirroring the tree
docs/                                        # this documentation set
```

## Adding a check

1. Pick (or create) the `checks/<category>.py` module matching your
   validation category.
2. Write a function taking a `CheckContext` (see
   `checks/registry.py`) and returning `list[Issue]`. Never print or raise
   for expected validation failures — return `Issue` objects instead; the
   orchestrator already isolates unexpected exceptions into `ENGINE001`, so
   you don't need defensive `try`/`except` inside a check for that.
3. Register it with `@register_check(name="...", category=Category.X)`.
4. Add a new rule code, or reuse an existing one if the check refines an
   existing meaning. **New codes are never reused for a different meaning
   later** — pick a fresh number in the right category's block. Document it
   in [checks.md](checks.md).
5. Add a test module `tests/test_checks_<category>.py` exercising both the
   passing and failing paths, using or extending
   `tests/fixtures/synthetic.py`.
6. If the check needs new `.uns`/`.obs`/`.var` conventions, document them in
   [anndata-mapping.md](anndata-mapping.md).

Because `checks/__init__.py` imports every check submodule (registering
them as an import side effect), a new check module must be added to that
file's import list to be picked up by `orchestrator.run_checks()` and, by
extension, `validate()` and the CLI.

## Adding a schema

1. Add a new YAML file under `schema/resources/`, following the shape
   described in [schemas.md](schemas.md).
2. Register its filename in `schema/loader.py`'s builtin-schema lookup so
   `cp-validate schema list`/`show` and `load_schema("your-name")` find it.
3. Add a test in `tests/test_schema_loader.py` (or a new module) confirming
   it loads and resolves against a representative synthetic fixture.
4. If the schema is derived from a specific external convention (like
   `jump-cp`), document that provenance in a new `docs/<name>-derivation.md`
   file, citing primary sources — see
   [jump-cp-derivation.md](jump-cp-derivation.md) as a template.

## The argv shim

`typer`/`click` cannot mix a bare top-level positional argument with
subcommands in the same command tree. Since the CLI needs both
`cp-validate experiment.h5ad` (bare path) and `cp-validate schema list`
(subcommand) to work, `cli/app.py` exposes an explicit `validate`
subcommand internally, and the `main()` console-script entry point
rewrites `sys.argv` to insert `"validate"` before Click parses it, whenever
the first token isn't already a known subcommand, a help/version flag, or
an option. See `apply_argv_shim()` in
[`src/cp_anndata_validator/cli/app.py`](../src/cp_anndata_validator/cli/app.py)
and its dedicated tests in `tests/test_cli.py`.

## Testing conventions

- Synthetic fixtures live in `tests/fixtures/synthetic.py` and cover
  `single-cell`, `well`, and `treatment` profiles, in both dense and sparse
  form, with realistic `.uns` metadata. Prefer extending these over
  building bespoke AnnData objects per test.
- Loading/sampling tests use spy objects to assert that no full-matrix
  materialization (`.toarray()`, full `[:]` slicing) occurs for sparse or
  backed input — keep that guarantee intact when touching `loading.py` or
  `sampling.py`.
- Check registry state is global by design (for `orchestrator.run_checks()`
  to work simply); tests that register fake checks must restore the
  registry afterward via `checks/registry.py`'s `clear_registry()` /
  `restore_registry()` helpers (see `tests/test_orchestrator.py`).
