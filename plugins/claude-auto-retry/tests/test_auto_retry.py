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


class TestPathHelpers(unittest.TestCase):
    def test_log_path_default(self):
        with mock.patch.dict("os.environ", {}, clear=False):
            __import__("os").environ.pop("CLAUDE_AUTO_RETRY_LOG_PATH", None)
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


if __name__ == "__main__":
    unittest.main()
