# Task 1: Dev tooling — pytest, ruff, mypy, pre-commit config

Part of Phase 0 (infrastructure) of the "Full Code Refactor: Thin Views/Templates, Fat Utils" plan for the Django project asseto-asset-management. This is purely tooling setup — no application code changes.

## Requirements (verbatim from the plan)

- `requirements.txt` (or new `requirements-dev.txt`) — add `pytest`, `pytest-django`, `pytest-cov`, `factory-boy`, `ruff`, `mypy`, `pre-commit` (`black`/`coverage` already present but unconfigured — confirm this by reading requirements.txt first).
- `pyproject.toml` (new) — `[tool.pytest.ini_options]` with `DJANGO_SETTINGS_MODULE` set to whatever the project's actual settings module is (find it — check `manage.py` or `AssetManagement/settings.py`), a marker `selenium` declared, and `addopts = "-m 'not selenium'"` so selenium tests are excluded by default. Plus `[tool.black]`, `[tool.ruff]`, `[tool.mypy]` sections with reasonable defaults for a Django project (e.g. ruff target Python version matching what's used, line-length matching black's default of 88 unless the project already has a documented line length).
- `.pre-commit-config.yaml` (new) — hooks for ruff, black, mypy (use `additional_dependencies: [django-stubs]` for mypy per Django convention), plus local pygrep-style hooks for:
  - no-debug-code: blocks `print(`, `pdb.set_trace()`, `breakpoint()`, `ipdb.`
  - no-commented-code: blocks lines like `# def `, `# class `, `# return `, `# import `, `# from `, `# if `, `# for `, `# while `, `# async ` at the start of a line (allow leading whitespace)
  - no-backup-files: blocks filenames matching `(_old|_backup|_bak|_copy|_orig|_temp|_tmp|_final)\.(py|html|js|css|md)$`
  Also include the standard pre-commit-hooks repo (trailing-whitespace, end-of-file-fixer, check-yaml, check-merge-conflict, check-added-large-files maxkb=500, no-commit-to-branch for main/master).

## Constraints

- Do not change any application code (views, models, templates) — this task is tooling config only.
- Do not run `pre-commit install` (that would modify the user's local git hooks without being asked) — just create the config file.
- Pin dependency versions loosely (e.g. `pytest>=8.0`) unless you find an existing convention in requirements.txt of pinning exact versions, in which case match that convention.
- Don't actually run `pip install` against the live environment unless you confirm it's safe to do so in a venv — installing into the system Python is out of scope. If there's an existing venv, you may install into it to verify config works; otherwise just verify config file syntax (e.g. `python -c "import tomllib; tomllib.load(open('pyproject.toml','rb'))"` for TOML validity) without altering the environment.

## Verification

- `pyproject.toml` parses as valid TOML.
- `.pre-commit-config.yaml` parses as valid YAML.
- If pytest is installed/available, run `pytest --collect-only -m "not selenium"` and report the result (it's fine if it fails right now due to the audit/tests collision — a separate task fixes that — just report what you see, don't try to fix it here).

## Report

Write your full report (what you created, exact file contents summary, any deviations and why, verification output) to `.superpowers/sdd/task-1-report.md`. Return to the controller only: status (DONE/DONE_WITH_CONCERNS/NEEDS_CONTEXT/BLOCKED), the commit hash(es), a one-line test/verification summary, and any concerns.
