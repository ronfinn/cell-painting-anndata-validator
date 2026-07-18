"""Independent validation checks, grouped by category.

Importing this package imports every built-in check submodule, which
registers their checks (via ``@register_check``) in the global registry.

Note: this file intentionally omits ``from __future__ import annotations``,
since importing the ``annotations`` check submodule below would otherwise
collide with that future-import's own module-level ``annotations`` binding.
"""

from cp_anndata_validator.checks import (
    aggregation,
    ai_readiness,
    annotations,
    features,
    identifiers,
    matrix,
    metadata,
    profile_consistency,
    provenance,
    schema_meta,
    structure,
)

__all__ = [
    "aggregation",
    "ai_readiness",
    "annotations",
    "features",
    "identifiers",
    "matrix",
    "metadata",
    "profile_consistency",
    "provenance",
    "schema_meta",
    "structure",
]
