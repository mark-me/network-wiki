"""
network-wiki
============
Generate interactive standalone HTML graph-visualizations with
expandable node wikis, Bootstrap 5 light/dark theming and Jinja2 templates.

Quickstart::

    import igraph as ig
    from network_wiki import GraphExporter, NodeStyle, WikiTemplateRenderer

    g = ig.Graph(directed=True)
    g.add_vertices(3)
    g.vs["name"] = ["A", "B", "C"]
    g.add_edges([(0, 1), (1, 2)])

    exporter = GraphExporter(g, title="Mijn Graph")
    exporter.export("graph.html")
"""

from .node_style import NodeColor, NodeFont, NodeStyle
from .edge_style import EdgeColor, EdgeArrows, EdgeStyle
from .wiki import WikiContent, WikiTemplateRenderer
from .layout import LayoutConfig, ThemeConfig
from .exporter import GraphExporter

__all__ = [
    "NodeColor", "NodeFont", "NodeStyle",
    "EdgeColor", "EdgeArrows", "EdgeStyle",
    "WikiContent", "WikiTemplateRenderer",
    "LayoutConfig", "ThemeConfig",
    "GraphExporter",
]

__version__ = "0.2.0"
