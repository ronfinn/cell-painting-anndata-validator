"""Resolve a schema's canonical fields against an AnnData object's actual columns."""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from cp_anndata_validator.profiles import ProfileLevel
from cp_anndata_validator.schema.models import SchemaDefinition


@dataclass(frozen=True)
class ResolvedField:
    """The outcome of resolving one canonical field against actual columns."""

    canonical_name: str
    column: str | None
    matched_alias: str | None

    @property
    def resolved(self) -> bool:
        return self.column is not None


@dataclass(frozen=True)
class ResolvedSchema:
    """A schema together with the outcome of matching its fields to one AnnData object."""

    schema: SchemaDefinition
    fields: dict[str, ResolvedField] = field(default_factory=dict)

    def is_resolved(self, canonical_name: str) -> bool:
        resolved_field = self.fields.get(canonical_name)
        return resolved_field is not None and resolved_field.resolved

    def column_for(self, canonical_name: str) -> str | None:
        resolved_field = self.fields.get(canonical_name)
        return resolved_field.column if resolved_field is not None else None

    def missing_required_fields(self, level: ProfileLevel) -> list[str]:
        return [
            name for name in self.schema.fields_required_for(level) if not self.is_resolved(name)
        ]


def _canonicalize(name: str) -> str:
    return name.strip().lower()


def resolve_schema(
    obs: pd.DataFrame, var: pd.DataFrame, schema: SchemaDefinition
) -> ResolvedSchema:
    """Match each of a schema's canonical fields against actual ``.obs``/``.var`` columns.

    Matching is case-insensitive and exact after trimming whitespace. There
    is no regex or fuzzy aliasing in v0.1, to avoid ambiguous or surprising
    matches.
    """
    obs_lookup = {_canonicalize(c): c for c in obs.columns}
    var_lookup = {_canonicalize(c): c for c in var.columns}

    resolved: dict[str, ResolvedField] = {}
    for canonical_name, spec in schema.fields.items():
        lookup = obs_lookup if spec.location == "obs" else var_lookup
        column: str | None = None
        matched_alias: str | None = None
        for alias in spec.aliases:
            key = _canonicalize(alias)
            if key in lookup:
                column = lookup[key]
                matched_alias = alias
                break
        resolved[canonical_name] = ResolvedField(
            canonical_name=canonical_name, column=column, matched_alias=matched_alias
        )

    return ResolvedSchema(schema=schema, fields=resolved)
