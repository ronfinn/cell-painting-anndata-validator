# Built-in schemas

Both built-in schemas are currently at **`schema_version: "0.2.1"`**.

| Name | Description |
|---|---|
| `generic-cell-painting` | Vendor-neutral schema; does not assume any single upstream pipeline's exact column names. |
| `jump-cp` | A compatibility preset based on public [JUMP Cell Painting Consortium](https://jump-cellpainting.broadinstitute.org/) metadata conventions. **Not** an official JUMP-endorsed AnnData schema — see [JUMP compatibility derivation](../pilots/jump-cp-derivation.md). |

Inspect them with the CLI:

```bash
cp-validate schema list
cp-validate schema show generic-cell-painting
cp-validate schema show jump-cp
```

## Measurement families (v0.2.0+)

Both schemas recognize these CellProfiler families for `FEAT002`:
`ObjectSkeleton`, `Math`, `Overlap`, `SizeShape`, `AreaOccupied`,
`ImageQuality`, in addition to the classic `AreaShape`, `Intensity`,
`Texture`, and related families declared in the YAML resources.

## Related

- [Alias resolution and precedence](aliases.md)
- [Custom schema format](custom.md)
- [Public-data pilots](../pilots/index.md)
