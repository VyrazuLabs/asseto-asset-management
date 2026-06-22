# Task 2 Report: Fix tests.py / tests/ module-package collisions (7 apps)

## Summary

Fixed the `<app>.tests` module/package collision in all 7 apps (`assets`, `audit`, `dashboard`,
`license`, `products`, `users`, `vendors`) by moving each `<app>/tests.py` into
`<app>/tests/test_<app>.py`, deleting the old file, and marking each app's
`tests/test_selenium.py` with `pytestmark = pytest.mark.selenium`. Handled the two special
cases (empty `users/tests.py`, stray `vendors/tests/tempCodeRunnerFile.py`) by deletion.

No test logic/assertions were changed. The only content edits were: (1) converting 4 relative
imports (`from .models import X`) to absolute imports (`from <app>.models import X`) — required
because the new file lives one package level deeper than the old one — and (2) adding the
selenium marker block to each `test_selenium.py`.

## Per-app summary

| App | Old file | New file | Relative import fix needed? | Notes |
|---|---|---|---|---|
| assets | `assets/tests.py` (9469 bytes, class `Asseto_test`) | `assets/tests/test_assets.py` | Yes — `from .models import Asset` → `from assets.models import Asset` | |
| audit | `audit/tests.py` (5394 bytes, class `AuditTest`) | `audit/tests/test_audit.py` | No — already absolute imports | |
| dashboard | `dashboard/tests.py` (15062 bytes, 9 classes) | `dashboard/tests/test_dashboard.py` | Yes — `from .models import ...` → `from dashboard.models import ...` | |
| license | `license/tests.py` (6664 bytes, class `LicenseTest`) | `license/tests/test_license.py` | No — already absolute imports | |
| products | `products/tests.py` (4969 bytes, classes `Asseto_test`, `DeleteProduct`) | `products/tests/test_products.py` | Yes — `from .models import Product` → `from products.models import Product` | |
| users | `users/tests.py` (0 bytes, empty) | — (deleted, no new file) | N/A | Confirmed empty per brief; no content to move. Phase 2 will write real tests later. |
| vendors | `vendors/tests.py` (4701 bytes, class `Asseto_test`) | `vendors/tests/test_vendors.py` | Yes — `from .models import Vendor` → `from vendors.models import Vendor` | Also removed stray `vendors/tests/tempCodeRunnerFile.py` (VSCode "Run Code" artifact, 952 bytes, not part of any package). |

All moves used `git mv` to preserve rename history. `<app>/tests/__init__.py` files were left
untouched (still present, still empty) in every app.

### Selenium marker addition

All 7 `test_selenium.py` files received the same two-line addition right after their last
top-level import statement and before the first `class` (or function) definition:

```python
import pytest

pytestmark = pytest.mark.selenium
```

Findings while inspecting these files:
- `audit`, `dashboard`, `license` test_selenium.py files have fully active, uncommented
  `LiveServerTestCase`-based test classes with live imports at the top of the file — marker
  added immediately after those imports.
- `assets`, `products`, `users`, `vendors` test_selenium.py files have an entirely commented-out
  legacy version of the test as the first block in the file, followed by a second, active,
  uncommented `LiveServerTestCase`-based class further down with its own import block. The
  marker was added after the *active* import block (immediately preceding the live `class`
  definition), not at the top of the file, since the brief's instruction to place it "near the
  top of the file, after imports" was interpreted as the real Python import statements that
  pytest will actually execute, not the commented-out historical code above them.
- All 7 are unittest-style `LiveServerTestCase` subclasses (none use plain pytest functions),
  so the module-level `pytestmark = pytest.mark.selenium` approach specified in the brief was
  used uniformly. `import pytest` was not previously present in any of the 7 files — added.

## Before / after pytest collection output

Verification run from project root with `env/` venv activated.

### Before (confirmed via `git stash` to revert working-tree changes)

```
$ pytest --collect-only -m "not selenium" -q
ERROR assets/tests.py
ERROR audit/tests.py
ERROR dashboard/tests.py
ERROR license/tests.py
ERROR products/tests.py
ERROR users/tests.py
ERROR vendors/tests.py
!!!!!!!!!!!!!!!!!!! Interrupted: 7 errors during collection !!!!!!!!!!!!!!!!!!!!
22 tests collected, 7 errors in 0.22s
```

Matches the brief's prediction exactly (7 errors, the same 7 apps).

### After

```
$ pytest --collect-only -m "not selenium" -q
... (coverage report omitted) ...
36/54 tests collected (18 deselected) in 2.99s
```

0 collection errors. 36 tests collected after deselecting 18 selenium-marked tests (54 total
discovered, matching the "no marker filter" run below).

```
$ pytest --collect-only -q
... (coverage report omitted) ...
36/54 tests collected (18 deselected) in 1.84s
```

Same 36/54(18 deselected) result — `--collect-only` deselects after collection regardless of
whether `-m` is passed explicitly on the command line, because `addopts = "-m 'not selenium'"`
in `pyproject.toml` (set by Task 1) applies by default. Confirmed all 7 `test_selenium.py`
files are discovered without error — they appear as collected/instrumented modules in the
coverage report for both runs (e.g. `audit/tests/test_selenium.py`, `vendors/tests/test_selenium.py`,
etc.), proving they import cleanly; they are simply deselected from the default run by the
marker, not failing to collect.

### Functional sanity check (not part of required verification, done as extra diligence)

Ran the 6 newly-created `test_<app>.py` files (excluding `users`, which has no tests) with
`pytest <files> -q --no-cov`:

```
3 failed, 29 passed, 4 warnings in 39.22s
```

The 3 failures are all in `dashboard/tests/test_dashboard.py::TestEditLocation` (
`test_delete_location`, `test_delete_product_category`, `test_delete_product_type`) and are
caused by a pre-existing infrastructure issue unrelated to this task: `dashboard/signals.py:268`
's `post_delete` handler tries to publish a Celery/notification message and gets
`ConnectionRefusedError: [Errno 61] Connection refused` (no RabbitMQ broker running in this
environment). This is not an import error, not caused by the move, and would have failed
identically on the original `dashboard/tests.py` content had it been able to run at all (it
couldn't, due to the collision this task fixes). Out of scope for Task 2 — flagging for
awareness only.

## Files changed

Renamed (content preserved, `git mv` used so rename is tracked):
- `assets/tests.py` → `assets/tests/test_assets.py` (1 import line changed)
- `audit/tests.py` → `audit/tests/test_audit.py` (no content change)
- `dashboard/tests.py` → `dashboard/tests/test_dashboard.py` (1 import line changed)
- `license/tests.py` → `license/tests/test_license.py` (no content change)
- `products/tests.py` → `products/tests/test_products.py` (1 import line changed)
- `vendors/tests.py` → `vendors/tests/test_vendors.py` (1 import line changed)

Deleted:
- `users/tests.py` (0 bytes, empty — confirmed before deletion)
- `vendors/tests/tempCodeRunnerFile.py` (stray VSCode Run Code artifact)

Modified (marker addition only, 3 lines each: blank + `import pytest` + blank +
`pytestmark = pytest.mark.selenium` + blank, exact placement varies slightly per file structure):
- `assets/tests/test_selenium.py`
- `audit/tests/test_selenium.py`
- `dashboard/tests/test_selenium.py`
- `license/tests/test_selenium.py`
- `products/tests/test_selenium.py`
- `users/tests/test_selenium.py`
- `vendors/tests/test_selenium.py`

Untouched (verified): all `<app>/tests/__init__.py` files remain present and empty.

Not touched by this task (pre-existing from Task 1, already in working tree before this task
started): `requirements.txt`, `pyproject.toml`, `.pre-commit-config.yaml`, `.superpowers/`.

## Self-review findings

1. **8th-app check**: Searched all `<app>/tests.py` files in the repo (14 total) and confirmed
   only the 7 listed apps also have a `tests/` directory alongside `tests.py`. The other 7 apps
   with a `tests.py` (`authentication`, `configurations`, `notifications`, `recycle_bin`,
   `roles`, `support`, `upload`) have no `tests/` package, so no collision exists there — no 8th
   app found.
2. **Relative import audit**: Specifically grepped every moved file for `^from \.` and
   `^import \.` patterns after the move; confirmed all 4 needed fixes were applied and no
   relative imports remain in any of the 6 moved files.
3. **Marker correctness**: Verified all 7 `test_selenium.py` files use `LiveServerTestCase`
   (unittest-style), so `pytestmark` module-level assignment (not class decoration) is the
   correct approach per the brief — confirmed no plain pytest-function-style tests exist in any
   of the 7 files.
4. **`tests/__init__.py` integrity**: Confirmed all 7 apps still have an empty, valid
   `tests/__init__.py` post-move (none were touched).
5. **No unrelated files touched**: Confirmed via `git diff --stat` that only test-related files
   plus the two special-case deletions changed; no `views.py`/`models.py`/`utils.py` files were
   modified.
6. **Build artifact hygiene**: Generated `.coverage` and `htmlcov/` directories during
   verification pytest runs were deleted afterward so they don't pollute the working tree (not
   part of this task's deliverable; not gitignored but were never staged).
7. **No commit made**: Confirmed via `git status` that all changes remain in the working tree,
   unstaged/staged-but-uncommitted as appropriate; no `git commit` was run.

## Issues / concerns

None blocking. One non-blocking observation already noted above: 3 pre-existing test failures
in `dashboard/tests/test_dashboard.py` due to a missing Celery/RabbitMQ broker in this dev
environment — unrelated to the collision fix, not introduced by this task, and out of scope per
the brief (this task is a structural move only). Flagging for whichever later phase owns runtime
test fixes / CI environment setup.
