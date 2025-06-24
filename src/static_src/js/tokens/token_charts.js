const defaultOptions = {
  chart: {
    background: 'undefined',
    toolbar: {
      show: false,
    },
  },
  //colors: ['#198754', '#dc3545'],
  theme: {
    mode: 'dark',
  },
}

var totalPlayersOptions = {
  ...defaultOptions,
  chart: {
    ...defaultOptions.chart,
    type: 'pie'
  },
  series: [5, 45],
  labels: ['Players', 'Non-players'],
  legend: {
    show: true,
    position: 'bottom',
    horizontalAlign: 'left',
    formatter: function(seriesName, opts) {
        return [seriesName, " - ", opts.w.globals.series[opts.seriesIndex]]
    },
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
    formatter: function(seriesName, opts) {
        return [seriesName, " - ", opts.w.globals.series[opts.seriesIndex]]
    },
  },
};

const tokenActivityData = JSON.parse(
    document.getElementById('tokenActivityChart').textContent
);
var tokenActivityOptions = {
  ...defaultOptions,
  chart: {
    ...defaultOptions.chart,
    type: 'bar'
  },
  series: [{
    name: 'Tokens found',
    data: tokenActivityData.series,
  }],
  dataLabels: {
    enabled: false,
  },
  xaxis: {
    categories: tokenActivityData.labels,
    tickAmount: 12,
    tickPlacement: 'on',
  },
};

const tokenCategoryData = JSON.parse(
    document.getElementById('tokenCategoryChart').textContent
);
var tokenCategoryOptions = {
  ...defaultOptions,
  chart: {
    ...defaultOptions.chart,
    type: 'radar',
    height: '100%',
    width: '100%'
  },
  series: [{
        data: tokenCategoryData
  }],
  yaxis: {
    show: false,
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
  var tokenActivity = new ApexCharts(
    document.querySelector("#token_activity_chart"),
    tokenActivityOptions
  );
  tokenActivity.render();
  var tokenCategory = new ApexCharts(
    document.querySelector("#token_category_chart"),
    tokenCategoryOptions
  );
  tokenCategory.render();
});

