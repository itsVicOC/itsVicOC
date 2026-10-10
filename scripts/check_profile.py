#!/usr/bin/env python3
"""Check that README images exist locally and SVGs are self-contained."""

from html.parser import HTMLParser
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]


class Images(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.images: list[tuple[str, str]] = []

    def handle_starttag(self, tag, attributes) -> None:
        if tag == "img":
            attrs = dict(attributes)
            self.images.append((attrs.get("src") or "", attrs.get("alt") or ""))


def check_profile(root: Path = ROOT) -> list[str]:
    errors = []
    readme = (root / "README.md").read_text(encoding="utf-8")
    parser = Images()
    parser.feed(readme)
    images = parser.images + [
        (source, alt) for alt, source in re.findall(r"!\[([^\]]*)\]\(([^\s)]+)\)", readme)
    ]
    if not images:
        errors.append("README contains no images")

    for source, alt in images:
        if not alt.strip():
            errors.append(f"Missing alternative text: {source}")
        url = urlsplit(source)
        if url.scheme or url.netloc or not url.path:
            errors.append(f"Image must use a repository-local path: {source}")
            continue
        path = (root / unquote(url.path)).resolve()
        if root.resolve() not in path.parents or not path.is_file():
            errors.append(f"Missing or out-of-repository image: {source}")
        elif path.stat().st_size == 0:
            errors.append(f"Empty image: {source}")

    for path in sorted((root / "assets").rglob("*.svg")):
        label = path.relative_to(root)
        try:
            text = path.read_text(encoding="utf-8")
            svg = ET.fromstring(text)
        except (OSError, ET.ParseError) as exc:
            errors.append(f"Invalid SVG {label}: {exc}")
            continue
        if svg.tag != "{http://www.w3.org/2000/svg}svg" or not svg.get("viewBox"):
            errors.append(f"SVG needs an SVG root and viewBox: {label}")
        for element in svg.iter():
            tag = element.tag.rsplit("}", 1)[-1]
            if tag in {"script", "foreignObject", "image"}:
                errors.append(f"SVG has a script, HTML or nested image dependency: {label}")
            for name, value in element.attrib.items():
                local_name = name.rsplit("}", 1)[-1]
                if local_name.lower().startswith("on"):
                    errors.append(f"SVG has an event handler: {label}")
                if local_name == "href" and not value.startswith("#"):
                    errors.append(f"SVG has an external reference: {label}")
        if re.search(r"url\(\s*['\"]?(?!#)[^\s)]+", text) or "@import" in text:
            errors.append(f"SVG has an external style dependency: {label}")
    return errors


if __name__ == "__main__":
    problems = check_profile()
    if problems:
        print("\n".join(problems), file=sys.stderr)
        raise SystemExit(1)
    print("Profile OK: all README images exist locally; SVGs have no external dependencies.")
