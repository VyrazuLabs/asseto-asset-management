"""Core logic behind `manage.py update_asseto`.

Full Asseto core update: git pull, dependency install, migrate core apps,
collectstatic, then a graceful reload. Extension apps' migrations are not
touched here — they run separately via enable_extension/update_extension.
See docs/extension-architecture.md §8.
"""

import subprocess


def _default_run_command(command):
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"{' '.join(command)} failed: {result.stderr}")


def run_core_update_steps(run_command=None, reload_fn=None) -> None:
    """Run the full core-update step sequence.

    Args:
        run_command: callable(command_list) executing one shell command;
            defaults to a real subprocess call. Raises on failure.
        reload_fn: callable() triggering the graceful gunicorn reload;
            defaults to configurations.extensions.reload.trigger_reload
            against settings.GUNICORN_PID_FILE.

    Stops (without reloading) at the first step that raises — a failed
    migrate/collectstatic must not be followed by a reload into a broken
    state.
    """
    run_command = run_command or _default_run_command
    if reload_fn is None:
        from django.conf import settings

        from configurations.extensions.reload import trigger_reload

        reload_fn = lambda: trigger_reload(settings.GUNICORN_PID_FILE)  # noqa: E731

    run_command(["git", "pull"])
    run_command(["uv", "pip", "install", "--system", "-r", "requirements.txt"])
    run_command(["python", "manage.py", "migrate"])
    run_command(["python", "manage.py", "collectstatic", "--noinput"])
    reload_fn()
