from __future__ import annotations
import copy
import datetime
import io
import json
import pathlib
import sys
import tempfile
import unittest
from unittest import mock
from zoneinfo import ZoneInfo

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


class TestLoadConfig(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.cwd = pathlib.Path(self.tmp.name)
        self.env_patch = mock.patch.dict(
            "os.environ",
            {"CLAUDE_AUTO_RETRY_USER_CONFIG": str(self.cwd / "nonexistent.toml")},
        )
        self.env_patch.start()
        self.addCleanup(self.env_patch.stop)

    def test_defaults_when_no_files(self):
        cfg = auto_retry._load_config(str(self.cwd))
        self.assertEqual(cfg, auto_retry.DEFAULT_CONFIG)

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


class TestParseResetTime(unittest.TestCase):
    def test_3am_today_if_in_future(self):
        now = datetime.datetime(2026, 5, 23, 2, 0, tzinfo=ZoneInfo("Asia/Bangkok"))
        text = "You've hit your limit · resets 3am (Asia/Bangkok)"
        delta = auto_retry._parse_reset_time(text, now=now)
        self.assertEqual(delta, 3600)

    def test_3am_tomorrow_if_already_past(self):
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
        import time as _t
        sentinel = pathlib.Path(self.tmp.name) / "claude-retry-7"
        sentinel.touch()
        old = _t.time() - 60
        __import__("os").utime(sentinel, (old, old))
        self.assertTrue(auto_retry._dedup_acquire("%7", 30))

    def test_different_panes_dont_collide(self):
        self.assertTrue(auto_retry._dedup_acquire("%7", 30))
        self.assertTrue(auto_retry._dedup_acquire("%9", 30))


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
        import json as _j
        rec = _j.loads(lines[0])
        self.assertEqual(rec["outcome"], "fired")
        self.assertEqual(rec["error"], "rate_limit")
        self.assertIn("ts", rec)

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
        auto_retry._delete_pending(12345)

    def test_list_pending(self):
        auto_retry._write_pending({"pid": 100, "pane_id": "%7", "fires_at": "x"})
        auto_retry._write_pending({"pid": 200, "pane_id": "%9", "fires_at": "y"})
        items = sorted(auto_retry._list_pending(), key=lambda e: e["pid"])
        self.assertEqual([i["pid"] for i in items], [100, 200])


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
                               return_value=mock.Mock(returncode=1, stderr="tmux: bad pane identifier: %7")):
            auto_retry._timer("%7", 0, "rate_limit")
        rec = json.loads(self.log.read_text().splitlines()[-1])
        self.assertEqual(rec["outcome"], "error")
        self.assertEqual(rec["reason"], "tmux_send_failed")
        self.assertEqual(auto_retry._list_pending(), [])


if __name__ == "__main__":
    unittest.main()
