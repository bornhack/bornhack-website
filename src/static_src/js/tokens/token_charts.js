const defaultOptions = {
  chart: {
    background: 'undefined'
  },
  colors: ['#198754', '#dc3545'],
  theme: {
    mode: 'dark',
  },
}

const totalPlayersOptions = {
  ...defaultOptions,
  chart: {
    ...defaultOptions.chart,
    type: 'pie'
  },
  series: [
    5, 45,
  ],
  labels: [
    'Players',
    'Non-players',
  ],
  legend: {
    show: true,
    position: 'bottom',
    horizontalAlign: 'left',
  },
};

const tokensFoundData = JSON.parse(
  document.getElementById('tokensFoundChart').textContent
);
var tokensFoundOptions = {
  ...defaultOptions,
  chart: {
    ...defaultOptions.chart,
    type: 'pie'
  },
  series: tokensFoundData.series,
  labels: tokensFoundData.labels,
  legend: {
    show: true,
    position: 'bottom',
    horizontalAlign: 'left',
  },
};

$(document).ready(function () {
  var totalPlayers = new ApexCharts(
    document.querySelector("#total_players_chart"),
    totalPlayersOptions
  );
  totalPlayers.render();
  var tokensFound = new ApexCharts(
    document.querySelector("#tokens_found_chart"),
    tokensFoundOptions
  );
  tokensFound.render();
});

