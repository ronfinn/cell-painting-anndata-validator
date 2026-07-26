# Schemas and checks

Schemas declare which canonical fields, aliases, compartments and measurement
families a dataset should satisfy. Checks emit stable rule codes when those
expectations are not met.

| Page | Contents |
|---|---|
| [Built-in schemas](built-in.md) | `generic-cell-painting` and `jump-cp` (both at schema version `0.2.1`) |
| [Custom schema format](custom.md) | YAML shape, validation of unknown keys |
| [Alias resolution and precedence](aliases.md) | Exact matching, declaration order, field conflicts |
| [Rule catalogue](rule-catalogue.md) | Stable rule codes, severities and remediations |

Schemas never contain executable code. They are loaded with `yaml.safe_load`
only. Package version (`0.2.0b1`) and schema versions are independent — see
[Schema and package versioning](../concepts/versioning.md).
