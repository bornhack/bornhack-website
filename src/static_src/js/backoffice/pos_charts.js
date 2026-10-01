document.addEventListener('DOMContentLoaded', function () {
  // get widget data
  const widgets = JSON.parse(document.getElementById('widgets').textContent);
  // light mode or dark mode?
  const theme = document.body.getAttribute('data-bs-theme');

  // reusable default options
  const defaultOptions = {
    chart: {
      background: 'undefined',
    },
    theme: {
      mode: theme === 'light' ? 'light' : 'dark',
      palette: 'palette2',
    },
    plotOptions: {
      pie: {
        dataLabels: {
          external: {
            show: true,
          },
        },
      },
      bar: {
        horizontal: false,
        dataLabels: {
          total: {
            enabled: true,
            formatter: function (val, opts) {
              return val + ' ' + widgets.unit;
            },
            offsetY: -7,
          },
        },
      },
    },
  };

  // the BornHack palette minus white
  const colors = [
    "#FFAFC7",
    "#73D7EE",
    "#613915",
    "#000000",
    "#E40303",
    "#FF8C00",
    "#FFED00",
    "#008026",
    "#750787",
    "#004DFF",
  ];

  var pies = [];
  if (widgets.pies) {
    // pie charts
    for (piechart of widgets.pies) {
      var pieOptions = {
        chart: {
          type: 'pie',
          animations: {
            enabled: false,
          },
        },
        series: piechart.chart.series,
        labels: piechart.chart.labels,
        tooltip: {
          enabled: false,
          theme: widgets.options.light_text ? 'dark' : 'light',
        },
        title: {
          text: piechart.title,
          align: 'center',
        },
        colors: colors,
        legend: {
          position: 'top',
        },
      };
      var pieChart = new ApexCharts(
        document.querySelector(piechart.selector),
        pieOptions
      );
      pieChart.render();
      pies.push(pieChart);
    };
  };


  // column charts
  var columns = [];
  if (widgets.columns) {
    for (colchart of widgets.columns) {
      var columnOptions = {
        ...defaultOptions,
        chart: {
          ...defaultOptions.chart,
          type: 'bar',
          stacked: true
        },
        series: colchart.chart.series,
        tooltip: {
          enabled: true,
          theme:  widgets.options.light_text ? 'dark' : 'light',
        },
        xaxis: {
          categories: colchart.chart.labels,
        },
        dataLabels: {
          enabled: true,
          style: {
            colors: ['#000'],
            fontWeight: 600,
          },
          formatter: function (val, opts) {
            // only show datalabel if value is more than 5% of the
            // largest total
            var ymax = Math.max(...opts.w.seriesData.stackedSeriesTotals);
            if (((val / ymax) * 100) > 5) {
              return opts.w.seriesData.seriesNames[opts.seriesIndex];
            } else {
              return '';
            };
          },
          background: {
            enabled: true,
            foreColor: '#fff',
            borderRadius: 2,
            padding: 4,
            opacity: 0.5,
            borderWidth: 0,
            borderColor: '#fff',
          },
        },
        title: {
          text: colchart.title,
          align: 'center',
        },
        colors: colors,
        legend: {
          position: 'top',
        },
        tooltip: {
          y: {
            formatter: function (value) {
              return value + ' ' + widgets.unit;
            },
          },
        },
        yaxis: {
          labels: {
            formatter: function (val) {
              return val + ' ' + widgets.unit;
            },
          },
        },
      };
      var columnChart = new ApexCharts(
        document.querySelector(colchart.selector),
        columnOptions
      );
      columnChart.render();
      columnChart.addEventListener('dataPointSelection', function (event, chartContext, config) {
        const dataObject = config.w.config.series[config.seriesIndex];
        console.log(dataObject);
        //console.log(event, chartContext, config);
        if (dataObject && dataObject.urls) {
          console.log(config);
          window.location.href=dataObject.urls[config.dataPointIndex];
        }
      })
    };
  };

  // treemap charts
  var treemaps = [];
  if (widgets.treemaps) {
    for (treechart of widgets.treemaps) {
      var treemapOptions = {
        ...defaultOptions,
        chart: {
          type: 'treemap',
        },
        series: treechart.chart.series,
        labels: treechart.chart.labels,
        tooltip: {
          enabled: true,
          theme: widgets.options.light_text ? 'dark' : 'light',
        },
        dataLabels: {
          enabled: true,
        },
        title: {
          text: treechart.title,
          align: 'center',
        },
        colors: colors,
        legend: {
          position: 'top',
        },
        tooltip: {
          y: {
            formatter: function (value) {
              return value + ' ' + widgets.unit;
            },
          },
        },
      };
      var treemap = new ApexCharts(
        document.querySelector(treechart.selector),
        treemapOptions
      );
      treemap.render();
      treemap.addEventListener('dataPointSelection', function (event, chartContext, config) {
        const dataObject = config.w.config.series[config.seriesIndex].data[config.dataPointIndex];
        if (dataObject && dataObject.url) {
          window.location.href=dataObject.url;
        }
      })
    };
  };
});
