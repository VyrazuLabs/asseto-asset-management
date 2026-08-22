"""Tests for configurations.extensions.reload.trigger_reload.

Sends SIGHUP to the gunicorn master process (read from a pidfile) to
gracefully respawn workers and re-import the app registry — the mechanism
that actually activates a pending_restart extension. See
docs/extension-architecture.md §4. os.kill is monkeypatched so these tests
never touch a real process.
"""

import pytest

from configurations.extensions.reload import ReloadUnavailableError, trigger_reload


def test_trigger_reload_raises_when_pidfile_missing(tmp_path):
    # Arrange
    pid_path = tmp_path / "gunicorn.pid"

    # Act / Assert
    with pytest.raises(ReloadUnavailableError):
        trigger_reload(pid_path)


def test_trigger_reload_sends_sighup_to_pid_in_file(tmp_path, monkeypatch):
    # Arrange
    pid_path = tmp_path / "gunicorn.pid"
    pid_path.write_text("12345\n")
    calls = []
    monkeypatch.setattr("os.kill", lambda pid, sig: calls.append((pid, sig)))

    # Act
    trigger_reload(pid_path)

    # Assert
    import signal

    assert calls == [(12345, signal.SIGHUP)]
