# Alabama 2017 U.S. Senate special election

## Claim
The map shows the two-candidate geographic margin between Democrat Doug Jones and Republican Roy Moore in Alabama's December 12, 2017 special U.S. Senate election.

## Sources
The rendering script reads `alabama/data/geospatial/election-precincts/al-vest-17.zip`, which contains the VEST 2017 precinct returns and geometry used by this bundle.

## Method
`create-alabama-2017-senate-special-election-map.py` computes `100 × (Jones − Moore) / (Jones + Moore)` for each precinct/VTD, repairs invalid projected geometries, and renders fixed diverging classes centered at zero. A missing-value color is retained for the one feature without a mapped value.

## Limitations
This is a two-candidate margin, not total turnout or a measure of individual voter behavior. The displayed geography is the 2017 precinct/VTD layer, and the rendering simplification is for display only.

## Rebuild
From the repository root, run `uv run python scripts/create-alabama-2017-senate-special-election-map.py`.


## Portfolio snapshot

Only the PNG files declared by `map_spec.json`, source code, and selected audit metadata are included. Original README descriptions above may refer to rebuild products available only after obtaining the excluded inputs. See the repository reproduction guide and source-attribution document. Original generation time is unknown; the snapshot date is not an election-result timestamp.
