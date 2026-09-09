"""
storybuilder.py – Helpers for authoring StoryMap chapters from a JupyterLab notebook.

License: MIT License
"""

# --- Standard Library ---
import base64
import json
import shutil
from pathlib import Path

# --- Third-Party Libraries ---
from ipywidgets import Box, HTML, VBox

# --- Globals ---
# The template ships inside this package, so it is found through the module's
# own location rather than the notebook's working directory. That keeps
# save_story working the same from notebooks/, from the repository root, or
# from a Colab clone, none of which agree on what "template" would mean.
TEMPLATE_DIR = Path(__file__).parent / "storymap_template"

# Chapter card width and left offset, as a % of the viewport. Mimic styles.css in template,
# so a preview here frames the same way the published page does.
ALIGNMENTS = {
    "lefty": (33, 5),
    "righty": (33, 60),
    "centered": (50, 25),
    "fully": (80, 10),
}

CARD_CSS = """
<style>
.chapter-stage { position: relative; }
.chapter-stage .chapter-card {
    position: absolute;
    top: 50%;
    transform: translateY(-50%);
    z-index: 500;
    box-sizing: border-box;
    background: #f1f5f6;
    color: #3b3b3b;
    border-radius: 10px;
    padding: 25px 50px;
    line-height: 1.5rem;
    pointer-events: none;   /* let the map be dragged from underneath the card */
}
</style>
"""


MIME = {
    ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
    ".gif": "image/gif", ".svg": "image/svg+xml", ".webp": "image/webp",
}

# --- Writing chapters --------------------------------------------------------
FORMS = {"circle": "circlePaint", "fill": "fillPaint"}


def _paint(form, colour, colour_by, colour_default, size, opacity, stroke, stroke_colour):
    """Build the paint block for one geometry type.

    `colour` takes whichever shape suits the layer:
      "#ef7851"                       one colour for everything
      {"Grey Heron": "#6c97ba", ...}  a colour per value of `colour_by`
      ["interpolate", ...]            a MapLibre expression, passed through
    """
    if isinstance(colour, dict):
        expression = ["match", ["get", colour_by]]
        for value, hex_code in colour.items():
            expression += [value, hex_code]
        expression.append(colour_default)
        colour = expression

    if form == "fill":
        paint = {"fill-color": colour, "fill-opacity": opacity}
        if stroke:
            paint["fill-outline-color"] = stroke_colour
        return paint

    paint = {"circle-radius": size, "circle-color": colour, "circle-opacity": opacity}
    if stroke:
        paint["circle-stroke-width"] = stroke
        paint["circle-stroke-color"] = stroke_colour
    return paint


def geojson_layer(file, *, form="circle", colour="#1d6ad6", colour_by="sp",
                  colour_default="#b9b7b0", size=5, opacity=0.85, stroke=0,
                  stroke_colour="#00000033", layer_id=None, source_id=None):
    """Describe one GeoJSON layer, ready to hand to write_chapter.

    Keeping this separate means a chapter call stays about the story - title,
    text, where the camera goes - while the styling is prepared once, next to
    the palette it uses, and can be reused by more than one chapter.

    Args:
        file: path to the GeoJSON, relative to the site root.
        form: "circle" for points, "fill" for polygons.
        colour: one hex, a {value: hex} mapping, or a MapLibre expression.
        colour_by: which property a {value: hex} mapping looks at.
        colour_default: colour for values the mapping does not name.
        size, opacity, stroke, stroke_colour: mark styling.
        layer_id: set this when two chapters read the same file, or the second
            one silently reuses the first one's layer and paint.
        source_id: give two chapters the same value to share one copy of the
            data. Without it each chapter's layer id produces its own source,
            so the same file is fetched and parsed once per chapter and the
            browser keeps a second copy of every feature in memory.

    Returns:
        The chapter's "data" block.
    """
    if form not in FORMS:
        raise ValueError(f"form {form!r} not in {sorted(FORMS)}")

    data = {"file": file,
            FORMS[form]: _paint(form, colour, colour_by, colour_default,
                                size, opacity, stroke, stroke_colour)}
    if layer_id:
        data["id"] = layer_id
    if source_id:
        data["sourceId"] = source_id
    return data


def write_chapter(title, text, center, zoom, *, align="lefty",
                  bearing=0, pitch=0, duration=None, image=None,
                  wmslayer=None, geojson=None):
    """Assemble one chapter for _config.json.

    Args:
        title, text: the card's heading and html body.
        center: [lon, lat] - MapLibre's order, longitude first. ipyleaflet's
            map.center is the other way round, so reverse it before passing.
        zoom: MapLibre zoom, one level lower than the same view in Leaflet.
        align: lefty, righty, centered or fully.
        bearing, pitch, duration: optional camera rotation, tilt, flight time.
        image: path to a picture for the card, relative to the site root.
        wmslayer: an XYZ tile url with {z}/{x}/{y}, shown while this chapter
            is active.
        geojson: a path, or a layer from geojson_layer() when it needs styling.

    Returns:
        A chapter dict, ready for the "chapters" list.
    """
    if align not in ALIGNMENT_VALUES:
        raise ValueError(f"alignment {align!r} not in {ALIGNMENT_VALUES}")

    location = {"center": list(center), "zoom": zoom,
                "bearing": bearing, "pitch": pitch}
    if duration is not None:
        location["duration"] = duration

    chapter = {"title": title, "description": text,
               "alignment": align, "location": location}
    if image:
        chapter["image"] = image
    if wmslayer:
        chapter["wmslayer"] = wmslayer
    if geojson:
        chapter["data"] = geojson_layer(geojson) if isinstance(geojson, str) else geojson
    return chapter


def _image_tag(src):
    """Build an <img> the widget can actually display.

    A relative path works in the published story map, because the browser
    resolves it against the site. It does not work here: the card is drawn
    inside the notebook's output frame, whose base URL is not this folder, so
    the browser looks for the file somewhere it does not exist and shows
    nothing. Reading the bytes and inlining them as a data URI sidesteps that.

    Remote URLs are passed through untouched, since those resolve anywhere.
    """
    if not src:
        return ""
    if src.startswith(("http://", "https://", "data:")):
        return f"<img src='{src}' style='max-width:100%;margin-top:.6em'>"

    path = Path(src)
    if not path.exists():
        return (f"<div style='color:#a33;font-size:12px;margin-top:.6em'>"
                f"image not found: {src}</div>")

    data = base64.b64encode(path.read_bytes()).decode("ascii")
    mime = MIME.get(path.suffix.lower(), "image/png")
    return (f"<img src='data:{mime};base64,{data}' "
            f"style='max-width:100%;margin-top:.6em'>")


def _coords_widget(m):
    """A readout that follows one map, already converted for MapLibre.

    ipyleaflet reports (lat, lon) and counts zoom on 256px tiles; MapLibre
    wants [lon, lat] and sits one level lower. Doing the conversion here means
    the numbers can be pasted into write_chapter as they are.

    Each call makes its own widget bound to its own map, so two maps in one
    notebook do not end up sharing a readout.
    """
    readout = HTML()

    def refresh(_=None):
        lat, lon = m.center
        readout.value = (f"<code>center = [{lon:.5f}, {lat:.5f}], "
                         f"zoom = {m.zoom - 1:.2f}</code>")

    refresh()
    m.observe(refresh, names=["center", "zoom"])
    return readout


def preview_map(m, height="500px"):
    """Show a map with a live centre and zoom readout underneath.

    Args:
        m: the ipyleaflet Map to follow.
        height: CSS height for the map.

    Returns:
        A VBox holding the map and its readout.
    """
    m.layout.height = height
    m.layout.width = "100%"
    return VBox([m, _coords_widget(m)])


def chapter_preview(chapter, m, height="500px"):
    """Draw a chapter card over a live map, to frame its location interactively.

    The card is placed with the width and offset the published page would give it,
    so panning and zooming the map below shows what the text box covers. The
    readout underneath reports the current view already converted to MapLibre's
    conventions - [lon, lat] order, and one zoom level lower than Leaflet - ready
    to paste into the chapter's "location".

    Args:
        chapter: chapter dict, using its "title", "description" and "alignment".
        m: the ipyleaflet Map to frame against.
        height: CSS height for the map.

    Returns:
        A VBox holding the styles, the map with its card, and the live readout.
    """
    width, left = ALIGNMENTS.get(chapter.get("alignment", "centered"), (50, 25))

    m.layout.height = height
    m.layout.width = "100%"

    card = HTML(
        f"<h3 style='margin:0 0 .4em'>{chapter['title']}</h3>"
        f"<div style='font-size:14px'>{chapter['description']}</div>"
        + _image_tag(chapter.get("image"))
    )
    card.add_class("chapter-card")
    card.layout.left = f"{left}%"
    card.layout.width = f"{width}%"

    stage = Box([m, card])
    stage.add_class("chapter-stage")
    stage.layout.width = "100%"

    return VBox([HTML(CARD_CSS), stage, _coords_widget(m)])


# --- Config schema -----------------------------------------------------------
# Only the four alignments below have a CSS class in styles.css. Anything else
# is added to the section as a class that does not exist, so the chapter loses
# its layout silently - no error, just a broken page.
ALIGNMENT_VALUES = ["lefty", "righty", "centered", "fully"]

_LOCATION = {
    "type": "object",
    "properties": {
        "center": {
            "type": "array", "minItems": 2, "maxItems": 2,
            "prefixItems": [
                {"type": "number", "minimum": -180, "maximum": 180},  # lon first
                {"type": "number", "minimum": -90, "maximum": 90},
            ],
        },
        "zoom": {"type": "number", "minimum": 0, "maximum": 24},
        "bearing": {"type": "number"},
        "pitch": {"type": "number", "minimum": 0, "maximum": 85},
        "duration": {"type": "number", "minimum": 0},
    },
    "required": ["center", "zoom"],
}

# intro panels and chapters are the same kind of step and go through the same
# code path in scrolly.js, so they take the same keys. Only the requirements
# differ: a chapter needs a title and a description, a hook may be one line.
_STEP_PROPERTIES = {
    "id": {"type": "string"},
    "title": {"type": "string", "minLength": 1},
    "description": {"type": "string"},
    "alignment": {"enum": ALIGNMENT_VALUES},
    # extra CSS classes on the section, e.g. "hook". Same caveat as alignment:
    # a class with no rule in styles.css does nothing and reports nothing.
    "class": {"type": "string"},
    "image": {"type": "string"},
    "image_alt": {"type": "string"},
    "threed": {"type": "boolean"},
    "wmslayer": {"type": ["string", "object"]},
    "location": _LOCATION,
    # a plain path string is shorthand for {"file": <path>}, as in scrolly.js.
    # "required" and "properties" only constrain objects, so a string skips both.
    "data": {
        "type": ["string", "object"],
        "required": ["file"],
        "properties": {
            "file": {"type": "string"},
            "id": {"type": "string"},
            "sourceId": {"type": "string"},
            "fillPaint": {"type": "object"},
            "circlePaint": {"type": "object"},
        },
    },
}

CONFIG_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "StoryMap _config.json",
    "type": "object",
    "required": ["chapters"],
    "properties": {
        "mapstyle": {"type": "string"},
        "wmslayer": {"type": ["string", "object"]},
        "threed": {"type": ["boolean", "string"]},
        "location": _LOCATION,
        "cover": {
            "type": "object",
            "properties": {"title": {"type": "string"},
                           "subtitle": {"type": "string"},
                           # a picture for the cover, laid down the left
                           "image": {"type": "string"}},
        },
        "footer": {"type": "string"},
        "intro": {
            "type": "array",
            "items": {"type": "object", "properties": _STEP_PROPERTIES},
        },
        "chapters": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["title", "description"],
                "properties": _STEP_PROPERTIES,
            },
        },
    },
}


def validate_config(config, base=None):
    """Check a config against the schema, and check the files it points at.

    JSON Schema catches shape errors - a missing title, an alignment with no CSS
    class, a latitude where a longitude belongs. It cannot know whether
    "assets/points.geojson" exists, so that is checked separately when `base` is
    given.

    Args:
        config: the config dict about to be written.
        base: directory the config's relative paths resolve against. Skipped
            when None.

    Raises:
        ValueError: with every problem found, not just the first.
    """
    import jsonschema

    problems = [
        f"{'/'.join(str(p) for p in e.absolute_path) or '(root)'}: {e.message}"
        for e in sorted(jsonschema.Draft202012Validator(CONFIG_SCHEMA).iter_errors(config),
                        key=lambda e: list(e.absolute_path))
    ]

    if base is not None:
        base = Path(base)
        cover_image = (config.get("cover") or {}).get("image")
        if cover_image and not cover_image.startswith(("http://", "https://")):
            if not (base / cover_image).exists():
                problems.append(f"cover/image: file not found: {cover_image}")

        for key in ("intro", "chapters"):
            for i, step in enumerate(config.get(key, [])):
                # unwrap the shorthand. anything else is left to the schema
                # error already collected above, rather than crashing here.
                data = step.get("data")
                data_file = data if isinstance(data, str) else (
                    data.get("file") if isinstance(data, dict) else None)
                for ref in (step.get("image"), data_file):
                    if ref and not ref.startswith(("http://", "https://")):
                        if not (base / ref).exists():
                            problems.append(f"{key}/{i}: file not found: {ref}")

    if problems:
        raise ValueError("config is not valid:\n  - " + "\n  - ".join(problems))
    return True


def save_story(config, site="storymap", assets="assets", template=None):
    """Validate a config, then write a self-contained story map folder.

    The page, its script and its styles are copied from the template, the
    template's own assets come along (the cover markup expects the logo), then
    everything in the story's `assets` folder is copied over the top.
    `_config.json` is written last, so a failed validation leaves any previous
    build untouched.

    Args:
        config: the config dict.
        site: output folder.
        assets: folder holding this story's images and data. Every file in it
            is copied to site/assets/, so a cover image or a GeoJSON only has
            to be dropped in there to reach the published page. Files here
            override same-named files from the template.
        template: folder holding template.html, scrolly.js, styles.css and
            assets/. Defaults to the copy shipped with this module; pass a
            path only to build against a customised template.

    Returns:
        Path to the site folder.
    """
    site = Path(site)
    template = TEMPLATE_DIR if template is None else Path(template)
    (site / "assets").mkdir(parents=True, exist_ok=True)

    shutil.copy(template / "template.html", site / "index.html")
    for name in ("scrolly.js", "styles.css"):
        shutil.copy(template / name, site / name)
    for f in sorted((template / "assets").glob("*")):
        if f.is_file():
            shutil.copy(f, site / "assets" / f.name)

    assets = Path(assets) if assets else None
    if assets and assets.is_dir():
        for f in sorted(assets.glob("*")):
            if f.is_file():
                shutil.copy(f, site / "assets" / f.name)

    # validated only now, so the assets it refers to are already in place
    validate_config(config, base=site)
    (site / "_config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    return site
