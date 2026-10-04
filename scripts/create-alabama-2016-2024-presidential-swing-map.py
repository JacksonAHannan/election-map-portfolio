"""Crosswalk 2016 presidential returns to 2024 precincts and map two-party swing.

Unchanged precincts are linked by reciprocal 99% polygon overlap. Changed
precincts are allocated with 2020 Census block voting-age population (VAP),
using polygon area only when a 2016 precinct contains no assigned VAP.
"""

from __future__ import annotations

import csv
import io
import json
import urllib.request
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.patches import Patch, Rectangle


ROOT = Path(__file__).resolve().parents[1]
SOURCE16 = ROOT / "alabama/data/geospatial/election-precincts/al-vest-16/al-vest-16.shp"
TARGET24 = (ROOT / "alabama/data/geospatial/election-precincts/al-2024-gen-prec"
            / "al-2024-gen-all-prec/al-2024-gen-all-prec.shp")
OUTPUT = ROOT / "outputs/alabama-2016-2024-presidential-swing"
CACHE = ROOT / "alabama/data/demographics/census-2020-blocks"
BLOCK_URL = ("https://www2.census.gov/geo/tiger/TIGER2020PL/STATE/01_ALABAMA/01/"
             "tl_2020_01_tabblock20.zip")
PL_URL = ("https://www2.census.gov/programs-surveys/decennial/2020/data/"
          "01-Redistricting_File--PL_94-171/Alabama/al2020.pl.zip")
EA = 5070
SERIF = "Nimbus Roman"
SANS = "Nimbus Sans Narrow"
PAPER = "#F4F1E9"
INK = "#172126"
MUTED = "#667078"
RED = ["#6D1E24", "#8D2F34", "#AD4547", "#C76360", "#DB8982", "#E8B4AA"]
BLUE = ["#B5CBE0", "#8DAFCE", "#6693BB", "#4277A4", "#285D8A", "#17436B"]
# Zero is a class boundary, not the midpoint of a neutral class. Thus every
# nonzero swing receives a directional hue, including movements under 2.5 pp.
COLORS = RED + BLUE
BOUNDS = np.arange(-30, 35, 5)


def download(url: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "Election-Maps/1.0"})
    with urllib.request.urlopen(request) as response, path.open("wb") as stream:
        while chunk := response.read(1024 * 1024):
            stream.write(chunk)


def census_blocks() -> gpd.GeoDataFrame:
    """Return official block internal points with PL 94-171 voting-age population."""
    CACHE.mkdir(parents=True, exist_ok=True)
    points_path = CACHE / "alabama-2020-block-vap.gpkg"
    if points_path.exists():
        cached = gpd.read_file(points_path)
        if len(cached) < 100_000 or cached.VAP20.sum() < 3_000_000:
            raise ValueError("Cached PL 94-171 block/VAP data are incomplete")
        return cached

    archive = CACHE / "tl_2020_01_tabblock20.zip"
    if not archive.exists():
        download(BLOCK_URL, archive)
    with ZipFile(archive) as zipped, TemporaryDirectory() as temporary:
        zipped.extractall(temporary)
        blocks = gpd.read_file(Path(temporary) / "tl_2020_01_tabblock20.shp")
    points = gpd.GeoDataFrame(
        blocks[["GEOID20", "COUNTYFP20"]].copy(),
        geometry=gpd.points_from_xy(
            pd.to_numeric(blocks.INTPTLON20), pd.to_numeric(blocks.INTPTLAT20)
        ), crs=4326,
    )

    # The public API may require a key for block requests. The official PL
    # state file is keyless and contains the same P3 total-VAP field. In its
    # pipe-delimited segment 2, fields are FILEID, STUSAB, CHARITER, CIFSN,
    # LOGRECNO, then P3_001N. The geography file supplies GEOID by LOGRECNO.
    pl_archive = CACHE / "al2020.pl.zip"
    if not pl_archive.exists():
        download(PL_URL, pl_archive)
    with ZipFile(pl_archive) as zipped:
        geoid_by_logrec = {}
        with zipped.open("algeo2020.pl") as raw:
            for row in csv.reader(io.TextIOWrapper(raw, encoding="latin-1"), delimiter="|"):
                if row[2] == "750":  # Census block summary level
                    geoid_by_logrec[row[7]] = row[9]
        records = []
        with zipped.open("al000022020.pl") as raw:
            for row in csv.reader(io.TextIOWrapper(raw, encoding="latin-1"), delimiter="|"):
                geoid = geoid_by_logrec.get(row[4])
                if geoid:
                    records.append((geoid, int(row[5])))
    vap = pd.DataFrame(records, columns=["GEOID20", "VAP20"])
    points = points.merge(vap[["GEOID20", "VAP20"]], on="GEOID20", validate="one_to_one")
    if len(points) < 100_000 or points.VAP20.sum() < 3_000_000:
        raise ValueError("PL 94-171 block/VAP linkage is unexpectedly incomplete")
    points.to_file(points_path, driver="GPKG", layer="block_internal_points")
    return points


def load_precincts() -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    p16 = gpd.read_file(SOURCE16)[
        ["COUNTYFP20", "GEOID16", "NAME16", "G16PREDCLI", "G16PRERTRU", "geometry"]
    ].rename(columns={"COUNTYFP20": "county_fips"}).to_crs(EA)
    p24 = gpd.read_file(TARGET24)[
        ["COUNTYFP", "UNIQUE_ID", "County", "Precinct", "G24PREDHAR", "G24PRERTRU", "geometry"]
    ].rename(columns={"COUNTYFP": "county_fips"}).to_crs(EA)
    p16["county_fips"] = p16.county_fips.astype(str).str.zfill(3)
    p24["county_fips"] = p24.county_fips.astype(str).str.zfill(3)
    p16 = p16.reset_index(drop=True).reset_index(names="i16")
    p24 = p24.reset_index(drop=True).reset_index(names="i24")
    return p16, p24


def polygon_intersections(p16: gpd.GeoDataFrame, p24: gpd.GeoDataFrame) -> pd.DataFrame:
    intersections = gpd.overlay(
        p16[["i16", "county_fips", "geometry"]],
        p24[["i24", "county_fips", "geometry"]],
        how="intersection", keep_geom_type=False,
    )
    # Enforce the administrative invariant even if source polygons contain slivers.
    intersections = intersections[
        intersections.county_fips_1.eq(intersections.county_fips_2)
    ].copy()
    intersections["intersection_area"] = intersections.geometry.area
    area16 = p16.set_index("i16").geometry.area
    area24 = p24.set_index("i24").geometry.area
    intersections["share16"] = intersections.intersection_area / intersections.i16.map(area16)
    intersections["share24"] = intersections.intersection_area / intersections.i24.map(area24)
    return pd.DataFrame(intersections.drop(columns="geometry"))


def exact_pairs(intersections: pd.DataFrame) -> pd.DataFrame:
    best16 = intersections.loc[
        intersections.groupby("i16").share16.idxmax(), ["i16", "i24", "share16", "share24"]
    ]
    best24 = intersections.loc[
        intersections.groupby("i24").share24.idxmax(), ["i24", "i16"]
    ].rename(columns={"i16": "back16"})
    paired = best16.merge(best24, on="i24")
    return paired[(paired.i16.eq(paired.back16)) & (paired.share16.ge(.99))
                  & (paired.share24.ge(.99))][["i16", "i24"]]


def allocate(p16: gpd.GeoDataFrame, p24: gpd.GeoDataFrame,
             intersections: pd.DataFrame, blocks: gpd.GeoDataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    exact = exact_pairs(intersections)
    exact_sources = set(exact.i16)
    exact_weights = exact.assign(weight=1.0, method="exact_geometry")

    changed = p16[~p16.i16.isin(exact_sources)][["i16", "county_fips", "geometry"]]
    block_points = blocks.to_crs(EA)[["VAP20", "geometry"]]
    with_source = gpd.sjoin(block_points, changed, how="inner", predicate="within")[
        ["VAP20", "i16", "county_fips", "geometry"]
    ]
    with_both = gpd.sjoin(
        with_source, p24[["i24", "county_fips", "geometry"]], how="inner", predicate="within",
        lsuffix="block", rsuffix="target",
    )
    with_both = with_both[with_both.county_fips_block.eq(with_both.county_fips_target)]
    pop_pairs = with_both.groupby(["i16", "i24"], as_index=False).VAP20.sum()
    pop_totals = pop_pairs.groupby("i16").VAP20.transform("sum")
    pop_weights = pop_pairs[pop_totals.gt(0)].copy()
    pop_weights["weight"] = pop_weights.VAP20 / pop_totals[pop_totals.gt(0)]
    pop_weights["method"] = "2020_block_vap"

    covered = set(pop_weights.i16)
    fallback_sources = set(changed.i16) - covered
    if len(fallback_sources) > 100:
        raise ValueError("Too many changed precincts lack block VAP; refusing area fallback")
    area = intersections[intersections.i16.isin(fallback_sources)].copy()
    area_total = area.groupby("i16").intersection_area.transform("sum")
    area["weight"] = area.intersection_area / area_total
    area["method"] = "polygon_area_fallback"
    weights = pd.concat([
        exact_weights[["i16", "i24", "weight", "method"]],
        pop_weights[["i16", "i24", "weight", "method"]],
        area[["i16", "i24", "weight", "method"]],
    ], ignore_index=True)
    sums = weights.groupby("i16").weight.sum()
    if len(sums) != len(p16) or not np.allclose(sums, 1):
        raise ValueError("Every 2016 precinct must have crosswalk weights summing to one")

    crosswalk = (weights.merge(
        p16[["i16", "county_fips", "GEOID16", "NAME16", "G16PREDCLI", "G16PRERTRU"]], on="i16"
    ).merge(
        p24[["i24", "UNIQUE_ID", "County", "Precinct"]], on="i24"
    ).merge(
        intersections[["i16", "i24", "share16", "share24"]], on=["i16", "i24"], how="left"
    ))
    crosswalk["allocated_clinton"] = crosswalk.weight * crosswalk.G16PREDCLI
    crosswalk["allocated_trump"] = crosswalk.weight * crosswalk.G16PRERTRU

    reconstructed = crosswalk.groupby("i24", as_index=False).agg(
        clinton_2016=("allocated_clinton", "sum"),
        trump_2016=("allocated_trump", "sum"),
        source_precincts=("i16", "nunique"),
    )
    meaningful = intersections[(intersections.share16.ge(.005)) | (intersections.share24.ge(.005))]
    source_degree = meaningful.groupby("i16").i24.nunique()
    target_degree = meaningful.groupby("i24").i16.nunique()
    exact_targets = set(exact.i24)
    quality = []
    for target in p24.i24:
        sources = meaningful.loc[meaningful.i24.eq(target), "i16"].unique()
        if target in exact_targets:
            quality.append("Exact geometry")
        elif len(sources) == 1 and source_degree.get(sources[0], 0) > 1:
            quality.append("Split allocation")
        elif len(sources) > 1 and all(source_degree.get(source, 0) == 1 for source in sources):
            quality.append("Merged precincts")
        else:
            quality.append("Complex change")
    reconstructed["crosswalk_quality"] = reconstructed.i24.map(dict(zip(p24.i24, quality)))
    return crosswalk, reconstructed


def validate(p16: gpd.GeoDataFrame, frame: gpd.GeoDataFrame,
             crosswalk: pd.DataFrame) -> dict:
    source = p16.groupby("county_fips")[["G16PREDCLI", "G16PRERTRU"]].sum()
    allocated = crosswalk.groupby("county_fips")[["allocated_clinton", "allocated_trump"]].sum()
    errors = pd.DataFrame({
        "clinton": allocated.allocated_clinton - source.G16PREDCLI,
        "trump": allocated.allocated_trump - source.G16PRERTRU,
    })
    if errors.abs().to_numpy().max() > 1e-6:
        raise ValueError("Allocated votes fail county reconciliation")
    return {
        "source_2016_precincts": int(len(p16)),
        "target_2024_precincts": int(len(frame)),
        "crosswalk_rows": int(len(crosswalk)),
        "weight_sum_min": float(crosswalk.groupby("i16").weight.sum().min()),
        "weight_sum_max": float(crosswalk.groupby("i16").weight.sum().max()),
        "maximum_county_vote_error": float(errors.abs().to_numpy().max()),
        "quality_counts": frame.crosswalk_quality.value_counts().to_dict(),
        "allocation_method_counts": crosswalk.method.value_counts().to_dict(),
        "statewide_2016_clinton": int(p16.G16PREDCLI.sum()),
        "statewide_2016_trump": int(p16.G16PRERTRU.sum()),
        "statewide_2024_harris": int(frame.G24PREDHAR.sum()),
        "statewide_2024_trump": int(frame.G24PRERTRU.sum()),
    }


def map_linework(ax, frame: gpd.GeoDataFrame) -> None:
    counties = frame.dissolve("County").geometry.boundary.union_all()
    gpd.GeoSeries([counties], crs=frame.crs).plot(ax=ax, color="#586267", linewidth=.42, zorder=3)
    state = frame.geometry.union_all()
    parts = list(state.geoms) if state.geom_type == "MultiPolygon" else [state]
    gpd.GeoSeries([part.exterior for part in parts], crs=frame.crs).plot(
        ax=ax, color=INK, linewidth=1.2, zorder=4
    )
    ax.set_axis_off(); ax.set_aspect("equal"); ax.margins(.006)


def draw_swing(frame: gpd.GeoDataFrame) -> None:
    cmap = ListedColormap(COLORS)
    norm = BoundaryNorm(BOUNDS, cmap.N, clip=True)
    fig = plt.figure(figsize=(10.5, 12), facecolor=PAPER)
    ax = fig.add_axes([.06, .19, .88, .67])
    frame.plot(ax=ax, column="swing_pp", cmap=cmap, norm=norm,
               edgecolor="#F7F4ED", linewidth=.13,
               missing_kwds={"color": "#AAA9A3", "edgecolor": "#F7F4ED"})
    map_linework(ax, frame)
    fig.text(.06, .945, "Alabama Presidential Swing by Precinct, 2016–2024",
             family=SERIF, fontsize=25, weight="bold", color=INK)
    fig.text(.06, .913, "Change in Democratic two-party vote share, shown on 2024 precinct boundaries",
             family=SERIF, fontsize=12.5, color=MUTED)
    fig.add_artist(Rectangle((.06, .889), .88, .002, transform=fig.transFigure,
                             facecolor=INK, edgecolor="none"))

    legend = fig.add_axes([.10, .105, .80, .055]); legend.axis("off")
    for index, color in enumerate(COLORS):
        legend.add_patch(Rectangle((index / len(COLORS), .42), 1 / len(COLORS), .28,
                                   transform=legend.transAxes, color=color, ec=PAPER, lw=.4))
    labels = ["R 25+", "R 20–25", "R 15–20", "R 10–15", "R 5–10", "R 0–5",
              "D 0–5", "D 5–10", "D 10–15", "D 15–20", "D 20–25", "D 25+"]
    for index, label in enumerate(labels):
        legend.text((index + .5) / len(labels), .28, label, ha="center", va="top",
                    family=SANS, fontsize=7.3, color=INK)
    legend.text(0, .86, "REPUBLICAN SWING", family=SANS, fontsize=8.5, weight="bold", color=RED[1])
    legend.text(1, .86, "DEMOCRATIC SWING", ha="right", family=SANS, fontsize=8.5,
                weight="bold", color=BLUE[-2])

    statewide16 = frame.clinton_2016.sum() / (frame.clinton_2016.sum() + frame.trump_2016.sum())
    statewide24 = frame.G24PREDHAR.sum() / (frame.G24PREDHAR.sum() + frame.G24PRERTRU.sum())
    fig.text(.06, .067, f"Statewide Democratic two-party share: {statewide16:.1%} in 2016 · "
             f"{statewide24:.1%} in 2024 · swing {100*(statewide24-statewide16):+.1f} points",
             family=SERIF, fontsize=10.5, color=INK)
    fig.text(.06, .035, "2016 results are exact for unchanged precincts; changed boundaries use 2020 Census "
             "block voting-age population. Five-point intervals divide at zero.", family=SERIF,
             fontsize=8.8, color=MUTED)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT / "alabama-presidential-swing-2016-2024.png", dpi=240,
                facecolor=PAPER, bbox_inches="tight")
    fig.savefig(OUTPUT / "alabama-presidential-swing-2016-2024.svg",
                facecolor=PAPER, bbox_inches="tight")
    plt.close(fig)


def draw_quality(frame: gpd.GeoDataFrame) -> None:
    palette = {"Exact geometry": "#D8D4C8", "Merged precincts": "#6D9A8D",
               "Split allocation": "#D0A45A", "Complex change": "#A45454"}
    fig = plt.figure(figsize=(10.5, 12), facecolor=PAPER)
    ax = fig.add_axes([.06, .17, .88, .70])
    frame.plot(ax=ax, color=frame.crosswalk_quality.map(palette),
               edgecolor="#F8F5EF", linewidth=.14)
    map_linework(ax, frame)
    fig.text(.06, .945, "2016–2024 Precinct Crosswalk Quality", family=SERIF,
             fontsize=25, weight="bold", color=INK)
    fig.text(.06, .913, "Classification of 2024 precincts by the boundary relationship used",
             family=SERIF, fontsize=12.5, color=MUTED)
    handles = [Patch(facecolor=color, label=f"{label} · {(frame.crosswalk_quality == label).sum():,}")
               for label, color in palette.items()]
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(.5, .07), ncol=2,
               frameon=False, prop={"family": SERIF, "size": 10}, labelcolor=INK)
    fig.text(.06, .035, "Exact geometry requires reciprocal overlap of at least 99%. Split and complex "
             "units use Census block VAP; merges sum their source results.", family=SERIF,
             fontsize=8.8, color=MUTED)
    fig.savefig(OUTPUT / "alabama-presidential-swing-crosswalk-quality.png", dpi=240,
                facecolor=PAPER, bbox_inches="tight")
    fig.savefig(OUTPUT / "alabama-presidential-swing-crosswalk-quality.svg",
                facecolor=PAPER, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    p16, p24 = load_precincts()
    intersections = polygon_intersections(p16, p24)
    crosswalk, reconstructed = allocate(p16, p24, intersections, census_blocks())
    frame = p24.merge(reconstructed, on="i24", validate="one_to_one")
    frame["dem_share_2016"] = frame.clinton_2016 / (frame.clinton_2016 + frame.trump_2016)
    frame["dem_share_2024"] = frame.G24PREDHAR / (frame.G24PREDHAR + frame.G24PRERTRU)
    frame["swing_pp"] = 100 * (frame.dem_share_2024 - frame.dem_share_2016)
    audit = validate(p16, frame, crosswalk)
    export = frame.to_crs(4326)
    export.to_file(OUTPUT / "alabama-presidential-swing-2016-2024.gpkg",
                   layer="precinct_swing", driver="GPKG")
    crosswalk.to_csv(OUTPUT / "alabama-2016-to-2024-precinct-crosswalk.csv", index=False)
    pd.DataFrame({"break_lower": BOUNDS[:-1], "break_upper": BOUNDS[1:],
                  "color": COLORS}).to_csv(OUTPUT / "swing-color-breaks.csv", index=False)
    (OUTPUT / "crosswalk-audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    draw_swing(frame)
    draw_quality(frame)
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
