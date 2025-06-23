const mapData = JSON.parse(
  document.getElementById('mapData').textContent
);
const loggedIn = mapData['loggedIn']
var mapObject = undefined;
window.addEventListener("map:init", function (event) {
  var map = event.detail.map;
  mapObject = new BHMap(map);
  mapObject.map.addControl(new L.Control.Fullscreen({
    pseudoFullscreen: true,
  }));
  if (mapData.grid) {
    mapObject.loadLayer(mapData.grid, "Grid squares", {
      onEachFeature: mapObject.onEachGrid,
      style: {
        color: "gray",
        fillOpacity: 0.0,
        weight: 0.5
      },
    });
  }
  if (mapData.facilitytype_list) {
    mapData['facilitytype_list'].forEach(function (item) {
      mapObject.loadLayer(item.url, item.name, facilityOptions, true, function(){}, "Facilities", item.icon);
    })
  }
  if (mapData.layers) {
    mapData['layers'].forEach(function (item) {
      mapObject.loadLayer(item.url, item.name, {
      });
    });
  }
});


document.addEventListener("DOMContentLoaded", function(){
  /* Method run when location lookup was successfull */
  function location_place_success(pos) {
    const crd = pos.coords;
    const geomInput = document.getElementsByClassName('django-leaflet-raw-textarea')[0];
    if (geomInput) {
      geomInput.value = `{"type":"Point","coordinates":[${crd.longitude},${crd.latitude}]}`;
      document.querySelector("form").submit();
    } else {
      console.log("Could not find input field");
    }
  }

  /* Method run when location lookup failed */
  function location_error(err) {
    alert(`ERROR(${err.code}): ${err.message}`);
  }

  const location_options = {
    enableHighAccuracy: true,
    timeout: 3000,
    maximumAge: 0, //Always retrieve position dont use cached value
  };
  var use_location_button = document.getElementById("use_location"); 
  if (use_location_button) {
    use_location_button.addEventListener("click", function(event){
      navigator.geolocation.getCurrentPosition(location_place_success, location_error, location_options);
      event.preventDefault()
    });
  }
});
