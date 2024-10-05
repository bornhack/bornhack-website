const frontendData = JSON.parse(
  document.getElementById('mapData').textContent
);
const loggedIn = frontendData['loggedIn']
const mapObject = new BHMap("map");
mapObject.setDefaultView();
mapObject.map.addControl(new L.Control.Fullscreen({
  pseudoFullscreen: true,
}));
mapObject.loadLayer(frontendData['grid'], "Grid squares", {
  onEachFeature: mapObject.onEachGrid,
  style: {
    color: "gray",
    fillOpacity: 0.0,
    weight: 0.5
  },
}, false, () => { mapObject.loadLayer(frontendData['url'], frontendData['name'], facilityOptions) });
