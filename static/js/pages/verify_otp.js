document.body.addEventListener('htmx:afterSwap', function (evt) {
  if (evt.detail.target.id === "modalContainer") {
    const modalElement = document.getElementById('verifyOtpModal');
    if (modalElement) {
      const modal = new bootstrap.Modal(modalElement);
      modal.show();
    }
  }
});

document.addEventListener("DOMContentLoaded", function () {
  const inputs = document.querySelectorAll(".otp-box");
  const hiddenInput = document.getElementById("userOtp");

  if (!inputs.length) return;

  inputs.forEach((input, index) => {
    input.addEventListener("input", (e) => {
      e.target.value = e.target.value.replace(/[^0-9]/g, '');
      if (e.target.value && index < inputs.length - 1) {
        inputs[index + 1].focus();
      }
      updateHiddenOtp();
    });

    input.addEventListener("keydown", (e) => {
      if (e.key === "Backspace" && !input.value && index > 0) {
        inputs[index - 1].focus();
      }
    });
  });

  function updateHiddenOtp() {
    let otp = "";
    inputs.forEach(input => otp += input.value);
    if (hiddenInput) hiddenInput.value = otp;
  }

  const verifyBtn = document.getElementById("verify2faBtn");
  if (verifyBtn) {
    verifyBtn.addEventListener("click", function () {
      const otpValue = hiddenInput ? hiddenInput.value.trim() : "";
      const emailEl = document.querySelector('input[name="email"]');
      const email = emailEl ? emailEl.value : "";

      if (!otpValue) {
        alert("Please enter OTP");
        return;
      }

      const url = `/api/authentication/login-otp/?email=${encodeURIComponent(email)}&otp=${encodeURIComponent(otpValue)}`;

      fetch(url, {
        method: "POST",
        credentials: "same-origin"
      })
      .then(response => response.json())
      .then(data => {
        if (data.access) {
          localStorage.setItem("access_token", data.access);
          localStorage.setItem("refresh_token", data.refresh);
          alert("Login successful!");
          window.location.href = "/";
        } else {
          alert(data.message || "Invalid OTP");
        }
      })
      .catch(error => {
        console.error("Error:", error);
        alert("Something went wrong");
      });
    });
  }

  const regenerateBtn = document.getElementById("regenerateQrBtn");
  if (regenerateBtn) {
    regenerateBtn.addEventListener("click", function () {
      const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
      const regenerateUrl = regenerateBtn.dataset.regenerateUrl;

      if (!regenerateUrl) return;

      regenerateBtn.disabled = true;
      regenerateBtn.innerText = "Generating...";

      fetch(regenerateUrl, {
        method: "POST",
        headers: { "X-CSRFToken": csrfToken }
      })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          const existingImg = document.getElementById("dynamicQrImage");
          if (existingImg) existingImg.remove();

          const img = document.createElement("img");
          img.id = "dynamicQrImage";
          img.src = "data:image/png;base64," + data.qr_code;
          img.className = "img-fluid mb-3";
          img.style.maxWidth = "200px";
          img.alt = "QR Code";

          regenerateBtn.parentNode.insertBefore(img, regenerateBtn);
        } else {
          alert("Failed to regenerate QR");
        }
      })
      .catch(error => {
        console.error("Error:", error);
        alert("Something went wrong");
      })
      .finally(() => {
        regenerateBtn.disabled = false;
        regenerateBtn.innerText = "Regenerate QR Code";
      });
    });
  }
});
