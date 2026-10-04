# Reproducing the analysis

The checked-in gallery works without external inputs. The original rendering scripts are retained at their original relative paths. Rebuilding requires independently acquiring the omitted sources; this is a reproducible source workflow with external prerequisites, not a fully bundled election dataset.

## Environment

Use Python 3.12 and uv:

```bash
uv sync --group dev
uv run pytest -q
uv run python scripts/verify-portfolio.py
```

The lockfile records the curated environment. Original saved map specs record GeoPandas 1.1.4, pandas 3.0.5 and Matplotlib 3.10.5; newer locked dependencies may differ. Exact typography uses Nimbus Roman/Nimbus Sans Narrow and Source Serif 4 where specified; Matplotlib substitutes missing system fonts. Font binaries are not included.

## Required local inputs

Keep shapefile families together, including `.shp`, `.shx`, `.dbf`, `.prj` and any `.cpg`. Paths below are relative to this repository. These inputs must remain untracked.

| Script | Inputs |
| --- | --- |
| `create-alabama-2016-2024-presidential-swing-map.py` | `alabama/data/geospatial/election-precincts/al-vest-16/al-vest-16.shp`; `alabama/data/geospatial/election-precincts/al-2024-gen-prec/al-2024-gen-all-prec/al-2024-gen-all-prec.shp`. Downloads official Alabama Census block/PL94 archives to its local cache when missing. |
| `create-tennessee-2016-2024-presidential-swing-map.py` | `tennessee/data/tn_vest_16/tn_vest_16.shp`; `tennessee/data/tn_2024_gen_prec/tn_2024_gen_all_prec/tn_2024_gen_all_prec.shp`; `tennessee/data/census-2020-blocks/tl_2020_47_tabblock20.zip`; `tennessee/data/census-2020-blocks/tn2020.pl.zip`. Acquire Census archives separately; this script does not download them. |
| `create-alabama-2017-senate-special-election-map.py` | `alabama/data/geospatial/election-precincts/al-vest-17.zip`, containing `al_2017.shp`. |
| `create-alabama-1992-2024-realignment-map.py` | Local 1992–2024 workbook/archive collections under `alabama/data/election-results/general-precinct`, plus the 2024 Alabama statewide precinct family. Its year-specific extractors list expected filenames and sheets. |
| `create-alabama-cd5-2026-original-maps.py` | `outputs/alabama-2026-custom-precincts/alabama-2026-precincts.gpkg`; `outputs/alabama-cd5-2026-democratic-primary/precinct-results-first-round.csv`, `precinct-results-runoff.csv` and `candidate-totals.csv`. These reviewed derived inputs require the original project's reconciliation workflow and are excluded here. The editorial renderer performs exact joins only. |

After obtaining the inputs, run from the repository root:

```bash
uv run python scripts/create-alabama-2016-2024-presidential-swing-map.py
uv run python scripts/create-tennessee-2016-2024-presidential-swing-map.py
uv run python scripts/create-alabama-2017-senate-special-election-map.py
uv run python scripts/create-alabama-1992-2024-realignment-map.py
uv run python scripts/create-alabama-cd5-2026-original-maps.py
```

Rebuilds overwrite their output bundles and may produce other images, SVG/PDF, geometry, vote tables and crosswalk files. Do not stage those automatically. Original scripts may rewrite original metadata formats; curate declarations and re-verify the publication subset before republishing. The copied helpers expose reusable vote-conservation, join-cardinality, cartography and output-manifest functions. They are small library examples; the original standalone renderers retain their own inline validation.

## Publication integrity

`manifest.json` records every intended publication file, its bytes and SHA-256. Each map bundle has a fresh manifest containing only the included artifacts, and a provenance note separating saved run evidence from this snapshot. `sources/snapshot-provenance.json` preserves original hashes before metadata adaptations. `verify-portfolio.py` checks declarations, bundle hashes, PNG decoding, the complete file inventory, forbidden source-data formats and local gallery links. It does not reconstruct elections or certify provider terms.
