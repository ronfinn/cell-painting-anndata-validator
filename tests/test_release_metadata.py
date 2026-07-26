"""Focused release-metadata checks for the current package/schema versions."""

from __future__ import annotations

import tomllib
from pathlib import Path

from typer.testing import CliRunner

import cp_anndata_validator
from cp_anndata_validator.cli.app import app
from cp_anndata_validator.schema.loader import list_builtin_schema_names, load_builtin_schema

EXPECTED_PACKAGE_VERSION = "0.2.0b1"
EXPECTED_SCHEMA_VERSION = "0.2.1"

runner = CliRunner()
_ROOT = Path(__file__).resolve().parents[1]


def test_package_dunder_version_matches_release_candidate() -> None:
    assert cp_anndata_validator.__version__ == EXPECTED_PACKAGE_VERSION


def test_pyproject_version_matches_package_version() -> None:
    data = tomllib.loads((_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert data["project"]["version"] == EXPECTED_PACKAGE_VERSION
    assert data["project"]["version"] == cp_anndata_validator.__version__


def test_citation_cff_version_matches_package_version() -> None:
    text = (_ROOT / "CITATION.cff").read_text(encoding="utf-8")
    assert f'version: "{EXPECTED_PACKAGE_VERSION}"' in text


def test_cli_version_prints_package_version_and_exits_zero() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert result.stdout.strip() == EXPECTED_PACKAGE_VERSION


def test_builtin_schemas_remain_at_schema_version_0_2_1() -> None:
    names = list_builtin_schema_names()
    assert names == ["generic-cell-painting", "jump-cp"]
    for name in names:
        schema = load_builtin_schema(name)
        assert schema.schema_version == EXPECTED_SCHEMA_VERSION
