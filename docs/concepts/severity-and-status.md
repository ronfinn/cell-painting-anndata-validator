# Severity and status semantics

## Severities

| Severity | Role |
|---|---|
| `error` | Blocks a normal pass |
| `warning` | Signals a gap; blocks only under `strict=True` / `--strict` |
| `information` | Explains detection or context; never blocks status |

## Report status

After checks complete, `report.status` is `"pass"` or `"fail"`. Status is
derived from issue severities and the `strict` flag — not from printing or
exit-code helpers.

## CLI mapping

| Situation | Exit |
|---|---|
| Status pass | `0` |
| Status fail | `1` |
| Load/schema/config/runtime failure before a verdict | `2` |

See [ADR-0003](../decisions/ADR-0003-severity-and-strict-mode.md).
