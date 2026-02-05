document.addEventListener('DOMContentLoaded', function () {
  const widgets = JSON.parse(document.getElementById('widgets').textContent);
  const theme = document.body.getAttribute('data-bs-theme');

  const defaultOptions = {
    chart: {
      background: 'undefined',
      toolbar: {
        show: false,
      },
    },
    theme: {
      mode: theme === 'light' ? 'light' : 'dark',
      monochrome: {
        enabled: true,
        shadeTo: widgets.options.light_text ? 'light' : 'dark',
        color: theme === 'light' && widgets.options.camp_colour === '#ffffff'
                ? '#f0f0f0' : widgets.options.camp_colour,
      },
    },
  }

  var totalPlayersOptions = {
    ...defaultOptions,
    chart: {
      ...defaultOptions.chart,
      type: 'pie'
    },
    series: widgets.total_players.chart.series,
    labels: widgets.total_players.chart.labels,
    legend: {
      show: true,
      position: 'bottom',
      horizontalAlign: 'left',
      formatter: function(seriesName, opts) {
          return [seriesName, '(' + opts.w.globals.series[opts.seriesIndex] + ')']
      },
    },
    tooltip: {
      enabled: true,
      theme:  widgets.options.light_text ? 'dark' : 'light',
    }
  };

  var totalFindsOptions = {
    ...defaultOptions,
    chart: {
      ...defaultOptions.chart,
      type: 'pie'
    },
    series: widgets.total_finds.chart.series,
    labels: widgets.total_finds.chart.labels,
    legend: {
      show: true,
      position: 'bottom',
      horizontalAlign: 'left',
      formatter: function(seriesName, opts) {
          return [seriesName, '(' + opts.w.globals.series[opts.seriesIndex] + ')']
      },
    },
    tooltip: {
      enabled: true,
      theme:  widgets.options.light_text ? 'dark' : 'light',
    }
  };

  var tokenCategoryOptions = {
    ...defaultOptions,
    chart: {
      ...defaultOptions.chart,
      type: 'radar',
      height: '100%',
    },
    series: [
      {
        name: 'Found',
        data: widgets.token_categories.chart.series
      }
    ],
    labels: widgets.token_categories.chart.labels,
    tooltip: {
      y: {
        formatter: function (value) {
          return value + '%';
        },
      },
    },
    yaxis: {
      show: false,
    },
  };

  var tokenActivityOptions = {
    ...defaultOptions,
    chart: {
      ...defaultOptions.chart,
      type: 'bar'
    },
    series: [{
      name: 'Tokens found',
      data: widgets.token_activity.chart.series,
    }],
    dataLabels: {
      enabled: false,
    },
    xaxis: {
      categories: widgets.token_activity.chart.labels,
      tickAmount: 12,
      tickPlacement: 'on',
    },
  };

  var totalPlayers = new ApexCharts(
    document.querySelector('#total_players_chart'),
    totalPlayersOptions
  );
  totalPlayers.render();

  var totalFinds = new ApexCharts(
    document.querySelector('#total_finds_chart'),
    totalFindsOptions
  );
  totalFinds.render();

  var tokenCategory = new ApexCharts(
    document.querySelector('#token_category_chart'),
    tokenCategoryOptions
  );
  tokenCategory.render();

  var tokenActivity = new ApexCharts(
    document.querySelector('#token_activity_chart'),
    tokenActivityOptions
  );
  tokenActivity.render();

});
