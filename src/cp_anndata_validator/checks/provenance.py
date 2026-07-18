"""Image, segmentation, and feature-extraction provenance checks."""

from __future__ import annotations

from typing import Any

from cp_anndata_validator.checks.registry import CheckContext, register_check
from cp_anndata_validator.models.issue import Category, Issue, Severity


def _uns_dict(ctx: CheckContext, key: str) -> dict[str, Any] | None:
    uns = ctx.handle.adata.uns
    value = uns.get(key) if hasattr(uns, "get") else None
    return value if isinstance(value, dict) else None


@register_check(name="image_provenance", category=Category.PROVENANCE_IMAGE)
def check_image_provenance(ctx: CheckContext) -> list[Issue]:
    """Source-image and illumination-correction provenance should be declared."""
    if _uns_dict(ctx, "image_provenance"):
        return []

    return [
        Issue(
            code="PROVIMG001",
            severity=Severity.WARNING,
            category=Category.PROVENANCE_IMAGE,
            location="uns.image_provenance",
            message="No image provenance metadata (uns['image_provenance']) was found.",
            evidence=None,
            remediation=(
                "Record source image and illumination-correction provenance in "
                "uns['image_provenance']."
            ),
            check_name="image_provenance",
        )
    ]


@register_check(name="segmentation_provenance", category=Category.PROVENANCE_SEGMENTATION)
def check_segmentation_provenance(ctx: CheckContext) -> list[Issue]:
    """The segmentation method/tool and version should be declared."""
    block = _uns_dict(ctx, "segmentation_provenance")
    if block and (block.get("method") or block.get("tool")):
        return []

    return [
        Issue(
            code="PROVSEG001",
            severity=Severity.WARNING,
            category=Category.PROVENANCE_SEGMENTATION,
            location="uns.segmentation_provenance",
            message="No segmentation method/tool is declared (uns['segmentation_provenance']).",
            evidence=None,
            remediation=(
                "Record the segmentation method/tool and version in uns['segmentation_provenance']."
            ),
            check_name="segmentation_provenance",
        )
    ]


@register_check(
    name="feature_extraction_provenance", category=Category.PROVENANCE_FEATURE_EXTRACTION
)
def check_feature_extraction_provenance(ctx: CheckContext) -> list[Issue]:
    """The feature-extraction tool/method and version should be declared."""
    block = _uns_dict(ctx, "feature_extraction_provenance")
    if block and (block.get("tool") or block.get("method")):
        return []

    return [
        Issue(
            code="PROVFEAT001",
            severity=Severity.WARNING,
            category=Category.PROVENANCE_FEATURE_EXTRACTION,
            location="uns.feature_extraction_provenance",
            message=(
                "No feature-extraction tool/version is declared "
                "(uns['feature_extraction_provenance'])."
            ),
            evidence=None,
            remediation=(
                "Record the feature-extraction tool and version in "
                "uns['feature_extraction_provenance']."
            ),
            check_name="feature_extraction_provenance",
        )
    ]
