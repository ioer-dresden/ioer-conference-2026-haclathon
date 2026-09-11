# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.5
#   kernelspec:
#     display_name: Python (3d-building-pareto-analysis)
#     language: python
#     name: 3d-building-pareto-analysis
# ---

# %% [markdown]
# # 3. Building the Analytical Foundation: Spatial Join and Aggregation
#
# ## 3.1 The Challenge
#
# In {doc}`2. Analyzing Building Stock Patterns <203b_analysis>`, we worked with pre-aggregated data — no need to process the full 5 GB dataset. But how did we get from **57 million building footprints** to the analytical dataset used in analysis?
#
# This chapter documents the first step of the pipeline:
#
# - **Spatial join** — assigning each footprint to its municipality (Gemeinde)
# - **Aggregation** — summing footprints to municipality level (`ags`)
#
# **Why we document this pipeline:**
#
# - **Reproducibility** — best practice for open science
# - **Showcasing** — how to work with large GeoParquet datasets efficiently using DuckDB
# - **Inspiration** — a potential template for your own large-scale analyses
#
# > **Note:** This chapter is documentation only. The code is provided for full reproducibility but requires the complete dataset (~5 GB). The analysis in Chapters 1–2 uses already aggregated data. In **Section 3.6**, we provide performance considerations based on the hardware used. In **Section 3.7**, we guide you through downloading the full dataset.
#
# ## 3.2 Setting Up the Processing Environment
#
# We use **DuckDB** — an in-process analytical database that:
# - Handles large spatial data efficiently
# - Uses spatial indexes (R-tree) for fast lookups
# - Reads GeoParquet files directly from disk
# - Processes data in parallel
#
# ### Setup
#
# First, we set up DuckDB with the spatial extension.

# %%
# ============================================================
# Setup DuckDB with spatial extension
# ============================================================
import duckdb
from pathlib import Path

# Define root directory
ROOT = Path.cwd().parent

# Paths
FOOTPRINTS_DIR = ROOT / "data" / "raw" / "3D_building_metrics_germany_2024"
VG25_GPKG_PATH = ROOT / "data" / "raw" / "VG25" / "Daten" / "DE_VG25.gpkg"
GEM_LAYER = "vg25_gem"

# Filter: only buildings with function code starting with '31'
BLDG_FUNCTION_PREFIX = "31"

# Connect to DuckDB (in-memory)
con = duckdb.connect(database=":memory:")

# Load spatial extension
con.execute("INSTALL spatial;")
con.execute("LOAD spatial;")

# Performance settings
con.execute("SET memory_limit='8GB';")
con.execute("SET threads TO 8;")
con.execute(f"SET temp_directory='{(ROOT / 'tmp_duckdb').as_posix()}';")

print("DuckDB ready with spatial extension.")

# %% [markdown]
# ### Load Administrative Boundaries
#
# We load the VG25 municipality boundaries (Gemeinden) into DuckDB and add a spatial index for fast joins.
#
# **Data source:** VG25 (Verwaltungsgebiete 1:25 000), © BKG (2025) CC BY 4.0, reference date 31.12.2024.  
# **Download:** [https://daten.gdz.bkg.bund.de/produkte/vg/vg25_ebenen/aktuell/vg25.utm32s.gpkg.zip](https://daten.gdz.bkg.bund.de/produkte/vg/vg25_ebenen/aktuell/vg25.utm32s.gpkg.zip)  
# **Quellenvermerk:** © BKG (2025) CC BY 4.0, Datenquellen: [https://sgx.geodatenzentrum.de/web_public/gdz/datenquellen/datenquellen_vg25.pdf](https://sgx.geodatenzentrum.de/web_public/gdz/datenquellen/datenquellen_vg25.pdf)  
# **Terms of use:** [http://sg.geodatenzentrum.de/web_public/nutzungsbedingungen.pdf](http://sg.geodatenzentrum.de/web_public/nutzungsbedingungen.pdf)
#
# > **Note:** The data provided in this repository has reference date **31.12.2024**. If you download the dataset via the link above, the reference date may be newer.
#

# %%
# ============================================================
# Load administrative boundaries (Gemeinden)
# ============================================================
con.execute(f"""
    CREATE OR REPLACE TEMP TABLE gemeinden AS
    SELECT
        AGS,
        GEN,
        geom AS geom_t
    FROM st_read('{VG25_GPKG_PATH.as_posix()}', layer='{GEM_LAYER}')
""")

# Add spatial index for faster joins
con.execute("CREATE INDEX gem_geom_idx ON gemeinden USING RTREE (geom_t);")

n_gemeinden = con.execute("SELECT COUNT(*) FROM gemeinden").fetchone()[0]
print(f"Loaded {n_gemeinden:,} Gemeinden with spatial index.")

# %% [markdown]
# ### Add State Codes
#
# We add state codes to prevent cross-state assignments during the spatial join.

# %%
# ============================================================
# Add state codes via AGS lookup
# ============================================================
con.execute("""
    CREATE OR REPLACE TEMP TABLE ags_lookup (
        ags_prefix  VARCHAR,
        short_id    VARCHAR,
        bundesland  VARCHAR
    )
""")

con.execute("""
    INSERT INTO ags_lookup VALUES
        ('01', 'sh', 'Schleswig-Holstein'),
        ('02', 'hh', 'Hamburg'),
        ('03', 'ni', 'Niedersachsen'),
        ('04', 'hb', 'Bremen'),
        ('05', 'nw', 'Nordrhein-Westfalen'),
        ('06', 'he', 'Hessen'),
        ('07', 'rp', 'Rheinland-Pfalz'),
        ('08', 'bw', 'Baden-Württemberg'),
        ('09', 'by', 'Bayern'),
        ('10', 'sl', 'Saarland'),
        ('11', 'be', 'Berlin'),
        ('12', 'bb', 'Brandenburg'),
        ('13', 'mv', 'Mecklenburg-Vorpommern'),
        ('14', 'sn', 'Sachsen'),
        ('15', 'st', 'Sachsen-Anhalt'),
        ('16', 'th', 'Thüringen')
""")

# Add state_code to gemeinden
con.execute("""
    CREATE OR REPLACE TEMP TABLE gemeinden AS
    SELECT
        g.AGS,
        g.GEN,
        g.geom_t,
        l.short_id AS state_code
    FROM gemeinden g
    LEFT JOIN ags_lookup l
        ON substr(g.AGS, 1, 2) = l.ags_prefix
""")

# Re-add spatial index
con.execute("CREATE INDEX gem_geom_idx ON gemeinden USING RTREE (geom_t);")

print("Boundaries ready with state_code and spatial index.")

# %% [markdown]
# ## 3.3 Spatial Join (Exact Match Only)
#
# We assign each building footprint to its municipality using a **centroid-in-polygon** join, restricted to the same federal state.
#
# **How it works:**
#
# 1. We already loaded the municipal geometries from the **VG25 dataset** (BKG) into DuckDB (table `gemeinden`), with state codes added.
# 2. We now iterate over the **16 GeoParquet partition files** (one per federal state).
# 3. For each partition:
#    - We compute the **centroid** of each building footprint.
#    - We join against the `gemeinden` table, restricted to the **same federal state** (`state_code` match).
#    - We use `ST_Within()` to check if the centroid falls inside a municipality polygon.
# 4. Results are stored in a DuckDB table called `footprints_with_ags` — one row per building footprint, with the assigned municipality code (`ags_vg25`) and name (`gemeinde_name`).
#
# This approach is efficient because:
# - The spatial index on `gemeinden` speeds up the join.
# - The state-code restriction reduces the number of candidate polygons per footprint.
# - GeoParquet files are read directly from disk — no need to load everything into memory.
# We assign each building footprint to its municipality using a **centroid-in-polygon** join, restricted to the same federal state.
#
# **Why no fallback?**
#
# A fallback join (e.g., nearest-neighbor within a search radius) could catch footprints near borders. However, for the scope of this analysis, we accept a small number of unmatched footprints. This keeps the pipeline simple and transparent.
#
# ### Step 1: Exact Join (Centroid-in-Polygon)
#
# We compute the centroid of each building footprint and check which municipality polygon contains it — within the same federal state.

# %%
# ============================================================
# Step 1: Exact centroid-in-polygon join (all 16 states)
# ============================================================
# This code is provided for full reproducibility.
# It requires the complete dataset (~5 GB).

import time

# Get all partition files
partition_files = sorted(FOOTPRINTS_DIR.glob("*.parquet"))

# Track unmatched footprints
unmatched_count = 0
total_count = 0

# Flag: first partition creates the table
first_partition = True

for i, pf in enumerate(partition_files, 1):
    t0 = time.time()
    
    state_name = pf.stem
    short_id = state_name.split("_")[0]
    
    print(f"[{i}/{len(partition_files)}] {state_name} ...", end=" ", flush=True)

    sql = f"""
        SELECT
            f.bldg_gmlid,
            f.bldg_function,
            f.bldg_volume,
            f.roof_area,
            f.footprint_area,
            g.AGS AS ags_vg25,
            g.GEN AS gemeinde_name,
            '{state_name}' AS source_partition,
            '{short_id}' AS state_code
        FROM (
            SELECT
                bldg_gmlid,
                bldg_function,
                bldg_volume,
                roof_area,
                footprint_area,
                ST_Centroid(geometry) AS centroid
            FROM read_parquet('{pf.as_posix()}')
            WHERE bldg_function LIKE '{BLDG_FUNCTION_PREFIX}%'
        ) f
        LEFT JOIN gemeinden g
            ON g.state_code = '{short_id}'
            AND ST_Within(f.centroid, g.geom_t)
    """

    if first_partition:
        con.execute(f"CREATE TABLE footprints_with_ags AS {sql}")
        first_partition = False
    else:
        con.execute(f"INSERT INTO footprints_with_ags {sql}")

    # Count unmatched for this partition
    n_unmatched = con.execute(f"""
        SELECT COUNT(*) FROM footprints_with_ags
        WHERE source_partition = '{state_name}' AND ags_vg25 IS NULL
    """).fetchone()[0]

    n_total = con.execute(f"""
        SELECT COUNT(*) FROM footprints_with_ags
        WHERE source_partition = '{state_name}'
    """).fetchone()[0]

    unmatched_count += n_unmatched
    total_count += n_total

    n_assigned = n_total - n_unmatched

    print(f"{n_assigned:,} assigned, {n_unmatched:,} unmatched, {time.time()-t0:.1f}s")

# Final summary
print(f"\n{'='*60}")
print(f"Spatial join complete — Exact match results")
print(f"{'='*60}")
print(f"Total footprints processed:  {total_count:>12,}")
print(f"Assigned (exact match):      {total_count - unmatched_count:>12,} ({(total_count - unmatched_count)/total_count*100:.6f}%)")
print(f"Unmatched:                   {unmatched_count:>12,} ({unmatched_count/total_count*100:.6f}%)")

# %% [markdown]
# ### Results from the Full Run
#
# | Metric | Value |
# |--------|-------|
# | Total footprints processed | 52,131,093 |
# | Assigned (exact match) | 52,130,838 (99.9995%) |
# | Unmatched | 255 (0.0005%) |
#
# > **Note:** 255 buildings were not assigned to any municipality, as their centroid could not be matched to a geometry within the same federal state. This can occur in border regions. Overall, this affects only 0.0005% of buildings — for the scope of this analysis, we leave these unmatched. If higher completeness is required, a fallback join (e.g., nearest-neighbor within a search radius of 25 meters) could be applied.
#
# ## 3.4 Aggregating to Municipality Level
#
# Now that each building footprint has been assigned to a municipality (via the spatial join to VG25 geometries), we can aggregate the footprints to municipality level (`ags`).
#
# This produces the analytical dataset used in Chapter 2 — one row per municipality with aggregated building statistics.
#
# We compute for each municipality:
#
# | Column | Description |
# |--------|-------------|
# | `n_buildings` | Number of buildings |
# | `total_volume_m3` | Sum of building volumes |
# | `avg_volume_m3` | Average building volume |
# | `total_roof_area_m2` | Sum of roof areas |
# | `avg_roof_area_m2` | Average roof area |
# | `total_footprint_m2` | Sum of footprint areas |
# | `avg_footprint_m2` | Average footprint area |
#
# The aggregation is performed by grouping the joined footprints by `ags_vg25` (the municipality code from the VG25 join) and `gemeinde_name`.

# %%
# ============================================================
# Aggregate building stats by AGS
# ============================================================
# This code is provided for full reproducibility.
# It requires the footprints_with_ags table from Section 3.3.

print("Aggregating by AGS...")

agg_df = con.execute("""
    SELECT
        ags_vg25                                AS ags,
        gemeinde_name,
        COUNT(*)                                AS n_buildings,
        SUM(bldg_volume)                        AS total_volume_m3,
        ROUND(AVG(bldg_volume), 1)              AS avg_volume_m3,
        SUM(roof_area)                          AS total_roof_area_m2,
        ROUND(AVG(roof_area), 1)                AS avg_roof_area_m2,
        SUM(footprint_area)                     AS total_footprint_m2,
        ROUND(AVG(footprint_area), 1)           AS avg_footprint_m2
    FROM footprints_with_ags
    WHERE ags_vg25 IS NOT NULL
    GROUP BY ags_vg25, gemeinde_name
    ORDER BY ags_vg25
""").df()

print(f"Aggregated: {len(agg_df):,} municipalities")
print(f"Total buildings: {agg_df['n_buildings'].sum():,}")
print(f"Total volume: {agg_df['total_volume_m3'].sum():,.0f} m³")
print(f"Total roof area: {agg_df['total_roof_area_m2'].sum():,.0f} m²")
print(f"Total footprint area: {agg_df['total_footprint_m2'].sum():,.0f} m²")

# %% [markdown]
# ### Results from the Full Run
#
# | Metric | Value |
# |--------|-------|
# | Municipalities | 10,925 |
# | Total buildings | 52,130,838 |
# | Total volume | 46,991,275,341 m³ |
# | Total roof area | 6,938,484,974 m² |
# | Total footprint area | 6,068,971,900 m² |
#
# > **Note:** The municipality-level dataset contains one row per municipality (Gemeinde) with aggregated building statistics. This is the input for Chapter 2, where we join it with RegioStaR classifications and aggregate to VWG level for analysis.
#
# ### Save the Municipality-Level Dataset
#
# We save this aggregated data to disk. This is the {doc}`input for 2.  Analyzing Building Stock Patterns <203b_analysis>`.

# %%
# ============================================================
# Save to disk (CSV + Parquet)
# ============================================================
# This code is provided for full reproducibility.

OUTPUT_DIR = ROOT / "data" / "processed"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Save as CSV (primary format – accessible)
agg_df.to_csv(OUTPUT_DIR / "3d_building_metrics_germany_2024_stats_by_municipality.csv", index=False)

# Save as Parquet (optional – for performance)
agg_df.to_parquet(OUTPUT_DIR / "3d_building_metrics_germany_2024_stats_by_municipality.parquet", index=False)

print(f"Saved to {OUTPUT_DIR.relative_to(ROOT)}")

# %% [markdown]
# ## 3.6 Performance Considerations
#
# The spatial join was executed on a **Lenovo ThinkStation P8** workstation with the following specifications:
#
# | Component | Specification |
# |-----------|---------------|
# | **Processor** | AMD Ryzen Threadripper PRO 7975WX (32 cores, 64 threads) |
# | **RAM** | 512 GB |
# | **Storage** | NVMe SSD |
# | **OS** | Windows 11 Pro |
#
# **Processing time on this machine:** ~15–25 minutes for the full spatial join (all 16 states).
#
# **Resource requirements:**
#
# | Resource | Minimum | Recommended |
# |----------|---------|-------------|
# | **Disk space** | ~5 GB for raw data + ~1 GB for intermediate files | ~10 GB free |
# | **RAM** | 8 GB | 16–32 GB |
# | **Processing time** | 1–2 hours (laptop) | 15–25 minutes (workstation) |
# | **Software** | DuckDB with spatial extension, Python 3.9+ | — |
#
# > **Note:** The processing time depends heavily on hardware. On a standard laptop with 16 GB RAM, expect **1–2 hours** for the full join. On a high-end workstation (like the one used here), it takes **15–25 minutes**.
#
# **Tips for working with large datasets:**
#
# - Use **GeoParquet** format — columnar storage for efficient queries
# - Use **spatial indexes** (R-tree) for fast joins
# - **Partition** data by state or region for parallel processing
# - **Filter early** — apply the building function filter before the join
# - **Adjust DuckDB memory limits** — set `memory_limit` based on your available RAM
#   
# ## 3.7 Accessing the Full Dataset
#
# The complete dataset is available via ioerDATA:
#
# > Münzinger, Markus, 2026, "3D Building Metrics Germany 2024",  
# > [https://doi.org/10.71830/9CBBWV](https://doi.org/10.71830/9CBBWV), ioerDATA, V1
#
# ### Download Options
#
# **Option 1: Web Interface**
#
# 1. Go to [Münzinger (2026)](https://doi.org/10.71830/9CBBWV)
# 2. Click the "Download" button
# 3. Select individual files or download all
#
# **Option 2: API Access**
#
# ```{code-block} python
# import requests
#
# # Get dataset metadata
# url = "https://data.ioer.de/api/datasets/9CBBWV"
# response = requests.get(url)
# metadata = response.json()
#
# # Download a specific file
# file_url = "https://data.ioer.de/api/access/datafile/XXXXX"
# response = requests.get(file_url)
# with open("sl_3d_building_metrics_2024.parquet", "wb") as f:
#     f.write(response.content)
# ```
#
# ### Where to Place the Files
#
# After downloading, place the files in:
#
# ```
# data/raw/3D_building_metrics_germany_2024/
# ├── bb_3d_building_metrics_2024.parquet
# ├── be_3d_building_metrics_2024.parquet
# ├── ...
# └── th_3d_building_metrics_2024.parquet
# ```
#
# ### Additional Data Files
#
# You also need:
#
# | File | Source | Purpose |
# |------|--------|---------|
# | `DE_VG25.gpkg` | BKG (GeoBasis-DE) | Administrative boundaries |
#
# ---
#
# ## Summary
#
# In this chapter, we documented:
#
# - ✅ The spatial join challenge (57M footprints → 10,925 municipalities)
# - ✅ Our exact-match approach (centroid-in-polygon, state-restricted)
# - ✅ The aggregation to municipality level (`ags`)
# - ✅ Saving the municipality-level dataset for Chapter 2
#
# **Key results:**
#
# | Step | Result |
# |------|--------|
# | Footprints processed | 52,131,093 |
# | Assigned (exact match) | 52,130,838 (99.9995%) |
# | Unmatched | 255 (0.0005%) |
# | Municipalities | 10,925 |
#
# **Key message:** The pipeline transforms raw footprints into comparable municipality-level building statistics. The next steps — adding spatial typologies and analyzing patterns — are covered in Chapter 2.
#
# ---
#
# ## Citation
#
# If you use this dataset or the pipeline in your work, please cite:
#
# ```{code-block} bibtex
# @book{muenzinger2026footprints,
#   title={From Footprints to Building Stock Insights},
#   author={Münzinger, Markus and Behnisch, Martin},
#   year={2026},
#   publisher={IOER}
# }
#
# @dataset{muenzinger2026dataset,
#   title={3D Building Metrics Germany 2024},
#   author={Münzinger, Markus},
#   year={2026},
#   publisher={ioerDATA},
#   doi={10.71830/9CBBWV}
# }
# ```
