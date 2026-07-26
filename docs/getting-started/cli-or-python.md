# Choosing CLI or Python

| Need | Prefer |
|---|---|
| One-off validation in a shell or CI job | CLI (`cp-validate`) |
| Embed validation in a Python pipeline | `validate()` |
| Custom rendering or programmatic filtering of issues | Python API + `reporting` helpers |
| Inspect built-in schemas quickly | CLI `schema list` / `schema show` |

Both surfaces share the same engine, schemas, rule codes and exit semantics.
The CLI is a thin Typer wrapper around `validate()` plus the console/JSON/HTML
renderers.

See [CLI reference](../reference/cli.md) and [Python API](../reference/python-api.md).
