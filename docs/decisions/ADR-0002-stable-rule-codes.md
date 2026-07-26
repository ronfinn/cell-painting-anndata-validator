# ADR-0002 — Stable validation rule codes

- **Status:** Accepted
- **Date:** 2026-07 (as embodied in the 0.2.0b1 codebase)

## Context

Downstream CI and documentation need durable identifiers for findings, not
unstable free-text messages alone.

## Decision

Every issue carries a stable code (for example `IDENT001`, `AGG001`).
Shipped codes keep their meaning; codes are not reused for different
findings; removed checks retire their codes.

## Consequences

- The [Rule catalogue](../schemas/rule-catalogue.md) must be updated with
  every new code.
- Message wording may improve without changing the code’s meaning.

## Alternatives considered

- Message-only findings — rejected for automation and changelogability.
- Auto-generated opaque IDs — rejected as unreadable in reviews.

## References

- `src/cp_anndata_validator/models/issue.py`
- `docs/schemas/rule-catalogue.md`
- Check modules under `src/cp_anndata_validator/checks/`
