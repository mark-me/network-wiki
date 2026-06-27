"""Layout- en thema-configuratie voor de gegenereerde HTML-pagina."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class LayoutConfig:
    """
    Vis.js physics- en layout-instellingen.

    solver-opties:
        ``"barnesHut"`` | ``"forceAtlas2Based"`` | ``"repulsion"`` |
        ``"hierarchicalRepulsion"``

    hierarchical_direction:
        ``"UD"`` (boven→onder) | ``"DU"`` | ``"LR"`` (links→rechts) | ``"RL"``
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
    Thema-instellingen voor de Bootstrap-gebaseerde UI.

    Bootstrap 5 wordt geladen via CDN. De pagina past automatisch mee met de
    OS-voorkeur van de gebruiker (light/dark) via ``prefers-color-scheme``.

    accent_color:
        CSS-kleur die als primaire accentkleur door de UI heen wordt gebruikt.
        Overschrijft de Bootstrap primary-kleur via een CSS custom property.

    panel_width_px:
        Breedte van het wiki-sidepanel in pixels.

    default_color_scheme:
        ``"auto"`` (volgt OS-voorkeur) | ``"light"`` | ``"dark"``
        Wordt als ``data-bs-theme`` op de ``<html>``-tag geplaatst.
        De schakelknop in de UI laat de gebruiker dit alsnog wijzigen.
    """
    accent_color: str = "#0d6efd"          # Bootstrap primary blauw als standaard
    panel_width_px: int = 380
    default_color_scheme: str = "auto"     # "auto" | "light" | "dark"
    lang: str = "nl"
