# Security Policy

## Supported versions

`cp-anndata-validator` is in **public beta** (`0.2.0b1`). Security fixes are
applied on the `main` branch. This section will be updated when stable release
lines are maintained.

## Reporting a vulnerability

Please report suspected vulnerabilities **privately**. Do **not** open a
public issue for a security problem.

- Preferred: GitHub Security Advisories →
  https://github.com/ronfinn/cell-painting-anndata-validator/security/advisories/new

Include a description, reproduction steps, affected version/commit, and
environment details. We will acknowledge the report and keep you informed.

## What is not a security vulnerability

Ordinary **validation findings** (missing identifiers, provenance warnings,
feature-name issues, fail status, exit code `1`) are not security reports.
File those as bugs or questions using the public issue templates.

## Scope notes

In scope examples:

- Path traversal or unexpected filesystem writes when given hostile paths
- Unsafe handling of untrusted schema YAML or AnnData metadata in HTML reports
- Dependency vulnerabilities that affect this package’s runtime

Out of scope examples:

- “My dataset failed validation”
- Requests to bypass checks or fabricate metadata
- Issues that require attaching proprietary datasets to diagnose
