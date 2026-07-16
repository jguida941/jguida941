"""Registry-facing facade for pure predicates over validated rendered-fact bundles."""

from scripts.contracts.rendered.contrast import rendered_contrast
from scripts.contracts.rendered.density import rendered_content_density
from scripts.contracts.rendered.interaction import rendered_responsive, rendered_touch_targets

__all__ = [
    "rendered_content_density",
    "rendered_contrast",
    "rendered_responsive",
    "rendered_touch_targets",
]
