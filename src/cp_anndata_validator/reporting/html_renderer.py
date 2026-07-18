"""Self-contained HTML report rendering via Jinja2.

The template's Jinja environment enables autoescaping for ``.jinja``/``.html``
templates, so issue text (messages, evidence, remediation) originating from
untrusted dataset content is always HTML-escaped rather than injected raw.
"""

from __future__ import annotations

import jinja2

from cp_anndata_validator.models.report import Report

_ENV = jinja2.Environment(
    loader=jinja2.PackageLoader("cp_anndata_validator.reporting", "templates"),
    autoescape=jinja2.select_autoescape(["html", "jinja"]),
)


def render_html(report: Report) -> str:
    """Render a Report as a single, self-contained HTML document."""
    template = _ENV.get_template("report.html.jinja")
    return template.render(report=report)
