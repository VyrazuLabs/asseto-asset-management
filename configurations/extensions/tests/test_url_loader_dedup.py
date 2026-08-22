"""Tests for build_extension_urlpatterns' one-mount-per-name behavior.

When both extensions.<name> (override) and extensions.core.<name> exist in
the enabled apps list (apps_loader's override pairing), only ONE URL
mount at /ext/<name>/ should be produced — the override's urls.py if it
has one, else core's — never both (would collide on the same prefix and
namespace). Exercised with real importable temp packages via sys.path so
django.urls.include() actually resolves, per docs/extension-architecture.md
§9.
"""

import sys
import textwrap

import pytest

from configurations.extensions.url_loader import build_extension_urlpatterns


@pytest.fixture
def temp_extension_packages(tmp_path, monkeypatch):
    """Build real importable extensions.core.demo_ext (+ optional extensions.demo_ext) packages."""

    def _build(with_override_urls=False, override_has_urls=True):
        pkg_root = tmp_path / "pkgroot"
        (pkg_root / "extensions" / "core" / "demo_ext").mkdir(parents=True)
        (pkg_root / "extensions" / "__init__.py").write_text("")
        (pkg_root / "extensions" / "core" / "__init__.py").write_text("")
        core_dir = pkg_root / "extensions" / "core" / "demo_ext"
        (core_dir / "__init__.py").write_text("")
        (core_dir / "urls.py").write_text(
            textwrap.dedent(
                """
                from django.urls import path
                from django.http import HttpResponse

                app_name = "ext_demo_ext"
                urlpatterns = [path("", lambda r: HttpResponse("core"), name="index")]
                """
            )
        )

        if with_override_urls:
            override_dir = pkg_root / "extensions" / "demo_ext"
            override_dir.mkdir(parents=True)
            (override_dir / "__init__.py").write_text("")
            if override_has_urls:
                (override_dir / "urls.py").write_text(
                    textwrap.dedent(
                        """
                        from django.urls import path
                        from django.http import HttpResponse

                        app_name = "ext_demo_ext"
                        urlpatterns = [path("", lambda r: HttpResponse("override"), name="index")]
                        """
                    )
                )

        monkeypatch.syspath_prepend(str(pkg_root))
        # Ensure re-import picks up this test's fresh packages, not a
        # stale module object from an earlier test in the same process.
        for mod in list(sys.modules):
            if mod == "extensions" or mod.startswith("extensions."):
                del sys.modules[mod]
        return pkg_root

    return _build


def test_mounts_only_core_when_no_override_present(temp_extension_packages):
    # Arrange
    temp_extension_packages(with_override_urls=False)
    app_paths = ["extensions.core.demo_ext"]

    # Act
    patterns = build_extension_urlpatterns_for(app_paths)

    # Assert
    assert len(patterns) == 1


def test_mounts_only_override_when_both_present_and_override_has_urls(temp_extension_packages):
    # Arrange
    temp_extension_packages(with_override_urls=True, override_has_urls=True)
    app_paths = ["extensions.demo_ext", "extensions.core.demo_ext"]

    # Act
    patterns = build_extension_urlpatterns_for(app_paths)

    # Assert — exactly one mount for this name, not two
    assert len(patterns) == 1


def test_falls_back_to_core_when_override_has_no_urls_module(temp_extension_packages):
    # Arrange — override folder exists (e.g. templates-only override) but has no urls.py
    temp_extension_packages(with_override_urls=True, override_has_urls=False)
    app_paths = ["extensions.demo_ext", "extensions.core.demo_ext"]

    # Act
    patterns = build_extension_urlpatterns_for(app_paths)

    # Assert — still exactly one mount, falls back to core's urls.py
    assert len(patterns) == 1


def build_extension_urlpatterns_for(app_paths):
    """Test helper: exercise the same dedup logic without the registry.json layer."""
    from configurations.extensions.url_loader import build_extension_urlpatterns_from_app_paths

    return build_extension_urlpatterns_from_app_paths(app_paths)
