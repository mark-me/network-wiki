"""Smoke tests for network-wiki."""
import igraph as ig
import pytest
from network_wiki import (
    GraphExporter, NodeStyle, EdgeStyle,
    WikiContent, WikiTemplateRenderer,
    LayoutConfig, ThemeConfig, BOOTSWATCH_THEMES,
)


@pytest.fixture
def simple_graph():
    g = ig.Graph(directed=True)
    g.add_vertices(3)
    g.vs["name"] = ["Pipeline", "Source", "Target"]
    g.vs["type"] = ["pipeline", "source", "target"]
    g.vs["description"] = ["Central pipeline", "Source model", "DWH table"]
    g.add_edges([(1, 0), (0, 2)])
    return g


# ── Basic export ──────────────────────────────────────────────────────────────

def test_export_default(simple_graph, tmp_path):
    out = tmp_path / "test.html"
    GraphExporter(simple_graph).export(out)
    html = out.read_text(encoding="utf-8")
    assert "vis-network" in html
    assert "bootstrap" in html.lower()
    assert "Pipeline" in html
    assert "WIKI_DATA" in html


def test_export_writes_file(simple_graph, tmp_path):
    out = tmp_path / "out.html"
    result = GraphExporter(simple_graph).export(out)
    assert result == out.resolve()
    assert out.exists()


# ── Bootswatch theming ────────────────────────────────────────────────────────

def test_bootswatch_light_theme(simple_graph, tmp_path):
    out = tmp_path / "light.html"
    GraphExporter(
        simple_graph,
        theme=ThemeConfig(bootswatch_theme="flatly"),
    ).export(out)
    html = out.read_text(encoding="utf-8")
    assert "bootswatch" in html
    assert "flatly" in html
    assert 'data-bs-theme="light"' in html


def test_bootswatch_dark_theme(simple_graph, tmp_path):
    out = tmp_path / "dark.html"
    GraphExporter(
        simple_graph,
        theme=ThemeConfig(bootswatch_theme="darkly"),
    ).export(out)
    html = out.read_text(encoding="utf-8")
    assert "darkly" in html
    assert 'data-bs-theme="dark"' in html


def test_no_bootswatch_uses_plain_bootstrap(simple_graph, tmp_path):
    out = tmp_path / "plain.html"
    GraphExporter(simple_graph, theme=ThemeConfig()).export(out)
    html = out.read_text(encoding="utf-8")
    assert "bootswatch" not in html
    assert "bootstrap@" in html


def test_invalid_bootswatch_theme_raises():
    with pytest.raises(ValueError, match="Unknown Bootswatch theme"):
        ThemeConfig(bootswatch_theme="nonexistent")


def test_bootswatch_themes_catalogue():
    assert "flatly" in BOOTSWATCH_THEMES
    assert "darkly" in BOOTSWATCH_THEMES
    assert BOOTSWATCH_THEMES["darkly"] == "dark"
    assert BOOTSWATCH_THEMES["flatly"] == "light"


# ── User light/dark toggle ────────────────────────────────────────────────────

def test_scheme_toggle_js_present(simple_graph, tmp_path):
    out = tmp_path / "toggle.html"
    GraphExporter(simple_graph).export(out)
    html = out.read_text(encoding="utf-8")
    assert "toggleScheme" in html
    assert "nw-scheme-btn" in html
    assert "localStorage" in html
    assert "prefers-color-scheme" in html


def test_os_preference_fallback_js(simple_graph, tmp_path):
    """The page must include the OS-preference fallback logic."""
    out = tmp_path / "os.html"
    GraphExporter(simple_graph).export(out)
    html = out.read_text(encoding="utf-8")
    assert "osPrefers" in html


# ── Node / edge styling ───────────────────────────────────────────────────────

def test_node_style_callback(simple_graph, tmp_path):
    out = tmp_path / "styled.html"
    exporter = GraphExporter(simple_graph)
    exporter.set_node_style_callback(lambda v: NodeStyle(shape="diamond", color="#ff0000"))
    exporter.export(out)
    assert "diamond" in out.read_text(encoding="utf-8")


# ── Wiki content ──────────────────────────────────────────────────────────────

def test_wiki_callback(simple_graph, tmp_path):
    out = tmp_path / "wiki.html"
    exporter = GraphExporter(simple_graph)
    exporter.set_wiki_callback(lambda v: WikiContent(
        mini_html=f"<p>Mini: {v['name']}</p>",
        full_html=f"<h2>{v['name']}</h2>",
    ))
    exporter.export(out)
    assert "Mini: Pipeline" in out.read_text(encoding="utf-8")


def test_package_templates_loaded(simple_graph, tmp_path):
    renderer = WikiTemplateRenderer(undefined_strict=False)
    exporter = GraphExporter(simple_graph)
    exporter.set_wiki_renderer(renderer)
    exporter.export(tmp_path / "pkg.html")


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


# ── Layout ────────────────────────────────────────────────────────────────────

def test_hierarchical_layout(simple_graph, tmp_path):
    exporter = GraphExporter(
        simple_graph,
        layout=LayoutConfig(hierarchical=True, hierarchical_direction="LR"),
    )
    exporter.export(tmp_path / "hier.html")
    html = (tmp_path / "hier.html").read_text(encoding="utf-8")
    assert '"enabled": false' in html
    assert "LR" in html


# ── Public API ────────────────────────────────────────────────────────────────

def test_module_imports():
    from network_wiki import (
        NodeColor, NodeFont, NodeStyle,
        EdgeColor, EdgeArrows, EdgeStyle,
        WikiContent, WikiTemplateRenderer,
        LayoutConfig, ThemeConfig, BOOTSWATCH_THEMES,
        GraphExporter,
    )
