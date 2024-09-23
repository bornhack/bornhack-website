const mapData = JSON.parse(
  document.getElementById('mapData').textContent
);
const loggedIn = mapData.loggedIn;
const mapObject = new BHMap("map");
mapObject.loadLayer(mapData.grid, "Grid squares", {
  onEachFeature: mapObject.onEachGrid,
  style: {
    color: "gray",
    fillOpacity: 0.0,
    weight: 0.5
  },
}, true, function(_json) {
  const layer = mapObject.findGridLoc(mapData.facility.location.y, mapData.facility.location.x);
  console.log(mapObject.cols[layer.feature.properties.col_index - 2] + (layer.feature.properties.row_index - 1));
  document.getElementById('gridLocator').innerHTML = mapObject.cols[layer.feature.properties.col_index - 2] + (layer.feature.properties.row_index - 1);
});

var marker = L.marker([mapData.facility.location.y, mapData.facility.location.x], {icon: L.AwesomeMarkers.icon({
  icon: mapData.facility.facility_type.icon,
  markerColor: mapData.facility.facility_type.marker.replace('Icon',''),
  prefix: 'fa',
})});
marker.bindPopup(`<b>${mapData.facility.name}</b><br><p>${mapData.facility.description}</p>`).addTo(mapObject.map);
// max zoom since we have only one marker
mapObject.map.setView(marker.getLatLng(), 20);
