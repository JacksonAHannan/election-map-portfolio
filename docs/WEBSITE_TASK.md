# Election map portfolio website

Goal: publish Jackson A. Hannan's existing election-map collection on GitHub Pages using this public portfolio repository.

Scope: every generated raster render in the main Election-Maps output collections, including map variants and companion analytical charts; preserve the six original portfolio PNGs and their reproduction workflows. Exclude raw source scans, vendor assets, browser QA captures and duplicate SVG versions. Preserve source identities, hashes, attributions, and scenario caveats. Do not alter the source archive or publish its raw datasets.

Completion criteria:
- [x] Inspect existing portfolio, archive, repository state and publication contracts.
- [x] Import all eligible renders reproducibly with web previews and source metadata; account for every excluded file.
- [x] Build responsive searchable gallery, filters, pagination, accessible image viewer, sources and direct image links.
- [x] Verify inventory completeness, image integrity, existing tests, desktop/mobile and keyboard browser behavior.
- [x] Commit/push the authorized website update; enable GitHub Pages and verify live deployment.

Design: map-led collection, white canvas, blue ink #172e47, slate #526477, pale blue #f0f4f7, blue #216485, muted red #b5434d. Georgia display type with Trebuchet MS/system sans-serif body. Left-aligned heading and intro beside a large Southern precinct map; quiet navigation and a full-width filterable image wall below. Use red/blue only sparingly in the site chrome so the maps carry their own palettes. Avoid ornamental map graphics and decorative statistics.

Design review: use a compact personal introduction rather than a promotional hero; the archive itself occupies most of the page. Keep charts and historical design variants available with descriptive categories and collection labels. Scenario maps must stay identified as hypothetical.

Evidence: existing repository clean, HEAD matches origin/main (9be211d). Main archive has 2,014 image exports (1,334 PNG, 678 SVG, 2 JPEG), including raw scans that will be excluded. GitHub Pages is not enabled yet (API returns 404).

Import evidence: 1,115 unique works in 77 collections; 1,122 eligible raster inputs, seven byte-identical duplicates, 224 excluded raw/support images. All six original PNG fingerprints are represented. All 678 SVGs have raster equivalents (some in parallel `svg` and `images` folders), or are support icons. The generated derivatives occupy approximately 233 MB.

Verification: existing 14 tests passed. Browser checks passed for combined filters, pagination, empty states, scenario labels, keyboard navigation, direct map links and layouts at 320/390/768/1440 pixels. The first browser run overlapped the import, so repeat it against the completed catalog. Initial inventory check caught local screenshot artifacts being included; add `.browser-artifacts` to both inventory scripts and rerun. This preserves the six-original-PNG contract.

Verification follow-up: the file-link check rejected the valid directory homepage link; the homepage now uses explicit `index.html`. Visual mobile review caught a missing space where the desktop heading line break was hidden; fixed the markup. Final integrity verification passed for 2,293 public files, all image derivatives and original bundles. Browser checks were repeated against the completed 1,115-work catalog and corrected markup. JavaScript syntax and whitespace checks passed. Publication complete: source pushed to `main` at b59ca44; GitHub Pages enabled from the repository root. Build and deployment run 44946748469 completed successfully. Live HTML, JavaScript, styles and catalog returned HTTP 200 with hashes matching the committed files. The complete browser check also passed against the public GitHub Pages URL. Repository homepage now links to the website. GitHub connector lacks Pages configuration and binary tree synchronization; use the authenticated local GitHub CLI for these operations.

Live website: https://jacksonahannan.github.io/election-map-portfolio/

Status: complete. No blockers. Source-documentation gaps remain explicitly visible by collection; analytical models were not rerun.

## Map correction and visual review (November 21, 2026)

User request: fix missing swing on split precincts in the latest House/Senate maps, and visually inspect the included maps for stray lines and unfilled precincts. This authorizes targeted corrections to source renderers and replacement of affected public derivatives; preserve unrelated existing source changes and raw inputs.

Completion criteria:
- [x] Reproduce missing split-precinct comparisons; identify a defensible district-specific historical baseline and distinguish observed from estimated values.
- [x] Fix the source pipeline with focused regression checks, preserve observed vote totals and audit every still-unavailable comparison.
- [x] Visually review every included render through readable sheets; inspect flagged maps individually and resolve rendering defects within scope.
- [x] Regenerate affected renders, import replacements, verify source/published integrity and browser behavior, publish and verify live update.

Parallel scope: a read-only split-data diagnosis; visual review of older Alabama collections; visual review of other states/regions. Parent owns current legislative/briefing series, source edits, integration and publication. Review evidence remains local under `.browser-artifacts/`; durable findings go in project documentation.

Diagnosis and correction: reproduced 73 missing finite D/R comparisons with valid whole-precinct continuity. Exact historical split-district presidential returns are unavailable; the smallest defensible correction uses explicitly labeled whole-precinct benchmarks for 49 House and 24 Senate reporting rows across 14 maps. No observed or historical vote count changes. The actual source policy and geometry-clipping path have 12 regression checks (red before helper, green after). Existing revised-data checks also pass. Broader rendering was stopped after refreshing audited data and seven unchanged statewide/congressional maps; a bounded invocation of the actual source functions regenerated the 14 affected maps from those audited outputs.

Visual coverage: merged per-image review records account for all 1,115 original catalog IDs, with no missing IDs. Parent inspected 316 IDs (including 20 overlap with the swing review), Alabama reviewer 414, other-state/swing reviewer 405. Suspects were enlarged; corrected legislative maps were rechecked. Confirmed visual findings: broken studio intermediate excluded; Madison atlas and SD25 primary text collisions assigned for correction. Documented missing data and real district/coastal shapes are retained.

Importer follow-up: source replacements now preserve existing shared map IDs and force both preview sizes to refresh. Source fingerprints in image URLs prevent stale cached renders. Two focused importer tests pass. Next: integrate the two layout renders, refresh source bundle manifests, import corrected derivatives and run publication verification.

Accepted corrections: 14 legislative benchmark maps plus two layout fixes are integrated. Seven statewide/congressional context maps were also redrawn during the initial standard rebuild, with unchanged data and additional visual checks. A partially written CD4 SVG from stopping that broad render was regenerated through the actual renderer and revalidated. Both image sizes for all 23 changed sources have changed bytes; existing shared IDs are preserved. One broken studio intermediate is excluded, leaving 1,114 works and 77 collections. Source acceptance compared all observed/historical counts and pre-existing eligible swings against the preserved prior output: unchanged, with exactly 73 newly supported comparisons.

Verification evidence: 31 source comparison/meeting checks passed, 12 affected layout/cartography/atlas checks passed, and all 16 website tests passed. Browser checks against the refreshed local catalog passed at 320/390/768/1440 pixels with no JavaScript or HTTP errors. Next: final manifests, publish and verify the live changed-image fingerprints.

Publication complete: correction commit b5b12fb371a9e2559e4ed8ce357aaf1b69e89851 deployed successfully in GitHub Pages run 44948733576. Live HTML, browser code, both catalog representations and all 23 changed full-size image files returned HTTP 200 with hashes matching the committed files. The complete browser suite also passed against the live public URL. All four correction/review acceptance units are complete; no blocker remains. Documented unavailable data and estimated benchmark assumptions remain visible.

## Portfolio UI simplification

User request: research sound UI practice and real portfolio examples, remove unnecessary text, and make the site simple and less formulaic.

Completion criteria:
- [x] Review primary UI guidance and real cartography/data-visualization portfolios; record linked findings in docs/UI_RESEARCH.md.
- [x] Replace the promotional hero and repeated explanation with direct access to the maps, compact navigation, short factual captions and restrained controls.
- [x] Keep all 1,114 works, filters/search, shareable URLs, keyboard access, required attribution and map-specific caveats available.
- [x] Inspect responsive screenshots, verify browsing and content integrity, publish and check the live site.

Constraints: change website presentation only. Do not redraw maps, alter their analytical values, drop maps, change fingerprints/IDs or add a framework. Research has one bounded owner; parent owns website edits and verification.

Initial audit: the current page repeats the purpose in a large slogan, personal introduction, collection heading/description, long about section and footer. Four main filters, seven category pills and sorting compete with the maps. Cards repeat filename-derived titles, collection names, category, geography/year and full credit sentences. Source and fingerprint details are always visible in the viewer. These are the main reduction targets.

Scope update: the user also requested editorial judgment about which maps to highlight. Add a selected-work opening view and retain the complete archive behind an explicit All maps control. Selection should favor clear electoral stories, strong compositions and a range of geography/scale; it should not simply feature the newest files or a run of near-identical districts.

Design plan after research: white #ffffff page, ink #222222, muted #626262, rule #d6d6d6, focus blue #1f4f8c and surface #f6f6f6. Use Arial/Helvetica for quiet site typography; original map typography remains the distinctive content. Compact owner identity and Selected / All maps navigation above a two-column, uncropped image grid; one column on mobile. All maps exposes search/geography first and secondary controls under More filters. Sources, full descriptions and fingerprints remain in the viewer's details disclosure. No slogan, hero, About essay, ornamental pills or animated entrances.

Review against brief: a neutral gallery is appropriate here because the maps already supply typography, color and detailed compositions. Two columns keep map details larger than a decorative three-column project wall. Eight selected works will show historical change, a major special election, a ballot question, a local race, special-election comparisons and one explicitly hypothetical regional map. Keep captions factual and short, and retain meaningful attribution.

Implementation evidence: selected-work page now opens directly on eight uncropped maps, with compact identity and two navigation choices. Archive controls are reduced to search/geography plus a More filters disclosure with active-filter count. Card text is a short factual caption and compact provider credit, with visible hypothetical/estimated flags where needed. Full credit sentences, source notes, claims and fingerprints remain in the large-view details. Slogan, hero, About copy, category pills and repeated card metadata were removed. Map/catalog bytes were not edited.

The updated browser suite passed against the local site, verifying eight distinct highlights, maps within 200px of the top, all archive browsing/filter/pagination behavior, scenario and estimate caveats, keyboard use, legacy URLs, source disclosure, and 320/390/768/1440px layouts. Screenshots inspected at desktop and mobile sizes. Existing browser assertions were updated where the intentionally changed UI replaces pills with a category select and moves advanced controls into disclosure; their behavior coverage was retained and expanded. Next: final integrity checks and publication.

UI update complete: d28ced8de10bf1df2151e750421d59f0f48dafc7 deployed successfully in GitHub Pages run 44951991002. Live HTML, JavaScript and CSS returned HTTP 200 and matched local committed SHA-256 hashes. The updated complete browser suite passed again against the public site at desktop, tablet and mobile widths, with no JavaScript or HTTP failures. All 16 website tests and the 2,294-file inventory check passed. No map or catalog records were changed. No blocker remains.
