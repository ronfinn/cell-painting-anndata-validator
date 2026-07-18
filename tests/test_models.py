"""Tests for the structured Issue and Report models."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from cp_anndata_validator.models import (
    Category,
    CheckExecution,
    InputFileInfo,
    Issue,
    IssueCounts,
    ProfileLevelResult,
    Report,
    Severity,
)
from cp_anndata_validator.profiles import ProfileLevel


def make_issue(
    code: str = "IDENT001",
    severity: Severity = Severity.ERROR,
    category: Category = Category.IDENTIFIERS,
) -> Issue:
    return Issue(
        code=code,
        severity=severity,
        category=category,
        location="obs.plate_id",
        message="Missing plate identifier column.",
        evidence="0 of 3 candidate aliases found",
        remediation="Add a plate identifier column such as Metadata_Plate.",
        check_name="identifier_completeness",
    )


def test_issue_round_trips_through_json() -> None:
    issue = make_issue()
    restored = Issue.model_validate_json(issue.model_dump_json())
    assert restored == issue


def test_issue_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        Issue.model_validate({**make_issue().model_dump(), "unexpected": "value"})


def test_issue_rejects_invalid_severity() -> None:
    with pytest.raises(ValidationError):
        Issue.model_validate({**make_issue().model_dump(), "severity": "critical"})


def test_issue_is_frozen() -> None:
    issue = make_issue()
    with pytest.raises(ValidationError):
        issue.message = "changed"  # type: ignore[misc]


def test_issue_counts_from_issues() -> None:
    issues = [
        make_issue(code="IDENT001", severity=Severity.ERROR),
        make_issue(code="IDENT002", severity=Severity.ERROR),
        make_issue(code="CTRL001", severity=Severity.WARNING, category=Category.ANNOTATIONS),
    ]
    counts = IssueCounts.from_issues(issues)
    assert counts.by_severity[Severity.ERROR] == 2
    assert counts.by_severity[Severity.WARNING] == 1
    assert counts.by_category[Category.IDENTIFIERS] == 2


def test_profile_level_result_effective_prefers_declared() -> None:
    result = ProfileLevelResult(
        declared=ProfileLevel.WELL,
        detected=ProfileLevel.SINGLE_CELL,
        confidence=0.4,
        explanation="declared overrides detected",
    )
    assert result.effective == ProfileLevel.WELL
    assert result.is_ambiguous is False


def test_profile_level_result_ambiguous_when_multiple_candidates() -> None:
    result = ProfileLevelResult(
        declared=None,
        detected=None,
        candidates=(ProfileLevel.WELL, ProfileLevel.TREATMENT),
        explanation="both well and treatment identifiers are present",
    )
    assert result.is_ambiguous is True
    assert result.effective is None


def make_report(issues: list[Issue]) -> Report:
    return Report(
        package_version="0.1.0",
        schema_id="generic-cell-painting",
        schema_version="1.0.0",
        input_file=InputFileInfo(
            path="experiment.h5ad", size_bytes=1024, format="h5ad", backed=False
        ),
        profile_level=ProfileLevelResult(
            declared=ProfileLevel.SINGLE_CELL,
            detected=ProfileLevel.SINGLE_CELL,
            confidence=1.0,
            explanation="all required single-cell identifiers were resolved",
        ),
        executed_at=datetime(2026, 1, 1, tzinfo=UTC),
        status="fail" if issues else "pass",
        counts=IssueCounts.from_issues(issues),
        issues=tuple(issues),
        checks=(CheckExecution(name="identifier_completeness", status="executed"),),
    )


def test_report_round_trips_through_json() -> None:
    report = make_report([make_issue()])
    restored = Report.model_validate_json(report.model_dump_json())
    assert restored == report


def test_report_has_errors_and_warnings() -> None:
    report = make_report([make_issue(severity=Severity.WARNING)])
    assert report.has_errors() is False
    assert report.has_warnings() is True


def test_report_rejects_unknown_fields() -> None:
    report = make_report([])
    with pytest.raises(ValidationError):
        Report.model_validate({**report.model_dump(), "unexpected": "value"})
