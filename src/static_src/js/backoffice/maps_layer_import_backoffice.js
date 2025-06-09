$(function() {
  document.getElementById("importURLFetch").onclick = function () {
    const url = document.getElementById('importURL').value;
    fetch(url)
      .then(r => r.text())
      .then(r => {
        document.getElementById('id_geojson_data').value = r;
      })
  };
  document.getElementById('selectFiles').onchange = function() {
    var files = document.getElementById('selectFiles').files;
    if (files.length <= 0) {
      return false;
    }
    var fr = new FileReader();
    fr.onload = function(e) {
      var result = {};
      try {
        result = JSON.parse(e.target.result);
      } catch(e) {
        alert(e);
      }
      var formatted = JSON.stringify(result);
      document.getElementById('id_geojson_data').value = formatted;
    }
    fr.readAsText(files.item(0));
  };
});
