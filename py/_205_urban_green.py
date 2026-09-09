# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.5
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% deletable=true tags=["hide-cell"] slideshow={"slide_type": ""} editable=true
import sys, os
from pathlib import Path

# Colab-specific setup
if 'google.colab' in sys.modules:
    if not os.path.exists("ioer-conference-2026-haclathon"):
        # !git clone -q https://github.com/ioer-dresden/ioer-conference-2026-haclathon.git
    # %cd -q ioer-conference-2026-haclathon/notebooks

# Install required packages
pyexec = sys.executable
# !../py/modules/pkginstall.sh "{pyexec}" geopandas matplotlib requests

# %% slideshow={"slide_type": ""} tags=["hide-cell"] editable=true deletable=true
#import cell
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import requests

# %% [markdown] editable=true deletable=true slideshow={"slide_type": ""}
# # 🌿 Urban Green for Climate Regulation
#
# * **Authors**: Marzan Tasnim Oyshi (IOER) 
# * **Topics**: Urban Green Infrastructure, Climate Regulation, Ecosystem Services, Open Data Re-use, Reproducible Research
# *  **Badges**: ![ioerDATA](https://img.shields.io/badge/Data-ioerDATA-green?style=flat-square) ![Dataverse API](https://img.shields.io/badge/Access-Dataverse_API-blueviolet?style=flat-square) ![FAIR Data](https://img.shields.io/badge/Principle-FAIR_Data-brightgreen?style=flat-square) ![Colab](https://img.shields.io/badge/Colab-Tested-yellow?style=flat-square&logo=googlecolab&logoColor=white) ![Jupyter](https://img.shields.io/badge/Jupyter4NFDI-Ready-orange?style=flat-square&logo=jupyter)
# ```{admonition} Summary
# :class: hint
# How much can urban green infrastructure contribute to climate regulation in German cities and how many people benefit from it?
#
# In this chapter, we reuse the openly published ioerDATA replication package **Climate Regulation in Cities** to explore a national ecosystem-service indicator for urban climate regulation.
#
# We will:
#
# - access an openly published replication package,
# - explore spatial indicators for German cities,
# - investigate cooling capacity provided by urban green infrastructure,
# - compare cooling capacity with population benefit,
# - create reproducible maps and visualisations,
# - and explore how the data could support urban planning.
#
# The aim is to demonstrate how published research data can be **reused, explored, and extended**.
# ```
#
# ```{warning}
# This chapter is a work in progress.
# ```
#
# ---
#
# ## 1. Why does urban green matter?
#
# Cities are particularly vulnerable to heat.
#
# Buildings, sealed surfaces, roads, and other artificial surfaces can store heat and contribute to the **urban heat island effect**. Green infrastructure can counteract some of these effects through shading, evapotranspiration, and other local climate-regulation processes.
#
# Urban green infrastructure includes elements such as:
#
# - trees,
# - parks,
# - urban forests,
# - gardens,
# - grass and vegetated surfaces,
# - and other green spaces.
#
# But simply asking **"How green is a city?"** is not enough.
#
# For climate adaptation, we are also interested in:
#
# > **Where does urban green provide cooling capacity, and how many people may benefit from it?**
#
# This notebook explores that question using an openly available research dataset.

# %% [markdown] slideshow={"slide_type": ""} editable=true deletable=true
# ## 2. From publication to reusable research data
#
# The analysis is based on the ioerDATA replication package:
#
# > **Replication package for: Climate Regulation in Cities**
#
# The dataset provides a national indicator of local climate regulation by urban green infrastructure for **165 German cities with more than 50,000 inhabitants**.
#
# It contains information on:
#
# - urban green infrastructure,
# - cooling capacity,
# - population,
# - and the proportion of inhabitants benefiting from climate-regulating ecosystem services.
#
# The replication package accompanies the publication:
#
# *Assessment and Monitoring of Local Climate Regulation in Cities by Green Infrastructure — A National Ecosystem Service Indicator for Germany.*
#
# This gives us an opportunity to move beyond simply reading a scientific publication.
#
# Instead, we can directly inspect and reuse the underlying research data.

# %% [markdown] slideshow={"slide_type": ""} deletable=true editable=true
# ## ♻️ Reproducibility first
#
# A scientific figure is much more useful when we can understand:
#
# 1. **where the data came from,**
# 2. **how it was processed,**
# 3. **which indicators were created,**
# 4. **and how the final visualisation was produced.**
#
# This notebook therefore keeps the complete workflow visible and executable.
#
# The same data can then be reused for questions that were not necessarily part of the original publication.

# %% [markdown] slideshow={"slide_type": ""} deletable=true editable=true
# ## 3. Access the replication package
#
# The dataset is published through **ioerDATA**, which is based on Dataverse.
#
# Instead of manually downloading the GeoPackage, we can retrieve it programmatically.
#
# This is useful because the source of the data becomes part of the analysis itself.

# %% deletable=true slideshow={"slide_type": ""} editable=true
dataset_doi = "doi:10.71830/AFW3N3"

api_url = (
    "https://data.fdz.ioer.de/api/datasets/:persistentId/"
    f"?persistentId={dataset_doi}"
)

metadata = requests.get(api_url).json()
files = metadata["data"]["latestVersion"]["files"]

for item in files:
    print(item["dataFile"]["filename"])

# %% [markdown] deletable=true slideshow={"slide_type": ""} editable=true
# ## 3. Download the replication package
#
# The replication package is published on **ioerDATA** and can be accessed through the Dataverse API.
#
# Some files are public, while others are **restricted** and require authentication. A personal API token allows the notebook to authenticate with ioerDATA and download all files your account is permitted to access.
#
# > ⚠️ **Keep your API token private.** Never save it in the notebook or commit it to GitHub.

# %% deletable=true editable=true slideshow={"slide_type": ""}
from pathlib import Path
from getpass import getpass
import requests

base_url = "https://data.fdz.ioer.de"
persistent_id = "doi:10.71830/AFW3N3"

# Authenticate securely
api_token = getpass("Paste your ioerDATA API token: ")
headers = {"X-Dataverse-key": api_token}

# Get dataset metadata and file list
url = f"{base_url}/api/datasets/:persistentId/"
metadata = requests.get(
    url,
    params={"persistentId": persistent_id},
    headers=headers
).json()

files = metadata["data"]["latestVersion"]["files"]

# Prepare download folder
data_dir = Path("data/raw")
data_dir.mkdir(parents=True, exist_ok=True)

print(f"{len(files)} files found.")

# %% deletable=true editable=true slideshow={"slide_type": ""}
for item in files:
    file = item["dataFile"]
    filename = file["filename"]
    output = data_dir / filename

    response = requests.get(
        f"{base_url}/api/access/datafile/{file['id']}",
        headers=headers,
        stream=True
    )

    if response.status_code in (401, 403):
        print(f"Skipped: {filename} — no permission")
        continue

    response.raise_for_status()

    with open(output, "wb") as f:
        for chunk in response.iter_content(1024 * 1024):
            if chunk:
                f.write(chunk)

    access = "restricted" if item.get("restricted") else "public"
    print(f"Downloaded: {filename} ({access})")

# %% [markdown]
# ## FAIR Data in Practice
#
# This replication package illustrates how the **FAIR principles** can support reproducible research:
#
# - **Findable** — the dataset has a persistent DOI and searchable metadata.
# - **Accessible** — data and metadata can be accessed through ioerDATA and its Dataverse API. Restricted files remain available through controlled access.
# - **Interoperable** — spatial data is provided in standard formats such as GeoPackage.
# - **Reusable** — documentation, metadata and provenance allow the data to be understood and used beyond the original study.
#
# > **FAIR does not necessarily mean open.**  
# > Restricted data can still be FAIR when access conditions are clearly described and authorised users can access the data through a transparent process.

# %% [markdown] editable=true slideshow={"slide_type": ""} deletable=true
# ## 4. Load the spatial data
#
# The main spatial dataset is stored as a GeoPackage. We load it with GeoPandas and inspect the available indicators before mapping them.

# %% editable=true slideshow={"slide_type": ""} deletable=true
import geopandas as gpd
import matplotlib.pyplot as plt

gpkg_path = data_dir / "climate_regulation_in_cities.gpkg"

gdf = gpd.read_file(gpkg_path)

print(f"Features: {len(gdf)}")
print(f"CRS: {gdf.crs}")

gdf.head()

# %% [markdown] editable=true deletable=true slideshow={"slide_type": ""}
# This is the checkpoint where you identify the exact columns for:
#
# >city name, cooling capacity, population benefit

# %% editable=true slideshow={"slide_type": ""} deletable=true
gdf.columns.tolist()

# %% [markdown] deletable=true slideshow={"slide_type": ""} editable=true
# ## 5. Where is climate-regulation capacity high?
#
# Urban green infrastructure provides different levels of cooling capacity across German cities.
#
# Mapping the indicator helps reveal where climate-regulation potential is comparatively high or low.

# %% slideshow={"slide_type": ""} deletable=true editable=true
#prepare map context
import matplotlib.patheffects as pe

value_col = "Pop_Benefit_Percent"
name_col = "GEN"
gdf_wgs = gdf.to_crs("EPSG:4326")

world = gpd.read_file(
    "https://naturalearth.s3.amazonaws.com/110m_cultural/ne_110m_admin_0_countries.zip"
)
germany = world[world["NAME"] == "Germany"]

major_cities = {
    "Berlin", "Hamburg", "München", "Dresden",
    "Köln", "Leipzig", "Frankfurt am Main", "Bremen"
}
labels = gdf_wgs[gdf_wgs[name_col].isin(major_cities)]

# %% deletable=true editable=true slideshow={"slide_type": ""}
#map the indicator
fig, ax = plt.subplots(figsize=(9, 9))

gdf_wgs.plot(
    column=value_col,
    cmap="viridis",
    legend=True,
    edgecolor="white",
    linewidth=0.3,
    ax=ax
)

germany.boundary.plot(ax=ax, color="black", linewidth=0.8)

for _, row in labels.iterrows():
    p = row.geometry.representative_point()
    txt = ax.text(p.x, p.y, row[name_col], fontsize=7, ha="center")
    txt.set_path_effects([pe.withStroke(linewidth=2, foreground="white")])

ax.set_title("Population Benefiting from Urban Climate Regulation")
ax.set_axis_off()

plt.show()

# %% [markdown] slideshow={"slide_type": ""} deletable=true editable=true
# ### What does the map show?
#
# The indicator represents the **share of inhabitants benefiting from the cooling effect of urban green infrastructure**.
#
# The map reveals that this benefit varies between German cities. This shifts the focus from simply asking *where green infrastructure exists* to asking:
#
# > **How effectively does urban green infrastructure provide climate-regulation benefits to people?**

# %% [markdown] editable=true slideshow={"slide_type": ""} deletable=true
# ## 6. From replication to exploration
#
# Reproducing the indicator map is only the starting point.
#
# Because the replication package provides reusable spatial data, we can explore additional questions:
#
# - Which cities show particularly high or low population benefit?
# - How do cities compare with each other?
# - What might these differences mean for urban green planning?

# %% editable=true deletable=true slideshow={"slide_type": ""}
#compare cities
top = gdf.nlargest(10, value_col).sort_values(value_col)

fig, ax = plt.subplots(figsize=(8, 5))

ax.barh(top[name_col], top[value_col])
ax.set_xlabel("Population benefiting (%)")
ax.set_title("Cities with High Population Benefit from UGI")

plt.tight_layout()
plt.show()

# %% [markdown] editable=true slideshow={"slide_type": ""} deletable=true
# ## Try it yourself
#
# Open data makes it possible to move beyond reproduction.
#
# Try changing the analysis:
#
# - Find the cities with the **lowest** population benefit.
# - Select a city you know and compare it with others.
# - Explore another file from the replication package.
#
# > **Replication reproduces evidence. Reuse creates opportunities for new questions.**

# %% [markdown] editable=true deletable=true slideshow={"slide_type": ""}
# ## Conclusion
#
# This example moves from:
#
# **open research data → spatial indicator → city comparison → planning question**
#
# Urban green infrastructure is not only about the amount of green space. Its relevance also depends on the **climate-regulation service it provides and the population that benefits from it**.
#
# The ioerDATA replication package makes this evidence accessible for reproduction, exploration, and further research.

# %% deletable=true slideshow={"slide_type": ""} editable=true
