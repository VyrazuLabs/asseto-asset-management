# Task 2: Fix tests.py / tests/ module-package collisions (7 apps)

Part of Phase 0 (infrastructure) of the "Full Code Refactor" plan. The original plan only documented this collision for `audit`, but running `pytest --collect-only -m "not selenium"` after Task 1 revealed the SAME collision in 7 apps: `assets`, `audit`, `dashboard`, `license`, `products`, `users`, `vendors`. Each of these has both a `tests.py` file (the real unittest suite) AND a `tests/` package (containing `__init__.py` + `test_selenium.py`). Python cannot resolve `<app>.tests` as both a module and a package — this blocks pytest from collecting any of them.

## Requirements

For EACH of the 7 apps (`assets`, `audit`, `dashboard`, `license`, `products`, `users`, `vendors`):

1. Move the existing `<app>/tests.py` file's content into a new file inside the `<app>/tests/` package: `<app>/tests/test_<app>.py` (e.g. `assets/tests/test_assets.py`, `audit/tests/test_audit_trail.py` if there's an existing convention to infer a better name from the test class names inside — otherwise default to `test_<app>.py`). Preserve the test content exactly — this is a pure move, not a rewrite. Update any relative imports if needed (they're typically fine since both old and new locations are within the same app directory, but verify).
2. Delete the old `<app>/tests.py` file.
3. Keep `<app>/tests/test_selenium.py` exactly where it is, but add a `@pytest.mark.selenium` marker to it so it's excluded by pytest's default run (which Task 1 already configured via `addopts = "-m 'not selenium'"` in pyproject.toml). Check whether `test_selenium.py` uses `unittest.TestCase`/`LiveServerTestCase` (class-based) or plain functions — for a unittest-style `TestCase` subclass, the correct way to apply a pytest marker is `pytestmark = pytest.mark.selenium` at the module level (add this line near the top of the file, after imports) rather than decorating the class, since classmethod/class-level marks on unittest.TestCase subclasses behave differently in pytest. Add the `import pytest` line if not already present.
4. `users/tests.py` is confirmed EMPTY (0 bytes) — for this app specifically, there is no real content to move. Just delete the empty `users/tests.py`. Do not invent test content; that's the job of a later phase (Phase 2 in the parent plan, which explicitly calls out `users` needing tests written from scratch).
5. Special case: `vendors/tests/tempCodeRunnerFile.py` exists — this is a stray editor-generated junk file (VSCode "Run Code" extension artifact), not a real test or part of any package. Delete it. (This is exactly the kind of "no garbage files" violation the project's CLAUDE.md forbids — see the project's CLAUDE.md if you want the rule reference, but the action is simply: delete this one file.)

## Constraints

- Do not change test logic/assertions — this is a structural move only, except for the one marker addition to each `test_selenium.py` and deleting the one empty file and the one junk file.
- Do not touch any app's `views.py`, `models.py`, `utils.py`, or any non-test file.
- Do not run `git commit` — leave changes in the working tree uncommitted (no explicit commit instruction was given for this task).
- After your changes, every app's `tests/__init__.py` must remain a valid empty package init (don't delete those).

## Verification

Run (from the project root, with the project's venv activated if one exists — check for `env/` or `venv/` at the project root and activate it):
```bash
pytest --collect-only -m "not selenium" -q
```
Expected: 0 collection errors (previously 7: assets/tests.py, audit/tests.py, dashboard/tests.py, license/tests.py, products/tests.py, users/tests.py, vendors/tests.py). Report the exact before/after test counts and confirm zero errors.

Also run:
```bash
pytest --collect-only -q
```
(no marker filter) and confirm the selenium test files are now discovered (not erroring), e.g. `audit/tests/test_selenium.py` should appear in the collection list even though the default run excludes it.

## Report

Write your full report (per-app summary of what moved where, before/after pytest output, any surprises) to `.superpowers/sdd/task-2-report.md`. Return to the controller only: status (DONE/DONE_WITH_CONCERNS/NEEDS_CONTEXT/BLOCKED), files changed (list), a one-line collection-count summary, and any concerns.
