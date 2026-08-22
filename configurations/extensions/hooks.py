"""Opt-in logic-override seam for extension core/override pairs.

A core extension exposes a hook point deliberately:

    def calculate_something(data):
        hook = resolve_hook("sample_extension", "calculate_something")
        if hook:
            return hook(data)
        return _default_calculate_something(data)

This only works for logic the core author explicitly exposed — unlike a
universal interceptor system, there's no way to override code that wasn't
written with a resolve_hook() call in it. Monkey-patching is not the
supported alternative; see docs/extension-architecture.md §9.
"""

import importlib


def resolve_hook(extension_name: str, function_name: str):
    """Look up an override function in extensions.<extension_name>.hooks.

    Args:
        extension_name: the extension's bare name (its override folder,
            not the core/ one).
        function_name: the function to look up in that module.

    Returns:
        The callable if extensions.<extension_name>.hooks defines it,
        else None (no override folder, no hooks.py, or the function isn't
        defined there — all three are treated the same: "use the default").
    """
    try:
        module = importlib.import_module(f"extensions.{extension_name}.hooks")
    except ModuleNotFoundError:
        return None
    return getattr(module, function_name, None)
