# network-wiki

Generate interactive standalone HTML graph visualisations from [igraph](https://igraph.org) graphs, with expandable per-node and per-edge wiki panels, [Bootstrap 5](https://getbootstrap.com) / [Bootswatch](https://bootswatch.com) theming, and [Jinja2](https://jinja.palletsprojects.com/) templates.

- Click a node or edge → side panel opens with a compact wiki
- Click **Wiki** → full-screen modal with your Jinja2-rendered page
- User toggles light / dark mode; preference persists in `localStorage` and defaults to the OS setting
- Works as a **static HTML file** or inside a **Flask application**

---

## 📥 Installation

### pip

```bash
# Core package (static HTML export)
pip install network-wiki

# With Flask integration
pip install "network-wiki[flask]"

# Directly from GitHub
pip install git+https://github.com/mark-me/network-wiki.git
```

### uv

```bash
# Core package
uv add network-wiki

# With Flask integration
uv add "network-wiki[flask]"

# Directly from GitHub
uv add git+https://github.com/mark-me/network-wiki.git
```

---

## 🗿 Quickstart — static HTML

```python
import igraph as ig
from network_wiki import GraphExporter, ThemeConfig

g = ig.Graph(directed=True)
g.add_vertices(3)
g.vs["name"] = ["Source", "Pipeline", "Target"]
g.vs["type"] = ["source", "pipeline", "target"]
g.add_edges([(0, 1), (1, 2)])

exporter = GraphExporter(
    g,
    title="My Graph",
    theme=ThemeConfig(bootswatch_theme="flatly"),
)
exporter.export("graph.html")
```

Open `graph.html` in any browser — no server required.

---

## 💫 Quickstart — Flask

Serve one or more graphs as interactive web pages. The graph can be replaced in the browser without a full page reload.

```python
from flask import Flask
from network_wiki import GraphExporter, ThemeConfig
from network_wiki.flask_view import GraphView
import igraph as ig

app = Flask(__name__)

g = ig.Graph(directed=True)
g.add_vertices(3)
g.vs["name"] = ["Source", "Pipeline", "Target"]
g.add_edges([(0, 1), (1, 2)])

exporter = GraphExporter(
    g,
    title="My Graph",
    theme=ThemeConfig(bootswatch_theme="flatly"),
)

view = GraphView(exporter, url_prefix="/graph")
view.register(app)

if __name__ == "__main__":
    app.run(debug=True)
```

| URL | Description |
| --- | ----------- |
| `GET /graph/` | Interactive page (HTML shell) |
| `GET /graph/default/data` | Graph data as JSON (fetched by the page) |

### Multiple graphs with a picker

Register several exporters under one `GraphView`. The toolbar shows a dropdown that switches graphs in place — no page reload.

```python
view = GraphView(url_prefix="/graphs")
view.add("etl",    etl_exporter,    title="ETL Pipeline")
view.add("schema", schema_exporter, title="DB Schema")
view.register(app)
# http://localhost:5000/graphs/etl/
# http://localhost:5000/graphs/schema/
```

### Dynamic graphs

Pass a factory function instead of an exporter. It is called on every request, which is useful when the graph is rebuilt from a database or API.

```python
def build_live_graph() -> GraphExporter:
    g = fetch_graph_from_db()
    return GraphExporter(g, title="Live Graph")

view = GraphView(url_prefix="/live")
view.add("live", build_live_graph, title="Live")
view.register(app)
```

---

## 🖌️ Node and edge styling

Pass a callback that returns a `NodeStyle` or `EdgeStyle` per vertex / edge:

```python
from network_wiki import NodeStyle, NodeFont, EdgeStyle, EdgeArrows

COLOR_MAP = {"source": "#4a90d9", "pipeline": "#e94560", "target": "#f5a623"}

exporter = GraphExporter(
    g,
    node_style_callback=lambda v: NodeStyle(
        shape="diamond" if v["type"] == "pipeline" else "box",
        color=COLOR_MAP.get(v["type"], "#888"),
        font=NodeFont(color="#ffffff", bold=True),
        tooltip=f"{v['name']} — {v['type']}",
    ),
    edge_style_callback=lambda e: EdgeStyle(
        width=2,
        dashes=not e["critical"],
        arrows=EdgeArrows(to_enabled=True),
    ),
)
```

Callbacks can also be set after construction:

```python
exporter.set_node_style_callback(lambda v: NodeStyle(color="#2ecc71"))
exporter.set_edge_style_callback(lambda e: EdgeStyle(width=3))
```

---

## 📚 Wiki content via Jinja2 templates

### Option A — template files

```python
from network_wiki import WikiTemplateRenderer

renderer = WikiTemplateRenderer(
    template_dir="my_templates/",
    mini_template_file="mini.html.j2",   # compact side-panel view
    full_template_file="full.html.j2",   # full-screen modal view
    # Per-type overrides (dispatched on type_attr, default "type"):
    full_template_files_by_type={
        "pipeline": "full_pipeline.html.j2",
        "source":   "full_source.html.j2",
    },
    global_context={"project": "My Project"},
)
exporter = GraphExporter(g, wiki_renderer=renderer)
```

### Option B — inline strings

```python
renderer = WikiTemplateRenderer(
    mini_template="""
    <div class="nw-mini-wiki">
      <div class="nw-node-type">{{ type_value }}</div>
      <div class="nw-node-desc">{{ attrs.description }}</div>
    </div>""",
    full_template="""
    <h2>{{ label }}</h2>
    <p>{{ attrs.description }}</p>
    <ul>{% for n in neighbours %}<li>{{ n }}</li>{% endfor %}</ul>
    """,
)
```

### Dispatch on any attribute

`type_attr` controls which vertex attribute drives template selection. It does not have to be `"type"`:

```python
# Organisational chart — dispatch on "role"
WikiTemplateRenderer(
    type_attr="role",
    full_templates_by_type={
        "manager":  MANAGER_TMPL,
        "engineer": ENGINEER_TMPL,
    },
)

# Network topology — dispatch on "device_class"
WikiTemplateRenderer(
    type_attr="device_class",
    full_template_files_by_type={
        "router": "router.html.j2",
        "switch": "switch.html.j2",
    },
)
```

### Template variables

| Variable | Type | Description |
| -------- | ---- | ----------- |
| `v` | `igraph.Vertex` | The vertex object |
| `attrs` | `dict` | All vertex attributes `{name: value}` |
| `label` | `str` | Display name |
| `type_value` | `str` | Value of the `type_attr` attribute, or `""` |
| `index` | `int` | Vertex index |
| `n_in` | `int` | Number of incoming edges |
| `n_out` | `int` | Number of outgoing edges |
| `neighbours` | `list[str]` | Names of neighbouring nodes |
| `graph` | `igraph.Graph` | The full graph |
| `...` | | Anything passed via `global_context` |

### Template resolution order

For each node, the first matching template wins:

1. Per-type file (`full_template_files_by_type`)
2. Per-type inline (`full_templates_by_type`)
3. Default file (`full_template_file`)
4. Default inline (`full_template`)
5. Built-in package fallback (`full_default.html.j2`)

The built-in fallbacks render all vertex attributes as a table — no configuration needed.

---

## 🎨 Theming

```python
from network_wiki import ThemeConfig

# Bootswatch theme (developer-chosen at export time)
ThemeConfig(bootswatch_theme="flatly")   # light theme
ThemeConfig(bootswatch_theme="darkly")   # dark theme
ThemeConfig(bootswatch_theme="minty", accent_color="#2ecc71")

# Plain Bootstrap (no Bootswatch)
ThemeConfig()
```

The end-user can toggle light / dark mode with the toolbar button. Their choice is saved in `localStorage` and falls back to the OS `prefers-color-scheme` setting on first load.

**Available Bootswatch themes:**

| Light | Dark |
| ----- | ---- |
| cerulean, cosmo, flatly, journal, litera, lumen, lux, materia, minty, morph, pulse, quartz, sandstone, simplex, sketchy, spacelab, united, yeti, zephyr | cyborg, darkly, slate, solar, superhero, vapor |

---

## 🗺️ Layout

```python
from network_wiki import LayoutConfig

LayoutConfig(
    hierarchical=True,
    hierarchical_direction="LR",   # left-to-right DAG; also "UD", "RL", "DU"
)

LayoutConfig(
    solver="forceAtlas2Based",
    gravity=-80,
    spring_length=250,
    navigation_buttons=True,
)
```

---

## 🛠️ Development

### pip

```bash
git clone https://github.com/mark-me/network-wiki.git
cd network-wiki
pip install -e ".[dev,flask]"
pytest
```

### uv

```bash
git clone https://github.com/mark-me/network-wiki.git
cd network-wiki
uv sync --extra dev --extra flask
uv run pytest
```

---

## ⚖️ License

MIT
