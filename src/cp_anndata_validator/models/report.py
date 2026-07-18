"""Structured validation report model."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from cp_anndata_validator.models.issue import Category, Issue, Severity
from cp_anndata_validator.profiles import ProfileLevelResult

__all__ = [
    "CheckExecution",
    "InputFileInfo",
    "IssueCounts",
    "ProfileLevelResult",
    "Report",
]


class InputFileInfo(BaseModel):
    """Information about the dataset that was validated."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    path: str
    size_bytes: int = Field(ge=0)
    format: str
    backed: bool


class CheckExecution(BaseModel):
    """A record of whether a registered check ran or was skipped, and why."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    status: Literal["executed", "skipped"]
    reason: str | None = None


class IssueCounts(BaseModel):
    """Issue counts broken down by severity and by category."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    by_severity: dict[Severity, int] = Field(default_factory=dict)
    by_category: dict[Category, int] = Field(default_factory=dict)

    @classmethod
    def from_issues(cls, issues: list[Issue]) -> IssueCounts:
        by_severity: dict[Severity, int] = {}
        by_category: dict[Category, int] = {}
        for issue in issues:
            by_severity[issue.severity] = by_severity.get(issue.severity, 0) + 1
            by_category[issue.category] = by_category.get(issue.category, 0) + 1
        return cls(by_severity=by_severity, by_category=by_category)


class Report(BaseModel):
    """The complete, structured result of validating one AnnData dataset."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    package_version: str
    schema_id: str
    schema_version: str
    input_file: InputFileInfo
    profile_level: ProfileLevelResult
    executed_at: datetime
    status: Literal["pass", "fail"]
    counts: IssueCounts
    issues: tuple[Issue, ...]
    checks: tuple[CheckExecution, ...]

    def has_errors(self) -> bool:
        return self.counts.by_severity.get(Severity.ERROR, 0) > 0

    def has_warnings(self) -> bool:
        return self.counts.by_severity.get(Severity.WARNING, 0) > 0
