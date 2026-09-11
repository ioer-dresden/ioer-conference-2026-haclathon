# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.5
#   kernelspec:
#     display_name: worker_env
#     language: python
#     name: worker_env
# ---

# %% [markdown] tags=["remove-cell"] editable=true slideshow={"slide_type": ""}
# **Install dependencies:** In case this notebook is not running [Carto-Lab Docker](https://cartolab.theplink.org/), the cell below aims to install the needed packages for this notebook. If packages are already available, they will be ignored.

# %% slideshow={"slide_type": ""} editable=true tags=["remove-cell"]
import sys, os

# Colab-specific setup
if 'google.colab' in sys.modules:
    if not os.path.exists("ioer-conference-2026-haclathon"):
        # !git clone -q https://github.com/ioer-dresden/ioer-conference-2026-haclathon.git
    # %cd -q ioer-conference-2026-haclathon/notebooks

# Universal install script
pyexec = sys.executable
print(f"Current Kernel {pyexec}")
# !../py/modules/pkginstall.sh "{pyexec}" owslib geopandas geoviews holoviews matplotlib shapely cartopy contextily adjustText myst_nb

# %% [markdown] slideshow={"slide_type": ""} editable=true
# # Data Retrieval: GBIF & LAND

# %% [markdown] editable=true slideshow={"slide_type": ""}
# ```{admonition} Summary
# :class: hint
# In this section, we will retrieve biodiversity data from GBIF/LAND. 
#
# This section covers:
#
# - Understanding the GBIF API, including the GBIF Species API and the GBIF Occurrence API
# - Mapping species data
# - Write advanced API queries
#     - Restrict queries to specific geographic areas (e.g., Saxony).
#     - Handle API limitations and optimize large data retrieval.
#     - Format spatial queries using bounding boxes and WKT polygons.
# ```

# %% [markdown] slideshow={"slide_type": ""} editable=true
# ## GBIF API Reference
#
#
# ```{figure} https://techdocs.gbif.org/en/_images/td-bg-02.png
# :name: gbif-graphic
# :figclass: fig-no-shadow
#
# GBIF API Reference (https://techdocs.gbif.org/en/openapi/).
# ```

# %% [markdown] editable=true slideshow={"slide_type": ""}
# LAND uses the [GBIF Application Programming Interface (API)](https://techdocs.gbif.org/en/openapi/) to provide standardized ways to access biodiversity data. 
#
# Retrieving data from APIs requires a specific syntax, which varies for each service. Here are two key concepts:
#
# - **Endpoint**: APIs commonly provide URLs (endpoints) that return structured data (e.g., in JSON format). The base URL for the GBIF API is [https://api.gbif.org/](https://api.gbif.org/). 
# - **Authentication**: Some APIs require authentication (such as API keys or OAuth tokens), while others - like GBIF- allow limited access without authentication.
#
#
# ```{dropdown} How do I know how to work with GBIF API?
# Good APIs have a documentation that explains how to use the specific API. It provides details on available endpoints, request methods (e.g., GET, POST), required parameters, and response formats (e.g., JSON, XML), often including code examples and testing tools. Good documentation helps developers to interact with the API efficiently.
#
# The [GBIF API Reference documentation](https://techdocs.gbif.org/en/openapi/) is well-structured and divided into several sections. GGBIF uses a RESTful API, which can be accessed through structured URLs. A great feature of this documentation is that it’s built using [Swagger](https://swagger.io/), an interactive API framework. Swagger-based API pages allow users to test API queries directly in the browser, making it easier to understand how they work.
# ```

# %% [markdown] editable=true slideshow={"slide_type": ""}
# ## Using the GBIF Species API

# %% [markdown] editable=true slideshow={"slide_type": ""}
# ### Finding a species' scientific name
#
# Let’s say we only have a species' common name — such as `English Sparrow`, which is also known as `House Sparrow` - and want to find its scientific name. The scientific name is essential for accurate data retrieval, as common names vary across languages and regions.
#
# We can search for the scientific name manually on Google or the [GBIF species search](https://www.gbif.org/species/search?q=english%20sparrow), but a more efficient approach is to use the **GBIF Species API**.

# %% [markdown] slideshow={"slide_type": ""} editable=true
# ```{admonition} Using the GBIF Species API in the browser
# :class: dropdown, hint
#
# The [GBIF Species API section](https://techdocs.gbif.org/en/openapi/v1/species#/Searching%20names/searchNames) allows to try the API directly in a web browser.
#
# 1. Go to <a href="https://techdocs.gbif.org/en/openapi/v1/species#/Searching%20names/searchNames">https://techdocs.gbif.org/en/openapi/v1/species#/Searching%20names/searchNames</a> and use the general species search for "English Sparrow".
# 2. Enter `English Sparrow` in the parameter field labeled `q`, which has the explaination: *"The value for this parameter can be a simple word or a phrase. Wildcards are not supported"* (Hint: The parameter field is located in the middle of the webpage). 
#
# We also specify a dataset to check this taxon. In this case, we use the base [GBIF Backbone Taxonomy](https://www.gbif.org/dataset/d7dddbf4-2cf0-4f39-9b2a-bb099caae36c).
#
# ```

# %% [markdown] editable=true slideshow={"slide_type": ""}
# ```{admonition} Important caveat: The ambiguity of common names in taxonomic mapping
# :class:warning
#
# The next step, where we map the common name "English sparrow" to the scientific name *Passer domesticus* using the GBIF API, is a simplified example for illustrative purposes in this workshop.
#
# **In real-world explorative analytics, this mapping requires careful scrutiny.** Common names can be highly ambiguous and may refer to different species depending on region, language, or local usage.
#
# For instance, the German word "Sperlinge" (sparrows) can encompass multiple species, notably the House Sparrow (*Passer domesticus*) and the Eurasian Tree Sparrow (*Passer montanus*). These two species have distinct habitat preferences, population trends, and ecological roles. A naive mapping without awareness of this distinction could lead to flawed analyses and conclusions.
#
# For a practical example of how to approach taxonomic reconciliation with more rigor, including techniques for fuzzy matching and merging data from sources like iNaturalist, please refer to this excellent resource:
# [Link iNaturalist observations to TRY](https://sojwolf.github.io/iNaturalist_traits/Chapter_3_Link_iNaturalist_observations_to_TRY.html) by Wolf et al. (2022).
# ```

# %% [markdown] slideshow={"slide_type": ""} editable=true
# ### Retrieving GBIF Species API in Python
# We can also query the API directly using Python:

# %% slideshow={"slide_type": ""} editable=true
import requests

# Define search parameters
search_name = "English Sparrow"
dataset_key = "d7dddbf4-2cf0-4f39-9b2a-bb099caae36c"

# Construct API URL
query_url = \
    f'https://api.gbif.org/v1/species/search' \
    f'?q={search_name}&datasetKey={dataset_key}'

# Send request to the API
json_text = None
response = requests.get(url=query_url)

# %% [markdown] editable=true slideshow={"slide_type": ""}
# **Understanding the code**
#
# - `f'{}'`: This is an f-string, [a handy Python convention](https://realpython.com/python-f-strings/) for concatenating strings and variables. Note: Here it would be _wise_ to prefer `urlencode`, as we did in the [Monitor API query in the following section](content:references:ioermonitor). Have a look at the difference and decide which syntax you prefer! In general, `urlencode` is more robust and safer for building and escaping URLs.
# - `requests.get()`: Sends a GET request to retrieve data from the API.
# - The data can be found in `response.text`, assuming the API responds successfully.

# %% [markdown] editable=true slideshow={"slide_type": ""}
# **Parsing JSON data**
#
# The API returns a JSON object containing multiple species matching our search query. We parse it using the `json` module:

# %% slideshow={"slide_type": ""} editable=true
import json

# Load JSON response
json_data = json.loads(response.text)
# Print first 1000 characters
print(json.dumps(json_data, indent=2)[0:1000])

# %% [markdown] slideshow={"slide_type": ""} editable=true
# The answer, `Passer domesticus`, is hidden in the nested JSON response. 
# (content:references:nub-id)=

# %% [markdown] editable=true slideshow={"slide_type": ""}
# **Extracting the scientific name**
#
# To extract only the scientific name, we navigate through the JSON structure. Below, we walk the json path from the `"results"`, which is a list, access the first entry by using `[0]` and the access its key of the name `scientificName`.

# %% slideshow={"slide_type": ""} editable=true
scientific_name = json_data["results"][0]["scientificName"]
print(scientific_name)

# %% [markdown] editable=true slideshow={"slide_type": ""}
# **Getting the taxon ID**
#
# Each species in GBIF has a unique taxon ID. The taxon ID uniquely identifies a species in the GBIF database, ensuring precise queries. This is neccessary for retrieving occurrence data.
# (content:references:passer-id)=

# %% editable=true slideshow={"slide_type": ""}
taxon_id = json_data["results"][0]["taxonID"]
print(taxon_id)

# %% [markdown] slideshow={"slide_type": ""} editable=true
# (content:references:admonition)=
# ```{admonition} Try it with another species
# :class: dropdown, attention
# You can modify the script to search for any species by replacing `English Sparrow` with another common name.
# ```

# %% [markdown] editable=true slideshow={"slide_type": ""}
# ## Using the GBIF Occurrence API

# %% [markdown] editable=true slideshow={"slide_type": ""}
# ### Finding species observations
#
# Now, we want to find species observations of `Passer domesticus` (English Sparrow). 
#
# Species observations can be previewed in the [LAND Occurrence Search](https://land.gbif.de/occurrence/search/) geo viewer. To see results for `Passer domesticus`, use the search function or click [here](https://land.gbif.de/occurrence/search/?taxonKey=5231190&view=MAP). Another option is to use the unique taxon ID `5231190` instead of the scientific name.
#
# Since LAND relies on the GBIF API, we can efficiently access the data programmatically using the GBIF Occurrence API.

# %% [markdown] editable=true slideshow={"slide_type": ""}
# ```{admonition} Using the GBIF Occurrence API in the browser
# :class: dropdown, hint
#
# The [GBIF Occurrence API](https://techdocs.gbif.org/en/openapi/v1/occurrence#/Searching%20occurrences/searchOccurrence) allows users to test queries directly in a web browser.
# ```

# %% [markdown] editable=true slideshow={"slide_type": ""}
#  ```{admonition} Recommended citation
# :class: attention
#
# There are several possibilities for citing the data used. The appropriate citation depends on how the GBIF data was downloaded and the choice of GBIF dataset(s), which determine how we need to cite the authors of these datasets. Please refer to the [citation guidelines](https://www.gbif.org/citation-guidelines) to find the appropriate citation format for your project.
#
# Since we used only a species dataset (the base taxonomy), we used the default citation from the `passer domesticus` species page:
#
# > Passer domesticus (Linnaeus, 1758) in GBIF Secretariat (2023). GBIF Backbone Taxonomy. Checklist dataset https://doi.org/10.15468/39omei accessed via GBIF.org on 2025-03-06.
# ```
#
#
# ### Retrieving GBIF Occurrence API in Python
#
#
# **Load dependencies**
#

# %% editable=true slideshow={"slide_type": ""}
# Standard library imports
import json
import os
import sys
import io
from pathlib import Path
from urllib.parse import urlencode

# Third-party imports
import requests
import geopandas as gp
import pandas as pd
import geoviews as gv
import holoviews as hv
import matplotlib.pyplot as plt
import shapely
from cartopy import crs as ccrs
from shapely.geometry import Point, Polygon
from shapely.wkt import dumps
from IPython.display import display, Markdown
import contextily as cx

# %% [markdown] editable=true slideshow={"slide_type": ""}
# **Load helper tools**
#
# To simplify the workflow, we use a set of helper tools stored in `py/modules/tools.py`. The following code snippet loads these tools to improve reusability.

# %% slideshow={"slide_type": ""} editable=true
module_path = str(Path.cwd().parents[0] / "py")
if module_path not in sys.path:
    sys.path.append(module_path)
from modules import tools

# %% slideshow={"slide_type": ""} editable=true tags=["remove-input"]
tools.display_file(Path.cwd().parents[0] / 'py' / 'modules' / 'tools.py')

# %% [markdown] editable=true slideshow={"slide_type": ""}
# To maintain reproducibility, it's good practice to print the versions of important packages. The following code uses the method `package_report()` from `tools`, which displays currently used package versions as a table.

# %% tags=["remove-input"] slideshow={"slide_type": ""} editable=true
root_packages = [
    'python', 'requests', 'contextily', 'geoviews', 'holoviews',
    'rasterio', 'geopandas', 'cartopy', 'matplotlib', 'shapely',
    'bokeh','pyproj', 'ipython', 'owslib', 'pandas']
tools.package_report(root_packages)

# %% [markdown] slideshow={"slide_type": ""} editable=true
# **Define parameters**
#
# To make Jupyter Notebooks easier to use and share, important parameters affecting processing are defined at the top and written in CAPITAL LETTERS ([a common Python convention](https://peps.python.org/pep-0008/)). 
#
# In this workflow, we define two key parameters:
# - The `SPECIES` we want to study
# - The spatial `FOCUS_STATE` under analysis 
# - The GBIF dataset key, we use the base [GBIF Backbone Taxonomy](https://www.gbif.org/dataset/d7dddbf4-2cf0-4f39-9b2a-bb099caae36c) dataset, found in our query above

# %% slideshow={"slide_type": ""} editable=true
# Common name of the species for which we query occurrence data 
SPECIES = "English Sparrow"
# GBIF Dataset key
GBIF_DATASET_KEY = "d7dddbf4-2cf0-4f39-9b2a-bb099caae36c"
# Region used to clip LAND species observations
FOCUS_STATE = "Sachsen"

# %% [markdown] editable=true slideshow={"slide_type": ""}
# ```{admonition} Select a different state
# :class: dropdown, attention
# You can replace "Sachsen" with another German state (e.g., "Brandenburg") in the parameter definition above. This selection will be used later to retrieve and clip data for the chosen region.
# ```

# %% [markdown] editable=true slideshow={"slide_type": ""}
# ```{admonition} Dynamic Dataset Key
# :class: info
# You can also reference the key dynamically (`GBIF_DATASET_KEY = json_data["results"][0]["datasetKey"]`). In this case, however, we have chosen to be explicit about which dataset we used.
# ```

# %% [markdown] slideshow={"slide_type": ""} editable=true
# ### Query the GBIF Occurrence API
#
# **Species search**:

# %% slideshow={"slide_type": ""} editable=true
# Define parameters
params = {
    "q": SPECIES,
    "datasetKey": GBIF_DATASET_KEY
}

# Construct the URL
base_url = "https://api.gbif.org/v1/species/search"
query_url = f"{base_url}?{urlencode(params)}"

# Make the request
response = requests.get(url=query_url)
json_data = json.loads(response.text)

# Extract nubKey
nub_key = json_data["results"][0]["nubKey"]
nub_key

# %% [markdown] slideshow={"slide_type": ""} editable=true
# **Search occurences:**
#
# The taxon key for *Passer domesticus* (English Sparrow) is referenced above in the API response as `nubKey`. Since GBIF refers to this as `taxonKey`, we rename it for consistency. For more details, see the [GBIF taxonomic keys](https://discourse.gbif.org/t/understanding-gbif-taxonomic-keys-usagekey-taxonkey-specieskey/3045). For the first test query, we set a limit of `10` observations of occurrence.

# %% slideshow={"slide_type": ""} editable=true
# Rename nub_key as taxon_key
# and further query params
taxon_key = nub_key
continent = "europe"
limit = 10

# Construct query as a dictionary
params = {
    "taxonKey": taxon_key,
    "limit": limit,
    "continent": continent
}

# make request
base_url = "https://api.gbif.org/v1/occurrence/search"
query_url = f"{base_url}?{urlencode(params)}"
response = requests.get(url=query_url)

# %% [markdown] editable=true slideshow={"slide_type": ""}
# To verify whether our request was successful, we print the HTML status code:

# %% slideshow={"slide_type": ""} editable=true
print(response.status_code)

# %% [markdown] editable=true slideshow={"slide_type": ""}
# If the output is `200`, it means the request was successful.

# %% [markdown] editable=true slideshow={"slide_type": ""}
# ```{admonition} Common HTML status codes
# :class: dropdown, hint
#
# | HTML Status Code | Message/Meaning       |
# | ---------------- | --------------------- |
# | 200              | OK                    |
# | 400              | Bad request           |
# | 403              | Forbidden             |
# | 429              | Too Many Requests     |
# | 500              | Internal Server Error |
# | 503              | Service Unavailable   |
# | 504              | Gateway Timeout       |
#
# ```

# %% [markdown] editable=true slideshow={"slide_type": ""}
# **Inspecting the API response**
#
# To check the returned data, access the `.text` field of the response and parse it as JSON:

# %% tags=["hide-output"] editable=true slideshow={"slide_type": ""}
json_text = response.text
json_data = json.loads(json_text)

# Print the first 1000 characters for a preview
print(json.dumps(json_data, indent=2)[0:1000])

# %% [markdown] slideshow={"slide_type": ""} editable=true
# The JSON response contains occurrence records, each with various attributes, such as dataset information, taxonomic details, and spatial coordinates.

# %% [markdown] slideshow={"slide_type": ""} editable=true
# **Validating the number of records**
#
# We can also apply a validity check by comparing how many results have been returned. Since we specified a limit of `10` occurrences, we check whether exactly 10 results were returned:

# %% editable=true slideshow={"slide_type": ""}
len(json_data["results"])

# %% [markdown] slideshow={"slide_type": ""} editable=true
# If the output is `10`, our query worked as expected.

# %% [markdown] slideshow={"slide_type": ""} editable=true
# ### Extracting and mapping spatial information
#
# After retrieving occurrence data from the GBIF API, we need to extract geographic coordinates, convert them into a structured format, and visualize them on a map. To display species observations, we first extract spatial coordinates from the JSON response and convert them into a GeoDataFrame for mapping.
#
# Each occurrence record contains geographic coordinates:

# %% editable=true slideshow={"slide_type": ""}
json_data["results"][0]["decimalLatitude"]

# %% slideshow={"slide_type": ""} editable=true
json_data["results"][0]["decimalLongitude"]

# %% [markdown] slideshow={"slide_type": ""} editable=true
# To inspect the first occurrence in detail:

# %% editable=true tags=["hide-output"] slideshow={"slide_type": ""}
json_data["results"][0]

# %% [markdown] editable=true slideshow={"slide_type": ""}
# This will output a JSON object containing attributes such as:
#
# - Taxonomic details (scientificName, taxonKey)
# - Location (decimalLatitude, decimalLongitude, country)
# - Data source (datasetKey, publishingOrgKey)
# - Time of observation (eventDate, year, month, day)

# %% [markdown] editable=true slideshow={"slide_type": ""}
# **Extracting coordinates**
#
# Each occurrence record contains longitude (`decimalLongitude`) and latitude (`decimalLatitude`) values. 
# We use [list comprehension](https://docs.python.org/3.8/tutorial/datastructures.html#list-comprehensions) to extract them:

# %% slideshow={"slide_type": ""} editable=true
coordinates = [
    (obs['decimalLongitude'], obs['decimalLatitude'])
    for obs in json_data["results"]]
coordinates

# %% [markdown] editable=true slideshow={"slide_type": ""}
# ```{admonition} Multiple observations at the same coordinate
# :class: dropdown, hint
# Some locations may have multiple records, as scientists or volunteers can report several observations from the same location.
# ```

# %% [markdown] slideshow={"slide_type": ""} editable=true
# **Converting coordinates to a GeoDataFrame** 
#
# To visualize these points on a map, we need to t convert the list of coordinates into `shapely.Point` objects and store them in a GeoDataFrame using the `geopandas` package. We also assign a global coordinate reference system  (CRS). 
#
# - `Point(x, y)`: Creates a point object from longitude (`x`) and latitude (`y`).
# - `gp.GeoDataFrame(geometry=geometry)`: Converts the list of points into a GeoDataFrame.
# - `set_crs(epsg=4326)`: Assigns WGS84 (EPSG:4326), the standard global coordinate system for latitude/longitude data.

# %% slideshow={"slide_type": ""} editable=true
# Convert to shapely.Point objects
geometry = [Point(x, y) for x, y in coordinates]

# Create GeoDataFrame and set CRS to WGS84 (EPSG:4326)
gdf = gp.GeoDataFrame(geometry=geometry)
gdf.set_crs(epsg=4326, inplace=True)

# Preview results
gdf.head()

# %% [markdown] slideshow={"slide_type": ""} editable=true
# **Reprojecting to Web Mercator Projection**
#
# Web Mercator Projection ([EPSG:3857](https://epsg.io/3857)) is the standard coordinate system for web mapping services such as Google Maps and OpenStreetMap. Before visualization, we transform our data into this projection.

# %% editable=true slideshow={"slide_type": ""}
CRS_PROJ = "epsg:3857"
gdf.to_crs(CRS_PROJ, inplace=True)

# %% [markdown] editable=true slideshow={"slide_type": ""}
# **Visualizing observations on a map**
#
# We use the [contextily](https://contextily.readthedocs.io/en/latest/) package to create a static map. This package helps add background map tiles (e.g., from CartoDB) behind our data points.

# %% editable=true slideshow={"slide_type": ""}
# Create a plot
ax = gdf.plot(
    figsize=(10, 15),
    alpha=0.8,
    linewidth=4,
    edgecolor="white",
    facecolor="red",
    markersize=300)

# Add basemap
cx.add_basemap(
    ax, alpha=0.5,
    source=cx.providers.OpenStreetMap.Mapnik)

# Turn of axes display
ax.set_axis_off()

# %% [markdown] editable=true slideshow={"slide_type": ""}
# ### Extracting and mapping spatial information for the focus regions (Saxony)
#
# In this example, we map species occurrences in our focus region, Saxony.
#
# To achieve this, we refine our test query into a structured method that loops through the GBIF API and saves the results as a CSV for further processing. However, we must consider the [GBIF Occurrence API documentation](https://techdocs.gbif.org/en/openapi/v1/occurrence#/Searching%20occurrences) limitations:
#
# - Each query can return a maximum of `300` results.
# - The total number of results for unauthenticated queries is `100,000`. For larger datasets, the GBIF asynchronous download service is recommended.
#
# Additionally, we apply the following constraints: 
# - The query is restricted to Saxony using a geospatial bounding box..
# - Results are stored as a CSV, a widely used, accessible, and portable format. However, other formats, such as [Python DataFrame pickles](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_pickle.html), can also be used.

# %% [markdown] slideshow={"slide_type": ""} editable=true
# **Defining the spatial parameter**
#
# Before running the query, we must define the spatial parameter to restrict results to Saxony. The [GBIF Occurrence API](https://techdocs.gbif.org/en/openapi/v1/occurrence#/Searching%20occurrences/searchOccurrence) provides a `geometry` parameter that accepts a Well-Known Text (WKT) geometry format. To create a bounding box, we use a pre-defined method stored in `py/modules/tools.py`, which downloads and extracts the latest [VG2500 administrative boundaries ](https://gdz.bkg.bund.de/index.php/default/verwaltungsgebiete-1-2-500-000-stand-31-12-vg2500-12-31.html) from the German Federal Agency for Cartography and Geodesy ([BKG](https://daten.gdz.bkg.bund.de/produkte/vg/vg2500/aktuell/)).

# %% [markdown] editable=true slideshow={"slide_type": ""}
# **Loading the geometry**

# %% slideshow={"slide_type": ""} editable=true
WORK_DIR = Path.cwd().parents[0] / "tmp"    # Define working directory
WORK_DIR.mkdir(exist_ok=True)               # Create directory if it doesn't exist

# Load world countries' geometry and extract Saxony
de_shapes = tools.get_shapes(
    "de", shape_dir=WORK_DIR / "shapes")   
de_shapes.to_crs(CRS_PROJ, inplace=True)    
sachsen = de_shapes[                        
    de_shapes.index == FOCUS_STATE]         # Saxony

# %% [markdown] slideshow={"slide_type": ""} editable=true
# **Visualizing the geometry**

# %% slideshow={"slide_type": ""} editable=true
plt_kwags = {
    "color": 'none',
    "edgecolor": 'black',
    "linewidth": 0.2,
    "figsize": (2, 4),
}
ax = de_shapes.plot(**plt_kwags)
plt_kwags["color"] = "red"
ax = sachsen.plot(ax=ax, **plt_kwags)
ax.set_axis_off()

# %% [markdown] editable=true slideshow={"slide_type": ""}
# **Projecting and saving the shapefile**
#
# The shapefile is projected to `EPSG:3035` and saved for later use:

# %% slideshow={"slide_type": ""} editable=true
base_path = Path.cwd().parents[0] # one level up from notebooks/ folder
OUTPUT = base_path / "out"
OUTPUT.mkdir(exist_ok=True)
sachsen_proj = sachsen.to_crs("epsg:3035")
sachsen_proj.to_file(OUTPUT / 'saxony.gpkg')

# %% [markdown] editable=true slideshow={"slide_type": ""}
# **Extracting the bounding box**
#
# To define the bounding box for API queries:
# 1. Convert the shape to WGS 1984 (`epsg:4326`), as the API requires coordinates in Decimal Degrees.
# 2. Use the [`.bounds` property of the GeoDataFrame](https://geopandas.org/en/stable/docs/reference/api/geopandas.GeoDataFrame.html) to get the bounding box.
# 3. Retrieve coordinates using [`.values`](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.values.html).
# 4. Apply [`.squeeze()` function](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.squeeze.html#pandas.DataFrame.squeeze) to simplify access to the four bounding box corners. 
#    
# (content:references:glue-example)=

# %% editable=true slideshow={"slide_type": ""}
bbox_sachsen = sachsen.to_crs("epsg:4326").bounds.values.squeeze()
minx, miny = bbox_sachsen[0], bbox_sachsen[1]
maxx, maxy = bbox_sachsen[2], bbox_sachsen[3]

# %% editable=true tags=["remove-cell"] slideshow={"slide_type": ""}
from myst_nb import glue
bounds_before = sachsen.to_crs("epsg:4326").bounds.values
glue("bounds_before", Markdown(
    f"""
    {bounds_before}
    """))
bounds_after = bbox_sachsen
glue("bounds_after", Markdown(
    f"""
     {bounds_after}
    """))

# %% [markdown] slideshow={"slide_type": ""} editable=true
# ````{admonition} Inspecting the bounding box
# :class: dropdown, tip
# Using Jupyter, we can inspect transformations:
#
# This are `sachsen.bounds.values` before using `.squeeze()`:
#
# ```{glue:md} bounds_before
# :format: myst
# ```
#
# .. and this is the result after using `squeeze()`:
#
# ```{glue:md} bounds_after
# :format: myst
# ```
#
# ````

# %% [markdown] slideshow={"slide_type": ""} editable=true
# **Converting bounding box to WKT**
#
# The bounding box is converted into a Well-Known Text (WKT) polygon with four corners. According to the GBIF API documentation, the polygon must be ordered in a specific way:
#
# > Polygons must have anticlockwise ordering of points. (A clockwise polygon represents the opposite area: the Earth's surface with a 'hole' in it. Such queries are not supported.)

# %% slideshow={"slide_type": ""} editable=true
polygon = Polygon([
    (minx, miny),  # Bottom-left
    (minx, maxy),  # Top-left
    (maxx, maxy),  # Top-right
    (maxx, miny),  # Bottom-right
    (minx, miny)   # Close the polygon
])

# Convert the polygon to WKT format
polygon_ordered = shapely.geometry.polygon.orient(Polygon(polygon), 1.0)
polygon_wkt = dumps(polygon_ordered)

print("Polygon WKT:", polygon_wkt)

# %% [markdown] slideshow={"slide_type": ""} editable=true
# ````{admonition} Simpler ways to generate Well-Known Text (WKT)
# :class: dropdown, tip
# There are simpler ways to create the Well-Known Text (WKT)
# - [GeoDataFrame.to_wkt()](https://geopandas.org/en/stable/docs/reference/api/geopandas.GeoDataFrame.to_wkt.html).
# - Look up the bounding box for Saxony using tools like [bboxfinder.com](http://bboxfinder.com/#50.324633,12.101440,51.237875,15.295715).
# - We could also have used the original shape of Saxony instead of its bounding box. However, complex polygons increase query time, which is why we did not use the original border of Saxony.
#
# The motivation for calculating the bounding box within the Jupyter Notebook using BKG data is to fully _parametrize_ data retrieval. This makes the Jupyter Notebook easily reusable for other regions. To query a different state, simply set `FOCUS_STATE` to the desired state, and all subsequent steps will adjust automatically.
# ````

# %% [markdown] slideshow={"slide_type": ""} editable=true
# ### Querying the GBIF Occurrence API for Saxony
#
# The final step is to write a method to request data in _chunks_ from the API. We start by defining our parameters in a dictionary, including the calculated bounding box.

# %% slideshow={"slide_type": ""} editable=true
query_url = "https://api.gbif.org/v1/occurrence/search"
limit = 300
params = {
    "taxon_key": taxon_key,
    "continent": continent,
    "limit": limit,
    "geometry": polygon_wkt,
    "offset": 0,
    }

# %% [markdown] editable=true slideshow={"slide_type": ""}
# Below, we use `params` parameter of `requests.get()` (instead of `urlencode`). (There are many ways to get to Rome! The choice is yours.)

# %% editable=true slideshow={"slide_type": ""}
response = requests.get(
        url=query_url, params=params)
print(response.url)
response.status_code

# %% [markdown] editable=true slideshow={"slide_type": ""}
# The generated query can be tested in a browser.

# %% slideshow={"slide_type": ""} tags=["remove-cell"] editable=true
map_url = 'https://www.gbif.org/occurrence/map'
r = requests.Request('GET', map_url, params=params)
pr = r.prepare()

# %% editable=true slideshow={"slide_type": ""}
display(Markdown(f"Test the above API query in your browser by clicking on it. You can also preview [the query on a map]({pr.url})."))


# %% [markdown] editable=true slideshow={"slide_type": ""}
# **Defining a query function**

# %% editable=true slideshow={"slide_type": ""}
def query_gbif_occurrences(query_url, params):
    """Perform an API call and attach results to dataframe
    
    Steps:
    1. Request occurrences
    2. Raise an error for bad responses
    3. Parse the JSON response
    4. Convert API response to a DataFrame
    5. Show progress
    """
    response = requests.get(
        url=query_url, params=params)               # 1.
    response.raise_for_status()                     # 2.
    data = response.json()                          # 3.
    df = pd.DataFrame.from_dict(data['results'])    # 4.
    clear_output(wait=True)                         # 5.
    display(HTML(
            f"Queried {params.get('offset')} occurrences, "
            f"<a href='{response.url}'>last query-url</a>."))
    return df, data['endOfRecords']


# %% [markdown] editable=true slideshow={"slide_type": ""}
# **Checking for existing cache and avoiding API abuse**

# %% [markdown] editable=true slideshow={"slide_type": ""}
# Public APIs must be used with care, as overuse can lead to poor performance for other users. The GBIF API allows 100,000 queries without authentication, which is very generous. Imagine a workshop class where all the students use the same shared code to make 100,000 API calls at the same time. This would result in 1 million API calls in a few minutes.
#
# To avoid this, we can
# 1. Check for a cache file. Only if it does not exist will the API be called again. This prevents a single user having to query the API multiple times because the cache file would exist after the first query.
# 2. Allow retrieval of a remote cache file for classrooms/workshops (etc). Those who just want to reproduce the results can use the remote cache, which is also faster than querying the original API. Those wishing to use notebooks as parameterised processing templates (e.g. to query GBIF data for another species) can do so by manually disabling the remote cache or overriding the behaviour in some other way.

# %% [markdown] editable=true slideshow={"slide_type": ""}
# First, if `taxon_key` is `5231190` (English Sparrow), we will fetch a remote cache. The logic here is: If the user has not changed the species to be queried, we will use the existing API cache that was queried once. This will allow anyone to reproduce our final results.

# %% slideshow={"slide_type": ""} editable=true
if taxon_key == 5231190:
    if not Path(OUTPUT / "occurrences_query.zip").exists():
        tools.get_zip_extract(
            output_path=OUTPUT,
            uri_filename="https://datashare.tu-dresden.de/s/AZ98faXX5iN4M5K/download")

# %% [markdown] slideshow={"slide_type": ""} editable=true
# Next, we check for a cache file:
# - this either loads the remote cache
# - or any local cache produced by a previous run by the user

# %% editable=true slideshow={"slide_type": ""}
cache_file = OUTPUT / "occurrences_query.csv"
if cache_file.exists():
    # do not query again if already queried;
    # load cache instead; 
    # infer data types by loading all data at once (low_memory=False)
    df = pd.read_csv(cache_file, low_memory=False)
    print("Loaded file from cache")

# %% [markdown] editable=true slideshow={"slide_type": ""}
# **Running the query**
#
# Start the query. Since the API has an upper limit of 100,000 occurrences, we iterate in chunks.

# %% slideshow={"slide_type": ""} editable=true
# %%time
from IPython.display import clear_output, HTML

if 'df' in locals() and not df.empty:
    pass
else:
    df = pd.DataFrame()
    status = 200

    OUTPUT = base_path / "out"

    for ix in range(int(100000 / limit)):
        params["offset"] = ix * limit
        new_df, end_of_records = query_gbif_occurrences(
            query_url, params)
        df = pd.concat(
            [df, new_df], axis=0, ignore_index=True, sort=True)
        if end_of_records:
            # exit when all available occurrences have been retrieved
            break

# %% [markdown] slideshow={"slide_type": ""} editable=true
# **Caching results**
#
# Before storing, we rename columns to `lat` (Latitude) and `lng` (Longitude).

# %% [markdown] editable=true slideshow={"slide_type": ""}
# :::{tip} Cache results as CSV file. 
# This is generally a good idea. As described above, it helps both to conserve limited API resources and to develop code faster (since you won't need to repeatedly query results over and over again).
# :::

# %% editable=true slideshow={"slide_type": ""}
df.rename(
    columns={"decimalLatitude": "lat", "decimalLongitude": "lng"},
    inplace=True)
if not cache_file.exists():
    df.to_csv(cache_file)

# %% editable=true slideshow={"slide_type": ""}
df.head()

# %% [markdown] editable=true slideshow={"slide_type": ""}
# ### Mapping the data
#
# To create a preview map, we keep only latitude (`lat`) and longitude (`lng`).

# %% slideshow={"slide_type": ""} editable=true
df = df.filter(items=['lat', 'lng'])

# %% [markdown] editable=true slideshow={"slide_type": ""}
# **Displaying the data**
#
# Using [Geoviews](https://github.com/holoviz/geoviews), we visualize occurrences on a map with Esri satellite imagery (`EsriImagery`) as a background.
#
# The first step is to load the `bokeh`-extension, which is the interactive visualization library that is used by Geoviews to create the map.
#
# Next, we create two layers, a point layer `gv.Points()`, and a polygon layer `gv.Polygons()`).
#
# In the last step, we combine these layers, together with a tile background, into an `Overlay`. Think of an Overlay as a dataframe in ESRI. The resulting `gv_layers` includes all data, interaction and style information.

# %% slideshow={"slide_type": ""} editable=true
hv.notebook_extension('bokeh')

occurrence_layer = gv.Points(df, kdims=['lng', 'lat'])

sachsen_proj.to_crs(ccrs.GOOGLE_MERCATOR, inplace=True)

sachsen_layer = gv.Polygons(
    sachsen_proj, crs=ccrs.GOOGLE_MERCATOR)

gv_layers = hv.Overlay(
    gv.tile_sources.EsriImagery * \
    sachsen_layer.opts(
        line_color='white',
        line_width=1.0,
        fill_color=None) * \
    occurrence_layer.opts(
        size=5,
        line_color='black',
        line_width=0.1,
        fill_alpha=0.8,
        fill_color='white'))


# %% [markdown] editable=true slideshow={"slide_type": ""}
# **Final adjustments**
#
# Before we visualize the Geoviews layer we created above, we apply some further tweaks below:  
# - Activate zooming with  the scroll wheel as a default.
# - Zoom to Saxony and the data boundaries.
# - Ensure the correct projection is used (Web Mercator).
# - Add a title to the map.

# %% slideshow={"slide_type": ""} editable=true
def set_active_tool(plot, element):
    """Enable wheel_zoom in bokeh plot by default"""
    plot.state.toolbar.active_scroll = plot.state.tools[0]

bbox_sachsen = sachsen_proj.bounds.values.squeeze()
minx, miny = bbox_sachsen[0], bbox_sachsen[1]
maxx, maxy = bbox_sachsen[2], bbox_sachsen[3]

from datetime import datetime
today = datetime.today().strftime('%Y-%m-%d')

title = f"Species observations of {scientific_name} " \
        f"({SPECIES}) in {FOCUS_STATE}. \n" \
        f"Number of oberservations: {len(df):,} ({today})"

layer_options = {
    # "projection": "epsg:3857",
    "projection": ccrs.GOOGLE_MERCATOR,
    "title": title,
    "responsive": True,        # responsive resize
    "xlim": (minx, maxx),      # limit map boundary to Saxony
    "ylim": (miny, maxy),
    "data_aspect": 1.0,        # maintain fixed aspect ratio
    "hooks": [set_active_tool] # enable zoom on scroll wheel by default
}

# %% editable=true slideshow={"slide_type": ""}
gv_layers.opts(**layer_options)

# %% [markdown] slideshow={"slide_type": ""} editable=true
# Also, it is possible to save this interactive map as a separate standalone HTML (e.g. for archiving purposes or sharing with others). You can view the final map from this step <a href="/geoviews_map.html" title="View the interactive map">here</a>.

# %% slideshow={"slide_type": ""} editable=true
layer_options["data_aspect"] = None
hv.save(
    gv_layers.opts(**layer_options),
    OUTPUT / f'geoviews_map.html', backend='bokeh')

# %% editable=true slideshow={"slide_type": ""} tags=["remove-input"]
import sys
from pathlib import Path

module_path = str(Path.cwd().parents[0] / "py")
if module_path not in sys.path:
    sys.path.append(module_path)
from modules import tools

root_packages = [
    'python', 'geopandas', 'pandas', 'matplotlib', 'owslib', 'requests', 'geoviews', 'holoviews', 'shapely', 'cartopy', 'contextily']
tools.package_report(root_packages)

# %% editable=true slideshow={"slide_type": ""}
