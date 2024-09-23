const mapData = JSON.parse(
    document.getElementById('mapData').textContent
  );
const mapObject = new BHMap("map");
mapObject.setDefaultView();
const loggedIn = mapData.loggedIn;
mapObject.loadLayer(mapData.grid, "Grid squares", {
  onEachFeature: mapObject.onEachGrid,
  style: {
    color: "gray",
    fillOpacity: 0.0,
    weight: 0.5
  },
}, false);

var marker = L.marker([mapData.y, mapData.x], {
  icon: L.AwesomeMarkers.icon({
    icon: "fa fa-campground",
    markerColor: "green",
    prefix: 'fa',
  })
});
marker.addTo(mapObject.map);
mapObject.map.flyTo(marker.getLatLng(), 17);
