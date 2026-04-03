// Frontend logic for the statics page. This file is responsible for fetching and displaying statistical data on the frontend.

let chart;

function updateUI(hunger) {
    document.getElementById("fill").style.width = hunger + "%";
    document.getElementById("hungerText").innerText = hunger + "/100";
}

function fetchHunger() {
    fetch("/api/hunger")
        .then(res => res.json())
        .then(data => updateUI(data.hunger));
}

function eat() {
    fetch("/api/eat", { method: "POST" })
        .then(res => res.json())
        .then(data => {
            updateUI(data.hunger);
            loadChart();
        });
}

function loadChart() {
    fetch("/api/history")
        .then(res => res.json())
        .then(data => {
            const labels = data.map(d => d.time);
            const values = data.map(d => d.hunger);

            if (chart) chart.destroy();

            const ctx = document.getElementById("chart").getContext("2d");
            chart = new Chart(ctx, {
                type: "line",
                data: {
                    labels: labels,
                    datasets: [{
                        label: "Hunger Over Time",
                        data: values,
                        borderColor: 'blue',
                        backgroundColor: 'lightblue',
                        fill: true
                    }]
                },
                options: {
                    scales: { y: { beginAtZero: true, max: 100 } }
                }
            });
        });
}

setInterval(fetchHunger, 5000);
fetchHunger();
loadChart();