"""The ``cp-validate`` command line interface.

Typer/Click cannot mix a top-level positional argument with subcommands, so
a bare invocation like ``cp-validate experiment.h5ad`` needs the hidden
default subcommand name (``validate``) inserted before Click parses argv.
:func:`main` (the console-script entry point) applies this shim; the
``app`` object itself always requires an explicit subcommand.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated

import typer

from cp_anndata_validator.api import validate as run_validate
from cp_anndata_validator.loading import LoadError
from cp_anndata_validator.models.report import Report
from cp_anndata_validator.profiles import ProfileLevel
from cp_anndata_validator.reporting import render_console, render_html, render_json
from cp_anndata_validator.sampling import DEFAULT_SAMPLE_ROWS
from cp_anndata_validator.schema.loader import (
    SchemaError,
    list_builtin_schema_names,
    load_builtin_schema,
)

app = typer.Typer(
    name="cp-validate",
    help="Validate the semantic correctness, metadata completeness, provenance, and "
    "AI readiness of Cell Painting AnnData datasets.",
    no_args_is_help=True,
    add_completion=False,
)

schema_app = typer.Typer(name="schema", help="Inspect built-in validation schemas.")
app.add_typer(schema_app, name="schema")

_EXIT_OK = 0
_EXIT_VALIDATION_FAILED = 1
_EXIT_USAGE_ERROR = 2
_EXIT_INTERNAL_ERROR = 3

_KNOWN_SUBCOMMANDS = {"validate", "schema"}
_PASSTHROUGH_TOKENS = {"--help", "-h", "--version"}


def apply_argv_shim(argv: list[str]) -> list[str]:
    """Insert the default ``validate`` subcommand when the first token is a dataset path.

    Left unchanged when ``argv`` is empty, already starts with a known
    subcommand, is a help/version flag, or looks like an option (starts with
    ``-``) -- only a bare positional first token gets the shim applied.
    """
    if not argv:
        return argv
    first = argv[0]
    if first in _KNOWN_SUBCOMMANDS or first in _PASSTHROUGH_TOKENS or first.startswith("-"):
        return argv
    return ["validate", *argv]


def _write_report_file(report: Report, path: Path, *, force: bool) -> None:
    suffix = path.suffix.lower()
    if suffix == ".json":
        content = render_json(report)
    elif suffix in (".html", ".htm"):
        content = render_html(report)
    else:
        typer.echo(
            f"Error: unsupported --report extension {suffix!r}; use .json or .html", err=True
        )
        raise typer.Exit(code=_EXIT_USAGE_ERROR)

    if path.exists() and not force:
        typer.echo(
            f"Error: --report path {path} already exists; pass --force to overwrite it",
            err=True,
        )
        raise typer.Exit(code=_EXIT_USAGE_ERROR)

    path.write_text(content, encoding="utf-8")


@app.command(name="validate")
def validate_command(
    path: Annotated[Path, typer.Argument(help="Path to the .h5ad file to validate.")],
    schema: Annotated[
        str,
        typer.Option(
            "--schema", help="Built-in schema name, or a path to a custom schema YAML file."
        ),
    ] = "generic-cell-painting",
    profile_level: Annotated[
        ProfileLevel | None,
        typer.Option(
            "--profile-level", help="Declare the profile level, overriding auto-detection."
        ),
    ] = None,
    report: Annotated[
        Path | None,
        typer.Option(
            "--report", help="Write a report to this path (.json or .html, inferred from suffix)."
        ),
    ] = None,
    backed: Annotated[
        bool | None,
        typer.Option(
            "--backed/--no-backed",
            help="Force backed or in-memory loading (default: auto-select by file size).",
        ),
    ] = None,
    sample_rows: Annotated[
        int,
        typer.Option("--sample-rows", help="Maximum rows sampled for numeric/AI-readiness checks."),
    ] = DEFAULT_SAMPLE_ROWS,
    strict: Annotated[
        bool, typer.Option("--strict", help="Treat warnings as failures (exit code 1).")
    ] = False,
    quiet: Annotated[
        bool,
        typer.Option("--quiet", "-q", help="Suppress console output (--report still writes)."),
    ] = False,
    force: Annotated[
        bool,
        typer.Option("--force", help="Allow --report to overwrite an existing file."),
    ] = False,
) -> None:
    """Validate one AnnData dataset and print (and optionally write) a report."""
    try:
        result = run_validate(
            path,
            schema=schema,
            profile_level=profile_level,
            backed=backed,
            sample_rows=sample_rows,
            strict=strict,
        )
    except (LoadError, SchemaError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=_EXIT_USAGE_ERROR) from exc
    except Exception as exc:  # noqa: BLE001 - safety net; checks are isolated by the orchestrator
        typer.echo(f"Unexpected internal error: {exc}", err=True)
        raise typer.Exit(code=_EXIT_INTERNAL_ERROR) from exc

    if not quiet:
        typer.echo(render_console(result))

    if report is not None:
        _write_report_file(result, report, force=force)

    raise typer.Exit(code=_EXIT_OK if result.status == "pass" else _EXIT_VALIDATION_FAILED)


@schema_app.command(name="list")
def schema_list_command() -> None:
    """List the names of every built-in schema."""
    for name in list_builtin_schema_names():
        typer.echo(name)


@schema_app.command(name="show")
def schema_show_command(
    name: Annotated[str, typer.Argument(help="Built-in schema name (see `schema list`).")],
) -> None:
    """Show a built-in schema's canonical fields, aliases, and profile-level requirements."""
    try:
        schema_definition = load_builtin_schema(name)
    except SchemaError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=_EXIT_USAGE_ERROR) from exc

    typer.echo(f"{schema_definition.schema_id} v{schema_definition.schema_version}")
    if schema_definition.description:
        typer.echo(schema_definition.description.strip())
    typer.echo()

    for field_name, spec in schema_definition.fields.items():
        required_for = ", ".join(level.value for level in spec.required_for) or "optional"
        typer.echo(f"- {field_name} ({spec.location}, required for: {required_for})")
        typer.echo(f"    aliases: {', '.join(spec.aliases)}")

    if schema_definition.compartments:
        typer.echo()
        typer.echo(f"compartments: {', '.join(schema_definition.compartments)}")


def main() -> None:
    """Console-script entry point: applies the argv shim, then runs the Typer app."""
    sys.argv[1:] = apply_argv_shim(sys.argv[1:])
    app()
