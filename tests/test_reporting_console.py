"""Tests for console report rendering (must work identically without a TTY)."""

from __future__ import annotations

from datetime import UTC, datetime

from cp_anndata_validator.models.issue import Category, Issue, Severity
from cp_anndata_validator.models.report import (
    CheckExecution,
    InputFileInfo,
    IssueCounts,
    Report,
)
from cp_anndata_validator.profiles import ProfileLevel, ProfileLevelResult
from cp_anndata_validator.reporting.console import render_console


def make_report(issues: list[Issue]) -> Report:
    return Report(
        package_version="0.1.0",
        schema_id="generic-cell-painting",
        schema_version="1.0.0",
        input_file=InputFileInfo(
            path="experiment.h5ad", size_bytes=2048, format="h5ad", backed=True
        ),
        profile_level=ProfileLevelResult(
            declared=ProfileLevel.SINGLE_CELL,
            detected=ProfileLevel.SINGLE_CELL,
            confidence=1.0,
            explanation="test",
        ),
        executed_at=datetime(2026, 1, 1, tzinfo=UTC),
        status="fail" if issues else "pass",
        counts=IssueCounts.from_issues(issues),
        issues=tuple(issues),
        checks=(CheckExecution(name="identifier_completeness", status="executed"),),
    )


def make_issue() -> Issue:
    return Issue(
        code="IDENT001",
        severity=Severity.ERROR,
        category=Category.IDENTIFIERS,
        location="obs.plate_id",
        message="Missing plate identifier column.",
        remediation="Add a plate identifier column.",
        check_name="identifier_completeness",
    )


def test_render_console_contains_no_ansi_escape_codes() -> None:
    output = render_console(make_report([make_issue()]))
    assert "\x1b" not in output


def test_render_console_shows_schema_and_profile_info() -> None:
    output = render_console(make_report([]))
    assert "generic-cell-painting" in output
    assert "single-cell" in output
    assert "backed" in output


def test_render_console_shows_no_issues_message_when_clean() -> None:
    output = render_console(make_report([]))
    assert "No issues found." in output
    assert "Status: PASS" in output


def test_render_console_shows_issue_details_and_fail_status() -> None:
    output = render_console(make_report([make_issue()]))
    assert "IDENT001" in output
    assert "Missing plate identifier column." in output
    assert "Status: FAIL" in output


def test_render_console_is_deterministic() -> None:
    report = make_report([make_issue()])
    assert render_console(report) == render_console(report)
