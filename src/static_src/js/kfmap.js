(function() {

    //  Workaround for 1px lines appearing in some browsers due to fractional transforms
    //  and resulting anti-aliasing.
    //  https://github.com/Leaflet/Leaflet/issues/3575
    if (window.navigator.userAgent.indexOf('Chrome') > -1) {
        var originalInitTile = L.GridLayer.prototype._initTile;
        L.GridLayer.include({
            _initTile: function (tile) {
                originalInitTile.call(this, tile);
                var tileSize = this.getTileSize();
                tile.style.width = tileSize.x + 1 + 'px';
                tile.style.height = tileSize.y + 1 + 'px';
            }
        });
    }

    var myAttributionText = '&copy; <a target="_blank" href="https://download.kortforsyningen.dk/content/vilk%C3%A5r-og-betingelser">Styrelsen for Dataforsyning og Effektivisering</a>';

    // we need a custom crs for the map
    var crs = new L.Proj.CRS('EPSG:25832', '+proj=utm +zone=32 +ellps=GRS80 +units=m +no_defs', {
        resolutions: [1638.4,819.2,409.6,204.8,102.4,51.2,25.6,12.8,6.4,3.2,1.6,0.8,0.4,0.2],
        origin: [120000,6500000],
        bounds: L.bounds([120000, 5661139.2],[1378291.2, 6500000])
    });

    // Make the map object using the custom projection
    var map = new L.Map('map', {
        crs: crs,
        center: [55.3, 9.9], // Set center location
        zoom: 9, // Initial zoom level
        minzoom: 0,
        maxzoom: 13,
    })

    // Define ortophoto layer [WMTS:orto_foraar]
    var ortofotowmts = L.tileLayer('/maps/kfproxy/orto_foraar?request=GetTile&version=1.0.0&service=WMTS&Layer=orto_foraar&style=default&format=image/jpeg&TileMatrixSet=View1&TileMatrix={zoom}&TileRow={y}&TileCol={x}', {
        minZoom: 0,
        maxZoom: 13,
        attribution: myAttributionText,
        crossOrigin: true,
        zoom: function () {
            var zoomlevel = map._animateToZoom ? map._animateToZoom : map.getZoom();
            if (zoomlevel < 10)
                return 'L0' + zoomlevel;
            else
                return 'L' + zoomlevel;
        }
    }).addTo(map);

    // skaermkort layer [WMTS:topo_skaermkort]
    var toposkaermkortwmts = L.tileLayer.wms('/maps/kfproxy/topo_skaermkort', {
        layers: 'dtk_skaermkort',
        format: 'image/png',
        attribution: myAttributionText
    });

    // hillshade tile layer [WMTS:dhm]
    var dhmwmts = L.tileLayer.wms('/maps/kfproxy/dhm', {
        layers: 'dhm_terraen_skyggekort_overdrevet',
        format: 'image/png',
        attribution: myAttributionText
    });

    // Matrikelskel overlay [WMS:mat]
    var matrikel = L.tileLayer.wms('/maps/kfproxy/mat', {
        transparent: true,
        layers: 'MatrikelSkel,Centroide',
        format: 'image/png',
        attribution: myAttributionText,
        minZoom: 9
    }).addTo(map); // addTo means that the layer is visible by default

    // Hillshade overlay [WMS:dhm]
    var hillshade = L.tileLayer.wms('/maps/kfproxy/dhm', {
        transparent: true,
        layers: 'dhm_terraen_skyggekort_transparent_overdrevet',
        format: 'image/png',
        attribution: myAttributionText,
    });

    // Define layer groups for layer control
    var baseLayers = {
        "Ortophoto Map": ortofotowmts,
        "Regular Map": toposkaermkortwmts,
        "Hillshade Map": dhmwmts
    };
    var overlays = {
        "Cadastral Map Overlay": matrikel,
        "Hillshade Map Overlay": hillshade
    };

    // Add layer control to map
    L.control.layers(baseLayers, overlays).addTo(map);

    // Add scale line to map, disable imperial units
    L.control.scale({imperial: false}).addTo(map);


    var Position = L.Control.extend({ 
        _container: null,
        options: {
          position: 'bottomright'
        },

        onAdd: function (map) {
          var latlng = L.DomUtil.create('div', 'mouseposition');
          latlng.style = 'background: rgba(255, 255, 255, 0.7);';
          this._latlng = latlng;
          return latlng;
        },

        updateHTML: function(lat, lng) {
          this._latlng.innerHTML = "&nbsp;Lat: " + lat + " Lng: " + lng + "<br>&nbsp;Right click to copy coordinates&nbsp;";
        }
    });
    position = new Position();
    map.addControl(position);
    var lat;
    var lng;
    map.addEventListener('mousemove', (event) => {
        lat = Math.round(event.latlng.lat * 100000) / 100000;
        lng = Math.round(event.latlng.lng * 100000) / 100000;
        this.position.updateHTML(lat, lng);
    });

    map.addEventListener("contextmenu", (event) => {
        alert("Lat: " + lat + " Lng: " + lng + '\n\nGeoJSON:\n{ "type": "Point", "coordinates": [ ' + lng + ', ' + lat + ' ] }');
        return false; // To disable default popup.
    });

    // fire our callback when ready
    map.whenReady(MapReadyCallback);
})();
