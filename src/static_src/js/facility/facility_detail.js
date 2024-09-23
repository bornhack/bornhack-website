const mapData = JSON.parse(
  document.getElementById('mapData').textContent
);
const loggedIn = mapData['loggedIn']
const mapObject = new BHMap("map");

mapObject.setDefaultView();
mapObject.loadLayer(mapData['grid'], "Grid squares", {
  onEachFeature: mapObject.onEachGrid,
  style: {
    color: "gray",
    fillOpacity: 0.0,
    weight: 0.5
  },
}, false);


var marker = L.marker([mapData.y, mapData.x], {icon: L.AwesomeMarkers.icon({
  icon: mapData.icon.replace('fas fa-',''),
  markerColor: mapData.marker.replace('Icon',''),
  prefix: 'fa',
})});
let feedback = "";
if (mapData.loggedIn) {
  feedback=`<p><a href='${mapData.feedbackUrl}' class='btn btn-primary' style='color: white;'><i class='fas fa-comment-dots'></i> Feedback</a></p>`;
}
marker.bindPopup(`<b>${mapData.name}</b><br><p>${mapData.description}</p><p>Responsible team: ${mapData.team} Team</p>${feedback}`).addTo(mapObject.map);
// max zoom since we have only one marker
mapObject.map.setView(marker.getLatLng(), 20);
