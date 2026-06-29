# Contributing to network-wiki

## Using the repository without publishing to PyPI

You do not need to create a new project or publish the package to use it in another project.
There are three ways to install it directly from the repository.

### Option 1 — local clone (recommended)

Clone the repo once, then install it as an editable package.
Any changes you make to the source are immediately reflected — no reinstall needed.

**pip**

```bash
git clone https://github.com/mark-me/network-wiki.git
cd network-wiki
pip install -e .
```

**uv**

```bash
git clone https://github.com/mark-me/network-wiki.git
cd network-wiki
uv sync
```

In your own project (anywhere on the same machine):

```python
from network_wiki import GraphExporter, ThemeConfig
```

### Option 2 — directly from GitHub

No local clone required. The package is fetched and installed from the
repository's default branch.

**pip**

```bash
pip install git+https://github.com/mark-me/network-wiki.git
```

**uv**

```bash
uv add git+https://github.com/mark-me/network-wiki.git
```

Pin a specific tag for reproducible installs:

**pip**

```bash
pip install git+https://github.com/mark-me/network-wiki.git@v0.5.0
```

**uv**

```bash
uv add "network-wiki @ git+https://github.com/mark-me/network-wiki.git@v0.5.0"
```

### Option 3 — path dependency in `pyproject.toml`

If your own project also uses a `pyproject.toml`, add network-wiki as a
local path dependency:

```toml
[project]
dependencies = [
    "network-wiki @ file:///absolute/path/to/network-wiki",
]
```

Or, with a relative path (pip ≥ 22 / uv):

```toml
dependencies = [
    "network-wiki @ file://../network-wiki",
]
```

---

## Setting up a development environment

**pip**

```bash
git clone https://github.com/mark-me/network-wiki.git
cd network-wiki
pip install -e ".[dev,flask]"
```

**uv**

```bash
git clone https://github.com/mark-me/network-wiki.git
cd network-wiki
uv sync --extra dev --extra flask
```

### Running the tests

**pip**

```bash
pytest
```

**uv**

```bash
uv run pytest
```

### Generating an example page

```bash
python examples/example_jinja.py
# → opens etl_jinja_wiki.html in the current directory
```

---

## Project layout

```
src/network_wiki/
├── __init__.py          # public API
├── exporter.py          # GraphExporter – main entry point
├── node_style.py        # NodeColor, NodeFont, NodeStyle
├── edge_style.py        # EdgeColor, EdgeArrows, EdgeStyle
├── wiki.py              # WikiContent, WikiTemplateRenderer
├── layout.py            # LayoutConfig, ThemeConfig, BOOTSWATCH_THEMES
└── templates/
    ├── page.html.j2         # full HTML page (Bootstrap + vis.js)
    ├── mini_default.html.j2 # default side-panel wiki
    ├── full_default.html.j2 # default full-screen wiki
    ├── full_pipeline.html.j2
    └── full_source.html.j2
tests/
examples/
```

---

## Code style

- Docstrings in **English**, Google-style.
- Type annotations on all public functions and methods.
- `from __future__ import annotations` at the top of every module.
