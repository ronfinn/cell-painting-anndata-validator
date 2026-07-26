# Contributing to cp-anndata-validator

Thanks for considering a contribution. This is a small, focused validator —
please open an issue to discuss anything beyond a small fix or a new check/
schema before investing significant time, so we can agree on scope first.

## Quick start

```bash
git clone https://github.com/ronfinn/cell-painting-anndata-validator.git
cd cell-painting-anndata-validator
uv sync --all-groups             # runtime + dev + docs groups
uv run pytest                    # run the test suite
uv run ruff check .              # lint
uv run ruff format --check .     # verify formatting (uv run ruff format . to fix)
uv run mypy src                  # type-check the package
uv run mkdocs build --strict     # documentation site
uv build                         # build sdist + wheel into dist/
```

CI (`.github/workflows/ci.yml`) runs the quality suite across supported Python
versions and builds the docs once (not per matrix entry).

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
- **Community standards.** See [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md).

## Where things live, and how to extend them

See [`docs/project/contributing.md`](docs/project/contributing.md) for:

- the full repository layout and architecture,
- step-by-step instructions for **adding a new check** (with a rule code)
  or **adding a new built-in schema**,
- testing conventions (fixtures, registry isolation, sparse/backed spies),
- why the CLI needs an `argv` shim.

Also see [`docs/schemas/rule-catalogue.md`](docs/schemas/rule-catalogue.md)
(the rule-code catalogue) and
[`docs/project/limitations.md`](docs/project/limitations.md) (documented gaps —
check there before assuming something is a bug).

Architecture decisions already embodied in the code are recorded under
[`docs/decisions/`](docs/decisions/).

## Pull requests

- Keep PRs focused: one check, one schema, or one bug fix per PR is easier
  to review than a bundle.
- Add or update tests for every behavioral change — this repo has no
  untested check.
- Update `docs/schemas/rule-catalogue.md` (and `CHANGELOG.md`, under
  "Unreleased") for any new/changed rule code or user-visible behavior.
- Describe *why* the change is needed, not just what it does.
- Use the pull request template checklist.

## Reporting bugs / requesting checks

Use the GitHub issue forms. Include:

- the `cp-anndata-validator` version (`cp-validate --version`),
- schema name, profile level and relevant rule codes,
- a minimal **synthetic** reproducing AnnData shape (obs/var columns, `uns`
  keys — not private data), and
- the command/API call and its actual vs. expected output.

Schema/alias requests need public evidence and precedence implications — use
the dedicated issue form.

## Release checklist (pre-publish)

Run before tagging or publishing a release. Do **not** publish to PyPI from
automation without an explicit human decision.

```bash
uv sync --all-groups
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run mkdocs build --strict
uv build
uv run cp-validate --version          # must match pyproject.toml / CITATION.cff
uv run cp-validate --help
uv run cp-validate schema list
uv run cp-validate schema show generic-cell-painting
uv run cp-validate schema show jump-cp
git diff --check
bash scripts/smoke_wheel.sh           # isolated wheel install + CLI smoke (temp venv)
git ls-files '*.h5ad'                 # must be empty
```

Also confirm manually:

- [ ] Package version in `pyproject.toml` and `CITATION.cff` match
      `uv run cp-validate --version`.
- [ ] Built-in schema versions remain independent (currently
      `schema_version: "0.2.1"`) — do not confuse them with the package version.
- [ ] `CHANGELOG.md` has an entry for this version; wheel contains schemas,
      HTML template and `py.typed`.
- [ ] No `.h5ad` binaries are tracked (`git ls-files '*.h5ad'` is empty).
- [ ] Mark GitHub prereleases appropriately for beta tags.
- [ ] PyPI publication remains a separate, deliberate decision.

## Code of conduct

See [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md).
