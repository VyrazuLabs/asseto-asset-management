"""Tests for configurations.extensions.hooks.resolve_hook.

Opt-in logic-override seam for the core/override split: a core extension
calls resolve_hook("<name>", "<fn>") at a point it deliberately exposed;
if extensions.<name>.hooks defines that function, it's used instead of the
core default. See docs/extension-architecture.md §9.
"""

import sys
import textwrap

import pytest

from configurations.extensions.hooks import resolve_hook


@pytest.fixture
def override_hooks_module(tmp_path, monkeypatch):
    def _build(contents: str):
        pkg_root = tmp_path / "pkgroot"
        override_dir = pkg_root / "extensions" / "hookdemo"
        override_dir.mkdir(parents=True)
        (pkg_root / "extensions" / "__init__.py").write_text("")
        (override_dir / "__init__.py").write_text("")
        (override_dir / "hooks.py").write_text(textwrap.dedent(contents))
        monkeypatch.syspath_prepend(str(pkg_root))
        for mod in list(sys.modules):
            if mod == "extensions" or mod.startswith("extensions."):
                del sys.modules[mod]

    return _build


def test_resolve_hook_returns_none_when_no_override_folder():
    # Act
    hook = resolve_hook("nonexistent_extension", "calculate_something")

    # Assert
    assert hook is None


def test_resolve_hook_returns_none_when_hooks_module_lacks_function(override_hooks_module):
    # Arrange
    override_hooks_module("def unrelated_function():\n    return 1\n")

    # Act
    hook = resolve_hook("hookdemo", "calculate_something")

    # Assert
    assert hook is None


def test_resolve_hook_returns_function_when_defined(override_hooks_module):
    # Arrange
    override_hooks_module("def calculate_something(data):\n    return data * 2\n")

    # Act
    hook = resolve_hook("hookdemo", "calculate_something")

    # Assert
    assert hook is not None
    assert hook(21) == 42
