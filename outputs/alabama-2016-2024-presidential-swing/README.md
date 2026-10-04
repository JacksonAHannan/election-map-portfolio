# Alabama presidential swing, 2016–2024

This directory maps the change in Democratic two-party presidential vote share
from 2016 to 2024 on the 2024 statewide precinct geography.

## Measure

`swing_pp = 100 × [Harris / (Harris + Trump) − Clinton / (Clinton + Trump)]`

Positive values indicate movement toward Democrats and negative values indicate
movement toward Republicans. Third-party votes are excluded from both years.
Zero is a color-class boundary rather than the center of a neutral class, so
every nonzero swing receives a directional color. Intensity changes in
five-percentage-point intervals on either side of zero.

## Crosswalk

- A 2016 and 2024 precinct pair is exact when each is the other's largest
  spatial match and both polygon-overlap shares are at least 99 percent.
- Exact pairs retain the reported 2016 vote totals without interpolation.
- Changed 2016 precincts are allocated to 2024 precincts using the voting-age
  population at official 2020 Census block internal points.
- Allocation is restricted within county boundaries and each source precinct's
  weights sum to one.
- Polygon area is implemented as a documented fallback for zero-VAP source
  precincts. It was not invoked in the completed statewide crosswalk.
- Allocated Clinton and Trump totals reconcile exactly to the VEST source totals
  in every county.

The crosswalk-quality categories describe target precincts: exact geometry,
simple merge, split allocation, or complex many-to-many boundary change. They
are relationship categories, not statistical confidence intervals.

## Files

- `alabama-presidential-swing-2016-2024.png` and `.svg`: finished swing map.
- `alabama-presidential-swing-crosswalk-quality.png` and `.svg`: boundary-change
  diagnostic map.
- `alabama-presidential-swing-2016-2024.gpkg`: 2024 precinct polygons with both
  elections, reconstructed 2016 totals, swing, and crosswalk class.
- `alabama-2016-to-2024-precinct-crosswalk.csv`: source-target weights,
  overlap shares, methods, and allocated 2016 candidate votes.
- `crosswalk-audit.json`: statewide totals, weight checks, reconciliation error,
  and category counts.
- `swing-color-breaks.csv`: exact five-point map intervals and hex colors.

## Sources and limitations

Election results and precinct geometry come from the repository's VEST-derived
2016 and Alabama 2024 statewide precinct files. Allocation weights use the 2020
Census PL 94-171 P3 voting-age total and TIGER/Line tabulation-block internal
points. A block-point allocation is substantially preferable to polygon area,
but it cannot recover within-block residential or voter-distribution differences.
The quality map should accompany close interpretation of reconstructed areas.

Fort Rucker in Coffee County has zero two-party presidential votes in both
source years and is the sole precinct shown without a swing value.


## Portfolio snapshot

Only the PNG files declared by `map_spec.json`, source code, and selected audit metadata are included. Original README descriptions above may refer to rebuild products available only after obtaining the excluded inputs. See the repository reproduction guide and source-attribution document. Original generation time is unknown; the snapshot date is not an election-result timestamp.
