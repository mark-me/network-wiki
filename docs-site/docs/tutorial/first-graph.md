# Your First Graph

## Basic Export

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

## Adding Attributes

Node attributes become wiki content automatically:

```python
g.vs["type"] = ["start", "process", "end"]
g.vs["description"] = ["Begin", "Middle step", "Finish"]
```

Click any node in the exported HTML to see its attributes in the sidebar.

## Choosing a Theme

Select from 23 Bootswatch 5 themes:

```python
from network_wiki import GraphExporter, ThemeConfig

exporter = GraphExporter(
    g,
    title="Themed Graph",
    theme=ThemeConfig(bootswatch_theme="darkly")  # Dark theme
)
exporter.export("themed.html")
```

Light themes: cerulean, cosmo, flatly, journal, litera, lumen, lux, materia, minty, morph, pulse, quartz, sandstone, simplex, sketchy, spacelab, united, yeti, zephyr

Dark themes: cyborg, darkly, slate, solar, superhero, vapor
