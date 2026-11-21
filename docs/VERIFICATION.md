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


## Website expansion, November 21, 2026

The October snapshot and its six original PNGs remain intact. The website adds 1,115 unique generated works from 77 collections, published as 3,000-pixel WebP images and 760-pixel thumbnails. Seven byte-identical duplicate inputs are collapsed; 224 raw scans, support assets and QA/presentation captures are excluded. `data/import-report.json` accounts for the input set. SVG alternatives are represented by raster equivalents rather than copied into Git. Each catalog record retains its original source path, SHA-256 and dimensions.

Validation for this update:

- Existing helper and bundle tests: `.venv/bin/python -m pytest -q` (14 passed).
- JavaScript syntax: `node --check gallery.js`.
- Complete public file inventory and SHA-256, five original bundles, six original PNGs, gallery catalog consistency, duplicate accounting and both WebP derivatives of all 1,115 works: `python scripts/refresh-manifest.py` then `uv run python scripts/verify-portfolio.py`.
- Playwright browser checks: run `tests/browser_gallery.py` against a static server on port 8765 using `uv run --no-project --with playwright python tests/browser_gallery.py`. `PORTFOLIO_BROWSER` can select an existing Chromium executable. Checks cover combined state/year/search filters, pagination, reset and no-results states, scenario labeling, keyboard viewer navigation, Escape, direct map links, persistent collection filters, and widths of 320, 390, 768 and 1440 pixels. JavaScript errors and failed HTTP responses fail the check.
- Desktop and mobile screenshots inspected locally; `.browser-artifacts/` is ignored and excluded from publication inventory.

These checks verify publication integrity and browsing behavior. They do not rerun analytical models, certify externally supplied election results, or resolve source-documentation gaps. Source notes and hypothetical-scenario labels remain visible in the gallery.

Publication verified at https://jacksonahannan.github.io/election-map-portfolio/. GitHub Pages build/deploy run 44946748469 succeeded for b59ca44. Live HTML, CSS, JavaScript and gallery catalog matched local SHA-256 hashes. The complete browser check above also passed against the public URL with no JavaScript or failed HTTP responses.
