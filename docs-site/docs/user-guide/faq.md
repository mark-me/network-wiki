# FAQ

Common questions and troubleshooting tips.

## Why don't my nodes display labels correctly?

Ensure vertices have either a `"name"` or `"label"` attribute. Falls back to `"Node <index>"` if absent.

## Can I use images instead of shapes?

Yes, set `shape="image"` or `shape="circularImage"` and provide a URL or data-URI via `NodeStyle.image`. See [Node and Edge Styling](styling.md).

## My edges aren't clickable

Edges only get a wiki panel when either:

* an `edge_wiki_callback` is registered, **or**
* the graph has at least one edge attribute (e.g. `g.es["weight"] = [...]`) — in that case content is auto-generated

Edges with neither will not respond to clicks. See [Templates → Edge Wikis](../tutorial/templates.md#edge-wikis).

## Why doesn't the light/dark toggle button appear?

The toggle is **intentionally hidden** when a Bootswatch theme is set (`ThemeConfig(bootswatch_theme=...)`). Bootswatch stylesheets are built for one fixed appearance and don't respond to Bootstrap's `data-bs-theme` attribute, so showing the toggle there would do nothing visible.

To get a user-toggleable light/dark mode, use plain Bootstrap instead:

```python
ThemeConfig()  # no bootswatch_theme — toggle is shown
```

See [Themes → Dark/Light Mode Toggle](themes.md#darklight-mode-toggle) for the full explanation.

## Templating doesn't find my custom templates

Verify that `template_dir` is correct relative to your script's working directory at runtime — it is **not** resolved relative to the script file's location. Use an absolute path or `Path(__file__).parent / "templates"` if you need this to work regardless of the current working directory.

## JavaScript console shows errors after export / the page is blank offline

network-wiki's bundled templates load Bootstrap (or Bootswatch), Bootstrap Icons, and vis.js from public CDNs. An internet connection is required when the generated HTML page is opened. For fully offline use, download the assets locally, vendor them alongside the exported HTML, and adjust the `<link>`/`<script>` URLs in a custom copy of `page.html.j2` passed via your own template directory.

## Does `GraphExporter` work without Flask installed?

Yes — Flask is an optional dependency. `GraphExporter.export()` and `render_html()` have no Flask dependency at all. Only `GraphView` (in `network_wiki.flask_view`) requires Flask; importing it without Flask installed raises a clear `ImportError` rather than failing silently.

## How many Bootswatch themes are available?

25 — 19 light and 6 dark. See [Themes](themes.md) for the full list, or inspect `network_wiki.BOOTSWATCH_THEMES` at runtime.
