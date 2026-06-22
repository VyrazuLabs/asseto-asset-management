document.addEventListener("DOMContentLoaded", function () {
    const toggle = document.getElementById("twoFactorToggle");
    const regenerateBtn = document.getElementById("regenerateQrBtn");
    const qrSection = document.getElementById("qrContainer");

    function getCSRFToken() {
        const el = document.querySelector('[name=csrfmiddlewaretoken]');
        if (el) return el.value;
        const value = `; ${document.cookie}`;
        const parts = value.split('; csrftoken=');
        if (parts.length === 2) return parts.pop().split(';').shift();
        return '';
    }

    function renderQrImage(base64Data) {
        const imgContainer = document.getElementById("img-container");
        if (!imgContainer) return;
        imgContainer.innerHTML = "";
        const img = document.createElement("img");
        img.id = "dynamicQrImage";
        img.src = "data:image/png;base64," + base64Data;
        img.className = "mt-3 qr-code-image";
        imgContainer.appendChild(img);
    }

    function showQr(data) {
        if (qrSection) qrSection.classList.remove("d-none");
        if (regenerateBtn) regenerateBtn.classList.remove("d-none");
        const verifiedSection = document.getElementById("verifiedSuccess");
        if (verifiedSection) verifiedSection.classList.add("d-none");
        if (toggle) toggle.dataset.isValidate = "false";
        if (data.qr_code) {
            renderQrImage(data.qr_code);
        }
    }

    function hideQr() {
        if (qrSection) qrSection.classList.add("d-none");
        if (regenerateBtn) regenerateBtn.classList.add("d-none");
        const verifiedSection = document.getElementById("verifiedSuccess");
        if (verifiedSection) verifiedSection.classList.add("d-none");
        if (toggle) toggle.dataset.isValidate = "false";
        const existingImg = document.getElementById("dynamicQrImage");
        if (existingImg) existingImg.remove();
    }

    function getQueryParam(name) {
        const params = new URLSearchParams(window.location.search);
        return params.get(name);
    }

    // Show verification success animation if ?verified=true
    if (getQueryParam("verified") === "true") {
        const verifiedSection = document.getElementById("verifiedSuccess");
        if (verifiedSection) {
            if (qrSection) qrSection.classList.add("d-none");
            verifiedSection.classList.remove("d-none");

            // Clean the URL without reloading
            const cleanUrl = window.location.pathname + window.location.hash;
            window.history.replaceState({}, document.title, cleanUrl);
        }
    }

    // On page load: handle verified state
    if (toggle && toggle.checked) {
        if (regenerateBtn) regenerateBtn.classList.remove("d-none");
        const isValidate = toggle.dataset.isValidate;
        const verifiedSection = document.getElementById("verifiedSuccess");
        if (isValidate === "true") {
            // Already verified — show tick, hide QR
            if (qrSection) qrSection.classList.add("d-none");
            if (verifiedSection) verifiedSection.classList.remove("d-none");
        } else {
            // Not verified — show QR
            if (isValidate === "false" || isValidate === "None" || isValidate === "") {
                if (qrSection) qrSection.classList.remove("d-none");
                if (verifiedSection) verifiedSection.classList.add("d-none");
                const qrData = qrSection.dataset.qrData;
                if (qrData) {
                    renderQrImage(qrData);
                }
            }
        }
    }

    // 2FA Toggle
    if (toggle) {
        toggle.addEventListener("change", function () {
            const isChecked = toggle.checked;
            const csrfToken = getCSRFToken();
            const toggleUrl = toggle.dataset.toggleUrl;

            fetch(toggleUrl, {
                method: "POST",
                credentials: "same-origin",
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded",
                    "X-CSRFToken": csrfToken
                },
                body: new URLSearchParams({
                    two_factor_auth: isChecked ? "on" : ""
                })
            })
                .then(response => {
                    if (!response.ok) {
                        throw new Error("Server responded with status " + response.status);
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.two_factor_auth) {
                        if (data.is_validate) {
                            // Already verified — show tick, hide QR
                            const verifiedSection = document.getElementById("verifiedSuccess");
                            if (qrSection) qrSection.classList.add("d-none");
                            if (verifiedSection) verifiedSection.classList.remove("d-none");
                            if (regenerateBtn) regenerateBtn.classList.remove("d-none");
                            if (toggle) toggle.dataset.isValidate = "true";
                        } else {
                            showQr(data);
                        }
                    } else {
                        hideQr();
                    }
                })
                .catch(error => {
                    console.error("2FA toggle error:", error);
                    toggle.checked = !isChecked;
                });
        });
    }

    // Verify OTP — AJAX, no page reload
    const verifyForm = document.getElementById("verifyOtpForm");
    if (verifyForm) {
        verifyForm.addEventListener("submit", function (e) {
            e.preventDefault();
            const otpInput = document.getElementById("userOtp");
            const otp = otpInput ? otpInput.value.trim() : "";
            if (otp.length !== 6) {
                alert("Please enter a valid 6-digit OTP.");
                return;
            }

            // Build form data manually
            const formData = new URLSearchParams();
            formData.append("csrfmiddlewaretoken", getCSRFToken());
            formData.append("otp", otp);

            fetch(verifyForm.action, {
                method: "POST",
                credentials: "same-origin",
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded",
                    "X-CSRFToken": getCSRFToken(),
                    "X-Requested-With": "XMLHttpRequest"
                },
                body: formData
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        const verifiedSection = document.getElementById("verifiedSuccess");
                        if (qrSection) qrSection.classList.add("d-none");
                        if (verifiedSection) {
                            verifiedSection.classList.remove("d-none");
                            // Force animation replay
                            const svg = verifiedSection.querySelector(".verified-tick-svg");
                            if (svg) {
                                const newSvg = svg.cloneNode(true);
                                svg.parentNode.replaceChild(newSvg, svg);
                            }
                        }
                        if (toggle) toggle.dataset.isValidate = "true";
                    } else {
                        alert(data.message || "Verification failed.");
                    }
                })
                .catch(error => {
                    console.error("Verify OTP error:", error);
                    alert("Something went wrong. Please try again.");
                });
        });
    }

    // Regenerate QR
    if (regenerateBtn) {
        regenerateBtn.addEventListener("click", function () {
            const csrfToken = getCSRFToken();
            const regenerateUrl = regenerateBtn.dataset.regenerateUrl;
            regenerateBtn.disabled = true;
            regenerateBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Generating...';

            fetch(regenerateUrl, {
                method: "POST",
                credentials: "same-origin",
                headers: {
                    "X-CSRFToken": csrfToken
                }
            })
                .then(response => {
                    if (!response.ok) {
                        throw new Error("Server responded with status " + response.status);
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.success) {
                        if (qrSection) qrSection.classList.remove("d-none");
                        const verifiedSection = document.getElementById("verifiedSuccess");
                        if (verifiedSection) verifiedSection.classList.add("d-none");
                        if (toggle) toggle.dataset.isValidate = "false";
                        renderQrImage(data.qr_code);
                    } else {
                        alert(data.message || "Failed to regenerate QR");
                    }
                })
                .catch(error => {
                    console.error("Regenerate QR error:", error);
                    alert("Something went wrong");
                })
                .finally(() => {
                    regenerateBtn.disabled = false;
                    regenerateBtn.innerHTML = '<i class="bi bi-qr-code"></i> Regenerate QR Code';
                });
        });
    }
});
