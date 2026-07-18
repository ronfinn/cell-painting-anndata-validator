"""The check registry: how independent validation checks are declared and discovered.

A check is a small, named unit of validation logic scoped to one
:class:`~cp_anndata_validator.models.issue.Category`. It receives a
:class:`CheckContext` and returns a list of
:class:`~cp_anndata_validator.models.issue.Issue` objects -- it never prints
and never raises for ordinary validation findings (only genuinely
unexpected/programmer errors should propagate, and even those are caught by
the orchestrator rather than aborting the whole run).
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

from cp_anndata_validator.loading import AnnDataHandle
from cp_anndata_validator.models.issue import Category, Issue
from cp_anndata_validator.profiles import ProfileLevelResult
from cp_anndata_validator.sampling import DEFAULT_SAMPLE_ROWS
from cp_anndata_validator.schema.resolve import ResolvedSchema

CheckFn = Callable[["CheckContext"], list[Issue]]
AppliesFn = Callable[["CheckContext"], bool]


@dataclass(frozen=True)
class CheckContext:
    """Everything a check needs, bundled once by the orchestrator."""

    handle: AnnDataHandle
    resolved_schema: ResolvedSchema
    profile: ProfileLevelResult
    sample_rows: int = DEFAULT_SAMPLE_ROWS


@dataclass(frozen=True)
class Check:
    """A registered validation check."""

    name: str
    category: Category
    run: CheckFn
    applies: AppliesFn = field(default=lambda ctx: True)


_REGISTRY: list[Check] = []


def register_check(
    *, name: str, category: Category, applies: AppliesFn = lambda ctx: True
) -> Callable[[CheckFn], CheckFn]:
    """Decorator that registers a function as a check.

    Example::

        @register_check(name="index_uniqueness", category=Category.STRUCTURE)
        def check_index_uniqueness(ctx: CheckContext) -> list[Issue]:
            ...
    """

    def decorator(func: CheckFn) -> CheckFn:
        _REGISTRY.append(Check(name=name, category=category, run=func, applies=applies))
        return func

    return decorator


def iter_checks() -> list[Check]:
    """All registered checks, sorted by ``(category, name)`` for deterministic ordering."""
    return sorted(_REGISTRY, key=lambda check: (check.category.value, check.name))


def clear_registry() -> Sequence[Check]:
    """Remove and return all currently registered checks (primarily for test isolation)."""
    snapshot = list(_REGISTRY)
    _REGISTRY.clear()
    return snapshot


def restore_registry(checks: Sequence[Check]) -> None:
    """Restore a previously cleared registry snapshot."""
    _REGISTRY.clear()
    _REGISTRY.extend(checks)
