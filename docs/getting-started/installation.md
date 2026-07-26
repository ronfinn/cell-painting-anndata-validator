# Installation

Requires **Python 3.12+**. The project uses [`uv`](https://docs.astral.sh/uv/)
for development; `pip` works for installing a built wheel.

## From a local clone (recommended while beta)

```bash
git clone https://github.com/ronfinn/cell-painting-anndata-validator.git
cd cell-painting-anndata-validator
uv sync
uv run cp-validate --version
```

## From a local wheel

```bash
uv build
uv pip install dist/cp_anndata_validator-*.whl
cp-validate --version
```

Or with an isolated smoke script that builds, installs into a temporary
environment, and exercises the CLI:

```bash
bash scripts/smoke_wheel.sh
```

## Names

| Role | Name |
|---|---|
| Distribution / PyPI name | `cp-anndata-validator` |
| Import package | `cp_anndata_validator` |
| CLI entry point | `cp-validate` |
| GitHub repository | `ronfinn/cell-painting-anndata-validator` |

## Verify schemas

```bash
uv run cp-validate schema list
uv run cp-validate schema show generic-cell-painting
uv run cp-validate schema show jump-cp
```

Both built-in schemas should report version **`0.2.1`**.
