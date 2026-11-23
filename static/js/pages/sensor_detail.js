(function () {
    "use strict";

    if (typeof ApexCharts === "undefined") return;

    document.addEventListener("DOMContentLoaded", function () {
        const chartEl = document.getElementById("sensorHistoricalChart");
        const emptyEl = document.getElementById("sensorChartEmpty");
        if (!chartEl) return;

        const endpoint = chartEl.dataset.endpoint;
        const unit = chartEl.dataset.unit || "";
        const sensorName = chartEl.dataset.sensorName || "Sensor reading";
        const rangeButtons = document.querySelectorAll(".sensor-chart-range-btn");

        let chart = null;
        let activeHours = 24;

        function getThemeConfig() {
            const isDark =
                document.body.classList.contains("theme-dark") ||
                document.body.classList.contains("dark") ||
                localStorage.getItem("theme") === "theme-dark";
            return {
                mode: isDark ? "dark" : "light",
                labelColor: isDark ? "#CBD5E1" : "#64748B",
                gridColor: isDark ? "#2D2D44" : "#E2E8F0",
            };
        }

        function xLabelFormat(hours) {
            if (hours <= 24) return "HH:mm";
            if (hours <= 48) return "DD MMM HH:mm";
            return "DD MMM";
        }

        function buildOptions(data, hours) {
            const config = getThemeConfig();
            return {
                series: [
                    {
                        name: sensorName,
                        data: data.map(function (d) {
                            return { x: new Date(d.timestamp).getTime(), y: d.value };
                        }),
                    },
                ],
                chart: {
                    type: "area",
                    height: 320,
                    background: "transparent",
                    foreColor: config.labelColor,
                    fontFamily: "inherit",
                    toolbar: { show: false },
                    zoom: { type: "x", enabled: true, autoScaleYaxis: true },
                    animations: { speed: 500 },
                },
                colors: ["#4F46E5"],
                fill: {
                    type: "gradient",
                    gradient: {
                        shade: "light",
                        shadeIntensity: 1,
                        opacityFrom: 0.35,
                        opacityTo: 0.05,
                        gradientToColors: ["#0EA5E9"],
                        stops: [0, 90, 100],
                    },
                },
                stroke: { curve: "smooth", width: 2.5 },
                dataLabels: { enabled: false },
                grid: {
                    borderColor: config.gridColor,
                    strokeDashArray: 4,
                    padding: { left: 10, right: 10 },
                },
                xaxis: {
                    type: "datetime",
                    labels: {
                        format: xLabelFormat(hours),
                        style: { colors: config.labelColor, fontSize: "12px" },
                    },
                    axisBorder: { show: false },
                    axisTicks: { show: false },
                },
                yaxis: {
                    labels: { style: { colors: config.labelColor, fontSize: "12px" } },
                    title: {
                        text: unit,
                        style: { color: config.labelColor, fontWeight: 600 },
                    },
                },
                tooltip: {
                    theme: config.mode,
                    x: { format: "DD MMM HH:mm" },
                    y: {
                        formatter: function (val) {
                            return val + " " + unit;
                        },
                    },
                },
                legend: { show: false },
            };
        }

        function applyTheme() {
            if (!chart) return;
            const config = getThemeConfig();
            chart.updateOptions({
                theme: { mode: config.mode },
                chart: { foreColor: config.labelColor },
                grid: { borderColor: config.gridColor },
                xaxis: { labels: { style: { colors: config.labelColor } } },
                yaxis: {
                    labels: { style: { colors: config.labelColor } },
                    title: { style: { color: config.labelColor } },
                },
                tooltip: { theme: config.mode },
            });
        }

        function showEmptyState() {
            // Keep chart visible with empty series rather than hiding it
            emptyEl.hidden = true;
            chartEl.hidden = false;
            if (chart) {
                chart.updateSeries([{ name: sensorName, data: [] }]);
                return;
            }
            chart = new ApexCharts(chartEl, buildOptions([], activeHours));
            chart.render();
        }

        function renderChart(data, hours) {
            emptyEl.hidden = true;
            chartEl.hidden = false;
            if (chart) {
                chart.updateOptions(buildOptions(data, hours), true);
                chart.updateSeries([
                    {
                        name: sensorName,
                        data: data.map(function (d) {
                            return { x: new Date(d.timestamp).getTime(), y: d.value };
                        }),
                    },
                ]);
                applyTheme();
                return;
            }
            chart = new ApexCharts(chartEl, buildOptions(data, hours));
            chart.render();
        }

        function loadData(hours) {
            fetch(endpoint + "?hours=" + hours)
                .then(function (response) {
                    if (!response.ok) throw new Error("Request failed");
                    return response.json();
                })
                .then(function (payload) {
                    const data = payload && payload.data ? payload.data : [];
                    if (!data.length) {
                        showEmptyState();
                        return;
                    }
                    renderChart(data, hours);
                })
                .catch(showEmptyState);
        }

        rangeButtons.forEach(function (button) {
            button.addEventListener("click", function () {
                rangeButtons.forEach(function (btn) {
                    btn.classList.remove("active");
                });
                button.classList.add("active");
                activeHours = parseInt(button.dataset.hours, 10) || 24;
                loadData(activeHours);
            });
        });

        const observer = new MutationObserver(function (mutations) {
            mutations.forEach(function (mutation) {
                if (mutation.attributeName === "class") applyTheme();
            });
        });
        observer.observe(document.body, { attributes: true });

        loadData(activeHours);
    });
})();