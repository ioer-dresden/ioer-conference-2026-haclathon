"""Fast, count-aware hotspot analysis for the digital-traces dataset.

The public functions deliberately separate the workflow into aggregation, analysis,
export, and display so notebooks can explain the method without carrying its
implementation details.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Any, Sequence

import duckdb
import geopandas as gpd
import numpy as np
import pandas as pd
from scipy.stats import binom


BASEMAP_DE_GRAY_STYLE = (
    "https://sgx.geodatenzentrum.de/gdz_basemapde_vektor/styles/bm_web_gry.json"
)
TOURIST_COLOR = (215, 48, 39, 190)
LOCAL_COLOR = (69, 117, 180, 190)


@dataclass(frozen=True)
class HotspotConfig:
    """Parameters for a post-composition hotspot analysis."""

    h3_resolution: int = 9
    neighborhood_radius: int = 1
    minimum_classified_posts: int = 30
    minimum_share_difference: float = 0.10
    fdr_alpha: float = 0.05
    tourist_source_label: str = "Tourist"
    local_source_label: str = "Local"
    unclassified_source_label: str = "Unclassified"

    def __post_init__(self) -> None:
        if not 0 <= self.h3_resolution <= 15:
            raise ValueError("h3_resolution must be between 0 and 15")
        if self.neighborhood_radius < 0:
            raise ValueError("neighborhood_radius must be non-negative")
        if self.minimum_classified_posts < 1:
            raise ValueError("minimum_classified_posts must be positive")
        if not 0 <= self.minimum_share_difference <= 1:
            raise ValueError("minimum_share_difference must be between 0 and 1")
        if not 0 < self.fdr_alpha < 1:
            raise ValueError("fdr_alpha must be between 0 and 1")


@dataclass
class AggregatedPosts:
    """An H3 aggregation held in a temporary DuckDB table."""

    con: duckdb.DuckDBPyConnection
    table_name: str
    source: str
    reference_name: str
    config: HotspotConfig
    input_posts: int
    h3_cells: int
    tourist_posts: int
    local_posts: int
    unclassified_posts: int
    reference_tourist_share: float
    seconds: float

    def overview(self) -> pd.DataFrame:
        """Return one concise row suitable for display in a notebook."""

        return pd.DataFrame(
            {
                "reference": [self.reference_name],
                "input_posts": [self.input_posts],
                "h3_cells": [self.h3_cells],
                "classified_posts": [
                    self.tourist_posts + self.local_posts
                ],
                "tourist_posts": [self.tourist_posts],
                "local_posts": [self.local_posts],
                "unclassified_posts": [self.unclassified_posts],
                "tourist_share": [self.reference_tourist_share],
                "aggregation_seconds": [self.seconds],
            }
        )


@dataclass
class HotspotResult:
    """Cell-level statistical results for the requested output extent."""

    cells: pd.DataFrame
    aggregation: AggregatedPosts
    output_bbox: tuple[tuple[float, float], tuple[float, float]] | None
    analyzed_cells: int
    tested_cells: int
    seconds: float

    @property
    def hotspots(self) -> pd.DataFrame:
        return self.cells.loc[self.cells["hot_spot_type"].notna()].copy()

    def summary(self) -> pd.DataFrame:
        """Return the main result counts and timings."""

        types = self.cells["hot_spot_type"]
        return pd.DataFrame(
            {
                "reference": [self.aggregation.reference_name],
                "output_cells": [len(self.cells)],
                "tested_cells": [self.tested_cells],
                "tourist_hotspots": [int(
                    (types == "Tourist hot spot").sum()
                )],
                "local_hotspots": [int(
                    (types == "Local hot spot").sum()
                )],
                "reference_tourist_share": [
                    self.aggregation.reference_tourist_share
                ],
                "analysis_seconds": [self.seconds],
            }
        )


@dataclass
class HotspotGeodata:
    """Matching polygon and centre-point versions of reported cells."""

    polygons: gpd.GeoDataFrame
    centroids: gpd.GeoDataFrame


@dataclass(frozen=True)
class ExportedHotspots:
    polygon_path: Path
    centroid_path: Path


def _parquet_source(source: str | Path) -> str:
    source_text = str(source)
    source_path = Path(source_text)
    if source_path.is_dir():
        return str(source_path / "*.parquet")
    if not any(token in source_text for token in ("*", "?", "[")) and not source_path.exists():
        raise FileNotFoundError(f"Parquet input not found: {source_path}")
    return source_text


def _load_h3(con: duckdb.DuckDBPyConnection) -> None:
    try:
        con.execute("LOAD h3")
    except duckdb.Error:
        con.execute("INSTALL h3; LOAD h3;")


def aggregate_posts(
    source: str | Path,
    *,
    reference_name: str = "available input data",
    config: HotspotConfig | None = None,
    con: duckdb.DuckDBPyConnection | None = None,
) -> AggregatedPosts:
    """Aggregate any compatible Parquet input to H3 cells with DuckDB.

    The reference distribution is derived from all rows in ``source``. Coordinates
    must be Web Mercator metres in columns ``x`` and ``y``; the source class must be
    in ``classification``.
    """

    cfg = config or HotspotConfig()
    connection = con or duckdb.connect()
    parquet = _parquet_source(source)
    _load_h3(connection)
    started = perf_counter()
    table_name = "composition_h3_input"

    connection.execute(
        f"""
        CREATE OR REPLACE TEMP TABLE {table_name} AS
        WITH snapped AS MATERIALIZED (
            SELECT
                x,
                y,
                COUNT(*) FILTER (WHERE classification = ?)::BIGINT
                    AS tourist_posts,
                COUNT(*) FILTER (WHERE classification = ?)::BIGINT
                    AS local_posts,
                COUNT(*) FILTER (WHERE classification = ?)::BIGINT
                    AS unclassified_posts,
                COUNT(*)::BIGINT AS all_posts
            FROM read_parquet(?)
            WHERE x IS NOT NULL AND y IS NOT NULL
            GROUP BY x, y
        )
        SELECT
            h3_latlng_to_cell(
                degrees(atan(sinh(y / 6378137.0))),
                degrees(x / 6378137.0),
                {cfg.h3_resolution}
            ) AS h3_index,
            SUM(tourist_posts)::BIGINT AS tourist_posts,
            SUM(local_posts)::BIGINT AS local_posts,
            SUM(unclassified_posts)::BIGINT AS unclassified_posts,
            SUM(all_posts)::BIGINT AS all_posts
        FROM snapped
        GROUP BY h3_index
        """,
        [
            cfg.tourist_source_label,
            cfg.local_source_label,
            cfg.unclassified_source_label,
            parquet,
        ],
    )

    totals = connection.execute(
        f"""
        SELECT
            COUNT(*)::BIGINT,
            SUM(all_posts)::BIGINT,
            SUM(tourist_posts)::BIGINT,
            SUM(local_posts)::BIGINT,
            SUM(unclassified_posts)::BIGINT
        FROM {table_name}
        """
    ).fetchone()
    if not totals or totals[1] is None:
        raise ValueError("The Parquet input contains no rows with valid x/y coordinates")

    h3_cells, input_posts, tourist, local, unclassified = map(int, totals)
    if tourist == 0 or local == 0:
        raise ValueError(
            "The input must contain at least one post from each compared source class"
        )

    invalid_coordinates = connection.execute(
        "SELECT COUNT(*) FROM read_parquet(?) WHERE x IS NULL OR y IS NULL", [parquet]
    ).fetchone()[0]
    if invalid_coordinates:
        raise ValueError(f"Input contains {invalid_coordinates:,} rows with missing coordinates")

    return AggregatedPosts(
        con=connection,
        table_name=table_name,
        source=parquet,
        reference_name=reference_name,
        config=cfg,
        input_posts=input_posts,
        h3_cells=h3_cells,
        tourist_posts=tourist,
        local_posts=local,
        unclassified_posts=unclassified,
        reference_tourist_share=tourist / (tourist + local),
        seconds=perf_counter() - started,
    )


def _by_adjust(p_values: np.ndarray, tested: np.ndarray) -> np.ndarray:
    """Benjamini-Yekutieli adjusted p-values for an arbitrary dependency structure."""

    q_values = np.ones(len(p_values), dtype=float)
    tested_indices = np.flatnonzero(tested)
    if not len(tested_indices):
        return q_values
    ordered = tested_indices[np.argsort(p_values[tested_indices])]
    ranks = np.arange(1, len(ordered) + 1)
    harmonic = np.sum(1.0 / ranks)
    adjusted = p_values[ordered] * len(ordered) * harmonic / ranks
    q_values[ordered] = np.minimum(1.0, np.minimum.accumulate(adjusted[::-1])[::-1])
    return q_values


def analyze_hotspots(
    aggregation: AggregatedPosts,
    *,
    output_bbox: tuple[tuple[float, float], tuple[float, float]] | None = None,
) -> HotspotResult:
    """Test H3 neighbourhood composition against the input-wide reference share.

    ``output_bbox`` is applied only after analysis, so it cannot change scores or
    truncate neighbourhoods. If the input itself is a spatial subset, its complete
    contents define the reference distribution.
    """

    cfg = aggregation.config
    con = aggregation.con
    started = perf_counter()
    neighborhood_table = "composition_h3_neighborhoods"

    con.execute(
        f"""
        CREATE OR REPLACE TEMP TABLE {neighborhood_table} AS
        SELECT
            focal.h3_index,
            focal.tourist_posts,
            focal.local_posts,
            focal.unclassified_posts,
            focal.all_posts,
            SUM(COALESCE(adjacent.tourist_posts, 0))::BIGINT
                AS neighborhood_tourist_posts,
            SUM(COALESCE(adjacent.local_posts, 0))::BIGINT
                AS neighborhood_local_posts
        FROM {aggregation.table_name} AS focal
        CROSS JOIN UNNEST(h3_grid_disk(focal.h3_index, {cfg.neighborhood_radius}))
            AS disk(neighbor_h3)
        LEFT JOIN {aggregation.table_name} AS adjacent
            ON adjacent.h3_index = disk.neighbor_h3
        WHERE focal.tourist_posts + focal.local_posts > 0
        GROUP BY
            focal.h3_index,
            focal.tourist_posts,
            focal.local_posts,
            focal.unclassified_posts,
            focal.all_posts
        """
    )

    cells = con.execute(
        f"""
        SELECT
            *,
            (tourist_posts + local_posts)::BIGINT
                AS classified_posts,
            tourist_posts::DOUBLE
                / (tourist_posts + local_posts)
                AS cell_tourist_share,
            (neighborhood_tourist_posts
                + neighborhood_local_posts)::BIGINT
                AS neighborhood_classified_posts,
            neighborhood_tourist_posts::DOUBLE
                / (neighborhood_tourist_posts + neighborhood_local_posts)
                AS neighborhood_tourist_share,
            h3_cell_to_lng(h3_index) AS lng,
            h3_cell_to_lat(h3_index) AS lat
        FROM {neighborhood_table}
        ORDER BY h3_index
        """
    ).df()
    analyzed_cells = len(cells)

    successes = cells["neighborhood_tourist_posts"].to_numpy(dtype=np.int64)
    trials = cells["neighborhood_classified_posts"].to_numpy(dtype=np.int64)
    tested = trials >= cfg.minimum_classified_posts
    p_values = np.ones(len(cells), dtype=float)
    p_values[tested] = np.minimum(
        1.0,
        2.0
        * np.minimum(
            binom.cdf(
                successes[tested], trials[tested], aggregation.reference_tourist_share
            ),
            binom.sf(
                successes[tested] - 1,
                trials[tested],
                aggregation.reference_tourist_share,
            ),
        ),
    )
    q_values = _by_adjust(p_values, tested)
    share_difference = (
        cells["neighborhood_tourist_share"].to_numpy()
        - aggregation.reference_tourist_share
    )
    reported = (
        tested
        & (q_values <= cfg.fdr_alpha)
        & (np.abs(share_difference) >= cfg.minimum_share_difference)
    )
    spot_type = np.full(len(cells), None, dtype=object)
    spot_type[reported & (share_difference > 0)] = "Tourist hot spot"
    spot_type[reported & (share_difference < 0)] = "Local hot spot"

    cells["share_difference"] = share_difference
    cells["p_value"] = p_values
    cells["q_value"] = q_values
    cells["hot_spot_type"] = pd.Categorical(
        spot_type,
        categories=["Tourist hot spot", "Local hot spot"],
    )

    if output_bbox is not None:
        (west, east), (south, north) = output_bbox
        if not (west < east and south < north):
            raise ValueError("output_bbox must be ((west, east), (south, north))")
        cells = cells.loc[
            cells["lng"].between(west, east) & cells["lat"].between(south, north)
        ].reset_index(drop=True)
        if cells.empty:
            raise ValueError("output_bbox contains no classified input posts")

    tested_cells = int(
        (cells["neighborhood_classified_posts"] >= cfg.minimum_classified_posts).sum()
    )
    result = HotspotResult(
        cells=cells,
        aggregation=aggregation,
        output_bbox=output_bbox,
        analyzed_cells=analyzed_cells,
        tested_cells=tested_cells,
        seconds=perf_counter() - started,
    )
    validate_result(result)
    return result


def to_geodataframes(result: HotspotResult) -> HotspotGeodata:
    """Create matching EPSG:4326 polygon and H3-centre point GeoDataFrames."""

    hotspot_cells = result.hotspots
    hotspot_cells["hot_spot_type"] = hotspot_cells["hot_spot_type"].astype(str)
    con = result.aggregation.con
    con.register("composition_hotspot_cells", hotspot_cells)
    try:
        frame = con.execute(
            """
            SELECT
                *,
                h3_h3_to_string(h3_index) AS h3_cell,
                h3_cell_to_boundary_wkb(h3_index) AS geometry
            FROM composition_hotspot_cells
            """
        ).df()
    finally:
        con.unregister("composition_hotspot_cells")

    boundary_geometry = gpd.GeoSeries.from_wkb(
        frame.pop("geometry").map(bytes), crs="EPSG:4326"
    )
    center_geometry = gpd.points_from_xy(
        frame.pop("lng"), frame.pop("lat"), crs="EPSG:4326"
    )
    geodata = HotspotGeodata(
        polygons=gpd.GeoDataFrame(frame.copy(), geometry=boundary_geometry),
        centroids=gpd.GeoDataFrame(
            frame.copy(), geometry=center_geometry, crs="EPSG:4326"
        ),
    )
    validate_geodata(geodata)
    return geodata


def _slug(value: str) -> str:
    return "".join(character.lower() if character.isalnum() else "_" for character in value).strip("_")


def export_hotspots(
    geodata: HotspotGeodata,
    output_directory: str | Path,
    analysis_name: str,
) -> ExportedHotspots:
    """Write polygon and centre-point GeoParquet files with matching attributes."""

    output = Path(output_directory)
    output.mkdir(parents=True, exist_ok=True)
    slug = _slug(analysis_name)
    paths = ExportedHotspots(
        polygon_path=output / f"{slug}_composition_hotspots.parquet",
        centroid_path=output / f"{slug}_composition_hotspots_centroids.parquet",
    )
    geodata.polygons.to_parquet(paths.polygon_path)
    geodata.centroids.to_parquet(paths.centroid_path)
    return paths


def make_lonboard_map(
    cells: pd.DataFrame,
    *,
    basemap_style: str = BASEMAP_DE_GRAY_STYLE,
    height: int = 700,
) -> Any:
    """Create a compact interactive Lonboard map using native H3 identifiers."""

    if cells.empty:
        raise ValueError("There are no reported cells to map")
    try:
        from lonboard import H3HexagonLayer, Map
        from lonboard.basemap import MaplibreBasemap
    except ImportError as error:
        raise ImportError("Install the optional map dependency with: pip install lonboard") from error

    map_data = pd.DataFrame(
        {
            "h3_index": cells["h3_index"].astype("uint64"),
            "Hot spot": cells["hot_spot_type"].astype("category"),
            "Local + Tourist posts": pd.to_numeric(
                cells["neighborhood_classified_posts"], downcast="unsigned"
            ),
            "Tourist share": cells["neighborhood_tourist_share"].astype(
                "float32"
            ),
            "Difference from reference": cells["share_difference"].astype(
                "float32"
            ),
        }
    )
    tourist = map_data["Hot spot"].eq("Tourist hot spot").to_numpy()
    colors = np.empty((len(map_data), 4), dtype=np.uint8)
    colors[tourist] = TOURIST_COLOR
    colors[~tourist] = LOCAL_COLOR

    layer = H3HexagonLayer.from_pandas(
        map_data,
        get_hexagon=map_data["h3_index"],
        get_fill_color=colors,
        coverage=1,
        extruded=False,
        stroked=False,
        opacity=0.8,
        pickable=True,
        auto_highlight=True,
    )
    return Map(
        layer,
        basemap=MaplibreBasemap(style=basemap_style),
        height=height,
        show_tooltip=True,
        show_side_panel=False,
    )


def _legend_html(*, overlay: bool) -> str:
    position = (
        "position:fixed;right:18px;top:18px;z-index:10000;"
        if overlay
        else "display:inline-block;margin:0 0 8px 0;"
    )
    items = (
        ("Tourist hot spot", TOURIST_COLOR),
        ("Local hot spot", LOCAL_COLOR),
    )
    rows = "".join(
        f'<div style="margin-top:6px;white-space:nowrap">'
        f'<span style="display:inline-block;width:13px;height:13px;'
        f'background:rgb({red},{green},{blue});margin-right:7px;'
        f'vertical-align:-2px"></span>{label}</div>'
        for label, (red, green, blue, _alpha) in items
    )
    return (
        f'<div style="{position}background:rgba(255,255,255,.94);'
        'border:1px solid #777;border-radius:4px;padding:9px 11px;'
        'font:13px/1.25 sans-serif;color:#222;box-shadow:0 1px 4px #0003">'
        f"<strong>Post-composition hot spots</strong>{rows}</div>"
    )


def map_with_legend(hotspot_map: Any) -> Any:
    """Return a notebook widget containing the categorical legend and map."""

    try:
        from ipywidgets import HTML, VBox
    except ImportError as error:
        raise ImportError("Install ipywidgets to display the map legend") from error
    return VBox([HTML(value=_legend_html(overlay=False)), hotspot_map])


def export_lonboard_map(
    hotspot_map: Any,
    output_file: str | Path,
    *,
    title: str = "Post-composition hot spots",
) -> Path:
    """Write a single standalone HTML page with the same map and legend."""

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    page = hotspot_map.to_html(title=title)
    if not isinstance(page, str):
        raise TypeError("Lonboard did not return standalone HTML")
    page = page.replace("<body>", f"<body>\n{_legend_html(overlay=True)}", 1)
    output_path.write_text(page, encoding="utf-8")
    return output_path


def validate_result(result: HotspotResult) -> None:
    """Validate invariants without assuming a particular geographic extent."""

    cells = result.cells
    cfg = result.aggregation.config
    numeric = cells[["p_value", "q_value", "share_difference"]]
    if not np.isfinite(numeric).all().all():
        raise AssertionError("Non-finite statistical result")
    if not cells["p_value"].between(0, 1).all() or not cells["q_value"].between(0, 1).all():
        raise AssertionError("p/q values must be between zero and one")
    reported = cells["hot_spot_type"].notna()
    if not (cells.loc[reported, "neighborhood_classified_posts"] >= cfg.minimum_classified_posts).all():
        raise AssertionError("A reported cell has insufficient support")
    if not (cells.loc[reported, "q_value"] <= cfg.fdr_alpha).all():
        raise AssertionError("A reported cell failed the FDR threshold")
    if not (cells.loc[reported, "share_difference"].abs() >= cfg.minimum_share_difference).all():
        raise AssertionError("A reported cell failed the effect-size threshold")


def validate_geodata(geodata: HotspotGeodata) -> None:
    """Ensure polygon and centroid exports contain the same reported cells."""

    polygons, centroids = geodata.polygons, geodata.centroids
    if len(polygons) != len(centroids):
        raise AssertionError("Polygon and centroid row counts differ")
    if polygons.crs.to_epsg() != 4326 or centroids.crs.to_epsg() != 4326:
        raise AssertionError("Hotspot outputs must use EPSG:4326")
    if not polygons.geometry.geom_type.eq("Polygon").all():
        raise AssertionError("Polygon output contains non-polygon geometry")
    if not centroids.geometry.geom_type.eq("Point").all():
        raise AssertionError("Centroid output contains non-point geometry")
    if not polygons["h3_cell"].equals(centroids["h3_cell"]):
        raise AssertionError("Polygon and centroid H3 identifiers differ")


def busiest_hotspots(
    polygons: gpd.GeoDataFrame,
    count: int = 15,
    columns: Sequence[str] | None = None,
) -> pd.DataFrame:
    """Return the busiest reported neighbourhoods for concise display."""

    selected_columns = list(columns or [
        "h3_cell",
        "neighborhood_classified_posts",
        "neighborhood_tourist_share",
        "share_difference",
        "q_value",
        "hot_spot_type",
    ])
    return (
        polygons.nlargest(count, "neighborhood_classified_posts")[selected_columns]
        .sort_values("neighborhood_classified_posts", ascending=False)
        .reset_index(drop=True)
    )
