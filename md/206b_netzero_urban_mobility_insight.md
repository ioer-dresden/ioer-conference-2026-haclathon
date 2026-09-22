---
jupyter:
  jupytext:
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.3'
      jupytext_version: 1.19.5
  kernelspec:
    display_name: Python 3 (ipykernel)
    language: python
    name: python3
---

<!-- #region -->
# 2. PART TWO
Looking at the facts and figures above, integrated urban development must promote sustainable transportation and infrastructure. Therefore, public transit services are one of the prerequisites for transforming the world toward a net-zero future. Let us explore a national-scale dataset related to urban transportation infrastructure services in Germany. "[ioerDATA](https://data.fdz.ioer.de/)—the Institutional Research Data Repository of the IOER—is a curated dataset on [urban public transit service frequency](https://doi.org/10.71830/ABPCUS)."


## Urban Public Transit Frequency Indicator — Germany

Three analyses:

| # | Analysis | Source |
|---|---|---|
| 1 | Country-level point density of transit stations | `xx_am_transit_frequency_station.gpkg` |
| 2 | City-level summary statistics | `de_transit_frequency_indicator_aggregated_statistics_all_cities.csv` (file id 6215) |
| 3 | City-level frequency EDA + spatial statistics | `data/..._grid_single_cities/<city>/*.gpkg` |

Analyses 3 follows the method of
[1_exploratory_data_analysis](https://github.com/ssujit/public_transit_germany/blob/main/jupyter_notebook/1_exploratory_data_analysis.ipynb) and
[3_spatial_statistics_neighborhood](https://github.com/ssujit/public_transit_germany/blob/main/jupyter_notebook/3_spatial_statistics_neighborhood.ipynb).

### Running this on Colab

Run the cells in order; section 0 installs what Colab lacks and picks up your API token.

To open it, either **File -> Upload notebook** and pick this `.ipynb` (works regardless of
repository visibility), or, if you have linked Colab to GitHub and can see this private
repo, **File -> Open notebook -> GitHub** and search `ssujit/urban_mobiltiy4netzero`.
Once the repository is public this badge works directly:

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ssujit/urban_mobiltiy4netzero/blob/main/scripts/gtfs.ipynb)

**Your token:** add it once as a Colab secret named `IOER_API_TOKEN` (key icon in the left
sidebar, with "Notebook access" enabled) and it is picked up automatically. Otherwise you
are prompted for it, hidden as you type. Either way the token is never written into the
notebook, so the file stays safe to commit.

**Access:** the account behind the token needs download rights on this DOI. The dataset
custodian's own account has them; a participant account generally does not until access is
granted (see section 1, which checks this before anything else runs).

### Two things to know before running

1. **Almost every file in this dataset is access-restricted.** You need an ioerDATA API
   token (ioerDATA → your account → API Token). Set it as `IOER_API_TOKEN` in your
   environment, or paste it when prompted below.
2. **Column naming differs from the reference notebooks.** The per-city grid files use
   `fi` for the frequency indicator (the reference EDA notebook says `pti`, because it
   reads a differently-named copy from GitHub). The INSPIRE grid CSV uses `pti_<slot>`.
   This notebook uses `fi`.
<!-- #endregion -->

## 0 · Environment

```python
# Dependencies. Safe to re-run; already-satisfied packages are skipped.
# Colab already has pandas/matplotlib/seaborn and usually geopandas, so only the
# spatial-statistics stack and the fast OGR reader normally need installing.
import importlib.util    # NB: plain `import importlib` does not expose .util
import sys

IN_COLAB = "google.colab" in sys.modules

PIP_NAME = {"sklearn": "scikit-learn"}          # import name -> pip name

missing = [m for m in ("geopandas", "pyogrio", "mapclassify",
                       "esda", "libpysal", "splot", "sklearn")
           if importlib.util.find_spec(m) is None]

if missing:
    pkgs = " ".join(PIP_NAME.get(m, m) for m in missing)
    print("installing:", pkgs)
    %pip install -q {pkgs}
    print("\nIf an import below fails, restart the runtime "
          "(Runtime -> Restart session) and re-run from here.")
else:
    print("all dependencies already present")
```

```python
import os
import sys
import warnings
from pathlib import Path
from getpass import getpass

import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import seaborn as sns
import requests

warnings.filterwarnings("ignore")
sns.set_theme(style="whitegrid")
plt.rcParams["figure.dpi"] = 110

IN_COLAB = "google.colab" in sys.modules   # restated so this cell stands alone

print(f"python {sys.version.split()[0]} | geopandas {gpd.__version__} | "
      f"pandas {pd.__version__} | matplotlib {plt.matplotlib.__version__}")
print(f"running on Colab: {IN_COLAB}")
```

## 1 · Connect to ioerDATA and index the dataset

Rather than hard-coding file ids (which change between dataset versions), pull the file
listing once and build a lookup table. Every download below resolves its id through this
index.

```python
BASE_URL = "https://data.fdz.ioer.de"
DOI = "doi:10.71830/ABPCUS"

# Token from the environment if present, otherwise prompt (input stays hidden).


def get_api_token():
    """Colab secret -> environment variable -> hidden prompt."""
    if IN_COLAB:
        try:
            from google.colab import userdata
            token = userdata.get("IOER_API_TOKEN")
            if token:
                print("token loaded from Colab secrets")
                return token.strip()
        except Exception:
            pass              # secret not set, or access not granted to this notebook
    token = os.environ.get("IOER_API_TOKEN")
    if token:
        print("token loaded from the environment")
        return token.strip()
    return getpass("ioerDATA API token: ").strip()


api_token = get_api_token()
headers = {"X-Dataverse-key": api_token}

resp = requests.get(
    f"{BASE_URL}/api/datasets/:persistentId/",
    params={"persistentId": DOI},
    headers=headers,
    timeout=60,
)
resp.raise_for_status()

files = resp.json()["data"]["latestVersion"]["files"]

index = pd.DataFrame(
    [
        {
            "id": f["dataFile"]["id"],
            "filename": f["dataFile"]["filename"],
            "directory": f.get("directoryLabel", ""),
            "mb": round(f["dataFile"].get("filesize", 0) / 1e6, 2),
            "restricted": f.get("restricted", False),
        }
        for f in files
    ]
)

print(f"{len(index)} files, {index.mb.sum():.0f} MB total, "
      f"{index.restricted.sum()} restricted")

# --- Permission check -------------------------------------------------------
# A valid token is not the same as access. Every analysis file in this dataset is
# restricted, and the token only authenticates you; the data custodian still has to
# grant download rights. Check before doing anything else.
me = requests.get(f"{BASE_URL}/api/users/:me", headers=headers, timeout=30).json()
print(f"authenticated as {me['data']['displayName']} (id {me['data']['id']})")

probe = index[index.filename ==
              "de_transit_frequency_indicator_aggregated_statistics_all_cities.csv"].iloc[0]
perm = requests.get(f"{BASE_URL}/api/access/datafile/{probe.id}/userPermissions",
                    headers=headers, timeout=30).json()["data"]

if perm["canDownloadFile"]:
    print("access granted - the analyses below will run")
else:
    print(
        "\nNO DOWNLOAD ACCESS to the restricted files.\n"
        "Neither downloading nor streaming can work until this is granted: both hit the\n"
        "same endpoint and both return 403. Request access per file with\n\n"
        f'    requests.post(f"{{BASE_URL}}/api/access/datafile/{{probe.id}}/requestAccess",\n'
        "                  headers=headers, timeout=30)\n\n"
        "or use the Request Access button on the file's ioerDATA page, then wait for the\n"
        "custodian (s.sikder@ioer.de) to approve."
    )

index[index.directory.isin(["", "data"])]
```

```python
# Colab runtimes are wiped when the session ends. Set USE_DRIVE = True to keep the
# downloads in your Google Drive so a later session reuses them instead of refetching.
USE_DRIVE = False

if IN_COLAB and USE_DRIVE:
    from google.colab import drive
    drive.mount("/content/drive")
    DATA_DIR = Path("/content/drive/MyDrive/ioer_transit/data/raw")
else:
    DATA_DIR = Path("data/raw")


def fetch(filename, directory=None, overwrite=False):
    """Download one dataset file by name, cached under data/raw/<directory>/.

    Returns the local Path. Re-running is free: an existing file is reused.
    """
    if "index" not in globals():
        raise RuntimeError("Run section 1 first - it authenticates and builds `index`.")

    hits = index[index.filename == filename]
    if directory is not None:
        hits = hits[hits.directory == directory]
    if len(hits) == 0:
        raise FileNotFoundError(f"{filename!r} is not in this dataset version")
    if len(hits) > 1:
        raise ValueError(
            f"{filename!r} is ambiguous; pass directory= one of "
            f"{hits.directory.tolist()}"
        )
    row = hits.iloc[0]

    out = DATA_DIR / row.directory / row.filename
    if out.exists() and not overwrite:
        return out
    out.parent.mkdir(parents=True, exist_ok=True)

    print(f"downloading {row.filename} ({row.mb} MB) ...", end=" ", flush=True)
    r = requests.get(
        f"{BASE_URL}/api/access/datafile/{row.id}",
        headers=headers,
        stream=True,
        timeout=300,
    )
    if r.status_code in (401, 403):
        raise PermissionError(
            f"No access to {row.filename}. This file is restricted — check that your "
            "token is valid and that access has been granted for this dataset."
        )
    r.raise_for_status()

    with open(out, "wb") as fh:
        for chunk in r.iter_content(1024 * 1024):
            fh.write(chunk)
    print("done")
    return out


print(f"cache: {DATA_DIR.resolve()}")
```

### Streaming instead of downloading

ioerDATA serves `206 Partial Content` and advertises `Accept-Ranges: bytes`, so GDAL can
read a remote GeoPackage through `/vsicurl` and pull only the pages it needs — no file on
disk. The helpers below do that.

**When streaming is worth it:** reading the schema, or pulling a bbox/column subset out of
a large layer. Fetching 1,200 features from the 106 MB national station layer touches a few
MB instead of all of it.

**When it is not:** reading a whole layer. A GeoPackage is a SQLite database, so a full
table scan becomes thousands of small range requests — measurably slower than one bulk
download. For the per-city grids (100–370 KB) always just `fetch()` them.

```python
import io

# GDAL passes these to libcurl on every /vsicurl request.
os.environ["GDAL_HTTP_HEADERS"] = f"X-Dataverse-key: {api_token}"
os.environ["CPL_VSIL_CURL_USE_HEAD"] = "NO"     # Dataverse HEAD omits Content-Length
os.environ["GDAL_HTTP_MULTIRANGE"] = "YES"      # coalesce reads into one request
os.environ["GDAL_HTTP_MERGE_CONSECUTIVE_RANGES"] = "YES"
os.environ["VSI_CACHE"] = "TRUE"
os.environ["VSI_CACHE_SIZE"] = str(64 * 1024 * 1024)


def _row(filename, directory=None):
    hits = index[index.filename == filename]
    if directory is not None:
        hits = hits[hits.directory == directory]
    if len(hits) != 1:
        raise ValueError(f"{filename!r} matched {len(hits)} files; pass directory=")
    return hits.iloc[0]


def remote_url(filename, directory=None):
    """GDAL virtual path for a dataset file — readable without downloading it."""
    return f"/vsicurl/{BASE_URL}/api/access/datafile/{_row(filename, directory).id}"


def read_remote(filename, directory=None, **kwargs):
    """Read a layer straight off the server.

    Pass bbox=(minx, miny, maxx, maxy) and/or columns=[...] to pull a subset —
    that is the case where streaming beats downloading.
    """
    return gpd.read_file(remote_url(filename, directory), engine="pyogrio", **kwargs)


def read_remote_csv(filename, directory=None, **kwargs):
    """Stream a CSV into a DataFrame without writing it to disk."""
    r = requests.get(f"{BASE_URL}/api/access/datafile/{_row(filename, directory).id}",
                     headers=headers, timeout=300)
    r.raise_for_status()
    return pd.read_csv(io.BytesIO(r.content), **kwargs)


# Schema of the 106 MB national station layer, without downloading it:
#   pyogrio.read_info(remote_url("wk_am_transit_frequency_station.gpkg",
#                                "other/transit_frequency_station"))
print("streaming helpers ready: remote_url / read_remote / read_remote_csv")
```

> **Note on bulk download.** The full dataset is ~2.5 GB (a 1.4 GB road network, 12 station
> layers of 20–210 MB each, and 1,158 per-city grids). Fetch only what each analysis needs
> — which is what `fetch()` above does.


## 2 · Analysis 1 — Country-level point density

Station-level service frequency for all of Germany. The dataset ships each time slot twice,
as GeoJSON and GeoPackage; the GeoPackage is half the size and parses far faster, so use it
(`wk_am_transit_frequency_station.gpkg`, 106 MB — the 211 MB GeoJSON at file id 6268 holds
the same data).

```python
STATION_SLOT = "wk_am"   # wk_am | wk_pm | sat_am | sat_pm | sun_am | sun_pm

stations_path = fetch(f"{STATION_SLOT}_transit_frequency_station.gpkg",
                      directory="other/transit_frequency_station")

stations = gpd.read_file(stations_path, engine="pyogrio")
print(f"{len(stations):,} station records | CRS {stations.crs}")
stations.head()
```

```python
# The station layer's fields are not documented in the dataset README, so inspect them
# and pick the frequency column rather than assuming a name.
print(stations.dtypes, end="\n\n")

numeric_cols = stations.select_dtypes("number").columns.tolist()
print("numeric columns:", numeric_cols)

# Prefer an explicit frequency field; fall back to the first numeric column.
for candidate in ("fi", "perH_sum", "freq", "count", "Value"):
    if candidate in stations.columns:
        WEIGHT_COL = candidate
        break
else:
    WEIGHT_COL = numeric_cols[0]

print(f"\nusing WEIGHT_COL = {WEIGHT_COL!r}")
stations[WEIGHT_COL].describe()
```

```python
# Project to ETRS89 / LAEA Europe (EPSG:3035) — the dataset's own grid CRS, and an
# equal-area projection, so hexagon counts are comparable across the country.
stations_3035 = stations.to_crs(3035)
x = stations_3035.geometry.x.to_numpy()
y = stations_3035.geometry.y.to_numpy()

boundaries = gpd.read_file(
    fetch("de_city_admin_boundary.gpkg", directory="other"), engine="pyogrio"
).to_crs(3035)

print(f"{len(boundaries)} city boundaries | bounds {stations_3035.total_bounds.round(0)}")
```

```python
fig, axes = plt.subplots(1, 2, figsize=(15, 9), constrained_layout=True)

# Left: station count per hexagon (where stations are).
hb = axes[0].hexbin(x, y, gridsize=140, bins="log", cmap="magma_r", mincnt=1, linewidths=0)
axes[0].set_title(f"Station density — {STATION_SLOT}\n(count per hexagon, log scale)")
fig.colorbar(hb, ax=axes[0], shrink=0.6, label="stations per hexagon")

# Right: mean service frequency per hexagon (how good the service is).
hb2 = axes[1].hexbin(
    x, y, C=stations_3035[WEIGHT_COL].to_numpy(),
    reduce_C_function=np.mean, gridsize=140, cmap="viridis", mincnt=1, linewidths=0,
)
axes[1].set_title(f"Mean {WEIGHT_COL} — {STATION_SLOT}\n(per hexagon)")
fig.colorbar(hb2, ax=axes[1], shrink=0.6, label=f"mean {WEIGHT_COL}")

for ax in axes:
    boundaries.boundary.plot(ax=ax, color="0.35", linewidth=0.3, zorder=3)
    ax.set_aspect("equal")
    ax.set_axis_off()

fig.suptitle("Germany — transit station point density (EPSG:3035)", fontsize=14)
plt.show()
```

```python
# Save for reuse outside the notebook.
OUT = Path("outputs/figures")
OUT.mkdir(parents=True, exist_ok=True)
fig.savefig(OUT / f"station_density_{STATION_SLOT}.png", dpi=200, bbox_inches="tight")
print(f"saved {OUT / f'station_density_{STATION_SLOT}.png'}")
```

## 3 · Analysis 2 — City-level statistics

File id **6215**, `de_transit_frequency_indicator_aggregated_statistics_all_cities.csv`:
one row per city × time slot, with `min`, `max`, `mean`, `median`, `std_dev` of the
frequency indicator, plus the official `ags` regional code for joining to other statistics.

```python
stats = pd.read_csv(fetch(
    "de_transit_frequency_indicator_aggregated_statistics_all_cities.csv",
    directory="data",
))

print(f"{stats.city.nunique()} cities × {stats.day_time.nunique()} time slots "
      f"= {len(stats)} rows")
print("slots:", sorted(stats.day_time.unique()))
stats.head()
```

```python
SLOT_ORDER = ["wk_am", "wk_pm", "sat_am", "sat_pm", "sun_am", "sun_pm"]
stats["day_time"] = pd.Categorical(stats.day_time, SLOT_ORDER, ordered=True)

stats.groupby("day_time", observed=True)[["mean", "median", "std_dev", "max"]].describe().T
```

```python
# Distribution of city mean frequency indicator, by time slot.
fig, axes = plt.subplots(1, 2, figsize=(14, 5), constrained_layout=True)

sns.boxplot(data=stats, x="mean", y="day_time", hue="day_time",
            order=SLOT_ORDER, palette="viridis", legend=False, ax=axes[0])
axes[0].set(title="City mean frequency indicator by time slot",
            xlabel="mean fi", ylabel="")

for slot in SLOT_ORDER:
    sns.kdeplot(stats.loc[stats.day_time == slot, "mean"],
                label=slot, ax=axes[1], linewidth=1.8)
axes[1].set(title="Density of city means", xlabel="mean fi")
axes[1].legend(title="slot")

plt.show()
```

```python
# Top and bottom 15 cities on weekday morning service.
wk = stats[stats.day_time == "wk_am"].sort_values("mean", ascending=False)
ends = pd.concat([wk.head(15).assign(group="Top 15"),
                  wk.tail(15).assign(group="Bottom 15")])

fig, ax = plt.subplots(figsize=(9, 10), constrained_layout=True)
sns.barplot(data=ends, x="mean", y="city", hue="group",
            palette={"Top 15": "#1b7837", "Bottom 15": "#c0504d"}, dodge=False, ax=ax)
ax.set(title="Weekday morning (06:00–08:59) mean transit frequency indicator",
       xlabel="mean fi", ylabel="")
plt.show()
```

```python
# Heatmap: the 30 best-served cities across all six slots.
top30 = wk.head(30).city
grid = (stats[stats.city.isin(top30)]
        .pivot(index="city", columns="day_time", values="mean")
        .reindex(columns=SLOT_ORDER)
        .sort_values("wk_am", ascending=False))

fig, ax = plt.subplots(figsize=(8, 11), constrained_layout=True)
sns.heatmap(grid, cmap="viridis", annot=True, fmt=".1f",
            cbar_kws={"label": "mean fi"}, linewidths=0.4, ax=ax)
ax.set(title="Mean frequency indicator — 30 best-served cities", xlabel="", ylabel="")
plt.show()
```

```python
# Weekend service retention: how much of weekday morning service survives to Sunday.
wide = stats.pivot(index="city", columns="day_time", values="mean").reindex(
    columns=SLOT_ORDER)
wide["sunday_retention"] = wide["sun_am"] / wide["wk_am"]

print(wide["sunday_retention"].describe().round(3), end="\n\n")
print("Weakest Sunday service relative to weekday:")
print(wide["sunday_retention"].nsmallest(10).round(3))

fig, ax = plt.subplots(figsize=(11, 5), constrained_layout=True)
sns.scatterplot(data=wide.reset_index(), x="wk_am", y="sun_am",
                size="sunday_retention", hue="sunday_retention",
                palette="RdYlGn", sizes=(15, 160), ax=ax)
lim = [0, wide[["wk_am", "sun_am"]].to_numpy().max() * 1.05]
ax.plot(lim, lim, "k--", linewidth=0.8, label="parity")
ax.set(title="Sunday morning vs weekday morning service, by city",
       xlabel="weekday AM mean fi", ylabel="Sunday AM mean fi", xlim=lim, ylim=lim)
ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left")
plt.show()
```

## 3b · Service inequality within cities

Two cities with the same mean can be very different: one spread evenly, one a dense core
and nothing else. `std_dev`, `mean` and `median` are already in the statistics table.

```python
am = stats[stats.day_time == "wk_am"].set_index("city")

ineq = pd.DataFrame({
    "mean": am["mean"],
    "cv": am["std_dev"] / am["mean"],              # spread relative to level
    "skew_gap": (am["mean"] - am["median"]) / am["mean"],   # >0 = a few hot cells
}).dropna()

ineq.describe().round(2)
```

```python
fig, ax = plt.subplots(figsize=(8, 6), constrained_layout=True)
ax.scatter(ineq["mean"], ineq["cv"], s=18, alpha=0.7)

mx, my = ineq["mean"].median(), ineq["cv"].median()
ax.axvline(mx, c="k", lw=0.8, ls="--")
ax.axhline(my, c="k", lw=0.8, ls="--")

for xf, yf, txt in [(0.97, 0.97, "high service\nuneven"),
                    (0.03, 0.97, "low service\nuneven"),
                    (0.97, 0.03, "high service\neven"),
                    (0.03, 0.03, "low service\neven")]:
    ax.text(xf, yf, txt, transform=ax.transAxes, fontsize=8, color="crimson",
            ha="right" if xf > 0.5 else "left", va="top" if yf > 0.5 else "bottom")

ax.set(xlabel="mean fi (weekday AM)", ylabel="coefficient of variation",
       title="Service level vs evenness")
plt.show()
```

```python
print("most uneven:\n", ineq.nlargest(8, "cv").round(2), "\n")
print("most even:\n", ineq.nsmallest(8, "cv").round(2))
```

## 3c · Weekly service profiles

Dividing each city by its own peak removes the level and leaves the *shape* of its week,
so cities can be grouped by when they run service rather than how much.

```python
from sklearn.cluster import KMeans

prof = stats.pivot(index="city", columns="day_time", values="mean").reindex(
    columns=SLOT_ORDER).dropna()

shape = prof.div(prof.max(axis=1), axis=0)          # level removed
shape["cluster"] = KMeans(4, n_init=10, random_state=0).fit_predict(shape[SLOT_ORDER])

shape.cluster.value_counts().sort_index()
```

```python
fig, ax = plt.subplots(figsize=(8, 5), constrained_layout=True)

for c, g in shape.groupby("cluster"):
    ax.plot(SLOT_ORDER, g[SLOT_ORDER].mean(), marker="o", label=f"type {c} (n={len(g)})")

ax.set(ylabel="share of the city's own peak", title="Weekly service profiles")
ax.legend()
plt.show()
```

```python
for c, g in shape.groupby("cluster"):
    print(f"type {c}: {', '.join(g.index[:6])}")
```

## 4 · Analysis 3 — City-level frequency EDA

Per-city 1 km grids, six time slots each. Fields (per the dataset README):
`fid`, `Value` (network distance, m), `grid_name`, `net_dis` (rounded), `perH_sum`
(aggregation per hour), **`fi`** (the frequency indicator), `city`, `geometry`.

```python
# Any of the 193 cities. The folder name is the slug; filenames follow <slot>_<slug>.gpkg,
# with a few irregular spellings — so select on the directory, not the filename.
CITY = "dresden"

city_dir = f"data/de_transit_frequency_indicator_grid_single_cities/{CITY}"
available = index[index.directory == city_dir]
if available.empty:
    slugs = (index[index.directory.str.contains("single_cities", na=False)]
             .directory.str.rsplit("/", n=1).str[-1].unique())
    raise ValueError(f"Unknown city {CITY!r}. Available: {sorted(slugs)[:20]} ...")

grids = {}
for _, row in available.iterrows():
    slot = "_".join(row.filename.split("_")[:2])          # e.g. "wk_am"
    grids[slot] = gpd.read_file(fetch(row.filename, directory=city_dir),
                                engine="pyogrio")

grids = {s: grids[s] for s in SLOT_ORDER if s in grids}
for slot, gdf in grids.items():
    print(f"{slot:7s} {len(gdf):5d} cells   fi: "
          f"{gdf.fi.min():.1f}–{gdf.fi.max():.1f}  mean {gdf.fi.mean():.1f}")

grids["wk_am"].head()
```

```python
# Choropleth of fi across all six slots, quantile-classified so classes are comparable.
fig, axes = plt.subplots(3, 2, figsize=(13, 17), constrained_layout=True)

for ax, (slot, gdf) in zip(axes.flatten(), grids.items()):
    gdf.plot("fi", cmap="viridis", scheme="quantiles", k=5,
             edgecolor="white", linewidth=0.1, legend=True,
             legend_kwds={"loc": "upper left", "fontsize": 7}, ax=ax)
    ax.set_title(f"{CITY.title()} — {slot}")
    ax.set_axis_off()

fig.suptitle(f"Transit frequency indicator, {CITY.title()} (1 km grid)", fontsize=15)
plt.show()
```

```python
# Distributions. fi is strongly right-skewed, which is why the spatial statistics
# section below works on a transformed variable.
fig, axes = plt.subplots(3, 2, figsize=(13, 11), constrained_layout=True)

for ax, (slot, gdf) in zip(axes.flatten(), grids.items()):
    ax.hist(gdf.fi.dropna(), bins=40, color="#3182bd", edgecolor="white", linewidth=0.4)
    ax.set(title=slot, xlabel="fi", ylabel="cells")

fig.suptitle(f"{CITY.title()} — distribution of fi by time slot", fontsize=14)
plt.show()
```

```python
# Side-by-side comparison across slots.
# NOTE: drawn with seaborn rather than plt.boxplot on purpose. The matplotlib keyword
# for category labels changed (`labels=` -> `tick_labels=`) and `vert=False` was
# superseded by `orientation=`, so raw boxplot calls break on either side of that
# version boundary. Colab and a local env rarely ship the same matplotlib.
fig, axes = plt.subplots(1, 2, figsize=(14, 5), constrained_layout=True)

long = pd.concat([g[["fi"]].assign(slot=slot) for slot, g in grids.items()])
sns.boxplot(data=long, x="fi", y="slot", hue="slot", order=list(grids),
            palette="viridis", legend=False, ax=axes[0])
axes[0].set(title=f"{CITY.title()} — fi by time slot", xlabel="fi", ylabel="")

for slot, gdf in grids.items():
    sns.kdeplot(gdf.fi.dropna(), label=slot, ax=axes[1], linewidth=1.8)
axes[1].set(title="Kernel density of fi", xlabel="fi")
axes[1].legend(title="slot")

plt.show()
```

```python
# Interactive map — pan/zoom to inspect individual cells.
grids["wk_am"].explore(column="fi", cmap="viridis", scheme="quantiles", k=5,
                       tiles="CartoDB positron", tooltip=["grid_name", "fi", "net_dis"])
```

## 5 · Analysis 3b — Spatial statistics and neighbourhood clustering

Following the reference spatial-statistics notebook: transform `fi` to tame its skew,
build a k-nearest-neighbour spatial weights matrix, then compute global Moran's I,
local Moran (LISA) clusters, and Getis-Ord \(G_i^*\) hot/cold spots.

```python
from libpysal import weights
from esda.moran import Moran, Moran_Local
from esda.getisord import G_Local
from splot import esda as esdaplot

SLOT = "wk_am"
city = grids[SLOT].copy().reset_index(drop=True)

# Double square root, as in the reference notebook: fi is heavily right-skewed and the
# Moran statistics assume a roughly symmetric variable.
city["fi_sqrt"] = np.sqrt(city["fi"])
city["fi_2ndsqrt"] = np.sqrt(city["fi_sqrt"])

fig, axes = plt.subplots(1, 3, figsize=(14, 4), constrained_layout=True)
for ax, col in zip(axes, ["fi", "fi_sqrt", "fi_2ndsqrt"]):
    sns.histplot(city[col].dropna(), kde=True, ax=ax, color="#3182bd")
    ax.set_title(f"{col}  (skew {city[col].skew():.2f})")
fig.suptitle(f"{CITY.title()} {SLOT} — effect of the variance-stabilising transform")
plt.show()
```

```python
# k=8 nearest neighbours, row-standardised (each row of weights sums to 1).
w = weights.distance.KNN.from_dataframe(city, k=8)
w.transform = "R"

VAR = "fi_2ndsqrt"
city["w_" + VAR] = weights.lag_spatial(w, city[VAR])
city[VAR + "_std"] = city[VAR] - city[VAR].mean()
city["w_" + VAR + "_std"] = weights.lag_spatial(w, city[VAR + "_std"])

print(f"{w.n} cells, mean neighbours {w.mean_neighbors:.1f}")
```

```python
# Global Moran's I — is high frequency spatially clustered at all?
values = city[VAR].to_numpy(dtype=float)   # esda's numba kernels reject int input
moran = Moran(values, w)
print(f"Moran's I = {moran.I:.4f}   E[I] = {moran.EI:.4f}   "
      f"z = {moran.z_sim:.2f}   pseudo p = {moran.p_sim:.4f}")

# Moran scatterplot: value against its spatial lag, split into the four quadrants.
fig, ax = plt.subplots(figsize=(6.5, 6.5), constrained_layout=True)
sns.regplot(x=VAR + "_std", y="w_" + VAR + "_std", data=city, ci=None,
            scatter_kws={"s": 8, "alpha": 0.5}, line_kws={"color": "crimson"}, ax=ax)
ax.axvline(0, c="k", alpha=0.5)
ax.axhline(0, c="k", alpha=0.5)

# NOTE: Series.ptp() was removed in pandas 3; use np.ptp on the array.
xr = city[VAR + "_std"].to_numpy()
yr = city["w_" + VAR + "_std"].to_numpy()
for label, xf, yf in [("HH", 0.75, 0.80), ("HL", 0.75, 0.10),
                      ("LH", 0.10, 0.80), ("LL", 0.10, 0.10)]:
    ax.text(xr.min() + xf * np.ptp(xr), yr.min() + yf * np.ptp(yr),
            label, fontsize=18, color="r", alpha=0.7)

ax.set(title=f"Moran scatterplot — {CITY.title()} {SLOT} (I = {moran.I:.3f})",
       xlabel=f"{VAR} (centred)", ylabel="spatial lag")
plt.show()
```

```python
# Local Moran / LISA.
lisa = Moran_Local(values, w)

fig, axs = plt.subplots(2, 2, figsize=(13, 13), constrained_layout=True)
axs = axs.flatten()

# 1 — local statistic
city.assign(Is=lisa.Is).plot(column="Is", cmap="plasma", scheme="quantiles", k=5,
                             edgecolor="white", linewidth=0.1, legend=True,
                             legend_kwds={"fontsize": 7}, ax=axs[0])
axs[0].set_title("Local Moran's $I_i$")

# 2 — quadrant of every cell (p=1 forces all cells to be coloured)
esdaplot.lisa_cluster(lisa, city, p=1, ax=axs[1])
axs[1].set_title("Quadrant (all cells)")

# 3 — which cells are significant
labels = pd.Series(np.where(lisa.p_sim < 0.05, "Significant", "Non-significant"),
                   index=city.index)
city.assign(cl=labels).plot(column="cl", categorical=True, cmap="Paired",
                            edgecolor="white", linewidth=0.1, legend=True,
                            legend_kwds={"fontsize": 8}, ax=axs[2])
axs[2].set_title("Significance (p < 0.05)")

# 4 — significant clusters only
esdaplot.lisa_cluster(lisa, city, p=0.05, ax=axs[3])
axs[3].set_title("Significant clusters (p < 0.05)")

for ax in axs:
    ax.set_axis_off()
fig.suptitle(f"LISA — {CITY.title()} {SLOT}, {VAR}", fontsize=15)
plt.show()
```

```python
# Cluster composition.
# NOTE: pandas 3 removed the top-level pandas.value_counts() the reference notebook uses.
SPOT_LABELS = {0: "Non-significant", 1: "HH", 2: "LH", 3: "LL", 4: "HL"}
city["lisa_label"] = pd.Series(lisa.q * (lisa.p_sim < 0.05), index=city.index).map(
    SPOT_LABELS)

share = city["lisa_label"].value_counts()
print(f"significant cells: {(lisa.p_sim < 0.05).mean() * 100:.1f}%\n")
print(pd.DataFrame({"cells": share, "share_%": (share / len(city) * 100).round(1)}))
```

```python
# Getis-Ord Gi and Gi* — hot spots (clusters of high service) and cold spots.
g_i = G_Local(values, w)
g_i_star = G_Local(values, w, star=True)


def g_map(g, gdf, ax):
    """Plot significant high (hot) and low (cold) clusters from a G_Local result."""
    sig = g.p_sim < 0.05
    gdf.loc[~sig].plot(ax=ax, color="lightgrey", edgecolor="0.8", linewidth=0.1)
    gdf.loc[sig & (g.Zs > 0)].plot(ax=ax, color="red", edgecolor="0.8", linewidth=0.1)
    gdf.loc[sig & (g.Zs < 0)].plot(ax=ax, color="blue", edgecolor="0.8", linewidth=0.1)
    ax.set_title(f"$G_i{'^*' if g.star else ''}$ — {CITY.title()} {SLOT}", size=13)
    ax.set_axis_off()


fig, axes = plt.subplots(1, 2, figsize=(13, 7), constrained_layout=True)
for g, ax in zip([g_i, g_i_star], axes):
    g_map(g, city, ax)

handles = [plt.Line2D([], [], marker="s", linestyle="", markersize=10, color=c, label=l)
           for c, l in [("red", "Hot spot (p<0.05)"), ("blue", "Cold spot (p<0.05)"),
                        ("lightgrey", "Not significant")]]
axes[1].legend(handles=handles, loc="lower right", fontsize=8)
plt.show()
```

```python
fig.savefig(OUT / f"getis_ord_{CITY}_{SLOT}.png", dpi=200, bbox_inches="tight")
print(f"saved {OUT / f'getis_ord_{CITY}_{SLOT}.png'}")
```

## 6 · Appendix — reading the public GTFS feed without downloading it

Access to the restricted files is granted **per dataset**. If you can open one ioerDATA
replication package but not this one, that is a missing grant on this DOI, not a broken
token — and no transfer method works around it, because streaming and downloading hit the
same 403.

What *is* public here are the two raw GTFS feeds the indicator was built from:
`opnv.zip` (181 MB, local/regional transit) and `sbahn.zip` (7.2 MB). Because ioerDATA
serves byte ranges, a zip's central directory can be read from its tail and individual
members pulled out — listing all of `opnv.zip` costs about 65 KiB instead of 181 MB.

```python
import struct
import zlib

GTFS_FEEDS = {"opnv": 6704, "sbahn": 6811}


def _range(file_id, start, end):
    r = requests.get(f"{BASE_URL}/api/access/datafile/{file_id}",
                     headers={**headers, "Range": f"bytes={start}-{end}"}, timeout=120)
    r.raise_for_status()
    return r.content


def _size(file_id):
    r = requests.get(f"{BASE_URL}/api/access/datafile/{file_id}",
                     headers={**headers, "Range": "bytes=0-0"}, timeout=60)
    r.raise_for_status()
    return int(r.headers["Content-Range"].split("/")[1])


def remote_zip_index(file_id):
    """Map member name -> (method, compressed_size, uncompressed_size, local_header_offset).

    Reads only the zip's end-of-central-directory and central directory.
    """
    total = _size(file_id)
    tail = _range(file_id, max(0, total - 65536), total - 1)
    i = tail.rfind(b"PK\x05\x06")
    if i < 0:
        raise ValueError("no end-of-central-directory found; not a zip?")
    cd_size, cd_off = struct.unpack("<II", tail[i + 12:i + 20])
    cd = _range(file_id, cd_off, cd_off + cd_size - 1)

    entries, p = {}, 0
    while p < len(cd) and cd[p:p + 4] == b"PK\x01\x02":
        method, = struct.unpack("<H", cd[p + 10:p + 12])
        csize, usize = struct.unpack("<II", cd[p + 20:p + 28])
        nlen, elen, clen = struct.unpack("<HHH", cd[p + 28:p + 34])
        lho, = struct.unpack("<I", cd[p + 42:p + 46])
        name = cd[p + 46:p + 46 + nlen].decode("utf-8", "replace")
        entries[name] = (method, csize, usize, lho)
        p += 46 + nlen + elen + clen
    return entries


def read_remote_zip_member(file_id, name, index=None):
    """Return one member of a remote zip as bytes, fetching only its own byte range."""
    index = index or remote_zip_index(file_id)
    method, csize, _, lho = index[name]
    lh = _range(file_id, lho, lho + 29)
    nlen, elen = struct.unpack("<HH", lh[26:30])
    start = lho + 30 + nlen + elen
    raw = _range(file_id, start, start + csize - 1)
    return zlib.decompress(raw, -15) if method == 8 else raw


idx = remote_zip_index(GTFS_FEEDS["opnv"])
print(f"opnv.zip contents ({_size(GTFS_FEEDS['opnv']) / 1e6:.0f} MB on the server):")
for name, (_, _, usize, _) in idx.items():
    print(f"  {name:20s} {usize / 1e6:8.1f} MB uncompressed")
```

```python
# Small members stream in instantly. feed_info.txt confirms the feed vintage the
# indicator was derived from.
print(read_remote_zip_member(GTFS_FEEDS["opnv"], "feed_info.txt", idx).decode())

agency = pd.read_csv(io.BytesIO(
    read_remote_zip_member(GTFS_FEEDS["opnv"], "agency.txt", idx)))
routes = pd.read_csv(io.BytesIO(
    read_remote_zip_member(GTFS_FEEDS["opnv"], "routes.txt", idx)))
print(f"{len(agency)} agencies, {len(routes)} routes")
routes.head()
```

> `stop_times.txt` is ~977 MB uncompressed and cannot be pulled apart by range — a zip
> member is a single deflate stream, so any part of it requires the whole member. Computing
> the frequency indicator from scratch means downloading the full feed. The point of this
> section is exploration: you can inspect the feed's structure, agencies and routes for a
> few tens of KiB before committing to that.


## Notes and caveats

- **Restricted access is per dataset.** 1,178 of this dataset's 1,184 files are restricted;
  only `README.md`, the two PDFs and the two GTFS feeds are open. A token that can download
  another ioerDATA package says nothing about this one — check `canDownloadFile` (section 1)
  rather than inferring from a token that works elsewhere. Access is granted by the
  custodian, Sujit Sikder (s.sikder@ioer.de), via Request Access on the file page or
  `POST /api/access/datafile/{id}/requestAccess`.
- **`fi` vs `pti`.** Per-city grids use `fi`; the aggregated INSPIRE grid CSV uses
  `pti_<slot>`. They are the same indicator under different names.
- **Reference-notebook code does not run as-is** on current library versions:
  `plt.boxplot(labels=...)` was removed in matplotlib 3.11 (renamed `tick_labels=`, and
  `vert=` became `orientation=`), `pandas.value_counts()` was removed in pandas 3 (use
  `Series.value_counts()`), and `seaborn.distplot` is deprecated (use `histplot`).
  Because Colab and a local environment rarely ship the same versions, the plots here
  avoid the keywords that moved.
- **If you join to city boundaries later**, zero-pad both sides of `ags` to 8 characters.
  IOER boundary layers store it as `'05911000'`; the statistics CSV drops the leading zero
  (`'5911000'`). An unpadded join silently loses every city in states 01-09 - in a test
  against 165 real city polygons it matched 24 of 165 instead of all of them.
- **One week only.** The indicator covers 17–23 July 2022 — school-holiday season in most
  German states, so service levels may sit below the annual norm.
- **KNN weights on polygons.** `KNN.from_dataframe` uses polygon centroids. On a regular
  1 km grid, k=8 approximates a queen-contiguity neighbourhood; at a city's edge it reaches
  further, since the eight nearest cells may all lie inward.

**Citation** — Sikder, S. K. (2025). *Urban Public Transit Frequency Indicator in Germany.*
IOER Research Data Centre. [doi:10.71830/ABPCUS](https://doi.org/10.71830/ABPCUS). CC BY 4.0.
