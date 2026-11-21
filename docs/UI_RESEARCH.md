# Portfolio UI research

Reviewed November 21, 2026. The task is to make the maps easy to browse and remove unnecessary presentation copy. The recommendations below are design judgments applied to this brief, rather than findings from a usability study of this portfolio.

## Guidance

- **Keep the main task visible.** Nielsen's aesthetic/minimalist heuristic says extra information competes with the information people need. For this site, project images and finding a map are primary; a promotional headline and repeated explanations delay them. [Nielsen Norman Group: usability heuristics, especially 2 and 8](https://www.nngroup.com/articles/ten-usability-heuristics/).
- **Show a few useful controls first.** Progressive disclosure presents core options initially and makes specialized options available on request. A clearly labeled additional-filter control fits a large archive better than showing every filter and seven subject pills simultaneously. Choosing which controls are primary is an inference from this site's browsing task, not measured usage. [Nielsen Norman Group: progressive disclosure](https://www.nngroup.com/articles/progressive-disclosure/).
- **Simplify use, not just appearance.** The government design principles distinguish making something look simple from making it simple to use. Keep search, readable captions, large views, and predictable navigation while removing duplicate prose. [Government Design Principles, sections 1 and 4](https://www.gov.uk/guidance/government-design-principles).
- **Retain accessible controls and necessary context.** W3C recommends identifiable interactive elements, associated field labels, visible keyboard focus, readable contrast, responsive layouts, and alternatives for complex images. A minimal layout should preserve these, plus scenario and estimated-comparison labels that prevent misreading a map. [W3C WAI: designing for web accessibility](https://www.w3.org/WAI/tips/designing/).

## Real portfolio examples

These are observations from each owner's live site, including desktop browser screenshots, rather than descriptions from template roundups.

| Portfolio | Observed presentation | Useful lesson for this site |
| --- | --- | --- |
| [Andy Woodruff](https://andywoodruff.com/) | Compact name and introductory sentence, then large map/project images with short project names and descriptions. | Let the actual work occupy the page immediately after identification. Keep captions concrete. |
| [Visual Cinnamon / Nadieh Bremer](https://www.visualcinnamon.com/portfolio/) | A three-column image grid dominates the featured work. Detailed project filtering appears later with the full archive. | A consistent image grid can carry visual variety without decorative card chrome or paragraphs beside every image. |
| [Sarah Bell Maps](https://sarahbellmaps.com/portfolio) | Restrained identity/navigation and images beside categories; the page also has a substantial introductory block. | Borrow the restrained navigation, but skip its longer introduction for this user's stated preference. |
| [Rachael Dottle](https://www.rachaeldottle.com/) | Very little prose, distinctive blue/yellow lettering and framed project thumbnails. | Personal authorship can come from a deliberate visual choice instead of generic promotional writing. Its maximalist visual treatment is not a match for this brief. |

## Direction for this portfolio

1. Start with Jackson's name and the plain description “Election maps,” followed by the collection. Remove the large slogan, featured-map hero, browse CTA, and separate promotional About section.
2. Use a white page, ordinary readable typography, restrained links and spacing. Let the maps provide the color. Avoid shadows, ornamental pills and card borders that add no information.
3. Put search and the most useful archive selector in one compact row. Disclose secondary filters under an explicit label. Keep the result count and reset action useful but quiet.
4. Use one short map caption. Remove repeated collection/category/state/year strings where the title already supplies them. Keep required provider attribution adjacent where applicable; keep scenario/estimated labels visible.
5. Keep sources, methods and provenance available in the map view or a labeled disclosure. The main gallery should not display file hashes, internal paths or repeated methodological paragraphs. Do not shorten captions by hiding distinguishing district numbers, years or map types.

## Retrieval evidence

Firecrawl was attempted first but rejected the scrape because the connected account had no remaining credits. Primary pages were then read with the web tool and inspected using the existing Playwright/Chromium installation. Local text, requested URLs, HTTP status records and portfolio screenshots are saved under the ignored `.firecrawl/ui-research/` directory. The screenshots verify visual observations at a 1440-pixel desktop viewport; they do not establish usability or mobile quality.


## Editorial selection

The user additionally asked for judgment about the most interesting maps. These eight were chosen after comparing the actual renders. This is an editorial judgment, not a measured ranking or a claim endorsed by the external references.

| Selected map | Reason to feature it |
| --- | --- |
| Alabama Senate special election, 2017 | A recognizable close statewide contest, with four metropolitan insets and a clear visual hierarchy. |
| Tennessee presidential shift, 2016–2024 | A strong statewide/metro composition showing a long-period geographic change. |
| Kansas swing relative to the nation, 2016–2024 | The national adjustment makes the analytical question distinct from a standard raw-swing map; urban insets support it. |
| Alabama county realignment, 1992–2024 | A simple historical argument over 32 years, with a useful categorical palette and county-count companion chart. |
| Alabama Amendment 2, 2000 | A ballot question adds subject and palette variety to the candidate-election work, with precise precinct detail. |
| Huntsville City Council District 2, 2026 | A local race demonstrates a different geographic scale and clear two-candidate presentation. |
| Florida special elections, 2026 | The three-race result/swing comparison broadens the geography and shows comparative layout. |
| Southern midterm scenario, 2026 | One clearly hypothetical regional experiment demonstrates scale and modeled analysis without making scenarios the portfolio's opening claim. |

The default page has eight selected works. All 1,114 catalog works remain in **All maps**, including the latest corrected legislative series. Captions are edited for display; original titles, sources, fingerprints and analytical artifacts remain unchanged.
