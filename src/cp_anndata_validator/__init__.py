"""cp-anndata-validator: validate Cell Painting datasets stored as AnnData.

The primary entry point is :func:`validate`, which returns a structured
:class:`Report`. See ``cp_anndata_validator.reporting`` for console/JSON/HTML
renderers, and the ``cp-validate`` CLI for a ready-made command-line tool.
"""

from __future__ import annotations

from cp_anndata_validator.api import validate
from cp_anndata_validator.loading import LoadError
from cp_anndata_validator.models.issue import Category, Issue, Severity
from cp_anndata_validator.models.report import Report
from cp_anndata_validator.profiles import ProfileLevel
from cp_anndata_validator.schema.loader import SchemaError
from cp_anndata_validator.version import __version__

__all__ = [
    "Category",
    "Issue",
    "LoadError",
    "ProfileLevel",
    "Report",
    "SchemaError",
    "Severity",
    "__version__",
    "validate",
]
