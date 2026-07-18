"""JSON rendering of a Report.

This is a thin, stable wrapper around Pydantic's own JSON serialization:
enum members serialize to their string value, ``datetime`` serializes to
ISO-8601, and field order matches the model's declaration order.
"""

from __future__ import annotations

from cp_anndata_validator.models.report import Report


def render_json(report: Report, *, indent: int | None = 2) -> str:
    """Render a Report as a JSON document."""
    return report.model_dump_json(indent=indent)
