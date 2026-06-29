# FAQ

Common questions and troubleshooting tips.

## Why don't my nodes display labels correctly?

Ensure vertices have either a `"name"` or `"label"` attribute. Falls back to `"Node <index>"` if absent.

## Can I use images instead of shapes?

Yes, set `shape="image"` or `"circularImage"` and provide URL/data-URI via `NodeStyle.image`.

## My edges aren't clickable

You must register `edge_wiki_callback` or enable edge attributes for automatic wiki generation. Edges without associated wiki content won't trigger the panel.

## Templating doesn't find my custom templates

Verify `template_dir` path is correct relative to execution location. Check files exist at runtime.

## JavaScript console shows errors after export

Ensure internet connection is required—Bootstrap and vis.js load from CDN. For offline use, download assets locally and adjust CDN URLs.
