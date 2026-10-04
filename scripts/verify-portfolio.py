#!/usr/bin/env python3
"""Check the curated publication inventory without obtaining election inputs."""

from __future__ import annotations

import ast
import hashlib
import json
import re
from pathlib import Path

from PIL import Image

from election_maps.output_contract import validate_bundle

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_PARTS = {".git", ".venv", "__pycache__", ".pytest_cache", "build", "dist"}
FORBIDDEN_SUFFIXES = {".gpkg", ".shp", ".shx", ".dbf", ".prj", ".cpg", ".zip", ".rar", ".xls", ".xlsx"}


def main() -> None:
    manifest = json.loads((ROOT / "manifest.json").read_text())
    declared = {record["path"]: record for record in manifest["files"]}
    actual = {
        str(path.relative_to(ROOT)): path
        for path in ROOT.rglob("*")
        if path.is_file()
        and not any(part in EXCLUDED_PARTS or part.endswith(".egg-info") for part in path.relative_to(ROOT).parts)
        and path.name != "manifest.json"
    }
    assert set(actual) == set(declared), f"Inventory differs: {set(actual) ^ set(declared)}"
    png_count = 0
    for name, path in actual.items():
        record = declared[name]
        assert path.stat().st_size == record["bytes"], f"Size changed: {name}"
        assert hashlib.sha256(path.read_bytes()).hexdigest() == record["sha256"], f"Hash changed: {name}"
        assert path.suffix.lower() not in FORBIDDEN_SUFFIXES, f"Source-data format: {name}"
        assert not (path.suffix == ".csv" and path.name != "manifest.csv"), f"Unexpected table: {name}"
        if path.suffix == ".png":
            with Image.open(path) as image:
                image.verify()
            png_count += 1
        if path.suffix == ".py":
            ast.parse(path.read_text(), filename=name)
        if path.suffix in {".py", ".md", ".html", ".json", ".toml", ".csv"}:
            content = path.read_text()
            assert not re.search(r"/(?:home|Users)/[A-Za-z0-9_-]+/", content), f"Private workstation path: {name}"
    assert png_count == 6, f"Expected six curated PNGs, found {png_count}"
    specs = list((ROOT / "outputs").rglob("map_spec.json"))
    assert len(specs) == 5, f"Expected five bundles, found {len(specs)}"
    for spec in specs:
        issues = validate_bundle(spec.parent)
        assert not issues, "\n".join(str(issue) for issue in issues)
    html = (ROOT / "index.html").read_text()
    for target in re.findall(r'(?:href|src)="([^"]+)"', html):
        if not target.startswith(("http:", "https:", "#")):
            assert (ROOT / target).is_file(), f"Broken gallery link: {target}"
    markdown = (ROOT / "README.md").read_text()
    for target in re.findall(r"\]\(([^)]+)\)", markdown):
        if not target.startswith(("http:", "https:", "#")):
            assert (ROOT / target).is_file(), f"Broken README link: {target}"
    credit = "This map was created using data from the Redistricting Data Hub."
    assert html.count(credit) == 6 and markdown.count(credit) == 6, "Missing adjacent map attribution"
    print(f"Verified {len(actual)} publication files, six PNGs, five bundle manifests, source syntax and gallery/README links.")


if __name__ == "__main__":
    main()
