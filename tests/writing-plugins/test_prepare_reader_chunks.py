import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = (Path(__file__).resolve().parents[2] / "plugins/public-hygiene/scripts"
          / "prepare_reader_chunks.py")
SPEC = importlib.util.spec_from_file_location("prepare_reader_chunks", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class PrepareReaderChunksTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / "private-source.md"
        self.destination = self.root / "reader"

    def test_line_endings_and_missing_terminal_newline(self):
        for data in (b"one\ntwo\nthree\n", b"one\r\ntwo\r\nthree\r\n",
                     b"one\ntwo\nthree", b"one\r\ntwo\r\nthree"):
            with self.subTest(data=data):
                self.source.write_bytes(data)
                destination = self.root / ("reader-" + str(len(list(self.root.iterdir()))))
                manifest = MODULE.prepare_chunks(self.source, destination, [1, 3])
                reconstructed = b"".join((destination / c["path"]).read_bytes()
                                          for c in manifest["chunks"])
                self.assertEqual(reconstructed, data)
                self.assertEqual(self.source.read_bytes(), data)
                self.assertEqual([(c["start_line"], c["end_line"])
                                  for c in manifest["chunks"]], [(1, 2), (3, 3)])

    def test_safe_boundary_preserves_multiline_block(self):
        data = "Introduction\n\n```python\nprint('café')\nprint(2)\n```\n\nAfter\n".encode()
        self.source.write_bytes(data)
        manifest = MODULE.prepare_chunks(self.source, self.destination, [1, 8])
        first = (self.destination / manifest["chunks"][0]["path"]).read_bytes()
        self.assertEqual(first, data[:data.index(b"After")])
        self.assertIn("```python\nprint('café')\nprint(2)\n```".encode(), first)

    def test_forward_excerpt_and_manifest_privacy(self):
        data = b"See definition below.\r\n\r\nDefinition\r\nExact wording."
        self.source.write_bytes(data)
        manifest = MODULE.prepare_chunks(self.source, self.destination, [1, 3], [(1, 3, 4)])
        excerpt = manifest["chunks"][0]["forward_excerpts"][0]
        self.assertEqual((self.destination / excerpt["path"]).read_bytes(),
                         b"Definition\r\nExact wording.")
        self.assertEqual((excerpt["start_line"], excerpt["end_line"]), (3, 4))
        self.assertEqual(manifest["chunks"][1]["forward_excerpts"], [])
        self.assertEqual(b"".join((self.destination / c["path"]).read_bytes()
                                  for c in manifest["chunks"]), data)
        serialized = (self.destination / "manifest.json").read_text()
        self.assertEqual(json.loads(serialized), manifest)
        self.assertNotIn(str(self.source), serialized)
        self.assertNotIn(self.source.name, serialized)
        self.assertNotIn("Definition", serialized)

    def test_invalid_ranges_leave_no_output(self):
        self.source.write_bytes(b"one\ntwo\nthree")
        invalid = [([], []), ([2], []), ([1, 1], []), ([1, 0], []),
                   ([1, 4], []), ([1], [(0, 1, 1)]), ([1], [(2, 1, 1)]),
                   ([1], [(1, 0, 1)]), ([1], [(1, 3, 2)]), ([1], [(1, 1, 4)])]
        for starts, forwards in invalid:
            with self.subTest(starts=starts, forwards=forwards):
                with self.assertRaises(ValueError):
                    MODULE.prepare_chunks(self.source, self.destination, starts, forwards)
                self.assertFalse(self.destination.exists())
                self.assertEqual(self.source.read_bytes(), b"one\ntwo\nthree")

    def test_empty_and_invalid_utf8_leave_no_output(self):
        for data in (b"", b"valid\n\xff"):
            with self.subTest(data=data):
                self.source.write_bytes(data)
                with self.assertRaises(ValueError):
                    MODULE.prepare_chunks(self.source, self.destination, [1])
                self.assertFalse(self.destination.exists())
                self.assertEqual(self.source.read_bytes(), data)

    def test_existing_destination_and_source_cannot_be_overwritten(self):
        self.source.write_bytes(b"source")
        self.destination.mkdir()
        sentinel = self.destination / "keep.txt"
        sentinel.write_bytes(b"keep")
        dangling = self.root / "dangling"
        dangling.symlink_to(self.root / "missing")
        for destination in (self.destination, self.source, dangling):
            with self.subTest(destination=destination):
                with self.assertRaises(ValueError):
                    MODULE.prepare_chunks(self.source, destination, [1])
                self.assertEqual(self.source.read_bytes(), b"source")
                self.assertEqual(sentinel.read_bytes(), b"keep")
                self.assertEqual(list(self.destination.iterdir()), [sentinel])
                self.assertTrue(dangling.is_symlink())

    def test_cli_manifest_and_invalid_forward_syntax(self):
        self.source.write_bytes(b"first\nsecond\nthird")
        command = [sys.executable, str(SCRIPT), str(self.source), str(self.destination),
                   "--starts", "1", "3", "--forward", "1:3:3"]
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout),
                         json.loads((self.destination / "manifest.json").read_text()))
        invalid_destination = self.root / "invalid"
        command[3] = str(invalid_destination)
        command[-1] = "1:three:3"
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(invalid_destination.exists())
        self.assertEqual(self.source.read_bytes(), b"first\nsecond\nthird")


if __name__ == "__main__":
    unittest.main()
