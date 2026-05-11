#!/usr/bin/env python3
"""
Copy academic-site-semifinished into a target repo's docs/ folder.

  --variant general   GitHub Pages root = 通用版 (index.html unchanged).
  --variant medical   Root = 临床加强版; 通用版保留为 index-general.html.

Run from any cwd; pass --source and --docs explicitly.
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

IGNORE_NAMES = {"__pycache__", ".git"}


def copy_tree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(
        src,
        dst,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        dirs_exist_ok=False,
    )


def apply_medical_docs(docs: Path) -> None:
    """Root index.html serves clinical; generic home at index-general.html."""
    index_html = docs / "index.html"
    index_clinical = docs / "index-clinical.html"
    if not index_clinical.is_file():
        raise FileNotFoundError(docs / "index-clinical.html")

    # Preserve generic home
    shutil.copy2(index_html, docs / "index-general.html")

    clinical_text = index_clinical.read_text(encoding="utf-8")
    clinical_text = clinical_text.replace("index-clinical.html", "index.html")
    index_html.write_text(clinical_text, encoding="utf-8")

    # Version-panel and explicit 通用/临床 switches (not js-home-back fallbacks)
    repl_pairs = [
        ('<a href="index.html">通用版</a>', '<a href="index-general.html">通用版</a>'),
        ('<a href="index-clinical.html">临床加强版</a>', '<a href="index.html">临床加强版</a>'),
        ('<a href="index-clinical.html">临床加强</a>', '<a href="index.html">临床加强</a>'),
    ]

    for path in sorted(docs.glob("*.html")):
        text = path.read_text(encoding="utf-8")
        new = text
        for a, b in repl_pairs:
            new = new.replace(a, b)
        if path.name == "index-general.html":
            new = new.replace(
                '<a class="site-chrome__brand" href="index.html"',
                '<a class="site-chrome__brand" href="index-general.html"',
            )
            new = new.replace(
                '<a href="index.html" class="mast-identity__name"',
                '<a href="index-general.html" class="mast-identity__name"',
            )
        if new != text:
            path.write_text(new, encoding="utf-8")

    # Keep index-clinical.html in sync with root (bookmarks / old links)
    shutil.copy2(index_html, index_clinical)

    # site-ui.js: treat index-general as a home variant for scroll/session
    sui = docs / "site-ui.js"
    if sui.is_file():
        t = sui.read_text(encoding="utf-8")
        t = t.replace(
            'var HOMES = ["index.html", "index-ai.html", "index-clinical.html"];',
            'var HOMES = ["index.html", "index-ai.html", "index-clinical.html", "index-general.html"];',
        )
        sui.write_text(t, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, required=True, help="academic-site-semifinished directory")
    ap.add_argument("--docs", type=Path, required=True, help="Target .../docs path")
    ap.add_argument("--variant", choices=("general", "medical"), required=True)
    args = ap.parse_args()

    src: Path = args.source.resolve()
    docs: Path = args.docs.resolve()
    if not src.is_dir():
        print("source not a directory:", src, file=sys.stderr)
        return 1

    docs.parent.mkdir(parents=True, exist_ok=True)
    copy_tree(src, docs)
    (docs / ".nojekyll").touch()

    if args.variant == "medical":
        apply_medical_docs(docs)

    print("OK:", args.variant, "->", docs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
