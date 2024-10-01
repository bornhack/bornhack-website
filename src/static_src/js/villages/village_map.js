const mapData = JSON.parse(
  document.getElementById('mapData').textContent
);
const loggedIn = mapData.loggedIn;
const mapObject = new BHMap("map");
mapObject.setDefaultView();
mapObject.map.addControl(new L.Control.Fullscreen({
  pseudoFullscreen: true,
}));
mapObject.loadLayer(mapData.grid, "Grid squares", {
  onEachFeature: mapObject.onEachGrid,
  style: {
    color: "gray",
    fillOpacity: 0.0,
    weight: 0.5
  },
}, false, gridLoaded());
mapObject.onGridClick = function (e) {
  e.target.setStyle({fillOpacity: 1.0});
  let center = e.target.getCenter();
  if (mapObject.cols[e.target.feature.properties.col_index - 2] && (e.target.feature.properties.row_index   - 1))
    alert(mapObject.cols[e.target.feature.properties.col_index - 2] + (e.target.feature.properties.row_index - 1) + " " + center.lat + "," + center.lng);
}
function gridLoaded() {
  mapObject.loadLayer(mapData.url, "Villages", villageOptions, true);
}
