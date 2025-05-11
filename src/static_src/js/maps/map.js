const mapData = JSON.parse(
  document.getElementById('mapData').textContent
);
const loggedIn = mapData['loggedIn']
const mapObject = new BHMap("map");
mapObject.setDefaultView();
mapObject.map.addControl(new L.Control.Fullscreen({
  pseudoFullscreen: true,
}));
mapObject.loadLayer(mapData['grid'], "Grid squares", {
  onEachFeature: mapObject.onEachGrid,
  style: {
    color: "gray",
    fillOpacity: 0.0,
    weight: 0.5
  },
}, false, gridLoaded(), "Generic", "fas fa-border-all");
function gridLoaded() {
  console.log("Loaded grid layer");
  mapData['facilitytype_list'].forEach(function (item) {
    mapObject.loadLayer(item.url, item.name, facilityOptions, true, function(){}, "Facilities", item.icon);
  })
  mapData['layers'].forEach(function (item) {
    mapObject.loadLayer(item.url, item.name, {
      onEachFeature: function(feature, layer) {
        let icon = `<i style="color: ${feature.properties.color}" class="${feature.properties.icon } fa-fw"></i>`;
        let content = `<b>${feature.properties.name}</b>${icon}<br><p>${feature.properties.description}</p>`;
        if (feature.properties.url)
          content += `<br><p><a href='${feature.properties.url}' class='btn btn-primary' style='color: white;'><i class='fas fa-search'></i> Details</a></p>`

        layer.bindPopup(content, { maxHeight: 400});
        if (feature.properties.color !== "#FFFFFFFF") {
          layer.setStyle({
            color: feature.properties.color
          })
        }
        if (layer.feature.geometry.type === 'GeometryCollection') {
          layer.eachLayer(function(l) {
            if(l._latlng && l.setIcon){
              l.setIcon(L.AwesomeMarkers.icon({
                icon: feature.properties.icon,
                color: feature.properties.color,
                markerColor: iconColors[feature.properties.marker],
                prefix: 'fa',
              }))
            }
          })
        }
      },
      pointToLayer: function(feature, latlng) {
        if (feature.properties.processing == "noisesensor")
          return new L.CircleMarker(latlng, {
            radius: 25,
            color: '#FF0000'
          });
        else
          return L.marker(latlng)
      },
      style: {
        color: "{{ layer.color }}"
      }
    }, !item.invisible, function(){}, item.group__name, item.icon);
  })
  mapData['externalLayers'].forEach(function (item) {
    mapObject.loadLayer(item.url, item.name, {}, false, function(){}, "External");
  })
  mapObject.loadLayer(mapData.villages, "Villages", villageOptions, true, function(){}, undefined, "fa fa-campground");

  mapData['user_location_types'].forEach(function (item) {
    mapObject.loadLayer(item.url, item.name, userLocationOptions, false, function(){}, "User Locations", item.icon);
  });
}
mapObject.onGridClick = function (e) {
  let center = e.target.getCenter();
  if (mapObject.cols[e.target.feature.properties.col_index - 2] && (e.target.feature.properties.row_index   - 1))
    alert(mapObject.cols[e.target.feature.properties.col_index - 2] + (e.target.feature.properties.row_index - 1) + " " + center.lat + "," + center.lng);
}
