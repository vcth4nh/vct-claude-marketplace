#!/usr/bin/env python3
"""Copy caller-selected line ranges into byte-identical reader chunks."""

import argparse
import json
from pathlib import Path
import shutil


def prepare_chunks(source, destination, starts, forwards=()):
    """Create a new directory of chunks and return its relative-path manifest."""
    source, destination = Path(source), Path(destination)
    if destination.exists() or destination.is_symlink():
        raise ValueError("destination already exists")
    if not destination.parent.is_dir():
        raise ValueError("destination parent must be an existing directory")

    data = source.read_bytes()
    if not data:
        raise ValueError("source must not be empty")
    try:
        data.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError("source must be valid UTF-8") from error
    lines = data.splitlines(keepends=True)
    if not starts or starts[0] != 1:
        raise ValueError("starts must begin with line 1")
    if any(a >= b for a, b in zip(starts, starts[1:])):
        raise ValueError("starts must be strictly increasing")
    if any(start < 1 or start > len(lines) for start in starts):
        raise ValueError("chunk start is outside the source line range")
    for chunk, start, end in forwards:
        if not 1 <= chunk <= len(starts):
            raise ValueError("forward excerpt references an invalid chunk")
        if not 1 <= start <= end <= len(lines):
            raise ValueError("forward excerpt is outside the source line range")

    chunks, outputs = [], {}
    ends = list(starts[1:]) + [len(lines) + 1]
    for index, (start, stop) in enumerate(zip(starts, ends), 1):
        name = f"chunk-{index:03d}.txt"
        outputs[name] = b"".join(lines[start - 1:stop - 1])
        chunks.append({"path": name, "start_line": start, "end_line": stop - 1,
                       "forward_excerpts": []})
    for index, (chunk, start, end) in enumerate(forwards, 1):
        name = f"excerpt-{index:03d}.txt"
        outputs[name] = b"".join(lines[start - 1:end])
        chunks[chunk - 1]["forward_excerpts"].append(
            {"path": name, "start_line": start, "end_line": end})
    manifest = {"chunks": chunks}

    # mkdir is exclusive: an existing destination is never reused or modified.
    destination.mkdir()
    try:
        for name, content in outputs.items():
            (destination / name).write_bytes(content)
        copied = b"".join((destination / chunk["path"]).read_bytes()
                          for chunk in chunks)
        if copied != data:
            raise OSError("written chunks do not reconstruct the source bytes")
        (destination / "manifest.json").write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    except Exception:
        shutil.rmtree(destination)
        raise
    return manifest


def forward_range(value):
    try:
        parts = tuple(int(part) for part in value.split(":"))
    except ValueError as error:
        raise argparse.ArgumentTypeError("expected CHUNK:START:END integers") from error
    if len(parts) != 3:
        raise argparse.ArgumentTypeError("expected CHUNK:START:END integers")
    return parts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--starts", required=True, nargs="+", type=int,
                        help="strictly increasing 1-based chunk starts, beginning with 1")
    parser.add_argument("--forward", action="append", type=forward_range, default=[],
                        metavar="CHUNK:START:END",
                        help="map an inclusive source-line excerpt to a chunk; repeatable")
    args = parser.parse_args()
    try:
        manifest = prepare_chunks(args.source, args.destination, args.starts, args.forward)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
