# Security

Security vulnerabilities and ordinary validation findings are different.

| Kind | Channel |
|---|---|
| Suspected **security vulnerability** (unsafe parsing, path handling, HTML injection in reports, dependency exploit, …) | Private advisory — see repository-root `SECURITY.md` |
| Validation **finding** (`IDENTxxx`, missing provenance, …) | Public issue or discussion; not a security report |
| Support / how-do-I questions | [Support](support.md) |

This package reads local AnnData and schema files and does not send dataset
contents to external services. Treat file paths and custom schema YAML as
untrusted input when validating data from others.
