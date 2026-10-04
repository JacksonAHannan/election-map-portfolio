"""Create a standalone 2017 Alabama Jones–Moore special-election margin map."""

from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import BoundaryNorm, LinearSegmentedColormap, ListedColormap
from matplotlib.patches import Rectangle


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "alabama/data/geospatial/election-precincts/al-vest-17.zip"
OUTPUT = ROOT / "outputs/alabama-2017-senate-special-election"
PAPER = "#F4F1E9"
INK = "#182329"
MUTED = "#677178"
DEM = "#286AA3"
REP = "#B54B48"
MISSING = "#AAA9A3"
SERIF = "Nimbus Roman"
SANS = "Nimbus Sans Narrow"
EA = 5070


def load_data() -> gpd.GeoDataFrame:
    frame = gpd.read_file(f"zip://{SOURCE}!al_2017.shp").to_crs(EA)
    required = {"COUNTYFP20", "GEOID17", "NAME17", "S17USSDJON", "S17USSRMOO", "geometry"}
    if missing := required - set(frame.columns):
        raise ValueError(f"Missing source fields: {sorted(missing)}")
    if frame.GEOID17.duplicated().any():
        raise ValueError("2017 precinct GEOIDs must be unique")
    if frame.geometry.isna().any() or frame.geometry.is_empty.any():
        raise ValueError("2017 precinct geometry is incomplete")
    repaired = int((~frame.geometry.is_valid).sum())
    if repaired:
        frame.geometry = frame.geometry.make_valid()
    frame.geometry = frame.geometry.simplify(10, preserve_topology=True)
    if (~frame.geometry.is_valid).any():
        raise ValueError("2017 geometry remains invalid after repair")
    frame.attrs["geometry_repaired"] = repaired
    frame["COUNTYFP20"] = frame.COUNTYFP20.astype(str).str.zfill(3)
    frame["jones"] = pd.to_numeric(frame.S17USSDJON, errors="raise")
    frame["moore"] = pd.to_numeric(frame.S17USSRMOO, errors="raise")
    total = frame.jones + frame.moore
    frame["jones_margin_pp"] = np.divide(
        frame.jones - frame.moore, total,
        out=np.full(len(frame), np.nan), where=total.to_numpy() > 0,
    ) * 100
    return frame


def palette() -> tuple[ListedColormap, BoundaryNorm, np.ndarray]:
    red = LinearSegmentedColormap.from_list("moore_red", ["#6F2025", "#EAB8AE"])
    blue = LinearSegmentedColormap.from_list("jones_blue", ["#B8CEE2", "#17466F"])
    colors = [red(x) for x in np.linspace(0, 1, 20)] + [blue(x) for x in np.linspace(0, 1, 20)]
    bounds = np.arange(-100, 105, 5)
    cmap = ListedColormap(colors)
    return cmap, BoundaryNorm(bounds, cmap.N, clip=True), bounds


def linework(ax, frame: gpd.GeoDataFrame) -> None:
    counties = frame.dissolve("COUNTYFP20").geometry.boundary.union_all()
    gpd.GeoSeries([counties], crs=frame.crs).plot(
        ax=ax, color="#697278", linewidth=.42, alpha=.72, zorder=4
    )
    state = frame.geometry.union_all()
    parts = list(state.geoms) if state.geom_type == "MultiPolygon" else [state]
    gpd.GeoSeries([part.exterior for part in parts], crs=frame.crs).plot(
        ax=ax, color=INK, linewidth=1.25, zorder=5
    )
    ax.set_axis_off(); ax.set_aspect("equal"); ax.margins(.008)


def render(frame: gpd.GeoDataFrame) -> list[dict]:
    cmap, norm, bounds = palette()
    fig = plt.figure(figsize=(14, 12), facecolor=PAPER)
    fig.text(.04, .948, "Alabama U.S. Senate Special Election Margin by Precinct",
             family=SERIF, fontsize=24, weight="bold", color=INK)
    fig.text(.04, .912, "Doug Jones margin over Roy Moore · December 12, 2017",
             family=SERIF, fontsize=11.5, color=MUTED)
    fig.add_artist(plt.Line2D([.04, .96], [.886, .886], transform=fig.transFigure,
                              color=INK, linewidth=1.1))
    ax = fig.add_axes([.31, .14, .49, .72])
    frame.plot(ax=ax, column="jones_margin_pp", cmap=cmap, norm=norm,
               edgecolor="#F7F4ED", linewidth=.15,
               missing_kwds={"color": MISSING, "edgecolor": "#F7F4ED"})
    linework(ax, frame)

    metro_lonlat = {
        "HUNTSVILLE": (-86.5861, 34.7304),
        "BIRMINGHAM": (-86.8025, 33.5207),
        "MONTGOMERY": (-86.3000, 32.3777),
        "MOBILE": (-88.0431, 30.6954),
    }
    centers = gpd.GeoSeries(
        gpd.points_from_xy([p[0] for p in metro_lonlat.values()],
                           [p[1] for p in metro_lonlat.values()]), crs=4326
    ).to_crs(frame.crs)
    fig.text(.04, .867, "METRO WINDOWS · IDENTICAL SCALE", family=SANS,
             fontsize=8.5, weight="bold", color=MUTED)
    counties = frame.dissolve("COUNTYFP20").geometry.boundary.union_all()
    windows = []
    half_width, half_height = 35_000, 20_000
    for (name, _), center, bottom in zip(metro_lonlat.items(), centers, [.685, .495, .305, .115]):
        inset = fig.add_axes([.04, bottom, .245, .17], facecolor=PAPER)
        frame.plot(ax=inset, column="jones_margin_pp", cmap=cmap, norm=norm,
                   edgecolor="#F7F4ED", linewidth=.22,
                   missing_kwds={"color": MISSING, "edgecolor": "#F7F4ED"})
        gpd.GeoSeries([counties], crs=frame.crs).plot(
            ax=inset, color="#59636A", linewidth=.55, alpha=.78, zorder=3
        )
        inset.set_xlim(center.x - half_width, center.x + half_width)
        inset.set_ylim(center.y - half_height, center.y + half_height)
        inset.set_aspect("equal", adjustable="box")
        inset.set_xticks([]); inset.set_yticks([])
        for spine in inset.spines.values():
            spine.set_visible(True); spine.set_color(INK); spine.set_linewidth(.85)
        inset.text(.025, .955, name, transform=inset.transAxes, ha="left", va="top",
                   family=SANS, fontsize=8.8, weight="bold", color=INK,
                   bbox={"facecolor": PAPER, "edgecolor": "none", "pad": 2.2, "alpha": .92})
        ax.add_patch(Rectangle((center.x - half_width, center.y - half_height),
                               2 * half_width, 2 * half_height, fill=False,
                               edgecolor="#39464D", linewidth=.65, zorder=6))
        windows.append({"name": name, "center": [center.x, center.y],
                        "width_m": 2 * half_width, "height_m": 2 * half_height})

    cax = fig.add_axes([.84, .30, .022, .44])
    scalar = matplotlib.cm.ScalarMappable(norm=norm, cmap=cmap)
    cbar = fig.colorbar(scalar, cax=cax, orientation="vertical", boundaries=bounds,
                        ticks=np.arange(-100, 101, 20), spacing="uniform")
    cbar.outline.set_edgecolor("#A9A69F"); cbar.outline.set_linewidth(.6)
    cbar.ax.tick_params(labelsize=8, length=3, color=MUTED)
    cbar.ax.set_yticklabels(
        ["MOORE +100", "MOORE +80", "MOORE +60", "MOORE +40", "MOORE +20", "0",
         "JONES +20", "JONES +40", "JONES +60", "JONES +80", "JONES +100"], family=SANS
    )
    fig.text(.81, .77, "TWO-CANDIDATE\nMARGIN", family=SANS, fontsize=8.5,
             weight="bold", color=MUTED, linespacing=1.25)
    fig.text(.81, .235, "Five-point bands\ndivide at zero.", family=SERIF,
             fontsize=8, color=MUTED, linespacing=1.35)
    fig.text(.81, .198, "Gray = no Jones–Moore votes.", family=SERIF,
             fontsize=7.7, color=MUTED)

    jones = int(frame.jones.sum()); moore = int(frame.moore.sum())
    margin = 100 * (jones - moore) / (jones + moore)
    fig.text(.31, .102, "STATEWIDE U.S. SENATE MARGIN", family=SANS, fontsize=8.5,
             weight="bold", color=MUTED)
    fig.text(.31, .066, f"JONES +{margin:.1f}", family=SERIF, fontsize=20,
             weight="bold", color=DEM)
    fig.text(.96, .068, "Margin = Jones minus Moore share of their combined vote.",
             ha="right", family=SERIF, fontsize=8.2, color=MUTED)
    fig.text(.04, .031,
             "Source: VEST 2017 Alabama precinct returns and boundaries. Write-in votes are excluded from margins.",
             family=SERIF, fontsize=8, color=MUTED)
    base = OUTPUT / "alabama-2017-senate-special-election-margin-by-precinct"
    fig.savefig(base.with_suffix(".png"), dpi=220, facecolor=PAPER)
    fig.savefig(base.with_suffix(".svg"), facecolor=PAPER)
    plt.close(fig)
    return windows


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    frame = load_data()
    windows = render(frame)
    jones = int(frame.jones.sum()); moore = int(frame.moore.sum())
    writeins = int(frame.S17USSOWRI.sum())
    total = frame.jones + frame.moore
    spec = {
        "title": "2017 Alabama U.S. Senate special election margin by precinct",
        "claim": "Show the two-candidate geographic margin between Doug Jones and Roy Moore.",
        "data": {"source": str(SOURCE.relative_to(ROOT)), "vintage": "2017-12-12",
                 "variable": "100 * (Jones - Moore) / (Jones + Moore)",
                 "unit": "percentage-point margin", "denominator": "Jones plus Moore votes",
                 "votes": {"jones": jones, "moore": moore, "write_in_excluded": writeins}},
        "geometry": {"source": str(SOURCE.relative_to(ROOT)), "vintage": "2017 precinct",
                     "unit": "precinct/VTD", "join_key": "embedded VEST returns",
                     "crs": str(frame.crs), "features": int(len(frame)),
                     "valid_features": int(frame.geometry.is_valid.sum()),
                     "features_repaired_after_projection": frame.attrs["geometry_repaired"],
                     "render_simplification_metres": 10},
        "classification": {"method": "fixed diverging", "center": 0,
                           "breaks": np.arange(-100, 105, 5).tolist(),
                           "clip": [-100, 100], "neutral_class": False,
                           "missing_features": int(total.eq(0).sum())},
        "style": {"missing_color": MISSING, "font_family": f"{SERIF}; {SANS}",
                  "line_widths": {"precinct": .15, "county": .42, "state": 1.25}},
        "layout": {"width_inches": 14, "height_inches": 12,
                   "metro_windows": windows},
        "outputs": ["alabama-2017-senate-special-election-margin-by-precinct.png",
                    "alabama-2017-senate-special-election-margin-by-precinct.svg"],
        "software_versions": {"geopandas": gpd.__version__, "pandas": pd.__version__,
                              "matplotlib": matplotlib.__version__},
    }
    (OUTPUT / "map_spec.json").write_text(json.dumps(spec, indent=2) + "\n")
    frame.to_crs(4326).to_file(OUTPUT / "alabama-2017-senate-special-election.gpkg",
                               layer="precinct_results", driver="GPKG")
    frame.drop(columns="geometry").to_csv(OUTPUT / "precinct-results.csv", index=False)
    print(json.dumps({"jones": jones, "moore": moore, "write_in": writeins,
                      "margin": 100 * (jones - moore) / (jones + moore),
                      "features": len(frame), "missing": int(total.eq(0).sum())}, indent=2))


if __name__ == "__main__":
    main()
