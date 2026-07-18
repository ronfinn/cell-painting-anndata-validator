"""Tests for check orchestration, using fake checks rather than the real catalogue."""

from __future__ import annotations

from pathlib import Path

import pytest

from cp_anndata_validator.checks.registry import (
    Check,
    CheckContext,
    clear_registry,
    register_check,
    restore_registry,
)
from cp_anndata_validator.loading import AnnDataHandle
from cp_anndata_validator.models.issue import Category, Issue, Severity
from cp_anndata_validator.models.report import InputFileInfo
from cp_anndata_validator.orchestrator import build_report, run_checks
from cp_anndata_validator.profiles import ProfileLevel, ProfileLevelResult
from cp_anndata_validator.schema.loader import load_builtin_schema
from cp_anndata_validator.schema.resolve import resolve_schema
from tests.fixtures.synthetic import make_single_cell_adata


def make_context() -> CheckContext:
    adata = make_single_cell_adata(n_obs=6)
    handle = AnnDataHandle(adata=adata, path=Path("fake.h5ad"), size_bytes=0, backed=False)
    schema = load_builtin_schema("generic-cell-painting")
    resolved = resolve_schema(adata.obs, adata.var, schema)
    profile = ProfileLevelResult(
        detected=ProfileLevel.SINGLE_CELL,
        confidence=1.0,
        candidates=(ProfileLevel.SINGLE_CELL,),
        explanation="test fixture",
    )
    return CheckContext(handle=handle, resolved_schema=resolved, profile=profile)


def make_issue(code: str = "FAKE001", check_name: str = "fake_check") -> Issue:
    return Issue(
        code=code,
        severity=Severity.WARNING,
        category=Category.STRUCTURE,
        location="obs.fake",
        message="fake issue",
        remediation="none needed",
        check_name=check_name,
    )


def test_run_checks_collects_issues_from_all_applicable_checks() -> None:
    ctx = make_context()
    checks = [
        Check(name="a", category=Category.STRUCTURE, run=lambda c: [make_issue("A001", "a")]),
        Check(name="b", category=Category.METADATA, run=lambda c: [make_issue("B001", "b")]),
    ]

    issues, executions = run_checks(ctx, checks)

    assert {issue.code for issue in issues} == {"A001", "B001"}
    assert {execution.name for execution in executions} == {"a", "b"}
    assert all(execution.status == "executed" for execution in executions)


def test_run_checks_skips_non_applicable_checks() -> None:
    ctx = make_context()
    checks = [
        Check(
            name="never_applies",
            category=Category.STRUCTURE,
            run=lambda c: [make_issue()],
            applies=lambda c: False,
        )
    ]

    issues, executions = run_checks(ctx, checks)

    assert issues == []
    assert executions[0].status == "skipped"
    assert executions[0].reason is not None
    assert "not applicable" in executions[0].reason


def test_run_checks_isolates_a_check_that_raises() -> None:
    ctx = make_context()

    def _boom(c: CheckContext) -> list[Issue]:
        raise RuntimeError("boom")

    checks = [
        Check(name="broken", category=Category.STRUCTURE, run=_boom),
        Check(
            name="healthy",
            category=Category.METADATA,
            run=lambda c: [make_issue("H001", "healthy")],
        ),
    ]

    issues, executions = run_checks(ctx, checks)

    codes = {issue.code for issue in issues}
    assert "ENGINE001" in codes
    assert "H001" in codes
    engine_issue = next(issue for issue in issues if issue.code == "ENGINE001")
    assert engine_issue.check_name == "broken"
    assert "boom" in (engine_issue.evidence or "")
    assert {e.status for e in executions} == {"executed"}


def test_run_checks_isolates_an_applies_function_that_raises() -> None:
    ctx = make_context()

    def _boom(c: CheckContext) -> bool:
        raise RuntimeError("applies boom")

    checks = [
        Check(name="broken_applies", category=Category.STRUCTURE, run=lambda c: [], applies=_boom)
    ]

    issues, executions = run_checks(ctx, checks)

    assert issues[0].code == "ENGINE001"
    assert executions[0].status == "executed"


def test_run_checks_orders_issues_by_severity_then_category_then_code() -> None:
    ctx = make_context()
    checks = [
        Check(
            name="mixed",
            category=Category.STRUCTURE,
            run=lambda c: [
                Issue(
                    code="Z999",
                    severity=Severity.INFORMATION,
                    category=Category.STRUCTURE,
                    location="x",
                    message="info",
                    remediation="none",
                    check_name="mixed",
                ),
                Issue(
                    code="A001",
                    severity=Severity.ERROR,
                    category=Category.STRUCTURE,
                    location="x",
                    message="error",
                    remediation="none",
                    check_name="mixed",
                ),
                Issue(
                    code="M001",
                    severity=Severity.WARNING,
                    category=Category.STRUCTURE,
                    location="x",
                    message="warning",
                    remediation="none",
                    check_name="mixed",
                ),
            ],
        )
    ]

    issues, _ = run_checks(ctx, checks)

    assert [issue.code for issue in issues] == ["A001", "M001", "Z999"]


def test_run_checks_defaults_to_global_registry() -> None:
    snapshot = clear_registry()
    try:

        @register_check(name="registered_fake", category=Category.STRUCTURE)
        def _fake(ctx: CheckContext) -> list[Issue]:
            return [make_issue("R001", "registered_fake")]

        ctx = make_context()
        issues, executions = run_checks(ctx)

        assert [issue.code for issue in issues] == ["R001"]
        assert [e.name for e in executions] == ["registered_fake"]
    finally:
        restore_registry(snapshot)


def make_report_kwargs(issues: list[Issue]) -> dict[str, object]:
    return {
        "schema_id": "generic-cell-painting",
        "schema_version": "1.0.0",
        "input_file": InputFileInfo(path="x.h5ad", size_bytes=1, format="h5ad", backed=False),
        "profile_level": ProfileLevelResult(detected=ProfileLevel.SINGLE_CELL, explanation=""),
        "issues": issues,
        "checks": [],
    }


def test_build_report_passes_with_only_warnings_when_not_strict() -> None:
    report = build_report(**make_report_kwargs([make_issue()]), strict=False)  # type: ignore[arg-type]
    assert report.status == "pass"


def test_build_report_fails_with_warnings_when_strict() -> None:
    report = build_report(**make_report_kwargs([make_issue()]), strict=True)  # type: ignore[arg-type]
    assert report.status == "fail"


def test_build_report_fails_with_any_error_regardless_of_strict() -> None:
    error_issue = Issue(
        code="E001",
        severity=Severity.ERROR,
        category=Category.STRUCTURE,
        location="x",
        message="bad",
        remediation="fix it",
        check_name="x",
    )
    report = build_report(**make_report_kwargs([error_issue]), strict=False)  # type: ignore[arg-type]
    assert report.status == "fail"


def test_build_report_passes_with_no_issues() -> None:
    report = build_report(**make_report_kwargs([]), strict=True)  # type: ignore[arg-type]
    assert report.status == "pass"


@pytest.fixture(autouse=True)
def _isolate_check_registry() -> None:
    """Ensure a fake check registered mid-test never leaks into other test modules."""
    snapshot = clear_registry()
    yield
    restore_registry(snapshot)
