# Rendering Pipeline

## Step 1: Graph Traversal

`_build_nodes()` iterates over `graph.vs`:

1. Extract label (`name` → `label` → `"Node N"`)
2. Apply node style callback or fallback
3. Generate wiki content (renderer → callback → auto-gen)

Returns `(vis_nodes_list, wiki_content_map)`.

## Step 2: Edge Construction

`_build_edges()` processes `graph.es`:

1. Get edge index for JS lookup
2. Resolve edge style
3. Build edge wiki map only if callback exists or attributes present

Returns `(vis_edges_list, edge_wiki_map)`.

## Step 3: Template Assembly

`_build_template_vars()`:

1. Serialize nodes/edges to JSON strings
2. Convert wiki maps to `{id: {mini_html, full_html}}` dictionaries
3. Merge theme variables
4. Add layout config as JSON

Outputs dict for Jinja2 context injection.

## Step 4: Template Rendering

`render_html()`:

1. Load Jinja2 Environment with filesystem loaders (user dir → inline store → package)
2. Parse `page.html.j2` (or `page_flask.html.j2`)
3. Inject assembled vars
4. Return rendered HTML string

Final write occurs in `export()` via `Path.write_text()`.
