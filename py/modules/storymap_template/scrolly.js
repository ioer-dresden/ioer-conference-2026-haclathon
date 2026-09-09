//scroll restoration
window.history.scrollRestoration = "manual";

var storyArea = document.getElementById("scrollyStory");
var cover = document.getElementById("cover");
var footer = document.getElementById("footer");

// load story content from JSON, then build the page
fetch("./_config.json")
  .then((response) => response.json())
  .then((article) => buildStory(article))
  .catch((err) => console.error("Could not load _config.json:", err));

function buildStory(article) {
  /* define cover */
  if (article.cover) {
    cover.classList.add("cover");
    cover.id = `cover`;
    var byline = document.getElementById("hint_scrollDown");
    if (article.cover.title) {
      var title = document.createElement("h1");
      title.innerHTML = article.cover.title;
      cover.insertBefore(title, byline);
    }
    if (article.cover.subtitle) {
      var subtitle = document.createElement("h2");
      subtitle.innerHTML = article.cover.subtitle;
      cover.insertBefore(subtitle, byline);
    }

    // a picture for the cover, laid down the left while the words sit right
    if (article.cover.image) {
      document.getElementById("cover_image").src = article.cover.image;
    }
  }

  /*define steps*/
  // optional intro panels come before the chapters, in one flat list. scrollama
  // reports a step by its position, so the list it indexes into has to hold
  // every step - otherwise an intro panel shifts each chapter's map behaviour.
  const steps = (article.intro || []).concat(article.chapters);

  steps.forEach((element, idx) => {
    // create a section to contain each chapter
    const section = document.createElement("section");
    section.classList.add("section");
    section.id = `section-${idx}`;

    // create a div for chapter content
    const chapter = document.createElement("div");
    chapter.id = `chapter-${idx}`;
    chapter.classList.add("chapter");

    // add content to the chapter
    if (element.title) {
      var title = document.createElement("h2");
      title.innerHTML = element.title;
      chapter.appendChild(title);
    }

    if (element.description) {
      var text = document.createElement("div");
      text.innerHTML = element.description;
      chapter.appendChild(text);
    }

    // add an image if it exists
    if (element.image) {
      var img = document.createElement("img");
      img.src = element.image;
      img.alt = element.image_alt || "image";
      img.classList.add("chapter-image");
      chapter.appendChild(img);
    }

    // define position of the chapter
    section.classList.add(element.alignment || "centered");

    // extra classes for a step styled differently from a chapter card
    if (element.class) {
      section.classList.add(...element.class.split(" "));
    }

    //set the first chapter as active
    if (idx === 0) {
      section.classList.add("active");
    }

    // add the chapter
    section.appendChild(chapter);
    storyArea.appendChild(section);
  });

  // show each counter's starting value until its chapter scrolls into view
  document.querySelectorAll(".animated-counter").forEach((el) => {
    el.innerText = el.dataset.from || "0";
  });

  // count any <span class="animated-counter"> in a chapter up to its target
  function animateCounters(container) {
    container.querySelectorAll(".animated-counter").forEach((el) => {
      const from = Number(el.dataset.from) || 0;
      const target = Number(el.dataset.target) || 0;
      const duration = Number(el.dataset.duration) || 2000;
      const start = performance.now();
      function tick(now) {
        const t = Math.min((now - start) / duration, 1);
        el.innerText = Math.round(from + (target - from) * t).toLocaleString();
        if (t < 1) requestAnimationFrame(tick);
      }
      requestAnimationFrame(tick);
    });
  }

  /*define footer*/
  if (article.footer) {
    const footer_text = document.createElement("div");
    footer_text.innerHTML = article.footer;
    footer.appendChild(footer_text);
  }

  /*define map*/
  // initial camera: optional top-level "location" in _config.json
  const start = article.location || {};
  const map = new maplibregl.Map({
    container: "map",
    style: `https://tiles.openfreemap.org/styles/${article.mapstyle}`,
    center: start.center || [13.748, 51.0312],
    zoom: start.zoom ?? 15.5,
    bearing: start.bearing ?? 0,
    pitch: start.pitch ?? 45,
  });

  // disable map zoom when using scroll
  map.scrollZoom.disable();

  // load a WMS/raster layer from the start if requested globally
  if (article.wmslayer) {
    map.on("load", () => loadWmsLayer(article.wmslayer, "wms-global"));
  }

  // add a WMS/raster layer on demand (only once per layer)
  function loadWmsLayer(wms, id) {
    if (!wms) return;

    // shorthand: a plain tile URL string, or an object for more control
    const url = typeof wms === "string" ? wms : wms.url;
    if (!url) return;
    const layerId = id || (typeof wms === "object" && wms.id) || "wms-layer";
    const sourceId = `${layerId}-source`;
    const tileSize = (typeof wms === "object" && wms.tileSize) || 256;

    // wait for the style if it isn't ready yet, then retry
    if (!map.isStyleLoaded()) {
      map.once("idle", () => loadWmsLayer(wms, id));
      return;
    }

    // if already added, just make it visible again
    if (map.getLayer(layerId)) {
      map.setLayoutProperty(layerId, "visibility", "visible");
      return;
    }

    if (!map.getSource(sourceId)) {
      map.addSource(sourceId, {
        type: "raster",
        tiles: [url],
        tileSize: tileSize,
      });
    }

    map.addLayer({
      id: layerId,
      type: "raster",
      source: sourceId,
      paint: {},
    });
  }

  // hide a WMS/raster layer when leaving a chapter
  function hideWmsLayer(wms, id) {
    if (!wms) return;
    const layerId = id || (typeof wms === "object" && wms.id) || "wms-layer";
    if (map.getLayer(layerId)) {
      map.setLayoutProperty(layerId, "visibility", "none");
    }
  }

  // load the 3D buildings from the start if requested globally
  if (article.threed) {
    map.on("load", load3dBuildings);
  }

  // add the 3D buildings layer on demand (only once)
  function load3dBuildings() {
    // wait for the style if it isn't ready yet, then retry
    if (!map.isStyleLoaded()) {
      map.once("idle", load3dBuildings);
      return;
    }

    // if already added, just make it visible again
    if (map.getLayer("3d-buildings")) {
      map.setLayoutProperty("3d-buildings", "visibility", "visible");
      return;
    }

    // Insert the layer beneath any symbol layer.
    const layers = map.getStyle().layers;

    let labelLayerId;
    for (let i = 0; i < layers.length; i++) {
      if (layers[i].type === "symbol" && layers[i].layout["text-field"]) {
        labelLayerId = layers[i].id;
        break;
      }
    }

    if (!map.getSource("openfreemap")) {
      map.addSource("openfreemap", {
        url: `https://tiles.openfreemap.org/planet`,
        type: "vector",
      });
    }

    map.addLayer(
      {
        id: "3d-buildings",
        source: "openfreemap",
        "source-layer": "building",
        type: "fill-extrusion",
        minzoom: 15,
        filter: ["!=", ["get", "hide_3d"], true],
        paint: {
          "fill-extrusion-color": "lightgray",
          "fill-extrusion-height": [
            "interpolate",
            ["linear"],
            ["zoom"],
            15,
            0,
            16,
            ["get", "render_height"],
          ],
          "fill-extrusion-base": [
            "case",
            [">=", ["get", "zoom"], 16],
            ["get", "render_min_height"],
            0,
          ],
        },
      },
      labelLayerId,
    );

    // make sure it's visible (it may have been hidden on a previous exit)
    map.setLayoutProperty("3d-buildings", "visibility", "visible");
  }

  // hide the 3D buildings layer when leaving a threed chapter
  function hide3dBuildings() {
    if (map.getLayer("3d-buildings")) {
      map.setLayoutProperty("3d-buildings", "visibility", "none");
    }
  }

  // add a chapter's custom map layer on demand (only once per layer)
  function loadLayer(chapter) {
    if (!chapter || !chapter.layer) return;

    const layer = chapter.layer;
    const sourceId = layer.sourceId || `${layer.id}-source`;

    // wait for the style if it isn't ready yet, then retry
    if (!map.isStyleLoaded()) {
      map.once("idle", () => loadLayer(chapter));
      return;
    }

    // if already added, just make it visible again
    if (map.getLayer(layer.id)) {
      map.setLayoutProperty(layer.id, "visibility", "visible");
      return;
    }

    if (layer.source && !map.getSource(sourceId)) {
      map.addSource(sourceId, layer.source);
    }

    map.addLayer({
      id: layer.id,
      type: layer.type,
      source: sourceId,
      paint: layer.paint || {},
    });
  }

  // hide a chapter's custom map layer when leaving the chapter
  function hideLayer(chapter) {
    if (!chapter || !chapter.layer) return;
    if (map.getLayer(chapter.layer.id)) {
      map.setLayoutProperty(chapter.layer.id, "visibility", "none");
    }
  }

  // normalize chapter.data, which may be a file string or a config object
  function dataConfig(chapter) {
    if (!chapter || !chapter.data) return null;
    // shorthand: "data": "assets/foo.geojson"
    const data =
      typeof chapter.data === "string" ? { file: chapter.data } : chapter.data;
    if (!data.file) return null;
    // derive a stable layer id from the file name if none was given
    data.id = data.id || data.file.split("/").pop().split(".")[0];
    return data;
  }

  // add a chapter's GeoJSON data (polygons + points, once per layer).
  // `visible` is false when preloading, so the layer is added out of sight.
  function loaddata(chapter, visible = true) {
    const data = dataConfig(chapter);
    if (!data) return;

    const sourceId = data.sourceId || `${data.id}-source`;
    const fillId = `${data.id}-fill`;
    const pointId = `${data.id}-point`;
    const layout = { visibility: visible ? "visible" : "none" };

    // wait for the style if it isn't ready yet, then retry
    if (!map.isStyleLoaded()) {
      map.once("idle", () => loaddata(chapter, visible));
      return;
    }

    // if already added, just set both layers to the visibility asked for
    if (map.getLayer(fillId) || map.getLayer(pointId)) {
      [fillId, pointId].forEach((id) => {
        if (map.getLayer(id)) {
          map.setLayoutProperty(id, "visibility", layout.visibility);
        }
      });
      return;
    }

    // add the GeoJSON source, reading from the file/URL in the config
    if (!map.getSource(sourceId)) {
      map.addSource(sourceId, {
        type: "geojson",
        data: data.file,
      });
    }

    // polygon layer (only renders Polygon/MultiPolygon features)
    map.addLayer({
      id: fillId,
      type: "fill",
      source: sourceId,
      layout: layout,
      filter: ["match", ["geometry-type"], ["Polygon", "MultiPolygon"], true, false],
      paint: data.fillPaint || {
        "fill-color": "#1d6ad6",
        "fill-opacity": 0.25,
        "fill-outline-color": "#1d6ad6",
      },
    });

    // point layer (only renders Point/MultiPoint features)
    map.addLayer({
      id: pointId,
      type: "circle",
      source: sourceId,
      layout: layout,
      filter: ["match", ["geometry-type"], ["Point", "MultiPoint"], true, false],
      paint: data.circlePaint || {
        "circle-radius": 5,
        "circle-color": "#e63946",
        "circle-stroke-width": 1,
        "circle-stroke-color": "#ffffff",
      },
    });
  }


  function preloadData() {
    if (!map.isStyleLoaded()) {
      map.once("idle", preloadData);
      return;
    }
    steps.forEach((step) => {
      const data = dataConfig(step);
      // a step already scrolled into view keeps the layers it just showed
      if (!data || map.getLayer(`${data.id}-fill`)) return;
      loaddata(step, false);
    });
  }

  map.on("load", preloadData);

  // hide a chapter's GeoJSON layers when leaving the chapter
  function hidedata(chapter) {
    const data = dataConfig(chapter);
    if (!data) return;
    [`${data.id}-fill`, `${data.id}-point`].forEach((id) => {
      if (map.getLayer(id)) {
        map.setLayoutProperty(id, "visibility", "none");
      }
    });
  }

  // instantiate the scrollama
  var scroller = scrollama();

  // set up scrolling actions
  scroller
    .setup({
      step: ".section",
      offset: 0.8,
      progress: true,
    })
    .onStepEnter((response) => {
      response.element.classList.add("active");
      animateCounters(response.element);
      const chapter = steps[response.index];
      if (chapter && chapter.location) {
        map.flyTo(chapter.location);
      }
      if (chapter && chapter.threed) {
        load3dBuildings();
      }
      if (chapter && chapter.wmslayer) {
        loadWmsLayer(chapter.wmslayer, `wms-${response.index}`);
      }
      loadLayer(chapter);
      loaddata(chapter);
    })
    .onStepExit((response) => {
      response.element.classList.remove("active");
      const chapter = steps[response.index];
      if (chapter && chapter.threed) {
        hide3dBuildings();
      }
      if (chapter && chapter.wmslayer) {
        hideWmsLayer(chapter.wmslayer, `wms-${response.index}`);
      }
      hideLayer(chapter);
      hidedata(chapter);
    });

  // keep scrollama's trigger points correct after a window resize
  window.addEventListener("resize", scroller.resize);
}
