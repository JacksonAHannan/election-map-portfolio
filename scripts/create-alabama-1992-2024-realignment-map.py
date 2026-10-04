#!/usr/bin/env python3
"""Create a county map of durable Republican presidential realignment in Alabama."""

from __future__ import annotations

import hashlib
import json
import re
import xml.etree.ElementTree as ET
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import geopandas as gpd
import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import Patch


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "alabama/data/election-results/general-precinct"
PRECINCTS = ROOT / "alabama/data/geospatial/election-precincts/al-2024-gen-prec/al-2024-gen-all-prec/al-2024-gen-all-prec.shp"
OUT = ROOT / "outputs/alabama-1992-2024-presidential-realignment"
YEARS = (1992, 1996, 2000, 2004, 2008, 2012, 2016, 2020, 2024)
CANDIDATES = {
    1992: ("clinton", "bush"), 1996: ("clinton", "dole"),
    2000: ("gore", "bush"), 2004: ("kerry", "bush"),
    2008: ("obama", "mccain"), 2012: ("obama", "romney"),
    2016: ("clinton", "trump"), 2020: ("biden", "trump"),
    2024: ("harris", "trump"),
}

ALIASES = {
    "covingto": "Covington", "jefferso": "Jefferson", "lauderd": "Lauderdale",
    "limeston": "Limestone", "montgome": "Montgomery", "stclair": "St. Clair",
    "tallade": "Talladega", "tallapoo": "Tallapoosa", "tuscalo": "Tuscaloosa",
    "washing": "Washington", "wilcox-2000genp": "Wilcox",
    "dekalb": "DeKalb", "st clair": "St. Clair", "radolph": "Randolph",
}

PALETTE = {
    "Republican throughout": "#6f1d1b",
    "1996": "#8f2d21", "2000": "#b5472e", "2004": "#d36b42",
    "2008": "#e68a58", "2012": "#eda66f", "2016": "#f1bd88",
    "2020": "#f4d1a6", "2024": "#f7e4c8",
    "Not Republican by 2024": "#315a86", "Incomplete record": "#c8c5bf",
}


def county_name(path: Path) -> str:
    name = path.name.lower().replace(".xls.xls", "").replace(".xlsx", "").replace(".xls", "")
    name = re.sub(r"^\d{4}-general-", "", name)
    name = re.sub(r"\s*-\s*gen04$", "", name)
    normalized = name.replace("_", " ")
    return ALIASES.get(normalized, normalized.title())


def canonical_county(name: str) -> str:
    normalized = name.strip().lower().replace(".", "")
    return ALIASES.get(normalized, name.strip().title())


def numeric_sum(series: pd.Series) -> float:
    return float(pd.to_numeric(series, errors="coerce").fillna(0).sum())


def candidate_columns(df: pd.DataFrame, dem: str, rep: str, rows: int = 12) -> tuple[int, int]:
    signatures = {
        col: " | ".join(str(v) for v in df.iloc[:rows, col].dropna()).lower()
        for col in range(df.shape[1])
    }
    dcols = [c for c, text in signatures.items() if dem in text]
    rcols = [c for c, text in signatures.items() if rep in text]
    if not dcols or not rcols:
        raise ValueError(f"Candidate columns not found: {dem}/{rep}")
    return dcols[0], rcols[0]


def extract_1992() -> dict[str, tuple[float, float]]:
    out = {}
    folder = DATA / "1992/92g-prec-0/92g-prec"
    for path in folder.glob("*.xls"):
        df = pd.read_excel(path, sheet_name=0, header=None)
        dcol, rcol = candidate_columns(df, "clinton", "bush")
        out[county_name(path)] = (numeric_sum(df.iloc[8:, dcol]), numeric_sum(df.iloc[8:, rcol]))
    return out


def extract_1996() -> dict[str, tuple[float, float]]:
    path = DATA / "1996/96g-prec/96g-prec/1996-compiled-results.xls"
    df = pd.read_excel(path, sheet_name="Summary Statewide Votes", header=1)
    return {
        canonical_county(str(row.iloc[0])): (float(row.iloc[1]), float(row.iloc[3]))
        for _, row in df.iloc[:67].iterrows() if pd.notna(row.iloc[0])
    }


def extract_column_files(year: int, paths: list[Path]) -> dict[str, tuple[float, float]]:
    dem, rep = CANDIDATES[year]
    out = {}
    # The 2000 archive contains reformatted duplicates; shortest paths are originals.
    for path in sorted(paths, key=lambda p: (len(p.parts), len(str(p)))):
        county = county_name(path)
        if county in out:
            continue
        try:
            df = pd.read_excel(path, sheet_name=0, header=None)
            dcol, rcol = candidate_columns(df, dem, rep)
            # Candidate labels occupy the header rows, so coercion safely excludes them.
            out[county] = (numeric_sum(df.iloc[:, dcol]), numeric_sum(df.iloc[:, rcol]))
        except (ValueError, IndexError):
            continue
    return out


def extract_2000() -> dict[str, tuple[float, float]]:
    out = {}
    paths = sorted((DATA / "2000").rglob("*.xls"), key=lambda p: (len(p.parts), len(str(p))))
    for path in paths:
        county = county_name(path)
        if county in out:
            continue
        raw = pd.read_excel(path, sheet_name=0, header=None)
        first_row = {str(value).strip() for value in raw.iloc[0].dropna()}
        if {"ContestTitle", "CandidateName", "NumberVotes"}.issubset(first_row):
            df = pd.read_excel(path, sheet_name=0)
            contest = df["ContestTitle"].astype(str).str.contains("PRESIDENT", case=False, na=False)
            names = df["CandidateName"].astype(str)
            dem = numeric_sum(df.loc[contest & names.str.contains("GORE", case=False, na=False), "NumberVotes"])
            rep = numeric_sum(df.loc[contest & names.str.contains("BUSH", case=False, na=False), "NumberVotes"])
            out[county] = (dem, rep)
            continue
        try:
            try:
                dcol, rcol = candidate_columns(raw, "gore", "bush")
            except ValueError:
                # Some exports identify the ticket by the vice-presidential nominees.
                dcol, rcol = candidate_columns(raw, "lieberman", "cheney")
            out[county] = (numeric_sum(raw.iloc[:, dcol]), numeric_sum(raw.iloc[:, rcol]))
        except ValueError:
            continue
    return out


def extract_2004() -> dict[str, tuple[float, float]]:
    archive = DATA / "2004/2004-generalelection-precinctlevel.zip"
    out = {}
    with ZipFile(archive) as zf:
        for member in zf.namelist():
            if not member.lower().endswith(".xls"):
                continue
            county = canonical_county(re.sub(r"\s*-\s*gen04\.xls$", "", Path(member).name, flags=re.I))
            df = pd.read_excel(BytesIO(zf.read(member)), header=None)
            contest = df.iloc[:, 0].astype(str).str.contains("PRESIDENT", case=False, na=False)
            names = df.iloc[:, 1].astype(str)
            dem = numeric_sum(df.loc[contest & names.str.contains("KERRY", case=False, na=False), 2])
            rep = numeric_sum(df.loc[contest & names.str.contains("BUSH", case=False, na=False), 2])
            if dem == 0 and rep == 0:
                dcol, rcol = candidate_columns(df, "kerry", "bush", rows=5)
                dem, rep = numeric_sum(df.iloc[2:, dcol]), numeric_sum(df.iloc[2:, rcol])
            out[county] = (dem, rep)
    return out


def extract_2008() -> dict[str, tuple[float, float]]:
    path = DATA / "2008/2008generalelectionprecinctlevelresults.xls"
    out = {}
    book = pd.ExcelFile(path)
    for county in book.sheet_names:
        df = pd.read_excel(path, sheet_name=county, header=None)
        dcol, rcol = candidate_columns(df, "obama", "mccain", rows=8)
        out[county] = (numeric_sum(df.iloc[:, dcol]), numeric_sum(df.iloc[:, rcol]))
    return out


def extract_2012() -> dict[str, tuple[float, float]]:
    out = {}
    folder = DATA / "2012/2012general-precinctlevel-duplicate-2"
    for path in folder.glob("*.xls*"):
        county = county_name(path)
        if path.name.endswith(".xls.xls"):
            ns = {"s": "urn:schemas-microsoft-com:office:spreadsheet"}
            tree = ET.parse(path)
            worksheet = next(
                ws for ws in tree.findall("s:Worksheet", ns)
                if ws.attrib.get("{urn:schemas-microsoft-com:office:spreadsheet}Name") == "2"
            )
            rows = worksheet.findall(".//s:Row", ns)[3:]
            values = []
            for row in rows:
                cells = [cell.findtext("s:Data", default="", namespaces=ns) for cell in row.findall("s:Cell", ns)]
                if len(cells) >= 6:
                    values.append(cells)
            out[county] = (
                numeric_sum(pd.Series([v[3] for v in values])),
                numeric_sum(pd.Series([v[5] for v in values])),
            )
            continue

        book = pd.ExcelFile(path)
        if "2" in book.sheet_names:
            df = pd.read_excel(path, sheet_name="2", header=None)
            header = df.iloc[1].fillna("").map(str).str.lower()
            dbase = next(i for i, text in enumerate(header) if "obama" in text)
            rbase = next(i for i, text in enumerate(header) if "romney" in text)
            out[county] = (numeric_sum(df.iloc[3:, dbase + 1]), numeric_sum(df.iloc[3:, rbase + 1]))
            continue

        # Montgomery uses the later row-oriented export format.
        for sheet in book.sheet_names:
            df = pd.read_excel(path, sheet_name=sheet)
            if df.shape[1] < 4:
                continue
            contest = df.iloc[:, 0].astype(str).str.contains("PRESIDENT", case=False, na=False)
            names = df.iloc[:, 2].astype(str)
            drow = df.loc[contest & names.str.contains("obama", case=False, na=False)].iloc[:, 3:]
            rrow = df.loc[contest & names.str.contains("romney", case=False, na=False)].iloc[:, 3:]
            if len(drow) == 1 and len(rrow) == 1:
                out[county] = (numeric_sum(drow.iloc[0]), numeric_sum(rrow.iloc[0]))
                break
    return out


def extract_row_files(year: int, folder: Path) -> dict[str, tuple[float, float]]:
    dem_name, rep_name = CANDIDATES[year]
    out = {}
    for path in folder.glob("*.xls"):
        df = pd.read_excel(path)
        contest = df.iloc[:, 0].astype(str).str.contains("PRESIDENT", case=False, na=False)
        names = df.iloc[:, 2].astype(str)
        drow = df.loc[contest & names.str.contains(dem_name, case=False, na=False)].iloc[:, 3:]
        rrow = df.loc[contest & names.str.contains(rep_name, case=False, na=False)].iloc[:, 3:]
        if len(drow) == 1 and len(rrow) == 1:
            out[county_name(path)] = (numeric_sum(drow.iloc[0]), numeric_sum(rrow.iloc[0]))
    return out


def load_results() -> pd.DataFrame:
    results = {
        1992: extract_1992(), 1996: extract_1996(),
        2000: extract_2000(),
        2004: extract_2004(), 2008: extract_2008(), 2012: extract_2012(),
        2016: extract_row_files(2016, DATA / "2016/2016-general-precinctlevel-duplicate-2"),
        2020: extract_row_files(2020, DATA / "2020/2020-general-precinct-results"),
        2024: extract_row_files(2024, DATA / "2024/2024-general-precinct-level-results"),
    }
    counties = sorted(set().union(*(r.keys() for r in results.values())))
    rows = []
    for county in counties:
        row = {"county": county}
        for year in YEARS:
            dem, rep = results[year].get(county, (None, None))
            row[f"dem_{year}"] = dem
            row[f"rep_{year}"] = rep
            row[f"winner_{year}"] = None if dem is None else ("R" if rep > dem else "D")
        rows.append(row)
    return pd.DataFrame(rows)


def classify(row: pd.Series) -> str:
    winners = [row[f"winner_{year}"] for year in YEARS]
    if winners[-1] == "D":
        return "Not Republican by 2024"
    last_democratic = max((i for i, winner in enumerate(winners) if winner == "D"), default=-1)
    # A gap after the last observed Democratic win can shift the crossover date.
    if any(pd.isna(winner) for winner in winners[last_democratic + 1:]):
        return "Incomplete record"
    crossover = last_democratic + 1
    if crossover < len(YEARS) and winners[crossover] == "R":
        return "Republican throughout" if crossover == 0 else str(YEARS[crossover])
    return "Incomplete record"


def geometry() -> gpd.GeoDataFrame:
    precincts = gpd.read_file(PRECINCTS, columns=["COUNTYFP", "County", "geometry"])
    if precincts.crs is None:
        raise ValueError("County source geometry has no CRS")
    if precincts["COUNTYFP"].duplicated().all():
        pass
    counties = precincts.dissolve(by="COUNTYFP", aggfunc={"County": "first"}).reset_index()
    if counties["COUNTYFP"].duplicated().any() or len(counties) != 67:
        raise ValueError("County dissolve did not produce 67 unique counties")
    if counties.geometry.isna().any() or counties.geometry.is_empty.any():
        raise ValueError("County geometry contains null or empty features")
    return counties


def render(gdf: gpd.GeoDataFrame, summary: pd.DataFrame) -> None:
    mpl.rcParams.update({
        "font.family": "serif", "font.serif": ["Source Serif 4", "Noto Serif", "DejaVu Serif"],
        "axes.facecolor": "#f5f1e8", "figure.facecolor": "#f5f1e8", "savefig.facecolor": "#f5f1e8",
        "text.color": "#25231f",
    })
    fig = plt.figure(figsize=(16, 10), constrained_layout=False)
    ax = fig.add_axes([0.055, 0.10, 0.66, 0.79])
    side = fig.add_axes([0.745, 0.12, 0.225, 0.73]); side.axis("off")

    for category, color in PALETTE.items():
        part = gdf[gdf["realignment"] == category]
        if len(part):
            part.plot(ax=ax, color=color, edgecolor="#f5f1e8", linewidth=0.75)
    gdf.boundary.plot(ax=ax, color="#6e685e", linewidth=0.32, alpha=0.65)
    gdf.dissolve().boundary.plot(ax=ax, color="#27241f", linewidth=1.25)
    ax.set_axis_off(); ax.set_aspect("equal")

    late = gdf[gdf["realignment"].isin(["2004", "2008", "2012", "2016", "2020", "2024", "Not Republican by 2024", "Incomplete record"])]
    for _, row in late.iterrows():
        point = row.geometry.representative_point()
        ax.text(point.x, point.y, row["County"], ha="center", va="center", fontsize=6.7,
                color="#201f1c" if row["realignment"] != "Not Republican by 2024" else "white",
                fontweight="semibold", path_effects=[])

    fig.text(0.055, 0.945, "Alabama’s county-level presidential realignment, 1992–2024",
             fontsize=25, fontweight="semibold", ha="left")
    fig.text(0.056, 0.905,
             "First Republican win followed by uninterrupted Republican presidential victories through 2024",
             fontsize=12.5, color="#5c574f", ha="left")

    order = [k for k in PALETTE if k in set(gdf["realignment"])]
    handles = [Patch(facecolor=PALETTE[k], edgecolor="#8c867d", linewidth=0.35, label=k) for k in order]
    side.text(0, 1.0, "DURABLE REALIGNMENT", fontsize=10, fontweight="bold", color="#5c574f", va="top")
    side.legend(handles=handles, loc="upper left", bbox_to_anchor=(-0.02, 0.96), frameon=False,
                fontsize=10.5, handlelength=1.5, handleheight=1.0, labelspacing=0.75)

    counts = summary["realignment"].value_counts()
    side.text(0, 0.49, "COUNTIES BY CROSSOVER WAVE", fontsize=10, fontweight="bold", color="#5c574f")
    y = 0.445
    for category in order:
        n = int(counts.get(category, 0))
        side.add_patch(mpl.patches.Rectangle((0, y - 0.012), n / 67 * 0.72, 0.024,
                                             transform=side.transAxes, color=PALETTE[category], clip_on=False))
        side.text(0.75, y, f"{n:>2}", va="center", ha="right", fontsize=10, transform=side.transAxes)
        side.text(0.78, y, category, va="center", ha="left", fontsize=8.8, transform=side.transAxes)
        y -= 0.047

    fig.text(0.055, 0.053,
             "Definition: earliest election in which the Republican presidential ticket won a county and won every later election shown. "
             "County totals are aggregated from Alabama Secretary of State precinct returns. Gray denotes a source gap that prevents dating the crossover.",
             fontsize=8.2, color="#625d55", ha="left", wrap=True)
    fig.text(0.055, 0.027, "Geography: 2024 Alabama precinct file dissolved to counties  •  Elections: 1992–2024 presidential general elections",
             fontsize=8.2, color="#625d55", ha="left")

    for suffix, dpi in (("png", 220), ("pdf", 300), ("svg", 300)):
        fig.savefig(OUT / f"alabama-presidential-realignment-1992-2024.{suffix}", dpi=dpi,
                    bbox_inches="tight", pad_inches=0.18)
    plt.close(fig)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    results = load_results()
    results["realignment"] = results.apply(classify, axis=1)
    counties = geometry()
    merged = counties.merge(results, left_on="County", right_on="county", how="left", validate="one_to_one")
    if merged["realignment"].isna().any():
        missing = merged.loc[merged["realignment"].isna(), "County"].tolist()
        raise ValueError(f"Unmatched counties: {missing}")

    results.to_csv(OUT / "county-presidential-results-and-realignment.csv", index=False)
    export_gdf = merged.drop(columns=["county"])
    export_gdf.to_file(OUT / "alabama-presidential-realignment-1992-2024.gpkg", layer="county_realign", driver="GPKG")
    render(merged, results)

    source_paths = [PRECINCTS] + [p for y in YEARS for p in (DATA / str(y)).rglob("*.xls*")]
    spec = {
        "title": "Alabama’s county-level presidential realignment, 1992–2024",
        "claim": "Maps the first durable Republican presidential win in each county during 1992–2024.",
        "data": {"source": "Alabama Secretary of State precinct returns", "vintage": "1992–2024",
                 "variable": "first Republican county win followed by uninterrupted Republican wins", "unit": "election year", "denominator": "two-party winner"},
        "geometry": {"source": str(PRECINCTS.relative_to(ROOT)), "vintage": "2024", "unit": "county",
                     "join_key": "county name", "crs": str(merged.crs)},
        "classification": {"method": "categorical election cycle", "center": None, "breaks": list(YEARS), "clip": None},
        "style": {"palette": PALETTE, "missing_color": PALETTE["Incomplete record"],
                  "line_widths": {"county": 0.32, "state": 1.25}, "font_family": "Source Serif 4",
                  "font_sizes": {"title": 25, "subtitle": 12.5, "county": 6.7, "notes": 8.2}},
        "layout": {"width": 16, "height": 10, "extent": list(map(float, merged.total_bounds)), "insets": []},
        "context_layers": [],
        "outputs": ["png", "svg", "pdf", "gpkg", "csv"],
        "qa": {"county_count": len(merged), "invalid_geometries": int((~merged.geometry.is_valid).sum()),
               "unmatched_counties": int(merged["county"].isna().sum()),
               "source_file_count": len(source_paths),
               "geometry_sha256": hashlib.sha256(PRECINCTS.read_bytes()).hexdigest()},
        "software_versions": {"geopandas": gpd.__version__, "pandas": pd.__version__, "matplotlib": mpl.__version__},
    }
    (OUT / "map_spec.json").write_text(json.dumps(spec, indent=2) + "\n")
    (OUT / "README.md").write_text(
        "# Alabama presidential realignment, 1992–2024\n\n"
        "County-level map of the first Republican presidential victory followed by uninterrupted Republican wins through 2024.\n\n"
        "Reproduce with `./.venv/bin/python scripts/create-alabama-1992-2024-realignment-map.py`.\n"
    )
    print(results["realignment"].value_counts(dropna=False).to_string())


if __name__ == "__main__":
    main()
