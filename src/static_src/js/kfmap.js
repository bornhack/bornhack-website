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
//        center: [55.3, 9.9], // Set center location
        center: [55.38739, 9.94032], // Set center location
        zoom: 11, // Initial zoom level
        minzoom: 1,
        maxzoom: 13,
    })

    // Define ortophoto layer [WMTS:orto_foraar_wmts]
    var ortofotowmts = L.tileLayer('/maps/kfproxy/GeoDanmarkOrto/orto_foraar_wmts/1.0.0/WMTS?REQUEST=GetTile&VERSION=1.0.0&service=WMTS&Layer=orto_foraar_wmts&style=default&format=image/jpeg&TileMatrixSet=KortforsyningTilingDK&TileMatrix={zoom}&TileRow={y}&TileCol={x}', {
        minZoom: 1,
        maxZoom: 13,
        attribution: myAttributionText,
        crossOrigin: true,
        zoom: function () {
            var zoomlevel = map._animateToZoom ? map._animateToZoom : map.getZoom();
            return zoomlevel;
//            if (zoomlevel < 10)
//                return 'L0' + zoomlevel;
//            else
//                return 'L' + zoomlevel;
        }
    }).addTo(map);

    // skaermkort layer [WMS:topo_skaermkort]
    var toposkaermkortwmts = L.tileLayer.wms('/maps/kfproxy/Dkskaermkort/topo_skaermkort/1.0.0/wms', {
        version: '1.3.0',
        layers: 'dtk_skaermkort',
        format: 'image/png',
        attribution: myAttributionText
    });

    // hillshade tile layer [WMS:dhm]
    var dhmwmts = L.tileLayer.wms('/maps/kfproxy/DHMNedboer/dhm/1.0.0/wms', {
        version: '1.3.0',
        layers: 'dhm_terraen_skyggekort',
        format: 'image/png',
        attribution: myAttributionText
    });

    // Matrikelskel overlay [WMS:mat]
    var matrikel = L.tileLayer.wms('/maps/kfproxy/Matrikel/MatrikelGaeldendeOgForeloebigWMS/1.0.0/wms', {
        version: '1.3.0',
        transparent: true,
        layers: 'MatrikelSkel_Foreloebig,Centroide_Gaeldende',
        format: 'image/png',
        attribution: myAttributionText,
        minZoom: 9
    });

    // Hillshade overlay [WMS:dhm]
    var hillshade = L.tileLayer.wms('/maps/kfproxy/DHMNedboer/dhm/1.0.0/wms', {
        version: '1.3.0',
        transparent: true,
        layers: 'dhm_terraen_skyggekort',
        format: 'image/png',
        attribution: myAttributionText,
    });

    // hylkedam overlay
    var venuepolygons = [
        [[54, 7], [54, 16], [58, 16], [58, 7]], // full map
        [[55.39019, 9.93918],[55.39007, 9.93991], [55.39001, 9.94075], [55.39002, 9.94119], [55.38997, 9.94154], [55.38983, 9.94355], [55.38983, 9.94383], [55.38973, 9.94474], [55.38953, 9.94742], [55.38946, 9.94739], [55.38955, 9.94587], [55.38956, 9.94503], [55.38952, 9.94435], [55.38941, 9.94359], [55.38377, 9.94072], [55.38462, 9.93793], [55.3847, 9.93778], [55.38499, 9.93675]], // hylkedam hole
    ];
    var venue = L.polygon(venuepolygons, {color: 'red'}).addTo(map); // default enabled

    // Define layer groups for layer control
    var baseLayers = {
        "Ortophoto Map": ortofotowmts,
        "Regular Map": toposkaermkortwmts,
        "Hillshade Map": dhmwmts
    };

    var overlays = {
        "Venue Overlay": venue,
        "Cadastral Overlay": matrikel,
        "Hillshade Overlay": hillshade
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
        alert("Lat: " + lat + " Lng: " + lng + ' - GeoJSON: { "type": "Point", "coordinates": [ ' + lng + ', ' + lat + ' ] }');
        return false; // To disable default popup.
    });

    // fire our callback when ready
    map.whenReady(MapReadyCallback);
})();
