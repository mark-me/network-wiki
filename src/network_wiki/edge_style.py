"""Visual style dataclasses for graph edges."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass
class EdgeColor:
    """Colour configuration for an edge.

    Args:
        color: Default edge colour (CSS string).
        highlight: Edge colour when selected.
        hover: Edge colour on mouse-over.
        inherit: Inherit colour from a connected node.
            ``"from"``, ``"to"``, ``"both"``, or ``False`` to disable.
    """

    color: str = "#848484"
    highlight: str = "#848484"
    hover: str = "#848484"
    inherit: Literal["from", "to", "both", False] = False

    def to_vis(self) -> dict:
        """Serialise to a vis.js edge colour dict."""
        return {
            "color": self.color,
            "highlight": self.highlight,
            "hover": self.hover,
            "inherit": self.inherit,
        }


@dataclass
class EdgeArrows:
    """Arrow endpoint configuration for an edge.

    Each endpoint (``to``, ``from``, ``middle``) can be independently
    enabled with its own scale and type.

    Args:
        to_enabled: Show an arrow at the target end.
        to_scale: Scale factor for the target arrowhead.
        to_type: Shape of the target arrowhead. Options: ``"arrow"``,
            ``"bar"``, ``"circle"``, ``"box"``, ``"crow"``, ``"curve"``,
            ``"diamond"``, ``"inv_curve"``, ``"inv_triangle"``,
            ``"triangle"``, ``"vee"``.
        from_enabled: Show an arrow at the source end.
        from_scale: Scale factor for the source arrowhead.
        from_type: Shape of the source arrowhead (same options as *to_type*).
        middle_enabled: Show an arrow at the midpoint of the edge.
        middle_scale: Scale factor for the midpoint arrowhead.
        middle_type: Shape of the midpoint arrowhead.
    """

    to_enabled: bool = True
    to_scale: float = 0.8
    to_type: str = "arrow"

    from_enabled: bool = False
    from_scale: float = 0.8
    from_type: str = "arrow"

    middle_enabled: bool = False
    middle_scale: float = 0.8
    middle_type: str = "arrow"

    def to_vis(self) -> dict:
        """Serialise to a vis.js arrows options dict."""
        d: dict[str, Any] = {}
        if self.to_enabled:
            d["to"] = {"enabled": True, "scaleFactor": self.to_scale, "type": self.to_type}
        if self.from_enabled:
            d["from"] = {"enabled": True, "scaleFactor": self.from_scale, "type": self.from_type}
        if self.middle_enabled:
            d["middle"] = {"enabled": True, "scaleFactor": self.middle_scale, "type": self.middle_type}
        return d


@dataclass
class EdgeStyle:
    """All visual properties of an edge, mapped directly to vis.js edge options.

    Args:
        width: Line width in pixels.
        width_selected: Line width when the edge is selected.
        color: A hex colour string or an :class:`EdgeColor` for full control.
        label: Optional text label rendered along the edge.
        font_color: CSS colour of the label text.
        font_size: Font size of the label in points.
        font_align: Label alignment: ``"middle"``, ``"top"``,
            ``"bottom"``, or ``"horizontal"``.
        arrows: Arrow endpoint configuration.
        dashes: Render the edge as a dashed line.
        smooth_type: Edge curve algorithm. Options: ``"dynamic"``,
            ``"continuous"``, ``"discrete"``, ``"diagonalCross"``,
            ``"straightCross"``, ``"horizontal"``, ``"vertical"``,
            ``"curvedCW"``, ``"curvedCCW"``, ``"cubicBezier"``.
        smooth_roundness: Curvature amount (0–1).
        shadow: Enable drop shadow on the edge line.
        tooltip: HTML string shown on mouse-over (vis.js ``title``).
        length: Preferred edge length in pixels (used by the physics engine).
        extra: Any additional vis.js edge properties not listed above.
            These are merged last and override earlier values.
    """

    width: float = 2.0
    width_selected: float = 3.0
    color: EdgeColor | str = field(default_factory=EdgeColor)
    label: str | None = None
    font_color: str = "#343434"
    font_size: int = 12
    font_align: str = "middle"
    arrows: EdgeArrows = field(default_factory=EdgeArrows)
    dashes: bool = False
    smooth_type: str = "cubicBezier"
    smooth_roundness: float = 0.5
    shadow: bool = False
    tooltip: str | None = None
    length: int | None = None
    extra: dict = field(default_factory=dict)

    def to_vis(self, from_id: int, to_id: int) -> dict:
        """Serialise this style to a vis.js edge dict.

        Args:
            from_id: Source vertex index.
            to_id: Target vertex index.

        Returns:
            A dict suitable for inclusion in the vis.js ``DataSet`` of edges.
        """
        col = (
            EdgeColor(color=self.color, highlight=self.color, hover=self.color).to_vis()
            if isinstance(self.color, str)
            else self.color.to_vis()
        )

        d: dict[str, Any] = {
            "from": from_id,
            "to": to_id,
            "width": self.width,
            "selectionWidth": self.width_selected,
            "color": col,
            "arrows": self.arrows.to_vis(),
            "smooth": {
                "type": self.smooth_type,
                "roundness": self.smooth_roundness,
            },
            "dashes": self.dashes,
            "shadow": self.shadow,
            "font": {
                "color": self.font_color,
                "size": self.font_size,
                "align": self.font_align,
            },
        }

        if self.label:
            d["label"] = self.label
        if self.tooltip:
            d["title"] = self.tooltip
        d["length"] = self.length or 0
        d |= self.extra
        return d
