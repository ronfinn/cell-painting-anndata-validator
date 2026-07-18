# Contributing to cp-anndata-validator

Thanks for considering a contribution. This is a small, focused validator —
please open an issue to discuss anything beyond a small fix or a new check/
schema before investing significant time, so we can agree on scope first.

## Quick start

```bash
git clone https://github.com/<org>/cp-anndata-validator.git
cd cp-anndata-validator
uv sync                          # install/lock dependencies (dev group included)
uv run pytest                    # run the test suite
uv run ruff check .              # lint
uv run ruff format --check .     # verify formatting (uv run ruff format . to fix)
uv run mypy src                  # type-check the package
uv build                         # build sdist + wheel into dist/
```

All five commands above must pass before a change is considered done — this
is exactly what CI (`.github/workflows/ci.yml`) runs on every push and pull
request, across every supported Python version.

## Ground rules

- **No dataset conversion.** This package validates AnnData; it does not
  convert CellProfiler/DeepProfiler/CytoTable outputs into AnnData. Changes
  that add conversion logic are out of scope.
- **Read-only.** Nothing in this package writes to, mutates, or "fixes" the
  input `.h5ad` file. Keep it that way.
- **Sparse/backed-safe.** Never call `.toarray()`/`.todense()` on a full
  matrix. Numeric checks must work via bounded sampling or `.data`-level
  inspection on sparse input — see `sampling.py` and its tests.
- **Structured results, not printing.** A check returns `list[Issue]`; it
  never prints, logs, or raises for an expected validation failure.
- **Stable rule codes.** A shipped code's meaning never changes and is never
  reused for something else later. If you remove a check, retire its code.
- **No large or binary fixtures.** Generate small synthetic AnnData
  programmatically in tests (see `tests/fixtures/synthetic.py`) and in
  `examples/generate_examples.py`. Don't commit `.h5ad`/`.json`/`.html`
  files — they're `.gitignore`d for a reason.
- **No secrets, no network calls in tests.** The test suite must run fully
  offline.

## Where things live, and how to extend them

See [`docs/contributing.md`](docs/contributing.md) for:

- the full repository layout and architecture,
- step-by-step instructions for **adding a new check** (with a rule code)
  or **adding a new built-in schema**,
- testing conventions (fixtures, registry isolation, sparse/backed spies),
- why the CLI needs an `argv` shim.

Also see [`docs/checks.md`](docs/checks.md) (the rule-code catalogue you'll
be adding to) and [`docs/limitations.md`](docs/limitations.md) (documented
v0.1 gaps — check there before assuming something is a bug).

## Pull requests

- Keep PRs focused: one check, one schema, or one bug fix per PR is easier
  to review than a bundle.
- Add or update tests for every behavioral change — this repo has no
  untested check.
- Update `docs/checks.md` (and `CHANGELOG.md`, under "Unreleased") for any
  new/changed rule code or user-visible behavior.
- Describe *why* the change is needed, not just what it does.

## Reporting bugs / requesting checks

Open an issue with:

- the `cp-anndata-validator` version (`pip show cp-anndata-validator` or
  `cp_anndata_validator.__version__`),
- a minimal reproducing AnnData shape (obs/var columns, `uns` keys — not the
  actual data, if sensitive), and
- the command/API call and its actual vs. expected output.

## Code of conduct

Be respectful and assume good faith. Disagreements about scope or design
are fine and expected; personal attacks are not.
