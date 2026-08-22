"""Tests for configurations.extensions.core_updater.run_core_update_steps.

`manage.py update_asseto` — full core update: git pull, dependency
install, migrate, collectstatic, reload. run_command is injected so tests
verify the step sequence without touching git/pip/the real DB. See
docs/extension-architecture.md §8.
"""

from configurations.extensions.core_updater import run_core_update_steps


def test_runs_steps_in_order():
    # Arrange
    calls = []

    def fake_run(command):
        calls.append(command)

    # Act
    run_core_update_steps(run_command=fake_run, reload_fn=lambda: calls.append(["reload"]))

    # Assert
    assert calls == [
        ["git", "pull"],
        ["uv", "pip", "install", "--system", "-r", "requirements.txt"],
        ["python", "manage.py", "migrate"],
        ["python", "manage.py", "collectstatic", "--noinput"],
        ["reload"],
    ]


def test_stops_and_does_not_reload_if_a_step_fails():
    # Arrange
    calls = []

    def failing_run(command):
        calls.append(command)
        if command[0] == "uv":
            raise RuntimeError("pip install failed")

    reload_calls = []

    # Act / Assert
    import pytest

    with pytest.raises(RuntimeError):
        run_core_update_steps(run_command=failing_run, reload_fn=lambda: reload_calls.append(True))

    assert calls == [["git", "pull"], ["uv", "pip", "install", "--system", "-r", "requirements.txt"]]
    assert reload_calls == []
