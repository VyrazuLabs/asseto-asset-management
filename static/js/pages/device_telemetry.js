(function () {
    "use strict";

    if (typeof ApexCharts === "undefined") return;

    document.addEventListener("DOMContentLoaded", function () {
        const root = document.getElementById("deviceTelemetry");
        if (!root) return;

        const deviceId = String(root.dataset.deviceId || "");
        const pairingStatusUrl = root.dataset.pairingStatusUrl || "";
        let started = false;

        const bodyEl = document.getElementById("deviceTelemetryBody");
        const pairingNoticeEl = document.getElementById("deviceTelemetryPairingNotice");
        const gaugesEl = document.getElementById("deviceTelemetryGauges");
        const emptyEl = document.getElementById("deviceTelemetryEmpty");
        const statusEl = document.getElementById("deviceTelemetryStatus");
        const updatedEl = document.getElementById("deviceTelemetryUpdated");

        const gauges = new Map();
        const ranges = new Map();
        const readings = new Map();

        function getTheme() {
            const isDark =
                document.body.classList.contains("theme-dark") ||
                document.body.classList.contains("dark") ||
                localStorage.getItem("theme") === "theme-dark";
            return {
                mode: isDark ? "dark" : "light",
                value: isDark ? "#FFFFFF" : "#1E293B",
                track: isDark ? "#2D2D44" : "#F1F5F9",
            };
        }

        function formatValue(value) {
            if (!Number.isFinite(value)) return "--";
            return String(Number(value.toFixed(2)));
        }

        function getRange(type, value) {
            let range = ranges.get(type);
            if (!range) {
                range = { min: Math.min(0, value), max: Math.max(100, value) };
                ranges.set(type, range);
            } else {
                range.min = Math.min(range.min, value);
                range.max = Math.max(range.max, value);
                if (range.max === range.min) range.max = range.min + 1;
            }
            return range;
        }

        function toPercent(type, value) {
            const range = getRange(type, value);
            return Math.max(0, Math.min(100, ((value - range.min) * 100) / (range.max - range.min)));
        }

        function gaugeOptions(type, value) {
            const config = getTheme();
            const percent = toPercent(type, value);
            return {
                series: [percent],
                chart: {
                    type: "radialBar",
                    height: 220,
                    background: "transparent",
                    fontFamily: "inherit",
                    toolbar: { show: false },
                },
                colors: ["#4F46E5"],
                fill: {
                    type: "gradient",
                    gradient: {
                        shade: "dark",
                        type: "horizontal",
                        shadeIntensity: 1,
                        gradientToColors: ["#0EA5E9"],
                        inverseColors: true,
                        opacityFrom: 1,
                        opacityTo: 1,
                        stops: [0, 100],
                    },
                },
                stroke: { lineCap: "round" },
                plotOptions: {
                    radialBar: {
                        startAngle: -90,
                        endAngle: 90,
                        hollow: { size: "68%" },
                        track: {
                            background: config.track,
                            strokeWidth: "97%",
                            margin: 5,
                            dropShadow: { enabled: false },
                        },
                        dataLabels: {
                            name: { show: false },
                            value: {
                                show: true,
                                fontSize: "22px",
                                fontWeight: 700,
                                color: config.value,
                                offsetY: -4,
                                formatter: function () {
                                    return formatValue(value);
                                },
                            },
                        },
                    },
                },
                tooltip: { enabled: false },
                theme: { mode: config.mode },
            };
        }

        function createGauge(type, reading) {
            const card = document.createElement("div");
            card.className = "device-telemetry-gauge-card";

            const title = document.createElement("div");
            title.className = "device-telemetry-gauge-title";
            title.textContent = String(type);

            const container = document.createElement("div");
            container.className = "device-telemetry-gauge";

            card.appendChild(title);
            card.appendChild(container);
            gaugesEl.appendChild(card);

            const chart = new ApexCharts(container, gaugeOptions(type, reading.value));
            chart.render();
            gauges.set(type, { chart: chart, card: card });
        }

        function renderGauges(types) {
            types.forEach(function (type) {
                const reading = readings.get(type);
                if (gauges.has(type)) {
                    gauges.get(type).chart.updateOptions(
                        gaugeOptions(type, reading.value),
                        true,
                        false
                    );
                } else {
                    createGauge(type, reading);
                }
            });

            gauges.forEach(function (gauge, type) {
                if (types.indexOf(type) === -1) {
                    gauge.chart.destroy();
                    gauge.card.remove();
                    gauges.delete(type);
                }
            });
        }

        function render() {
            const types = Array.from(readings.keys());
            emptyEl.hidden = types.length > 0;
            renderGauges(types);
            updatedEl.textContent = new Date().toLocaleTimeString();
        }

        function setStatus(text, live) {
            statusEl.textContent = text;
            statusEl.classList.toggle("live", Boolean(live));
        }

        function applyTheme() {
            const config = getTheme();
            gauges.forEach(function (gauge) {
                gauge.chart.updateOptions(
                    {
                        theme: { mode: config.mode },
                        plotOptions: {
                            radialBar: {
                                track: { background: config.track },
                                dataLabels: {
                                    value: { color: config.value },
                                },
                            },
                        },
                    },
                    true,
                    false
                );
            });
        }

        function connect() {
            const scheme = window.location.protocol === "https:" ? "wss://" : "ws://";
            const socket = new WebSocket(
                scheme + window.location.host + "/ws/iot/device/random-data"
            );

            socket.onopen = function () {
                setStatus("Live", true);
            };

            socket.onmessage = function (event) {
                let message;
                try {
                    message = JSON.parse(event.data);
                } catch (error) {
                    return;
                }
                if (!message || message.type !== "sensor_message") return;

                const sensors = (message.data && message.data.sensors) || [];
                const current = sensors.filter(function (sensor) {
                    return sensor && String(sensor.id) === deviceId;
                });
                if (!current.length) return;

                const next = new Map();
                function addReading(key, rawValue) {
                    const value = parseFloat(rawValue);
                    if (!Number.isFinite(value)) return;
                    next.set(String(key), { value: value });
                }

                current.forEach(function (sensor) {
                    if (sensor.type !== undefined && sensor.value !== undefined) {
                        addReading(sensor.type, sensor.value);
                        return;
                    }
                    Object.keys(sensor).forEach(function (key) {
                        if (key !== "id") addReading(key, sensor[key]);
                    });
                });
                if (!next.size) return;

                readings.clear();
                next.forEach(function (reading, type) {
                    readings.set(type, reading);
                });
                render();
            };

            socket.onclose = function () {
                setStatus("Disconnected", false);
                setTimeout(connect, 3000);
            };

            socket.onerror = function () {
                socket.close();
            };
        }

        const observer = new MutationObserver(function () {
            applyTheme();
        });
        observer.observe(document.body, { attributes: true, attributeFilter: ["class"] });

        function start() {
            if (started) return;
            started = true;
            bodyEl.hidden = false;
            pairingNoticeEl.hidden = true;
            setStatus("Connecting…", false);
            connect();
        }

        function watchPairing() {
            if (!pairingStatusUrl) return;
            fetch(pairingStatusUrl, { credentials: "same-origin" })
                .then(function (response) {
                    if (!response.ok) throw new Error("Request failed");
                    return response.text();
                })
                .then(function (html) {
                    const documentFragment = new DOMParser().parseFromString(
                        html,
                        "text/html"
                    );
                    const status = documentFragment.querySelector("[data-is-paired]");
                    if (status && Number(status.dataset.isPaired) === 2) {
                        start();
                        return;
                    }
                    setTimeout(watchPairing, 2000);
                })
                .catch(function () {
                    setTimeout(watchPairing, 2000);
                });
        }

        if (Number(root.dataset.isPaired) === 2) {
            start();
        } else {
            watchPairing();
        }
    });
})();
