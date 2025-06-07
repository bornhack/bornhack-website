const mapData = JSON.parse(
  document.getElementById('mapData').textContent
);

var mapObject = undefined;
window.addEventListener("map:init", function (event) {
  var map = event.detail.map;
  mapObject = new BHMap(map);
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
});


document.addEventListener("DOMContentLoaded", function(){
  /* Method run when location lookup was successfull */
  function location_place_success(pos) {
    const crd = pos.coords;
    //alert(`Your current position is: ${crd.latitude}/${crd.longitude} More or less ${crd.accuracy} meters.`)
    console.log("Your current position is:");
    console.log(`Latitude : ${crd.latitude}`);
    console.log(`Longitude: ${crd.longitude}`);
    console.log(`More or less ${crd.accuracy} meters.`);
    const geomInput = document.getElementsByClassName('django-leaflet-raw-textarea')[0];
    if (geomInput) {
      geomInput.value = `{"type":"Point","coordinates":[${crd.longitude},${crd.latitude}]}`;
      document.querySelector("form").submit();
    } else {
      console.log("Could not find input field");
    }
  }
  function location_error(err) {
    alert(`ERROR(${err.code}): ${err.message}`);
  }
  const location_options = {
    enableHighAccuracy: true,
    timeout: 5000,
    maximumAge: 0,
  };
  var use_location_button = document.getElementById("use_location"); 
  if (use_location_button) {
    use_location_button.addEventListener("click", function(event){
      navigator.geolocation.getCurrentPosition(location_place_success, location_error, location_options);
      event.preventDefault()
    });
  }
});
