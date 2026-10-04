# Election Map Portfolio

Election cartography by Jackson A. Hannan: six finished maps showing precinct analysis, geographic reconciliation and editorial design across Alabama and Tennessee. Python workflows use GeoPandas, pandas, NumPy and Matplotlib, with saved audit evidence and source attribution.

[Browse the image gallery](index.html) · [Reproduction guide](docs/REPRODUCING.md) · [Sources and limitations](docs/DATA_SOURCES.md)

## Precinct swing with boundary-change diagnostics

![Alabama presidential swing by precinct, 2016–2024](outputs/alabama-2016-2024-presidential-swing/alabama-presidential-swing-2016-2024.png)

This map was created using data from the Redistricting Data Hub. [RDH terms and conditions](https://redistrictingdatahub.org/terms-and-conditions/).

Historical precinct boundaries change. The Alabama workflow preserves exact matches and allocates changed 2016 precincts to 2024 geography using 2020 Census block voting-age population. Its saved audit reconciles candidate totals within every county: 2,000 historical precincts to 1,947 current precincts, with zero maximum county vote error. These are archived run results, not a fresh reconstruction for this snapshot.

![Alabama precinct crosswalk quality](outputs/alabama-2016-2024-presidential-swing/alabama-presidential-swing-crosswalk-quality.png)

This map was created using data from the Redistricting Data Hub. [RDH terms and conditions](https://redistrictingdatahub.org/terms-and-conditions/).

The companion diagnostic distinguishes exact geometry, merges, splits and complex changes. It makes the reconstruction visible alongside the headline map. [Source](scripts/create-alabama-2016-2024-presidential-swing-map.py) · [Saved audit](outputs/alabama-2016-2024-presidential-swing/crosswalk-audit.json)

## A second state, with metro context

![Tennessee presidential shift by precinct, 2016–2024](outputs/tennessee-2016-2024-presidential-swing/tennessee-presidential-shift-2016-2024.png)

This map was created using data from the Redistricting Data Hub. [RDH terms and conditions](https://redistrictingdatahub.org/terms-and-conditions/).

The Tennessee map combines a statewide view, Nashville–Murfreesboro inset and a fixed diverging scale. The crosswalk retains documented population and area fallback methods; it compares aggregate two-party vote shares, not individual voter transitions. [Source](scripts/create-tennessee-2016-2024-presidential-swing-map.py) · [Saved audit](outputs/tennessee-2016-2024-presidential-swing/crosswalk-audit.json)

## Historical results at statewide and metropolitan scales

![2017 Alabama Senate special-election margin by precinct](outputs/alabama-2017-senate-special-election/alabama-2017-senate-special-election-margin-by-precinct.png)

This map was created using data from the Redistricting Data Hub. [RDH terms and conditions](https://redistrictingdatahub.org/terms-and-conditions/).

The Jones–Moore map uses four metro windows at an identical scale, repaired projected geometry and five-point margin classes. The denominator includes only the two named candidates; write-ins are excluded. [Source](scripts/create-alabama-2017-senate-special-election-map.py) · [Map specification](outputs/alabama-2017-senate-special-election/map_spec.json)

## Thirty-two years of county realignment

![Alabama county presidential realignment, 1992–2024](outputs/alabama-1992-2024-presidential-realignment/alabama-presidential-realignment-1992-2024.png)

This map was created using data from the Redistricting Data Hub. [RDH terms and conditions](https://redistrictingdatahub.org/terms-and-conditions/).

Year-specific spreadsheet extractors reconcile county names and classify the first Republican presidential victory followed by uninterrupted wins through 2024. The finished map pairs categorical geography with a county-count chart; gray counties retain incomplete-record warnings. [Source](scripts/create-alabama-1992-2024-realignment-map.py)

## An original editorial election graphic

![Alabama CD5 2026 Democratic runoff broadsheet](outputs/alabama-cd5-2026-democratic-primary/original-broadsheet/alabama-cd5-2026-democratic-runoff-broadsheet.png)

This map was created using data from the Redistricting Data Hub. [RDH terms and conditions](https://redistrictingdatahub.org/terms-and-conditions/).

A full-width map, candidate-specific margin shading and proportional official-result bar tell the runoff story. Reviewed precinct identities are joined exactly to derived 2026 reporting geography. Mapped election-day votes and official totals including absentee/provisional votes remain distinct; five no-vote geometries are hatched. [Source](scripts/create-alabama-cd5-2026-original-maps.py) · [Saved rendering audit](outputs/alabama-cd5-2026-democratic-primary/original-broadsheet/render-audit.json)

## What is included

The repository includes six PNG renders, five original Python rendering/analysis scripts, reusable integrity and cartography helpers, selected map specifications and saved audit summaries, tests and hash manifests. The source snapshot preserves original relative paths and excludes original Git history.

```bash
uv sync --group dev
uv run pytest -q
uv run python scripts/verify-portfolio.py
```

The gallery opens directly as a local HTML file. Rebuilding maps requires external election and geometry inputs documented in the [reproduction guide](docs/REPRODUCING.md). No raw election tables, precinct geometry, voter records, candidate photographs or downloaded source archives are shipped. Original map generation timestamps are unknown; the preparation snapshot is dated October 3, 2026.

Sources include the Alabama and Tennessee Secretaries of State, VEST, Redistricting Data Hub, the U.S. Census Bureau and county/Comptroller geometry providers. Provider processing may allocate absentee/provisional votes to precincts; changed boundaries require estimates. Preserve [source attribution and interpretation limits](docs/DATA_SOURCES.md) when reusing these images. The [MIT license](LICENSE) applies to code only; maps and external data retain applicable input terms.

## Related projects

[Political Map Studio](https://github.com/JacksonAHannan/political-map-studio) is the companion interactive layout editor with synthetic demonstration data. [Huntsville District 3 results](https://jacksonahannan.github.io/huntsville-district-3-results/) shows a separately published read-only election-results website.

## Resume description

Built Python election-cartography pipelines with GeoPandas, pandas and Matplotlib; reconciled changing precinct boundaries using reciprocal spatial overlap and Census block voting-age population, documented county-level vote-conservation checks, and published source-attributed case studies across Alabama and Tennessee.
