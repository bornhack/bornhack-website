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
}, false, gridLoaded());
function gridLoaded() {
  mapData['facilitytypeList'].forEach(function (feature, index) {
    mapObject.loadLayer(feature.url, feature.name, facilityOptions);
  })
}
