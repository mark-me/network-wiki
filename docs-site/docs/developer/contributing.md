# Contributing

Thank you for wanting to contribute! Here's how to get started.

## Setup

```bash
git clone https://github.com/markzwart/network-wiki.git
cd network-wiki
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Running Tests

```bash
pytest tests/ -v
```

## Adding features

* Create feature branch from main
* Implement change with supporting tests
* Update corresponding docs in docs-site/
* Submit pull request

## Documentation Changes

Docs use MDK syntax driven by zensical.toml nav structure. Edit individual .md files under docs-site/ directory matching your contribution scope.
