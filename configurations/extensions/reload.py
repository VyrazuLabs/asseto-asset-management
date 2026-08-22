"""Graceful gunicorn reload — the mechanism that activates pending
extension changes without downtime.

Sending SIGHUP to gunicorn's master process (its PID is written to a
pidfile by `--pid` on the gunicorn command line, see setup.sh) triggers a
graceful worker respawn: old workers keep serving until new ones finish
booting, and the new workers re-import the full Django app registry,
picking up whatever extensions/registry.json now says. See
docs/extension-architecture.md §4.
"""

import os
import signal
from pathlib import Path


class ReloadUnavailableError(Exception):
    """Raised when a reload can't be triggered (no pidfile — not running under gunicorn)."""


def trigger_reload(pid_file: Path) -> None:
    """Send SIGHUP to the gunicorn master process named in pid_file.

    Args:
        pid_file: path to gunicorn's --pid file.

    Raises:
        ReloadUnavailableError: if the pidfile doesn't exist — reload only
            works under the gunicorn-managed deployment (e.g. not under
            `manage.py runserver` in local dev).
    """
    pid_file = Path(pid_file)
    if not pid_file.is_file():
        raise ReloadUnavailableError(
            f"Gunicorn pidfile not found at {pid_file}; reload only works under "
            "the gunicorn-managed deployment."
        )
    pid = int(pid_file.read_text().strip())
    os.kill(pid, signal.SIGHUP)
