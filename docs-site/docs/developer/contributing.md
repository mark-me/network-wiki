# Contributing

Thank you for wanting to contribute! Here's how to get started.

## 💻 Setup

=== "pip"

    ```bash
    git clone https://github.com/mark-me/network-wiki.git
    cd network-wiki
    python -m venv .venv
    source .venv/bin/activate
    pip install -e ".[dev,flask]"
    ```

=== "uv"

    ```bash
    git clone https://github.com/mark-me/network-wiki.git
    cd network-wiki
    uv sync --extra dev --extra flask
    ```

## 🧪 Running Tests

=== "pip"

    ```bash
    pytest tests/ -v
    ```

=== "uv"

    ```bash
    uv run pytest tests/ -v
    ```

The test suite covers `node_style`, `edge_style`, `layout`, the exporter (including HTML validity checks), and the Flask integration. Run a single file with `pytest tests/test_exporter.py -v`.

## Trying the Examples

```bash
python examples/example_etl.py            # ETL pipeline, file-based templates
python examples/example_generic.py        # non-ETL graph, type_attr demo
python examples/example_wiki_content.py    # every wiki mechanism side by side
python examples/example_flask_app.py       # Flask app with static + live graphs
```

## Adding Features

* Create a feature branch from `main`
* Implement the change with supporting tests
* Update the corresponding docs under `docs-site/docs/`
* Add a `CHANGELOG.md` entry under `[Unreleased]`
* Submit a pull request

CI runs the full test suite on both `pip` and `uv` install paths, across Python 3.11/3.12 and Ubuntu/Windows/macOS for the `pip` matrix — see `.github/workflows/ci.yml`.

## Documentation Changes

Docs use Markdown driven by the `zensical.toml` nav structure. Edit the individual `.md` files under `docs-site/docs/` matching your contribution's scope, and add new pages to the `nav` list in `zensical.toml` if you create one.
