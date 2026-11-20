(function () {
    "use strict";

    if (typeof ApexCharts === "undefined") return;

    document.addEventListener("DOMContentLoaded", function () {
        const gaugeEl = document.getElementById("sensorLiveGauge");
        const emptyEl = document.getElementById("sensorGaugeEmpty");
        if (!gaugeEl) return;

        const sensorId = gaugeEl.dataset.sensorId;
        const unit = gaugeEl.dataset.unit || "";
        const endpoint = gaugeEl.dataset.endpoint;
        const initialValue = parseFloat(gaugeEl.dataset.initialValue);
        const initialTime = gaugeEl.dataset.initialTime;

        const minEl = document.getElementById("sensorGaugeMin");
        const maxEl = document.getElementById("sensorGaugeMax");
        const valueEl = document.getElementById("sensorGaugeValue");
        const updatedEl = document.getElementById("sensorGaugeUpdated");

        let chart = null;
        let rangeMin = 0;
        let rangeMax = 100;

        function getThemeConfig() {
            const isDark =
                document.body.classList.contains("theme-dark") ||
                document.body.classList.contains("dark") ||
                localStorage.getItem("theme") === "theme-dark";
            return {
                mode: isDark ? "dark" : "light",
                labelColor: isDark ? "#CBD5E1" : "#94A3B8",
                valueColor: isDark ? "#FFFFFF" : "#1E293B",
                trackColor: isDark ? "#2D2D44" : "#F1F5F9",
            };
        }

        function formatTime(input) {
            if (!input) return "--";
            const date = input instanceof Date ? input : new Date(input);
            if (isNaN(date.getTime())) return "--";
            return date.toLocaleString([], {
                month: "short",
                day: "numeric",
                hour: "2-digit",
                minute: "2-digit",
                second: "2-digit",
            });
        }

        function valueToPercent(value) {
            if (rangeMax === rangeMin) return 50;
            const percent = ((value - rangeMin) * 100) / (rangeMax - rangeMin);
            return Math.max(0, Math.min(100, percent));
        }

        function percentToValue(percent) {
            return (percent * (rangeMax - rangeMin)) / 100 + rangeMin;
        }

        function buildOptions() {
            const config = getThemeConfig();
            return {
                series: [0],
                chart: {
                    type: "radialBar",
                    height: 300,
                    background: "transparent",
                    fontFamily: "inherit",
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
                labels: ["Current Reading"],
                plotOptions: {
                    radialBar: {
                        startAngle: -90,
                        endAngle: 90,
                        hollow: { size: "70%" },
                        track: {
                            background: config.trackColor,
                            strokeWidth: "97%",
                            margin: 5,
                            dropShadow: { enabled: false },
                        },
                        dataLabels: {
                            name: {
                                show: true,
                                fontSize: "14px",
                                fontWeight: 600,
                                color: config.labelColor,
                                offsetY: 50,
                            },
                            value: {
                                show: true,
                                fontSize: "26px",
                                fontWeight: 700,
                                color: config.valueColor,
                                offsetY: -10,
                                formatter: function (val) {
                                    const real = percentToValue(val);
                                    const text = Number.isFinite(real) ? real.toFixed(1) : "--";
                                    return unit ? text + " " + unit : text;
                                },
                            },
                        },
                    },
                },
                theme: { mode: config.mode },
            };
        }

        function applyTheme() {
            if (!chart) return;
            const config = getThemeConfig();
            chart.updateOptions({
                theme: { mode: config.mode },
                plotOptions: {
                    radialBar: {
                        track: { background: config.trackColor },
                        dataLabels: {
                            name: { color: config.labelColor },
                            value: { color: config.valueColor },
                        },
                    },
                },
            });
        }

        function setMeta(value, time) {
            if (valueEl) {
                const text = Number.isFinite(value) ? value.toFixed(1) : "--";
                valueEl.textContent = unit ? text + " " + unit : text;
            }
            if (rangeMin !== null && minEl) {
                minEl.textContent = unit ? rangeMin.toFixed(1) + " " + unit : rangeMin.toFixed(1);
            }
            if (rangeMax !== null && maxEl) {
                maxEl.textContent = unit ? rangeMax.toFixed(1) + " " + unit : rangeMax.toFixed(1);
            }
            if (updatedEl) updatedEl.textContent = formatTime(time);
        }

        function renderGauge(value, time) {
            gaugeEl.hidden = false;
            if (emptyEl) emptyEl.hidden = true;
            setMeta(value, time);
            if (!chart) {
                chart = new ApexCharts(gaugeEl, buildOptions());
                chart.render();
            }
            chart.updateSeries([valueToPercent(value)]);
        }

        function showEmpty() {
            // Keep gauge visible in idle state rather than hiding it
            gaugeEl.hidden = false;
            if (emptyEl) emptyEl.hidden = true;
            if (valueEl) valueEl.textContent = "--";
            if (minEl) minEl.textContent = "--";
            if (maxEl) maxEl.textContent = "--";
            if (updatedEl) updatedEl.textContent = "--";
            if (!chart) {
                chart = new ApexCharts(gaugeEl, buildOptions());
                chart.render();
            }
            chart.updateSeries([0]);
        }

        function setCurrent(value, time) {
            if (!Number.isFinite(value)) return;
            if (value < rangeMin) rangeMin = value;
            if (value > rangeMax) rangeMax = value;
            renderGauge(value, time);
        }

        function padRange(min, max, seed) {
            const base = Math.abs(seed) || 1;
            let pad;
            if (min === max) pad = base * 0.1;
            else pad = (max - min) * 0.1;
            return { min: min - pad, max: max + pad };
        }

        function initFromHistory() {
            fetch(endpoint + "?hours=24")
                .then(function (response) {
                    if (!response.ok) throw new Error("Request failed");
                    return response.json();
                })
                .then(function (payload) {
                    const data = payload && payload.data ? payload.data : [];
                    const values = data
                        .map(function (d) {
                            return parseFloat(d.value);
                        })
                        .filter(function (v) {
                            return Number.isFinite(v);
                        });

                    if (values.length) {
                        const lo = Math.min.apply(null, values);
                        const hi = Math.max.apply(null, values);
                        const padded = padRange(lo, hi, hi);
                        rangeMin = padded.min;
                        rangeMax = padded.max;

                        const current = values[values.length - 1];
                        const time = data[data.length - 1].timestamp
                            ? new Date(data[data.length - 1].timestamp * 1000)
                            : null;
                        renderGauge(current, time);
                        return;
                    }

                    if (Number.isFinite(initialValue)) {
                        const padded = padRange(initialValue, initialValue, initialValue);
                        rangeMin = padded.min;
                        rangeMax = padded.max;
                        renderGauge(initialValue, initialTime);
                        return;
                    }

                    showEmpty();
                })
                .catch(function () {
                    if (Number.isFinite(initialValue)) {
                        const padded = padRange(initialValue, initialValue, initialValue);
                        rangeMin = padded.min;
                        rangeMax = padded.max;
                        renderGauge(initialValue, initialTime);
                        return;
                    }
                    showEmpty();
                });
        }

        function connectWebSocket() {
            const scheme = window.location.protocol === "https:" ? "wss://" : "ws://";
            let socket = null;
            let reconnectTimer = null;

            function open() {
                socket = new WebSocket(scheme + window.location.host + "/ws/iot/device/random-data");

                socket.onopen = function () {};

                socket.onmessage = function (event) {
                    let message;
                    try {
                        message = JSON.parse(event.data);
                    } catch (e) {
                        return;
                    }
                    if (!message || message.type !== "sensor_message") return;
                    const payload = message.data || {};
                    const sensors = payload.sensors || [];

                    // Find the sensor matching this page's sensor ID
                    const match = sensors.find(function (s) {
                        return String(s.id) === String(sensorId);
                    });
                    if (!match) return;

                    const value = parseFloat(match.value);
                    if (!Number.isFinite(value)) return;
                    setCurrent(value, new Date());
                };

                socket.onclose = function () {
                    if (reconnectTimer) clearTimeout(reconnectTimer);
                    reconnectTimer = setTimeout(open, 3000);
                };

                socket.onerror = function () {
                    if (socket) socket.close();
                };
            }

            open();
        }

        const observer = new MutationObserver(function (mutations) {
            mutations.forEach(function (mutation) {
                if (mutation.attributeName === "class") applyTheme();
            });
        });
        observer.observe(document.body, { attributes: true });

        initFromHistory();
        connectWebSocket();
    });
})();