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
}, false);

mapData['facility_list'].forEach(function (facility) {
  let authContent = "";
  if (mapData.loggedIn)
    authContent = `<p><a href='${facility.url}' class='btn btn-primary' style='color: white;'><i class='fas fa-search'></i> Details</a></p>`;
  L.marker([
    facility.location.y,
    facility.location.x
  ], {
    icon: L.AwesomeMarkers.icon({
      icon: facility.facility_type.icon,
      markerColor: iconColors[facility.facility_type.marker],
      prefix: 'fa',
    })
  }).bindPopup(`<b>${facility.name}</b><br><p>${facility.description}</p><p>Responsible team: ${facility.facility_type.team} Team</p>${authContent}`).addTo(mapObject.map);
});
