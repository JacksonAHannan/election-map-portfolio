from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from election_maps.output_contract import Artifact, validate_bundle, write_manifest


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def make_contract_files(path: Path, *, kind: str = "map") -> None:
    path.mkdir(parents=True, exist_ok=True)
    (path / "README.md").write_text("# Example bundle\n", encoding="utf-8")
    spec_name = "map_spec.json" if kind == "map" else "analysis_spec.json"
    _write_json(path / spec_name, {"bundle_kind": kind, "title": "Example"})
    _write_json(
        path / "provenance.json",
        {
            "bundle_kind": kind,
            "source_data": {"status": "unknown", "sha256": None},
        },
    )
    (path / "result.png").write_bytes(b"png")
    if kind == "map":
        (path / "result.svg").write_text("<svg/>\n", encoding="utf-8")
    artifacts = []
    for artifact_path in sorted(path.iterdir()):
        if artifact_path.name in {"manifest.csv", "README.md"}:
            continue
        media_type = {
            ".json": "application/json",
            ".png": "image/png",
            ".svg": "image/svg+xml",
        }.get(artifact_path.suffix, "application/octet-stream")
        artifacts.append(
            Artifact(
                path=artifact_path.name,
                role="output" if artifact_path.suffix in {".png", ".svg"} else "metadata",
                media_type=media_type,
                sha256=hashlib.sha256(artifact_path.read_bytes()).hexdigest(),
            )
        )
    write_manifest(path / "manifest.csv", artifacts)


def test_map_bundle_requires_readme_spec_provenance_manifest_png_and_svg(tmp_path: Path):
    issues = validate_bundle(tmp_path)
    assert {issue.code for issue in issues} >= {
        "MISSING_README",
        "MISSING_MAP_SPEC",
        "MISSING_PROVENANCE",
        "MISSING_MANIFEST",
        "MISSING_PNG",
        "MISSING_SVG",
    }


def test_analysis_bundle_does_not_require_map_exports(tmp_path: Path):
    make_contract_files(tmp_path, kind="analysis")
    (tmp_path / "result.png").unlink()
    write_manifest(
        tmp_path / "manifest.csv",
        [
            Artifact(
                path="analysis_spec.json",
                role="metadata",
                media_type="application/json",
                sha256=hashlib.sha256((tmp_path / "analysis_spec.json").read_bytes()).hexdigest(),
            ),
            Artifact(
                path="provenance.json",
                role="metadata",
                media_type="application/json",
                sha256=hashlib.sha256((tmp_path / "provenance.json").read_bytes()).hexdigest(),
            ),
        ],
    )
    assert validate_bundle(tmp_path) == []


def test_validator_collects_manifest_path_hash_and_media_errors(tmp_path: Path):
    make_contract_files(tmp_path)
    manifest = tmp_path / "manifest.csv"
    rows = list(csv.DictReader(manifest.open(newline="", encoding="utf-8")))
    rows.extend(
        [
            {"path": "/tmp/absolute.png", "role": "output", "media_type": "image/png", "sha256": "0" * 64},
            {"path": "missing.png", "role": "output", "media_type": "image/png", "sha256": "not-a-hash"},
            {"path": "result.png", "role": "", "media_type": "text/plain", "sha256": "0" * 64},
        ]
    )
    with manifest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["path", "role", "media_type", "sha256"])
        writer.writeheader()
        writer.writerows(rows)

    codes = {issue.code for issue in validate_bundle(tmp_path)}
    assert {"ABSOLUTE_PATH", "MISSING_ARTIFACT", "INVALID_SHA256", "INVALID_MEDIA_TYPE", "MISSING_ROLE"} <= codes




def test_validator_requires_provenance_kind_match(tmp_path: Path):
    make_contract_files(tmp_path, kind="map")
    provenance = json.loads((tmp_path / "provenance.json").read_text(encoding="utf-8"))
    provenance["bundle_kind"] = "analysis"
    _write_json(tmp_path / "provenance.json", provenance)

    assert "PROVENANCE_KIND_MISMATCH" in {issue.code for issue in validate_bundle(tmp_path)}


def test_validator_reports_malformed_csv(tmp_path: Path):
    make_contract_files(tmp_path, kind="analysis")
    (tmp_path / "manifest.csv").write_text(
        'path,role,media_type,sha256\n"unterminated,metadata,application/json,'
        + "0" * 64
        + "\n",
        encoding="utf-8",
    )

    assert any(issue.code == "INVALID_MANIFEST" for issue in validate_bundle(tmp_path))


def test_validator_requires_published_spec_outputs_in_manifest(tmp_path: Path):
    make_contract_files(tmp_path, kind="map")
    spec = json.loads((tmp_path / "map_spec.json").read_text(encoding="utf-8"))
    spec["outputs"] = ["result.png", "missing.svg"]
    _write_json(tmp_path / "map_spec.json", spec)

    codes = {issue.code for issue in validate_bundle(tmp_path)}
    assert {"MISSING_OUTPUT", "UNMANIFESTED_OUTPUT"} <= codes


def test_write_manifest_computes_missing_hashes(tmp_path: Path):
    artifact = tmp_path / "result.json"
    artifact.write_text("{}\n", encoding="utf-8")
    write_manifest(
        tmp_path / "manifest.csv",
        [Artifact(path="result.json", role="metadata", media_type="application/json")],
    )
    rows = list(csv.DictReader((tmp_path / "manifest.csv").open(newline="", encoding="utf-8")))
    assert rows[0]["path"] == "result.json"
    assert rows[0]["sha256"] == hashlib.sha256(artifact.read_bytes()).hexdigest()
