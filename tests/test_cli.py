"""Tests for the cp-validate CLI: argv shim, exit codes, --report, and schema commands."""

from __future__ import annotations

import importlib
import json
import re
from pathlib import Path

import pytest
from typer.testing import CliRunner

from cp_anndata_validator.cli.app import app, apply_argv_shim
from cp_anndata_validator.version import __version__
from tests.fixtures.synthetic import make_single_cell_adata, make_well_level_adata, write_h5ad

# `cp_anndata_validator.cli` re-exports the `app` *attribute* from this submodule under
# the same name the submodule itself has, which clobbers the parent package's automatic
# `cli.app -> module` binding. `importlib.import_module` reads straight from `sys.modules`
# and sidesteps that attribute-traversal footgun, unlike `import cp_anndata_validator.cli.app`.
cli_app = importlib.import_module("cp_anndata_validator.cli.app")

# Rich 15+ with force_terminal (triggered by GITHUB_ACTIONS + TERM env vars) applies
# per-span ANSI codes that can split a "--option" name across two escape sequences,
# e.g. "\x1b[1;36m-\x1b[0m\x1b[1;36m-version\x1b[0m", making bare substring
# search unreliable.  Strip codes before any assertion on option presence.
_ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*[mGKHFABCDsu]")


def _strip_ansi(text: str) -> str:
    return _ANSI_ESCAPE_RE.sub("", text)


runner = CliRunner()


def test_argv_shim_inserts_validate_for_a_bare_path() -> None:
    assert apply_argv_shim(["experiment.h5ad"]) == ["validate", "experiment.h5ad"]


def test_argv_shim_inserts_validate_before_options() -> None:
    assert apply_argv_shim(["experiment.h5ad", "--strict"]) == [
        "validate",
        "experiment.h5ad",
        "--strict",
    ]


def test_argv_shim_leaves_known_subcommands_unchanged() -> None:
    assert apply_argv_shim(["schema", "list"]) == ["schema", "list"]
    assert apply_argv_shim(["validate", "experiment.h5ad"]) == ["validate", "experiment.h5ad"]


def test_argv_shim_leaves_help_and_option_first_tokens_unchanged() -> None:
    assert apply_argv_shim(["--help"]) == ["--help"]
    assert apply_argv_shim(["--version"]) == ["--version"]
    assert apply_argv_shim(["-q", "experiment.h5ad"]) == ["-q", "experiment.h5ad"]


def test_argv_shim_handles_empty_argv() -> None:
    assert apply_argv_shim([]) == []


def test_validate_command_exits_zero_for_a_clean_dataset(tmp_path: Path) -> None:
    path = write_h5ad(make_single_cell_adata(), tmp_path)
    result = runner.invoke(app, ["validate", str(path)])
    assert result.exit_code == 0
    assert "Status: PASS" in result.output


def test_bare_path_invocation_works_through_the_shim(tmp_path: Path) -> None:
    path = write_h5ad(make_single_cell_adata(), tmp_path)
    argv = apply_argv_shim([str(path)])
    result = runner.invoke(app, argv)
    assert result.exit_code == 0


def test_validate_command_exits_one_for_a_dataset_with_errors(tmp_path: Path) -> None:
    adata = make_single_cell_adata()
    adata.obs = adata.obs.drop(columns=["cell_id"])
    path = write_h5ad(adata, tmp_path)

    result = runner.invoke(app, ["validate", str(path), "--profile-level", "single-cell"])

    assert result.exit_code == 1
    assert "Status: FAIL" in result.output


def test_validate_command_exits_two_for_a_missing_file(tmp_path: Path) -> None:
    result = runner.invoke(app, ["validate", str(tmp_path / "missing.h5ad")])
    assert result.exit_code == 2
    assert "does not exist" in result.output


def test_validate_command_exits_two_for_an_unknown_schema(tmp_path: Path) -> None:
    path = write_h5ad(make_single_cell_adata(), tmp_path)
    result = runner.invoke(app, ["validate", str(path), "--schema", "not-a-real-schema"])
    assert result.exit_code == 2


def test_validate_command_exits_two_for_an_unexpected_execution_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A bug/crash outside the orchestrator's own exception isolation is a usage-level
    failure (exit 2), not a validation failure (exit 1) -- the run never reached a verdict."""

    def _boom(*args: object, **kwargs: object) -> None:
        raise RuntimeError("simulated unexpected failure")

    monkeypatch.setattr(cli_app, "run_validate", _boom)
    path = write_h5ad(make_single_cell_adata(), tmp_path)

    result = runner.invoke(app, ["validate", str(path)])

    assert result.exit_code == 2
    assert "Unexpected internal error" in result.output


def test_validate_command_supports_the_schema_option(tmp_path: Path) -> None:
    path = write_h5ad(make_well_level_adata(), tmp_path)
    result = runner.invoke(app, ["validate", str(path), "--schema", "jump-cp"])
    assert result.exit_code == 0
    assert "jump-cp" in result.output


def test_validate_command_strict_turns_warnings_into_failures(tmp_path: Path) -> None:
    adata = make_single_cell_adata()
    del adata.uns["licence"]  # produces a warning-level LICENSE001 issue only
    path = write_h5ad(adata, tmp_path)

    lenient = runner.invoke(app, ["validate", str(path)])
    strict = runner.invoke(app, ["validate", str(path), "--strict"])

    assert lenient.exit_code == 0
    assert strict.exit_code == 1


def test_validate_command_quiet_suppresses_console_output(tmp_path: Path) -> None:
    path = write_h5ad(make_single_cell_adata(), tmp_path)
    result = runner.invoke(app, ["validate", str(path), "--quiet"])
    assert result.exit_code == 0
    assert result.stdout == ""


def test_validate_command_writes_json_report(tmp_path: Path) -> None:
    path = write_h5ad(make_single_cell_adata(), tmp_path)
    report_path = tmp_path / "report.json"

    result = runner.invoke(app, ["validate", str(path), "--report", str(report_path)])

    assert result.exit_code == 0
    payload = json.loads(report_path.read_text())
    assert payload["status"] == "pass"


def test_validate_command_writes_html_report(tmp_path: Path) -> None:
    path = write_h5ad(make_single_cell_adata(), tmp_path)
    report_path = tmp_path / "report.html"

    result = runner.invoke(app, ["validate", str(path), "--report", str(report_path)])

    assert result.exit_code == 0
    content = report_path.read_text()
    assert content.strip().startswith("<!doctype html>")


def test_validate_command_refuses_to_overwrite_an_existing_report(tmp_path: Path) -> None:
    path = write_h5ad(make_single_cell_adata(), tmp_path)
    report_path = tmp_path / "report.json"
    report_path.write_text("pre-existing content")

    result = runner.invoke(app, ["validate", str(path), "--report", str(report_path)])

    assert result.exit_code == 2
    assert "already exists" in result.output
    assert report_path.read_text() == "pre-existing content"


def test_validate_command_force_allows_overwriting_an_existing_report(tmp_path: Path) -> None:
    path = write_h5ad(make_single_cell_adata(), tmp_path)
    report_path = tmp_path / "report.json"
    report_path.write_text("pre-existing content")

    result = runner.invoke(app, ["validate", str(path), "--report", str(report_path), "--force"])

    assert result.exit_code == 0
    payload = json.loads(report_path.read_text())
    assert payload["status"] == "pass"


def test_validate_command_rejects_unsupported_report_extension(tmp_path: Path) -> None:
    path = write_h5ad(make_single_cell_adata(), tmp_path)
    result = runner.invoke(app, ["validate", str(path), "--report", str(tmp_path / "report.txt")])
    assert result.exit_code == 2


def test_validate_command_declared_profile_level(tmp_path: Path) -> None:
    path = write_h5ad(make_single_cell_adata(), tmp_path)
    result = runner.invoke(app, ["validate", str(path), "--profile-level", "single-cell"])
    assert result.exit_code == 0
    assert "declared=single-cell" in result.stdout


def test_schema_list_command_lists_builtin_schemas() -> None:
    result = runner.invoke(app, ["schema", "list"])
    assert result.exit_code == 0
    assert "generic-cell-painting" in result.stdout
    assert "jump-cp" in result.stdout


def test_schema_show_command_describes_a_schema() -> None:
    result = runner.invoke(app, ["schema", "show", "jump-cp"])
    assert result.exit_code == 0
    assert "jump-cp v0.2.1" in result.stdout
    assert "Metadata_Plate" in result.stdout


def test_schema_show_command_exits_two_for_unknown_schema() -> None:
    result = runner.invoke(app, ["schema", "show", "not-a-real-schema"])
    assert result.exit_code == 2


def test_top_level_help_lists_both_subcommands() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "validate" in result.stdout
    assert "schema" in result.stdout


def test_version_option_prints_installed_version_and_exits_zero() -> None:
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert result.stdout.strip() == __version__


def test_version_option_needs_no_subcommand_or_dataset_path() -> None:
    """--version is eager, so it must short-circuit before the otherwise-required
    subcommand (and its dataset argument) is resolved."""
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert "Missing command" not in result.output
    assert "Usage:" not in result.output


def test_version_option_is_listed_in_top_level_help() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "--version" in _strip_ansi(result.stdout)
