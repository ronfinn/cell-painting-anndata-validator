# Generate JSON and HTML reports

```bash
uv run cp-validate experiment.h5ad --report out/report.json
uv run cp-validate experiment.h5ad --report out/report.html --force
```

Format is inferred from the suffix (`.json` or `.html`). The console report
still prints unless `--quiet` is set.

From Python:

```python
from pathlib import Path
from cp_anndata_validator import validate
from cp_anndata_validator.reporting import render_html, render_json

report = validate("experiment.h5ad")
Path("report.json").write_text(render_json(report))
Path("report.html").write_text(render_html(report))
```

HTML output escapes user-controlled strings. Reports avoid dumping large or
sensitive matrix values.
