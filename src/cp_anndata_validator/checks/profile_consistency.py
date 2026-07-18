"""Checks that relate the resolved schema to the declared/detected profile level."""

from __future__ import annotations

from cp_anndata_validator.checks.registry import CheckContext, register_check
from cp_anndata_validator.models.issue import Category, Issue, Severity


@register_check(name="profile_level_requirements", category=Category.PROFILE)
def check_profile_level_requirements(ctx: CheckContext) -> list[Issue]:
    """The effective (declared, else detected) profile level's requirements must be met."""
    level = ctx.profile.effective
    if level is None:
        return []

    missing = ctx.resolved_schema.missing_required_fields(level)
    if not missing:
        return []

    return [
        Issue(
            code="PROFILE001",
            severity=Severity.ERROR,
            category=Category.PROFILE,
            location="obs",
            message=(
                f"The {level.value} profile level requires field(s) "
                f"{', '.join(sorted(missing))}, which could not be resolved."
            ),
            evidence=ctx.profile.explanation or None,
            remediation=(
                "Add the missing identifier column(s), or select a different --profile-level."
            ),
            check_name="profile_level_requirements",
        )
    ]


@register_check(name="profile_level_ambiguity", category=Category.PROFILE)
def check_profile_level_ambiguity(ctx: CheckContext) -> list[Issue]:
    """Auto-detection may legitimately be ambiguous; surface it as information, not silence."""
    if not ctx.profile.is_ambiguous:
        return []

    candidates = ", ".join(candidate.value for candidate in ctx.profile.candidates)
    return [
        Issue(
            code="PROFILE002",
            severity=Severity.INFORMATION,
            category=Category.PROFILE,
            location="obs",
            message=f"Profile level auto-detection was ambiguous between: {candidates}.",
            evidence=ctx.profile.explanation or None,
            remediation="Pass --profile-level explicitly to disambiguate.",
            check_name="profile_level_ambiguity",
        )
    ]


@register_check(name="profile_level_declared_vs_detected", category=Category.PROFILE)
def check_profile_level_declared_vs_detected(ctx: CheckContext) -> list[Issue]:
    """Warn when a CLI-declared profile level disagrees with what was auto-detected."""
    declared = ctx.profile.declared
    detected = ctx.profile.detected
    if declared is None or detected is None or declared == detected:
        return []

    return [
        Issue(
            code="PROFILE003",
            severity=Severity.WARNING,
            category=Category.PROFILE,
            location="obs",
            message=(
                f"Declared profile level {declared.value!r} does not match the "
                f"auto-detected level {detected.value!r}."
            ),
            evidence=ctx.profile.explanation or None,
            remediation="Confirm --profile-level is correct for this dataset.",
            check_name="profile_level_declared_vs_detected",
        )
    ]
