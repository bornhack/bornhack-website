class BHMap {
  constructor(div) {
    this.onGridClick = function (_e) {}
    this.findGridName = this.findGridName.bind(this)
    this.findGridLoc = this.findGridLoc.bind(this)
    this.findGridLocEach = this.findGridLocEach.bind(this)
    this.findGridEach = this.findGridEach.bind(this)
    this.onEachGrid = this.onEachGrid.bind(this)
    this.onEachGridClick = this.onEachGridClick.bind(this)
    this.onEachMqttFeature = this.onEachMqttFeature.bind(this)
    this.onMqtt = this.onMqtt.bind(this)
    this.onMqttLayer = this.onMqttLayer.bind(this)
    this.onMqttLayerFeature = this.onMqttLayerFeature.bind(this)
    this.controls = undefined;
    this.baseLayers = {};
    this.layers = {};
    this.overlays = {};
    this.processing = undefined;
    this.cols = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', 'AA', 'AB', 'AC', 'AD', 'AE', 'AF', 'AG', 'AH', 'AI', 'AJ', 'AK', 'AL', 'AM', 'AN', 'AO', 'AP', 'AQ', 'AR', 'AS', 'AT', 'AU', 'AV', 'AW', 'AX', 'AY', 'AZ'];
    if (typeof div === 'string' || div instanceof String)
      this.map = L.map(div);
    else
      this.map = div;
    this.myAttributionText = '&copy; <a target="_blank" href="https://download.kortforsyningen.dk/content/vilk%C3%A5r-og-betingelser">Styrelsen for Dataforsyning og Effektivisering</a>';


    this.baseLayers['Ortophoto Map'] = L.tileLayer.wms('/maps/kfproxy/GeoDanmarkOrto/orto_foraar/1.0.0/WMS', {
      minZoom: 1,
      maxZoom: 20,
      maxNativeZoom: 17,
      attribution: this.myAttributionText,
      crossOrigin: true,
      layers: 'orto_foraar',
    }).addTo(this.map);

    this.baseLayers['Regular Map'] = L.tileLayer.wms('/maps/kfproxy/Dkskaermkort/topo_skaermkort/1.0.0/wms', {
      minZoom: 1,
      maxZoom: 20,
      maxNativeZoom: 17,
      version: '1.3.0',
      layers: 'dtk_skaermkort',
      format: 'image/png',
      attribution: this.myAttributionText
    });

    this.baseLayers['Hillshade Map'] = L.tileLayer.wms('/maps/kfproxy/DHMNedboer/dhm/1.0.0/wms', {
      minZoom: 1,
      maxZoom: 20,
      maxNativeZoom: 17,
      version: '1.3.0',
      layers: 'dhm_terraen_skyggekort',
      format: 'image/png',
      attribution: this.myAttributionText
    });

    this.baseLayers['OSS (external)'] = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 18,
    });

    this.baseLayers['Google Sat (external)'] = L.tileLayer('https://www.google.cn/maps/vt?lyrs=s@189&gl=cn&x={x}&y={y}&z={z}', {
      opacity: 1.0,
      minZoom: 1,
      maxZoom: 28,
      minNativeZoom: 0,
      maxNativeZoom: 18
    });

    var venuepolygons = [
      [[54, 7], [54, 16], [58, 16], [58, 7]], // full map
      [[55.39019, 9.93918],[55.39007, 9.93991], [55.39001, 9.94075], [55.39002, 9.94119], [55.38997, 9.94154], [55.38983, 9.94355], [55.38983, 9.94383], [55.38973, 9.94474], [55.38953, 9.94742], [55.38946, 9.94739], [55.38955, 9.94587], [55.38956, 9.94503], [55.38952, 9.94435], [  55.38941, 9.94359], [55.38377, 9.94072], [55.38462, 9.93793], [55.3847, 9.93778], [55.38499, 9.93675]], // hylkedam hole
    ];
    //this.overlays['Venue Overlay'] = L.polygon(venuepolygons, {color: 'red'}).addTo(this.map);
    if (L.Control.PanelLayers) {
      console.log("PanelLayers loaded");
      const baseLayers = Object.entries(this.baseLayers).map(([name, layer]) => ({
        name,
        layer
      }));
      const overLayers = Object.entries(this.overlays).map(([name, layer]) => ({
        name,
        layer,
      }));
      this.controls = new L.Control.PanelLayers(baseLayers, [
          {
            "group": "Generic",
            "layers": overLayers,
            "collapsed": true,
          },
          {
            "group": "External",
            "layers": [],
            "collapsed": true,
          },
          {
            "group": "User Locations",
            "layers": [],
            "collapsed": true,
          }
        ], {
        selectorGroup: true,
        collapsibleGroups: true,
        compact: true,
        //collapsed: true,
      });
      this.map.addControl(this.controls);
    } else {
      this.controls = L.control.layers(this.baseLayers, this.overlays).addTo(this.map);
    }
    if (typeof MapProcessing !== 'undefined') {
      this.processing = new MapProcessing();
    }
  }

  //Set the default view of the map
  setDefaultView() {
    this.map.setView([55.38723, 9.94080], 17);
  }

  //Load a layer and add it to overlay/map
  loadLayer(url, name, options, active=true, callback=function(){}, group=null, icon=undefined ) {
    this.loadShapefile(url).then(json => {
      if (active)
        this.layers[name] = L.geoJson(json, options).addTo(this.map);
      else
        this.layers[name] = L.geoJson(json, options);
      if (L.Control.PanelLayers) {
        this.controls.addOverlay({
          name: name,
          layer: this.layers[name],
          icon: (icon?`<i class="${icon}"></i>`:undefined),
        }, name, group)
      } else {
        this.controls.addOverlay(this.layers[name], name);
      }
      callback(json);
    });
  }

  async loadShapefile(url) {
    let shape_obj = await (await fetch(url)).json();
    return shape_obj
  }

  // Find the grid locator by lat lng
  findGridLoc(lat, lon) {
    const m1 = L.latLng([lat, lon]);
    if (this.layers['Grid squares'] && this.layers['Grid squares']._layers) {
      for (var i in this.layers['Grid squares']._layers) {
        if (this.findGridLocEach(this.layers['Grid squares']._layers[i], m1)) {
          return this.layers['Grid squares']._layers[i];
        }
      }
    }
  }

  findGridLocEach(e, m1) {
    if (e.getBounds().contains(m1)) {
      this.resetStyle();
      this.selectedLayer = e;
      return e;
    }
  }

  // Find the grid locator by name
  findGridName(fullgrid) {
    this.resetStyle();
    let regex = /^([A-Z]+)([0-9]+)/g;
    const reggrid = regex.exec(fullgrid);
    const col = this.cols.indexOf(reggrid[1]) + 2;
    const row = Number(reggrid[2]) + 1
    this.layers['Grid squares'].eachLayer(layer => this.findGridEach(layer, col, row));
    return this.selectedLayer;
  }

  findGridEach(layer, col, row) {
      if (Number(layer.feature.properties.col_index) == col && Number(layer.feature.properties.row_index) == row) {
        this.selectedLayer = layer;
        return layer;
      }
  }

  resetStyle() {
    if (this.selectedLayer) {
      this.selectedLayer.setStyle({fillOpacity: 0.0});
      this.selectedLayer = undefined;
    }
  }

  onEachGrid(_feature, layer) {
    layer.on('click', layer => this.onEachGridClick(layer));
  }

  onEachGridClick(e) {
    this.resetStyle();
    this.selectedLayer = e.target;
    this.onGridClick(e);
  }

  onEachMqttFeature(_feature, layer) {
    layer.on('click', function (e) {
      console.log(e);
    });
  }

  onMqtt(topic, payload) {
    if (this.processing !== undefined) {
      this.map.eachLayer(layer => this.onMqttLayer(topic, payload, layer));
    }
  }

  onMqttLayer(topic, payload, layer) {
    if (layer.feature && layer.feature.properties.topic && layer.feature.properties.topic === topic) {
      if (this.processing[layer.feature.properties.processing]) {
        if (layer.feature.geometry.type === 'GeometryCollection') {
          layer.eachLayer(feature => this.onMqttLayerFeature(topic, payload, layer, feature));
        }
        this.processing[layer.feature.properties.processing](topic, payload, layer);
      }
    }
  }

  onMqttLayerFeature(topic, payload, layer, feature) {
    this.processing[layer.feature.properties.processing](topic, payload, feature);
  }
}
