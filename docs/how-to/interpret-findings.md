# Interpret findings

Every issue carries a stable **rule code**, **severity**, **category**,
AnnData **location**, **message**, optional **evidence**, **remediation**,
and **check name**.

## Severity

| Severity | Normal mode | Strict mode |
|---|---|---|
| `error` | Fails the report | Fails the report |
| `warning` | Does not fail | Fails the report |
| `information` | Does not fail | Does not fail |

## Status

`report.status` is `"pass"` or `"fail"` after all checks run. Exit code `1`
maps to a failed report; exit code `2` means validation never completed.

## Reading common categories

| Category | Typical meaning |
|---|---|
| Identifiers | Missing or incomplete plate/well/site/cell/perturbation fields |
| Annotations | Control/treatment labels incomplete |
| Features | Compartment or measurement-family naming gaps |
| Matrix / slots | Shape, numeric validity, layer/obsm alignment |
| Metadata / provenance | Licence, schema id, image/segmentation/feature provenance |
| Aggregation | Missing or incomplete aggregation blocks on well/treatment data |
| AI readiness | Constant or heavily missing features (sampled on large matrices) |
| Profile | Declared vs detected level mismatch or ambiguity |

For fixture-derived baselines and “is this a false positive?” guidance, see
[Expected findings and false positives](false-positives.md). The full code
list is in the [Rule catalogue](../schemas/rule-catalogue.md).

## What findings are not

A validation finding is **not** a security vulnerability and is **not** a
biological claim. See [Scientific boundaries](../concepts/scientific-boundaries.md)
and [Security](../project/security.md).
