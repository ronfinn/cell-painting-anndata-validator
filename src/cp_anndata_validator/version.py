"""Package version, resolved from installed distribution metadata."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("cp-anndata-validator")
except PackageNotFoundError:  # pragma: no cover - only hit for an uninstalled checkout
    __version__ = "0.0.0+unknown"
