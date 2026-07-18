"""Tests for schema model validation and YAML loading."""

from __future__ import annotations

from pathlib import Path

import pytest

from cp_anndata_validator.profiles import ProfileLevel
from cp_anndata_validator.schema import SchemaError, load_schema
from cp_anndata_validator.schema.loader import list_builtin_schema_names, load_builtin_schema
from cp_anndata_validator.schema.models import SchemaDefinition


@pytest.mark.parametrize("name", ["generic-cell-painting", "jump-cp"])
def test_builtin_schemas_load_and_validate(name: str) -> None:
    schema = load_builtin_schema(name)
    assert isinstance(schema, SchemaDefinition)
    assert schema.schema_id == name
    assert schema.schema_version
    assert "plate" in schema.fields
    assert "well" in schema.fields


def test_list_builtin_schema_names_is_sorted() -> None:
    assert list_builtin_schema_names() == ["generic-cell-painting", "jump-cp"]


def test_load_schema_dispatches_builtin_by_name() -> None:
    schema = load_schema("jump-cp")
    assert schema.schema_id == "jump-cp"


def test_generic_schema_requires_plate_and_well_for_single_cell_and_well_levels() -> None:
    schema = load_builtin_schema("generic-cell-painting")
    for level in (ProfileLevel.SINGLE_CELL, ProfileLevel.WELL):
        required = schema.fields_required_for(level)
        assert "plate" in required
        assert "well" in required
    assert "plate" not in schema.fields_required_for(ProfileLevel.TREATMENT)


def test_generic_schema_requires_cell_id_only_for_single_cell() -> None:
    schema = load_builtin_schema("generic-cell-painting")
    assert "cell_id" in schema.fields_required_for(ProfileLevel.SINGLE_CELL)
    assert "cell_id" not in schema.fields_required_for(ProfileLevel.WELL)
    assert "cell_id" not in schema.fields_required_for(ProfileLevel.TREATMENT)


def test_jump_cp_uses_metadata_prefixed_aliases() -> None:
    schema = load_builtin_schema("jump-cp")
    assert "Metadata_Plate" in schema.fields["plate"].aliases
    assert "Metadata_JCP2022" in schema.fields["perturbation_id"].aliases


def test_load_schema_from_path_reads_custom_file(tmp_path: Path) -> None:
    custom = tmp_path / "custom.yaml"
    custom.write_text(
        """
        schema_id: custom-test
        schema_version: "0.1.0"
        fields:
          plate:
            aliases: [plate_id]
            location: obs
            required_for: [well]
        """
    )
    schema = load_schema(custom)
    assert schema.schema_id == "custom-test"
    assert schema.fields["plate"].required_for == [ProfileLevel.WELL]


def test_unknown_builtin_schema_name_raises_schema_error() -> None:
    with pytest.raises(SchemaError, match="Unknown built-in schema"):
        load_builtin_schema("not-a-real-schema")


def test_missing_schema_file_raises_schema_error(tmp_path: Path) -> None:
    with pytest.raises(SchemaError, match="does not exist"):
        load_schema(tmp_path / "missing.yaml")


def test_malformed_yaml_raises_schema_error(tmp_path: Path) -> None:
    bogus = tmp_path / "bad.yaml"
    bogus.write_text("schema_id: [unterminated\nfields: {")
    with pytest.raises(SchemaError, match="not valid YAML"):
        load_schema(bogus)


def test_non_mapping_yaml_raises_schema_error(tmp_path: Path) -> None:
    bogus = tmp_path / "list.yaml"
    bogus.write_text("- just\n- a\n- list\n")
    with pytest.raises(SchemaError, match="mapping"):
        load_schema(bogus)


def test_unknown_top_level_key_is_rejected(tmp_path: Path) -> None:
    bogus = tmp_path / "unknown_key.yaml"
    bogus.write_text(
        """
        schema_id: bad-schema
        schema_version: "1.0.0"
        fields: {}
        this_key_does_not_exist: true
        """
    )
    with pytest.raises(SchemaError, match="invalid"):
        load_schema(bogus)


def test_unknown_field_level_key_is_rejected(tmp_path: Path) -> None:
    bogus = tmp_path / "unknown_field_key.yaml"
    bogus.write_text(
        """
        schema_id: bad-schema
        schema_version: "1.0.0"
        fields:
          plate:
            aliases: [plate_id]
            location: obs
            not_a_real_key: true
        """
    )
    with pytest.raises(SchemaError, match="invalid"):
        load_schema(bogus)


def test_invalid_profile_level_in_required_for_is_rejected(tmp_path: Path) -> None:
    bogus = tmp_path / "bad_profile_level.yaml"
    bogus.write_text(
        """
        schema_id: bad-schema
        schema_version: "1.0.0"
        fields:
          plate:
            aliases: [plate_id]
            location: obs
            required_for: [colony-level]
        """
    )
    with pytest.raises(SchemaError, match="invalid"):
        load_schema(bogus)


def test_directory_as_schema_path_raises_schema_error(tmp_path: Path) -> None:
    directory = tmp_path / "schema_dir.yaml"
    directory.mkdir()
    with pytest.raises(SchemaError, match="not a file"):
        load_schema(directory)
