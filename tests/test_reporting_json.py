"""Tests for JSON report rendering."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from cp_anndata_validator.models.issue import Category, Issue, Severity
from cp_anndata_validator.models.report import (
    CheckExecution,
    InputFileInfo,
    IssueCounts,
    Report,
)
from cp_anndata_validator.profiles import ProfileLevel, ProfileLevelResult
from cp_anndata_validator.reporting.json_renderer import render_json


def make_report() -> Report:
    issue = Issue(
        code="IDENT001",
        severity=Severity.ERROR,
        category=Category.IDENTIFIERS,
        location="obs.plate_id",
        message="Missing plate identifier column.",
        evidence="0 of 3 candidate aliases found",
        remediation="Add a plate identifier column.",
        check_name="identifier_completeness",
    )
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
        status="fail",
        counts=IssueCounts.from_issues([issue]),
        issues=(issue,),
        checks=(CheckExecution(name="identifier_completeness", status="executed"),),
    )


def test_render_json_produces_valid_parseable_json() -> None:
    report = make_report()
    payload = json.loads(render_json(report))
    assert payload["schema_id"] == "generic-cell-painting"
    assert payload["status"] == "fail"
    assert payload["issues"][0]["code"] == "IDENT001"
    assert payload["issues"][0]["severity"] == "error"
    assert payload["profile_level"]["declared"] == "single-cell"


def test_render_json_round_trips_to_the_same_report() -> None:
    report = make_report()
    restored = Report.model_validate_json(render_json(report))
    assert restored == report


def test_render_json_indent_none_is_compact() -> None:
    report = make_report()
    compact = render_json(report, indent=None)
    pretty = render_json(report, indent=2)
    assert "\n" not in compact
    assert "\n" in pretty
    assert json.loads(compact) == json.loads(pretty)


def test_render_json_is_stable_across_calls() -> None:
    report = make_report()
    assert render_json(report) == render_json(report)
