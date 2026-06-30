# Rendering Pipeline

## Step 1: Node Construction

`_build_nodes()` iterates over `graph.vs`:

1. Extract label (`name` → `label` → `"Node N"`)
2. Apply node style callback, or fall back to `default_node_style`
3. Generate wiki content: `wiki_renderer` → `wiki_callback` → `_auto_wiki()` (renders all vertex attributes generically)

Returns `(vis_nodes_list, node_wiki_map)`.

## Step 2: Edge Construction

`_build_edges()` iterates over `graph.es`:

1. Apply edge style callback, or fall back to `default_edge_style`; the edge's igraph index is stored on the dict for client-side lookup
2. Build the edge wiki entry only when `edge_wiki_callback` is set, **or** when no callback is set but the graph has at least one edge attribute (`graph.edge_attributes()` is non-empty) — in that case `_auto_edge_wiki()` renders the attributes generically
3. Edges with neither a callback nor any edge attributes get no wiki entry at all, so clicking them does nothing

Returns `(vis_edges_list, edge_wiki_map)`.

## Step 3: Template Assembly

`_build_template_vars()` — the single point where Python data becomes the Jinja2 context, shared by both static export and Flask serving:

1. Serialize nodes/edges to JSON strings
2. Convert node and edge wiki maps to `{id: {label, mini, full}}` dictionaries
3. Merge theme variables (`css_url`, `accent_color`, `base_scheme`, `bootswatch_theme`, ...)
4. Add the layout config as a JSON string

Returns a single dict suitable for `Template.render(**vars)`.

## Step 4: Template Rendering

`render_html(template="page.html.j2")`:

1. Load a Jinja2 `Environment` pointed at the package's bundled `templates/` directory
2. Parse the requested template — `page.html.j2` for static export, `page_flask.html.j2` for the Flask shell
3. Render with the vars from Step 3
4. Return the HTML as a string

`export(path)` calls `render_html()` and writes the result with `Path.write_text()`.

## Flask Serving Differs After Step 4

`GraphView` does **not** call `export()`. Instead:

- The page route (`/<name>/`) renders `page_flask.html.j2` directly via a separate template call that omits the graph data — the shell ships with no inline `nodes`/`edges`/wiki JSON
- The data route (`/<name>/data`) calls `_build_template_vars()` directly and returns the node/edge/wiki data as a `jsonify()` response, skipping HTML rendering entirely
- The browser fetches `/<name>/data` on page load (and again whenever the graph picker changes), then populates the vis.js `DataSet` client-side

This split is what allows `GraphView` to swap graphs without a full page reload, and to support factory-based graphs that rebuild on every request — see [Architecture](architecture.md#data-flow--flask-serving).
