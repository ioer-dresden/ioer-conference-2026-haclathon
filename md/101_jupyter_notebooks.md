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

<!-- #region editable=true slideshow={"slide_type": ""} -->
# Setup & Getting familiar with Jupyter
<!-- #endregion -->

```{admonition} Summary
:class: hint
This chapter provides a brief introduction to the key components of the Jupyter. For a more detailed information, please see [jupyter.org](https://docs.jupyter.org/en/latest/).
```


**Jupyter** is a software that includes various tools for interactive computing. 
These training materials are built using **Jupyter Notebooks**, which are interactive documents that combine explanations, code, and outputs in one place. The notebooks were created using **JupyterLab**, which is a web-based development environment that provides an integrated workspace for notebooks, text editors, terminals, and more. To make navigation easier, individual notebooks have been structured into a **Jupyter Book**, which organizes the content into chapters and pages.

Learn more about [Jupyter Notebook](https://jupyter-notebook.readthedocs.io/en/latest/), [JupyterLab](https://jupyterlab.readthedocs.io/en/stable/getting_started/overview.html) and [Jupyter Book](https://jupyterbook.org/en/stable/intro.html).


## How to use the Notebooks?

The notebooks can be used in several ways:

- **As a source of information**: Use the notebooks as a source of information by reading the main chapters and skipping sections that involve Python specifics.
- **For code snippets**: Browse through the chapters and select and copy relevant code snippets to use in your own projects.
- **Interactively**: Run the Jupyter Notebooks to explore and experiment  with the workflows, trying out the code and modifying it for your needs.


## How to copy code snippets?
The page is organized into sections called ‘cells,’ which may include text explanations, images, or code.

To copy a code snippet, click the copy icon in the top-right corner of the code cell.

```python slideshow={"slide_type": ""} editable=true
# See the copy button on the right corner when you hover over this text.
```

`````{tip}
:class: tip
In Jupyter Notebooks, text cells use Markdown, a simple markup language for formatting notes, documents, presentations, and websites. Markdown works across all operating systems and is converted to HTML for display in web browsers.

Learn more about using [Markdown](https://www.markdownguide.org/getting-started/).
`````

<!-- #region editable=true slideshow={"slide_type": ""} -->
## How to run the training materials interactively?
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
In Python, "dependencies" typically refer to **packages** and **libraries** that the code needs to work properly. Packages and libraries are collections of pre-written code that help you perform various tasks more easily. Each package or library is designed for a specific purpose, such as visualising data.

To successfully run the workflows in these notebooks, you must have the required packages or libraries installed. The first software that is needed is **JupyterLab**.
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
```{admonition} Not familiar with Python packages or libraries?
:class: dropdown, seealso
The [Python Standard Library Documentation](https://docs.python.org/3/library/index.html) and the lists below provide selected standard library modules as well as third-party packages and libraries.

<details>
<summary><strong>Selected standard library modules (pre-installed with Python)</strong></summary>
    
- [csv](https://docs.python.org/3/library/csv.html):                CSV file reading and writing
- [sys](https://docs.python.org/3/library/sys.html):                System-specific parameters and functions
- [pathlib](https://docs.python.org/3/library/pathlib.html): Object-oriented filesystem paths
- [collections](https://docs.python.org/3/library/collections.html): Container datatypes
- [typing](https://docs.python.org/3/library/typing.html): Support for type hints
- [os](https://docs.python.org/3/library/os.html): Miscellaneous operating system interfaces
      
</details>

<details>
<summary><strong>Selected third-party packages and libaries (require installation)</strong></summary> 
    
- [requests](https://pypi.org/project/requests/): Simplifies making HTTP requests, allowing users to easily send and receive data from web APIs
- [shapely](https://shapely.readthedocs.io/en/latest/manual.html): Geometric operations and spatial queries
- [numpy](https://numpy.org/): Numerical computing and array operations
- [holoviews](https://holoviews.org/): High-level data visualization framework
- [geoviews](https://geoviews.org/): Geographic data visualizations for HoloViews
- [geopandas](https://geopandas.org): Geospatial data manipulation using pandas.
- [pyproj](https://pypi.org/project/pyproj/): Cartographic projections and coordinate transformations library
- [cartopy](https://github.com/SciTools/cartopy): Drawing maps for data analysis and visualisation
- [bokeh](https://github.com/bokeh/bokeh): Interactive web-based visualizations with JavaScript integration.
- [matplotlib](https://matplotlib.org/): Plotting and data visualization library
- [ggplot2](https://ggplot2.tidyverse.org/): System for declaratively creating graphics
  
</details>

```
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
Installing JupyterLab is relatively easy:
<!-- #endregion -->

<!-- #region -->
```bash
pip install jupyterlab
jupyter lab # run jupyterlab
```
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
However, from there, Python package management, version conflicts, dependency issues and many other challenges can make it very difficult for beginnings to reproduce the outputs we show here. You have different options that we explain below.
<!-- #endregion -->

### Jupyter4NFDI

You can interactively run this notebook on the Jupyter4NFDI platform using Binder integration. Simply click the Binder icon in the upper-right corner of the page.

```{figure} ../resources/binder.png
:name: Jupyter4NFDI_Binder
:figclass: fig-no-shadow

Run a notebook in this book via the Jupyter4NFDI platform using Binder integration.
```

#### 🔐 Authentication via Helmholtz AAI

Jupyter4NFDI utilizes the Helmholtz Authentication and Authorization Infrastructure (AAI) for secure access. This federated login system allows you to authenticate using your institutional credentials or social identities like GitHub, Google, or ORCID.

1. **Click the Binder icon**: Located in the top-right corner of the notebook page.
2. **Select your Identity Provider (IdP)**: Choose your home institution or preferred social IdP from the list.
3. **Authenticate**: Enter your credentials as prompted.
4. **Access the notebook**: After successful authentication, you'll be directed to an interactive Jupyter environment with the notebook ready to use.

```{admonition} Tip for IOER Members. 
:class: tip
If you're affiliated with the IOER, select **TU Dresden** as your Identity Provider during the login process.
```

For a list of connected organizations supporting eduGAIN, refer to the [Helmholtz AAI documentation](https://hifis.net/doc/helmholtz-aai/list-of-connected-organisations/#edugain).

**Additional Resources:**

- **Jupyter4NFDI Hub**: [https://hub.nfdi-jupyter.de/hub/home](https://hub.nfdi-jupyter.de/hub/home)
- **Jupyter4NFDI Documentation**: [https://jupyterjsc.pages.jsc.fz-juelich.de/docs/jupyter4nfdi/](https://jupyterjsc.pages.jsc.fz-juelich.de/docs/jupyter4nfdi/)


<video controls style="max-width: 100%; height: auto; border: 0px; border-radius: 0px;">
  <source src="../_static/videos/jupyter4nfdi.webm" type="video/webm" />
  Your browser does not support the video tag.
</video>
<figcaption>Starting a notebook interactively in the Jupyter4NFDI Binder Hub.</figcaption>


### Carto-Lab Docker

<!-- #region slideshow={"slide_type": ""} editable=true -->
To ensure full reproducibility of the HaCLAthon materials, we use a prepared system environment called [Carto-Lab Docker](https://cartolab.fdz.ioer.info/).

Carto-Lab Docker includes
- Jupyter Lab 
- A Python environment with major cartographic packages pre-installed 
- The base system (Linux) 

All these components are packaged in a Docker container, which is **versioned** and made available through a registry. The version number allows you to pull the correct archive container to run these notebooks. Below we show the version of Carto-Lab Docker used:
<!-- #endregion -->

```python editable=true tags=["remove-input"] slideshow={"slide_type": ""}
from IPython.display import Markdown as md
from datetime import date

today = date.today()

try:
    app_version = open('/.version').read().split("'")[1]
    extra = f', [IOER FDZ Carto-Lab Docker](https://cartolab.fdz.ioer.info/) <kbd>Version {app_version}</kbd>'
except FileNotFoundError:
    extra = ''

md(f"Last updated: <kbd>{today.strftime('%b-%d-%Y')}</kbd>{extra}")
```

<!-- #region slideshow={"slide_type": ""} editable=true -->
`````{admonition} See the Carto-Lab Docker docs for installation instructions
:class: dropdown, hint

This is from the [Carto-Lab Docker docs](https://cartolab.theplink.org/docker/).
                                              
```bash
# create a shallow clone (no git history, just the latest files)
git clone --depth 1 https://gitlab.vgiscience.de/lbsn/tools/jupyterlab.git
cd jupyterlab
cp .env.example .env
nano .env
# Enter the Carto-Lab Docker version you want to use
# TAG=v0.26.1
docker network create lbsn-network
docker-compose pull && docker-compose up -d
```
`````
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
```{admonition} We only guarantee reproducibility with Carto-Lab Docker
:class: attention
Due to the wide variety of possible setups, operating systems (Windows, Linux, Mac), software versions and changing environments, we can only guarantee complete reproducibility with the exact Carto-Lab Docker version shown above. You may still be lucky if you use some of the alternatives we show you below.

In general, we recommend to avoid Windows under any circumstances. If you are working in Windows, a better alternative is either to use Windows Subsystem for Linux (WSL) or to run these notebooks in the cloud somewhere (ask your IT/Admin). For instance, Carto-Lab Docker can also be run in the cloud.
```
<!-- #endregion -->

### Clone the training materials


In order to use the starter kit locally or in Carto-Lab, the repository must be cloned. Open a terminal and type the following command:

<!-- #region -->
```bash
# create a shallow clone (no git history, just the latest files)
git clone --depth 1 https://github.com/ioer-dresden/ioer-conference-2026-hackathon.git
```
<!-- #endregion -->

<!-- #region slideshow={"slide_type": ""} editable=true -->
``````{admonition} Use the Jupyter Terminal
:class: hint
You can use the terminal that is provided by Jupyter. At your Jupyter Dashboard, click the following Icon:
```{figure} ../resources/terminal.jpg
:name: terminal-icon

This is the terminal icon.
```
Afterwards, type:
```bash
cd /home/jovyan/work/
# create a shallow clone (no git history, just the latest files)
git clone --depth 1 https://github.com/ioer-dresden/ioer-conference-2026-hackathon.git
```

- `/home/jovyan/work/` is the path to the default home folder in Jupyter. The home folder is the folder you see in the explorer on the left side when you are logged in to Jupyter.
``````
<!-- #endregion -->

<!-- #region slideshow={"slide_type": ""} editable=true -->
### Jupyterlab: Basic key commands 

After these steps, you are ready to go. You can find the individual notebooks of the training materials in the subfolder `notebooks/`.

These are the most important key commands, to get you started.

- <kbd>SHIFT + ENTER</kbd> → Run the current cell and go to the next
- <kbd>CTRL + ENTER</kbd> → Run multiple selected cells
- <kbd>CTRL + X</kbd> → Cut selected cells
- <kbd>d d (press d twice)</kbd> → Delete selected cells

<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
### Installing dependencies individually

You can also install the packages individually:
1. Install all packages for all notebooks in a single environment (harder, but less work)
2. or install all packages for each notebook into a separate environment (easier, but more work)
<!-- #endregion -->

<!-- #region slideshow={"slide_type": ""} editable=true -->
You can start with the [environment.yml](https://raw.githubusercontent.com/ioer-dresden/ioer-conference-2026-haclathon/refs/heads/main/.binder/environment.yaml) that we provide in the `.binder` folder and install the environment manually with:
```bash
conda env create -f environment.yaml
```
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
This will install the packages, but not the exact package versions. We  provide a summary of the package versions used at the end of each notebook chapter. Example:
<!-- #endregion -->

```python editable=true tags=["remove-input"] slideshow={"slide_type": ""}
import sys
from pathlib import Path

module_path = str(Path.cwd().parents[0] / "py")
if module_path not in sys.path:
    sys.path.append(module_path)
from modules import tools

root_packages = [
    'python', 'geopandas', 'pandas', 'matplotlib', 'dask', 'datashader']
tools.package_report(root_packages)
```

<!-- #region -->
To install the above packages, use e.g.:
```bash
pip install python==3.11.6 dask==2024.12.1 datashader==0.17.0 geopandas==0.14.4 matplotlib==3.10.1 pandas==2.2.3
```
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
## Temporary package installs
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
Sometimes, a default environment exists that already includes many packages. Only some new packages need to be installed for certain notebooks. In these cases, it can be _Ok_ to install packages temporarily directly from within Jupyter. 

```{admonition} Example notebook
:class: hint
We do this, for example, for `owslib` in our workflow in [Data Retrieval: IOER Monitor](102_data_retrieval_monitor): The Carto-Lab Docker environment does not contain this package and we only need it once to query the IOER Monitor API.
```
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
You can install packages temporarily by issuing bash commands directly in a code cell with a `!`-prefix.
<!-- #endregion -->

<!-- #region slideshow={"slide_type": ""} editable=true -->
```bash
!pip install owslib
```
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
We have written a little helper script that comes with the training materials that also checks if the package is already installed.
<!-- #endregion -->

```python slideshow={"slide_type": ""} editable=true tags=["remove-input"]
tools.display_file(Path.cwd().parents[0] / 'py' / 'modules' / 'pkginstall.sh')
```

<!-- #region slideshow={"slide_type": ""} editable=true -->
``````{note}
This script _should_ work in most environments. Make sure you specify the name of the current kernel environment, e.g:
```
import sys
pyexec = sys.executable
print(f"Current Kernel {pyexec}")
!../py/modules/pkginstall.sh "{pyexec}" geopandas 
```
``````
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": ""} -->
## How to import Packages and Libraries
<!-- #endregion -->

After successfully installing the package, you need to import it in your notebook to be able to use their functions.


Create a new code cell where you can write your statements. To import a package, use the "import" keyword followed by the "package name". 
- **Example:** import pandas

Or to make it easier to call during coding use an alias :

- **Example:** import pandas as pd



![../resources/7.png](../resources/7.png)


This cell is not showing any output unless the package or library not installed successfully :


![../resources/8.png](../resources/8.png)


If the installation was successful but still the issue persists, it could be due to using the wrong environment or kernel.


- Wrong Environment: Package or Library is not installed in the current environment:
  
  **Solution:** Activate the correct environment, then restart Jupyter.



<!-- #region editable=true slideshow={"slide_type": ""} -->
- Wrong Kernel: Package or Library is not installed in the selected Jupyter kernel.

  **Solution:** Switch to the correct kernel via the upper-right menu in Jupyter.
 
  

<!-- #endregion -->

![../resources/9.png](../resources/9.png)

```python

```
