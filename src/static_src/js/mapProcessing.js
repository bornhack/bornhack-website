class MapProcessing {
  constructor() {
    console.log("Loaded Map Processing");
  }
  trafficlight(_topic, payload, layer){
    var icon = new L.Icon({
      iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-'+payload.value+'.png',
      shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
      iconSize: [25, 41],
      iconAnchor: [12, 41],
      popupAnchor: [1, -34],
      shadowSize: [41, 41]
    });
    if (layer.setIcon) {
      layer.setIcon(icon);
      layer.bindTooltip(payload.value);
      layer.openTooltip();
    }
  }
  noisesensor(_topic, payload, layer) {
    var hue = ((1 - payload.avg / 100) * 120).toString(10);
    var color = ["hsl(", hue, ",100%,50%)"].join("");
    if (layer.setStyle && layer.feature) {
      layer.setStyle({
        radius: Number(payload.avg),
        fillColor: color
      })
      layer.bindPopup(layer.feature.properties.name + ": " + payload.avg + " dB", {
        maxHeight: 400
      });
    }
  }
  golfcar(_topic, payload, layer) {
    if (layer.setLatLng)
      layer.setLatLng([payload.lat, payload.lng])
  }
}
