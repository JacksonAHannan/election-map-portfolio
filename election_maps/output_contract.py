"""Validation and manifest helpers for publication output bundles.

A bundle is deliberately metadata-first: source files and external provenance may be
unavailable in a checkout, but the shape of the bundle and the integrity of the
artifacts that are present remain checkable.
"""

from __future__ import annotations

import csv
import hashlib
import json
import mimetypes
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Sequence

BundleKind = Literal["map", "analysis"]
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_MANIFEST_FIELDS = ("path", "role", "media_type", "sha256")
_MEDIA_TYPES = {
    ".csv": "text/csv",
    ".json": "application/json",
    ".md": "text/markdown",
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".svg": "image/svg+xml",
}
_ALLOWED_ROLES = {"metadata", "output", "audit", "crosswalk", "source", "documentation"}


@dataclass(frozen=True)
class Artifact:
    """One file recorded in a bundle manifest.

    ``sha256`` may be omitted when writing a manifest; :func:`write_manifest`
    computes it from the artifact relative to the manifest directory.
    """

    path: str | Path
    role: str
    media_type: str
    sha256: str | None = None


@dataclass(frozen=True)
class ContractIssue:
    """A single validation failure, suitable for CLI and programmatic reporting."""

    code: str
    message: str
    path: Path | None = None

    def __str__(self) -> str:
        location = f"{self.path}: " if self.path else ""
        return f"{location}{self.code}: {self.message}"


def _issue(issues: list[ContractIssue], code: str, message: str, path: Path | None = None) -> None:
    issues.append(ContractIssue(code=code, message=message, path=path))


def _load_json(path: Path, issues: list[ContractIssue], code: str) -> dict[str, object] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        _issue(issues, code, f"invalid JSON: {exc}", path)
        return None
    if not isinstance(value, dict):
        _issue(issues, code, "must contain a JSON object", path)
        return None
    return value


def _declared_kind(spec: dict[str, object]) -> str | None:
    value = spec.get("bundle_kind", spec.get("kind"))
    return value if isinstance(value, str) else None


def _canonical_extension(spec: dict[str, object]) -> str:
    value = spec.get("canonical_format", "svg")
    if not isinstance(value, str):
        return "svg"
    value = value.lower().strip()
    return value[1:] if value.startswith(".") else value


def _validate_relative_path(value: str, manifest: Path, issues: list[ContractIssue]) -> Path | None:
    candidate = Path(value)
    if candidate.is_absolute():
        _issue(issues, "ABSOLUTE_PATH", "manifest paths must be relative", manifest)
        return None
    if not value or candidate == Path(".") or any(part == ".." for part in candidate.parts):
        _issue(issues, "INVALID_PATH", "manifest path must stay inside its bundle", manifest)
        return None
    return candidate


def _expected_media_type(path: Path) -> str:
    return _MEDIA_TYPES.get(path.suffix.lower()) or mimetypes.guess_type(path.name)[0] or "application/octet-stream"


def _validate_manifest(bundle: Path, issues: list[ContractIssue]) -> set[str]:
    manifest = bundle / "manifest.csv"
    paths: set[str] = set()
    try:
        with manifest.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle, strict=True)
            fields = tuple(reader.fieldnames or ())
            if not set(_MANIFEST_FIELDS).issubset(fields):
                missing = ", ".join(field for field in _MANIFEST_FIELDS if field not in fields)
                _issue(issues, "INVALID_MANIFEST", f"missing required columns: {missing}", manifest)
                return paths
            seen: set[str] = set()
            for number, row in enumerate(reader, start=2):
                raw_path = (row.get("path") or "").strip()
                artifact_path = _validate_relative_path(raw_path, manifest, issues)
                if artifact_path is None:
                    continue
                paths.add(raw_path)
                if raw_path in seen:
                    _issue(issues, "DUPLICATE_ARTIFACT", f"duplicate manifest path {raw_path!r}", manifest)
                seen.add(raw_path)
                artifact = bundle / artifact_path
                if not artifact.is_file():
                    _issue(issues, "MISSING_ARTIFACT", f"artifact does not exist: {raw_path}", manifest)
                role = (row.get("role") or "").strip()
                if not role:
                    _issue(issues, "MISSING_ROLE", f"row {number} has no artifact role", manifest)
                elif role not in _ALLOWED_ROLES:
                    _issue(issues, "INVALID_ROLE", f"unsupported artifact role {role!r}", manifest)
                media_type = (row.get("media_type") or "").strip()
                if not media_type or media_type != _expected_media_type(artifact_path):
                    _issue(
                        issues,
                        "INVALID_MEDIA_TYPE",
                        f"{raw_path!r} declares {media_type!r}; expected {_expected_media_type(artifact_path)!r}",
                        manifest,
                    )
                digest = (row.get("sha256") or "").strip()
                if not _SHA256_RE.fullmatch(digest):
                    _issue(issues, "INVALID_SHA256", f"row {number} has no valid SHA-256 digest", manifest)
                elif artifact.is_file():
                    actual = hashlib.sha256(artifact.read_bytes()).hexdigest()
                    if digest != actual:
                        _issue(issues, "STALE_SHA256", f"SHA-256 does not match {raw_path}", manifest)
    except (csv.Error, OSError, UnicodeError) as exc:
        _issue(issues, "INVALID_MANIFEST", f"cannot read manifest: {exc}", manifest)
    return paths


def _published_spec_outputs(spec: dict[str, object]) -> list[object] | None:
    outputs = spec.get("outputs")
    if isinstance(outputs, list):
        return outputs
    if isinstance(outputs, dict):
        declared: list[object] = []
        for key in ("files", "paths", "outputs", "manifest"):
            value = outputs.get(key)
            if isinstance(value, list):
                declared.extend(value)
            elif isinstance(value, str):
                declared.append(value)
        return declared
    return None


def _validate_spec_outputs(
    bundle: Path,
    spec: dict[str, object],
    spec_path: Path,
    manifest_paths: set[str],
    issues: list[ContractIssue],
) -> None:
    outputs = _published_spec_outputs(spec)
    if outputs is None:
        return
    for value in outputs:
        if not isinstance(value, str):
            _issue(issues, "INVALID_SPEC_OUTPUT", "published outputs must be relative path strings", spec_path)
            continue
        artifact_path = _validate_relative_path(value, spec_path, issues)
        if artifact_path is None:
            continue
        normalized = artifact_path.as_posix()
        if not (bundle / artifact_path).is_file():
            _issue(issues, "MISSING_OUTPUT", f"published output does not exist: {value}", spec_path)
        if normalized not in manifest_paths:
            _issue(issues, "UNMANIFESTED_OUTPUT", f"published output is absent from manifest: {value}", spec_path)


def validate_bundle(path: Path) -> list[ContractIssue]:
    """Return every contract issue found in *path* without raising on bad metadata."""

    bundle = Path(path)
    issues: list[ContractIssue] = []
    if not bundle.is_dir():
        _issue(issues, "MISSING_BUNDLE", "bundle directory does not exist", bundle)
        return issues

    readme = bundle / "README.md"
    if not readme.is_file():
        _issue(issues, "MISSING_README", "bundle README.md is required", readme)

    map_spec = bundle / "map_spec.json"
    analysis_spec = bundle / "analysis_spec.json"
    map_exists = map_spec.is_file()
    analysis_exists = analysis_spec.is_file()
    if map_exists and analysis_exists:
        _issue(issues, "MULTIPLE_SPECS", "bundle must declare exactly one map or analysis specification", bundle)
    if analysis_exists:
        kind: BundleKind = "analysis"
        spec_path = analysis_spec
    else:
        kind = "map"
        spec_path = map_spec
        if not map_exists:
            _issue(issues, "MISSING_MAP_SPEC", "map_spec.json is required for a map bundle", map_spec)

    spec = _load_json(spec_path, issues, "INVALID_SPEC") if spec_path.is_file() else None
    if spec is not None:
        declared = _declared_kind(spec)
        if declared != kind:
            _issue(issues, "KIND_MISMATCH", f"spec declares {declared!r}, expected {kind!r}", spec_path)

    provenance = bundle / "provenance.json"
    if not provenance.is_file():
        _issue(issues, "MISSING_PROVENANCE", "provenance.json is required", provenance)
    else:
        provenance_data = _load_json(provenance, issues, "INVALID_PROVENANCE")
        if provenance_data is not None:
            provenance_kind = _declared_kind(provenance_data)
            if provenance_kind != kind:
                _issue(
                    issues,
                    "PROVENANCE_KIND_MISMATCH",
                    f"provenance declares {provenance_kind!r}, expected {kind!r}",
                    provenance,
                )

    manifest = bundle / "manifest.csv"
    manifest_paths: set[str] = set()
    if not manifest.is_file():
        _issue(issues, "MISSING_MANIFEST", "manifest.csv is required", manifest)
    else:
        manifest_paths = _validate_manifest(bundle, issues)
    if spec is not None:
        _validate_spec_outputs(bundle, spec, spec_path, manifest_paths, issues)

    if kind == "map":
        if not any(p.is_file() for p in bundle.rglob("*.png")):
            _issue(issues, "MISSING_PNG", "map bundles require at least one PNG artifact", bundle)
        canonical = _canonical_extension(spec or {})
        if not any(p.is_file() for p in bundle.rglob(f"*.{canonical}")):
            _issue(issues, f"MISSING_{canonical.upper()}", f"map bundle requires canonical .{canonical} artifact", bundle)

    return issues


def write_manifest(path: Path, artifacts: Sequence[Artifact]) -> None:
    """Write a deterministic CSV manifest, computing omitted hashes when possible."""

    manifest = Path(path)
    manifest.parent.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, str]] = []
    for artifact in artifacts:
        relative = Path(artifact.path)
        if relative.is_absolute() or any(part == ".." for part in relative.parts):
            raise ValueError(f"artifact paths must be relative: {relative}")
        digest = artifact.sha256
        target = manifest.parent / relative
        if not digest:
            digest = hashlib.sha256(target.read_bytes()).hexdigest()
        rows.append(
            {
                "path": relative.as_posix(),
                "role": artifact.role,
                "media_type": artifact.media_type,
                "sha256": digest,
            }
        )
    rows.sort(key=lambda row: row["path"])
    with manifest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=_MANIFEST_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
