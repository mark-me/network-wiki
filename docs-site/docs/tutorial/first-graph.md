# Your First Graph

## 📤 Basic Export

Start with a simple directed graph:

```python
import igraph as ig
from network_wiki import GraphExporter

g = ig.Graph(directed=True)
g.add_vertices(3)
g.vs["name"] = ["A", "B", "C"]
g.add_edges([(0, 1), (1, 2)])

exporter = GraphExporter(g, title="Simple Graph")
exporter.export("first_graph.html")
```

Open `first_graph.html` in a browser. You'll see three connected nodes; clicking any node opens a side panel.

## ➕ Adding Attributes

Vertex attributes become wiki content automatically — no extra configuration needed:

```python
g.vs["type"] = ["start", "process", "end"]
g.vs["description"] = ["Begin", "Middle step", "Finish"]
```

Click any node in the exported HTML to see its attributes listed in the side panel. This auto-generated wiki works for any attribute names — see [Templates](templates.md) once you want full control over the layout.

## 🎨 Choosing a Theme

Select from 25 Bootswatch 5 themes:

```python
from network_wiki import GraphExporter, ThemeConfig

exporter = GraphExporter(
    g,
    title="Themed Graph",
    theme=ThemeConfig(bootswatch_theme="darkly"),  # dark theme
)
exporter.export("themed.html")
```

**Light themes:** cerulean, cosmo, flatly, journal, litera, lumen, lux, materia, minty, morph, pulse, quartz, sandstone, simplex, sketchy, spacelab, united, yeti, zephyr

**Dark themes:** cyborg, darkly, slate, solar, superhero, vapor

See [Themes](../user-guide/themes.md) for the full list and how the light/dark toggle interacts with Bootswatch themes.

## 🖌️ Styling Nodes and Edges

Pass callbacks to control node and edge appearance individually:

```python
from network_wiki import GraphExporter, NodeStyle, EdgeStyle

exporter = GraphExporter(
    g,
    title="Styled Graph",
    node_style_callback=lambda v: NodeStyle(
        color="#2ecc71" if v["type"] == "start" else "#3498db",
        shape="diamond" if v["type"] == "process" else "box",
    ),
    edge_style_callback=lambda e: EdgeStyle(width=2),
)
exporter.export("styled.html")
```

Callbacks can also be set after construction with `exporter.set_node_style_callback(...)` and `exporter.set_edge_style_callback(...)`.

## ⏩ Next Steps

* [Templates](templates.md) — build rich wiki content with Jinja2
* [Flask integration](flask.md) — serve graphs dynamically from a web app
