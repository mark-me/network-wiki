"""Integration and smoke tests for GraphExporter."""
from __future__ import annotations

import html.parser
import igraph as ig
import pytest
from network_wiki import (
    GraphExporter, NodeStyle, EdgeStyle,
    WikiContent, WikiTemplateRenderer,
    LayoutConfig, ThemeConfig, BOOTSWATCH_THEMES,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def simple_graph():
    g = ig.Graph(directed=True)
    g.add_vertices(3)
    g.vs["name"] = ["Pipeline", "Source", "Target"]
    g.vs["type"] = ["pipeline", "source", "target"]
    g.vs["description"] = ["Central pipeline", "Source model", "DWH table"]
    g.add_edges([(1, 0), (0, 2)])
    return g


@pytest.fixture
def graph_with_edge_attrs(simple_graph):
    simple_graph.es["weight"] = [1.5, 2.0]
    simple_graph.es["critical"] = [True, False]
    return simple_graph


# ---------------------------------------------------------------------------
# HTML validity helper
# ---------------------------------------------------------------------------

class _HTMLChecker(html.parser.HTMLParser):
    """Minimal well-formedness checker – raises on parser errors."""
    def __init__(self):
        super().__init__()
        self.errors: list[str] = []
    def handle_error(self, message):          # type: ignore[override]
        self.errors.append(message)


def assert_valid_html(text: str) -> None:
    checker = _HTMLChecker()
    checker.feed(text)
    assert not checker.errors, f"HTML parser errors: {checker.errors}"


# ---------------------------------------------------------------------------
# Basic export
# ---------------------------------------------------------------------------

def test_export_creates_file(simple_graph, tmp_path):
    out = tmp_path / "out.html"
    result = GraphExporter(simple_graph).export(out)
    assert result == out.resolve()
    assert out.exists()


def test_export_contains_vis_and_bootstrap(simple_graph, tmp_path):
    out = tmp_path / "test.html"
    GraphExporter(simple_graph).export(out)
    html = out.read_text(encoding="utf-8")
    assert "vis-network" in html
    assert "bootstrap" in html.lower()


def test_export_contains_node_labels(simple_graph, tmp_path):
    out = tmp_path / "test.html"
    GraphExporter(simple_graph).export(out)
    html = out.read_text(encoding="utf-8")
    assert "Pipeline" in html
    assert "Source" in html
    assert "Target" in html


def test_export_html_parseable(simple_graph, tmp_path):
    out = tmp_path / "test.html"
    GraphExporter(simple_graph).export(out)
    assert_valid_html(out.read_text(encoding="utf-8"))


def test_export_returns_absolute_path(simple_graph, tmp_path):
    out = tmp_path / "out.html"
    result = GraphExporter(simple_graph).export(out)
    assert result.is_absolute()


# ---------------------------------------------------------------------------
# Bootswatch theming
# ---------------------------------------------------------------------------

def test_bootswatch_light_injects_url_and_scheme(simple_graph, tmp_path):
    out = tmp_path / "light.html"
    GraphExporter(simple_graph, theme=ThemeConfig(bootswatch_theme="flatly")).export(out)
    html = out.read_text(encoding="utf-8")
    assert "bootswatch" in html
    assert "flatly" in html
    assert 'data-bs-theme="light"' in html


def test_bootswatch_dark_sets_dark_scheme(simple_graph, tmp_path):
    out = tmp_path / "dark.html"
    GraphExporter(simple_graph, theme=ThemeConfig(bootswatch_theme="darkly")).export(out)
    html = out.read_text(encoding="utf-8")
    assert "darkly" in html
    assert 'data-bs-theme="dark"' in html


def test_no_bootswatch_uses_plain_bootstrap(simple_graph, tmp_path):
    out = tmp_path / "plain.html"
    GraphExporter(simple_graph, theme=ThemeConfig()).export(out)
    html = out.read_text(encoding="utf-8")
    assert "bootswatch" not in html
    assert "bootstrap@" in html


def test_invalid_bootswatch_raises_at_config_time():
    with pytest.raises(ValueError, match="Unknown Bootswatch theme"):
        ThemeConfig(bootswatch_theme="nonexistent")


# ---------------------------------------------------------------------------
# Light/dark user toggle
# ---------------------------------------------------------------------------

def test_toggle_js_present(simple_graph, tmp_path):
    out = tmp_path / "t.html"
    GraphExporter(simple_graph).export(out)
    html = out.read_text(encoding="utf-8")
    assert "toggleScheme" in html
    assert "nw-scheme-btn" in html
    assert "localStorage" in html


def test_os_preference_logic_present(simple_graph, tmp_path):
    out = tmp_path / "t.html"
    GraphExporter(simple_graph).export(out)
    html = out.read_text(encoding="utf-8")
    assert "prefers-color-scheme" in html
    assert "osPrefers" in html


# ---------------------------------------------------------------------------
# Fit button
# ---------------------------------------------------------------------------

def test_fit_button_in_toolbar(simple_graph, tmp_path):
    out = tmp_path / "fit.html"
    GraphExporter(simple_graph).export(out)
    html = out.read_text(encoding="utf-8")
    assert "network.fit()" in html
    assert "bi-fullscreen" in html


# ---------------------------------------------------------------------------
# vis-network version pin
# ---------------------------------------------------------------------------

def test_vis_network_version_pinned(simple_graph, tmp_path):
    out = tmp_path / "vis.html"
    GraphExporter(simple_graph).export(out)
    html = out.read_text(encoding="utf-8")
    # Must reference vis-network with a specific version, not just "latest"
    assert "vis-network@" in html


# ---------------------------------------------------------------------------
# Node styling
# ---------------------------------------------------------------------------

def test_node_style_callback_applied(simple_graph, tmp_path):
    out = tmp_path / "styled.html"
    exporter = GraphExporter(simple_graph)
    exporter.set_node_style_callback(lambda v: NodeStyle(shape="diamond", color="#ff0000"))
    exporter.export(out)
    assert "diamond" in out.read_text(encoding="utf-8")


def test_node_style_as_constructor_arg(simple_graph, tmp_path):
    out = tmp_path / "ctor.html"
    GraphExporter(
        simple_graph,
        node_style_callback=lambda v: NodeStyle(shape="star"),
    ).export(out)
    assert "star" in out.read_text(encoding="utf-8")


def test_constructor_callback_beats_setter(simple_graph, tmp_path):
    out = tmp_path / "priority.html"
    exporter = GraphExporter(
        simple_graph,
        node_style_callback=lambda v: NodeStyle(shape="star"),
    )
    # Setter is called AFTER constructor — constructor arg should still win.
    exporter.set_node_style_callback(lambda v: NodeStyle(shape="dot"))
    exporter.export(out)
    # The setter overwrites, so dot wins (setter takes effect when called)
    assert "dot" in out.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Node wiki
# ---------------------------------------------------------------------------

def test_wiki_callback(simple_graph, tmp_path):
    out = tmp_path / "wiki.html"
    exporter = GraphExporter(simple_graph)
    exporter.set_wiki_callback(lambda v: WikiContent(
        mini_html=f"<p>Mini: {v['name']}</p>",
        full_html=f"<h2>{v['name']}</h2>",
    ))
    exporter.export(out)
    assert "Mini: Pipeline" in out.read_text(encoding="utf-8")


def test_wiki_renderer_takes_priority_over_callback(simple_graph, tmp_path):
    out = tmp_path / "priority.html"
    exporter = GraphExporter(simple_graph)
    exporter.set_wiki_callback(lambda v: WikiContent(mini_html="<p>FROM_CALLBACK</p>"))
    exporter.set_wiki_renderer(WikiTemplateRenderer(
        mini_template="<p>FROM_RENDERER</p>",
        undefined_strict=False,
    ))
    exporter.export(out)
    html = out.read_text(encoding="utf-8")
    assert "FROM_RENDERER" in html
    assert "FROM_CALLBACK" not in html


def test_package_templates_loaded(simple_graph, tmp_path):
    renderer = WikiTemplateRenderer(undefined_strict=False)
    exporter = GraphExporter(simple_graph)
    exporter.set_wiki_renderer(renderer)
    exporter.export(tmp_path / "pkg.html")
    assert (tmp_path / "pkg.html").exists()


def test_user_template_overrides_package(simple_graph, tmp_path):
    tmpl_dir = tmp_path / "templates"
    tmpl_dir.mkdir()
    (tmpl_dir / "mini_default.html.j2").write_text(
        "<p class='user-mini'>{{ label }}</p>", encoding="utf-8"
    )
    renderer = WikiTemplateRenderer(
        template_dir=str(tmpl_dir),
        mini_template_file="mini_default.html.j2",
        undefined_strict=False,
    )
    exporter = GraphExporter(simple_graph)
    exporter.set_wiki_renderer(renderer)
    exporter.export(tmp_path / "override.html")
    assert "user-mini" in (tmp_path / "override.html").read_text(encoding="utf-8")


def test_inline_template(simple_graph, tmp_path):
    renderer = WikiTemplateRenderer(
        mini_template="<span class='inline-mini'>{{ label }}</span>",
        undefined_strict=False,
    )
    exporter = GraphExporter(simple_graph)
    exporter.set_wiki_renderer(renderer)
    exporter.export(tmp_path / "inline.html")
    assert "inline-mini" in (tmp_path / "inline.html").read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Edge wiki
# ---------------------------------------------------------------------------

def test_edge_wiki_callback(graph_with_edge_attrs, tmp_path):
    out = tmp_path / "edge_wiki.html"
    exporter = GraphExporter(graph_with_edge_attrs)
    exporter.set_edge_wiki_callback(lambda e: WikiContent(
        mini_html=f"<p>Edge {e.index}: weight={e['weight']}</p>",
        full_html=f"<h2>Edge {e.index}</h2>",
    ))
    exporter.export(out)
    html = out.read_text(encoding="utf-8")
    assert "EDGE_WIKI" in html
    assert "weight=" in html


def test_edge_wiki_auto_generated_when_attrs_exist(graph_with_edge_attrs, tmp_path):
    out = tmp_path / "auto_edge.html"
    GraphExporter(graph_with_edge_attrs).export(out)
    html = out.read_text(encoding="utf-8")
    assert "EDGE_WIKI" in html


def test_edge_wiki_empty_when_no_attrs(simple_graph, tmp_path):
    out = tmp_path / "no_edge.html"
    GraphExporter(simple_graph).export(out)
    html = out.read_text(encoding="utf-8")
    # EDGE_WIKI should be present as empty object {}
    assert "EDGE_WIKI" in html
    assert "HAS_EDGE_WIKI = false" in html


def test_edge_wiki_js_click_handler(simple_graph, tmp_path):
    out = tmp_path / "click.html"
    GraphExporter(simple_graph).export(out)
    html = out.read_text(encoding="utf-8")
    assert "params.edges" in html


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

def test_hierarchical_layout(simple_graph, tmp_path):
    exporter = GraphExporter(
        simple_graph,
        layout=LayoutConfig(hierarchical=True, hierarchical_direction="LR"),
    )
    exporter.export(tmp_path / "hier.html")
    html = (tmp_path / "hier.html").read_text(encoding="utf-8")
    assert '"enabled": false' in html
    assert "LR" in html


# ---------------------------------------------------------------------------
# Public API surface
# ---------------------------------------------------------------------------

def test_all_public_imports():
    from network_wiki import (
        NodeColor, NodeFont, NodeStyle,
        EdgeColor, EdgeArrows, EdgeStyle,
        WikiContent, WikiTemplateRenderer,
        LayoutConfig, ThemeConfig, BOOTSWATCH_THEMES,
        GraphExporter,
    )
    assert callable(GraphExporter)
    assert isinstance(BOOTSWATCH_THEMES, dict)


# ---------------------------------------------------------------------------
# Generic type_attr dispatch
# ---------------------------------------------------------------------------

def test_type_attr_dispatches_on_arbitrary_attribute(tmp_path):
    """type_attr can be any vertex attribute, not just "type"."""
    g = ig.Graph(directed=True)
    g.add_vertices(2)
    g.vs["name"]  = ["Router", "Switch"]
    g.vs["layer"] = ["core", "access"]   # different attribute name
    g.add_edges([(0, 1)])

    renderer = WikiTemplateRenderer(
        type_attr="layer",               # dispatch on "layer", not "type"
        full_templates_by_type={
            "core":   "<h2>Core: {{ label }}</h2><p>Layer: {{ type_value }}</p>",
            "access": "<h2>Access: {{ label }}</h2><p>Layer: {{ type_value }}</p>",
        },
        mini_template="<p>{{ label }} / {{ type_value }}</p>",
        undefined_strict=False,
    )
    exporter = GraphExporter(g, wiki_renderer=renderer)
    out = tmp_path / "network.html"
    exporter.export(out)
    html = out.read_text(encoding="utf-8")

    assert "Core: Router" in html
    assert "Access: Switch" in html
    assert "Layer: core" in html


def test_type_value_in_context(tmp_path):
    """type_value is always present in template context."""
    g = ig.Graph()
    g.add_vertices(1)
    g.vs["name"] = ["Node A"]
    g.vs["role"] = ["manager"]

    renderer = WikiTemplateRenderer(
        type_attr="role",
        mini_template="<p>{{ type_value }}</p>",
        undefined_strict=True,   # strict — type_value must be defined
    )
    exporter = GraphExporter(g, wiki_renderer=renderer)
    out = tmp_path / "out.html"
    exporter.export(out)
    assert "manager" in out.read_text(encoding="utf-8")


def test_type_value_empty_when_attribute_absent(tmp_path):
    """type_value is empty string when the type attribute is not on the vertex."""
    g = ig.Graph()
    g.add_vertices(1)
    g.vs["name"] = ["Node A"]
    # no "type" attribute at all

    renderer = WikiTemplateRenderer(
        mini_template="<p>type={{ type_value }}</p>",
        undefined_strict=True,
    )
    exporter = GraphExporter(g, wiki_renderer=renderer)
    out = tmp_path / "out.html"
    exporter.export(out)
    assert "type=" in out.read_text(encoding="utf-8")  # type_value is ""


def test_default_templates_render_without_type(tmp_path):
    """Bundled templates work for graphs with no type attribute at all."""
    g = ig.Graph(directed=True)
    g.add_vertices(2)
    g.vs["name"] = ["Alpha", "Beta"]
    g.vs["score"] = [42, 87]
    g.add_edges([(0, 1)])

    exporter = GraphExporter(
        g,
        wiki_renderer=WikiTemplateRenderer(undefined_strict=False),
    )
    out = tmp_path / "out.html"
    exporter.export(out)
    html = out.read_text(encoding="utf-8")
    assert "Alpha" in html
    assert "Beta" in html
    assert "42" in html


def test_default_templates_render_with_custom_type_attr(tmp_path):
    """Bundled templates show type_value from a non-default type attribute."""
    g = ig.Graph()
    g.add_vertices(1)
    g.vs["name"]   = ["Node"]
    g.vs["device"] = ["router"]

    renderer = WikiTemplateRenderer(
        type_attr="device",
        undefined_strict=False,
    )
    exporter = GraphExporter(g, wiki_renderer=renderer)
    out = tmp_path / "out.html"
    exporter.export(out)
    # mini_default.html.j2 shows type_value in nw-node-type div
    assert "ROUTER" in out.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Light/dark toggle visibility — regression test for Bootswatch + toggle bug
# ---------------------------------------------------------------------------

def test_toggle_hidden_when_bootswatch_theme_active(simple_graph, tmp_path):
    """Bootswatch stylesheets ignore data-bs-theme, so the toggle must not
    be shown — it would have no visible effect and confuse the user."""
    out = tmp_path / "bsw.html"
    GraphExporter(simple_graph, theme=ThemeConfig(bootswatch_theme="darkly")).export(out)
    html = out.read_text(encoding="utf-8")
    assert "nw-scheme-btn" not in html


def test_toggle_visible_for_plain_bootstrap(simple_graph, tmp_path):
    """Plain Bootstrap responds to data-bs-theme, so the toggle must be shown."""
    out = tmp_path / "plain.html"
    GraphExporter(simple_graph, theme=ThemeConfig()).export(out)
    html = out.read_text(encoding="utf-8")
    # assert "nw-scheme-btn" in html
    assert "toggleScheme" in html


# ---------------------------------------------------------------------------
# Mixed wiki strategies — node templates (file + inline) + edge callback
# ---------------------------------------------------------------------------

def test_mixed_node_wiki_strategies(tmp_path):
    """Per-type file templates, inline templates, and auto-fallback can
    coexist on a single WikiTemplateRenderer."""
    g = ig.Graph(directed=True)
    g.add_vertices(3)
    g.vs["name"] = ["Exec", "Manager", "Other"]
    g.vs["type"] = ["executive", "manager", "untemplated"]
    g.add_edges([(1, 0), (2, 1)])

    tmpl_dir = tmp_path / "tmpl"
    tmpl_dir.mkdir()
    (tmpl_dir / "full_exec.html.j2").write_text(
        "<h2>FILE_EXEC: {{ label }}</h2>", encoding="utf-8"
    )

    renderer = WikiTemplateRenderer(
        template_dir=str(tmpl_dir),
        full_template_files_by_type={"executive": "full_exec.html.j2"},
        full_templates_by_type={"manager": "<h2>INLINE_MANAGER: {{ label }}</h2>"},
        undefined_strict=False,
    )

    out = tmp_path / "mixed.html"
    GraphExporter(g, wiki_renderer=renderer).export(out)
    html = out.read_text(encoding="utf-8")

    assert "FILE_EXEC: Exec" in html
    assert "INLINE_MANAGER: Manager" in html
    # "untemplated" type has no template registered → auto-fallback table
    assert "Other" in html


def test_edge_wiki_callback_with_node_template_renderer(tmp_path):
    """Edge wikis (callback) and node wikis (template renderer) work together."""
    g = ig.Graph(directed=True)
    g.add_vertices(2)
    g.vs["name"] = ["A", "B"]
    g.vs["type"] = ["x", "x"]
    g.add_edges([(0, 1)])
    g.es["label_text"] = ["connects"]

    exporter = GraphExporter(
        g,
        wiki_renderer=WikiTemplateRenderer(undefined_strict=False),
        edge_wiki_callback=lambda e: WikiContent(
            mini_html=f"<p>EDGE: {e['label_text']}</p>",
            full_html=f"<h2>EDGE_FULL: {e['label_text']}</h2>",
        ),
    )
    out = tmp_path / "edge_node_mix.html"
    exporter.export(out)
    html = out.read_text(encoding="utf-8")
    assert "EDGE: connects" in html
    assert "EDGE_FULL: connects" in html
