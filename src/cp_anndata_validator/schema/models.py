"""Pydantic models describing a versioned, data-driven validation schema."""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from cp_anndata_validator.profiles import ProfileLevel

_SEMVER_RE = re.compile(
    r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$",
)


class FieldSpec(BaseModel):
    """A single canonical semantic field and the column aliases that satisfy it."""

    model_config = ConfigDict(extra="forbid")

    aliases: list[str] = Field(min_length=1)
    location: Literal["obs", "var"] = "obs"
    required_for: list[ProfileLevel] = Field(default_factory=list)
    description: str = ""

    @field_validator("aliases")
    @classmethod
    def _reject_duplicate_aliases(cls, aliases: list[str]) -> list[str]:
        seen: dict[str, str] = {}
        for alias in aliases:
            key = alias.strip().lower()
            if key in seen:
                raise ValueError(
                    f"duplicate alias {alias!r} (case-insensitive clash with {seen[key]!r})"
                )
            seen[key] = alias
        return aliases


class SchemaDefinition(BaseModel):
    """A versioned, data-driven schema: canonical fields, aliases and compartments.

    Unknown top-level or per-field keys are rejected (``extra="forbid"``)
    rather than silently ignored, so configuration mistakes in a schema file
    surface immediately.
    """

    model_config = ConfigDict(extra="forbid")

    schema_id: str = Field(min_length=1)
    schema_version: str = Field(min_length=1)
    description: str = ""
    fields: dict[str, FieldSpec] = Field(default_factory=dict)
    compartments: list[str] = Field(default_factory=list)
    measurement_families: list[str] = Field(default_factory=list)

    @field_validator("schema_version")
    @classmethod
    def _require_semver(cls, version: str) -> str:
        if not _SEMVER_RE.match(version):
            raise ValueError(
                f"schema_version {version!r} is not a valid semantic version "
                "(expected MAJOR.MINOR.PATCH, e.g. '0.1.0')"
            )
        return version

    @model_validator(mode="after")
    def _reject_aliases_reused_across_fields(self) -> SchemaDefinition:
        owner_by_alias: dict[str, str] = {}
        for field_name, spec in self.fields.items():
            for alias in spec.aliases:
                key = alias.strip().lower()
                owner = owner_by_alias.get(key)
                if owner is not None and owner != field_name:
                    raise ValueError(
                        f"alias {alias!r} is used by both {owner!r} and {field_name!r} "
                        "fields; each alias must resolve to exactly one canonical field"
                    )
                owner_by_alias[key] = field_name
        return self

    def fields_required_for(self, profile_level: ProfileLevel) -> dict[str, FieldSpec]:
        return {
            name: spec for name, spec in self.fields.items() if profile_level in spec.required_for
        }
