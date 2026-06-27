"""Layout- and theme-configuration for the generated HTML page."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class LayoutConfig:
    """
    Vis.js physics- en layout-settings.

    solver-options:
        ``"barnesHut"`` | ``"forceAtlas2Based"`` | ``"repulsion"`` |
        ``"hierarchicalRepulsion"``

    hierarchical_direction:
        ``"UD"`` (up-down) | ``"DU"`` | ``"LR"`` (left-right) | ``"RL"``
    """
    # Physics
    physics_enabled: bool = True
    solver: str = "forceAtlas2Based"
    stabilization_iterations: int = 150
    gravity: float = -50
    spring_length: int = 200
    spring_constant: float = 0.05
    damping: float = 0.09

    # Hierarchisch layout
    hierarchical: bool = False
    hierarchical_direction: str = "LR"
    hierarchical_sort_method: str = "directed"  # directed | hubsize
    hierarchical_level_separation: int = 200
    hierarchical_node_spacing: int = 120

    # Interactie
    hover: bool = True
    multiselect: bool = True
    navigation_buttons: bool = False
    keyboard_navigation: bool = False
    zoom_speed: float = 1.0
    min_zoom: float = 0.1
    max_zoom: float = 10.0

    def to_vis(self) -> dict:
        """Convert this layout configuration into a vis.js-compatible settings dict.
        Include physics, interaction and optional hierarchical layout settings.

        Returns:
            dict: A dictionary with vis.js layout and physics configuration derived from this
                ``LayoutConfig`` instance.
        """
        cfg: dict[str, Any] = {
            "physics": {
                "enabled": self.physics_enabled,
                "solver": self.solver,
                "stabilization": {"iterations": self.stabilization_iterations},
                self.solver: {
                    "gravitationalConstant": self.gravity,
                    "springLength": self.spring_length,
                    "springConstant": self.spring_constant,
                    "damping": self.damping,
                },
            },
            "interaction": {
                "hover": self.hover,
                "multiselect": self.multiselect,
                "navigationButtons": self.navigation_buttons,
                "keyboard": self.keyboard_navigation,
                "zoomSpeed": self.zoom_speed,
                "zoomView": True,
                "minZoom": self.min_zoom,
                "maxZoom": self.max_zoom,
            },
        }
        if self.hierarchical:
            cfg["layout"] = {
                "hierarchical": {
                    "enabled": True,
                    "direction": self.hierarchical_direction,
                    "sortMethod": self.hierarchical_sort_method,
                    "levelSeparation": self.hierarchical_level_separation,
                    "nodeSpacing": self.hierarchical_node_spacing,
                }
            }
            cfg["physics"]["enabled"] = False  # physics incompatibel met hierarchisch
        return cfg


@dataclass
class ThemeConfig:
    """
    Theme settings for the Bootstrap-based UI.

    Bootstrap 5 is loaded via CDN. The page automatically adapts to the
    user's OS preference (light/dark) via ``prefers-color-scheme``.

    accent_color:
        CSS color that is used as the primary accent color throughout the UI.
        Overrides the Bootstrap primary color via a CSS custom property.

    panel_width_px:
        Width of the wiki-sidepanel in pixels.

    default_color_scheme:
        ``"auto"`` (follows OS preference) | ``"light"`` | ``"dark"``
        Is placed as ``data-bs-theme`` on the ``<html>`` tag.
        The toggle button in the UI allows the user to change this manually.
    """
    accent_color: str = "#0d6efd"          # Bootstrap primary blue as default
    panel_width_px: int = 380
    default_color_scheme: str = "auto"     # "auto" | "light" | "dark"
    lang: str = "nl"
