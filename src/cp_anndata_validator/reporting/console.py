"""Human-readable console rendering of a Report, using Rich.

Rendering always targets an in-memory buffer with ``force_terminal=False``
and ``color_system=None``, so the output is plain text regardless of
whether a real TTY is attached -- this keeps rendering deterministic for
tests and for piped/redirected output.
"""

from __future__ import annotations

import io

from rich.console import Console
from rich.table import Table
from rich.text import Text

from cp_anndata_validator.models.issue import Severity
from cp_anndata_validator.models.report import Report

_SEVERITY_STYLES: dict[Severity, str] = {
    Severity.ERROR: "bold red",
    Severity.WARNING: "yellow",
    Severity.INFORMATION: "cyan",
}

_DEFAULT_WIDTH = 120


def render_console(report: Report, *, width: int = _DEFAULT_WIDTH) -> str:
    """Render a Report as plain text suitable for terminal or log output."""
    buffer = io.StringIO()
    console = Console(file=buffer, width=width, force_terminal=False, color_system=None)

    console.print(f"[bold]cp-anndata-validator[/bold] v{report.package_version}")
    backed_label = "backed" if report.input_file.backed else "in-memory"
    console.print(f"Input: {report.input_file.path} ({report.input_file.format}, {backed_label})")
    console.print(f"Schema: {report.schema_id} v{report.schema_version}")

    profile = report.profile_level
    effective = profile.effective.value if profile.effective else "unknown"
    declared = profile.declared.value if profile.declared else "none"
    detected = profile.detected.value if profile.detected else "none"
    console.print(f"Profile level: {effective} (declared={declared}, detected={detected})")
    console.print()

    if not report.issues:
        console.print("[bold green]No issues found.[/bold green]")
    else:
        table = Table(title="Issues")
        for column in ("Severity", "Code", "Category", "Location", "Message"):
            table.add_column(column)
        for issue in report.issues:
            style = _SEVERITY_STYLES.get(issue.severity, "")
            table.add_row(
                Text(issue.severity.value, style=style),
                issue.code,
                issue.category.value,
                issue.location,
                issue.message,
            )
        console.print(table)

    console.print()
    severity_summary = ", ".join(
        f"{severity.value}={count}"
        for severity, count in sorted(report.counts.by_severity.items(), key=lambda kv: kv[0].value)
    )
    total = sum(report.counts.by_severity.values())
    console.print(
        f"Counts: {total} issue(s)" + (f" -- {severity_summary}" if severity_summary else "")
    )

    status_style = "bold green" if report.status == "pass" else "bold red"
    console.print(Text(f"Status: {report.status.upper()}", style=status_style))

    return buffer.getvalue()
