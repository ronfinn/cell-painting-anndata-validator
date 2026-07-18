"""Tests for self-contained HTML report rendering."""

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
from cp_anndata_validator.reporting.html_renderer import render_html


def make_report(issues: list[Issue]) -> Report:
    return Report(
        package_version="0.1.0",
        schema_id="generic-cell-painting",
        schema_version="1.0.0",
        input_file=InputFileInfo(
            path="experiment.h5ad", size_bytes=2048, format="h5ad", backed=False
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


def make_issue(message: str = "Missing plate identifier column.") -> Issue:
    return Issue(
        code="IDENT001",
        severity=Severity.ERROR,
        category=Category.IDENTIFIERS,
        location="obs.plate_id",
        message=message,
        remediation="Add a plate identifier column.",
        check_name="identifier_completeness",
    )


def test_render_html_produces_a_self_contained_document() -> None:
    html = render_html(make_report([make_issue()]))
    assert html.strip().startswith("<!doctype html>")
    assert "<html" in html
    assert "</html>" in html
    assert "<style>" in html  # CSS is inline, not a separate file/asset


def test_render_html_shows_no_issues_message_when_clean() -> None:
    html = render_html(make_report([]))
    assert "No issues found." in html
    assert "<table>" not in html
    assert "status-pass" in html


def test_render_html_shows_issue_table_when_present() -> None:
    html = render_html(make_report([make_issue()]))
    assert "<table>" in html
    assert "IDENT001" in html
    assert "status-fail" in html


def test_render_html_escapes_untrusted_issue_content() -> None:
    malicious_message = "<script>alert('xss')</script>"
    html = render_html(make_report([make_issue(message=malicious_message)]))
    assert "<script>alert" not in html
    assert "&lt;script&gt;" in html


def test_render_html_is_deterministic() -> None:
    report = make_report([make_issue()])
    assert render_html(report) == render_html(report)
