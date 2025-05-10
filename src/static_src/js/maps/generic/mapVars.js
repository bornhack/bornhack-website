const iconColors = {
  blueIcon: 'blue',
  goldIcon: 'cadetblue',
  redIcon: 'red',
  greenIcon: 'green',
  orangeIcon: 'orange',
  yellowIcon: 'cadetblue',
  violetIcon: 'darkpurple',
  greyIcon: 'darkgreen',
  blackIcon: 'blue',
}

const iconColorsHex = {
  blueIcon: '#2A81CB',
  goldIcon: '#FFD326',
  redIcon: '#CB2B3E',
  greenIcon: '#2AAD27',
  orangeIcon: '#CB8427',
  yellowIcon: '#CAC428',
  violetIcon: '#9C2BCB',
  greyIcon: '#7B7B7B',
  blackIcon: '#3D3D3D',
}

const facilityOptions = {
  onEachFeature: function(feature, layer) {

    const gridLayer = mapObject.findGridLoc(feature.geometry.coordinates[1], feature.geometry.coordinates[0]);
    let grid = "";
    if (gridLayer !== undefined && gridLayer.feature)
      grid = `<p>Grid: ${mapObject.cols[gridLayer.feature.properties.col_index - 2]}${(gridLayer.feature.properties.row_index - 1)}</p>`;
    let icon = `<i style="color: ${feature.properties.color}" class="${feature.properties.icon } fa-fw"></i>`;
    const content = `<b>${feature.properties.name}${icon}</b><br><p>${feature.properties.description}</p><p>Responsible team: ${feature.properties.team} Team</p>${grid}`
    const authContent = `<p><a href='${feature.properties.detail_url}' class='btn btn-primary' style='color: white;'><i class='fas fa-search'></i> Details</a><a href='${feature.properties.feedback_url}' class='btn btn-primary' style='color: white;'><i class='fas fa-comment-dots'></i> Feedback</a></p>`
    if (loggedIn)
      layer.bindPopup(content + authContent, { maxHeight: 400});
    else
      layer.bindPopup(content, { maxHeight: 400});
    layer.setIcon(L.AwesomeMarkers.icon({
      icon: feature.properties.icon,
      color: iconColorsHex[feature.properties.marker],
      markerColor: iconColors[feature.properties.marker],
      prefix: 'fa',
    }))
  }
}

const villageOptions = {
  onEachFeature: function(feature, layer) {
    const gridLayer = mapObject.findGridLoc(feature.geometry.coordinates[1],feature.geometry.coordinates[0]);
    let grid = "";
    if (gridLayer !== undefined && gridLayer.feature)
      grid = `<p>Grid: ${mapObject.cols[gridLayer.feature.properties.col_index - 2]}${(gridLayer.feature.properties.row_index - 1)}</p>`;
    const content = `<b>${feature.properties.name}</b><i class="fa fa-campground"></i><br><p>${feature.properties.description}</p>${grid}<p><a href='${feature.properties.detail_url}' class='btn btn-primary' style='color: white;'><i class='fas fa-search'></i> Village Details</a></p>`;
    layer.bindPopup(content, { maxHeight: 400});
    layer.setIcon(L.AwesomeMarkers.icon({
      icon: "fa fa-campground",
      markerColor: "green",
      color: iconColorsHex['greenIcon'],
      prefix: 'fa',
    }))
  }
}

const peopleOptions = {
  onEachFeature: function(feature, layer) {
    const gridLayer = mapObject.findGridLoc(feature.geometry.coordinates[1],feature.geometry.coordinates[0]);
    let grid = "";
    if (gridLayer !== undefined && gridLayer.feature)
      grid = `<p>Grid: ${mapObject.cols[gridLayer.feature.properties.col_index - 2]}${(gridLayer.feature.properties.row_index - 1)}</p>`;
    const content = `<b>${feature.properties.public_credit_name}</b><i class="fa fa-user"></i><br>${grid}`;
    layer.bindPopup(content, { maxHeight: 400});
    layer.setIcon(L.AwesomeMarkers.icon({
      icon: "fa fa-user",
      markerColor: "green",
      color: iconColorsHex['greenIcon'],
      prefix: 'fa',
    }))
  }
}

const genericLayerOptions = {
  onEachFeature: function(feature, layer) {
    const icon = `<i style="color: ${feature.properties.color}" class="${feature.properties.icon }"></i>`;
    const content = `<b>${feature.properties.name} ${icon}</b><br><p>${feature.properties.description}</p>`;
    layer.bindPopup(content, { maxHeight: 400});
  }
}

const popOptions = {
  onEachFeature: function(feature, layer) {
    const content = `${feature.properties['name']}`
    layer.bindPopup(content, { maxHeight: 400});
  }
}

const connectionOptions = {
  style: {
    opacity: 1,
    color: 'rgba(213,180,60,1.0)',
    dashArray: '',
    lineCap: 'square',
    lineJoin: 'bevel',
    weight: 8.0,
    fillOpacity: 0,
    interactive: true,
  },
  onEachFeature: function(feature, layer) {
    const content = `${feature.properties['name']}<br><b>From:</b> ${feature.properties['POP_A']}<br>To: ${feature.properties['POP_B']}`
    layer.bindPopup(content, { maxHeight: 400});
  }
}
