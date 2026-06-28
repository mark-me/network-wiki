# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project uses [semantic versioning](https://semver.org/).

---

## [0.4.0] – 2024-07-01

### Added
- **Edge wiki support** – clicking an edge now opens the wiki side-panel, just
  like clicking a node.  Supply an `edge_wiki_callback` or let the exporter
  auto-generate content from edge attributes.
- **Fit button** in the toolbar – resets zoom and pan to show the full graph
  (`network.fit()`).
- **`BOOTSWATCH_THEMES`** exported from the top-level package so callers can
  inspect available themes without importing from `layout`.
- **`CHANGELOG.md`** (this file).

### Changed
- `ThemeConfig` replaces `accent_color` + `default_color_scheme` with
  `bootswatch_theme` (developer-chosen) while the user controls light/dark via
  a toolbar toggle persisted in `localStorage`.
- `ThemeConfig.lang` default changed from `"nl"` to `"en"` to match English
  docstrings and bundled templates.
- All bundled Jinja2 templates (`mini_default`, `full_default`,
  `full_pipeline`, `full_source`) translated to English and updated to use the
  `nw-` CSS class namespace.
- vis-network CDN URL pinned to `vis-network@9.1.9` for reproducibility.
- Callbacks can now be passed directly to `GraphExporter.__init__` as well as
  via the `set_*` setter methods.  Constructor arguments take priority.
- `_build_context` in `WikiTemplateRenderer` now uses the shared
  `_vertex_label` helper instead of duplicating the label-resolution logic.

### Fixed
- O(n²) label lookup in `export()` replaced by an O(n) dict built from
  `vis_nodes`.
- GitHub URL placeholder (`YOUR_USERNAME`) replaced with `mark-me` throughout
  `pyproject.toml`, `README.md`, and `CONTRIBUTING.md`.

---

## [0.3.0] – 2024-06-15

### Added
- Bootswatch 5 theme support via `ThemeConfig(bootswatch_theme=...)`.
- Validation of theme name in `ThemeConfig.__post_init__` (raises `ValueError`
  on unknown names).
- `ThemeConfig.css_url` and `ThemeConfig.base_scheme` properties.
- User light/dark toggle in the toolbar, persisted in `localStorage`, with
  automatic OS preference detection (`prefers-color-scheme`).

### Changed
- Codebase split from a single `exporter.py` into `node_style`, `edge_style`,
  `wiki`, `layout`, and `exporter` modules.
- `page.html.j2` introduced as a Jinja2 template for the full page structure.
- All Python docstrings converted to English (Google style).

---

## [0.2.0] – 2024-05-20

### Added
- Bootstrap 5 UI with light/dark theming.
- `WikiTemplateRenderer` with Jinja2 template support (file-based and inline).
- Template resolution priority: per-type file → per-type inline → default file
  → default inline → bundled package fallback.
- `importlib.resources` for reliable access to bundled templates when installed
  via pip.
- GitHub Actions CI workflow (`ci.yml`).
- `CONTRIBUTING.md` with three install options (local clone, GitHub URL, path
  dependency).

---

## [0.1.0] – 2024-04-10

### Added
- Initial release.
- `GraphExporter` converting `igraph.Graph` to a standalone HTML page.
- vis.js graph with clickable nodes opening a side-panel wiki.
- `NodeStyle`, `EdgeStyle`, `WikiContent` dataclasses.
- `LayoutConfig` and `ThemeConfig`.
- Bundled Jinja2 templates for mini and full wiki content.
