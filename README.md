# network-wiki

Generate interactive standalone HTML graph visualisations from [igraph](https://igraph.org) graphs, with expandable per-node wiki panels powered by [vis.js](https://visjs.github.io/vis-network/docs/network/) and [Jinja2](https://jinja.palletsprojects.com/).

Click a node → side panel opens with a mini wiki.
Click "Full wiki" → modal opens with your full Jinja2-rendered page.

## 📥 Installation

```bash
pip install network-wiki
```

Or, directly from GitHub:

```bash
pip install git+https://github.com/mark-me/network-wiki.git
```

## 🚀 Quickstart

```python
import igraph as ig
from network_wiki import GraphExporter, NodeStyle, WikiTemplateRenderer

g = ig.Graph(directed=True)
g.add_vertices(3)
g.vs["name"] = ["ETL Pipeline", "Source", "Target"]
g.vs["type"] = ["pipeline", "source", "target"]
g.add_edges([(1, 0), (0, 2)])

exporter = GraphExporter(g, title="My Graph")
exporter.export("graph.html")
```

## 🎨 Node and edge styling

Pass a callback that returns a `NodeStyle` or `EdgeStyle` per vertex/edge:

```python
COLOR_MAP = {"pipeline": "#e94560", "source": "#a8dadc", "target": "#f5a623"}

exporter.set_node_style_callback(lambda v: NodeStyle(
    shape="diamond" if v["type"] == "pipeline" else "box",
    color=COLOR_MAP.get(v["type"], "#888"),
    size=30,
))

exporter.set_edge_style_callback(lambda e: EdgeStyle(
    width=2,
    dashes=not e["critical"],
))
```

## 📚 Wiki content via Jinja2 templates

### Option A — your own template files

```python
from network_wiki import WikiTemplateRenderer

renderer = WikiTemplateRenderer(
    template_dir="my_templates/",       # directory with your .j2 files
    mini_template_file="mini.html.j2",  # shown in the side panel
    full_template_file="full.html.j2",  # shown in the modal
    # Override per node type:
    full_template_files_by_type={
        "pipeline": "full_pipeline.html.j2",
        "source":   "full_source.html.j2",
    },
    global_context={"project": "My Project"},   # available in every template
)
exporter.set_wiki_renderer(renderer)
```

### Option B — inline template strings

```python
renderer = WikiTemplateRenderer(
    mini_template="""
    <div class="mini-wiki">
      <div class="node-type">{{ attrs.type }}</div>
      <div class="node-desc">{{ attrs.description }}</div>
    </div>""",
    full_template="""
    <h2>{{ label }}</h2>
    <p>{{ attrs.description }}</p>
    <h3>Neighbours</h3>
    <ul>{% for n in neighbours %}<li>{{ n }}</li>{% endfor %}</ul>
    """,
)
exporter.set_wiki_renderer(renderer)
```

### Template variables

Every template receives:

| Variable | Type | Description |
|---|---|---|
| `v` | `igraph.Vertex` | The vertex object itself |
| `attrs` | `dict` | All vertex attributes `{name: value}` |
| `label` | `str` | Display name |
| `index` | `int` | Vertex index |
| `n_in` | `int` | Number of incoming edges |
| `n_out` | `int` | Number of outgoing edges |
| `neighbours` | `list[str]` | Names of neighbouring nodes |
| `graph` | `igraph.Graph` | The full graph |
| `...` | | Anything you pass via `global_context` |

### Template resolution order

For each node, the renderer picks the **first matching template**:

1. Per-type file (`full_template_files_by_type`)
2. Per-type inline (`full_templates_by_type`)
3. Default file (`full_template_file`)
4. Default inline (`full_template`)
5. Built-in package fallback (`full_default.html.j2`)

### Built-in templates

The package ships with fallback templates that work out of the box:

| File | Used for |
|---|---|
| `mini_default.html.j2` | Mini wiki (side panel) |
| `full_default.html.j2` | Full wiki (modal) — generic fallback |
| `full_pipeline.html.j2` | Full wiki for `type="pipeline"` |
| `full_source.html.j2` | Full wiki for `type="source"` |

You can override any of these by placing a file with the same name in your `template_dir`.

## 🖼️ Layout and theme

```python
from network_wiki import LayoutConfig, ThemeConfig

exporter = GraphExporter(
    g,
    layout=LayoutConfig(
        hierarchical=True,
        hierarchical_direction="LR",  # left-to-right DAG
    ),
    theme=ThemeConfig(
        page_bg="#1a1a2e",
        accent="#e94560",
        panel_width_px=400,
    ),
)
```

## 🛠️ Development

```bash
git clone https://github.com/mark-me/network-wiki.git
cd network-wiki
pip install -e ".[dev]"
pytest
```

## ⚖️ License

MIT
