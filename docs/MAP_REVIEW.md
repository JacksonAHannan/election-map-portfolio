# Map corrections and visual review

The November 21 review covered all 1,115 works that were originally published. Every image was viewed on a readable contact sheet; suspected defects and corrected maps were inspected at larger sizes. This is a visual screening of the full collection, not a native-resolution audit of every precinct pixel.

## Latest House and Senate comparisons

The revised Alabama 2026 general-election maps previously withheld every split-precinct comparison. The correction restores 73 supported reporting-row comparisons across nine House and five Senate maps: HD2, HD4, HD5, HD8, HD10, HD19, HD20, HD21, HD25, SD2, SD3, SD6, SD7 and SD8.

These are explicitly **estimated comparisons to the 2024 whole-precinct presidential margin**. Historical presidential returns do not separately report each legislative district fragment. A split fragment can use the whole-precinct margin as a benchmark only where the source has a single historical precinct, complete returns and at least 99% mutual boundary continuity. This assumes a uniform historical margin inside the precinct. It does not recover an observed same-electorate swing.

The map headings and footnotes identify the benchmark. Exact and estimated comparison counts are separated in the source completeness reports. All observed 2026 votes, historical vote counts, result-fill masks and previously supported whole-unit comparisons were checked against the preceding output and remain unchanged. Boundary failures, undefined D/R comparisons and other unsupported areas remain gray. Administrative ballots remain in totals and off the maps.

## Visual findings

- The affected 14 legislative maps were regenerated and inspected after the comparison fix.
- The Madison general-election atlas top-ticket graphic had subtitle/panel-label and legend/footer overlaps; its layout was corrected without changing the underlying map data.
- The Democratic Senate District 25 primary map had a title/year-label collision; the header spacing was corrected.
- A studio intermediate, `political-map-studio/output/browser-verified.png`, had four empty inset frames. It was excluded from the public gallery; completed sibling examples remain. The original source render is preserved locally. The gallery consequently contains 1,114 works across the same 77 collections.
- Investigated apparent holes and lines were explained by official district concavities, coastline/precinct coverage, documented unmatched comparisons or zero-vote areas. HD74's notch matches the district geometry; Fort Rucker's gray area has no 2024 presidential votes. Older primary maps intentionally retain faint county context outlines outside the filled district. Those contextual lines do not join unrelated polygon rings.

Earlier briefing versions remain separate historical collections. Their documented comparison and local-electorate exclusions are preserved; the corrected revised collection is the current general-election presentation.

## Verification

Focused source tests exercise real HD10 and SD8 split rows, preservation of both years' counts, unsupported comparisons, and clipping/masking through the actual map builder. Layout regression tests detect the two text collisions. The website importer has regression coverage for refreshing both image sizes after a source changes while preserving existing shared map IDs, and for excluding the broken studio intermediate. Image URLs include the source fingerprint so corrected maps replace cached previews.

Publication verification includes all catalog images and fingerprints, the original six-map bundles, JavaScript syntax, website tests and desktop/mobile browser checks. Local evidence includes per-image review records, contact sheets, original-file backups and corrected-render audits; these support files are not public source datasets.
