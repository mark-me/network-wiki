# Flask Integration

Serve multiple dynamic graphs with a single Flask app.

## Single Graph

```python
from flask import Flask
from network_wiki.flask_view import GraphView
from network_wiki import GraphExporter, ThemeConfig
import igraph as ig

app = Flask(__name__)

g = ig.Graph(directed=True)
g.add_vertices(3)
g.vs["name"] = ["A", "B", "C"]
g.add_edges([(0, 1), (1, 2)])

view = GraphView(
    GraphExporter(g, title="My Graph", theme=ThemeConfig(bootswatch_theme="flatly")),
    url_prefix="/graph",
)
view.register(app)

if __name__ == "__main__":
    app.run(debug=True)
```

Visit [http://localhost:5000/graph/](http://localhost:5000/graph/) to view.

## Multiple Graphs with Picker

```python
etl_view = GraphView(url_prefix="/graphs")
etl_view.add("pipeline", etl_exporter, title="ETL Pipeline")
etl_view.add("schema", schema_exporter, title="DB Schema")
etl_view.register(app)
```

URLs:

* `/graphs/` → redirects to first graph
* `/graphs/pipeline/` → ETL page with picker
* `/graphs/schema/` → DB schema page with picker

## Dynamic Graphs

Rebuild graphs on every request:

```python
def build_live_graph():
    # Fetch from database, recompute, etc.
    return g

view = GraphView(url_prefix="/live")
view.add("live", lambda: GraphExporter(build_live_graph(), title="Live"))
view.register(app)
```

The factory function is called fresh on each request.
