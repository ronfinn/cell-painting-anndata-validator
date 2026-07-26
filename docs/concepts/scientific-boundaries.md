# Scientific boundaries

This package validates AnnData representations of Cell Painting datasets. It
does **not**:

- convert CellProfiler, DeepProfiler, CytoTable or tabular profiles into AnnData;
- mutate, repair or rewrite the input file;
- endorse a particular biological conclusion;
- claim official JUMP Consortium standardisation (the `jump-cp` schema is a
  **compatibility preset** derived from public conventions);
- send dataset contents to external services.

`jump-cp` documents how public JUMP-oriented column names map onto canonical
fields. It is not an official JUMP AnnData standard. See
[JUMP compatibility derivation](../pilots/jump-cp-derivation.md).

Public Gallery pilots demonstrate that real consortium tables can be
validated after a **truthful** conversion. Pilots do not invent missing
licence or provenance blocks to force a green report.
