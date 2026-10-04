# Snapshot verification

Prepared October 3, 2026. The original archive and its existing working-tree changes were preserved. The public copy contains only an explicit selected file set; no original Git history is included.

## Checks run on the isolated copy

- `uv sync --group dev`: passed; Python 3.12.13, 27 resolved packages, curated `uv.lock` generated.
- `uv run pytest -q`: **14 passed** in 3.74 seconds. Tests cover vote conservation, join cardinality, cartography helpers, output declarations and manifest/path integrity.
- `uv run python scripts/verify-portfolio.py`: passed. Checks complete publication file inventory and hashes, five output bundles, six PNG decodes, Python syntax, forbidden raw-data formats, private workstation-path patterns, local README/gallery links and adjacent RDH attribution.
- Six selected maps were visually inspected in the original archive before copying. Their PNG hashes preserve original bytes in this snapshot.

These checks verify the selected artifacts and software helpers. Election-input rebuilds were not run because the public copy intentionally excludes election tables, precinct geometry and reviewed derived inputs. Saved analytical audit values are archived run evidence, not newly reproduced results. The gallery was validated as static HTML and local links; no browser-interaction test is required for this static publication.

The installed copy environment resolves newer geospatial/rendering versions than the original saved map specifications. PNGs are unchanged original renders; installing the lock and passing helper tests does not demonstrate identical rerendering with those newer dependencies. See the reproduction guide for prerequisites and font limitations.

The synthetic `/tmp/absolute.png` string in a contract regression test verifies that absolute paths are rejected. It is a fixture and contains no private workstation path.
