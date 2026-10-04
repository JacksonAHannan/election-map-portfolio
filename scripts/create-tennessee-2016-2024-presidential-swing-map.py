"""Crosswalk Tennessee 2016 presidential returns to 2024 precincts and map swing."""

from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

import geopandas as gpd
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.patches import Rectangle


ROOT = Path(__file__).resolve().parents[1]
SOURCE16 = ROOT / "tennessee/data/tn_vest_16/tn_vest_16.shp"
TARGET24 = (ROOT / "tennessee/data/tn_2024_gen_prec/tn_2024_gen_all_prec"
            / "tn_2024_gen_all_prec.shp")
CACHE = ROOT / "tennessee/data/census-2020-blocks"
BLOCK_ARCHIVE = CACHE / "tl_2020_47_tabblock20.zip"
PL_ARCHIVE = CACHE / "tn2020.pl.zip"
OUTPUT = ROOT / "outputs/tennessee-2016-2024-presidential-swing"

EA = 5070
SERIF = "Nimbus Roman"
SANS = "Nimbus Sans Narrow"
PAPER = "#F4F1E9"
HEADER = "#172329"
INK = "#172126"
MUTED = "#667078"
MISSING = "#AAA9A3"
GOLD = "#E2B13C"
RED = ["#6D1E24", "#8D2F34", "#AD4547", "#C76360", "#DB8982", "#E8B4AA"]
BLUE = ["#B5CBE0", "#8DAFCE", "#6693BB", "#4277A4", "#285D8A", "#17436B"]
COLORS = RED + BLUE
BOUNDS = np.arange(-30, 35, 5)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def census_blocks() -> gpd.GeoDataFrame:
    """Return official 2020 block internal points with PL voting-age population."""
    cache = CACHE / "tennessee-2020-block-vap.gpkg"
    if cache.exists():
        points = gpd.read_file(cache)
        if len(points) < 170_000 or points.VAP20.sum() < 5_000_000:
            raise ValueError("Cached Tennessee block/VAP file is incomplete")
        return points
    if not BLOCK_ARCHIVE.exists() or not PL_ARCHIVE.exists():
        raise FileNotFoundError("Official Census block geometry and Tennessee PL archives are required")

    with ZipFile(BLOCK_ARCHIVE) as zipped, TemporaryDirectory() as temporary:
        zipped.extractall(temporary)
        blocks = gpd.read_file(Path(temporary) / "tl_2020_47_tabblock20.shp")
    points = gpd.GeoDataFrame(
        blocks[["GEOID20", "COUNTYFP20"]].copy(),
        geometry=gpd.points_from_xy(
            pd.to_numeric(blocks.INTPTLON20), pd.to_numeric(blocks.INTPTLAT20)
        ), crs=4326,
    )
    with ZipFile(PL_ARCHIVE) as zipped:
        geoid_by_logrec = {}
        with zipped.open("tngeo2020.pl") as raw:
            for row in csv.reader(io.TextIOWrapper(raw, encoding="latin-1"), delimiter="|"):
                if row[2] == "750":
                    geoid_by_logrec[row[7]] = row[9]
        records = []
        with zipped.open("tn000022020.pl") as raw:
            for row in csv.reader(io.TextIOWrapper(raw, encoding="latin-1"), delimiter="|"):
                geoid = geoid_by_logrec.get(row[4])
                if geoid:
                    records.append((geoid, int(row[5])))
    vap = pd.DataFrame(records, columns=["GEOID20", "VAP20"])
    points = points.merge(vap, on="GEOID20", validate="one_to_one")
    if len(points) < 170_000 or points.VAP20.sum() < 5_000_000:
        raise ValueError("Tennessee PL block/VAP linkage is unexpectedly incomplete")
    points.to_file(cache, driver="GPKG", layer="block_internal_points")
    return points


def load_precincts() -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    p16 = gpd.read_file(SOURCE16)[
        ["COUNTYFP", "VTD", "NAME", "G16PREDCLI", "G16PRERTRU", "geometry"]
    ].rename(columns={"COUNTYFP": "county_fips", "VTD": "source_id", "NAME": "source_name"})
    p24 = gpd.read_file(TARGET24)[
        ["COUNTYFP", "UNIQUE_ID", "County", "Precinct", "G24PREDHAR", "G24PRERTRU", "geometry"]
    ].rename(columns={"COUNTYFP": "county_fips"})
    for label, frame in (("2016", p16), ("2024", p24)):
        if frame.crs is None or frame.geometry.isna().any() or frame.geometry.is_empty.any():
            raise ValueError(f"{label} precinct geometry requires a CRS and nonempty features")
        if (~frame.is_valid).any():
            raise ValueError(f"{label} precinct geometry contains invalid features")
    p16 = p16.to_crs(EA).reset_index(drop=True).reset_index(names="i16")
    p24 = p24.to_crs(EA).reset_index(drop=True).reset_index(names="i24")
    p16["county_fips"] = p16.county_fips.astype(str).str.zfill(3)
    p24["county_fips"] = p24.county_fips.astype(str).str.zfill(3)
    if p16.i16.duplicated().any() or p24.i24.duplicated().any() or p24.UNIQUE_ID.duplicated().any():
        raise ValueError("Precinct identifiers must be unique")
    return p16, p24


def polygon_intersections(p16: gpd.GeoDataFrame, p24: gpd.GeoDataFrame) -> pd.DataFrame:
    pieces = []
    for county in sorted(set(p16.county_fips) | set(p24.county_fips)):
        left = p16.loc[p16.county_fips.eq(county), ["i16", "geometry"]]
        right = p24.loc[p24.county_fips.eq(county), ["i24", "geometry"]]
        if left.empty or right.empty:
            continue
        part = gpd.overlay(left, right, how="intersection", keep_geom_type=False)
        part["county_fips"] = county
        pieces.append(part)
    intersections = pd.concat(pieces, ignore_index=True)
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
    return paired[(paired.i16.eq(paired.back16)) & paired.share16.ge(.99)
                  & paired.share24.ge(.99)][["i16", "i24"]]


def allocate(p16, p24, intersections, blocks) -> tuple[pd.DataFrame, pd.DataFrame]:
    exact = exact_pairs(intersections)
    exact_sources = set(exact.i16)
    exact_weights = exact.assign(weight=1.0, method="exact_geometry")

    changed = p16.loc[~p16.i16.isin(exact_sources), ["i16", "county_fips", "geometry"]]
    block_points = blocks.to_crs(EA)[["VAP20", "COUNTYFP20", "geometry"]].copy()
    block_points["county_fips"] = block_points.COUNTYFP20.astype(str).str.zfill(3)
    with_source = gpd.sjoin(
        block_points[["VAP20", "county_fips", "geometry"]], changed,
        how="inner", predicate="within", lsuffix="block", rsuffix="source",
    )
    with_source = with_source[with_source.county_fips_block.eq(with_source.county_fips_source)]
    with_both = gpd.sjoin(
        with_source[["VAP20", "i16", "county_fips_block", "geometry"]],
        p24[["i24", "county_fips", "geometry"]], how="inner", predicate="within",
        lsuffix="block", rsuffix="target",
    )
    with_both = with_both[with_both.county_fips_block.eq(with_both.county_fips)]
    pop_pairs = with_both.groupby(["i16", "i24"], as_index=False).VAP20.sum()
    totals = pop_pairs.groupby("i16").VAP20.transform("sum")
    pop_weights = pop_pairs[totals.gt(0)].copy()
    pop_weights["weight"] = pop_weights.VAP20 / totals[totals.gt(0)]
    pop_weights["method"] = "2020_block_vap"

    uncovered = set(changed.i16) - set(pop_weights.i16)
    if len(uncovered) > 200:
        raise ValueError("Too many changed precincts lack block VAP")
    area = intersections[intersections.i16.isin(uncovered)].copy()
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
        raise ValueError("Every 2016 precinct must have allocation weights summing to one")

    crosswalk = (weights.merge(
        p16[["i16", "county_fips", "source_id", "source_name", "G16PREDCLI", "G16PRERTRU"]], on="i16"
    ).merge(
        p24[["i24", "UNIQUE_ID", "County", "Precinct"]], on="i24"
    ).merge(
        intersections[["i16", "i24", "share16", "share24"]],
        on=["i16", "i24"], how="left"
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
    exact_targets = set(exact.i24)
    quality = {}
    for target in p24.i24:
        sources = meaningful.loc[meaningful.i24.eq(target), "i16"].unique()
        if target in exact_targets:
            quality[target] = "Exact geometry"
        elif len(sources) == 1 and source_degree.get(sources[0], 0) > 1:
            quality[target] = "Split allocation"
        elif len(sources) > 1 and all(source_degree.get(source, 0) == 1 for source in sources):
            quality[target] = "Merged precincts"
        else:
            quality[target] = "Complex change"
    reconstructed["crosswalk_quality"] = reconstructed.i24.map(quality)
    return crosswalk, reconstructed


def validate(p16, frame, crosswalk) -> dict:
    source = p16.groupby("county_fips")[["G16PREDCLI", "G16PRERTRU"]].sum()
    allocated = crosswalk.groupby("county_fips")[["allocated_clinton", "allocated_trump"]].sum()
    errors = pd.DataFrame({
        "clinton": allocated.allocated_clinton - source.G16PREDCLI,
        "trump": allocated.allocated_trump - source.G16PRERTRU,
    })
    if errors.abs().to_numpy().max() > 1e-6:
        raise ValueError("Allocated votes fail county reconciliation")
    share16 = p16.G16PREDCLI.sum() / (p16.G16PREDCLI.sum() + p16.G16PRERTRU.sum())
    share24 = frame.G24PREDHAR.sum() / (frame.G24PREDHAR.sum() + frame.G24PRERTRU.sum())
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
        "statewide_democratic_two_party_share_2016": float(share16),
        "statewide_democratic_two_party_share_2024": float(share24),
        "statewide_democratic_shift_pp": float(100 * (share24 - share16)),
    }


def linework(ax, frame, county_width=.42, state_width=1.2) -> None:
    counties = frame.dissolve("County").boundary
    counties.plot(ax=ax, color="#586267", linewidth=county_width, zorder=4)
    state = frame.geometry.union_all()
    parts = list(state.geoms) if state.geom_type == "MultiPolygon" else [state]
    gpd.GeoSeries([part.exterior for part in parts], crs=frame.crs).plot(
        ax=ax, color=INK, linewidth=state_width, zorder=5
    )
    ax.set_axis_off(); ax.set_aspect("equal")


def draw_data(ax, frame, cmap, norm, edge_width=.14) -> None:
    frame.plot(ax=ax, column="swing_pp", cmap=cmap, norm=norm,
               edgecolor="#F7F4ED", linewidth=edge_width,
               missing_kwds={"color": MISSING, "edgecolor": "#F7F4ED"})
    linework(ax, frame)


def render(frame: gpd.GeoDataFrame, audit: dict) -> None:
    cmap = ListedColormap(COLORS)
    norm = BoundaryNorm(BOUNDS, cmap.N, clip=True)
    fig = plt.figure(figsize=(14, 10), facecolor=PAPER)
    fig.add_artist(Rectangle((.008, .855), .984, .135, transform=fig.transFigure,
                             facecolor=HEADER, edgecolor="none", zorder=-2))
    fig.text(.05, .942, "Tennessee Presidential Shift by Precinct, 2016–2024",
             family=SERIF, fontsize=24, weight="bold", color="white")
    fig.text(.05, .895,
             "Change in Democratic two-party vote share, shown on 2024 precinct boundaries",
             family=SERIF, fontsize=11.3, color="#C8D7DF")

    ax = fig.add_axes([.045, .395, .91, .405])
    draw_data(ax, frame, cmap, norm)
    ax.margins(.006)

    # Tennessee silhouette acts as the gold locator in the title tab.
    locator = fig.add_axes([.815, .888, .155, .070], facecolor=HEADER)
    state = gpd.GeoDataFrame(geometry=[frame.geometry.union_all()], crs=frame.crs)
    state.plot(ax=locator, color=GOLD, edgecolor="white", linewidth=.8)
    locator.set_axis_off(); locator.set_aspect("equal")
    fig.text(.805, .932, "TENNESSEE", family=SANS, fontsize=8.3,
             color="#C8D7DF", weight="bold", ha="right")
    fig.text(.805, .900, "2016–2024", family=SANS, fontsize=9.2,
             color=GOLD, weight="bold", ha="right")

    # Large Nashville-area window, linked to the statewide map.
    center = gpd.GeoSeries(gpd.points_from_xy([-86.77], [36.03]), crs=4326).to_crs(frame.crs).iloc[0]
    half_width, half_height = 66_000, 42_000
    inset = fig.add_axes([.055, .095, .43, .255], facecolor=PAPER)
    draw_data(inset, frame, cmap, norm, edge_width=.30)
    inset.set_xlim(center.x - half_width, center.x + half_width)
    inset.set_ylim(center.y - half_height, center.y + half_height)
    for spine in inset.spines.values():
        spine.set_visible(True); spine.set_color(INK); spine.set_linewidth(.85)
    inset.text(.018, .965, "NASHVILLE–MURFREESBORO AREA", transform=inset.transAxes,
               ha="left", va="top", family=SANS, fontsize=8.5, weight="bold", color=INK,
               bbox={"facecolor": PAPER, "edgecolor": "none", "pad": 2.2, "alpha": .92})
    ax.add_patch(Rectangle((center.x - half_width, center.y - half_height),
                           2 * half_width, 2 * half_height, fill=False,
                           edgecolor="#52666F", linewidth=.58,
                           linestyle=(0, (3, 2)), zorder=7))

    cax = fig.add_axes([.875, .105, .022, .235])
    scalar = matplotlib.cm.ScalarMappable(norm=norm, cmap=cmap)
    cbar = fig.colorbar(scalar, cax=cax, boundaries=BOUNDS,
                        ticks=np.arange(-30, 31, 5), spacing="uniform")
    cbar.outline.set_edgecolor("#A9A69F"); cbar.outline.set_linewidth(.6)
    cbar.ax.tick_params(labelsize=8.3, length=3, color=MUTED)
    cbar.ax.set_yticklabels(
        ["R +30", "R +25", "R +20", "R +15", "R +10", "R +5", "0",
         "D +5", "D +10", "D +15", "D +20", "D +25", "D +30"], family=SANS
    )
    fig.text(.842, .365, "PRESIDENTIAL\nSHIFT", family=SANS, fontsize=8.5,
             weight="bold", color=MUTED, linespacing=1.2)
    fig.text(.842, .065, "Five-point bands\ndivide at zero.", family=SERIF,
             fontsize=8, color=MUTED, linespacing=1.35)

    shift = audit["statewide_democratic_shift_pp"]
    direction = "D" if shift >= 0 else "R"
    fig.text(.545, .280, "STATEWIDE TWO-PARTY SHIFT", family=SANS,
             fontsize=8.7, weight="bold", color=MUTED)
    fig.text(.545, .215, f"{direction} +{abs(shift):.1f}", family=SERIF, fontsize=27,
             weight="bold", color=BLUE[-2] if shift >= 0 else RED[1])
    fig.text(.545, .165,
             f"Democratic share: {audit['statewide_democratic_two_party_share_2016']:.1%} in 2016 · "
             f"{audit['statewide_democratic_two_party_share_2024']:.1%} in 2024",
             family=SERIF, fontsize=10, color=INK)

    fig.text(.05, .036,
             "Sources: Tennessee Secretary of State; VEST/RDH precinct boundaries and results; 2020 Census PL 94-171.",
             family=SERIF, fontsize=8.1, color=MUTED)
    fig.text(.95, .036,
             "Shift = change in Democratic two-party presidential vote share.",
             ha="right", family=SERIF, fontsize=8.1, color=MUTED)
    fig.text(.05, .014,
             "Changed 2016 precincts are allocated to 2024 geography using 2020 block voting-age population; gray indicates no two-party vote.",
             family=SERIF, fontsize=7.8, color=MUTED)

    OUTPUT.mkdir(parents=True, exist_ok=True)
    base = OUTPUT / "tennessee-presidential-shift-2016-2024"
    fig.savefig(base.with_suffix(".png"), dpi=240, facecolor=PAPER)
    fig.savefig(base.with_suffix(".svg"), facecolor=PAPER)
    plt.close(fig)


def write_spec(audit: dict) -> None:
    spec = {
        "title": "Tennessee Presidential Shift by Precinct, 2016–2024",
        "claim": "Show the change in Democratic two-party presidential vote share on 2024 precinct boundaries.",
        "data": {
            "source_2016": "VEST/RDH Tennessee 2016 precinct and election results",
            "source_2024": "RDH Tennessee 2024 general election precinct results and boundaries; Tennessee Secretary of State results",
            "variable": "2024 Harris two-party share minus 2016 Clinton two-party share",
            "unit": "percentage-point Democratic shift",
            "denominator": "Democratic plus Republican presidential votes",
        },
        "geometry": {
            "source": str(TARGET24.relative_to(ROOT)),
            "vintage": "2024 general-election reporting precincts",
            "unit": "precinct",
            "join_key": "2024 UNIQUE_ID; 2016 votes transferred by spatial crosswalk",
            "crs": "EPSG:5070 analysis; source output reprojected to EPSG:4326",
            "source_2016_sha256": sha256(ROOT / "tennessee/tn_vest_16.zip"),
            "source_2024_sha256": sha256(ROOT / "tennessee/tn_2024_gen_prec.zip"),
        },
        "classification": {"method": "fixed diverging", "center": 0,
                           "breaks": BOUNDS.tolist(), "clip": [-30, 30]},
        "style": {"palette": COLORS, "missing_color": MISSING,
                  "font_family": f"{SERIF}; {SANS}"},
        "layout": {"width_inches": 14, "height_inches": 10,
                   "extent": "Tennessee",
                   "insets": ["Nashville–Murfreesboro, 132 km by 84 km",
                              "gold Tennessee silhouette in title tab"]},
        "context_layers": ["county boundaries", "state boundary", "metro locator rectangle"],
        "outputs": ["tennessee-presidential-shift-2016-2024.png",
                    "tennessee-presidential-shift-2016-2024.svg",
                    "tennessee-presidential-swing-2016-2024.gpkg",
                    "tennessee-2016-to-2024-precinct-crosswalk.csv"],
        "software_versions": {"geopandas": gpd.__version__, "pandas": pd.__version__,
                              "matplotlib": matplotlib.__version__},
        "audit_summary": audit,
    }
    (OUTPUT / "map_spec.json").write_text(json.dumps(spec, indent=2) + "\n")


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
    frame.to_crs(4326).to_file(
        OUTPUT / "tennessee-presidential-swing-2016-2024.gpkg",
        layer="precinct_swing", driver="GPKG"
    )
    crosswalk.to_csv(OUTPUT / "tennessee-2016-to-2024-precinct-crosswalk.csv", index=False)
    pd.DataFrame({"break_lower": BOUNDS[:-1], "break_upper": BOUNDS[1:],
                  "color": COLORS}).to_csv(OUTPUT / "swing-color-breaks.csv", index=False)
    (OUTPUT / "crosswalk-audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    render(frame, audit)
    write_spec(audit)
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
