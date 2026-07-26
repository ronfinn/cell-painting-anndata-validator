# Truthful metadata and provenance

The validator never fabricates licence, provenance or aggregation metadata
to make a dataset pass. Checks report what is missing or incomplete.

When converting public tables (LINCS, JUMP, or lab exports) into AnnData:

- map columns that **exist**;
- leave absent governance fields absent;
- document conversion outside the AnnData if needed;
- do not invent `uns['licence']` or provenance blocks solely to silence
  warnings unless those facts are known and true.

See [ADR-0007](../decisions/ADR-0007-truthful-metadata.md) and
[Public-data pilots](../pilots/index.md).
