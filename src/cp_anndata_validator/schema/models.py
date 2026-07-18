"""Pydantic models describing a versioned, data-driven validation schema."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from cp_anndata_validator.profiles import ProfileLevel


class FieldSpec(BaseModel):
    """A single canonical semantic field and the column aliases that satisfy it."""

    model_config = ConfigDict(extra="forbid")

    aliases: list[str] = Field(min_length=1)
    location: Literal["obs", "var"] = "obs"
    required_for: list[ProfileLevel] = Field(default_factory=list)
    description: str = ""


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

    def fields_required_for(self, profile_level: ProfileLevel) -> dict[str, FieldSpec]:
        return {
            name: spec for name, spec in self.fields.items() if profile_level in spec.required_for
        }
