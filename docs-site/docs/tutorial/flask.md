# Flask Integration

Serve one or more dynamic graphs with a single Flask app, using `GraphView` — a self-contained Blueprint built on top of `GraphExporter`.

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

Visit [http://localhost:5000/graph/](http://localhost:5000/graph/). Internally, passing an exporter directly to `GraphView(...)` registers it under the name `"default"`, so `/graph/` redirects to `/graph/default/`. The data is served from `/graph/default/data`.

## Multiple Graphs with Picker

Register named graphs explicitly with `.add(name, exporter, title=...)`:

```python
view = GraphView(url_prefix="/graphs")
view.add("pipeline", etl_exporter, title="ETL Pipeline")
view.add("schema", schema_exporter, title="DB Schema")
view.register(app)
```

URLs:

* `/graphs/` → redirects to the first registered graph (`pipeline`, in registration order)
* `/graphs/pipeline/` → ETL page, with a picker dropdown in the toolbar
* `/graphs/schema/` → DB schema page, same picker
* `/graphs/pipeline/data` and `/graphs/schema/data` → JSON payloads fetched by the page

When more than one graph is registered, every page shows a dropdown that lets the user switch graphs without a full page reload.

## Dynamic Graphs

Pass a zero-argument callable instead of an exporter to rebuild the graph fresh on every request — useful for data from a database or external API:

```python
def build_live_graph() -> GraphExporter:
    g = fetch_graph_from_db()   # your own data-loading logic
    return GraphExporter(g, title="Live")

view = GraphView(url_prefix="/live")
view.add("live", build_live_graph, title="Live")
view.register(app)
```

The factory is called on every request to `/live/live/` and `/live/live/data` — there is no caching, so each page load (and each picker switch) reflects current data.

## How It Works

`GraphView` does not call `GraphExporter.export()`. Instead:

1. The page route renders a lightweight shell (`page_flask.html.j2`) with no graph data inlined
2. The shell fetches `/<name>/data` on load via JavaScript
3. The data route calls the exporter's internal `_build_template_vars()` and returns the result as JSON
4. vis.js populates its node/edge `DataSet`s from that JSON, client-side

See [Architecture → Data Flow — Flask Serving](../developer/architecture.md#data-flow--flask-serving) for the full diagram.
