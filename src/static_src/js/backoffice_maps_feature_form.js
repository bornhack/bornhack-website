const mapData = JSON.parse(
  document.getElementById('mapData').textContent
);
var mapObject = undefined;
window.addEventListener("map:init", function (event) {
  var map = event.detail.map;
  mapObject = new BHMap(map);
  mapObject.loadLayer(mapData.grid, "Grid squares", {
    onEachFeature: mapObject.onEachGrid,
    style: {
      color: "gray",
      fillOpacity: 0.0,
      weight: 0.5
    },
  });
});

