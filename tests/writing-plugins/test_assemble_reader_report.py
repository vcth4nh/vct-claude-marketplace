import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


SCRIPT = (Path(__file__).resolve().parents[2] / "plugins/public-hygiene/scripts"
          / "assemble_reader_report.py")
SPEC = importlib.util.spec_from_file_location("assemble_reader_report", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class AssembleReaderReportTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.summary = self.root / "summary.txt"
        self.checkpoints = [self.root / "first.txt", self.root / "second.txt"]
        self.output = self.root / "report.txt"
        self.summary.write_bytes(b"AUDIENCE: New readers\nOverall assessment.\nVERDICT: PASS\n")
        for i, path in enumerate(self.checkpoints, 1):
            path.write_bytes(f"FIRST READ {i}/2: section {i}\nObservation {i}.\nSTAGE: COMPLETE\n".encode())

    def cli(self, output=None, summary=None, checkpoints=None):
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(output or self.output),
             "--summary", str(summary or self.summary), "--checkpoints",
             *map(str, self.checkpoints if checkpoints is None else checkpoints)],
            capture_output=True, text=True, timeout=10)

    def assert_cli_error(self, **kwargs):
        result = self.cli(**kwargs)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertIn("error:", result.stderr)
        return result

    def test_cli_preserves_original_bytes_and_reports_ordered_hashes(self):
        for ending in (b"\n", b"\r\n", b"\r"):
            for terminal in (True, False):
                with self.subTest(ending=ending, terminal=terminal):
                    audience = "AUDIENCE: Café maintainers".encode() + ending
                    rest = ending.join([b"Assessment.", b"VERDICT: NEEDS CONTEXT (1 gap)"])
                    if terminal:
                        rest += ending
                    summary = audience + rest
                    first = ending.join([b"FIRST READ 1/2: intro", "Question about naïve input?".encode(),
                                         b"STAGE: COMPLETE"])
                    second = b"FIRST READ 2/2: conclusion\r\nLater answer.\r\nSTAGE: COMPLETE\r\n"
                    if terminal:
                        first += ending
                    self.summary.write_bytes(summary)
                    self.checkpoints[0].write_bytes(first)
                    self.checkpoints[1].write_bytes(second)
                    result = self.cli()
                    self.assertEqual(result.returncode, 0, result.stderr)
                    expected = audience + first + (b"" if terminal else b"\n") + second + rest
                    self.assertEqual(self.output.read_bytes(), expected)
                    manifest = json.loads(result.stdout)
                    self.assertEqual(manifest["output"], {
                        "path": str(self.output), "sha256": hashlib.sha256(expected).hexdigest()})
                    self.assertEqual([entry["role"] for entry in manifest["inputs"]],
                                     ["summary", "checkpoint", "checkpoint"])
                    self.assertEqual([entry["path"] for entry in manifest["inputs"]],
                                     list(map(str, [self.summary, *self.checkpoints])))
                    self.assertEqual([entry["sha256"] for entry in manifest["inputs"]],
                                     [hashlib.sha256(data).hexdigest() for data in (summary, first, second)])
                    for path, original in zip([self.summary, *self.checkpoints], [summary, first, second]):
                        self.assertEqual(path.read_bytes(), original)
                    self.output.unlink()

    def test_supported_verdicts(self):
        for verdict in ("PASS", "INCOMPLETE", "NEEDS CONTEXT (1 gap)",
                        "NEEDS CONTEXT (2 gaps)", "NEEDS CONTEXT (12 gaps)"):
            with self.subTest(verdict=verdict):
                self.summary.write_text(f"AUDIENCE: Readers\nVERDICT: {verdict}", encoding="utf-8")
                result = self.cli()
                self.assertEqual(result.returncode, 0, result.stderr)
                self.output.unlink()

    def test_invalid_checkpoint_structure_leaves_no_output(self):
        cases = [b"", b"\xff", b"\xef\xbb\xbfFIRST READ 1/2: intro\nSTAGE: COMPLETE",
                 b"FIRST READ 1/2: \nSTAGE: COMPLETE", b"FIRST READ 1/2:  \nSTAGE: COMPLETE",
                 b"FIRST READ 0/2: intro\nSTAGE: COMPLETE", b"FIRST READ 01/2: intro\nSTAGE: COMPLETE",
                 b"FIRST READ 1/3: intro\nSTAGE: COMPLETE", b"FIRST READ 2/2: intro\nSTAGE: COMPLETE",
                 b"FIRST READ 1/2: intro\nSTAGE: INCOMPLETE", b"FIRST READ 1/2: intro\nSTAGE: COMPLETE\n\n",
                 b"FIRST READ 1/2: intro\nSTAGE: COMPLETE\nTrailing text",
                 b"FIRST READ 1/2: intro\n FIRST READ 1/2: duplicate\nSTAGE: COMPLETE",
                 b"FIRST READ 1/2: intro\nSTAGE: COMPLETE\nSTAGE: COMPLETE",
                 b"FIRST READ 1/2: intro\nVERDICT: PASS\nSTAGE: COMPLETE",
                 b"FIRST READ 1/2: intro\n\tVERDICT: PASS\nSTAGE: COMPLETE"]
        for data in cases:
            with self.subTest(data=data):
                self.checkpoints[0].write_bytes(data)
                self.assert_cli_error()
                self.assertFalse(self.output.exists())
                self.assertEqual(self.checkpoints[0].read_bytes(), data)

    def test_invalid_summary_structure_leaves_no_output(self):
        cases = [b"", b"\xff", b"Readers\nVERDICT: PASS", b" AUDIENCE: Readers\nVERDICT: PASS",
                 b"AUDIENCE: Readers\nNo verdict", b"AUDIENCE: Readers\nVERDICT: PASS\nVERDICT: PASS",
                 b"AUDIENCE: Readers\nFIRST READ 1/1: intro\nVERDICT: PASS",
                 b"AUDIENCE: Readers\n STAGE: COMPLETE\nVERDICT: PASS",
                 b"AUDIENCE: Readers\nVERDICT: NEEDS CONTEXT (0 gaps)",
                 b"AUDIENCE: Readers\nVERDICT: NEEDS CONTEXT (1 gaps)",
                 b"AUDIENCE: Readers\nVERDICT: NEEDS CONTEXT (2 gap)",
                 b"AUDIENCE: Readers\nVERDICT: NEEDS CONTEXT (01 gap)",
                 b"AUDIENCE: Readers\nVERDICT: PASS \n", b"AUDIENCE: Readers\nVERDICT: PASS\n\n",
                 b"AUDIENCE: Readers\nVERDICT: PASS\nTrailing text"]
        for data in cases:
            with self.subTest(data=data):
                self.summary.write_bytes(data)
                self.assert_cli_error()
                self.assertFalse(self.output.exists())
                self.assertEqual(self.summary.read_bytes(), data)

    def test_missing_reordered_and_duplicate_checkpoints(self):
        hardlink = self.root / "same-inode.txt"
        os.link(self.checkpoints[0], hardlink)
        for paths in ([], self.checkpoints[:1], list(reversed(self.checkpoints)),
                      [self.checkpoints[0], self.checkpoints[0]],
                      [self.checkpoints[0], hardlink], [self.checkpoints[0], self.root / "missing"]):
            with self.subTest(paths=paths):
                self.assert_cli_error(checkpoints=paths)
                self.assertFalse(self.output.exists())

    def test_existing_outputs_and_input_aliases_are_unchanged(self):
        self.output.write_bytes(b"keep existing output")
        hardlink = self.root / "hardlink.txt"
        os.link(self.summary, hardlink)
        symlink = self.root / "symlink.txt"
        symlink.symlink_to(self.checkpoints[0])
        dangling = self.root / "dangling.txt"
        dangling.symlink_to(self.root / "missing")
        originals = {p: p.read_bytes() for p in [self.output, self.summary, *self.checkpoints, hardlink]}
        for output in (self.output, self.summary, *self.checkpoints, hardlink, symlink, dangling, self.root):
            with self.subTest(output=output):
                self.assert_cli_error(output=output)
                for path, data in originals.items():
                    self.assertEqual(path.read_bytes(), data)
                self.assertTrue(symlink.is_symlink())
                self.assertTrue(dangling.is_symlink())

    def test_nonregular_and_symlink_inputs_are_rejected_without_hanging(self):
        symlink = self.root / "linked-summary.txt"
        symlink.symlink_to(self.summary)
        dangling = self.root / "dangling-input.txt"
        dangling.symlink_to(self.root / "missing")
        paths = [self.root, symlink, dangling, self.root / "missing"]
        if hasattr(os, "mkfifo"):
            fifo = self.root / "pipe"
            os.mkfifo(fifo)
            paths.append(fifo)
        for path in paths:
            with self.subTest(path=path):
                self.assert_cli_error(summary=path)
                self.assert_cli_error(checkpoints=[path, self.checkpoints[1]])
                self.assertFalse(self.output.exists())

    def test_exclusive_create_preserves_output_created_after_validation(self):
        original_open = Path.open

        def concurrent_create(path, mode="r", *args, **kwargs):
            if path == self.output and mode == "xb":
                with original_open(path, "wb") as stream:
                    stream.write(b"concurrent writer")
            return original_open(path, mode, *args, **kwargs)

        with mock.patch.object(Path, "open", concurrent_create):
            with self.assertRaises(FileExistsError):
                MODULE.assemble_report(self.output, self.summary, self.checkpoints)
        self.assertEqual(self.output.read_bytes(), b"concurrent writer")

    def test_failed_write_removes_partial_output(self):
        original_open = Path.open

        class FailingWriter:
            def __init__(self, stream):
                self.stream = stream

            def __enter__(self):
                return self

            def __exit__(self, *args):
                self.stream.close()

            def fileno(self):
                return self.stream.fileno()

            def write(self, content):
                self.stream.write(content[:10])
                self.stream.flush()
                raise OSError("simulated full disk")

        def fail_write(path, mode="r", *args, **kwargs):
            stream = original_open(path, mode, *args, **kwargs)
            return FailingWriter(stream) if path == self.output and mode == "xb" else stream

        with mock.patch.object(Path, "open", fail_write):
            with self.assertRaisesRegex(OSError, "simulated full disk"):
                MODULE.assemble_report(self.output, self.summary, self.checkpoints)
        self.assertFalse(self.output.exists())

    def test_missing_output_parent_is_cli_error_without_partial_output(self):
        output = self.root / "missing-parent" / "report.txt"
        self.assert_cli_error(output=output)
        self.assertFalse(output.parent.exists())


if __name__ == "__main__":
    unittest.main()
