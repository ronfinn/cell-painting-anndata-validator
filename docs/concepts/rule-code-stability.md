# Rule-code stability

Every issue has a stable code such as `IDENT001` or `AGG001`.

Contract for this beta line:

- A shipped code’s **meaning does not change**.
- A code is **not reused** for a different finding later.
- If a check is removed, its code is **retired**, not reassigned.
- Documentation in the [Rule catalogue](../schemas/rule-catalogue.md) is the
  human-readable source of truth for codes.

See [ADR-0002](../decisions/ADR-0002-stable-rule-codes.md).
