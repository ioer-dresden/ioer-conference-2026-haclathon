---
jupyter:
  jupytext:
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.3'
      jupytext_version: 1.19.5
  kernelspec:
    display_name: worker_env
    language: python
    name: worker_env
---

<!-- #region slideshow={"slide_type": ""} editable=true tags=["remove-cell"] -->
**Install dependencies:** In case this notebook is not running [Carto-Lab Docker](https://cartolab.theplink.org/), the cell below aims to install the needed packages for this notebook. If packages are already available, they will be ignored.
<!-- #endregion -->

```python slideshow={"slide_type": ""} editable=true tags=["remove-cell"]
import sys, os

# Colab-specific setup
if 'google.colab' in sys.modules:
    if not os.path.exists("ioer-conference-2026-haclathon"):
        !git clone -q https://github.com/ioer-dresden/ioer-conference-2026-haclathon.git
    %cd -q ioer-conference-2026-haclathon/notebooks

# Universal install script
pyexec = sys.executable
print(f"Current Kernel {pyexec}")
!../py/modules/pkginstall.sh "{pyexec}" owslib geopandas matplotlib lxml rasterio cartopy dotenv adjustText geoviews
```

<!-- #region slideshow={"slide_type": ""} editable=true -->
# Data Retrieval: IOER Monitor

<!-- #endregion -->

```{admonition} Summary
:class: hint

In this section, we will retrieve and visualize spatial data from the IOER Monitor.

```


In this section, we retrieve spatial data from the IOER Monitor using the Web Coverage Service (WCS). Specifically, we will access the indicator "Percentage of built-up settlement area and transport space to reference area" (Anteil baulich geprägter Siedlungs- und Verkehrsfläche an Gebietsfläche). This indicator describes the proportion of built-up settlement and transport space in an administrative territory and correlates with soil sealing and open space availability (IOER Monitor 2025).

The IOER Monitor data can be previewed in the [geo viewer](https://monitor.ioer.de/?raeumliche_gliederung=raster&zoom=7&lat=51.32717923968566&lng=10.458984375000002&time=2023&ind=S12RG&language=en). The necessary WFS and WCS URLs, along with the unique indicator code (`S12RG`), can be found under <kbd>Export</kbd> → <kbd>OGC Services</kbd>. 

<!-- #region slideshow={"slide_type": ""} editable=true -->


```{figure} ../resources/094_Verdichtung.jpg
:name: 094_Verdichtung
:figclass: fig-no-shadow

Densification of the block development in Berlin Friedrichshain. Photo: Jürgen Hohmuth, aus der Reihe "Gestalt des Raumes" (Buch und Ausstellung), © IOER-Media.
```


<!-- #endregion -->

(content:references:monitorkey)=
## IOER Monitor of Settlement and Open Space Development
The IOER Monitor of Settlement and Open Space Development (short [IOER Monitor](https://monitor.ioer.de/)) is a research data infrastructure provided by the Leibniz Institute of Ecological Urban and Regional Development (IOER). It offers insights into land use structure, development, and landscape quality in Germany. Indicators and data can be explored and visualized in an [interactive geo viewer](https://monitor.ioer.de).
All IOER Monitor data is available through **Web Feature Service (WFS)** and **Web Coverage Service (WCS)**, allowing users to retrieve spatial data in standardized formats.

There are two ways to access and download data:

- **Via web browser**: Login, search and download individual data files directly from the IOER Monitor's download services.
- **Via code**: Use the Monitor API to access data programmatically.

In both cases, [registration](https://monitor.ioer.de/monitor_api/) is required.


```{admonition} Using the Monitor API
:class: warning

If you want to use the Monitor API, you need to register:

1. Register at [monitor.ioer.de/monitor_api/signup](https://monitor.ioer.de/monitor_api/signup).
2. Generate a personal API key in your account settings.
3. Store your personal API key in a file called `.env` as `API_KEY=xyz`
```


```{figure} https://www.ioer-monitor.de/fileadmin/user_upload/monitor/img/Ergebnisse/siedlungsdichte.png
:name: monitor-graphic

Wie dicht leben wir? [IOER Monitor data](https://www.ioer-monitor.de/ergebnisse/analyseergebnisse/wie-dicht-leben-wir/).
```


## Accessing IOER Monitor Data

The IOER Monitor allows querying:

- Raster data via [Web Coverage Service (WCS)](https://de.wikipedia.org/wiki/Web_Coverage_Service)
- Vector data via [Web Feature Service (WFS)](https://en.wikipedia.org/wiki/Web_Feature_Service)

To use the API programmatically, you need a personal API key. If you don’t have one yet, refer to the previous section for instructions.

<!-- #region editable=true slideshow={"slide_type": ""} -->
## Retrieving IOER Monitor API in Python 

**Load dependencies**

Before running the workflow, ensure the necessary libraries are installed and imported:
<!-- #endregion -->

```python slideshow={"slide_type": ""} editable=true tags=["hide-input"]
# Standard library imports
import json
import os
import sys
import io
from pathlib import Path
from urllib.parse import urlencode

# Third-party imports
import matplotlib.pyplot as plt
import pandas as pd
import geopandas as gp
from IPython.display import display, Markdown
import rasterio
from rasterio.plot import show
from rasterio.mask import mask
from owslib.wcs import WebCoverageService
from lxml import etree
```

Load additional tools module

```python editable=true slideshow={"slide_type": ""} tags=["hide-input"]
base_path = Path.cwd().parent
module_path = str(base_path / "py")
if module_path not in sys.path:
    sys.path.append(module_path)
from modules import tools
```

<!-- #region slideshow={"slide_type": ""} editable=true -->
**Define parameters**

To access the IOER Monitor data, we define two key parameters:

- `MONITOR_WCS_BASE`: IOER Monitor API base endpoint
- `IOERMONITOR_WCS_ID`: unique indicator code
<!-- #endregion -->

```python slideshow={"slide_type": ""} editable=true
MONITOR_WCS_BASE = "https://monitor.ioer.de/monitor_api/user" # API base endpoint
IOERMONITOR_WCS_ID = "S12RG" # Unique indicator code
```

**Define the base path to store output files in this notebook**

```python editable=true slideshow={"slide_type": ""}
base_path = Path.cwd().parents[0]
OUTPUT = base_path / "out"
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
**Secure API Key**
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
To store your API key securely, use a dotenv (`.env`) file. This helps keep sensitive data safe and prevents accidental exposure: 

```{admonition} Alternatively, use <code>getpass()</code>
:class: hint
If you don't want to use an `.env` file, leave this step and you will be asked to directly enter the password in Jupyter below, by using `getpass.getpass()`.
```

1. Create a file named `.env` in the project root. Typically, `.env` files are added to `.gitignore` files to prevent them from being tracked.
2. Add the following line:

   ```
   IOERMONITOR_API_KEY=REPLACE-WITH-YOUR-PASSWORD # replace with your password
   ```
<!-- #endregion -->

<!-- #region slideshow={"slide_type": ""} editable=true -->
3. Load the key in your script:
<!-- #endregion -->

```python slideshow={"slide_type": ""} editable=true
from dotenv import load_dotenv
load_dotenv(
    Path.cwd().parents[0] / '.env', override=True)

MONITOR_API_KEY = os.getenv('IOERMONITOR_API_KEY')
```

```{admonition} You can continue without IOER Monitor Key
:class: hint
See [Notebook 201](content:references:monitorkey) to register your IOER Monitor key. You can continue without an IOER Monitor API key, in which case you will only be able to view cached results below (e.g. for reproduction). If you want to retrieve new data (another region, etc.), register for a trial IOER Monitor key.
```

```python slideshow={"slide_type": ""} editable=true
if MONITOR_API_KEY is None:
    import getpass
    MONITOR_API_KEY = getpass.getpass("Please enter your IOER Monitor API key")
    if not MONITOR_API_KEY:
        # user response empty
        print("Monitor API key not provided. Continuing with cached results..")
```

<!-- #region slideshow={"slide_type": ""} editable=true -->
## Querying WCS Data 

**Configure API request**
<!-- #endregion -->

<!-- #region slideshow={"slide_type": ""} editable=true -->
(content:references:ioermonitor)=
In order to connect to WCS services from Python, we use `owslib` (see documentation of [owslib.wcs](https://owslib.readthedocs.io/en/latest/usage.html#wcs)).
<!-- #endregion -->

```python editable=true slideshow={"slide_type": ""}
from urllib.parse import urlencode

params = {
    "id": IOERMONITOR_WCS_ID,
    "key": MONITOR_API_KEY,
    "service": "wcs",
}
wcs_url = f"{MONITOR_WCS_BASE}?{urlencode(params)}"

wcs = WebCoverageService(wcs_url, version="1.0.0") # WCS version `1.0.0`
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
:::{tip}

When making requests to web APIs, you often need to pass parameters in a URL. However, some characters (such as spaces, special symbols, or non-ASCII characters) can cause issues if they are not properly encoded. `urlencode` prevents character encoding issues and improves readability. For more information, see [urllib.parse module documentation](https://docs.python.org/3/library/urllib.parse.html) 
:::
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
**Explore Available Data**

Let's first run some checks on the returned `wcs` object and see what data we can access. The data is available for different time intervals and resolutions, as you can see below.
<!-- #endregion -->

```python editable=true slideshow={"slide_type": ""} tags=["hide-output"]
pd.DataFrame(wcs.contents.keys())
```

<!-- #region slideshow={"slide_type": ""} editable=true -->
Select the dataset for `2023` at `200`m raster resolution, which leads us to the key `S12RG_2023_200m`.
<!-- #endregion -->

```python slideshow={"slide_type": ""} editable=true
LAYER = 'S12RG_2023_200m'
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
Check the supported output formats for this layer.
<!-- #endregion -->

```python editable=true slideshow={"slide_type": ""}
if MONITOR_API_KEY: print(wcs.contents[LAYER].supportedFormats)
```

<!-- #region slideshow={"slide_type": ""} editable=true -->
We can also query all additional available metadata for the layer (see dropdown below).
<!-- #endregion -->

```python tags=["hide-input", "hide-output"] slideshow={"slide_type": ""} editable=true
layer_metadata = wcs.contents[LAYER]

print("Available Attributes for the Layer:")
if not MONITOR_API_KEY:
    print("Skipping because API key is not available.")
else:
    for attr in dir(layer_metadata):
        if not attr.startswith("_"):
            try:
                value = getattr(layer_metadata, attr)
                if attr == "descCov":
                    xml_content = etree.tostring(
                        value, pretty_print=True, encoding="unicode")
                    print(f"{attr} (XML Content):\n{xml_content}")
                else:
                    print(f"{attr}: {value}")
            except Exception as e:
                print(f"{attr}: Error accessing attribute - {e}")
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
Check the maximum available boundary for this layer. We can see that the limits are available in two different projections. In the following we will use the projected version of the boundary and not the WGS1984 version.
<!-- #endregion -->

```python slideshow={"slide_type": ""} tags=["hide-output"] editable=true
if MONITOR_API_KEY: print(wcs.contents[LAYER].boundingboxes)
```

<!-- #region slideshow={"slide_type": ""} editable=true -->
Check the coordinate reference system (CRS).
<!-- #endregion -->

```python editable=true slideshow={"slide_type": ""}
if MONITOR_API_KEY: print(wcs.contents[LAYER].supportedCRS) # ['EPSG:3035']
```

<!-- #region slideshow={"slide_type": ""} editable=true -->
**Retrieve and visualize data**

Set up query parameters and request the dataset.
<!-- #endregion -->

```python editable=true slideshow={"slide_type": ""}
BBOX = None
if MONITOR_API_KEY: BBOX = wcs.contents[LAYER].boundingboxes[1]["bbox"]
CRS = "EPSG:3035"
```

```python editable=true slideshow={"slide_type": ""}
monitor_param = {
    "identifier": LAYER,
    "bbox": BBOX,
    "resx": 500,
    "resy": 500,
    "crs": CRS,
    "format": "GTiff"
} 
if MONITOR_API_KEY: response = wcs.getCoverage(**monitor_param)
```

```python slideshow={"slide_type": ""} editable=true
monitor_param
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
Load and display the GeoTiff with [rasterio](https://rasterio.readthedocs.io/en/stable/). If a cache exist, we prefer to load it directly (instead of querying the API again). If it does not exist, write it.
<!-- #endregion -->

```python slideshow={"slide_type": ""} editable=true
cache_file = OUTPUT / f"{LAYER}_DE.tiff"

if not cache_file.exists():
    if not MONITOR_API_KEY:
        if not Path(OUTPUT / "S12RG_2023_200m_DE.zip").exists():
            tools.get_zip_extract(
                output_path=OUTPUT,
                uri_filename="https://datashare.tu-dresden.de/s/HjGzHT7c3j36tai/download")
    else:
        # write to cache
        with open(cache_file, "wb") as f:
            f.write(response.read())
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
Visualize response (or cache).
<!-- #endregion -->

```python editable=true slideshow={"slide_type": ""}
with rasterio.open(cache_file) as src:
    fig, ax = plt.subplots(figsize=(8, 8))
    show(src, ax=ax)
    ax.axis('off')
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
## Filtering data for Saxony
<!-- #endregion -->

<!-- #region slideshow={"slide_type": ""} editable=true -->
However, we want to restrict the raster data to the following boundaries of the state of Saxony, similar to the way we restricted the responses for the GBIF Occurrence API.

1. Reproject the Saxony boundary to `EPSG:3035`.
2. Get boundaries (see section Data Retrieval: GBIF & LAND)
3. Update the monitor parameters (a Python dictionary) with the new `bbox`.
4. Get the grid with the new `bbox` boundary
<!-- #endregion -->

<!-- #region slideshow={"slide_type": ""} editable=true -->
**Restricting to Saxony boundaries**

Load Saxony boundaries and reproject to match WCS layer.
<!-- #endregion -->

```python slideshow={"slide_type": ""} editable=true
sachsen_proj = gp.read_file(OUTPUT / 'saxony.gpkg')
BBOX = sachsen_proj.bounds.values.squeeze()
monitor_param["bbox"] = list(map(str, BBOX))
```

<!-- #region slideshow={"slide_type": ""} editable=true -->
Retrieve and visualize clipped data using `rasterio.show()`.

1. Check and retrieve cache
<!-- #endregion -->

```python slideshow={"slide_type": ""} editable=true
cache_file = OUTPUT / f"{LAYER}_Saxony.tiff"

if not cache_file.exists():
    if not MONITOR_API_KEY:
        if not Path(OUTPUT / "S12RG_2023_200m_Saxony.zip").exists():
            tools.get_zip_extract(
                output_path=OUTPUT,
                uri_filename="https://datashare.tu-dresden.de/s/Bm74ix6BDQtDzmP/download")
    else:
        # retrieve and write to cache
        response = wcs.getCoverage(**monitor_param)
        with open(cache_file, "wb") as f:
            f.write(response.read())
```

<!-- #region slideshow={"slide_type": ""} editable=true -->
2. Visualize
<!-- #endregion -->

```python editable=true slideshow={"slide_type": ""}
with rasterio.open(cache_file) as src:
    fig, ax = plt.subplots(figsize=(8, 8))
    show(src, ax=ax)
    sachsen_proj.boundary.plot(
        ax=ax, color='white', linewidth=2)
    ax.axis('off')
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
**Clipping the raster**

Use `rasterio.mask` to clip the raster with the boundaries of `sachsen_proj`. In addition, the `cmap` (a [Matplotlib Colormap](https://matplotlib.org/stable/users/explain/colors/colormaps.html)) is changed to `Reds`.
<!-- #endregion -->

```python editable=true slideshow={"slide_type": ""}
with rasterio.open(cache_file) as src:
    out_image, out_transform = mask(
        src, sachsen_proj.geometry, crop=True, filled=False)
    out_meta = src.meta.copy()
    fig, ax = plt.subplots(
        figsize=(8, 8))
    show(
        out_image, 
        transform=out_transform, 
        ax=ax, cmap='Reds')
    sachsen_proj.boundary.plot(
        ax=ax, color='black', linewidth=1)
    ax.axis('off')
```

<!-- #region slideshow={"slide_type": ""} editable=true -->
:::{seealso}
For a better understanding of the code, see the [rasterio documentation](https://rasterio.readthedocs.io/en/stable/topics/masking-by-shapefile.html).
:::
<!-- #endregion -->

<!-- #region slideshow={"slide_type": ""} editable=true -->
Save the results to disk as a GeoTIFF. To do this, we first update the clipped raster meta object (`out_meta`) with the transformation information.
<!-- #endregion -->

```python editable=true slideshow={"slide_type": ""}
out_meta.update({
    "driver": "GTiff",
    "height": out_image.shape[1],
    "width": out_image.shape[2],
    "transform": out_transform,
    })
```

<!-- #region editable=true slideshow={"slide_type": ""} -->
Then use `rasterio.open()` to write the clipped raster.
<!-- #endregion -->

```python slideshow={"slide_type": ""} editable=true
gtiff_path = OUTPUT / f'saxony_{LAYER}.tif'

with rasterio.open(gtiff_path, "w", **out_meta) as dest:
    dest.write(out_image)

# Get the file size in MB
file_size = gtiff_path.stat().st_size / (1024 * 1024)

print(f"GeoTIFF saved successfully. File size: {file_size:.2f} MB.")
```

```python slideshow={"slide_type": ""} tags=["remove-input"] editable=true
import sys
from pathlib import Path

module_path = str(Path.cwd().parents[0] / "py")
if module_path not in sys.path:
    sys.path.append(module_path)
from modules import tools

root_packages = [
    'python', 'geopandas', 'pandas', 'matplotlib', 'owslib', 'requests', 'rasterio', 'lxml' 'dotenv']
tools.package_report(root_packages)
```

```python

```

```python

```
