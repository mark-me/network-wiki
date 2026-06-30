"""Wiki content dataclasses and Jinja2-based template rendering."""


from __future__ import annotations

import contextlib
import html as html_mod
import importlib.resources as _pkg_res
from dataclasses import dataclass
from pathlib import Path
from typing import Union

try:
    from jinja2 import (
        ChoiceLoader,
        DictLoader,
        Environment,
        FileSystemLoader,
        StrictUndefined,
        Undefined,
        select_autoescape,
    )
    _JINJA2_AVAILABLE = True
except ImportError:
    _JINJA2_AVAILABLE = False

from igraph import Graph, Vertex, Edge


@dataclass
class WikiContent:
    """HTML content for a single node's wiki.

    Args:
        mini_html [str | None]: HTML shown in the collapsible side-panel (compact view).
            When ``None`` the exporter auto-generates content from vertex
            attributes.
        full_html [str | None]: HTML shown in the full-screen modal.
            When ``None`` the "Full wiki" button is hidden for that node.
    """

    mini_html: str | None = None
    full_html: str | None = None


class WikiTemplateRenderer:
    """Render mini- and full-wiki HTML via Jinja2 templates.

    Every template receives the following context variables:

    ============== ===========================================================
    ``v``          The ``igraph.Vertex`` object.
    ``attrs``      Dict of all vertex attributes: ``{name: value}``.
    ``label``      Display name of the node (``str``).
    ``index``      Vertex index (``int``).
    ``n_in``       Number of incoming edges (``int``).
    ``n_out``      Number of outgoing edges (``int``).
    ``neighbours`` Names of all neighbouring nodes (``list[str]``).
    ``graph``      The full ``igraph.Graph`` object.
    ``type_value`` Value of the *type_attr* attribute for this vertex, or
                   ``""`` when absent.  Use this in templates instead of
                   ``attrs[type_attr]`` so templates stay decoupled from
                   the attribute name.
    ============== ===========================================================

    Additional keys supplied via ``global_context`` are available in every
    template.

    **Template resolution order** (first match wins):

    1. Per-type file   - ``*_template_files_by_type``
    2. Per-type inline - ``*_templates_by_type``
    3. Default file    - ``*_template_file``
    4. Default inline  - ``*_template``
    5. Bundled package fallback (``mini_default.html.j2`` / ``full_default.html.j2``)

    Args:
        template_dir [str | None]: Directory containing user-supplied ``.html.j2`` files.
            When ``None``, only inline strings and package defaults are used.
        mini_template [str]: Inline Jinja2 string for the mini-wiki (side-panel).
        full_template [str]: Inline Jinja2 string for the full-wiki (modal).
        mini_template_file [str]: Filename (relative to *template_dir*) for the
            mini-wiki template.
        full_template_file [str]: Filename (relative to *template_dir*) for the
            full-wiki template.
        type_attr [str]: Name of the vertex attribute whose value selects
            per-type templates (default ``"type"``).  Set this to any
            attribute on your graph nodes — the value becomes ``type_value``
            in every template and drives template resolution.

            Examples::

                # Default: use the "type" attribute
                WikiTemplateRenderer()

                # Organisational chart: dispatch on "role"
                WikiTemplateRenderer(
                    type_attr="role",
                    full_templates_by_type={
                        "manager":   MANAGER_TMPL,
                        "engineer":  ENGINEER_TMPL,
                    },
                )

                # Network topology: dispatch on "device_class"
                WikiTemplateRenderer(
                    type_attr="device_class",
                    full_template_files_by_type={
                        "router":  "router.html.j2",
                        "switch":  "switch.html.j2",
                        "host":    "host.html.j2",
                    },
                )
        mini_templates_by_type [dict[str, str] | None]: Inline mini-templates keyed by type string.
        full_templates_by_type [dict[str, str] | None]: Inline full-templates keyed by type string.
        mini_template_files_by_type [dict[str, str] | None]: Filenames of mini-templates keyed by type.
        full_template_files_by_type [dict[str, str] | None]: Filenames of full-templates keyed by type.
        global_context [dict | None]: Extra variables available in every template.
        undefined_strict [bool]: When ``True``, Jinja2 raises on unknown variables.
            Recommended during development.

    Example::

        renderer = WikiTemplateRenderer(
            template_dir="templates/wiki",
            full_template_file="full_default.html.j2",
            full_template_files_by_type={
                "pipeline": "full_pipeline.html.j2",
            },
            global_context={"project": "ETL v2"},
        )
        exporter.set_wiki_renderer(renderer)
    """

    def __init__(
        self,
        template_dir: Union[str, Path] | None = None,
        mini_template: str | None = None,
        full_template: str | None = None,
        mini_template_file: str | None = None,
        full_template_file: str | None = None,
        type_attr: str = "type",
        mini_templates_by_type: dict[str, str] | None = None,
        full_templates_by_type: dict[str, str] | None = None,
        mini_template_files_by_type: dict[str, str] | None = None,
        full_template_files_by_type: dict[str, str] | None = None,
        global_context: dict | None = None,
        undefined_strict: bool = True,
    ):
        self._ensure_jinja_available()

        self.type_attr = type_attr
        self.global_context = global_context or {}

        loaders = self._build_loaders(template_dir)

        self._env = self._build_environment(loaders, undefined_strict)

        (
            self._mini_inline,
            self._full_inline,
            self._mini_file,
            self._full_file,
            self._mini_by_type,
            self._full_by_type,
            self._mini_files_by_type,
            self._full_files_by_type,
        ) = self._init_template_mappings(
            mini_template,
            full_template,
            mini_template_file,
            full_template_file,
            mini_templates_by_type,
            full_templates_by_type,
            mini_template_files_by_type,
            full_template_files_by_type,
        )

    def _ensure_jinja_available(self) -> None:
        """Raise an informative error when Jinja2 is not installed."""
        if not _JINJA2_AVAILABLE:
            raise ImportError(
                "Jinja2 is required for WikiTemplateRenderer. "
                "Install it with: pip install jinja2"
            )

    def _build_loaders(self, template_dir: Union[str, Path] | None) -> list:
        """Construct the loader chain for Jinja2 templates."""
        loaders: list = []

        if template_dir is not None:
            self._template_dir = Path(template_dir).resolve()
            loaders.append(FileSystemLoader(str(self._template_dir)))
        else:
            self._template_dir = None

        self._inline_store: dict[str, str] = {}
        loaders.append(DictLoader(self._inline_store))

        _pkg_templates = _pkg_res.files("network_wiki").joinpath("templates")
        loaders.append(FileSystemLoader(str(_pkg_templates)))
        return loaders

    def _build_environment(self, loaders: list, undefined_strict: bool) -> Environment:
        """Create the Jinja2 environment for this renderer."""
        return Environment(
            loader=ChoiceLoader(loaders),
            autoescape=select_autoescape(["html", "j2"]),
            undefined=StrictUndefined if undefined_strict else Undefined,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def _init_template_mappings(
        self,
        mini_template: str | None,
        full_template: str | None,
        mini_template_file: str | None,
        full_template_file: str | None,
        mini_templates_by_type: dict[str, str] | None,
        full_templates_by_type: dict[str, str] | None,
        mini_template_files_by_type: dict[str, str] | None,
        full_template_files_by_type: dict[str, str] | None,
    ) -> tuple[
        str | None,
        str | None,
        str | None,
        str | None,
        dict[str, str],
        dict[str, str],
        dict[str, str],
        dict[str, str],
    ]:
        """Initialize inline and file-based template mappings."""
        mini_inline: str | None = None
        full_inline: str | None = None
        mini_file: str | None = mini_template_file
        full_file: str | None = full_template_file
        mini_by_type: dict[str, str] = mini_templates_by_type or {}
        full_by_type: dict[str, str] = full_templates_by_type or {}
        mini_files_by_type: dict[str, str] = mini_template_files_by_type or {}
        full_files_by_type: dict[str, str] = full_template_files_by_type or {}

        if mini_template:
            self._inline_store["__mini_default__"] = mini_template
            mini_inline = "__mini_default__"
        if full_template:
            self._inline_store["__full_default__"] = full_template
            full_inline = "__full_default__"
        for vtype, tmpl in mini_by_type.items():
            self._inline_store[f"__mini_{vtype}__"] = tmpl
        for vtype, tmpl in full_by_type.items():
            self._inline_store[f"__full_{vtype}__"] = tmpl

        return (
            mini_inline,
            full_inline,
            mini_file,
            full_file,
            mini_by_type,
            full_by_type,
            mini_files_by_type,
            full_files_by_type,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_context(self, vertex: Vertex, graph: Graph) -> dict:
        """Assemble the full Jinja2 context dict for *vertex*."""
        attrs = self._collect_vertex_attrs(vertex, graph)
        label = _vertex_label(vertex, vertex.index)
        n_in, n_out = self._count_edges(vertex, graph)
        neighbours = self._collect_neighbours(vertex, graph)

        # type_value: resolved value of the configured type attribute.
        # Templates use this variable instead of attrs[type_attr] directly,
        # keeping them decoupled from the actual attribute name.
        raw_type_value = attrs.get(self.type_attr)
        type_value = None if raw_type_value is None else str(raw_type_value)

        ctx = {
            "v": vertex,
            "attrs": attrs,
            "label": label,
            "index": vertex.index,
            "n_in": n_in,
            "n_out": n_out,
            "neighbours": neighbours,
            "graph": graph,
            "type_value": type_value,
        } | self.global_context
        ctx |= self.global_context
        return ctx

    def _collect_vertex_attrs(self, vertex: Vertex, graph: Graph) -> dict:
        """Collect all attribute values for *vertex* into a dict."""
        attrs: dict = {}
        for attr in graph.vertex_attributes():
            with contextlib.suppress(KeyError, IndexError):
                attrs[attr] = vertex[attr]
        return attrs

    def _count_edges(self, vertex: Vertex, graph: Graph) -> tuple[int, int]:
        """Return the number of incoming and outgoing edges for *vertex*."""
        n_in = len(graph.predecessors(vertex.index))
        n_out = len(graph.successors(vertex.index))
        return n_in, n_out

    def _collect_neighbours(self, vertex: Vertex, graph: Graph) -> list[str]:
        """Return display labels for all neighbours of *vertex*."""
        return [
            _vertex_label(graph.vs[i], i)
            for i in graph.neighbors(vertex.index)
        ]

    def _resolve(
        self,
        vtype: str | None,
        by_type_inline: dict[str, str],
        by_type_files: dict[str, str],
        default_inline: str | None,
        default_file: str | None,
        prefix: str,
        package_fallback: str,
    ) -> str:
        """Return the template name to use, in priority order.

        Always returns at least the package fallback name.
        """
        if vtype:
            if vtype in by_type_inline:
                return f"__{prefix}_{vtype}__"
            if vtype in by_type_files:
                return by_type_files[vtype]
        if default_inline:
            return default_inline
        if default_file:
            return default_file
        return package_fallback

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def render(self, vertex: Vertex, graph: Graph) -> WikiContent:
        """Render mini- and full-wiki HTML for *vertex*.

        Args:
            vertex: ``igraph.Vertex`` to render wiki content for.
            graph: The parent ``igraph.Graph``.

        Returns:
            A :class:`WikiContent` with ``mini_html`` and ``full_html`` set.
        """
        ctx = self._build_context(vertex, graph)
        raw_vtype = ctx["attrs"].get(self.type_attr)
        vtype = None if raw_vtype is None else str(raw_vtype)

        mini_name = self._resolve(
            vtype,
            self._mini_by_type, self._mini_files_by_type,
            self._mini_inline, self._mini_file,
            "mini", "mini_default.html.j2",
        )
        full_name = self._resolve(
            vtype,
            self._full_by_type, self._full_files_by_type,
            self._full_inline, self._full_file,
            "full", "full_default.html.j2",
        )

        return WikiContent(
            mini_html=self._env.get_template(mini_name).render(**ctx),
            full_html=self._env.get_template(full_name).render(**ctx),
        )


# ---------------------------------------------------------------------------
# Helpers used by GraphExporter when no wiki renderer/callback is set
# ---------------------------------------------------------------------------

def _vertex_label(vertex, fallback_index: int) -> str:
    """Return the display label for *vertex*, falling back to ``"Node <index>"``."""
    for key in ("name", "label"):
        with contextlib.suppress(KeyError, IndexError):
            val = vertex[key]
            if val is not None:
                return str(val)
    return f"Node {fallback_index}"


def _auto_wiki(vertex: Vertex, graph: Graph) -> WikiContent:
    """Auto-generate :class:`WikiContent` from vertex attributes.

    Used when neither a :class:`WikiTemplateRenderer` nor a wiki callback is
    configured on the exporter.
    """
    attrs = _collect_vertex_attrs(vertex, graph)
    label = _derive_vertex_label(attrs, vertex)
    n_in, n_out = _count_vertex_edges(vertex, graph)

    mini = _build_auto_mini_wiki(vertex, attrs, n_in, n_out)
    full = _build_auto_full_wiki(vertex, graph, attrs, label)

    return WikiContent(mini_html=mini, full_html=full)


def _collect_vertex_attrs(vertex: Vertex, graph: Graph) -> dict:
    """Collect non-None attribute values for *vertex* into a dict."""
    return {k: vertex[k] for k in graph.vertex_attributes() if vertex[k] is not None}


def _derive_vertex_label(attrs: dict, vertex: Vertex) -> str:
    """Derive a human-readable label for *vertex* from its attributes."""
    return next(
        (str(attrs[k]) for k in ("name", "label") if attrs.get(k) is not None),
        f"Node {vertex.index}",
    )


def _count_vertex_edges(vertex: Vertex, graph: Graph) -> tuple[int, int]:
    """Return counts of incoming and outgoing edges for *vertex*."""
    n_in = len(graph.predecessors(vertex.index))
    n_out = len(graph.successors(vertex.index))
    return n_in, n_out


def _build_auto_mini_wiki(
    vertex: Vertex,
    attrs: dict,
    n_in: int,
    n_out: int,
) -> str:
    """Build the mini-wiki HTML snippet for a vertex."""
    attr_boxes = "".join(
        f'<div class="nw-attr-box">'
        f'<div class="nw-attr-label">{html_mod.escape(str(k))}</div>'
        f'<div class="nw-attr-value">{html_mod.escape(str(v))}</div>'
        f'</div>'
        for k, v in attrs.items()
    )
    return (
        f'<div class="nw-mini-wiki">'
        f'<div class="nw-node-type">Node {vertex.index}</div>'
        f'<div class="nw-attr-grid">{attr_boxes}</div>'
        f'<div class="nw-connections">'
        f'Incoming: <strong>{n_in}</strong>&nbsp;|&nbsp;Outgoing: <strong>{n_out}</strong>'
        f'</div></div>'
    )

def _build_auto_full_wiki(
    vertex: Vertex,
    graph: Graph,
    attrs: dict,
    label: str,
) -> str:
    """Build the full-wiki HTML snippet for a vertex."""
    neighbour_ids = graph.neighbors(vertex.index)
    nbr_items = "".join(
        f"<li>{html_mod.escape(_vertex_label(graph.vs[i], i))}</li>"
        for i in neighbour_ids
    )
    full_rows = "".join(
        f"<tr><td>{html_mod.escape(str(k))}</td><td>{html_mod.escape(str(v))}</td></tr>"
        for k, v in attrs.items()
    )
    return (
        f"<h2>{html_mod.escape(label)}</h2>"
        f"<table class='table table-sm table-striped'>"
        f"<thead><tr><th>Attribute</th><th>Value</th></tr></thead>"
        f"<tbody>{full_rows}</tbody></table>"
        f"<h5 class='mt-3'>Connected nodes</h5>"
        f"<ul>{nbr_items or '<li><em>None</em></li>'}</ul>"
    )


def _auto_edge_wiki(edge: Edge, graph: Graph) -> WikiContent:
    """Auto-generate :class:`WikiContent` for an edge from its attributes.

    Used when no edge wiki callback is configured but the graph has edge
    attributes worth displaying.

    Args:
        edge: The ``igraph.Edge`` to generate wiki content for.
        graph: The parent ``igraph.Graph``.

    Returns:
        A :class:`WikiContent` with simple attribute table mini- and full-HTML.
    """
    attrs = {k: edge[k] for k in graph.edge_attributes() if edge[k] is not None}
    src_label = _vertex_label(graph.vs[edge.source], edge.source)
    tgt_label = _vertex_label(graph.vs[edge.target], edge.target)

    attr_boxes = "".join(
        f'<div class="nw-attr-box">'
        f'<div class="nw-attr-label">{html_mod.escape(str(k))}</div>'
        f'<div class="nw-attr-value">{html_mod.escape(str(v))}</div>'
        f'</div>'
        for k, v in attrs.items()
    )
    mini = (
        f'<div class="nw-mini-wiki">'
        f'<div class="nw-node-type">Edge {edge.index}</div>'
        f'<div class="nw-node-desc">{html_mod.escape(src_label)} &rarr; {html_mod.escape(tgt_label)}</div>'
        f'<div class="nw-attr-grid">{attr_boxes}</div>'
        f'</div>'
    )

    full_rows = "".join(
        f"<tr><td>{html_mod.escape(str(k))}</td><td>{html_mod.escape(str(v))}</td></tr>"
        for k, v in attrs.items()
    )
    full = (
        f"<h2>Edge {edge.index}: {html_mod.escape(src_label)} &rarr; {html_mod.escape(tgt_label)}</h2>"
        f"<table class='table table-sm table-striped'>"
        f"<thead><tr><th>Attribute</th><th>Value</th></tr></thead>"
        f"<tbody>{full_rows or '<tr><td colspan=2><em>No attributes</em></td></tr>'}</tbody></table>"
    )
    return WikiContent(mini_html=mini, full_html=full)
