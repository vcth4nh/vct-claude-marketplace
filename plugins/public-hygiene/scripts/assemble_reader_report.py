#!/usr/bin/env python3
"""Validate a reading stage or assemble checkpoints without rewriting their bytes.

This checks report structure, not semantic correctness, reading chronology, or
whether an input was edited before assembly. Hashes identify the bytes used.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat


MARKER = re.compile(r"^[ \t]*(FIRST READ|STAGE|VERDICT)\b")
HEADER = re.compile(r"FIRST READ ([1-9][0-9]*)/([1-9][0-9]*): (\S.*)")
GAPS = re.compile(r"VERDICT: NEEDS CONTEXT \(([1-9][0-9]*) (gap|gaps)\)")


def read_input(path, seen):
    """Read a regular, non-symlink file once; reject path and inode aliases."""
    path = Path(path)
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode):
        raise ValueError(f"input must be a regular non-symlink file: {path}")
    identity = (before.st_dev, before.st_ino)
    if identity in seen:
        raise ValueError(f"input paths must identify distinct files: {path}")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    with os.fdopen(os.open(path, flags), "rb") as stream:
        opened = os.fstat(stream.fileno())
        if (not stat.S_ISREG(opened.st_mode)
                or (opened.st_dev, opened.st_ino) != identity):
            raise ValueError(f"input changed while being opened: {path}")
        data = stream.read()
    try:
        data.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError(f"input must be valid UTF-8: {path}") from error
    seen.add(identity)
    lines = data.splitlines(keepends=True)
    text_lines = [line.rstrip(b"\r\n").decode("utf-8") for line in lines]
    record = {"path": str(path.resolve()), "sha256": hashlib.sha256(data).hexdigest()}
    return data, lines, text_lines, record


def markers(lines):
    return [match.group(1) for line in lines if (match := MARKER.match(line))]


def validate_summary(lines):
    if not lines or not lines[0].startswith("AUDIENCE:"):
        raise ValueError("summary must start with an AUDIENCE: line")
    if markers(lines) != ["VERDICT"]:
        raise ValueError("summary requires one VERDICT and no FIRST READ or STAGE sections")
    if lines[-1] in ("VERDICT: PASS", "VERDICT: INCOMPLETE"):
        return
    match = GAPS.fullmatch(lines[-1])
    if match and (match[2] == "gap") == (int(match[1]) == 1):
        return
    raise ValueError("summary must end with VERDICT: PASS, NEEDS CONTEXT (N gaps), "
                     "or INCOMPLETE; use 1 gap for a single gap")


def validate_checkpoint(lines, index, total):
    if not 1 <= index <= total:
        raise ValueError("stage and total must satisfy 1 <= stage <= total")
    if not lines or not (match := HEADER.fullmatch(lines[0])):
        raise ValueError("checkpoint must start with FIRST READ i/n: <location>")
    if (int(match[1]), int(match[2])) != (index, total):
        raise ValueError(f"expected checkpoint {index}/{total}, got {match[1]}/{match[2]}")
    if markers(lines) != ["FIRST READ", "STAGE"]:
        raise ValueError("checkpoint requires one FIRST READ, one STAGE, and no VERDICT")
    if lines[-1] != "STAGE: COMPLETE":
        raise ValueError("checkpoint must end with STAGE: COMPLETE")


def validate_checkpoint_file(path, index, total):
    """Validate one saved stage without changing it or creating any output file."""
    _, _, lines, record = read_input(path, set())
    validate_checkpoint(lines, index, total)
    return {**record, "stage": index, "total": total, "status": "COMPLETE"}


def assemble_report(output, summary, checkpoints):
    """Validate all inputs, exclusively create the output, and return byte hashes."""
    output = Path(output)
    try:
        output.lstat()
    except FileNotFoundError:
        pass
    else:
        raise ValueError("output already exists (including input aliases and symlinks)")
    checkpoints = list(checkpoints)
    if not checkpoints:
        raise ValueError("at least one checkpoint is required")

    seen = set()
    _, summary_lines, summary_text, summary_record = read_input(summary, seen)
    validate_summary(summary_text)
    inputs = [{"role": "summary", **summary_record}]
    parts = [summary_lines[0]]
    for index, path in enumerate(checkpoints, 1):
        data, _, lines, record = read_input(path, seen)
        validate_checkpoint(lines, index, len(checkpoints))
        inputs.append({"role": "checkpoint", "index": index, **record})
        parts.append(data)
        # A missing final line terminator needs a separator before the next input.
        # Existing LF, CRLF, and CR terminators are left exactly as supplied.
        if not data.endswith((b"\n", b"\r")):
            parts.append(b"\n")
    parts.extend(summary_lines[1:])
    content = b"".join(parts)
    result = {"output": {"path": str(output.resolve()),
                         "sha256": hashlib.sha256(content).hexdigest()},
              "inputs": inputs}

    created_identity = None
    try:
        # Exclusive creation also rejects an output that appeared after validation.
        with output.open("xb") as stream:
            created = os.fstat(stream.fileno())
            created_identity = (created.st_dev, created.st_ino)
            stream.write(content)
    except Exception:
        # A failed write must not leave a partial report or remove someone else's file.
        if created_identity is not None:
            try:
                current = output.lstat()
                if (current.st_dev, current.st_ino) == created_identity:
                    output.unlink()
            except FileNotFoundError:
                pass
        raise
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", nargs="?", type=Path,
                        help="new assembled report (assembly mode only)")
    parser.add_argument("--summary", type=Path)
    parser.add_argument("--checkpoints", nargs="+", type=Path,
                        help="complete checkpoint files in FIRST READ order")
    parser.add_argument("--validate-checkpoint", type=Path,
                        help="validate one saved checkpoint before advancing; writes no files")
    parser.add_argument("--stage", type=int, help="expected 1-based stage number")
    parser.add_argument("--total", type=int, help="expected total number of stages")
    args = parser.parse_args()
    try:
        if args.validate_checkpoint is not None:
            if any(value is not None for value in (args.output, args.summary, args.checkpoints)):
                parser.error("--validate-checkpoint cannot be combined with assembly arguments")
            if args.stage is None or args.total is None:
                parser.error("--validate-checkpoint requires --stage and --total")
            result = validate_checkpoint_file(args.validate_checkpoint, args.stage, args.total)
        else:
            if args.stage is not None or args.total is not None:
                parser.error("--stage and --total require --validate-checkpoint")
            if any(value is None for value in (args.output, args.summary, args.checkpoints)):
                parser.error("assembly requires output, --summary, and --checkpoints")
            result = assemble_report(args.output, args.summary, args.checkpoints)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
