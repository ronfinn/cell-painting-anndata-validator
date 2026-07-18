"""AnnData loading and safe inspection (architecture layer 1).

This module never densifies a sparse matrix and never reads a complete
large matrix when metadata is sufficient: :func:`load_anndata` only reads
what ``anndata`` itself reads eagerly (``.obs``, ``.var``, ``.uns``, shape
and dtype metadata), and defers to :mod:`cp_anndata_validator.sampling` for
any bounded inspection of matrix values.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import anndata as ad
from anndata import AnnData
from scipy import sparse

DEFAULT_BACKED_THRESHOLD_BYTES = 500 * 1024 * 1024
"""Files larger than this are opened backed by default when ``backed=None``."""


class LoadError(Exception):
    """Raised when an AnnData file cannot be opened safely for validation."""


@dataclass(frozen=True)
class AnnDataHandle:
    """A thin, inspection-friendly wrapper around a loaded AnnData object."""

    adata: AnnData
    path: Path
    size_bytes: int
    backed: bool

    @property
    def n_obs(self) -> int:
        return self.adata.n_obs

    @property
    def n_vars(self) -> int:
        return self.adata.n_vars

    @property
    def x_is_sparse(self) -> bool:
        return bool(sparse.issparse(self.adata.X))

    @property
    def x_dtype(self) -> str:
        x = self.adata.X
        dtype = getattr(x, "dtype", None)
        return str(dtype) if dtype is not None else "unknown"

    @property
    def x_shape(self) -> tuple[int, int]:
        x = self.adata.X
        if x is None:
            return (self.n_obs, 0)
        return (int(x.shape[0]), int(x.shape[1]))

    def close(self) -> None:
        """Release the underlying file handle when opened in backed mode."""
        file = getattr(self.adata, "file", None)
        if self.backed and file is not None:
            file.close()


def load_anndata(path: str | Path, *, backed: bool | None = None) -> AnnDataHandle:
    """Safely open an ``.h5ad`` file for validation.

    ``backed`` selects the loading mode: ``True`` forces backed (``'r'``)
    mode, ``False`` forces a full in-memory load, and ``None`` (the default)
    picks backed mode automatically once the file exceeds
    :data:`DEFAULT_BACKED_THRESHOLD_BYTES`. Any failure to open the file is
    raised as a :class:`LoadError` with an actionable message, never as a
    raw exception from ``anndata`` or ``h5py``.
    """
    resolved = Path(path).expanduser().resolve()

    if not resolved.exists():
        raise LoadError(f"Dataset file does not exist: {resolved}")
    if not resolved.is_file():
        raise LoadError(f"Dataset path is not a file: {resolved}")
    if resolved.suffix != ".h5ad":
        raise LoadError(
            f"Unsupported file extension {resolved.suffix!r}; expected an '.h5ad' file: {resolved}"
        )

    size_bytes = resolved.stat().st_size
    use_backed = backed if backed is not None else size_bytes > DEFAULT_BACKED_THRESHOLD_BYTES

    try:
        adata = ad.read_h5ad(resolved, backed="r" if use_backed else None)
    except Exception as exc:
        raise LoadError(f"Failed to read AnnData file {resolved}: {exc}") from exc

    return AnnDataHandle(adata=adata, path=resolved, size_bytes=size_bytes, backed=use_backed)
