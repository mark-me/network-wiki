"""Layout and theme configuration for the generated HTML page."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, TypedDict

# ---------------------------------------------------------------------------
# Bootswatch catalogue
# ---------------------------------------------------------------------------

class BootswatchThemesDict(TypedDict):
    # Light themes
    cerulean: Literal["light"]
    cosmo: Literal["light"]
    flatly: Literal["light"]
    journal: Literal["light"]
    litera: Literal["light"]
    lumen: Literal["light"]
    lux: Literal["light"]
    materia: Literal["light"]
    minty: Literal["light"]
    morph: Literal["light"]
    pulse: Literal["light"]
    quartz: Literal["light"]
    sandstone: Literal["light"]
    simplex: Literal["light"]
    sketchy: Literal["light"]
    spacelab: Literal["light"]
    united: Literal["light"]
    yeti: Literal["light"]
    zephyr: Literal["light"]
    # Dark themes
    cyborg: Literal["dark"]
    darkly: Literal["dark"]
    slate: Literal["dark"]
    solar: Literal["dark"]
    superhero: Literal["dark"]
    vapor: Literal["dark"]


#: All available Bootswatch 5 themes, mapped to their base colour scheme.
#: Developers pick one of these names for ``ThemeConfig.bootswatch_theme``.
BOOTSWATCH_THEMES: BootswatchThemesDict = {
    # Light themes
    "cerulean":  "light",
    "cosmo":     "light",
    "flatly":    "light",
    "journal":   "light",
    "litera":    "light",
    "lumen":     "light",
    "lux":       "light",
    "materia":   "light",
    "minty":     "light",
    "morph":     "light",
    "pulse":     "light",
    "quartz":    "light",
    "sandstone": "light",
    "simplex":   "light",
    "sketchy":   "light",
    "spacelab":  "light",
    "united":    "light",
    "yeti":      "light",
    "zephyr":    "light",
    # Dark themes
    "cyborg":    "dark",
    "darkly":    "dark",
    "slate":     "dark",
    "solar":     "dark",
    "superhero": "dark",
    "vapor":     "dark",
}

BootswatchThemeName = Literal[
    "cerulean",
    "cosmo",
    "flatly",
    "journal",
    "litera",
    "lumen",
    "lux",
    "materia",
    "minty",
    "morph",
    "pulse",
    "quartz",
    "sandstone",
    "simplex",
    "sketchy",
    "spacelab",
    "united",
    "yeti",
    "zephyr",
    "cyborg",
    "darkly",
    "slate",
    "solar",
    "superhero",
    "vapor",
]

_BOOTSWATCH_VERSION = "5.3.3"
_BOOTSTRAP_VERSION  = "5.3.3"

_BOOTSTRAP_CSS_URL  = (
    "https://cdn.jsdelivr.net/npm/bootstrap@{v}/dist/css/bootstrap.min.css"
)
_BOOTSWATCH_CSS_URL = (
    "https://cdn.jsdelivr.net/npm/bootswatch@{v}/dist/{theme}/bootstrap.min.css"
)


def bootswatch_css_url(theme: str | None) -> str:
    """Return the CDN URL for the given Bootswatch theme, or the default Bootstrap CSS.

    Args:
        theme: A Bootswatch theme name (e.g. ``"darkly"``), or ``None`` for plain Bootstrap.

    Returns:
        The full CDN URL string for the requested stylesheet.

    Raises:
        ValueError: If *theme* is not ``None`` and not present in :data:`BOOTSWATCH_THEMES`.
    """
    if theme is None:
        return _BOOTSTRAP_CSS_URL.format(v=_BOOTSTRAP_VERSION)
    theme = theme.lower()
    if theme not in BOOTSWATCH_THEMES:
        raise ValueError(
            f"Unknown Bootswatch theme: '{theme}'. "
            f"Choose from: {', '.join(sorted(BOOTSWATCH_THEMES))}."
        )
    return _BOOTSWATCH_CSS_URL.format(v=_BOOTSWATCH_VERSION, theme=theme)


def bootswatch_base_scheme(theme: str | None) -> Literal["light", "dark"]:
    """Return the base colour scheme (``"light"`` or ``"dark"``) for a Bootswatch theme.

    Args:
        theme: A Bootswatch theme name, or ``None`` for plain Bootstrap (defaults to ``"light"``).

    Returns:
        ``"light"`` or ``"dark"``.
    """
    if theme is None:
        return "light"
    return BOOTSWATCH_THEMES.get(theme.lower(), "light")


# ---------------------------------------------------------------------------
# LayoutConfig
# ---------------------------------------------------------------------------

@dataclass
class LayoutConfig:
    """Physics and layout configuration passed directly to vis.js.

    Args:
        physics_enabled: Enable or disable the physics simulation.
        solver: Physics solver. One of ``"barnesHut"``, ``"forceAtlas2Based"``,
            ``"repulsion"``, or ``"hierarchicalRepulsion"``.
        stabilization_iterations: Number of stabilization iterations on load.
        gravity: Gravitational constant (negative = repulsive).
        spring_length: Preferred edge length in pixels.
        spring_constant: Edge spring stiffness (0–1).
        damping: Velocity damping factor (0–1).
        hierarchical: Enable hierarchical layout (disables physics).
        hierarchical_direction: Layout direction: ``"UD"``, ``"DU"``,
            ``"LR"``, or ``"RL"``.
        hierarchical_sort_method: Node ordering: ``"directed"`` or ``"hubsize"``.
        hierarchical_level_separation: Vertical distance between levels in pixels.
        hierarchical_node_spacing: Horizontal distance between nodes in pixels.
        hover: Highlight nodes and edges on mouse-over.
        multiselect: Allow selecting multiple nodes with a drag-box.
        navigation_buttons: Show zoom/fit navigation buttons.
        keyboard_navigation: Enable keyboard-driven navigation.
        zoom_speed: Scroll-wheel zoom sensitivity.
        min_zoom: Minimum zoom scale factor.
        max_zoom: Maximum zoom scale factor.
    """

    # Physics
    physics_enabled: bool = True
    solver: str = "forceAtlas2Based"
    stabilization_iterations: int = 150
    gravity: float = -50
    spring_length: int = 200
    spring_constant: float = 0.05
    damping: float = 0.09

    # Hierarchical layout
    hierarchical: bool = False
    hierarchical_direction: str = "LR"
    hierarchical_sort_method: str = "directed"
    hierarchical_level_separation: int = 200
    hierarchical_node_spacing: int = 120

    # Interaction
    hover: bool = True
    multiselect: bool = True
    navigation_buttons: bool = False
    keyboard_navigation: bool = False
    zoom_speed: float = 1.0
    min_zoom: float = 0.1
    max_zoom: float = 10.0

    def to_vis(self) -> dict:
        """Serialise this configuration to a vis.js-compatible options dict.

        Returns:
            A dictionary suitable for passing to ``new vis.Network(..., options)``.
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
            # Physics and hierarchical layout are mutually exclusive in vis.js.
            cfg["physics"]["enabled"] = False
        return cfg


# ---------------------------------------------------------------------------
# ThemeConfig
# ---------------------------------------------------------------------------

@dataclass
class ThemeConfig:
    """Visual theme configuration for the Bootstrap-based HTML page.

    The developer chooses a Bootswatch theme at export time.  The end-user
    can then toggle between light and dark mode inside the page; their
    preference is persisted in ``localStorage`` and automatically falls back
    to the OS setting (``prefers-color-scheme``) on first load.

    Args:
        bootswatch_theme: Optional Bootswatch 5 theme name.  ``None`` uses
            plain Bootstrap.

            Light themes: ``cerulean``, ``cosmo``, ``flatly``, ``journal``,
            ``litera``, ``lumen``, ``lux``, ``materia``, ``minty``, ``morph``,
            ``pulse``, ``quartz``, ``sandstone``, ``simplex``, ``sketchy``,
            ``spacelab``, ``united``, ``yeti``, ``zephyr``.

            Dark themes: ``cyborg``, ``darkly``, ``slate``, ``solar``,
            ``superhero``, ``vapor``.

        accent_color: CSS colour string used as the primary accent throughout
            the UI (toolbar highlight, panel title, wiki headings).  Defaults
            to Bootstrap primary blue.

        panel_width_px: Width of the wiki side-panel in pixels.

        lang: Value for the HTML ``lang`` attribute (e.g. ``"en"``, ``"nl"``).

    Example::

        # Dark Bootswatch theme with a custom accent
        ThemeConfig(bootswatch_theme="darkly", accent_color="#e94560")

        # Light Bootswatch theme
        ThemeConfig(bootswatch_theme="minty")

        # Plain Bootstrap (no Bootswatch)
        ThemeConfig()
    """

    bootswatch_theme: str | None = None
    accent_color: str = "#0d6efd"
    panel_width_px: int = 380
    lang: str = "en"

    def __post_init__(self) -> None:
        """Validate bootswatch_theme immediately so errors surface at config time."""
        if self.bootswatch_theme is not None:
            name = self.bootswatch_theme.lower()
            if name not in BOOTSWATCH_THEMES:
                raise ValueError(
                    f"Unknown Bootswatch theme: '{self.bootswatch_theme}'. "
                    f"Choose from: {', '.join(sorted(BOOTSWATCH_THEMES))}."
                )
            self.bootswatch_theme = name

    @property
    def css_url(self) -> str:
        """CDN URL for the active Bootstrap or Bootswatch stylesheet."""
        return bootswatch_css_url(self.bootswatch_theme)

    @property
    def base_scheme(self) -> Literal["light", "dark"]:
        """Base colour scheme (``"light"`` or ``"dark"``) of the chosen theme."""
        return bootswatch_base_scheme(self.bootswatch_theme)
