// JavaScript for chart functionality and round selection

// NOTE: Carousel related functions (myslide, dot, autoSlide, plusSlides, currentSlide, resetTimer, slidefun, togglePause) have been removed as there will only be a single news event displayed per round.

let myCharts = [];
let currentStockIndex = 0;
let intervalID; // Declare a variable to store the interval ID
let isStop = false; // Variable to keep track of the pause state

// Function to create a chart (remains unchanged)
function createChart(ctx, labels, data, label, backgroundColor, borderColor) {
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: label,
                data: data,
                backgroundColor: backgroundColor,
                borderColor: borderColor,
                borderWidth: 4,
                pointRadius: 8,
                fill: false
            }]
        },

        options: {
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: '#E2E8F0'
                    }
                },
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: "Round",
                        color: '#E2E8F0'
                    },
                    ticks: {
                        color: '#E2E8F0',
                    }
                }
            },
            plugins: {
                legend: {
                    labels: {
                        color: '#E2E8F0',
                    }
                }
            },
            layout: {
                padding: {
                    left: 20,
                    right: 20,
                    top: 20,
                    bottom: 20
                }
            },
            responsive: true,
            maintainAspectRatio: false,
        }
    });
}

// Function to update charts (remains unchanged)
function updateCharts(round) {
    const stockData = {{ stock_data | tojson }};
    const labels = Array.from({ length: round }, (_, i) => i === 0 ? 'Initial' : `${i}`);
    const allStocks = Object.keys(stockData);

    document.querySelectorAll('.chart-container canvas').forEach((canvas, index) => {
        if (myCharts[index]) {
            myCharts[index].destroy();
        }
        const currentStock = allStocks[currentStockIndex];
        const data = stockData[currentStock].slice(0, round);

        myCharts[index] = createChart(canvas.getContext('2d'), labels, data, currentStock, '#' + Math.floor(Math.random()*16777215).toString(16), '#' + Math.floor(Math.random()*16777215).toString(16));

        currentStockIndex = (currentStockIndex + 1) % allStocks.length;
    });
}

// Function to change round (remains unchanged)
function changeRound() {
    const roundSelect = document.getElementById('round-select');
    const selectedRound = parseInt(roundSelect.value);
    clearInterval(intervalID);
    const ID = {{ ID }};
    window.location.href = `/round/${ID}/${selectedRound}`;
}

// Function to toggle pause (remains unchanged)
function toggleChartPause() {
    if (isStop) {
        intervalID = setInterval(() => {
            updateCharts(initialRound);
        }, 3000);
        document.querySelectorAll('.pause-chart-button').forEach(button => {
            button.textContent = "Pause";
        });
    } else {
        clearInterval(intervalID);
        document.querySelectorAll('.pause-chart-button').forEach(button => {
            button.textContent = "Play";
        });
    }
    isStop = !isStop;
}

// Call updateCharts initially on page load
const initialRound = {{ current_round }};
updateCharts(initialRound);

// Start the interval initially
intervalID = setInterval(() => {
    updateCharts(initialRound);
}, 3000);



