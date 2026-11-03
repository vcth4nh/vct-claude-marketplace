#!/usr/bin/env python3
"""Fetch the public held-out documents; keep their full text outside this repo.

Uses only Python's standard library. The manifest pins the README revision,
arXiv version, and prepared text hashes. Website HTML can change without its
article changing; validation uses the extracted article, not page chrome.
This script does not create or read evaluator rubrics.
"""

import argparse
import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen


VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}


class Element(HTMLParser):
    """Extract one element with a specified class, preserving its inner HTML."""

    def __init__(self, class_name):
        super().__init__(convert_charrefs=False)
        self.class_name, self.depth, self.found, self.parts = class_name, 0, False, []

    def handle_starttag(self, tag, attrs):
        classes = dict(attrs).get("class", "").split()
        if not self.found and self.class_name in classes:
            self.found, self.depth = True, 1
        elif self.depth:
            self.parts.append(self.get_starttag_text())
            if tag not in VOID:
                self.depth += 1

    def handle_startendtag(self, tag, attrs):
        if self.depth:
            self.parts.append(self.get_starttag_text())

    def handle_endtag(self, tag):
        if self.depth:
            self.depth -= 1
            if self.depth:
                self.parts.append(f"</{tag}>")

    def handle_data(self, text):
        if self.depth:
            self.parts.append(text)

    def handle_entityref(self, name):
        self.handle_data(f"&{name};")

    def handle_charref(self, name):
        self.handle_data(f"&#{name};")


def element(html, class_name):
    parser = Element(class_name)
    parser.feed(html)
    if not parser.found or parser.depth:
        raise ValueError(f"Missing or incomplete element: {class_name}")
    return "".join(parser.parts)


class Markdown(HTMLParser):
    """Render only the simple article markup used in these pinned sources."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts, self.images, self.links = [], [], []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in {"p", "figure", "figcaption", "ul"}:
            self.parts.append("\n\n")
        elif re.fullmatch(r"h[1-6]", tag):
            self.parts.append("\n\n" + "#" * int(tag[1]) + " ")
        elif tag == "li":
            self.parts.append("\n- ")
        elif tag in {"strong", "b"}:
            self.parts.append("**")
        elif tag in {"em", "i"}:
            self.parts.append("*")
        elif tag == "code":
            self.parts.append("`")
        elif tag == "a":
            self.parts.append("[")
            self.links.append(attrs["href"])
        elif tag == "img":
            url = attrs["src"]
            name = f"assets/spike-figure-{len(self.images) + 1}.png"
            self.images.append({"url": url, "path": name})
            self.parts.append(f"\n\n![{attrs.get('alt', '')}]({name})\n\n")
        elif tag == "br":
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in {"p", "figure", "figcaption", "ul"} or re.fullmatch(r"h[1-6]", tag):
            self.parts.append("\n\n")
        elif tag in {"strong", "b"}:
            self.parts.append("**")
        elif tag in {"em", "i"}:
            self.parts.append("*")
        elif tag == "code":
            self.parts.append("`")
        elif tag == "a":
            self.parts.append(f"]({self.links.pop()})")

    def handle_data(self, text):
        if text.strip():
            self.parts.append(re.sub(r"\s+", " ", text))
        elif "\n" not in text:
            self.parts.append(" ")

    def text(self):
        text = re.sub(r"[ \t]+\n", "\n", "".join(self.parts))
        return re.sub(r"\n{3,}", "\n\n", text).strip()


def render(html):
    parser = Markdown()
    parser.feed(html)
    return parser.text(), parser.images


def prepare(document, raw):
    kind = document["format"]
    if kind == "markdown":
        return raw, []
    html = raw.decode("utf-8")
    if kind == "spike_article":
        title, _ = render(element(html, "spike-article__title"))
        author, _ = render(element(html, "spike-author__name"))
        date, _ = render(element(html, "spike-author__date"))
        body, images = render(element(html, "spike-article__content"))
        return f"# {title}\n\n{author} — {date}\n\n{body}\n".encode(), images
    if kind == "arxiv_abstract":
        title, _ = render(element(html, "title"))
        authors, _ = render(element(html, "authors"))
        abstract, _ = render(element(html, "abstract"))
        title = title.removeprefix("Title:")
        authors = "Authors: " + authors.removeprefix("Authors:").strip()
        abstract = abstract.removeprefix("Abstract:")
        return f"# {title}\n\n{authors}\n\n## Abstract\n\n{abstract}\n".encode(), []
    raise ValueError(f"Unknown source format: {kind}")


def fetch(url):
    req = Request(url, headers={"User-Agent": "writing-plugin-heldout-evaluation/1.0"})
    with urlopen(req, timeout=60) as response:
        return response.read()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("/tmp/writing-next-heldout"))
    parser.add_argument("--reuse-downloads", action="store_true", help="Use existing raw snapshots when present")
    args = parser.parse_args()
    manifest = json.loads(Path(__file__).with_name("sources.json").read_text())
    output = args.output.resolve()
    repo = Path(__file__).resolve().parents[3]
    if output == repo or repo in output.parents:
        parser.error("Full source text must remain outside the repository")
    output.mkdir(parents=True, exist_ok=True)
    for document in manifest["documents"]:
        snapshot = output / document["snapshot"]["path"]
        raw = snapshot.read_bytes() if args.reuse_downloads and snapshot.exists() else fetch(document["pinned_url"])
        prepared, images = prepare(document, raw)
        digest = hashlib.sha256(prepared).hexdigest()
        if digest != document["input"]["sha256"]:
            raise ValueError(f"Prepared content changed for {document['id']}: {digest}")
        if len(prepared.decode().split()) > 1500:
            raise ValueError(f"Word limit exceeded: {document['id']}")
        snapshot.write_bytes(raw)
        (output / document["input"]["path"]).write_bytes(prepared)
        chunks = document.get("sequential_chunks", [])
        lines = prepared.splitlines(keepends=True)
        combined = []
        for chunk in chunks:
            content = b"".join(lines[chunk["start_line"] - 1:chunk["end_line"]])
            if hashlib.sha256(content).hexdigest() != chunk["sha256"]:
                raise ValueError(f"Sequential chunk changed: {chunk['path']}")
            combined.append(content)
            path = output / chunk["path"]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        if chunks and b"".join(combined) != prepared:
            raise ValueError(f"Chunks do not cover the original: {document['id']}")
        for image in images:
            if not any(asset["path"] == image["path"] and asset["url"] == image["url"]
                       for asset in document["assets"]):
                raise ValueError(f"Article image reference changed: {image['url']}")
        # Markdown can link live external images without rewriting their URLs.
        # Fetch those declared companions as well as images extracted from HTML.
        for asset in document["assets"]:
            path = output / asset["path"]
            content = path.read_bytes() if args.reuse_downloads and path.exists() else fetch(asset["url"])
            if hashlib.sha256(content).hexdigest() != asset["sha256"]:
                raise ValueError(f"Image changed: {asset['url']}")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        print(f"{document['id']}: {len(prepared.decode().split())} words, SHA-256 {digest}")


if __name__ == "__main__":
    main()
