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

# %% deletable=true tags=["remove-cell"] editable=true slideshow={"slide_type": ""}
# Run this cell to work in colab
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

# %% [markdown] slideshow={"slide_type": ""} editable=true deletable=true
# # 🌿 Urban Green Cooling Benifits with ioerDATA: From API to Insight
#
# * **Authors**: Marzan Tasnim Oyshi (IOER) & Maria Nieswand (IOER)
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

# %% [markdown] slideshow={"slide_type": ""} editable=true deletable=true
# ## Reproducibility first
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

# %% [markdown] editable=true slideshow={"slide_type": ""} deletable=true
# ## 3. Access the replication package
#
# The dataset is published through **ioerDATA**, which is based on Dataverse.
#
# Instead of manually downloading the GeoPackage, we can retrieve it programmatically.
#
# This is useful because the source of the data becomes part of the analysis itself.

# %% [markdown] editable=true slideshow={"slide_type": ""}
# ### Setup
#
# Import the libraries needed for this chapter

# %% editable=true slideshow={"slide_type": "slide"} tags=["hide-input"]
#import cell
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import requests

from pathlib import Path
from getpass import getpass

import geopandas as gpd
import matplotlib.pyplot as plt

import matplotlib.patheffects as pe

from tqdm.auto import tqdm

print("Installed libraries ✓")

# %% [markdown] editable=true slideshow={"slide_type": ""}
# ### Check the dataset contents
#
# Before downloading the data, we first query the ioerDATA API to see which files are included in the replication package.
#
# The request may take a few moments. A loading indicator will appear while the metadata is being retrieved.

# %% slideshow={"slide_type": "slide"} editable=true tags=["hide-input"]
# DOI of the ioerDATA replication package
dataset_doi = "doi:10.71830/AFW3N3"

# Build the Dataverse API URL for the dataset
api_url = (
    "https://data.fdz.ioer.de/api/datasets/:persistentId/"
    f"?persistentId={dataset_doi}"
)

# Show a loading message while requesting the metadata
print("⏳ Retrieving dataset information from ioerDATA...")

# Request metadata from the ioerDATA Dataverse API
response = requests.get(api_url, timeout=60)
response.raise_for_status()

# Convert the API response to JSON
metadata = response.json()

# Extract the files from the latest dataset version
files = metadata["data"]["latestVersion"]["files"]

# Confirm that the request has finished
print(f"✓ Done! Found {len(files)} files:\n")

# Display the available filenames
for item in files:
    print(f"  • {item['dataFile']['filename']}")

# %% [markdown] slideshow={"slide_type": ""} editable=true deletable=true
# ## 3. Download the replication package
#
# The replication package is published on **ioerDATA** and can be accessed through the Dataverse API.
#
# While many files are publicly available, some are **restricted** and require authentication. By creating a free **ioerDATA account**, you can generate a **personal API token** that allows this notebook to securely access all files your account is authorized to use.
#
# **Already have an ioerDATA account?** Simply log in.  
# **New to ioerDATA?** Sign up for an account and follow the steps below to create your personal API token.
#
# ![ioerDATA login](../resources/dataverse.png "ioerDATA login")
# ![ioerDATA API](../resources/dataverse_api.png "ioerDATA API")
#
# > ⚠️ **Keep your API token private.** Never save it in the notebook or commit it to GitHub.

# %% tags=["hide-input"] editable=true slideshow={"slide_type": "slide"}
# ioerDATA Dataverse address and dataset DOI
base_url = "https://data.fdz.ioer.de"
persistent_id = "doi:10.71830/AFW3N3"

# Ask for the personal API token securely.
# The entered token will not be displayed in the notebook.
api_token = getpass("🔑 Paste your ioerDATA API token: ")
headers = {"X-Dataverse-key": api_token}

print("\n⏳ Authenticating and retrieving dataset information...")

# Request metadata for the latest version of the dataset
url = f"{base_url}/api/datasets/:persistentId/"

response = requests.get(
    url,
    params={"persistentId": persistent_id},
    headers=headers,
    timeout=60
)

# Stop with a clear error if the request was unsuccessful
response.raise_for_status()

# Extract the list of files from the API response
metadata = response.json()
files = metadata["data"]["latestVersion"]["files"]

# Create a folder for the downloaded files
data_dir = Path("data/raw")
data_dir.mkdir(parents=True, exist_ok=True)

# Confirm that everything is ready for the download
print(f"✓ Ready! {len(files)} files found.")
print(f"📁 Files will be stored in: {data_dir.resolve()}")

# %% [markdown] slideshow={"slide_type": ""} editable=true
# ### Download the dataset files
#
# The files are now downloaded to a local `data/raw` folder.
#
# A progress bar shows the download status for each file. Restricted files are downloaded only if your ioerDATA account has permission.
#
# If you are running this notebook in **Google Colab**, you can also package the downloaded files into a ZIP archive and download them to your computer.

# %% tags=["hide-input"] slideshow={"slide_type": "slide"} editable=true
# Show where files will be stored
print(f"📁 Download folder:\n{data_dir.resolve()}\n")

# Show the complete list before downloading anything
print(f"📦 {len(files)} files found in the replication package:\n")

for i, item in enumerate(files, start=1):
    file = item["dataFile"]
    filename = file["filename"]
    access = "restricted" if item.get("restricted") else "public"

    print(f"{i:>2}. {filename} ({access})")

print("\n⬇ Starting downloads...\n")

# Download files one by one
for i, item in enumerate(files, start=1):
    file = item["dataFile"]
    filename = file["filename"]
    output = data_dir / filename
    access = "restricted" if item.get("restricted") else "public"

    print(f"\n[{i}/{len(files)}] {filename} ({access})")

    # Request the file as a stream so it can be downloaded in chunks
    response = requests.get(
        f"{base_url}/api/access/datafile/{file['id']}",
        headers=headers,
        stream=True,
        timeout=120
    )

    # Skip restricted files if the account does not have permission
    if response.status_code in (401, 403):
        print("⏭ Skipped — no permission")
        continue

    # Stop if another download error occurs
    response.raise_for_status()

    # Get the expected file size, if provided by the server
    total_size = int(response.headers.get("content-length", 0))

    # Save the file while showing download progress
    with open(output, "wb") as f:
        with tqdm(
            total=total_size,
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
            desc="Downloading",
            leave=True
        ) as progress:

            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
                    progress.update(len(chunk))

    print(f"✓ Saved to: {output.resolve()}")

# Final summary
print("\n✅ Download process complete.")
print(f"📁 Available files are stored in:\n{data_dir.resolve()}")

# %% slideshow={"slide_type": "slide"} tags=["hide-input"] deletable=true editable=true
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

# %% [markdown] editable=true slideshow={"slide_type": ""}
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

# %% [markdown] deletable=true slideshow={"slide_type": ""} editable=true
# ## 4. Load the spatial data
#
# The main spatial dataset is stored as a GeoPackage. We load it with GeoPandas and inspect the available indicators before mapping them.

# %% editable=true tags=["hide-input"] slideshow={"slide_type": "slide"}
# Define the path to the downloaded GeoPackage
gpkg_path = data_dir / "climate_regulation_in_cities.gpkg"

# Load the spatial dataset as a GeoDataFrame
gdf = gpd.read_file(gpkg_path)

# Display basic information about the dataset
print(f"Features: {len(gdf)}")
print(f"CRS: {gdf.crs}")

# Preview the first five rows
gdf.head()

# %% [markdown] editable=true slideshow={"slide_type": ""} deletable=true
# This is the checkpoint where you identify the exact columns for:
#
# >city name, cooling capacity, population benefit

# %% editable=true deletable=true tags=["hide-input"] slideshow={"slide_type": "slide"}
# List all attribute columns available in the spatial dataset
gdf.columns.tolist()

# %% [markdown] editable=true slideshow={"slide_type": ""} deletable=true
# ## 5. Where is climate-regulation capacity high?
#
# Urban green infrastructure provides different levels of cooling capacity across German cities.
#
# Mapping the indicator helps reveal where climate-regulation potential is comparatively high or low.

# %% slideshow={"slide_type": "slide"} editable=true tags=["hide-input"]
# Prepare the data and geographic context for the map

# Select the indicator to visualize and the column containing city names
value_col = "Pop_Benefit_Percent"
name_col = "GEN"

# Reproject the city data to WGS84 for mapping
gdf_wgs = gdf.to_crs("EPSG:4326")

# Load country boundaries from Natural Earth
world = gpd.read_file(
    "https://naturalearth.s3.amazonaws.com/110m_cultural/ne_110m_admin_0_countries.zip"
)

# Select Germany to provide geographic context
germany = world[world["NAME"] == "Germany"]

# Select major cities to label without overcrowding the map
major_cities = {
    "Berlin", "Hamburg", "München", "Dresden",
    "Köln", "Leipzig", "Frankfurt am Main", "Bremen"
}

# Keep only the selected cities for map labels
labels = gdf_wgs[gdf_wgs[name_col].isin(major_cities)]
print ("Map Context Prepared!")

# %% editable=true slideshow={"slide_type": "slide"} tags=["hide-input"]
# Create the map and set the figure size
fig, ax = plt.subplots(figsize=(9, 9))

# Map the percentage of population benefiting from urban climate regulation
gdf_wgs.plot(
    column=value_col,
    cmap="viridis",
    legend=True,
    edgecolor="white",
    linewidth=0.3,
    ax=ax
)

# Add the German national boundary for geographic context
germany.boundary.plot(
    ax=ax,
    color="black",
    linewidth=0.8
)

# Add labels for selected major cities
for _, row in labels.iterrows():

    # Find a suitable point inside each city geometry for the label
    p = row.geometry.representative_point()

    # Add the city name
    txt = ax.text(
        p.x,
        p.y,
        row[name_col],
        fontsize=7,
        ha="center"
    )

    # Add a white outline to make labels easier to read
    txt.set_path_effects([
        pe.withStroke(linewidth=2, foreground="white")
    ])

# Add a descriptive title and remove map axes
ax.set_title("Population Benefiting from Urban Climate Regulation")
ax.set_axis_off()

# Display the finished map
plt.show()

# %% [markdown] slideshow={"slide_type": ""} editable=true deletable=true
# ### What does the map show?
#
# The indicator represents the **share of inhabitants benefiting from the cooling effect of urban green infrastructure**.
#
# The map reveals that this benefit varies between German cities. This shifts the focus from simply asking *where green infrastructure exists* to asking:
#
# > **How effectively does urban green infrastructure provide climate-regulation benefits to people?**

# %% [markdown] editable=true deletable=true slideshow={"slide_type": ""}
# ## 6. From replication to exploration
#
# Reproducing the indicator map is only the starting point.
#
# Because the replication package provides reusable spatial data, we can explore additional questions:
#
# - Which cities show particularly high or low population benefit?
# - How do cities compare with each other?
# - What might these differences mean for urban green planning?

# %% editable=true slideshow={"slide_type": "slide"} tags=["hide-input"]
# Select the 10 cities with the highest population benefit
# and sort them for a clear horizontal bar chart
top = gdf.nlargest(10, value_col).sort_values(value_col)

# Create the figure
fig, ax = plt.subplots(figsize=(8, 5))

# Compare the population benefit across the selected cities
ax.barh(
    top[name_col],
    top[value_col]
)

# Add a descriptive axis label and title
ax.set_xlabel("Population benefiting (%)")
ax.set_title("Cities with High Population Benefit from UGI")

# Adjust spacing so labels are not cut off
plt.tight_layout()

# Display the finished chart
plt.show()

# %% [markdown] slideshow={"slide_type": ""} editable=true deletable=true
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

# %% [markdown] editable=true slideshow={"slide_type": ""} deletable=true
# ## Conclusion
#
# This example moves from:
#
# **open research data → spatial indicator → city comparison → planning question**
#
# Urban green infrastructure is not only about the amount of green space. Its relevance also depends on the **climate-regulation service it provides and the population that benefits from it**.
#
# The ioerDATA replication package makes this evidence accessible for reproduction, exploration, and further research.

# %% [markdown] slideshow={"slide_type": ""} editable=true deletable=true
# ## Acknowledgements
#
# This contribution builds on the broader [**ioerDATA training materials**](https://github.com/ioer-dresden/jupyter-book-ioerdata) developed at IOER.
#
# The author gratefully acknowledges **Cruickshank, Claudia** for feedback and refinement & **Dunkel, Alexander** for technical support and earlier training resources.

# %% editable=true slideshow={"slide_type": ""}
