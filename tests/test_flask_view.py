"""Tests for the Flask integration (GraphView)."""
from __future__ import annotations

import json
import pytest
import igraph as ig

from network_wiki import GraphExporter, ThemeConfig, GraphView
from network_wiki.flask_view import GraphView as _GV


@pytest.fixture
def simple_graph():
    g = ig.Graph(directed=True)
    g.add_vertices(3)
    g.vs["name"] = ["A", "B", "C"]
    g.vs["type"] = ["source", "pipeline", "target"]
    g.add_edges([(0, 1), (1, 2)])
    return g


@pytest.fixture
def exporter(simple_graph):
    return GraphExporter(
        simple_graph,
        title="Test Graph",
        theme=ThemeConfig(bootswatch_theme="flatly"),
    )


@pytest.fixture
def flask_app(exporter):
    from flask import Flask
    app = Flask(__name__)
    app.config["TESTING"] = True
    view = GraphView(url_prefix="/graph")
    view.add("test", exporter, title="Test Graph")
    view.register(app)
    return app


@pytest.fixture
def client(flask_app):
    return flask_app.test_client()


# ---------------------------------------------------------------------------
# Route existence
# ---------------------------------------------------------------------------

def test_root_redirects_to_first_graph(client):
    resp = client.get("/graph/")
    assert resp.status_code == 302
    assert "/graph/test" in resp.headers["Location"]


def test_page_route_returns_html(client):
    resp = client.get("/graph/test/")
    assert resp.status_code == 200
    assert b"text/html" in resp.content_type.encode()
    assert b"vis-network" in resp.data
    assert b"bootstrap" in resp.data.lower()


def test_data_route_returns_json(client):
    resp = client.get("/graph/test/data")
    assert resp.status_code == 200
    assert resp.content_type == "application/json"


def test_unknown_graph_page_returns_404(client):
    assert client.get("/graph/nonexistent/").status_code == 404


def test_unknown_graph_data_returns_404(client):
    assert client.get("/graph/nonexistent/data").status_code == 404


# ---------------------------------------------------------------------------
# JSON payload structure
# ---------------------------------------------------------------------------

def test_data_payload_has_required_keys(client):
    data = client.get("/graph/test/data").get_json()
    for key in ("title", "nodes", "edges", "node_wiki", "edge_wiki", "has_edge_wiki"):
        assert key in data, f"Missing key: {key}"


def test_data_payload_nodes_match_graph(client, simple_graph):
    data = client.get("/graph/test/data").get_json()
    assert len(data["nodes"]) == simple_graph.vcount()


def test_data_payload_edges_match_graph(client, simple_graph):
    data = client.get("/graph/test/data").get_json()
    assert len(data["edges"]) == simple_graph.ecount()


def test_data_payload_node_wiki_keys(client, simple_graph):
    data = client.get("/graph/test/data").get_json()
    wiki = data["node_wiki"]
    assert len(wiki) == simple_graph.vcount()
    for entry in wiki.values():
        assert "label" in entry
        assert "mini" in entry
        assert "full" in entry


def test_data_payload_title(client):
    data = client.get("/graph/test/data").get_json()
    assert data["title"] == "Test Graph"


# ---------------------------------------------------------------------------
# Page shell content
# ---------------------------------------------------------------------------

def test_page_shell_contains_data_url(client):
    html = client.get("/graph/test/").data.decode()
    assert "/graph/test/data" in html


def test_page_shell_contains_loadgraph_js(client):
    html = client.get("/graph/test/").data.decode()
    assert "loadGraph" in html


def test_page_shell_contains_bootswatch(client):
    html = client.get("/graph/test/").data.decode()
    assert "bootswatch" in html
    assert "flatly" in html


def test_page_shell_has_scheme_toggle(client):
    html = client.get("/graph/test/").data.decode()
    assert "toggleScheme" in html


def test_page_shell_no_inline_graph_data(client):
    """The Flask shell must NOT inline VIS_NODES — data comes via fetch."""
    html = client.get("/graph/test/").data.decode()
    assert "VIS_NODES = [" not in html


# ---------------------------------------------------------------------------
# Multiple graphs
# ---------------------------------------------------------------------------

@pytest.fixture
def multi_app(simple_graph):
    from flask import Flask
    app = Flask(__name__)
    app.config["TESTING"] = True

    g2 = ig.Graph(directed=True)
    g2.add_vertices(2)
    g2.vs["name"] = ["X", "Y"]
    g2.add_edges([(0, 1)])

    view = GraphView(url_prefix="/graphs")
    view.add("alpha", GraphExporter(simple_graph, title="Alpha"))
    view.add("beta",  GraphExporter(g2, title="Beta"))
    view.register(app)
    return app


def test_multi_both_pages_accessible(multi_app):
    c = multi_app.test_client()
    assert c.get("/graphs/alpha/").status_code == 200
    assert c.get("/graphs/beta/").status_code == 200


def test_multi_data_endpoints_independent(multi_app, simple_graph):
    c = multi_app.test_client()
    alpha = c.get("/graphs/alpha/data").get_json()
    beta  = c.get("/graphs/beta/data").get_json()
    assert len(alpha["nodes"]) == simple_graph.vcount()
    assert len(beta["nodes"]) == 2


def test_multi_picker_in_shell(multi_app):
    """With multiple graphs, the picker select element must be present."""
    c = multi_app.test_client()
    html = c.get("/graphs/alpha/").data.decode()
    assert "nw-graph-picker" in html
    assert "Alpha" in html
    assert "Beta" in html


# ---------------------------------------------------------------------------
# Dynamic (factory) graph
# ---------------------------------------------------------------------------

def test_factory_graph_is_called_per_request(simple_graph):
    from flask import Flask
    app = Flask(__name__)
    app.config["TESTING"] = True

    call_count = {"n": 0}

    def factory():
        call_count["n"] += 1
        return GraphExporter(simple_graph, title=f"Call {call_count['n']}")

    view = GraphView(url_prefix="/dyn")
    view.add("g", factory, title="Dynamic")
    view.register(app)

    c = app.test_client()
    d1 = c.get("/dyn/g/data").get_json()
    d2 = c.get("/dyn/g/data").get_json()
    assert call_count["n"] == 2   # factory called twice


# ---------------------------------------------------------------------------
# render_html() — static export still works
# ---------------------------------------------------------------------------

def test_render_html_returns_string(exporter):
    html = exporter.render_html()
    assert isinstance(html, str)
    assert "vis-network" in html
    assert "NODE_WIKI" in html   # static page inlines data


def test_export_still_writes_file(exporter, tmp_path):
    out = tmp_path / "out.html"
    exporter.export(out)
    assert out.exists()
    assert "NODE_WIKI" in out.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# GraphView import from top-level package
# ---------------------------------------------------------------------------

def test_graphview_importable_from_package():
    from network_wiki import GraphView
    assert GraphView is _GV


# ---------------------------------------------------------------------------
# ImportError when Flask is not installed
# ---------------------------------------------------------------------------

def test_graph_view_raises_import_error_when_flask_unavailable(monkeypatch):
    """GraphView raises ImportError with an instructive message when Flask is absent."""
    monkeypatch.setattr("network_wiki.flask_view._FLASK_AVAILABLE", False)

    g = ig.Graph(directed=True)
    g.add_vertices(2)
    g.vs["name"] = ["A", "B"]
    g.add_edges([(0, 1)])
    exporter = GraphExporter(g)

    with pytest.raises(ImportError) as exc_info:
        _GV(exporter)

    msg = str(exc_info.value).lower()
    assert "flask is required for graphview" in msg
    assert "pip install flask" in msg


# ---------------------------------------------------------------------------
# Toggle visibility with Bootswatch — regression test
# ---------------------------------------------------------------------------

def test_flask_toggle_hidden_when_bootswatch_active(simple_graph):
    """See test_exporter.py::test_toggle_hidden_when_bootswatch_theme_active
    for why this checks the rendered element rather than the bare id."""
    from flask import Flask
    app = Flask(__name__)
    app.config["TESTING"] = True
    exp = GraphExporter(simple_graph, theme=ThemeConfig(bootswatch_theme="darkly"))
    view = GraphView(url_prefix="/g")
    view.add("d", exp)
    view.register(app)

    html = app.test_client().get("/g/d/").data.decode()
    assert 'id="nw-scheme-btn"' not in html


def test_flask_toggle_visible_for_plain_bootstrap(simple_graph):
    from flask import Flask
    app = Flask(__name__)
    app.config["TESTING"] = True
    exp = GraphExporter(simple_graph, theme=ThemeConfig())
    view = GraphView(url_prefix="/g")
    view.add("p", exp)
    view.register(app)

    html = app.test_client().get("/g/p/").data.decode()
    assert "nw-scheme-btn" in html
    assert "toggleScheme" in html
