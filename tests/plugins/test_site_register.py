#!/usr/bin/env python3
import importlib
import inspect
import pathlib

import pytest
from novel_downloader.plugins import registry

SITES_DIR = (
    pathlib.Path(__file__).parents[2] / "src" / "novel_downloader" / "plugins" / "sites"
)

MODULE_DECORATOR_MAP = {
    "fetcher": ("register_fetcher", "_fetchers"),
    "parser": ("register_parser", "_parsers"),
    "client": ("register_client", "_client"),
    "searcher": ("register_searcher", "_searchers"),
}


@pytest.mark.parametrize("site_path", [p for p in SITES_DIR.iterdir() if p.is_dir()])
def test_site_plugin_structure(site_path):
    site_key = site_path.name

    for mod_name, (decorator_name, registry_attr) in MODULE_DECORATOR_MAP.items():
        py_file = site_path / f"{mod_name}.py"
        if not py_file.exists():
            continue  # optional module

        module_path = f"novel_downloader.plugins.sites.{site_key}.{mod_name}"
        module = importlib.import_module(module_path)

        # Find all classes defined in this module
        classes = {
            name: cls
            for name, cls in inspect.getmembers(module, inspect.isclass)
            if cls.__module__ == module_path
        }

        # Check naming convention
        matched_class = None
        for name, cls in classes.items():
            # support mangg_com -> ManggComSession, etc.
            if name.lower().startswith(site_key.replace("_", "")):
                matched_class = cls
                break

        assert matched_class, f"{module_path}: missing expected class"

        # Check registry field
        registry_obj = registry.registrar
        reg_dict = getattr(registry_obj, registry_attr)
        assert isinstance(reg_dict, dict), f"{registry_attr} is not a dict in registry"

        # Check if the class has been registered
        registered_class = reg_dict.get(site_key.lower())
        msg = (
            f"{matched_class.__name__} not registered via "
            f"@{decorator_name} for key '{site_key}'"
        )
        assert registered_class == matched_class, msg
