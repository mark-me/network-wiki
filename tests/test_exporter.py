"""Basic smoke tests for network-wiki."""
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
    """Export met standaard instellingen produceert een geldig HTML-bestand."""
    out = tmp_path / "test.html"
    exporter = GraphExporter(simple_graph)
    exporter.export(out)
    html = out.read_text(encoding="utf-8")
    assert "vis-network" in html
    assert "Pipeline" in html
    assert "WIKI_DATA" in html


def test_export_with_node_style_callback(simple_graph, tmp_path):
    """NodeStyle callback wordt toegepast."""
    out = tmp_path / "styled.html"
    exporter = GraphExporter(simple_graph)
    exporter.set_node_style_callback(
        lambda v: NodeStyle(shape="diamond", color="#ff0000")
    )
    exporter.export(out)
    assert "diamond" in out.read_text(encoding="utf-8")


def test_export_with_wiki_callback(simple_graph, tmp_path):
    """WikiContent callback vult de wiki-data."""
    out = tmp_path / "wiki.html"
    exporter = GraphExporter(simple_graph)
    exporter.set_wiki_callback(
        lambda v: WikiContent(
            mini_html=f"<p>Mini: {v['name']}</p>",
            full_html=f"<h2>{v['name']}</h2><p>Full wiki.</p>",
        )
    )
    exporter.export(out)
    html = out.read_text(encoding="utf-8")
    assert "Mini: Pipeline" in html
    assert "Full wiki." in html


def test_package_templates_loaded(simple_graph, tmp_path):
    """Gebundelde package-templates worden gevonden zonder template_dir."""
    out = tmp_path / "pkg_tmpl.html"
    renderer = WikiTemplateRenderer(
        mini_template_file="mini_default.html.j2",
        full_template_file="full_default.html.j2",
        undefined_strict=False,
    )
    exporter = GraphExporter(simple_graph)
    exporter.set_wiki_renderer(renderer)
    exporter.export(out)
    assert out.exists()


def test_user_template_overrides_package(simple_graph, tmp_path):
    """Een gebruikerstemplate heeft prioriteit boven de package-template."""
    tmpl_dir = tmp_path / "templates"
    tmpl_dir.mkdir()
    (tmpl_dir / "mini_default.html.j2").write_text(
        "<p class='user-mini'>{{ label }}</p>", encoding="utf-8"
    )
    out = tmp_path / "override.html"
    renderer = WikiTemplateRenderer(
        template_dir=str(tmpl_dir),
        mini_template_file="mini_default.html.j2",
        undefined_strict=False,
    )
    exporter = GraphExporter(simple_graph)
    exporter.set_wiki_renderer(renderer)
    exporter.export(out)
    assert "user-mini" in out.read_text(encoding="utf-8")


def test_inline_template_overrides_package(simple_graph, tmp_path):
    """Een inline template heeft prioriteit boven de package-template."""
    out = tmp_path / "inline.html"
    renderer = WikiTemplateRenderer(
        mini_template="<span class='inline-mini'>{{ label }}</span>",
        undefined_strict=False,
    )
    exporter = GraphExporter(simple_graph)
    exporter.set_wiki_renderer(renderer)
    exporter.export(out)
    assert "inline-mini" in out.read_text(encoding="utf-8")


def test_hierarchical_layout(simple_graph, tmp_path):
    """Hierarchisch layout schakelt physics uit."""
    out = tmp_path / "hier.html"
    exporter = GraphExporter(
        simple_graph,
        layout=LayoutConfig(hierarchical=True, hierarchical_direction="LR"),
    )
    exporter.export(out)
    html = out.read_text(encoding="utf-8")
    assert '"enabled": false' in html  # physics disabled
    assert "LR" in html
