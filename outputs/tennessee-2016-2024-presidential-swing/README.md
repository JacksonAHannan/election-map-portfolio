# Tennessee presidential swing, 2016–2024

## Claim
The map shows the change in Democratic two-party presidential vote share on Tennessee's 2024 reporting-precinct boundaries.

## Sources
The specification identifies VEST/RDH Tennessee 2016 precinct returns and RDH/Tennessee Secretary of State 2024 general-election results and boundaries. The rendering script uses the 2024 statewide precinct shapefile and records both source hashes.

## Method
`create-tennessee-2016-2024-presidential-swing-map.py` transfers 2016 votes through a spatial crosswalk to 2024 precincts, computes `2024 Harris two-party share − 2016 Clinton two-party share`, and renders fixed diverging classes centered at zero. The crosswalk and audit summary are included with the bundle.

## Limitations
This is a geographic comparison of two presidential electorates, not an individual-level or causal estimate. Crosswalk allocation and the 2024 reporting geography affect local values; the output CRS and source CRS differ as documented in `map_spec.json`.

## Rebuild
From the repository root, run `uv run python scripts/create-tennessee-2016-2024-presidential-swing-map.py`.


## Portfolio snapshot

Only the PNG files declared by `map_spec.json`, source code, and selected audit metadata are included. Original README descriptions above may refer to rebuild products available only after obtaining the excluded inputs. See the repository reproduction guide and source-attribution document. Original generation time is unknown; the snapshot date is not an election-result timestamp.
