"""Render original editorial maps for the 2026 Alabama CD-5 Democratic primary.

Uses the completed 2026 reporting geometry and reviewed result tables. This
script performs exact key joins only; it does not fuzzy-match precinct names.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import geopandas as gpd
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import to_rgb
from matplotlib.patches import Rectangle


ROOT = Path(__file__).resolve().parents[1]
GEOMETRY_PATH = ROOT / "outputs/alabama-2026-custom-precincts/alabama-2026-precincts.gpkg"
RESULTS_ROOT = ROOT / "outputs/alabama-cd5-2026-democratic-primary"
OUTPUT = RESULTS_ROOT / "original-broadsheet"
TOTALS_PATH = RESULTS_ROOT / "candidate-totals.csv"

FIGURE_BG = "#F4F0E7"
PAPER = "#FDFBF6"
INK = "#1C2428"
MUTED = "#596268"
HAIRLINE = "#BEB8AC"
NO_VOTE = "#C4C2BC"
COUNTY_LINE = "#4C565B"
SERIF = "Nimbus Roman"
SANS = "Nimbus Sans Narrow"

CANDIDATES = {
    "Andrew Sneed": {"label": "Andrew Sneed", "color": "#2F6FAF"},
    "Candice Dollar Duvieilh": {"label": "Candice Duvieilh", "color": "#7651A1"},
    "Jeremy Devito": {"label": "Jeremy DeVito", "color": "#C2822B"},
}

ROUNDS = {
    "first-round": {"round_label": "FIRST ROUND", "date": "MAY 19, 2026",
                    "headline": "Sneed led, but the field remained divided"},
    "runoff": {"round_label": "RUNOFF", "date": "JUNE 16, 2026",
               "headline": "Sneed won nearly four in five runoff votes"},
}

BREAKS = [0, 5, 10, 20, 35, 50, np.inf]
SHADE_FACTORS = [0.46, 0.57, 0.68, 0.79, 0.90, 1.0]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def mix_with_paper(hex_color: str, factor: float) -> tuple[float, float, float]:
    base = np.array(to_rgb(hex_color))
    paper = np.array(to_rgb(PAPER))
    return tuple(paper + (base - paper) * factor)


def load_geometry() -> gpd.GeoDataFrame:
    geometry = gpd.read_file(GEOMETRY_PATH)
    required = {"PCT26_ID", "COUNTY", "SOURCES", "geometry"}
    if missing := required - set(geometry.columns):
        raise ValueError(f"Updated geometry is missing columns: {sorted(missing)}")
    if geometry.crs is None:
        raise ValueError("Updated geometry has no CRS")
    if geometry.PCT26_ID.duplicated().any():
        raise ValueError("PCT26_ID is not unique")
    if geometry.geometry.isna().any() or geometry.geometry.is_empty.any() or (~geometry.is_valid).any():
        raise ValueError("Updated geometry contains null, empty, or invalid features")
    return geometry


def load_round(round_name: str, geometry: gpd.GeoDataFrame) -> tuple[gpd.GeoDataFrame, dict]:
    path = RESULTS_ROOT / f"precinct-results-{round_name}.csv"
    results = pd.read_csv(path)
    candidate_cols = [name for name in CANDIDATES if name in results.columns]

    # The reviewed first-round table supplies the canonical updated source label
    # for every legacy UNIQUE_ID. Reuse that established identity in the runoff,
    # whose workbook sometimes abbreviates the same polling-place label.
    canonical = pd.read_csv(RESULTS_ROOT / "precinct-results-first-round.csv")
    canonical = canonical[["UNIQUE_ID", "source_precinct"]].rename(
        columns={"source_precinct": "canonical_source_precinct"}
    )
    if canonical.UNIQUE_ID.duplicated().any():
        raise ValueError("First-round UNIQUE_ID is not unique")
    results = results.merge(canonical, on="UNIQUE_ID", how="left", validate="one_to_one")
    results["source_precinct"] = results.canonical_source_precinct.fillna(results.source_precinct)

    # The reviewed tables already contain accepted source labels. Exploding the
    # updated layer's SOURCES field makes exact many-to-one aggregation explicit.
    base_lookup = geometry[["PCT26_ID", "COUNTY", "SOURCES"]].copy()
    lookup = base_lookup.copy()
    lookup["source_precinct"] = lookup.SOURCES.str.split(" + ", regex=False)
    lookup = lookup.explode("source_precinct")
    # A previously reviewed CD-5 row already combines the same two Limestone
    # returns represented by one PCT26 geometry. Retain that exact composite key
    # alongside the component aliases; this is not a new match decision.
    composite = base_lookup[base_lookup.SOURCES.str.contains(" + ", regex=False)].copy()
    composite["source_precinct"] = composite.SOURCES
    lookup = pd.concat([lookup, composite], ignore_index=True)
    lookup = lookup.rename(columns={"COUNTY": "County"})
    if lookup.duplicated(["County", "source_precinct"]).any():
        raise ValueError("Updated geometry contains a duplicated county/source label")

    accepted_count = int(results.matched.fillna(False).sum())
    joined = results.merge(
        lookup[["PCT26_ID", "County", "source_precinct"]],
        on=["County", "source_precinct"], how="left", validate="one_to_one",
    )
    unmatched = joined.PCT26_ID.isna()
    if unmatched.any():
        labels = joined.loc[unmatched, ["County", "source_precinct"]].to_dict("records")
        raise ValueError(f"Accepted results missing from updated geometry: {labels[:5]}")

    aggregated = joined.groupby("PCT26_ID", as_index=False)[candidate_cols].sum()
    frame = geometry.merge(aggregated, on="PCT26_ID", how="inner", validate="one_to_one")
    frame[candidate_cols] = frame[candidate_cols].fillna(0)
    frame["total_votes"] = frame[candidate_cols].sum(axis=1)
    frame["winner"] = frame[candidate_cols].idxmax(axis=1)
    frame.loc[frame.total_votes.eq(0), "winner"] = pd.NA
    ordered = np.sort(frame[candidate_cols].to_numpy(), axis=1)
    frame["margin_pp"] = np.where(
        frame.total_votes.gt(0),
        (ordered[:, -1] - ordered[:, -2]) / frame.total_votes * 100,
        np.nan,
    )
    frame["margin_class"] = pd.cut(
        frame.margin_pp, BREAKS, labels=False, include_lowest=True, right=False
    ).fillna(-1).astype(int)
    unclassified_voting = frame.total_votes.gt(0) & frame.margin_class.lt(0)
    if unclassified_voting.any():
        raise ValueError(
            f"{int(unclassified_voting.sum())} voting geometries fall outside the margin classes"
        )

    official = pd.read_csv(TOTALS_PATH)
    official = official[official["round"].eq(round_name)].copy()
    totals = {
        row.candidate: {"votes": int(row.votes), "share": float(row.share)}
        for row in official.itertuples()
    }
    audit = {
        "source_rows": int(len(results)),
        "accepted_source_rows": accepted_count,
        "mapped_reporting_geometries": int(len(frame)),
        "voting_reporting_geometries": int(frame.total_votes.gt(0).sum()),
        "mapped_vote_total": int(frame.total_votes.sum()),
        "official_vote_total": int(official.votes.sum()),
        "tied_reporting_geometries": int((frame.total_votes.gt(0) & frame.margin_pp.eq(0)).sum()),
        "unclassified_voting_geometries": int(unclassified_voting.sum()),
        "candidate_columns": candidate_cols,
    }
    return frame, {"totals": totals, "audit": audit, "results_path": path}


def add_header(fig, meta: dict) -> None:
    fig.text(0.052, 0.955, "THE ALABAMA PRIMARY", color=INK, fontsize=10,
             fontweight="bold", fontfamily=SANS)
    fig.text(0.948, 0.955, "5TH CONGRESSIONAL DISTRICT", ha="right", color=INK,
             fontsize=10, fontweight="bold", fontfamily=SANS)
    fig.add_artist(plt.Line2D([0.052, 0.948], [0.938, 0.938], transform=fig.transFigure,
                              color=INK, linewidth=1.5))
    fig.text(0.052, 0.885, meta["headline"], color=INK, fontsize=32,
             fontweight="bold", fontfamily=SERIF)
    fig.text(0.052, 0.840, "Precinct winner and margin in the Democratic nomination contest",
             color=MUTED, fontsize=12, fontfamily=SERIF)
    fig.text(0.948, 0.862, meta["round_label"], ha="right", color=INK, fontsize=10,
             fontweight="bold", fontfamily=SANS)
    fig.text(0.948, 0.838, meta["date"], ha="right", color=MUTED, fontsize=10,
             fontfamily=SANS)


def add_map(fig, frame: gpd.GeoDataFrame) -> None:
    ax = fig.add_axes([0.052, 0.325, 0.896, 0.475])
    ax.set_facecolor(FIGURE_BG)

    no_vote = frame[frame.total_votes.eq(0)]
    if len(no_vote):
        no_vote.plot(ax=ax, color=NO_VOTE, edgecolor="#858A8D", linewidth=0.45, hatch="////")
    for candidate, info in CANDIDATES.items():
        for class_id, factor in enumerate(SHADE_FACTORS):
            subset = frame[(frame.winner == candidate) & (frame.margin_class == class_id)]
            if len(subset):
                subset.plot(ax=ax, color=mix_with_paper(info["color"], factor),
                            edgecolor=PAPER, linewidth=0.32)

    counties = frame.dissolve("COUNTY")
    counties.boundary.plot(ax=ax, color=COUNTY_LINE, linewidth=0.75, alpha=0.78)
    frame.dissolve().boundary.plot(ax=ax, color=INK, linewidth=1.8)

    labels = counties.representative_point()
    for county, point in labels.items():
        ax.text(point.x, point.y, str(county).upper(), ha="center", va="center", fontsize=7.2,
                fontweight="bold", color=INK, alpha=0.76,
                fontfamily=SERIF,
                bbox={"boxstyle": "square,pad=0.14", "facecolor": PAPER,
                      "edgecolor": "none", "alpha": 0.84})
    ax.set_axis_off()
    ax.margins(0.025)


def add_legend(fig, audit: dict) -> None:
    ax = fig.add_axes([0.052, 0.265, 0.896, 0.052]); ax.axis("off")
    ax.text(0, 0.68, "WINNER", fontsize=8.5, fontweight="bold", color=MUTED, fontfamily=SANS)
    x = 0.075
    present = [c for c in CANDIDATES if c in audit["candidate_columns"]]
    for candidate in present:
        ax.add_patch(Rectangle((x, 0.49), 0.018, 0.28, transform=ax.transAxes,
                               facecolor=CANDIDATES[candidate]["color"], edgecolor="none"))
        ax.text(x + 0.025, 0.63, CANDIDATES[candidate]["label"].split()[0], fontsize=8.5,
                color=INK, va="center", fontfamily=SERIF)
        x += 0.13
    if audit["voting_reporting_geometries"] < audit["mapped_reporting_geometries"]:
        missing = audit["mapped_reporting_geometries"] - audit["voting_reporting_geometries"]
        ax.add_patch(Rectangle((0.40, 0.49), 0.022, 0.28, transform=ax.transAxes,
                               facecolor=NO_VOTE, edgecolor="#858A8D", hatch="////", linewidth=0.4))
        ax.text(0.43, 0.63, f"No vote ({missing})", fontsize=7.5, color=MUTED,
                va="center", fontfamily=SANS)
    ax.text(0.50, 0.68, "VICTORY MARGIN", fontsize=8.5, fontweight="bold", color=MUTED,
            fontfamily=SANS)
    labels = ["<5", "5–10", "10–20", "20–35", "35–50", "50+"]
    for idx, (factor, label) in enumerate(zip(SHADE_FACTORS, labels)):
        xpos = 0.59 + idx * 0.058
        ax.add_patch(Rectangle((xpos, 0.45), 0.052, 0.36, transform=ax.transAxes,
                               facecolor=mix_with_paper(CANDIDATES["Andrew Sneed"]["color"], factor), edgecolor="none"))
        ax.text(xpos + 0.026, 0.19, label, ha="center", fontsize=7.2, color=MUTED, fontfamily=SANS)
    ax.text(0.948, 0.63, "points", ha="right", fontsize=7.2, color=MUTED, fontfamily=SANS)


def add_results(fig, totals: dict, candidate_cols: list[str], audit: dict) -> None:
    ax = fig.add_axes([0.052, 0.085, 0.896, 0.145])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    ax.text(0, 0.93, "OFFICIAL RESULT", fontsize=8.5, fontweight="bold", color=MUTED,
            fontfamily=SANS)
    ordered = sorted(candidate_cols, key=lambda c: totals[c]["votes"], reverse=True)
    left = 0.0
    centers = []
    for candidate in ordered:
        share = totals[candidate]["share"]
        ax.add_patch(Rectangle((left, 0.58), share, 0.18, transform=ax.transAxes,
                               facecolor=CANDIDATES[candidate]["color"], edgecolor=FIGURE_BG,
                               linewidth=1.2))
        ax.text(left + share / 2, 0.67, f"{share:.1%}", color="white", ha="center", va="center",
                fontsize=10, fontweight="bold", fontfamily=SANS)
        centers.append((left + share / 2, candidate))
        left += share
    for center, candidate in centers:
        data = totals[candidate]
        ax.text(center, 0.40, CANDIDATES[candidate]["label"], ha="center", color=INK,
                fontsize=10, fontweight="bold", fontfamily=SERIF)
        ax.text(center, 0.22, f"{data['votes']:,} votes", ha="center", color=MUTED,
                fontsize=8.5, fontfamily=SANS)
    ax.text(0, 0.01,
            f"Map: {audit['voting_reporting_geometries']} voting geometries and "
            f"{audit['mapped_vote_total']:,} election-day votes. Official totals also include absentee and provisional ballots.",
            color=MUTED, fontsize=7.5, fontfamily=SERIF)


def add_notes(fig, audit: dict) -> None:
    status_note = "Unfilled areas lie outside District 5."
    if audit["voting_reporting_geometries"] < audit["mapped_reporting_geometries"]:
        status_note += " Gray hatching marks reporting geometries with no recorded district vote."
    fig.text(0.052, 0.043, status_note + " County labels are orientation aids.",
             color=MUTED, fontsize=7.5, fontfamily=SERIF)
    fig.text(0.948, 0.043, "Source: Alabama Secretary of State · Derived 2026 reporting geometry",
             ha="right", color=MUTED, fontsize=7.5, fontfamily=SERIF)


def render(round_name: str, geometry: gpd.GeoDataFrame) -> dict:
    frame, details = load_round(round_name, geometry)
    fig = plt.figure(figsize=(16, 11.5), dpi=100, facecolor=FIGURE_BG)
    add_header(fig, ROUNDS[round_name])
    add_map(fig, frame)
    add_legend(fig, details["audit"])
    add_results(fig, details["totals"], details["audit"]["candidate_columns"], details["audit"])
    add_notes(fig, details["audit"])
    output_base = OUTPUT / f"alabama-cd5-2026-democratic-{round_name}-broadsheet"
    fig.savefig(output_base.with_suffix(".png"), dpi=200, facecolor=FIGURE_BG)
    fig.savefig(output_base.with_suffix(".svg"), facecolor=FIGURE_BG)
    plt.close(fig)
    return {
        **details["audit"],
        "result_sha256": sha256(details["results_path"]),
        "png": str(output_base.with_suffix(".png").relative_to(ROOT)),
        "svg": str(output_base.with_suffix(".svg").relative_to(ROOT)),
    }


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    geometry = load_geometry()
    audits = {round_name: render(round_name, geometry) for round_name in ROUNDS}
    (OUTPUT / "render-audit.json").write_text(json.dumps(audits, indent=2) + "\n")
    print(json.dumps(audits, indent=2))


if __name__ == "__main__":
    main()
