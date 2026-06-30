"""Flask integration for network-wiki.

Provides :class:`GraphView` — a self-contained Flask :class:`~flask.Blueprint`
that serves one or more :class:`~network_wiki.exporter.GraphExporter` instances
as interactive web pages, without needing to write HTML files to disk.

Usage
-----
Minimal single-graph setup::

    from flask import Flask
    from network_wiki.flask_view import GraphView
    from network_wiki import GraphExporter, ThemeConfig
    import igraph as ig

    app = Flask(__name__)

    g = ig.Graph(directed=True)
    g.add_vertices(3)
    g.vs["name"] = ["A", "B", "C"]
    g.add_edges([(0, 1), (1, 2)])

    view = GraphView(
        GraphExporter(g, title="My Graph", theme=ThemeConfig(bootswatch_theme="flatly")),
        url_prefix="/graph",
    )
    view.register(app)

    # http://localhost:5000/graph/  → interactive page
    # http://localhost:5000/graph/data  → JSON payload (fetched by the page)

Multiple graphs with a picker in the toolbar::

    etl_view = GraphView(url_prefix="/graphs")
    etl_view.add("pipeline", etl_exporter, title="ETL Pipeline")
    etl_view.add("schema",   schema_exporter, title="DB Schema")
    etl_view.register(app)

    # http://localhost:5000/graphs/           → redirects to first graph
    # http://localhost:5000/graphs/pipeline/  → ETL pipeline page (with picker)
    # http://localhost:5000/graphs/schema/    → DB schema page (with picker)

Dynamic graphs (graph is rebuilt on every request)::

    def build_graph() -> ig.Graph:
        # fetch from database, recompute, etc.
        ...

    view = GraphView(url_prefix="/live")
    view.add("live", lambda: GraphExporter(build_graph(), title="Live"))
    view.register(app)
"""

from __future__ import annotations

import importlib.resources as _pkg_res
import json
from typing import Callable, Union

from jinja2 import Environment, FileSystemLoader
from markupsafe import Markup

from .json_safe import serialize_json

from .exporter import GraphExporter
from .layout import ThemeConfig

try:
    from flask import Blueprint, Response, jsonify, redirect, url_for
    _FLASK_AVAILABLE = True
except ImportError:
    _FLASK_AVAILABLE = False

#: Type alias: either a ready-made exporter or a zero-argument callable that
#: returns one (useful for graphs that are rebuilt on every request).
ExporterOrFactory = Union[GraphExporter, Callable[[], GraphExporter]]


def _resolve(source: ExporterOrFactory) -> GraphExporter:
    """Return an exporter, calling *source* first if it is a factory."""
    return source() if callable(source) else source


class GraphView:
    """A Flask Blueprint that serves network-wiki graphs as interactive pages.

    One :class:`GraphView` can host any number of named graphs.  Each graph
    gets its own ``/<name>/`` page route and a ``/<name>/data`` JSON route.
    When more than one graph is registered, the toolbar shows a picker that
    switches graphs in place — without a full page reload.

    Args:
        default_exporter: Optional exporter (or factory) for the default graph.
            Equivalent to calling ``add("default", exporter)`` afterwards.
        url_prefix: URL prefix under which all routes are registered.
            Defaults to ``"/graph"``.
        blueprint_name: Internal Flask blueprint name.  Must be unique per app.

    Raises:
        ImportError: If Flask is not installed
            (``pip install network-wiki[flask]``).
    """

    def __init__(
        self,
        default_exporter: ExporterOrFactory | None = None,
        url_prefix: str = "/graph",
        blueprint_name: str = "network_wiki",
    ):
        if not _FLASK_AVAILABLE:
            raise ImportError(
                "Flask is required for GraphView. "
                "Install it with: pip install flask  or  pip install network-wiki[flask]"
            )

        self._url_prefix = url_prefix.rstrip("/")
        self._bp = Blueprint(blueprint_name, __name__)
        # Ordered dict: name → (exporter_or_factory, display_title)
        self._graphs: dict[str, tuple[ExporterOrFactory, str]] = {}

        if default_exporter is not None:
            exporter = _resolve(default_exporter)
            self.add("default", default_exporter, title=exporter.title)

        self._register_routes()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add(
        self,
        name: str,
        exporter: ExporterOrFactory,
        title: str | None = None,
    ) -> "GraphView":
        """Register a named graph.

        Args:
            name: URL-safe identifier (``[a-zA-Z0-9_-]``).  Used in the route
                ``/<name>/`` and the data endpoint ``/<name>/data``.
            exporter: A :class:`~network_wiki.exporter.GraphExporter` instance,
                or a zero-argument callable that returns one.  The callable form
                is evaluated on every request, which is useful when the graph is
                rebuilt from a database.
            title: Human-readable title shown in the toolbar picker.  Defaults
                to ``exporter.title`` (or the factory result's title).

        Returns:
            ``self`` for method chaining.

        Example::

            view.add("etl",    etl_exporter,    title="ETL Pipeline")
            view.add("schema", schema_exporter, title="DB Schema")
            view.add("live",   lambda: GraphExporter(fetch_live_graph()))
        """
        if title is None:
            title = _resolve(exporter).title
        self._graphs[name] = (exporter, title)
        return self

    def register(self, app) -> None:
        """Register this view's Blueprint with a Flask application.

        Args:
            app: A :class:`flask.Flask` application instance.

        Example::

            view = GraphView(exporter, url_prefix="/graphs")
            view.register(app)
        """
        app.register_blueprint(self._bp, url_prefix=self._url_prefix)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _graph_list(self, active_name: str) -> list[dict]:
        """Build the picker list passed to the template."""
        return [
            {
                "name":  name,
                "title": title,
                "url":   f"{self._url_prefix}/{name}/data",
            }
            for name, (_, title) in self._graphs.items()
        ]

    def _shell_html(self, exporter: GraphExporter, active_name: str) -> str:
        """Render the page_flask.html.j2 shell (no inline graph data)."""
        t = exporter.theme
        tmpl_path = _pkg_res.files("network_wiki").joinpath("templates")
        env = Environment(loader=FileSystemLoader(str(tmpl_path)), autoescape=True)
        return env.get_template("page_flask.html.j2").render(
            title=exporter.title,
            css_url=t.css_url,
            accent_color=t.accent_color,
            panel_width=t.panel_width_px,
            base_scheme=t.base_scheme,
            bootswatch_theme=t.bootswatch_theme,
            lang=t.lang,
            # Markup() keeps this pre-validated JSON safe from autoescape's
            # HTML-entity-escaping — see the matching comment in exporter.py.
            layout_json=Markup(serialize_json(exporter.layout.to_vis())),
            data_url=f"{self._url_prefix}/{active_name}/data",
            graphs=self._graph_list(active_name),
        )

    def _data_response(self, exporter: GraphExporter) -> Response:
        """Build the JSON payload fetched by the browser on graph load/switch."""
        tvars = exporter._build_template_vars()
        payload = {
            "title":        tvars["title"],
            "nodes":        json.loads(tvars["nodes_json"]),
            "edges":        json.loads(tvars["edges_json"]),
            "node_wiki":    json.loads(tvars["node_wiki_json"]),
            "edge_wiki":    json.loads(tvars["edge_wiki_json"]),
            "has_edge_wiki": tvars["has_edge_wiki"],
        }
        return jsonify(payload)

    # ------------------------------------------------------------------
    # Route registration
    # ------------------------------------------------------------------

    def _register_routes(self) -> None:
        """Attach all URL rules to the Blueprint."""
        bp = self._bp

        # Root redirect → first registered graph (or "default").
        @bp.route("/")
        @bp.route("")
        def _root():
            if not self._graphs:
                return "No graphs registered.", 404
            first = next(iter(self._graphs))
            return redirect(f"{self._url_prefix}/{first}/")

        # Page shell — served once; graph data is fetched separately.
        @bp.route("/<name>/")
        @bp.route("/<name>")
        def _page(name: str):
            if name not in self._graphs:
                return f"Graph '{name}' not found.", 404
            source, _ = self._graphs[name]
            exporter = _resolve(source)
            return self._shell_html(exporter, name)

        # JSON data endpoint — fetched by the browser's loadGraph().
        @bp.route("/<name>/data")
        def _data(name: str):
            if name not in self._graphs:
                return jsonify({"error": f"Graph '{name}' not found"}), 404
            source, _ = self._graphs[name]
            exporter = _resolve(source)
            return self._data_response(exporter)
