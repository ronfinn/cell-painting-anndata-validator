"""Schema identifier/version and dataset licence checks."""

from __future__ import annotations

from cp_anndata_validator.checks.registry import CheckContext, register_check
from cp_anndata_validator.models.issue import Category, Issue, Severity


@register_check(name="schema_metadata_declared", category=Category.SCHEMA)
def check_schema_metadata_declared(ctx: CheckContext) -> list[Issue]:
    """The dataset should self-declare which schema and version it targets."""
    uns = ctx.handle.adata.uns
    issues: list[Issue] = []

    schema_id = uns.get("schema_id") if hasattr(uns, "get") else None
    if not schema_id:
        issues.append(
            Issue(
                code="SCHEMA001",
                severity=Severity.WARNING,
                category=Category.SCHEMA,
                location="uns.schema_id",
                message="No schema identifier (uns['schema_id']) is declared on the dataset.",
                evidence=None,
                remediation=(
                    "Record uns['schema_id'] so downstream tools know which schema this "
                    "dataset targets."
                ),
                check_name="schema_metadata_declared",
            )
        )

    schema_version = uns.get("schema_version") if hasattr(uns, "get") else None
    if not schema_version:
        issues.append(
            Issue(
                code="SCHEMA002",
                severity=Severity.WARNING,
                category=Category.SCHEMA,
                location="uns.schema_version",
                message="No schema version (uns['schema_version']) is declared on the dataset.",
                evidence=None,
                remediation="Record uns['schema_version'] alongside uns['schema_id'].",
                check_name="schema_metadata_declared",
            )
        )

    return issues


@register_check(name="dataset_licence_declared", category=Category.LICENCE)
def check_dataset_licence_declared(ctx: CheckContext) -> list[Issue]:
    """The dataset should declare a licence, checking both spellings of the key."""
    uns = ctx.handle.adata.uns
    licence = None
    if hasattr(uns, "get"):
        licence = uns.get("licence") or uns.get("license")
    if licence:
        return []

    return [
        Issue(
            code="LICENSE001",
            severity=Severity.WARNING,
            category=Category.LICENCE,
            location="uns.licence",
            message="No dataset licence (uns['licence'] or uns['license']) is declared.",
            evidence=None,
            remediation="Record the dataset's licence in uns['licence'].",
            check_name="dataset_licence_declared",
        )
    ]
