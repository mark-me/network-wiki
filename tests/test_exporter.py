"""Smoke tests voor network-wiki."""
import igraph as ig
import pytest
from network_wiki import (
    GraphExporter, NodeStyle, EdgeStyle,
    WikiContent, WikiTemplateRenderer,
    LayoutConfig, ThemeConfig,
)


@pytest.fixture
def simple_graph():
    g = ig.Graph(directed=True)
    g.add_vertices(3)
    g.vs["name"] = ["Pipeline", "Bron", "Target"]
    g.vs["type"] = ["pipeline", "source", "target"]
    g.vs["description"] = ["Centrale pipeline", "Bronmodel", "DWH tabel"]
    g.add_edges([(1, 0), (0, 2)])
    return g


def test_export_default(simple_graph, tmp_path):
    out = tmp_path / "test.html"
    GraphExporter(simple_graph).export(out)
    html = out.read_text(encoding="utf-8")
    assert "vis-network" in html
    assert "bootstrap" in html.lower()
    assert "Pipeline" in html
    assert "WIKI_DATA" in html


def test_bootstrap_theming(simple_graph, tmp_path):
    out = tmp_path / "themed.html"
    GraphExporter(
        simple_graph,
        theme=ThemeConfig(accent_color="#e94560", default_color_scheme="dark"),
    ).export(out)
    html = out.read_text(encoding="utf-8")
    assert "#e94560" in html
    assert 'data-bs-theme="dark"' in html


def test_theme_toggle_js(simple_graph, tmp_path):
    out = tmp_path / "toggle.html"
    GraphExporter(simple_graph).export(out)
    html = out.read_text(encoding="utf-8")
    assert "toggleTheme" in html
    assert "nw-theme-toggle" in html


def test_node_style_callback(simple_graph, tmp_path):
    out = tmp_path / "styled.html"
    exporter = GraphExporter(simple_graph)
    exporter.set_node_style_callback(
        lambda v: NodeStyle(shape="diamond", color="#ff0000")
    )
    exporter.export(out)
    assert "diamond" in out.read_text(encoding="utf-8")


def test_wiki_callback(simple_graph, tmp_path):
    out = tmp_path / "wiki.html"
    exporter = GraphExporter(simple_graph)
    exporter.set_wiki_callback(
        lambda v: WikiContent(
            mini_html=f"<p>Mini: {v['name']}</p>",
            full_html=f"<h2>{v['name']}</h2>",
        )
    )
    exporter.export(out)
    html = out.read_text(encoding="utf-8")
    assert "Mini: Pipeline" in html


def test_package_templates_loaded(simple_graph, tmp_path):
    renderer = WikiTemplateRenderer(undefined_strict=False)
    exporter = GraphExporter(simple_graph)
    exporter.set_wiki_renderer(renderer)
    exporter.export(tmp_path / "pkg_tmpl.html")


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


def test_hierarchical_layout(simple_graph, tmp_path):
    exporter = GraphExporter(
        simple_graph,
        layout=LayoutConfig(hierarchical=True, hierarchical_direction="LR"),
    )
    exporter.export(tmp_path / "hier.html")
    html = (tmp_path / "hier.html").read_text(encoding="utf-8")
    assert '"enabled": false' in html
    assert "LR" in html


def test_module_imports():
    from network_wiki import (
        NodeColor, NodeFont, NodeStyle,
        EdgeColor, EdgeArrows, EdgeStyle,
        WikiContent, WikiTemplateRenderer,
        LayoutConfig, ThemeConfig, GraphExporter,
    )
