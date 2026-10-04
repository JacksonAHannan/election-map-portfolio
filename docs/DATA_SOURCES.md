# Source attribution and interpretation

The maps are original cartographic compositions using external election results and geometry. MIT applies to code only. No raw election tables, voter files, candidate photos, downloaded archives or precinct geometries are distributed here. Maps and data retain their applicable input terms; exclusion of raw inputs does not create new redistribution rights.

## Providers

- **Alabama Secretary of State**: [election data](https://www.sos.alabama.gov/alabama-votes/voter/election-data). Primary result source for Alabama historical and 2026 contests.
- **Tennessee Secretary of State**: [2016 results](https://sos.tn.gov/elections/results#2016) and [2024 results](https://sos.tn.gov/elections/results#2024).
- **Voting and Election Science Team (VEST)** and **Redistricting Data Hub (RDH)**: joined precinct election returns and boundaries for the state/year datasets described in the individual map specifications. RDH is a project of [nonpartisan Community Research Lab](https://redistrictingdatahub.org/). Consult RDH's current usage/attribution requirements when acquiring and reusing inputs.
- **U.S. Census Bureau**: 2020 PL 94-171 voting-age population and TIGER/Line tabulation-block internal points. The block-point weighting uses P3 total voting-age population, not registered voters or race-specific vote estimates.
- **Tennessee Comptroller of the Treasury**: [maps](https://comptroller.tn.gov/maps.html), a principal Tennessee precinct-geometry provider. Hamilton County GIS and other county governments supplied additional boundaries. Alabama geometry also incorporates Census and county-government sources through VEST/RDH processing.

## Dataset evidence retained from local provider readmes

Alabama 2016 VEST/RDH metadata records retrieval on 2021-06-01 and cites the Alabama Secretary of State, selected corrected county canvasses, Census geometry and county geometry. Alabama 2024 RDH metadata records retrieval on 2025-04-21 and uses RDH's 2022/2020 Alabama layers plus county-specific updates. It allocates county or judicial-division absentee/provisional votes to precincts by candidate election-day share.

Tennessee 2016 VEST/RDH metadata records retrieval on 2022-01-20 and cites the Tennessee Secretary of State, Comptroller and Hamilton County GIS. Some absentee/provisional and write-in returns are distributed by candidate precinct share. Tennessee 2024 RDH metadata records retrieval on 2026-03-13, describes boundary updates and district splits, and reports statewide totals matching official results. A third-party voter file was used by the provider for geography checks; no voter records are included in this portfolio.

## RDH usage terms

This map was created using data from the Redistricting Data Hub.

This is a noncommercial, nonpartisan analytical portfolio. [RDH terms and conditions](https://redistrictingdatahub.org/terms-and-conditions/) permit noncommercial, nonpartisan maps and copies with attribution and retained terms, and prohibit use to support gerrymandering. Reusers must follow those terms and applicable dataset-specific provider notices. The maps are analytical illustrations, not district-drawing tools. No data is offered under MIT.

Specific dataset landing URLs and full original license records were not present for every locally archived input. Named providers and saved source fingerprints are evidence of provenance, not a blanket license grant. Obtain missing inputs from the provider and check its current terms. Snapshot provenance records copy integrity; original map generation dates remain unknown.

## Limits visible in the gallery

**Alabama presidential swing:** 2016 returns are exact for unchanged precincts. Changed boundaries allocate votes using Census block voting-age population, constrained by county. The saved audit reports 2,000 source precincts, 1,947 target precincts, 1,398 exact target matches and zero maximum county vote error. These are stored run results; this public snapshot did not rerun the crosswalk. The paired quality map describes geometry relationships, not statistical confidence intervals.

**Tennessee presidential shift:** the saved audit reports 1,985 source precincts, 1,862 targets and zero maximum county vote error. Fifteen crosswalk rows used an area fallback; all other allocated rows used block voting-age population or exact matching. Precinct estimates depend on geography and provider allocation choices.

**2017 Alabama Senate:** two-candidate margin excludes write-ins. The saved spec records 1,996 valid features, 30 projected-geometry repairs and one missing mapped value. Map linework is simplified for display by 10 metres.

**1992–2024 Alabama realignment:** county categories date the first Republican presidential win followed by uninterrupted wins through 2024. Two counties have incomplete source records and are shown gray; the classification does not date an individual voter's party change.

**2026 Alabama CD5 runoff:** the original broadsheet uses reviewed results and reconstructed 2026 reporting geography on a 2024 base, not certified 2026 election boundaries. It maps 20,835 election-day votes across 202 voting geometries. Official totals include absentee/provisional votes and sum to 21,295. Five geometries have no recorded district candidate votes; those are visibly hatched. No votes are assigned to omitted areas.

Geographic change does not identify individual voter transitions or establish causes. Maps describe aggregate electoral patterns; they are not forecasts.
