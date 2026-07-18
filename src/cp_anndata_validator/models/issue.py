"""Structured validation issue model.

Every validation check returns a list of :class:`Issue` objects instead of
printing. Renderers and the orchestrator are the only consumers of this
structure.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class Severity(StrEnum):
    """How serious a validation issue is."""

    ERROR = "error"
    WARNING = "warning"
    INFORMATION = "information"


class Category(StrEnum):
    """The validation category an issue (or check) belongs to."""

    STRUCTURE = "structure"
    IDENTIFIERS = "identifiers"
    PROFILE = "profile"
    ANNOTATIONS = "annotations"
    FEATURES = "features"
    MATRIX = "matrix"
    SLOT_SEMANTICS = "slot_semantics"
    METADATA = "metadata"
    PROVENANCE_IMAGE = "provenance_image"
    PROVENANCE_SEGMENTATION = "provenance_segmentation"
    PROVENANCE_FEATURE_EXTRACTION = "provenance_feature_extraction"
    SCHEMA = "schema"
    LICENCE = "licence"
    AGGREGATION = "aggregation"
    AI_READINESS = "ai_readiness"
    ENGINE = "engine"


class Issue(BaseModel):
    """A single, structured validation finding.

    ``code`` is a stable rule code (for example ``"IDENT003"``) that must
    never be renumbered or reused once shipped. ``location`` should point at
    an AnnData path such as ``"obs.plate_id"``, ``"var.index"`` or
    ``"uns.provenance"``.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    code: str = Field(min_length=1)
    severity: Severity
    category: Category
    location: str = Field(min_length=1)
    message: str = Field(min_length=1)
    evidence: str | None = None
    remediation: str = Field(min_length=1)
    check_name: str = Field(min_length=1)
