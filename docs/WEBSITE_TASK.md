# Election map portfolio website

Goal: publish Jackson A. Hannan's existing election-map collection on GitHub Pages using this public portfolio repository.

Scope: every generated raster render in the main Election-Maps output collections, including map variants and companion analytical charts; preserve the six original portfolio PNGs and their reproduction workflows. Exclude raw source scans, vendor assets, browser QA captures and duplicate SVG versions. Preserve source identities, hashes, attributions, and scenario caveats. Do not alter the source archive or publish its raw datasets.

Completion criteria:
- [x] Inspect existing portfolio, archive, repository state and publication contracts.
- [x] Import all eligible renders reproducibly with web previews and source metadata; account for every excluded file.
- [x] Build responsive searchable gallery, filters, pagination, accessible image viewer, sources and direct image links.
- [x] Verify inventory completeness, image integrity, existing tests, desktop/mobile and keyboard browser behavior.
- [ ] Commit/push the authorized website update; enable GitHub Pages and verify live deployment.

Design: map-led collection, white canvas, blue ink #172e47, slate #526477, pale blue #f0f4f7, blue #216485, muted red #b5434d. Georgia display type with Trebuchet MS/system sans-serif body. Left-aligned heading and intro beside a large Southern precinct map; quiet navigation and a full-width filterable image wall below. Use red/blue only sparingly in the site chrome so the maps carry their own palettes. Avoid ornamental map graphics and decorative statistics.

Design review: use a compact personal introduction rather than a promotional hero; the archive itself occupies most of the page. Keep charts and historical design variants available with descriptive categories and collection labels. Scenario maps must stay identified as hypothetical.

Evidence: existing repository clean, HEAD matches origin/main (9be211d). Main archive has 2,014 image exports (1,334 PNG, 678 SVG, 2 JPEG), including raw scans that will be excluded. GitHub Pages is not enabled yet (API returns 404).

Import evidence: 1,115 unique works in 77 collections; 1,122 eligible raster inputs, seven byte-identical duplicates, 224 excluded raw/support images. All six original PNG fingerprints are represented. All 678 SVGs have raster equivalents (some in parallel `svg` and `images` folders), or are support icons. The generated derivatives occupy approximately 233 MB.

Verification: existing 14 tests passed. Browser checks passed for combined filters, pagination, empty states, scenario labels, keyboard navigation, direct map links and layouts at 320/390/768/1440 pixels. The first browser run overlapped the import, so repeat it against the completed catalog. Initial inventory check caught local screenshot artifacts being included; add `.browser-artifacts` to both inventory scripts and rerun. This preserves the six-original-PNG contract.

Verification follow-up: the file-link check rejected the valid directory homepage link; the homepage now uses explicit `index.html`. Visual mobile review caught a missing space where the desktop heading line break was hidden; fixed the markup. Final integrity verification passed for 2,293 public files, all image derivatives and original bundles. Browser checks were repeated against the completed 1,115-work catalog and corrected markup. JavaScript syntax and whitespace checks passed. Next: commit/push and enable GitHub Pages, then verify live deployment. GitHub connector lacks Pages configuration and binary tree synchronization; use the authenticated local GitHub CLI for these operations.
