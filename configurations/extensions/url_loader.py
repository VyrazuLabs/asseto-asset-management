"""Builds root-URLconf entries for enabled extensions.

AssetManagement/urls.py calls build_extension_urlpatterns(BASE_DIR) once and
appends the result to urlpatterns. Each logical extension is mounted at
/ext/<name>/, per docs/extension-architecture.md §2/§9. An extension with
no urls.py is skipped (not every extension needs URLs — models/admin-only
extensions are valid), logged rather than crashing the whole URLconf. When
both an override (extensions.<name>) and its core counterpart
(extensions.core.<name>) are enabled, only ONE mount is produced per name —
the override's urls.py wins if it has one, else core's — never both (they'd
collide on the same prefix/namespace).
"""

import logging

logger = logging.getLogger(__name__)


def extension_url_parts(app_path: str):
    """Derive the URL prefix and namespace for an extension's app path.

    Args:
        app_path: e.g. "extensions.core.sample_extension" (core) or
            "extensions.sample_extension" (override/standalone).

    Returns:
        (prefix, namespace) e.g. ("ext/sample_extension/", "ext_sample_extension").
    """
    name = app_path.rsplit(".", 1)[-1]
    return f"ext/{name}/", f"ext_{name}"


def build_extension_urlpatterns_from_app_paths(app_paths):
    """Build one path() entry per logical extension name from an app-path list.

    Args:
        app_paths: enabled app import paths, in precedence order (override
            before core, as returned by apps_loader.load_enabled_extension_apps).

    Returns:
        List of path() entries, at most one per distinct extension name.
    """
    from django.urls import include, path

    patterns = []
    mounted_names = set()
    for app_path in app_paths:
        prefix, namespace = extension_url_parts(app_path)
        name = app_path.rsplit(".", 1)[-1]
        if name in mounted_names:
            continue
        try:
            patterns.append(path(prefix, include(f"{app_path}.urls", namespace=namespace)))
            mounted_names.add(name)
        except ModuleNotFoundError:
            logger.info(
                "Extension %s has no urls module; trying next candidate for '%s'",
                app_path,
                name,
            )
    return patterns


def build_extension_urlpatterns(base_dir):
    """Build a list of django.urls.path() entries for enabled extensions.

    Args:
        base_dir: project BASE_DIR.

    Returns:
        List of path() entries suitable for appending to root urlpatterns.
    """
    from configurations.extensions.apps_loader import load_enabled_extension_apps

    app_paths = load_enabled_extension_apps(base_dir)
    return build_extension_urlpatterns_from_app_paths(app_paths)
