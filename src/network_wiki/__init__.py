"""
network-wiki
============
Generate interactive standalone HTML graph visualisations with
expandable per-node wiki panels, powered by vis.js and Jinja2.

Quickstart::

    import igraph as ig
    from network_wiki import GraphExporter, NodeStyle, WikiTemplateRenderer

    g = ig.Graph(directed=True)
    g.add_vertices(3)
    g.vs["name"] = ["A", "B", "C"]
    g.add_edges([(0, 1), (1, 2)])

    exporter = GraphExporter(g, title="My Graph")
    exporter.export("graph.html")
"""

from .exporter import (
    # Visual style
    NodeColor,
    NodeFont,
    NodeStyle,
    EdgeColor,
    EdgeArrows,
    EdgeStyle,
    # Wiki
    WikiContent,
    WikiTemplateRenderer,
    # Config
    LayoutConfig,
    ThemeConfig,
    # Main class
    GraphExporter,
)

__all__ = [
    "NodeColor",
    "NodeFont",
    "NodeStyle",
    "EdgeColor",
    "EdgeArrows",
    "EdgeStyle",
    "WikiContent",
    "WikiTemplateRenderer",
    "LayoutConfig",
    "ThemeConfig",
    "GraphExporter",
]

__version__ = "0.1.0"
