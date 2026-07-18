"""Validation orchestration: run every applicable check and assemble a Report."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Literal

from cp_anndata_validator.checks.registry import Check, CheckContext, iter_checks
from cp_anndata_validator.models.issue import Category, Issue, Severity
from cp_anndata_validator.models.report import CheckExecution, InputFileInfo, IssueCounts, Report
from cp_anndata_validator.profiles import ProfileLevelResult
from cp_anndata_validator.version import __version__

_SEVERITY_ORDER: dict[Severity, int] = {
    Severity.ERROR: 0,
    Severity.WARNING: 1,
    Severity.INFORMATION: 2,
}

_MAX_ENGINE_EVIDENCE_LENGTH = 500


def _engine_issue(check_name: str, detail: str) -> Issue:
    """Build the single, stable-coded issue used when a check misbehaves.

    One failing check must never abort the whole validation run; instead its
    failure is captured as an ``ENGINE001`` error issue.
    """
    return Issue(
        code="ENGINE001",
        severity=Severity.ERROR,
        category=Category.ENGINE,
        location="<engine>",
        message=(
            f"Check {check_name!r} failed unexpectedly; its result was replaced with this "
            "issue so the rest of the validation run could continue."
        ),
        evidence=detail[:_MAX_ENGINE_EVIDENCE_LENGTH],
        remediation="Please report this as a defect in cp-anndata-validator.",
        check_name=check_name,
    )


def run_checks(
    ctx: CheckContext, checks: Sequence[Check] | None = None
) -> tuple[list[Issue], list[CheckExecution]]:
    """Run every applicable check in ``checks`` (default: the global registry).

    Returns ``(issues, check_executions)``. Issues are sorted deterministically
    by ``(severity, category, code, location)``. A check that is not
    applicable to the current profile level is recorded as skipped rather
    than run; a check that raises is recorded as executed but contributes a
    single ``ENGINE001`` issue instead of propagating the exception.
    """
    selected = list(checks) if checks is not None else iter_checks()
    issues: list[Issue] = []
    executions: list[CheckExecution] = []

    for check in selected:
        try:
            applicable = check.applies(ctx)
        except Exception as exc:  # noqa: BLE001 - isolate a misbehaving check
            issues.append(_engine_issue(check.name, f"applicability check raised: {exc}"))
            executions.append(CheckExecution(name=check.name, status="executed"))
            continue

        if not applicable:
            executions.append(
                CheckExecution(
                    name=check.name,
                    status="skipped",
                    reason=f"not applicable to profile level {ctx.profile.effective}",
                )
            )
            continue

        try:
            found = check.run(ctx)
        except Exception as exc:  # noqa: BLE001 - isolate a misbehaving check
            issues.append(_engine_issue(check.name, str(exc)))
            executions.append(CheckExecution(name=check.name, status="executed"))
            continue

        issues.extend(found)
        executions.append(CheckExecution(name=check.name, status="executed"))

    issues.sort(
        key=lambda issue: (
            _SEVERITY_ORDER[issue.severity],
            issue.category.value,
            issue.code,
            issue.location,
        )
    )
    return issues, executions


def build_report(
    *,
    schema_id: str,
    schema_version: str,
    input_file: InputFileInfo,
    profile_level: ProfileLevelResult,
    issues: list[Issue],
    checks: list[CheckExecution],
    strict: bool = False,
) -> Report:
    """Assemble the final, structured :class:`Report` from orchestration results.

    ``strict`` only changes the pass/fail threshold (warnings count as
    failures under strict mode); it never mutates issue severities.
    """
    counts = IssueCounts.from_issues(issues)
    has_errors = counts.by_severity.get(Severity.ERROR, 0) > 0
    has_warnings = counts.by_severity.get(Severity.WARNING, 0) > 0
    status: Literal["pass", "fail"] = "fail" if has_errors or (strict and has_warnings) else "pass"

    return Report(
        package_version=__version__,
        schema_id=schema_id,
        schema_version=schema_version,
        input_file=input_file,
        profile_level=profile_level,
        executed_at=datetime.now(UTC),
        status=status,
        counts=counts,
        issues=tuple(issues),
        checks=tuple(checks),
    )
