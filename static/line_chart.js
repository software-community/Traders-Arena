function initFunction(portfolio, cash, rankings, numberOfRounds) {
  var labels_list = [""];
  for (var i = 1; i <= numberOfRounds; i++) {
    labels_list.push(i.toString());
  }

  // Generating all the charts for teams before final results
  Object.keys(portfolio).forEach(function (teamName) {
    // Creating a canvas element
    var canvas = document.createElement("canvas");
    canvas.className = "chart-canvas w-full h-full";
    // Setting the class name to include the team name
    // Appending the canvas element to the div
    document.getElementById("card " + teamName).appendChild(canvas);

    // chart configuration for the current team
    var chartConfig = {
      type: "line",
      data: {
        labels: labels_list, // labels_list is defined aboce
        datasets: [
          {
            label: "Portfolio",
            data: portfolio[teamName], // using team name here
            borderColor: "rgb(75, 192, 192)",
            tension: 0.1,
          },
          {
            label: "Cash",
            data: cash[teamName], // using team name here
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
            min: 0, // minimum value for the y-axis scale
            max: 10000, // maximum value for the y-axis scale
          },
        },
      },
    };

    // Initializing a chart for the current canvas element with the chart configuration
    new Chart(canvas, chartConfig);
  });

  // Generating charts for top 3 teams for final result display
  Object.keys(rankings).forEach(function (teamName) {
    // Creating a canvas element
    var canvas = document.createElement("canvas");
    canvas.className = "chart-canvas w-full h-full";
    // Setttng the class name to include the team name
    // Appending the canvas element to the document body or any container element
    document.getElementById("result " + teamName).innerHTML = "";
    document.getElementById("result " + teamName).appendChild(canvas);

    // chart configuration for the current team
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
            min: 0, // minimum value for the y-axis scale
            max: 10000, // maximum value for the y-axis scale
          },
        },
      },
    };

    // Initializing a chart for the current canvas element with the chart configuration
    new Chart(canvas, chartConfig);
  });
}
