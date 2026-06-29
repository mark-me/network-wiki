# Templates

Advanced wiki content customization beyond auto-generated attribute tables.

## Template Resolution Order

When rendering node wiki content:

1. Per-type file (`full_template_files_by_type`)
2. Per-type inline (`full_templates_by_type`)
3. Default file (`full_template_file`)
4. Default inline (`full_template`)
5. Bundled fallback (`full_default.html.j2`)

Same priority order applies to mini-template variants.

## Template Files Location

Place `.html.j2` files in your specified `template_dir`:

```text
project/
├── templates/wiki/
│ ├── full_default.html.j2
│ ├── mini_default.html.j2
│ └── full_manager.html.j2
└── script.py
```

## Built-in Fallbacks

network-wiki bundles default templates accessible even without custom files. These render:

- Compact attribute grids in mini-view
- Detailed tables with connections in full-modal view
