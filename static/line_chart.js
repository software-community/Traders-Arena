function initFunction(portfolio, cash, rankings, numberOfRounds) {
  var labels_list = [""];
  for (var i = 1; i <= numberOfRounds; i++) {
    labels_list.push(i.toString());
  }

  var maxPortfolioValue = 0;
  var maxCashValue = 0;

  // Finding the maximum value in the portfolio and cash datasets
  Object.keys(portfolio).forEach(function(teamName) {
    portfolio[teamName].forEach(function(value) {
      if (value > maxPortfolioValue) {
        maxPortfolioValue = value;
      }
    });

    cash[teamName].forEach(function(value) {
      if (value > maxCashValue) {
        maxCashValue = value;
      }
    });
  });

  // Adding a buffer for better visualization
  var maxYValue = parseInt(Math.max(maxPortfolioValue, maxCashValue) * 1.1);

  // Generating all the charts for teams before final results
  Object.keys(portfolio).forEach(function(teamName) {
    var canvas = document.createElement("canvas");
    canvas.className = "chart-canvas w-full h-full";
    document.getElementById("card " + teamName).appendChild(canvas);

    var chartConfig = {
      type: "line",
      data: {
        labels: labels_list,
        datasets: [
          {
            label: "Portfolio",
            data: portfolio[teamName],
            borderColor: "rgb(75, 192, 192)",
            tension: 0.1,
          },
          {
            label: "Cash",
            data: cash[teamName],
            borderColor: "rgba(56,143,237)",
            tension: 0.1,
          },
        ],
      },
      options: {
        responsive: true,
        animation: false,
        scales: {
          x: {
            display: true,
            title: {
              display: true,
              text: "Round",
            },
          },
          y: {
            display: true,
            title: {
              display: true,
              text: "Value",
            },
            min: 0,
            max: maxYValue,
          },
        },
      },
    };

    new Chart(canvas, chartConfig);
  });

  // Generating charts for top 3 teams for final result display
  Object.keys(rankings).forEach(function(teamName) {
    var canvas = document.createElement("canvas");
    canvas.className = "chart-canvas w-full h-full";
    document.getElementById("result " + teamName).innerHTML = "";
    document.getElementById("result " + teamName).appendChild(canvas);

    var chartConfig = {
      type: "line",
      data: {
        labels: labels_list,
        datasets: [
          {
            label: "Portfolio",
            data: rankings[teamName],
            borderColor: "rgb(75, 192, 192)",
            tension: 0.1,
          },
          {
            label: "Cash",
            data: cash[teamName],
            borderColor: "rgba(56,143,237)",
            tension: 0.1,
          },
        ],
      },
      options: {
        responsive: true,
        animation: false,
        scales: {
          x: {
            display: true,
            title: {
              display: true,
              text: "Round",
            },
          },
          y: {
            display: true,
            title: {
              display: true,
              text: "Value",
            },
            min: 0,
            max: maxYValue,
          },
        },
      },
    };

    new Chart(canvas, chartConfig);
  });
}
