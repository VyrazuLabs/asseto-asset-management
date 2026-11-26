/* =============================================================================
 * sms_integration.js — Page-level JS for the SMS Configuration page
 * (templates/configurations/sms_integration.html).
 *
 * Server-side values (provider metadata, CSRF token, URLs, state flags) are
 * passed in via data-* attributes on #smsConfigForm / #testSmsModal, so this
 * file contains no Django template syntax.
 * ========================================================================== */

"use strict";

(function () {
  let config = null;

  /* ─── Configuration ────────────────────────────────────────────────────── */

  function readConfig() {
    const form = document.getElementById("smsConfigForm");
    const modal = document.getElementById("testSmsModal");
    const hiddenProvider = document.getElementById("hiddenProviderInput");
    const providersScript = document.getElementById("providersData");
    const allCredsScript = document.getElementById("allCredentialsData");
    const statusScript = document.getElementById("providerStatusData");

    let providers = {};
    if (providersScript && providersScript.textContent) {
      try {
        providers = JSON.parse(providersScript.textContent);
      } catch (e) {
        console.error("Failed to parse providersData script:", e);
      }
    } else if (form && form.dataset.providers) {
      try {
        providers = JSON.parse(form.dataset.providers);
      } catch (e) {
        providers = {};
      }
    }

    let allCredentials = {};
    if (allCredsScript && allCredsScript.textContent) {
      try {
        allCredentials = JSON.parse(allCredsScript.textContent);
      } catch (e) {
        allCredentials = {};
      }
    }

    let providerStatus = {};
    if (statusScript && statusScript.textContent) {
      try {
        providerStatus = JSON.parse(statusScript.textContent);
      } catch (e) {
        providerStatus = {};
      }
    }

    const csrfInput = form
      ? form.querySelector('input[name="csrfmiddlewaretoken"]')
      : null;

    return {
      providers: providers,
      allCredentials: allCredentials,
      providerStatus: providerStatus,
      selectedProviderKey: hiddenProvider ? hiddenProvider.value : "msg91",
      wasActiveInitially: form ? form.dataset.wasActive === "true" : false,
      otherActiveProvider: form ? form.dataset.otherActiveProvider || "" : "",
      testSmsUrl: (modal && modal.dataset.testUrl) ? modal.dataset.testUrl : "/configurations/test-sms/",
      csrfToken: csrfInput ? csrfInput.value : "",
    };
  }

  function providerLabel(key) {
    if (!key) return "";
    return (config && config.providers && config.providers[key] && config.providers[key].name) || key.toUpperCase();
  }

  /* ─── Dynamic Field Rendering ──────────────────────────────────────────── */

  function renderFields(providerKey) {
    if (!config || !config.providers) return;
    const provider = config.providers[providerKey];
    if (!provider || !provider.fields) return;

    const container = document.getElementById("dynamicFieldsContainer");
    if (!container) return;
    container.innerHTML = "";

    const creds = (config.allCredentials && config.allCredentials[providerKey]) || {};

    provider.fields.forEach(function (field) {
      const col = document.createElement("div");
      col.className = "col-md-6 col-12 mb-3";

      const label = document.createElement("label");
      label.setAttribute("for", "field_" + field.key);
      const labelBold = document.createElement("b");
      labelBold.textContent = field.label || "";
      label.appendChild(labelBold);
      if (field.required) {
        label.appendChild(document.createTextNode(" "));
        const reqSpan = document.createElement("span");
        reqSpan.className = "text-danger";
        reqSpan.textContent = "*";
        label.appendChild(reqSpan);
      }
      col.appendChild(label);

      const val = creds[field.key] || "";
      const input = document.createElement("input");
      input.className = "form-control";
      input.id = "field_" + field.key;
      input.name = field.key;
      input.placeholder = field.placeholder || "";
      input.value = val;
      if (field.required) {
        input.required = true;
      }

      if (field.type === "password") {
        input.type = "password";
        const group = document.createElement("div");
        group.className = "input-group mt-1";
        group.appendChild(input);

        const toggleBtn = document.createElement("button");
        toggleBtn.className = "btn btn-outline-secondary";
        toggleBtn.type = "button";
        toggleBtn.dataset.passwordToggle = "field_" + field.key;
        const icon = document.createElement("i");
        icon.className = "bi bi-eye";
        toggleBtn.appendChild(icon);
        group.appendChild(toggleBtn);
        col.appendChild(group);
      } else {
        input.type = "text";
        input.className = "form-control mt-1";
        if (field.maxlength) {
          input.maxLength = field.maxlength;
        }
        col.appendChild(input);
      }

      if (field.help) {
        const helpEl = document.createElement("small");
        helpEl.className = "text-muted d-block mt-1";
        helpEl.textContent = field.help;
        col.appendChild(helpEl);
      }

      container.appendChild(col);
    });
  }

  /* ─── Provider switching ───────────────────────────────────────────────── */

  function supportsCustomMessage(providerKey) {
    const provider = config && config.providers && config.providers[providerKey];
    if (!provider || typeof provider.supports_custom_message === "undefined") {
      return providerKey !== "msg91";
    }
    return Boolean(provider.supports_custom_message);
  }

  function updateTestModalProvider(providerKey) {
    const testMsgGroup = document.getElementById("testMessageGroup");
    const msg91Notice = document.getElementById("msg91TemplateNotice");
    if (!testMsgGroup || !msg91Notice) return;

    if (supportsCustomMessage(providerKey)) {
      testMsgGroup.classList.remove("d-none");
      msg91Notice.classList.add("d-none");
    } else {
      testMsgGroup.classList.add("d-none");
      msg91Notice.classList.remove("d-none");
    }
  }

  function switchProvider(providerKey) {
    if (!providerKey) return;
    if (config) config.selectedProviderKey = providerKey;

    // 1. Update hidden input & dropdowns
    const hiddenProvider = document.getElementById("hiddenProviderInput");
    if (hiddenProvider) hiddenProvider.value = providerKey;

    const testProviderSelect = document.getElementById("testProviderSelect");
    if (testProviderSelect) testProviderSelect.value = providerKey;

    updateTestModalProvider(providerKey);

    const providerSelect = document.getElementById("providerSelect");
    if (providerSelect && providerSelect.value !== providerKey) {
      providerSelect.value = providerKey;
    }

    // 2. Update URL in browser address bar (without full page refresh)
    try {
      const newUrl = new URL(window.location.href);
      newUrl.searchParams.set("provider", providerKey);
      window.history.replaceState({}, "", newUrl.toString());
    } catch (e) {}

    // 3. Update Step-by-Step Guide
    if (config && config.providers && config.providers[providerKey]) {
      const p = config.providers[providerKey];
      const guideTitle = document.getElementById("guideTitle");
      if (guideTitle) guideTitle.innerText = "How to obtain " + p.name + " credentials:";

      const portalBtn = document.getElementById("providerPortalBtn");
      if (portalBtn) {
        portalBtn.href = p.portal_url || "#";
        portalBtn.innerHTML = "Open " + p.name + " Portal <i class=\"bi bi-box-arrow-up-right ms-1\"></i>";
      }

      const guideList = document.getElementById("guideList");
      if (guideList && p.guide) {
        guideList.innerHTML = p.guide
          .map(function (step) {
            return "<li>" + step + "</li>";
          })
          .join("");
      }
    }

    // 4. Update status toggle switch
    const statusSwitch = document.getElementById("id_is_active");
    if (statusSwitch && config && config.providerStatus) {
      statusSwitch.checked = Boolean(config.providerStatus[providerKey]);
    }

    // 5. Render fields dynamically
    renderFields(providerKey);
  }

  window.switchProvider = switchProvider;

  /* ─── Password field visibility ────────────────────────────────────────── */

  function togglePasswordVisibility(fieldId, btn) {
    const input = document.getElementById(fieldId);
    if (!input) return;

    const icon = btn.querySelector("i");
    if (input.type === "password") {
      input.type = "text";
      icon.classList.remove("bi-eye");
      icon.classList.add("bi-eye-slash");
    } else {
      input.type = "password";
      icon.classList.remove("bi-eye-slash");
      icon.classList.add("bi-eye");
    }
  }

  /* ─── Test SMS modal ───────────────────────────────────────────────────── */

  function submitTestSms() {
    const phone = document.getElementById("testPhoneInput").value.trim();
    const provider = document.getElementById("testProviderSelect").value;
    const messageInput = document.getElementById("testMessageInput");
    const message = messageInput ? messageInput.value.trim() : "";
    const alertBox = document.getElementById("testAlertBox");
    const sendBtn = document.getElementById("sendTestSmsBtn");
    const spinner = document.getElementById("testSpinner");
    const sendText = document.getElementById("testSendText");

    if (!phone) {
      alertBox.className = "alert alert-danger";
      alertBox.innerText = "Please enter a recipient phone number.";
      alertBox.classList.remove("d-none");
      return;
    }

    // Only digits, optional leading + (country code). 10–15 digits total
    // (E.164 max is 15; 10 covers domestic Indian numbers).
    const phoneDigits = phone.replace(/\D/g, "");
    if (!/^\+?\d+$/.test(phone) || phoneDigits.length < 10 || phoneDigits.length > 15) {
      alertBox.className = "alert alert-danger";
      alertBox.innerText =
        "Please enter a valid mobile number: digits only (10–15), optionally starting with + and country code (e.g. 9876543210 or +919876543210).";
      alertBox.classList.remove("d-none");
      return;
    }

    const formData = new FormData();
    formData.append("csrfmiddlewaretoken", config.csrfToken);
    formData.append("provider", provider);
    formData.append("phone", phone);
    // Template-only providers deliver their registered template body, so only
    // submit a custom message when the provider supports one.
    if (supportsCustomMessage(provider) && messageInput) {
      formData.append("message", message);
    }

    // Include unsaved credential fields from the configuration form
    document.querySelectorAll("#smsConfigForm input").forEach(function (input) {
      if (input.name && input.value) {
        formData.append(input.name, input.value);
      }
    });

    sendBtn.disabled = true;
    spinner.classList.remove("d-none");
    sendText.innerText = "Sending...";
    alertBox.classList.add("d-none");

    fetch(config.testSmsUrl, {
      method: "POST",
      body: formData,
      headers: {
        "X-Requested-With": "XMLHttpRequest",
      },
    })
      .then(function (response) {
        return response.json().then(function (data) {
          return { status: response.status, body: data };
        });
      })
      .then(function ({ status, body }) {
        sendBtn.disabled = false;
        spinner.classList.add("d-none");
        sendText.innerText = "Send Test";

        if (body.success) {
          alertBox.className = "alert alert-success";
          alertBox.replaceChildren();
          const strong = document.createElement("strong");
          strong.textContent = "Success! ";
          alertBox.appendChild(strong);
          alertBox.appendChild(document.createTextNode(body.message || ""));
          alertBox.classList.remove("d-none");
        } else {
          alertBox.className = "alert alert-danger";
          alertBox.replaceChildren();
          const strong = document.createElement("strong");
          strong.textContent = "Delivery Failed: ";
          alertBox.appendChild(strong);
          alertBox.appendChild(document.createTextNode(body.error || "Unknown error"));
          if (body.details) {
            const wrap = document.createElement("div");
            wrap.className = "mt-2";
            const label = document.createElement("strong");
            label.textContent = "API Response: ";
            const pre = document.createElement("pre");
            pre.className = "mb-0";
            pre.style.cssText =
              "font-size:0.75rem;white-space:pre-wrap;word-break:break-all;background:transparent;border:0;padding:0;";
            pre.textContent =
              typeof body.details === "string"
                ? body.details
                : JSON.stringify(body.details, null, 2);
            wrap.appendChild(label);
            wrap.appendChild(pre);
            alertBox.appendChild(wrap);
          }
          alertBox.classList.remove("d-none");
        }
      })
      .catch(function (err) {
        sendBtn.disabled = false;
        spinner.classList.add("d-none");
        sendText.innerText = "Send Test";
        alertBox.className = "alert alert-danger";
        alertBox.replaceChildren();
        const strong = document.createElement("strong");
        strong.textContent = "Request Failed: ";
        alertBox.appendChild(strong);
        alertBox.appendChild(document.createTextNode(err.message || "Network error"));
        alertBox.classList.remove("d-none");
      });
  }

  // Reset the Test SMS modal to a fresh state every time it is closed
  function resetTestSmsModal() {
    const alertBox = document.getElementById("testAlertBox");
    const sendBtn = document.getElementById("sendTestSmsBtn");
    const spinner = document.getElementById("testSpinner");
    const sendText = document.getElementById("testSendText");
    if (alertBox) {
      alertBox.className = "alert d-none mb-3";
      alertBox.innerHTML = "";
    }
    if (sendBtn) sendBtn.disabled = false;
    if (spinner) spinner.classList.add("d-none");
    if (sendText) sendText.innerText = "Send Test";
  }

  /* ─── Status toggle confirmation ───────────────────────────────────────── */

  function handleStatusToggleChange(switchElem) {
    if (!switchElem.checked) {
      if (config.wasActiveInitially) {
        const confirmed = confirm(
          "Are you sure you want to disable SMS service?\n\n" +
            "Disabling it will stop sending automated notifications for support tickets and alerts."
        );
        if (!confirmed) {
          switchElem.checked = true;
        }
      }
    } else {
      if (
        config.otherActiveProvider &&
        config.otherActiveProvider !== config.selectedProviderKey
      ) {
        const newProvider = providerLabel(config.selectedProviderKey);
        const confirmed = confirm(
          "Activating " +
            newProvider +
            " will deactivate " +
            config.otherActiveProvider.toUpperCase() +
            ".\n\n" +
            "Only one SMS provider can be active at a time. All future alerts will be routed via " +
            newProvider +
            ".\n\n" +
            "Do you want to proceed?"
        );
        if (!confirmed) {
          switchElem.checked = false;
        }
      }
    }
  }

  /* ─── Form validation ──────────────────────────────────────────────────── */

  function initFormValidation() {
    const smsForm = document.getElementById("smsConfigForm");
    if (!smsForm) return;

    smsForm.addEventListener("submit", function (e) {
      // If disabling an active service, confirm with the user
      const statusSwitch = document.getElementById("id_is_active");
      if (config.wasActiveInitially && statusSwitch && !statusSwitch.checked) {
        const confirmed = confirm(
          "Are you sure you want to disable SMS service?\n\n" +
            "Disabling it will stop sending automated notifications for support tickets and alerts."
        );
        if (!confirmed) {
          e.preventDefault();
          statusSwitch.checked = true;
          return false;
        }
      }

      let isValid = true;
      let firstInvalid = null;

      const requiredInputs = smsForm.querySelectorAll("input[required]");
      requiredInputs.forEach(function (input) {
        const val = input.value.trim();
        if (!val) {
          isValid = false;
          input.classList.add("is-invalid");
          if (!firstInvalid) {
            firstInvalid = input;
          }
        } else {
          input.classList.remove("is-invalid");
        }
      });

      if (!isValid) {
        e.preventDefault();
        if (firstInvalid) {
          firstInvalid.focus();
          const labelElem = firstInvalid.closest(".mb-3")?.querySelector("label b");
          const labelText = labelElem ? labelElem.innerText : "Required field";
          if (typeof Toastify === "function") {
            Toastify({
              text: "Field '" + labelText + "' is required.",
              duration: 3500,
              close: true,
              style: { background: "#d9534f" },
            }).showToast();
          }
        }
        return false;
      }
    });

    // Clear invalid styling when the user types
    smsForm.querySelectorAll("input").forEach(function (input) {
      input.addEventListener("input", function () {
        if (this.value.trim()) {
          this.classList.remove("is-invalid");
        }
      });
    });
  }

  /* ─── Initialization ───────────────────────────────────────────────────── */

  function init() {
    config = readConfig();

    const providerSelect = document.getElementById("providerSelect");
    if (providerSelect) {
      providerSelect.addEventListener("change", function () {
        switchProvider(this.value);
      });
      if (window.jQuery) {
        window.jQuery(providerSelect).on("change select2:select", function () {
          switchProvider(this.value);
        });
      }
    }

    const statusSwitch = document.getElementById("id_is_active");
    if (statusSwitch) {
      statusSwitch.addEventListener("change", function () {
        handleStatusToggleChange(this);
      });
    }

    // Password show/hide (event delegation for dynamically rendered fields)
    const fieldsContainer = document.getElementById("dynamicFieldsContainer");
    if (fieldsContainer) {
      fieldsContainer.addEventListener("click", function (e) {
        const btn = e.target.closest("[data-password-toggle]");
        if (!btn) return;
        togglePasswordVisibility(btn.dataset.passwordToggle, btn);
      });
    }

    const sendTestBtn = document.getElementById("sendTestSmsBtn");
    if (sendTestBtn) {
      sendTestBtn.addEventListener("click", submitTestSms);
    }

    // Keep the custom Message field / DLT notice in sync with the provider
    // chosen inside the Test SMS modal itself.
    const testProviderSelect = document.getElementById("testProviderSelect");
    if (testProviderSelect) {
      testProviderSelect.addEventListener("change", function () {
        updateTestModalProvider(this.value);
      });
    }

    updateTestModalProvider(config.selectedProviderKey);

    const testModal = document.getElementById("testSmsModal");
    if (testModal) {
      testModal.addEventListener("hidden.bs.modal", resetTestSmsModal);
    }

    initFormValidation();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
