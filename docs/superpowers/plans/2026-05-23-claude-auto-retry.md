# claude-auto-retry Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Claude Code plugin that auto-retries transient API errors by injecting `Up Enter` into the tmux pane after a class-appropriate backoff.

**Architecture:** Single multi-mode Python script (`auto_retry.py`) runs as a `StopFailure` hook, detaches a timer subprocess of itself, sleeps, and uses `tmux send-keys` to re-submit the last prompt in the same session. TOML config (stdlib `tomllib`). Persistent log at `~/.local/state/claude-auto-retry/log.jsonl`; ephemeral pending pidfiles at `/tmp/claude-auto-retry/pending/`.

**Tech Stack:** Python 3.11+ stdlib only (no third-party deps). tmux. unittest for tests.

**Spec reference:** `docs/superpowers/specs/2026-05-23-claude-auto-retry-design.md`

**Plugin install path:** `plugins/claude-auto-retry/` (inside this marketplace repo).

---

## Conventions used in every task

- All paths absolute, rooted at the marketplace repo `/home/ubuntu/dev/vct-claude-marketplace-public/`.
- Tests run from the plugin dir with `python3 -m unittest discover tests -v`.
- Commits use `git -c user.name='vcth4nh' -c user.email='tvu25337@gmail.com' commit ...` since the user wants those identities on the marketplace repo.
- The engine reads paths from env vars when set, defaults otherwise. Tests set these env vars to point at temp dirs:
  - `CLAUDE_AUTO_RETRY_LOG_PATH` → `~/.local/state/claude-auto-retry/log.jsonl`
  - `CLAUDE_AUTO_RETRY_PENDING_DIR` → `/tmp/claude-auto-retry/pending`
  - `CLAUDE_AUTO_RETRY_SENTINEL_DIR` → `/tmp`
  - `CLAUDE_AUTO_RETRY_USER_CONFIG` → `~/.config/claude-auto-retry/config.toml`

---

## Task 1: Scaffold plugin directories and manifest

**Files:**
- Create: `plugins/claude-auto-retry/.claude-plugin/plugin.json`
- Create: `plugins/claude-auto-retry/hooks/.gitkeep`
- Create: `plugins/claude-auto-retry/skills/.gitkeep`
- Create: `plugins/claude-auto-retry/examples/.gitkeep`
- Create: `plugins/claude-auto-retry/tests/.gitkeep`

- [ ] **Step 1: Create directory layout**

```bash
cd /home/ubuntu/dev/vct-claude-marketplace-public
mkdir -p plugins/claude-auto-retry/.claude-plugin
mkdir -p plugins/claude-auto-retry/hooks
mkdir -p plugins/claude-auto-retry/skills/claude-auto-retry-about
mkdir -p plugins/claude-auto-retry/skills/status
mkdir -p plugins/claude-auto-retry/examples
mkdir -p plugins/claude-auto-retry/tests/integration
touch plugins/claude-auto-retry/hooks/.gitkeep
touch plugins/claude-auto-retry/skills/.gitkeep
touch plugins/claude-auto-retry/examples/.gitkeep
touch plugins/claude-auto-retry/tests/.gitkeep
```

- [ ] **Step 2: Write `plugin.json`**

`plugins/claude-auto-retry/.claude-plugin/plugin.json`:
```json
{
  "name": "claude-auto-retry",
  "version": "0.1.0",
  "description": "Auto-retry Claude Code sessions on transient API errors (rate limits, 5xx, overloaded) via a StopFailure hook + tmux send-keys. Hard usage quotas parsed from the error text and scheduled. Pure stdlib, no daemon, no wrapper.",
  "author": {
    "name": "vcth4nh"
  },
  "keywords": ["rate-limit", "retry", "tmux", "hook", "resilience"],
  "license": "CC-BY-SA-4.0"
}
```

- [ ] **Step 3: Verify layout**

```bash
cd /home/ubuntu/dev/vct-claude-marketplace-public
find plugins -type f -o -type d | sort
```
Expected: shows the dirs + plugin.json + .gitkeep files.

- [ ] **Step 4: Commit**

```bash
cd /home/ubuntu/dev/vct-claude-marketplace-public
git add plugins/
git -c user.name='vcth4nh' -c user.email='tvu25337@gmail.com' \
  commit -q -m "claude-auto-retry: scaffold plugin directory layout"
```

---

## Task 2: Engine skeleton with argparse modes (stubs)

**Files:**
- Create: `plugins/claude-auto-retry/hooks/auto_retry.py`
- Create: `plugins/claude-auto-retry/tests/test_auto_retry.py`
- Create: `plugins/claude-auto-retry/tests/conftest_helpers.py`

- [ ] **Step 1: Write conftest helper (path setup)**

`plugins/claude-auto-retry/tests/conftest_helpers.py`:
```python
"""Importable test helpers. Adjusts sys.path so tests can import auto_retry."""
from __future__ import annotations
import pathlib
import sys

PLUGIN_DIR = pathlib.Path(__file__).resolve().parent.parent
HOOKS_DIR = PLUGIN_DIR / "hooks"
if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))
```

- [ ] **Step 2: Write failing test for argparse stubs**

`plugins/claude-auto-retry/tests/test_auto_retry.py`:
```python
from __future__ import annotations
import io
import sys
import unittest
from unittest import mock

from conftest_helpers import *  # noqa: F401,F403  -- side effect: sys.path

import auto_retry


class TestArgparseModes(unittest.TestCase):
    def _run_main(self, argv: list[str]) -> tuple[int, str]:
        out = io.StringIO()
        with mock.patch.object(sys, "argv", ["auto_retry.py", *argv]), \
             mock.patch.object(sys, "stdout", out):
            try:
                auto_retry.main()
                exit_code = 0
            except SystemExit as e:
                exit_code = int(e.code or 0)
        return exit_code, out.getvalue()

    def test_status_mode_runs(self):
        rc, _ = self._run_main(["--status"])
        self.assertEqual(rc, 0)

    def test_init_config_mode_runs(self):
        with mock.patch.object(auto_retry, "_init_config", return_value=None) as m:
            rc, _ = self._run_main(["--init-config"])
        self.assertEqual(rc, 0)
        m.assert_called_once()

    def test_timer_mode_requires_three_args(self):
        with mock.patch.object(auto_retry, "_timer", return_value=None) as m:
            rc, _ = self._run_main(["--timer", "%7", "60", "rate_limit"])
        self.assertEqual(rc, 0)
        m.assert_called_once_with("%7", 60, "rate_limit")

    def test_hook_mode_is_default(self):
        with mock.patch.object(auto_retry, "_hook", return_value=None) as m:
            rc, _ = self._run_main([])
        self.assertEqual(rc, 0)
        m.assert_called_once()


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run test to verify it fails**

```bash
cd /home/ubuntu/dev/vct-claude-marketplace-public/plugins/claude-auto-retry
python3 -m unittest tests.test_auto_retry -v
```
Expected: ImportError / ModuleNotFoundError for `auto_retry`.

- [ ] **Step 4: Write the engine skeleton**

`plugins/claude-auto-retry/hooks/auto_retry.py`:
```python
#!/usr/bin/env python3
"""Claude Code StopFailure auto-retry engine.

Runs in four modes via argparse:
  --hook            (default) read StopFailure event on stdin, schedule retry
  --timer P D E     detached child: sleep D, send Up+Enter to pane P for error E
  --status          render recent retries + pending timers
  --init-config     copy examples/config.toml into <cwd>/.claude/
"""
from __future__ import annotations

import argparse
import sys


def _hook() -> None:
    """Read StopFailure event, classify, schedule timer. Stub for now."""
    pass


def _timer(pane: str, delay: int, error: str) -> None:
    """Sleep, then inject Up+Enter via tmux. Stub for now."""
    pass


def _status() -> None:
    """Print recent + pending. Stub for now."""
    pass


def _init_config() -> None:
    """Copy examples/config.toml into <cwd>/.claude/. Stub for now."""
    pass


def main() -> None:
    parser = argparse.ArgumentParser(prog="auto_retry")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--hook", action="store_true",
                       help="run as StopFailure hook (default)")
    group.add_argument("--status", action="store_true",
                       help="print recent retries and pending timers")
    group.add_argument("--init-config", action="store_true",
                       help="copy example config into <cwd>/.claude/")
    group.add_argument("--timer", nargs=3, metavar=("PANE", "DELAY", "ERROR"),
                       help="(internal) detached timer mode")
    args = parser.parse_args()

    if args.status:
        _status()
    elif args.init_config:
        _init_config()
    elif args.timer:
        pane, delay, error = args.timer
        _timer(pane, int(delay), error)
    else:
        _hook()


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run tests to verify pass**

```bash
cd /home/ubuntu/dev/vct-claude-marketplace-public/plugins/claude-auto-retry
python3 -m unittest tests.test_auto_retry -v
```
Expected: 4 tests pass.

- [ ] **Step 6: Commit**

```bash
cd /home/ubuntu/dev/vct-claude-marketplace-public
git add plugins/claude-auto-retry/
git -c user.name='vcth4nh' -c user.email='tvu25337@gmail.com' \
  commit -q -m "claude-auto-retry: engine skeleton + argparse mode dispatch"
```

---

## Task 3: Path helpers (env-overridable)

**Files:**
- Modify: `plugins/claude-auto-retry/hooks/auto_retry.py`
- Modify: `plugins/claude-auto-retry/tests/test_auto_retry.py`

- [ ] **Step 1: Write failing tests for the path helpers**

Append to `tests/test_auto_retry.py`:
```python
class TestPathHelpers(unittest.TestCase):
    def test_log_path_default(self):
        with mock.patch.dict("os.environ", {}, clear=False):
            for k in ("CLAUDE_AUTO_RETRY_LOG_PATH",):
                __import__("os").environ.pop(k, None)
            p = auto_retry._log_path()
        self.assertTrue(str(p).endswith(".local/state/claude-auto-retry/log.jsonl"))

    def test_log_path_env_override(self):
        with mock.patch.dict("os.environ",
                             {"CLAUDE_AUTO_RETRY_LOG_PATH": "/tmp/x/y.jsonl"}):
            self.assertEqual(str(auto_retry._log_path()), "/tmp/x/y.jsonl")

    def test_pending_dir_default(self):
        with mock.patch.dict("os.environ", {}, clear=False):
            __import__("os").environ.pop("CLAUDE_AUTO_RETRY_PENDING_DIR", None)
            self.assertEqual(str(auto_retry._pending_dir()),
                             "/tmp/claude-auto-retry/pending")

    def test_pending_dir_env_override(self):
        with mock.patch.dict("os.environ",
                             {"CLAUDE_AUTO_RETRY_PENDING_DIR": "/tmp/zz"}):
            self.assertEqual(str(auto_retry._pending_dir()), "/tmp/zz")

    def test_sentinel_dir_default(self):
        with mock.patch.dict("os.environ", {}, clear=False):
            __import__("os").environ.pop("CLAUDE_AUTO_RETRY_SENTINEL_DIR", None)
            self.assertEqual(str(auto_retry._sentinel_dir()), "/tmp")
```

- [ ] **Step 2: Run tests to verify fail**

```bash
cd /home/ubuntu/dev/vct-claude-marketplace-public/plugins/claude-auto-retry
python3 -m unittest tests.test_auto_retry.TestPathHelpers -v
```
Expected: AttributeError (functions don't exist yet).

- [ ] **Step 3: Add path helpers to `auto_retry.py`**

After the imports in `auto_retry.py`, add:
```python
import os
import pathlib


def _log_path() -> pathlib.Path:
    return pathlib.Path(
        os.environ.get("CLAUDE_AUTO_RETRY_LOG_PATH")
        or (pathlib.Path.home() / ".local/state/claude-auto-retry/log.jsonl")
    )


def _pending_dir() -> pathlib.Path:
    return pathlib.Path(
        os.environ.get("CLAUDE_AUTO_RETRY_PENDING_DIR")
        or "/tmp/claude-auto-retry/pending"
    )


def _sentinel_dir() -> pathlib.Path:
    return pathlib.Path(os.environ.get("CLAUDE_AUTO_RETRY_SENTINEL_DIR") or "/tmp")
```

- [ ] **Step 4: Run tests**

```bash
python3 -m unittest tests.test_auto_retry.TestPathHelpers -v
```
Expected: 5 tests pass.

- [ ] **Step 5: Commit**

```bash
cd /home/ubuntu/dev/vct-claude-marketplace-public
git add plugins/claude-auto-retry/
git -c user.name='vcth4nh' -c user.email='tvu25337@gmail.com' \
  commit -q -m "claude-auto-retry: env-overridable path helpers"
```

---

## Task 4: Config defaults

**Files:**
- Modify: `plugins/claude-auto-retry/hooks/auto_retry.py`
- Modify: `plugins/claude-auto-retry/tests/test_auto_retry.py`

- [ ] **Step 1: Write failing test for `DEFAULT_CONFIG`**

Append to `tests/test_auto_retry.py`:
```python
class TestDefaultConfig(unittest.TestCase):
    def test_defaults_present(self):
        c = auto_retry.DEFAULT_CONFIG
        self.assertTrue(c["enabled"])
        self.assertEqual(c["dedup_window"], 30)
        self.assertFalse(c["quiet"])
        self.assertEqual(c["backoff"]["rate_limit_transient"], 60)
        self.assertEqual(c["backoff"]["server_error"], 30)
        self.assertEqual(c["backoff"]["unknown"], 30)
        self.assertEqual(c["backoff"]["hard_quota_fallback"], 1800)
        self.assertTrue(c["hard_quota"]["parse_reset_time"])
        self.assertEqual(c["hard_quota"]["max_wait"], 14400)
        self.assertTrue(c["per_error_enable"]["rate_limit"])
        self.assertTrue(c["per_error_enable"]["server_error"])
        self.assertTrue(c["per_error_enable"]["unknown"])
```

- [ ] **Step 2: Run test, verify fail**

```bash
python3 -m unittest tests.test_auto_retry.TestDefaultConfig -v
```
Expected: AttributeError (DEFAULT_CONFIG missing).

- [ ] **Step 3: Add `DEFAULT_CONFIG` to `auto_retry.py`**

After the path helpers, add:
```python
DEFAULT_CONFIG: dict = {
    "enabled": True,
    "dedup_window": 30,
    "quiet": False,
    "backoff": {
        "rate_limit_transient": 60,
        "server_error": 30,
        "unknown": 30,
        "hard_quota_fallback": 1800,
    },
    "hard_quota": {
        "parse_reset_time": True,
        "max_wait": 14400,
    },
    "per_error_enable": {
        "rate_limit": True,
        "server_error": True,
        "unknown": True,
    },
}
```

- [ ] **Step 4: Run tests**

```bash
python3 -m unittest tests.test_auto_retry.TestDefaultConfig -v
```
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
cd /home/ubuntu/dev/vct-claude-marketplace-public
git add plugins/claude-auto-retry/
git -c user.name='vcth4nh' -c user.email='tvu25337@gmail.com' \
  commit -q -m "claude-auto-retry: bake DEFAULT_CONFIG into engine"
```

---

## Task 5: `_load_config` — defaults when no files exist

**Files:**
- Modify: `plugins/claude-auto-retry/hooks/auto_retry.py`
- Modify: `plugins/claude-auto-retry/tests/test_auto_retry.py`

- [ ] **Step 1: Write failing test**

Append to `tests/test_auto_retry.py`:
```python
import tempfile

class TestLoadConfig(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.cwd = pathlib.Path(self.tmp.name)
        # Point user config at a nonexistent path
        self.env_patch = mock.patch.dict(
            "os.environ",
            {"CLAUDE_AUTO_RETRY_USER_CONFIG": str(self.cwd / "nonexistent.toml")},
        )
        self.env_patch.start()
        self.addCleanup(self.env_patch.stop)

    def test_defaults_when_no_files(self):
        cfg = auto_retry._load_config(str(self.cwd))
        self.assertEqual(cfg, auto_retry.DEFAULT_CONFIG)
```

(`pathlib` is already imported via the engine; tests use `pathlib.Path` via `auto_retry.pathlib` — but to keep tests independent, also `import pathlib` at top of test file if not already there.)

Make sure `import pathlib` is at the top of `tests/test_auto_retry.py`. Add if missing.

- [ ] **Step 2: Run test, verify fail**

```bash
python3 -m unittest tests.test_auto_retry.TestLoadConfig -v
```
Expected: AttributeError or wrong return value (function returns None / undefined).

- [ ] **Step 3: Add `_load_config` and `_user_config_path` to `auto_retry.py`**

Add to imports near the top: `import copy`.

Add after `DEFAULT_CONFIG`:
```python
def _user_config_path() -> pathlib.Path:
    return pathlib.Path(
        os.environ.get("CLAUDE_AUTO_RETRY_USER_CONFIG")
        or (pathlib.Path.home() / ".config/claude-auto-retry/config.toml")
    )


def _project_config_path(cwd: str) -> pathlib.Path:
    return pathlib.Path(cwd) / ".claude" / "claude-auto-retry.toml"


def _load_config(cwd: str) -> dict:
    """Resolve config: DEFAULT_CONFIG <- user <- project. Section-shallow merge."""
    import tomllib

    cfg = copy.deepcopy(DEFAULT_CONFIG)
    for path in (_user_config_path(), _project_config_path(cwd)):
        try:
            with open(path, "rb") as f:
                layer = tomllib.load(f)
        except FileNotFoundError:
            continue
        except Exception:
            # Malformed TOML — log a warning later; for now silently use defaults
            continue
        for top_key, value in layer.items():
            if isinstance(value, dict) and isinstance(cfg.get(top_key), dict):
                cfg[top_key].update(value)
            else:
                cfg[top_key] = value
    return cfg
```

- [ ] **Step 4: Run test**

```bash
python3 -m unittest tests.test_auto_retry.TestLoadConfig -v
```
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/claude-auto-retry/
git -c user.name='vcth4nh' -c user.email='tvu25337@gmail.com' \
  commit -q -m "claude-auto-retry: _load_config returns defaults when no files exist"
```

---

## Task 6: `_load_config` — user + project overrides + malformed handling

**Files:**
- Modify: `plugins/claude-auto-retry/tests/test_auto_retry.py`

- [ ] **Step 1: Write 3 failing tests**

Add to `TestLoadConfig`:
```python
    def test_user_overrides_defaults(self):
        user_cfg = self.cwd / "user.toml"
        user_cfg.write_text(
            "dedup_window = 90\n"
            "[backoff]\n"
            "rate_limit_transient = 120\n"
        )
        with mock.patch.dict("os.environ",
                             {"CLAUDE_AUTO_RETRY_USER_CONFIG": str(user_cfg)}):
            cfg = auto_retry._load_config(str(self.cwd))
        self.assertEqual(cfg["dedup_window"], 90)
        self.assertEqual(cfg["backoff"]["rate_limit_transient"], 120)
        # Other defaults preserved
        self.assertEqual(cfg["backoff"]["server_error"], 30)

    def test_project_overrides_user(self):
        user_cfg = self.cwd / "user.toml"
        user_cfg.write_text("[backoff]\nrate_limit_transient = 120\n")
        project_dir = self.cwd / ".claude"
        project_dir.mkdir()
        (project_dir / "claude-auto-retry.toml").write_text(
            "[backoff]\nrate_limit_transient = 300\n"
        )
        with mock.patch.dict("os.environ",
                             {"CLAUDE_AUTO_RETRY_USER_CONFIG": str(user_cfg)}):
            cfg = auto_retry._load_config(str(self.cwd))
        self.assertEqual(cfg["backoff"]["rate_limit_transient"], 300)

    def test_malformed_toml_falls_back_silently(self):
        user_cfg = self.cwd / "user.toml"
        user_cfg.write_text("this is = not [ valid TOML\n")
        with mock.patch.dict("os.environ",
                             {"CLAUDE_AUTO_RETRY_USER_CONFIG": str(user_cfg)}):
            cfg = auto_retry._load_config(str(self.cwd))
        self.assertEqual(cfg, auto_retry.DEFAULT_CONFIG)
```

- [ ] **Step 2: Run tests, verify pass (implementation already covers this)**

```bash
python3 -m unittest tests.test_auto_retry.TestLoadConfig -v
```
Expected: All 4 tests PASS — Task 5's implementation already supports this. If any fail, fix `_load_config` until they pass.

- [ ] **Step 3: Commit**

```bash
git add plugins/claude-auto-retry/
git -c user.name='vcth4nh' -c user.email='tvu25337@gmail.com' \
  commit -q -m "claude-auto-retry: _load_config user/project override + malformed handling tests"
```

---

## Task 7: `_classify` — transient errors

**Files:**
- Modify: `plugins/claude-auto-retry/hooks/auto_retry.py`
- Modify: `plugins/claude-auto-retry/tests/test_auto_retry.py`

- [ ] **Step 1: Write failing tests**

Append to `tests/test_auto_retry.py`:
```python
class TestClassifyTransient(unittest.TestCase):
    def setUp(self):
        self.cfg = copy.deepcopy(auto_retry.DEFAULT_CONFIG)

    def test_rate_limit_transient(self):
        text = "API Error: Server is temporarily limiting requests · Rate limited"
        backoff, source = auto_retry._classify("rate_limit", text, self.cfg)
        self.assertEqual(backoff, 60)
        self.assertEqual(source, "transient")

    def test_server_error(self):
        backoff, source = auto_retry._classify("server_error", "500 Internal", self.cfg)
        self.assertEqual(backoff, 30)
        self.assertEqual(source, "transient")

    def test_unknown(self):
        backoff, source = auto_retry._classify("unknown", "Overloaded", self.cfg)
        self.assertEqual(backoff, 30)
        self.assertEqual(source, "transient")

    def test_invalid_request_skip(self):
        backoff, source = auto_retry._classify("invalid_request", "policy", self.cfg)
        self.assertIsNone(backoff)
        self.assertEqual(source, "not_retryable")

    def test_max_output_tokens_skip(self):
        backoff, source = auto_retry._classify("max_output_tokens", "", self.cfg)
        self.assertIsNone(backoff)
        self.assertEqual(source, "not_retryable")
```

Add `import copy` to top of test file if missing.

- [ ] **Step 2: Run, verify fail**

```bash
python3 -m unittest tests.test_auto_retry.TestClassifyTransient -v
```
Expected: AttributeError.

- [ ] **Step 3: Add `_classify` to `auto_retry.py`**

Add after `_load_config`:
```python
# Error classes that map to retryable transient backoffs.
_RETRYABLE = {"rate_limit", "server_error", "unknown"}


def _classify(err: str, text: str, cfg: dict) -> tuple[int | None, str]:
    """Decide retry backoff for an error.

    Returns (seconds, source) on retry; (None, reason) on skip.
    Does NOT consult TMUX_PANE, enabled, or per-error-enable — those are
    handled by _hook's skip-check ladder.
    """
    if err not in _RETRYABLE:
        return None, "not_retryable"
    if err == "rate_limit":
        if "hit your" in text and "limit" in text:
            # Hard quota — handled in Task 9 (parse reset time).
            return None, "quota_unimplemented"
        return int(cfg["backoff"]["rate_limit_transient"]), "transient"
    if err == "server_error":
        return int(cfg["backoff"]["server_error"]), "transient"
    # err == "unknown"
    return int(cfg["backoff"]["unknown"]), "transient"
```

- [ ] **Step 4: Run tests**

```bash
python3 -m unittest tests.test_auto_retry.TestClassifyTransient -v
```
Expected: 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/claude-auto-retry/
git -c user.name='vcth4nh' -c user.email='tvu25337@gmail.com' \
  commit -q -m "claude-auto-retry: _classify handles transient and not-retryable classes"
```

---

## Task 8: `_parse_reset_time` — extract seconds-until-reset

**Files:**
- Modify: `plugins/claude-auto-retry/hooks/auto_retry.py`
- Modify: `plugins/claude-auto-retry/tests/test_auto_retry.py`

- [ ] **Step 1: Write failing tests**

Append to `tests/test_auto_retry.py`:
```python
import datetime
from zoneinfo import ZoneInfo

class TestParseResetTime(unittest.TestCase):
    def test_3am_today_if_in_future(self):
        # "now" is 2am Bangkok same day → 3am same day = 1h delta
        now = datetime.datetime(2026, 5, 23, 2, 0, tzinfo=ZoneInfo("Asia/Bangkok"))
        text = "You've hit your limit · resets 3am (Asia/Bangkok)"
        delta = auto_retry._parse_reset_time(text, now=now)
        self.assertEqual(delta, 3600)

    def test_3am_tomorrow_if_already_past(self):
        # "now" is 5am Bangkok → 3am next day = 22h delta
        now = datetime.datetime(2026, 5, 23, 5, 0, tzinfo=ZoneInfo("Asia/Bangkok"))
        text = "You've hit your limit · resets 3am (Asia/Bangkok)"
        delta = auto_retry._parse_reset_time(text, now=now)
        self.assertEqual(delta, 22 * 3600)

    def test_8pm_today(self):
        now = datetime.datetime(2026, 5, 23, 14, 0, tzinfo=ZoneInfo("Asia/Bangkok"))
        text = "You've hit your session limit · resets 8pm (Asia/Bangkok)"
        delta = auto_retry._parse_reset_time(text, now=now)
        self.assertEqual(delta, 6 * 3600)

    def test_explicit_date(self):
        now = datetime.datetime(2026, 5, 8, 10, 0, tzinfo=ZoneInfo("Asia/Bangkok"))
        text = "You've hit your limit · resets May 13, 1pm (Asia/Bangkok)"
        delta = auto_retry._parse_reset_time(text, now=now)
        # May 8 10:00 → May 13 13:00 = 5 days + 3 hours
        self.assertEqual(delta, 5 * 86400 + 3 * 3600)

    def test_no_timezone_uses_utc(self):
        now = datetime.datetime(2026, 5, 23, 2, 0, tzinfo=ZoneInfo("UTC"))
        text = "You've hit your limit · resets 3am"
        delta = auto_retry._parse_reset_time(text, now=now)
        self.assertEqual(delta, 3600)

    def test_gibberish_returns_none(self):
        self.assertIsNone(auto_retry._parse_reset_time("nope"))

    def test_no_time_returns_none(self):
        self.assertIsNone(auto_retry._parse_reset_time("resets soon"))
```

- [ ] **Step 2: Run, verify fail**

```bash
python3 -m unittest tests.test_auto_retry.TestParseResetTime -v
```
Expected: AttributeError or wrong returns.

- [ ] **Step 3: Implement `_parse_reset_time`**

Add to imports: `import datetime`, `import re`, `from zoneinfo import ZoneInfo`.

Add after `_classify`:
```python
# "resets 3am (Asia/Bangkok)" or "resets May 13, 1pm (Asia/Bangkok)"
# Time: <hour>(:<minute>)?(am|pm)
# Optional date prefix: <Mon> <day>,
_RESET_RE = re.compile(
    r"resets\s+"
    r"(?:(?P<month>Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+"
    r"(?P<day>\d{1,2}),\s+)?"
    r"(?P<hour>\d{1,2})(?::(?P<minute>\d{2}))?(?P<ampm>am|pm)"
    r"(?:\s*\((?P<tz>[^)]+)\))?",
    re.IGNORECASE,
)

_MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def _parse_reset_time(text: str,
                      now: datetime.datetime | None = None) -> int | None:
    """Parse '...resets 3am (Asia/Bangkok)...' → seconds from now until reset.

    Returns None on any parse failure. If no timezone is in the text, UTC is
    assumed.
    """
    try:
        m = _RESET_RE.search(text)
        if not m:
            return None
        tz = ZoneInfo(m.group("tz")) if m.group("tz") else ZoneInfo("UTC")
        if now is None:
            now = datetime.datetime.now(tz=tz)
        elif now.tzinfo is None:
            now = now.replace(tzinfo=tz)
        else:
            now = now.astimezone(tz)

        hour = int(m.group("hour")) % 12
        if m.group("ampm").lower() == "pm":
            hour += 12
        minute = int(m.group("minute") or 0)

        if m.group("month"):
            month = _MONTHS[m.group("month").lower()]
            day = int(m.group("day"))
            target = datetime.datetime(now.year, month, day, hour, minute, tzinfo=tz)
            if target < now:
                target = target.replace(year=now.year + 1)
        else:
            target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if target <= now:
                target += datetime.timedelta(days=1)

        delta = int((target - now).total_seconds())
        return max(delta, 0)
    except Exception:
        return None
```

- [ ] **Step 4: Run tests**

```bash
python3 -m unittest tests.test_auto_retry.TestParseResetTime -v
```
Expected: 7 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/claude-auto-retry/
git -c user.name='vcth4nh' -c user.email='tvu25337@gmail.com' \
  commit -q -m "claude-auto-retry: _parse_reset_time extracts seconds-until-reset"
```

---

## Task 9: `_classify` — hard-quota branch

**Files:**
- Modify: `plugins/claude-auto-retry/hooks/auto_retry.py`
- Modify: `plugins/claude-auto-retry/tests/test_auto_retry.py`

- [ ] **Step 1: Write failing tests**

Append to `tests/test_auto_retry.py`:
```python
class TestClassifyHardQuota(unittest.TestCase):
    def setUp(self):
        self.cfg = copy.deepcopy(auto_retry.DEFAULT_CONFIG)
        self.now = datetime.datetime(
            2026, 5, 23, 2, 0, tzinfo=ZoneInfo("Asia/Bangkok"))

    def test_parsed_within_max_wait(self):
        text = "You've hit your limit · resets 3am (Asia/Bangkok)"
        with mock.patch.object(auto_retry, "_parse_reset_time", return_value=3600):
            backoff, source = auto_retry._classify("rate_limit", text, self.cfg)
        self.assertEqual(backoff, 3600)
        self.assertEqual(source, "quota_parsed")

    def test_parse_fails_uses_fallback(self):
        text = "You've hit your limit · resets at some weird time"
        with mock.patch.object(auto_retry, "_parse_reset_time", return_value=None):
            backoff, source = auto_retry._classify("rate_limit", text, self.cfg)
        self.assertEqual(backoff, self.cfg["backoff"]["hard_quota_fallback"])
        self.assertEqual(source, "quota_fallback")

    def test_too_far_skipped(self):
        text = "You've hit your limit · resets May 30, 1pm (Asia/Bangkok)"
        with mock.patch.object(auto_retry, "_parse_reset_time", return_value=10 * 86400):
            backoff, source = auto_retry._classify("rate_limit", text, self.cfg)
        self.assertIsNone(backoff)
        self.assertEqual(source, "quota_too_far")

    def test_parse_disabled_uses_fallback(self):
        self.cfg["hard_quota"]["parse_reset_time"] = False
        text = "You've hit your limit · resets 3am (Asia/Bangkok)"
        with mock.patch.object(auto_retry, "_parse_reset_time") as m:
            backoff, source = auto_retry._classify("rate_limit", text, self.cfg)
        m.assert_not_called()
        self.assertEqual(backoff, self.cfg["backoff"]["hard_quota_fallback"])
        self.assertEqual(source, "quota_fallback")
```

- [ ] **Step 2: Run, verify fail**

```bash
python3 -m unittest tests.test_auto_retry.TestClassifyHardQuota -v
```
Expected: 4 fail with `source == "quota_unimplemented"` or similar.

- [ ] **Step 3: Replace the placeholder hard-quota branch in `_classify`**

In `auto_retry.py`, replace the line `return None, "quota_unimplemented"` with:
```python
        # Hard usage quota
        if not bool(cfg["hard_quota"]["parse_reset_time"]):
            return int(cfg["backoff"]["hard_quota_fallback"]), "quota_fallback"
        delta = _parse_reset_time(text)
        if delta is None:
            return int(cfg["backoff"]["hard_quota_fallback"]), "quota_fallback"
        if delta > int(cfg["hard_quota"]["max_wait"]):
            return None, "quota_too_far"
        return delta, "quota_parsed"
```

- [ ] **Step 4: Run tests**

```bash
python3 -m unittest tests.test_auto_retry.TestClassifyHardQuota tests.test_auto_retry.TestClassifyTransient -v
```
Expected: All pass.

- [ ] **Step 5: Commit**

```bash
git add plugins/claude-auto-retry/
git -c user.name='vcth4nh' -c user.email='tvu25337@gmail.com' \
  commit -q -m "claude-auto-retry: _classify routes hard-quota errors via parse-or-fallback"
```

---

## Task 10: `_dedup_acquire` — atomic O_EXCL sentinel

**Files:**
- Modify: `plugins/claude-auto-retry/hooks/auto_retry.py`
- Modify: `plugins/claude-auto-retry/tests/test_auto_retry.py`

- [ ] **Step 1: Write failing tests**

Append:
```python
import time

class TestDedupAcquire(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.env = mock.patch.dict(
            "os.environ",
            {"CLAUDE_AUTO_RETRY_SENTINEL_DIR": self.tmp.name},
        )
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_first_call_wins(self):
        self.assertTrue(auto_retry._dedup_acquire("%7", 30))

    def test_second_call_within_window_loses(self):
        self.assertTrue(auto_retry._dedup_acquire("%7", 30))
        self.assertFalse(auto_retry._dedup_acquire("%7", 30))

    def test_stale_sentinel_lets_next_through(self):
        sentinel = pathlib.Path(self.tmp.name) / "claude-retry-7"
        sentinel.touch()
        # Backdate
        old = time.time() - 60
        os.utime(sentinel, (old, old))
        self.assertTrue(auto_retry._dedup_acquire("%7", 30))

    def test_different_panes_dont_collide(self):
        self.assertTrue(auto_retry._dedup_acquire("%7", 30))
        self.assertTrue(auto_retry._dedup_acquire("%9", 30))
```

- [ ] **Step 2: Run, verify fail**

```bash
python3 -m unittest tests.test_auto_retry.TestDedupAcquire -v
```
Expected: AttributeError.

- [ ] **Step 3: Implement `_dedup_acquire`**

Add `import time` to engine imports (top of file).

Add after `_parse_reset_time`:
```python
def _sentinel_path(pane_id: str) -> pathlib.Path:
    return _sentinel_dir() / f"claude-retry-{pane_id.lstrip('%')}"


def _dedup_acquire(pane_id: str, window: int) -> bool:
    """Return True if we got the dedup slot for this pane.

    Uses O_CREAT|O_EXCL for atomicity. If a sentinel exists but is older
    than `window` seconds, replace it and return True.
    """
    path = _sentinel_path(pane_id)
    path.parent.mkdir(parents=True, exist_ok=True)

    # If a stale sentinel exists, blow it away first.
    try:
        age = time.time() - path.stat().st_mtime
        if age > window:
            path.unlink(missing_ok=True)
    except FileNotFoundError:
        pass

    try:
        fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        os.close(fd)
        return True
    except FileExistsError:
        return False
```

- [ ] **Step 4: Run tests**

```bash
python3 -m unittest tests.test_auto_retry.TestDedupAcquire -v
```
Expected: 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/claude-auto-retry/
git -c user.name='vcth4nh' -c user.email='tvu25337@gmail.com' \
  commit -q -m "claude-auto-retry: _dedup_acquire with O_EXCL + stale eviction"
```

---

## Task 11: `_log_event` — atomic JSONL append

**Files:**
- Modify: `plugins/claude-auto-retry/hooks/auto_retry.py`
- Modify: `plugins/claude-auto-retry/tests/test_auto_retry.py`

- [ ] **Step 1: Write failing test**

Append:
```python
import json

class TestLogEvent(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.log_path = pathlib.Path(self.tmp.name) / "log.jsonl"
        self.env = mock.patch.dict(
            "os.environ",
            {"CLAUDE_AUTO_RETRY_LOG_PATH": str(self.log_path)},
        )
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_log_appends_one_line(self):
        auto_retry._log_event({"outcome": "fired", "error": "rate_limit"})
        lines = self.log_path.read_text().splitlines()
        self.assertEqual(len(lines), 1)
        rec = json.loads(lines[0])
        self.assertEqual(rec["outcome"], "fired")
        self.assertEqual(rec["error"], "rate_limit")
        self.assertIn("ts", rec)  # auto-added

    def test_log_appends_multiple_lines(self):
        for i in range(3):
            auto_retry._log_event({"i": i})
        self.assertEqual(len(self.log_path.read_text().splitlines()), 3)

    def test_log_creates_parent_dirs(self):
        nested = pathlib.Path(self.tmp.name) / "a/b/c/log.jsonl"
        with mock.patch.dict("os.environ",
                             {"CLAUDE_AUTO_RETRY_LOG_PATH": str(nested)}):
            auto_retry._log_event({"x": 1})
        self.assertTrue(nested.exists())
```

- [ ] **Step 2: Run, verify fail**

```bash
python3 -m unittest tests.test_auto_retry.TestLogEvent -v
```
Expected: AttributeError.

- [ ] **Step 3: Implement `_log_event`**

Add `import json` to engine imports.

Add after `_dedup_acquire`:
```python
def _log_event(event: dict) -> None:
    """Append one JSON line to the persistent log. Best-effort, never raises."""
    try:
        path = _log_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        if "ts" not in event:
            event = {"ts": datetime.datetime.now().astimezone().isoformat(),
                     **event}
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
    except Exception:
        pass  # logging must never crash a hook
```

- [ ] **Step 4: Run tests**

```bash
python3 -m unittest tests.test_auto_retry.TestLogEvent -v
```
Expected: 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/claude-auto-retry/
git -c user.name='vcth4nh' -c user.email='tvu25337@gmail.com' \
  commit -q -m "claude-auto-retry: _log_event appends JSONL with timestamp"
```

---

## Task 12: Pending pidfile management

**Files:**
- Modify: `plugins/claude-auto-retry/hooks/auto_retry.py`
- Modify: `plugins/claude-auto-retry/tests/test_auto_retry.py`

- [ ] **Step 1: Write failing tests**

Append:
```python
class TestPendingFiles(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.env = mock.patch.dict(
            "os.environ",
            {"CLAUDE_AUTO_RETRY_PENDING_DIR": self.tmp.name},
        )
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_write_creates_pidfile(self):
        auto_retry._write_pending({"pid": 9999, "pane_id": "%7", "fires_at": "x"})
        self.assertTrue((pathlib.Path(self.tmp.name) / "9999.json").exists())

    def test_delete_removes_pidfile(self):
        auto_retry._write_pending({"pid": 9999})
        auto_retry._delete_pending(9999)
        self.assertFalse((pathlib.Path(self.tmp.name) / "9999.json").exists())

    def test_delete_missing_is_silent(self):
        auto_retry._delete_pending(12345)  # no error

    def test_list_pending(self):
        auto_retry._write_pending({"pid": 100, "pane_id": "%7", "fires_at": "x"})
        auto_retry._write_pending({"pid": 200, "pane_id": "%9", "fires_at": "y"})
        items = sorted(auto_retry._list_pending(), key=lambda e: e["pid"])
        self.assertEqual([i["pid"] for i in items], [100, 200])
```

- [ ] **Step 2: Run, verify fail**

```bash
python3 -m unittest tests.test_auto_retry.TestPendingFiles -v
```

- [ ] **Step 3: Implement pending helpers**

Add after `_log_event`:
```python
def _pending_path(pid: int) -> pathlib.Path:
    return _pending_dir() / f"{pid}.json"


def _write_pending(entry: dict) -> None:
    path = _pending_path(int(entry["pid"]))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(entry, ensure_ascii=False))


def _delete_pending(pid: int) -> None:
    try:
        _pending_path(pid).unlink()
    except FileNotFoundError:
        pass


def _list_pending() -> list[dict]:
    out = []
    try:
        for p in _pending_dir().iterdir():
            if not p.name.endswith(".json"):
                continue
            try:
                out.append(json.loads(p.read_text()))
            except Exception:
                continue
    except FileNotFoundError:
        pass
    return out
```

- [ ] **Step 4: Run tests**

```bash
python3 -m unittest tests.test_auto_retry.TestPendingFiles -v
```
Expected: 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/claude-auto-retry/
git -c user.name='vcth4nh' -c user.email='tvu25337@gmail.com' \
  commit -q -m "claude-auto-retry: pending pidfile read/write/list/delete"
```

---

## Task 13: `_cleanup_stale_pending` and `_rotate_log_if_needed`

**Files:**
- Modify: `plugins/claude-auto-retry/hooks/auto_retry.py`
- Modify: `plugins/claude-auto-retry/tests/test_auto_retry.py`

- [ ] **Step 1: Write failing tests**

Append:
```python
class TestStaleCleanup(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.log = pathlib.Path(self.tmp.name) / "log.jsonl"
        self.pending = pathlib.Path(self.tmp.name) / "pending"
        self.env = mock.patch.dict(
            "os.environ",
            {
                "CLAUDE_AUTO_RETRY_LOG_PATH": str(self.log),
                "CLAUDE_AUTO_RETRY_PENDING_DIR": str(self.pending),
            },
        )
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_unlinks_entry_past_grace(self):
        far_past = (datetime.datetime.now() - datetime.timedelta(hours=24))\
                   .astimezone().isoformat()
        auto_retry._write_pending(
            {"pid": 9999, "pane_id": "%7", "fires_at": far_past})
        auto_retry._cleanup_stale_pending(grace=300)
        self.assertEqual(auto_retry._list_pending(), [])

    def test_keeps_entry_within_grace(self):
        soon = (datetime.datetime.now() + datetime.timedelta(seconds=60))\
               .astimezone().isoformat()
        auto_retry._write_pending(
            {"pid": 9999, "pane_id": "%7", "fires_at": soon})
        auto_retry._cleanup_stale_pending(grace=300)
        self.assertEqual(len(auto_retry._list_pending()), 1)


class TestLogRotation(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.log = pathlib.Path(self.tmp.name) / "log.jsonl"
        self.env = mock.patch.dict(
            "os.environ",
            {"CLAUDE_AUTO_RETRY_LOG_PATH": str(self.log)},
        )
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_no_rotation_under_threshold(self):
        self.log.parent.mkdir(parents=True, exist_ok=True)
        self.log.write_text("x" * 100)
        auto_retry._rotate_log_if_needed(threshold=1024)
        self.assertTrue(self.log.exists())
        self.assertFalse(self.log.with_suffix(".jsonl.1").exists())

    def test_rotates_at_threshold(self):
        self.log.parent.mkdir(parents=True, exist_ok=True)
        self.log.write_text("x" * 2000)
        auto_retry._rotate_log_if_needed(threshold=1024)
        rotated = pathlib.Path(str(self.log) + ".1")
        self.assertTrue(rotated.exists())
        self.assertFalse(self.log.exists())
```

- [ ] **Step 2: Run, verify fail**

```bash
python3 -m unittest tests.test_auto_retry.TestStaleCleanup tests.test_auto_retry.TestLogRotation -v
```

- [ ] **Step 3: Implement both**

Add after `_list_pending`:
```python
def _cleanup_stale_pending(grace: int) -> None:
    """Remove pending entries whose fires_at is more than `grace` seconds past."""
    now = datetime.datetime.now().astimezone()
    for entry in _list_pending():
        try:
            fires_at = datetime.datetime.fromisoformat(entry["fires_at"])
            if (now - fires_at).total_seconds() > grace:
                _delete_pending(int(entry["pid"]))
                _log_event({
                    "outcome": "error",
                    "reason": "stale_orphan",
                    "pid": entry.get("pid"),
                    "pane_id": entry.get("pane_id"),
                })
        except Exception:
            continue


def _rotate_log_if_needed(threshold: int = 5 * 1024 * 1024) -> None:
    """Rotate log.jsonl → log.jsonl.1 when it exceeds threshold bytes."""
    try:
        path = _log_path()
        if path.stat().st_size > threshold:
            rotated = pathlib.Path(str(path) + ".1")
            path.rename(rotated)
    except FileNotFoundError:
        pass
    except Exception:
        pass
```

- [ ] **Step 4: Run tests**

```bash
python3 -m unittest tests.test_auto_retry.TestStaleCleanup tests.test_auto_retry.TestLogRotation -v
```
Expected: 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/claude-auto-retry/
git -c user.name='vcth4nh' -c user.email='tvu25337@gmail.com' \
  commit -q -m "claude-auto-retry: stale pending cleanup + lazy log rotation"
```

---

## Task 14: `_resolve_pane` — friendly name via tmux

**Files:**
- Modify: `plugins/claude-auto-retry/hooks/auto_retry.py`
- Modify: `plugins/claude-auto-retry/tests/test_auto_retry.py`

- [ ] **Step 1: Write failing tests**

Append:
```python
import subprocess

class TestResolvePane(unittest.TestCase):
    def test_returns_tmux_output_on_success(self):
        completed = mock.Mock(returncode=0, stdout="mywork:0.1 (claude)\n")
        with mock.patch.object(auto_retry.subprocess, "run", return_value=completed):
            self.assertEqual(auto_retry._resolve_pane("%7"), "mywork:0.1 (claude)")

    def test_falls_back_on_tmux_error(self):
        def boom(*a, **k):
            raise subprocess.CalledProcessError(1, "tmux")
        with mock.patch.object(auto_retry.subprocess, "run", side_effect=boom):
            self.assertEqual(auto_retry._resolve_pane("%7"), "%7")

    def test_falls_back_on_missing_tmux(self):
        with mock.patch.object(auto_retry.subprocess, "run",
                               side_effect=FileNotFoundError):
            self.assertEqual(auto_retry._resolve_pane("%7"), "%7")
```

- [ ] **Step 2: Run, verify fail**

```bash
python3 -m unittest tests.test_auto_retry.TestResolvePane -v
```

- [ ] **Step 3: Implement `_resolve_pane`**

Add `import subprocess` to engine imports.

Add after `_rotate_log_if_needed`:
```python
_PANE_FORMAT = "#{session_name}:#{window_index}.#{pane_index} (#{pane_title})"


def _resolve_pane(pane_id: str) -> str:
    """Return a human-readable name for a tmux pane ID. Falls back to the ID."""
    try:
        r = subprocess.run(
            ["tmux", "display-message", "-t", pane_id, "-p", _PANE_FORMAT],
            capture_output=True, text=True, timeout=2, check=True,
        )
        return r.stdout.strip() or pane_id
    except Exception:
        return pane_id
```

- [ ] **Step 4: Run tests**

```bash
python3 -m unittest tests.test_auto_retry.TestResolvePane -v
```
Expected: 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/claude-auto-retry/
git -c user.name='vcth4nh' -c user.email='tvu25337@gmail.com' \
  commit -q -m "claude-auto-retry: _resolve_pane via tmux display-message with fallback"
```

---

## Task 15: `_hook` orchestration

**Files:**
- Modify: `plugins/claude-auto-retry/hooks/auto_retry.py`
- Modify: `plugins/claude-auto-retry/tests/test_auto_retry.py`

- [ ] **Step 1: Write failing tests**

Append:
```python
class TestHookOrchestration(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.log = pathlib.Path(self.tmp.name) / "log.jsonl"
        self.pending = pathlib.Path(self.tmp.name) / "pending"
        self.sentinel = pathlib.Path(self.tmp.name) / "sentinel"
        self.sentinel.mkdir()
        self.env = mock.patch.dict(
            "os.environ",
            {
                "CLAUDE_AUTO_RETRY_LOG_PATH": str(self.log),
                "CLAUDE_AUTO_RETRY_PENDING_DIR": str(self.pending),
                "CLAUDE_AUTO_RETRY_SENTINEL_DIR": str(self.sentinel),
                "CLAUDE_AUTO_RETRY_USER_CONFIG": str(self.sentinel / "nope.toml"),
                "TMUX_PANE": "%7",
            },
        )
        self.env.start()
        self.addCleanup(self.env.stop)

    def _feed(self, event: dict) -> None:
        with mock.patch.object(sys, "stdin", io.StringIO(json.dumps(event))):
            auto_retry._hook()

    def test_disabled_short_circuits(self):
        cfg_path = pathlib.Path(self.tmp.name) / "u.toml"
        cfg_path.write_text("enabled = false\n")
        with mock.patch.dict("os.environ",
                             {"CLAUDE_AUTO_RETRY_USER_CONFIG": str(cfg_path)}), \
             mock.patch.object(auto_retry.subprocess, "Popen") as p:
            self._feed({"hook_event_name": "StopFailure", "error": "rate_limit",
                        "error_details": "transient", "cwd": self.tmp.name})
            p.assert_not_called()
        rec = json.loads(self.log.read_text().splitlines()[-1])
        self.assertEqual(rec["source"], "disabled")

    def test_no_tmux_skipped(self):
        with mock.patch.dict("os.environ", {"TMUX_PANE": ""}), \
             mock.patch.object(auto_retry.subprocess, "Popen") as p:
            self._feed({"hook_event_name": "StopFailure", "error": "rate_limit",
                        "error_details": "transient", "cwd": self.tmp.name})
            p.assert_not_called()
        rec = json.loads(self.log.read_text().splitlines()[-1])
        self.assertEqual(rec["source"], "no_tmux")

    def test_not_retryable_skipped(self):
        with mock.patch.object(auto_retry.subprocess, "Popen") as p:
            self._feed({"hook_event_name": "StopFailure", "error": "invalid_request",
                        "error_details": "policy", "cwd": self.tmp.name})
            p.assert_not_called()
        rec = json.loads(self.log.read_text().splitlines()[-1])
        self.assertEqual(rec["source"], "not_retryable")

    def test_per_error_disabled_skipped(self):
        cfg_path = pathlib.Path(self.tmp.name) / "u.toml"
        cfg_path.write_text("[per_error_enable]\nrate_limit = false\n")
        with mock.patch.dict("os.environ",
                             {"CLAUDE_AUTO_RETRY_USER_CONFIG": str(cfg_path)}), \
             mock.patch.object(auto_retry.subprocess, "Popen") as p:
            self._feed({"hook_event_name": "StopFailure", "error": "rate_limit",
                        "error_details": "transient text",
                        "cwd": self.tmp.name})
            p.assert_not_called()
        rec = json.loads(self.log.read_text().splitlines()[-1])
        self.assertEqual(rec["source"], "per_error_disabled")

    def test_happy_path_spawns_timer(self):
        with mock.patch.object(auto_retry.subprocess, "Popen") as p, \
             mock.patch.object(auto_retry, "_resolve_pane", return_value="my:0.1"):
            self._feed({"hook_event_name": "StopFailure", "error": "rate_limit",
                        "error_details": "Server is temporarily limiting",
                        "session_id": "abc", "cwd": self.tmp.name})
            p.assert_called_once()
            args, kwargs = p.call_args
            self.assertIn("--timer", args[0])
            self.assertIn("%7", args[0])
            self.assertIn("60", args[0])
            self.assertEqual(kwargs.get("start_new_session"), True)
        # Sentinel created
        self.assertTrue((self.sentinel / "claude-retry-7").exists())

    def test_dedup_bounces_second_hook(self):
        with mock.patch.object(auto_retry.subprocess, "Popen") as p, \
             mock.patch.object(auto_retry, "_resolve_pane", return_value="my:0.1"):
            evt = {"hook_event_name": "StopFailure", "error": "rate_limit",
                   "error_details": "Server is temporarily limiting",
                   "session_id": "abc", "cwd": self.tmp.name}
            self._feed(evt)
            self._feed(evt)
            self.assertEqual(p.call_count, 1)
        rec = json.loads(self.log.read_text().splitlines()[-1])
        self.assertEqual(rec["source"], "dedup_bounced")

    def test_malformed_stdin_does_not_crash(self):
        with mock.patch.object(sys, "stdin", io.StringIO("not json")):
            auto_retry._hook()  # should not raise
```

- [ ] **Step 2: Run, verify fail**

```bash
python3 -m unittest tests.test_auto_retry.TestHookOrchestration -v
```

- [ ] **Step 3: Implement `_hook`**

Replace the stub `_hook` in `auto_retry.py` with:
```python
def _hook() -> None:
    """StopFailure entry. Fast (<1s), fire-and-forget."""
    try:
        raw = sys.stdin.read()
        try:
            event = json.loads(raw) if raw.strip() else {}
        except json.JSONDecodeError:
            _log_event({"outcome": "error", "reason": "stdin_not_json"})
            return

        err = event.get("error", "unknown")
        text = event.get("error_details") or event.get("last_assistant_message") or ""
        text = text[:500]  # cap for logging hygiene
        status = event.get("apiErrorStatus")
        session_id = event.get("session_id")
        cwd = event.get("cwd") or os.getcwd()

        cfg = _load_config(cwd)

        # Order: enabled → no_tmux → not_retryable → per_error_disabled
        #        → dedup → classify (which can produce quota_too_far)
        base_event = {
            "error": err,
            "error_status": status,
            "error_text": text,
            "session_id": session_id,
        }

        if not bool(cfg.get("enabled", True)):
            _log_event({**base_event, "outcome": "skipped", "source": "disabled"})
            return

        pane_id = os.environ.get("TMUX_PANE") or ""
        if not pane_id:
            _log_event({**base_event, "outcome": "skipped", "source": "no_tmux"})
            return

        if err not in _RETRYABLE:
            _log_event({**base_event, "outcome": "skipped", "source": "not_retryable"})
            return

        per_err = cfg.get("per_error_enable", {})
        if not bool(per_err.get(err, True)):
            _log_event({**base_event, "outcome": "skipped",
                       "source": "per_error_disabled"})
            return

        # Stale cleanup before we add to pending.
        grace = int(cfg["hard_quota"]["max_wait"]) + 300
        _cleanup_stale_pending(grace=grace)
        _rotate_log_if_needed()

        if not _dedup_acquire(pane_id, int(cfg.get("dedup_window", 30))):
            _log_event({**base_event, "outcome": "skipped",
                       "source": "dedup_bounced", "pane_id": pane_id})
            return

        backoff, source = _classify(err, text, cfg)
        if backoff is None:
            _log_event({**base_event, "outcome": "skipped", "source": source,
                       "pane_id": pane_id})
            return

        pane_name = _resolve_pane(pane_id)

        # Spawn detached timer
        subprocess.Popen(
            [sys.executable, os.path.abspath(__file__),
             "--timer", pane_id, str(backoff), err],
            start_new_session=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env={**os.environ, "_CAR_PANE_NAME": pane_name,
                 "_CAR_SOURCE": source,
                 "_CAR_ERROR_STATUS": "" if status is None else str(status),
                 "_CAR_SESSION_ID": session_id or "",
                 "_CAR_ERROR_TEXT": text},
        )
        _log_event({**base_event, "outcome": "scheduled", "source": source,
                   "backoff": backoff, "pane_id": pane_id, "pane_name": pane_name})
    except Exception as e:
        # Never re-raise from a hook. KeyboardInterrupt/SystemExit propagate.
        _log_event({"outcome": "error", "reason": f"hook_exception: {e}"})
```

- [ ] **Step 4: Run all engine tests**

```bash
python3 -m unittest discover tests -v
```
Expected: All pass (including 7 hook tests).

- [ ] **Step 5: Commit**

```bash
git add plugins/claude-auto-retry/
git -c user.name='vcth4nh' -c user.email='tvu25337@gmail.com' \
  commit -q -m "claude-auto-retry: _hook orchestrates classify+dedup+spawn"
```

---

## Task 16: `_timer` — sleep, send-keys, log, cleanup

**Files:**
- Modify: `plugins/claude-auto-retry/hooks/auto_retry.py`
- Modify: `plugins/claude-auto-retry/tests/test_auto_retry.py`

- [ ] **Step 1: Write failing tests**

Append:
```python
class TestTimer(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.log = pathlib.Path(self.tmp.name) / "log.jsonl"
        self.pending = pathlib.Path(self.tmp.name) / "pending"
        self.env = mock.patch.dict(
            "os.environ",
            {
                "CLAUDE_AUTO_RETRY_LOG_PATH": str(self.log),
                "CLAUDE_AUTO_RETRY_PENDING_DIR": str(self.pending),
                "_CAR_PANE_NAME": "my:0.1 (claude)",
                "_CAR_SOURCE": "transient",
                "_CAR_ERROR_STATUS": "429",
                "_CAR_SESSION_ID": "abc",
                "_CAR_ERROR_TEXT": "test",
            },
        )
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_writes_pending_then_deletes(self):
        sleeps = []
        with mock.patch.object(auto_retry.time, "sleep",
                               side_effect=lambda s: sleeps.append(s)), \
             mock.patch.object(auto_retry.subprocess, "run", return_value=mock.Mock(returncode=0)):
            auto_retry._timer("%7", 0, "rate_limit")
        self.assertEqual(sleeps, [0])
        self.assertEqual(auto_retry._list_pending(), [])

    def test_sends_up_and_enter(self):
        calls = []
        def fake_run(args, **kwargs):
            calls.append(args)
            return mock.Mock(returncode=0)
        with mock.patch.object(auto_retry.time, "sleep"), \
             mock.patch.object(auto_retry.subprocess, "run", side_effect=fake_run):
            auto_retry._timer("%7", 0, "rate_limit")
        send_keys = [c for c in calls if c[:2] == ["tmux", "send-keys"]]
        self.assertEqual(len(send_keys), 1)
        self.assertIn("Up", send_keys[0])
        self.assertIn("Enter", send_keys[0])
        self.assertIn("%7", send_keys[0])

    def test_quiet_skips_display_message(self):
        cfg_path = pathlib.Path(self.tmp.name) / "u.toml"
        cfg_path.write_text("quiet = true\n")
        with mock.patch.dict("os.environ",
                             {"CLAUDE_AUTO_RETRY_USER_CONFIG": str(cfg_path)}), \
             mock.patch.object(auto_retry.time, "sleep"), \
             mock.patch.object(auto_retry.subprocess, "run",
                               return_value=mock.Mock(returncode=0)) as run:
            auto_retry._timer("%7", 0, "rate_limit")
        cmds = [c.args[0] for c in run.call_args_list]
        self.assertFalse(any(c[:2] == ["tmux", "display-message"] for c in cmds))

    def test_logs_fired_outcome(self):
        with mock.patch.object(auto_retry.time, "sleep"), \
             mock.patch.object(auto_retry.subprocess, "run",
                               return_value=mock.Mock(returncode=0)):
            auto_retry._timer("%7", 0, "rate_limit")
        rec = json.loads(self.log.read_text().splitlines()[-1])
        self.assertEqual(rec["outcome"], "fired")
        self.assertEqual(rec["pane_id"], "%7")
        self.assertEqual(rec["error"], "rate_limit")

    def test_tmux_failure_logs_error_and_still_cleans_up(self):
        with mock.patch.object(auto_retry.time, "sleep"), \
             mock.patch.object(auto_retry.subprocess, "run",
                               return_value=mock.Mock(returncode=1)):
            auto_retry._timer("%7", 0, "rate_limit")
        rec = json.loads(self.log.read_text().splitlines()[-1])
        self.assertEqual(rec["outcome"], "error")
        self.assertEqual(rec["reason"], "tmux_send_failed")
        self.assertEqual(auto_retry._list_pending(), [])
```

- [ ] **Step 2: Run, verify fail**

```bash
python3 -m unittest tests.test_auto_retry.TestTimer -v
```

- [ ] **Step 3: Implement `_timer`**

Replace the stub `_timer` with:
```python
def _timer(pane: str, delay: int, error: str) -> None:
    """Sleep, then send Up+Enter to `pane`. Append fired/error log entry."""
    pid = os.getpid()
    now = datetime.datetime.now().astimezone()
    fires_at = (now + datetime.timedelta(seconds=delay)).isoformat()
    pane_name = os.environ.get("_CAR_PANE_NAME") or pane
    source = os.environ.get("_CAR_SOURCE") or "transient"
    error_status_raw = os.environ.get("_CAR_ERROR_STATUS") or ""
    error_status: int | None
    try:
        error_status = int(error_status_raw) if error_status_raw else None
    except ValueError:
        error_status = None
    session_id = os.environ.get("_CAR_SESSION_ID") or None
    error_text = os.environ.get("_CAR_ERROR_TEXT") or ""

    entry = {
        "pid": pid,
        "pane_id": pane,
        "pane_name": pane_name,
        "session_id": session_id,
        "error": error,
        "error_status": error_status,
        "scheduled_at": now.isoformat(),
        "fires_at": fires_at,
        "backoff": delay,
        "source": source,
    }
    try:
        _write_pending(entry)
        time.sleep(delay)

        send = subprocess.run(
            ["tmux", "send-keys", "-t", pane, "Up", "Enter"],
            capture_output=True, text=True,
        )
        if send.returncode != 0:
            _log_event({**entry, "outcome": "error", "error_text": error_text,
                       "reason": "tmux_send_failed",
                       "stderr": (send.stderr or "")[:200]})
            return

        cfg = _load_config(os.getcwd())
        if not bool(cfg.get("quiet", False)):
            subprocess.run(
                ["tmux", "display-message", "-t", pane,
                 f"[auto-retry: {error} — retried after {delay}s]"],
                capture_output=True, text=True,
            )
        _log_event({**entry, "outcome": "fired", "error_text": error_text})
    except Exception as e:
        _log_event({**entry, "outcome": "error",
                   "reason": f"timer_exception: {e}"})
    finally:
        _delete_pending(pid)
```

- [ ] **Step 4: Run all tests**

```bash
python3 -m unittest discover tests -v
```
Expected: All tests pass (existing + 5 new timer tests).

- [ ] **Step 5: Commit**

```bash
git add plugins/claude-auto-retry/
git -c user.name='vcth4nh' -c user.email='tvu25337@gmail.com' \
  commit -q -m "claude-auto-retry: _timer injects keys + logs outcome"
```

---

## Task 17: `_status` rendering

**Files:**
- Modify: `plugins/claude-auto-retry/hooks/auto_retry.py`
- Modify: `plugins/claude-auto-retry/tests/test_auto_retry.py`

- [ ] **Step 1: Write failing tests**

Append:
```python
class TestStatus(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.log = pathlib.Path(self.tmp.name) / "log.jsonl"
        self.pending = pathlib.Path(self.tmp.name) / "pending"
        self.env = mock.patch.dict(
            "os.environ",
            {
                "CLAUDE_AUTO_RETRY_LOG_PATH": str(self.log),
                "CLAUDE_AUTO_RETRY_PENDING_DIR": str(self.pending),
            },
        )
        self.env.start()
        self.addCleanup(self.env.stop)

    def _capture(self) -> str:
        buf = io.StringIO()
        with mock.patch.object(sys, "stdout", buf):
            auto_retry._status()
        return buf.getvalue()

    def test_empty_state(self):
        out = self._capture()
        self.assertIn("PENDING (0)", out)
        self.assertIn("RECENT (0)", out)

    def test_shows_pending(self):
        future = (datetime.datetime.now() + datetime.timedelta(seconds=60))\
                 .astimezone().isoformat()
        auto_retry._write_pending({
            "pid": 100, "pane_id": "%7", "pane_name": "my:0.1",
            "error": "rate_limit", "fires_at": future, "backoff": 60,
            "source": "transient",
        })
        out = self._capture()
        self.assertIn("PENDING (1)", out)
        self.assertIn("my:0.1", out)
        self.assertIn("rate_limit", out)

    def test_shows_recent_log_entries(self):
        auto_retry._log_event({"outcome": "fired", "error": "rate_limit",
                              "pane_name": "my:0.1", "backoff": 60,
                              "source": "transient"})
        out = self._capture()
        self.assertIn("RECENT (1)", out)
        self.assertIn("fired", out)
        self.assertIn("rate_limit", out)

    def test_recent_capped_at_20(self):
        for i in range(25):
            auto_retry._log_event({"outcome": "fired", "error": "rate_limit",
                                  "pane_name": "p", "backoff": 60,
                                  "source": "transient"})
        out = self._capture()
        self.assertIn("RECENT (20)", out)
```

- [ ] **Step 2: Run, verify fail**

```bash
python3 -m unittest tests.test_auto_retry.TestStatus -v
```

- [ ] **Step 3: Implement `_status`**

Replace the stub `_status` with:
```python
def _status() -> None:
    """Print pending + recent retry events as two tables."""
    print(_status_text())


def _status_text() -> str:
    now = datetime.datetime.now().astimezone()
    pending = _list_pending()

    pending_rows = []
    for entry in pending:
        try:
            fires_at = datetime.datetime.fromisoformat(entry["fires_at"])
            delta = int((fires_at - now).total_seconds())
            in_str = f"{delta}s" if delta < 60 else f"{delta // 60}m {delta % 60}s"
        except Exception:
            in_str = "?"
        pending_rows.append((
            entry.get("pane_name") or entry.get("pane_id") or "-",
            in_str,
            entry.get("error", "-"),
            f"{entry.get('backoff', '-')}s",
            entry.get("source", "-"),
        ))

    recent_rows = []
    try:
        with open(_log_path(), encoding="utf-8") as f:
            for line in f.read().splitlines()[-20:]:
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                recent_rows.append((
                    rec.get("outcome", "-"),
                    rec.get("ts", "-")[:19],
                    rec.get("pane_name") or rec.get("pane_id") or "-",
                    rec.get("error", "-"),
                    f"{rec.get('backoff', '-')}s" if rec.get("backoff") else "-",
                    rec.get("source") or rec.get("reason") or "-",
                ))
    except FileNotFoundError:
        pass

    lines = []
    lines.append(f"PENDING ({len(pending_rows)})")
    if pending_rows:
        lines.append(f"  {'pane':<30} {'fires in':>10}  {'error':<14} {'backoff':>8}  source")
        for row in pending_rows:
            lines.append(f"  {row[0]:<30} {row[1]:>10}  {row[2]:<14} {row[3]:>8}  {row[4]}")
    lines.append("")
    lines.append(f"RECENT ({len(recent_rows)})")
    if recent_rows:
        lines.append(f"  {'outcome':<10} {'ts':<19}  {'pane':<24} {'error':<14} {'backoff':>8}  source")
        for row in recent_rows:
            lines.append(f"  {row[0]:<10} {row[1]:<19}  {row[2]:<24} {row[3]:<14} {row[4]:>8}  {row[5]}")
    return "\n".join(lines)
```

- [ ] **Step 4: Run all tests**

```bash
python3 -m unittest discover tests -v
```

- [ ] **Step 5: Commit**

```bash
git add plugins/claude-auto-retry/
git -c user.name='vcth4nh' -c user.email='tvu25337@gmail.com' \
  commit -q -m "claude-auto-retry: _status renders pending + recent tables"
```

---

## Task 18: `_init_config`

**Files:**
- Modify: `plugins/claude-auto-retry/hooks/auto_retry.py`
- Create: `plugins/claude-auto-retry/examples/config.toml`
- Modify: `plugins/claude-auto-retry/tests/test_auto_retry.py`

- [ ] **Step 1: Write `examples/config.toml`**

`plugins/claude-auto-retry/examples/config.toml`:
```toml
# claude-auto-retry configuration.
# Drop this file at one of:
#   ~/.config/claude-auto-retry/config.toml         (user-wide)
#   <project>/.claude/claude-auto-retry.toml        (per-project override)
#
# The project file overrides the user file overrides these defaults.

# Master switch. If false, the hook short-circuits and logs `disabled`.
enabled = true

# Two-hook-fires-for-the-same-pane within this many seconds → the second is
# bounced. Prevents duplicate scheduling on error bursts.
dedup_window = 30

# When true, suppress the `tmux display-message` notice after a retry fires.
quiet = false

[backoff]
# "Server is temporarily limiting requests" (transient throttle).
rate_limit_transient = 60
# 500 Internal server error.
server_error = 30
# Generic "Overloaded" / "Internal server error" with no status code.
unknown = 30
# Used when the hook can't parse a hard-quota reset time.
hard_quota_fallback = 1800

[hard_quota]
# Parse messages like "resets 3am (Asia/Bangkok)" and schedule for then.
# If false, always use hard_quota_fallback.
parse_reset_time = true
# Skip auto-retry entirely if the parsed wait is longer than this (seconds).
# Default: 4h.
max_wait = 14400

[per_error_enable]
# Per-class toggles. Set any to false to log+skip that class.
rate_limit = true
server_error = true
unknown = true
```

- [ ] **Step 2: Write failing tests**

Append:
```python
class TestInitConfig(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.cwd = pathlib.Path(self.tmp.name)

    def test_copies_example_into_dot_claude(self):
        with mock.patch.object(auto_retry.os, "getcwd", return_value=str(self.cwd)):
            auto_retry._init_config()
        out = self.cwd / ".claude" / "claude-auto-retry.toml"
        self.assertTrue(out.exists())
        self.assertIn("enabled = true", out.read_text())

    def test_refuses_to_overwrite(self):
        out = self.cwd / ".claude" / "claude-auto-retry.toml"
        out.parent.mkdir()
        out.write_text("# mine\n")
        with mock.patch.object(auto_retry.os, "getcwd", return_value=str(self.cwd)):
            auto_retry._init_config()
        self.assertEqual(out.read_text(), "# mine\n")
```

- [ ] **Step 3: Run, verify fail**

```bash
python3 -m unittest tests.test_auto_retry.TestInitConfig -v
```

- [ ] **Step 4: Implement `_init_config`**

Add `import shutil` to engine imports.

Replace the stub `_init_config` with:
```python
def _init_config() -> None:
    """Copy examples/config.toml to <cwd>/.claude/claude-auto-retry.toml."""
    src = pathlib.Path(__file__).resolve().parent.parent / "examples" / "config.toml"
    dst_dir = pathlib.Path(os.getcwd()) / ".claude"
    dst = dst_dir / "claude-auto-retry.toml"
    if dst.exists():
        print(f"refusing to overwrite existing {dst}", file=sys.stderr)
        return
    dst_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    print(f"wrote {dst}")
```

- [ ] **Step 5: Run tests**

```bash
python3 -m unittest discover tests -v
```
Expected: All pass.

- [ ] **Step 6: Commit**

```bash
git add plugins/claude-auto-retry/
git -c user.name='vcth4nh' -c user.email='tvu25337@gmail.com' \
  commit -q -m "claude-auto-retry: examples/config.toml + _init_config copies it"
```

---

## Task 19: Hook registration (`hooks/hooks.json`)

**Files:**
- Create: `plugins/claude-auto-retry/hooks/hooks.json`

- [ ] **Step 1: Write `hooks.json`**

`plugins/claude-auto-retry/hooks/hooks.json`:
```json
{
  "hooks": {
    "StopFailure": [
      {
        "matcher": "rate_limit|server_error|unknown",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ${CLAUDE_PLUGIN_ROOT}/hooks/auto_retry.py --hook"
          }
        ]
      }
    ]
  }
}
```

- [ ] **Step 2: Verify JSON parses**

```bash
python3 -c "import json; json.load(open('/home/ubuntu/dev/vct-claude-marketplace-public/plugins/claude-auto-retry/hooks/hooks.json'))"
```
Expected: no output (parse OK).

- [ ] **Step 3: Commit**

```bash
git add plugins/claude-auto-retry/hooks/hooks.json
git -c user.name='vcth4nh' -c user.email='tvu25337@gmail.com' \
  commit -q -m "claude-auto-retry: register StopFailure hook for retryable classes"
```

---

## Task 20: User-invoked status skill

**Files:**
- Create: `plugins/claude-auto-retry/skills/status/SKILL.md`

- [ ] **Step 1: Write the skill**

`plugins/claude-auto-retry/skills/status/SKILL.md`:
```markdown
---
description: Show recent claude-auto-retry events and pending retry timers. Use when the user asks "what's pending", "did my retry fire", "show auto-retry log", "claude-auto-retry status", or invokes /claude-auto-retry:status.
argument-hint: ""
allowed-tools: [Bash]
---

# claude-auto-retry status

Run this command and show the raw output verbatim:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/hooks/auto_retry.py --status
```

If the command exits non-zero, report the exit code and any stderr — do not
re-render or interpret. The output is two tables (PENDING and RECENT) already
formatted for terminal display.
```

- [ ] **Step 2: Commit**

```bash
git add plugins/claude-auto-retry/skills/status/SKILL.md
git -c user.name='vcth4nh' -c user.email='tvu25337@gmail.com' \
  commit -q -m "claude-auto-retry: /claude-auto-retry:status user-invoked skill"
```

---

## Task 21: Passive "about" skill

**Files:**
- Create: `plugins/claude-auto-retry/skills/claude-auto-retry-about/SKILL.md`

- [ ] **Step 1: Write the skill**

`plugins/claude-auto-retry/skills/claude-auto-retry-about/SKILL.md`:
```markdown
---
description: Reference for the claude-auto-retry plugin. Use this skill when the user asks "how does auto-retry work", "why didn't my retry fire", "disable rate-limit retry", "claude-auto-retry config", "auto-retry status meaning", or any question about how this plugin classifies errors, where its state lives, or how to tune it.
---

# claude-auto-retry — Reference

The plugin auto-retries Claude Code sessions on transient API errors by
listening on the engine's `StopFailure` hook and injecting `Up Enter` into the
session's tmux pane after a class-appropriate backoff. No daemon, no wrapper,
no `--resume`.

## What gets retried

| Error class | Default action |
|---|---|
| `rate_limit` (transient: "Server is temporarily limiting") | retry after 60s |
| `rate_limit` (hard quota: "You've hit your limit · resets X") | parse reset time, schedule retry for then (fallback 30min if parse fails) |
| `server_error` (500) | retry after 30s |
| `unknown` (generic Overloaded / Internal server error with no status) | retry after 30s |
| `invalid_request`, `authentication_failed`, `billing_error`, `max_output_tokens` | **skipped** — not auto-recoverable |

The hook only fires inside a tmux pane (it uses `tmux send-keys` to inject
the retry keystrokes). Outside tmux it logs `no_tmux` and exits.

## Config

Three layers, last-wins, shallow merge per section:

1. Built-in defaults (in `hooks/auto_retry.py`)
2. User: `~/.config/claude-auto-retry/config.toml`
3. Project: `<cwd>/.claude/claude-auto-retry.toml`

To create a project config, run inside the project:
```
python3 $(claude plugin path claude-auto-retry)/hooks/auto_retry.py --init-config
```

Full schema in `examples/config.toml` (every field documented).

### To disable temporarily

Set `enabled = false` in either config layer. The hook short-circuits and logs
a `disabled` event so `--status` still shows it.

### To disable a specific error class

```toml
[per_error_enable]
rate_limit = false  # don't auto-retry rate limits at all
```

## Where state lives

| What | Where | Lifetime |
|---|---|---|
| Persistent retry log | `~/.local/state/claude-auto-retry/log.jsonl` | survives reboot, rotates at 5 MB |
| Live timer tracking | `/tmp/claude-auto-retry/pending/<pid>.json` | until timer completes or reboot |
| Dedup sentinel | `/tmp/claude-retry-<pane>` | `dedup_window` seconds (default 30) |

## Reading `/claude-auto-retry:status` output

Two sections:

- **PENDING** — timers currently sleeping. Columns: pane, fires-in, error class, backoff, source.
- **RECENT** — last 20 log entries. Columns: outcome, timestamp, pane, error class, backoff, source.

Outcomes:
- `scheduled` — timer was spawned (you'll see a matching `fired` later)
- `fired` — retry actually injected
- `skipped` — see `source` column for why (`disabled`, `no_tmux`, `not_retryable`, `per_error_disabled`, `dedup_bounced`, `quota_too_far`)
- `error` — something went wrong; `reason` column has the detail

## Known limitations

- **Subagent failures (`isSidechain: true`)** don't currently trigger `StopFailure` for the main session, so the plugin can't recover them. Planned for v0.2.
- **Non-tmux environments** are not supported — the plugin needs `tmux send-keys` as its injection channel.
- **Linux-only** target. macOS likely works (we don't use TIOCSTI), but unverified.

## Troubleshooting

- "I expected a retry and got nothing." → Run `/claude-auto-retry:status`. Check the most recent entry; the `source` field explains why it was skipped.
- "It retried but the timing was way off." → Look at the entry's `source`. `quota_fallback` means the reset-time parser couldn't read the message; consider opening an issue with the verbatim text.
- "Two retries fired for one error." → Should be impossible due to the `O_EXCL` sentinel. If it happens, file a bug with the log entries.
```

- [ ] **Step 2: Commit**

```bash
git add plugins/claude-auto-retry/skills/claude-auto-retry-about/SKILL.md
git -c user.name='vcth4nh' -c user.email='tvu25337@gmail.com' \
  commit -q -m "claude-auto-retry: passive about skill"
```

---

## Task 22: README

**Files:**
- Create: `plugins/claude-auto-retry/README.md`

- [ ] **Step 1: Write `README.md`**

`plugins/claude-auto-retry/README.md`:
```markdown
# claude-auto-retry

Auto-retry Claude Code sessions on transient API errors (rate limits, 5xx,
overloaded). Hooks the engine's `StopFailure` event; when an error fires,
schedules a backoff and uses `tmux send-keys` to re-submit the user's last
prompt against the same live session — no `--resume`, no wrapper, no daemon.

## Install

```
/plugin marketplace add vcth4nh/vct-claude-marketplace-public
/plugin install claude-auto-retry@vct-public
```

You must be running Claude Code inside a tmux pane. Outside tmux the plugin
silently no-ops (and logs why, visible in `--status`).

## How it works

| Error | Default | Configurable |
|---|---|---|
| `rate_limit` (transient throttle) | retry after 60s | yes |
| `rate_limit` (hard quota with reset time) | parse + schedule; fallback 30min | yes |
| `server_error` / `unknown` (5xx, Overloaded) | retry after 30s | yes |
| `invalid_request` / auth / billing / max_output_tokens | skipped — not auto-recoverable | n/a |

A brief notice fires in the pane after retry (`[auto-retry: rate_limit —
retried after 60s]`). Disable with `quiet = true` in config.

## Commands

- `/claude-auto-retry:status` — show pending timers and the last 20 events.

## Configuration

```bash
# Drop the example config into your project:
python3 $(claude plugin path claude-auto-retry)/hooks/auto_retry.py --init-config
# Or place it at ~/.config/claude-auto-retry/config.toml for user-wide settings.
```

Schema and every field documented in `examples/config.toml`. The
[`claude-auto-retry-about` skill](skills/claude-auto-retry-about/SKILL.md)
explains it in conversation.

## State

- `~/.local/state/claude-auto-retry/log.jsonl` — persistent retry history (5 MB rotation)
- `/tmp/claude-auto-retry/pending/<pid>.json` — live timer tracking
- `/tmp/claude-retry-<pane>` — dedup sentinel

## Manual smoke test

```bash
# In a tmux pane, launch claude. In another pane:
echo '{"hook_event_name":"StopFailure","error":"rate_limit","error_details":"Server is temporarily limiting","session_id":"test","cwd":"'$PWD'"}' \
  | TMUX_PANE=%X python3 ~/.claude/plugins/.../hooks/auto_retry.py --hook
# Wait 60s; the claude pane should auto-submit its last prompt.
# /claude-auto-retry:status will show one fired event.
```

## Known limitations (v0.1.0)

- Subagent errors (`isSidechain: true`) do not trigger `StopFailure` on the
  main session and are not retried. Planned for v0.2.
- Linux-only. macOS likely works but unverified.

## License

CC-BY-SA-4.0
```

- [ ] **Step 2: Commit**

```bash
git add plugins/claude-auto-retry/README.md
git -c user.name='vcth4nh' -c user.email='tvu25337@gmail.com' \
  commit -q -m "claude-auto-retry: README"
```

---

## Task 23: Integration test harness

**Files:**
- Create: `plugins/claude-auto-retry/tests/integration/run.sh`

- [ ] **Step 1: Write the harness**

`plugins/claude-auto-retry/tests/integration/run.sh`:
```bash
#!/usr/bin/env bash
# Integration tests for claude-auto-retry. Requires tmux.
# Run from the plugin root: bash tests/integration/run.sh
set -euo pipefail

if ! command -v tmux >/dev/null 2>&1; then
  echo "SKIP: tmux not installed"
  exit 0
fi

PLUGIN_DIR=$(cd "$(dirname "$0")/../.." && pwd)
ENGINE="$PLUGIN_DIR/hooks/auto_retry.py"
WORK=$(mktemp -d)
TMUX_BIN=$(command -v tmux)

# PATH shim: every `tmux` call (from the engine too) routes through our
# isolated -L it-test server, so send-keys targets the right pane.
cat > "$WORK/tmux" <<SHIM
#!/usr/bin/env bash
exec "$TMUX_BIN" -L it-test "\$@"
SHIM
chmod +x "$WORK/tmux"
export PATH="$WORK:$PATH"

trap "\"$TMUX_BIN\" -L it-test kill-server 2>/dev/null || true; rm -rf '$WORK'" EXIT

export CLAUDE_AUTO_RETRY_LOG_PATH="$WORK/log.jsonl"
export CLAUDE_AUTO_RETRY_PENDING_DIR="$WORK/pending"
export CLAUDE_AUTO_RETRY_SENTINEL_DIR="$WORK/sentinel"
export CLAUDE_AUTO_RETRY_USER_CONFIG="$WORK/nope.toml"
mkdir -p "$CLAUDE_AUTO_RETRY_SENTINEL_DIR"

# Now `tmux` (via shim) uses -L it-test for the engine too.
tmux new-session -d -s test 'cat'
TMUX_PANE=$(tmux list-panes -t test -F '#{pane_id}')
echo "Test pane: $TMUX_PANE"

# Project config: 1s transient backoff, quiet (no display-message).
mkdir -p "$WORK/.claude"
cat > "$WORK/.claude/claude-auto-retry.toml" <<TOML
[backoff]
rate_limit_transient = 1
quiet = true
TOML

EVT='{"hook_event_name":"StopFailure","error":"rate_limit","error_details":"Server is temporarily limiting","session_id":"itest","cwd":"'$WORK'"}'

echo "Test 1: end-to-end injection"
TMUX_PANE="$TMUX_PANE" bash -c "echo '$EVT' | python3 '$ENGINE' --hook"

# Wait up to 8s for the retry to fire
for _ in 1 2 3 4 5 6 7 8; do
  sleep 1
  if grep -q '"outcome": "fired"' "$CLAUDE_AUTO_RETRY_LOG_PATH" 2>/dev/null; then
    break
  fi
done

if ! grep -q '"outcome": "fired"' "$CLAUDE_AUTO_RETRY_LOG_PATH"; then
  echo "FAIL: no fired event in log"
  cat "$CLAUDE_AUTO_RETRY_LOG_PATH" 2>/dev/null || echo "(no log)"
  exit 1
fi
echo "  PASS"

echo "Test 2: --status renders"
out=$(python3 "$ENGINE" --status)
echo "$out" | grep -q "PENDING" || { echo "FAIL: no PENDING"; exit 1; }
echo "$out" | grep -q "RECENT" || { echo "FAIL: no RECENT"; exit 1; }
echo "  PASS"

echo "Test 3: orphan cleanup"
mkdir -p "$CLAUDE_AUTO_RETRY_PENDING_DIR"
echo '{"pid":99999,"pane_id":"%99","fires_at":"1990-01-01T00:00:00+00:00"}' \
  > "$CLAUDE_AUTO_RETRY_PENDING_DIR/99999.json"
# Trigger another hook to drive the cleanup pass. Sentinel for this pane is
# already present from Test 1, so the second hook will log dedup_bounced
# *after* running _cleanup_stale_pending. That's still what we want — cleanup
# happens before dedup. But we need to clear the sentinel first or the orphan
# check won't run (cleanup happens before dedup; let's just confirm).
TMUX_PANE="$TMUX_PANE" bash -c "echo '$EVT' | python3 '$ENGINE' --hook"
if [ -f "$CLAUDE_AUTO_RETRY_PENDING_DIR/99999.json" ]; then
  echo "FAIL: orphan was not cleaned up"
  ls -la "$CLAUDE_AUTO_RETRY_PENDING_DIR"
  exit 1
fi
echo "  PASS"

echo "All integration tests passed."
```

- [ ] **Step 2: Make executable and run (if tmux available)**

```bash
cd /home/ubuntu/dev/vct-claude-marketplace-public/plugins/claude-auto-retry
chmod +x tests/integration/run.sh
if command -v tmux >/dev/null 2>&1; then
  bash tests/integration/run.sh
else
  echo "tmux missing; skipping integration"
fi
```
Expected: "All integration tests passed." (or "SKIP" if no tmux).

- [ ] **Step 3: Commit**

```bash
git add plugins/claude-auto-retry/tests/integration/run.sh
git -c user.name='vcth4nh' -c user.email='tvu25337@gmail.com' \
  commit -q -m "claude-auto-retry: tmux-gated integration test harness"
```

---

## Task 24: Register plugin in marketplace.json

**Files:**
- Modify: `/home/ubuntu/dev/vct-claude-marketplace-public/.claude-plugin/marketplace.json`

- [ ] **Step 1: Read current state**

```bash
cat /home/ubuntu/dev/vct-claude-marketplace-public/.claude-plugin/marketplace.json
```
Expected: marketplace.json with `"plugins": []`.

- [ ] **Step 2: Replace with registered entry**

Overwrite `/home/ubuntu/dev/vct-claude-marketplace-public/.claude-plugin/marketplace.json` with:
```json
{
  "name": "vct-public",
  "owner": {
    "name": "vcth4nh"
  },
  "metadata": {
    "version": "0.1.0",
    "description": "Public Claude Code plugins by vcth4nh"
  },
  "plugins": [
    {
      "name": "claude-auto-retry",
      "version": "0.1.0",
      "source": "./plugins/claude-auto-retry",
      "description": "Auto-retry Claude Code sessions on transient API errors via StopFailure hook + tmux send-keys. Pure stdlib, no daemon, no wrapper.",
      "author": {
        "name": "vcth4nh"
      },
      "license": "CC-BY-SA-4.0",
      "keywords": ["rate-limit", "retry", "tmux", "hook", "resilience"]
    }
  ]
}
```

- [ ] **Step 3: Validate JSON**

```bash
python3 -c "import json; json.load(open('/home/ubuntu/dev/vct-claude-marketplace-public/.claude-plugin/marketplace.json'))"
```
Expected: no output.

- [ ] **Step 4: Commit**

```bash
cd /home/ubuntu/dev/vct-claude-marketplace-public
git add .claude-plugin/marketplace.json
git -c user.name='vcth4nh' -c user.email='tvu25337@gmail.com' \
  commit -q -m "marketplace: register claude-auto-retry@0.1.0"
```

---

## Task 25: Update marketplace README to list the plugin

**Files:**
- Modify: `/home/ubuntu/dev/vct-claude-marketplace-public/README.md`

- [ ] **Step 1: Replace the "Plugins" section**

In `/home/ubuntu/dev/vct-claude-marketplace-public/README.md`, replace:
```
## Plugins

_(none yet — first plugin in progress)_
```

With:
```
## Plugins

| Plugin | Version | Description |
|---|---|---|
| [`claude-auto-retry`](plugins/claude-auto-retry/) | 0.1.0 | Auto-retry on transient API errors (rate limits, 5xx, overloaded) via StopFailure hook + tmux send-keys. |
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git -c user.name='vcth4nh' -c user.email='tvu25337@gmail.com' \
  commit -q -m "README: list claude-auto-retry"
```

---

## Task 26: Final verification — full unit test run + marketplace consistency

**Files:** none modified

- [ ] **Step 1: Run all unit tests cleanly**

```bash
cd /home/ubuntu/dev/vct-claude-marketplace-public/plugins/claude-auto-retry
python3 -m unittest discover tests -v 2>&1 | tail -20
```
Expected: `OK` summary line with all tests passing (~50+ tests).

- [ ] **Step 2: Run integration tests (if tmux is present)**

```bash
bash tests/integration/run.sh
```
Expected: "All integration tests passed." or "SKIP".

- [ ] **Step 3: Verify plugin manifest + marketplace alignment**

```bash
python3 - <<'PY'
import json, pathlib
root = pathlib.Path("/home/ubuntu/dev/vct-claude-marketplace-public")
mp = json.loads((root / ".claude-plugin/marketplace.json").read_text())
plug = json.loads((root / "plugins/claude-auto-retry/.claude-plugin/plugin.json").read_text())
entry = next(p for p in mp["plugins"] if p["name"] == "claude-auto-retry")
assert entry["version"] == plug["version"], (entry["version"], plug["version"])
assert entry["source"] == "./plugins/claude-auto-retry"
print("OK: marketplace and plugin manifest agree on version", plug["version"])
PY
```
Expected: "OK: marketplace and plugin manifest agree on version 0.1.0".

- [ ] **Step 4: Confirm hooks.json matches what hook spec expects**

```bash
python3 - <<'PY'
import json
h = json.load(open("/home/ubuntu/dev/vct-claude-marketplace-public/plugins/claude-auto-retry/hooks/hooks.json"))
sf = h["hooks"]["StopFailure"][0]
assert sf["matcher"] == "rate_limit|server_error|unknown"
assert "auto_retry.py" in sf["hooks"][0]["command"]
assert "${CLAUDE_PLUGIN_ROOT}" in sf["hooks"][0]["command"]
print("OK: hooks.json registers StopFailure correctly")
PY
```
Expected: "OK: hooks.json registers StopFailure correctly".

- [ ] **Step 5: Git log review**

```bash
cd /home/ubuntu/dev/vct-claude-marketplace-public
git log --oneline | head -30
```
Expected: Linear history of ~26 commits, all prefixed with `claude-auto-retry:` or `marketplace:` / `README:`.

---

## Task 27: Retire the prototype

**Files:**
- Delete: `/home/ubuntu/dev/claude-auto-retry/` (whole directory)

- [ ] **Step 1: Confirm contents of the prototype**

```bash
ls -la /home/ubuntu/dev/claude-auto-retry/
```
Expected: `hook.py`, `settings.example.json`.

- [ ] **Step 2: Confirm the new plugin works**

(Already verified in Task 26.)

- [ ] **Step 3: Remove prototype directory**

```bash
rm -rf /home/ubuntu/dev/claude-auto-retry
```

- [ ] **Step 4: Verify**

```bash
ls /home/ubuntu/dev/ | grep claude-auto-retry || echo "gone"
```
Expected: "gone".

(This step is outside any git repo so there's nothing to commit.)

---

## Spec coverage check

Mapping spec sections to tasks:

| Spec section | Tasks |
|---|---|
| Architecture: one engine, four modes | T2, T15, T16, T17, T18 |
| State layout (split) | T11, T12, T13 (paths via T3 helpers) |
| Config resolution + TOML schema | T4, T5, T6, T18 |
| Components: hooks.json | T19 |
| Components: auto_retry.py | T2–T18 |
| Components: about skill | T21 |
| Components: status skill | T20 |
| Components: examples/config.toml | T18 |
| Data flow: happy path | T15, T16 (covered by happy-path test) |
| Data flow: hard-quota branch | T8, T9 |
| Data flow: skip branches | T15 (all six tested) |
| Data flow: status read path | T17 |
| Error handling: try/except envelope | T15 (test_malformed_stdin_does_not_crash) |
| Error handling: timer try/finally | T16 (test_tmux_failure_logs_error_and_still_cleans_up) |
| Error handling: config forgiveness | T6 (test_malformed_toml_falls_back_silently) |
| Error handling: stale cleanup | T13 |
| Error handling: log rotation | T13 |
| Error handling: concurrency (O_EXCL) | T10 |
| Testing: unit | T2–T18 |
| Testing: integration | T23 |
| Testing: manual smoke | README (T22) |
| Marketplace registration | T24, T25 |
| Final verification | T26 |
| Prototype retirement | T27 |

No gaps.
