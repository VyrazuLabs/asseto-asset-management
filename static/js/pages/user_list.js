/**
 * user_list.js
 * Page-level JS for the Users List page (templates/users/list.html).
 * All logic extracted from inline onclick/onsubmit handlers per
 * django_template_rules.md (Rule 1: Separation of Concerns).
 */

"use strict";

/* ─── Technician filter dropdown ─────────────────────────────────────────── */

/**
 * Handles clicks on the technician filter dropdown items.
 * Reads `data-technician-value` and `data-technician-label` attributes
 * set on each <a> element, then updates the hidden input and triggers
 * the HTMX form change.
 */
function initTechnicianFilter() {
  document.addEventListener("click", function (event) {
    const item = event.target.closest("[data-technician-value]");
    if (!item) return;

    event.preventDefault();

    const form = document.getElementById("user-filter-form");
    const btn  = document.getElementById("technician-btn");
    if (!form || !btn) return;

    const value = item.dataset.technicianValue;
    const label = item.dataset.technicianLabel;

    form.querySelector("[name=technician]").value = value;
    // childNodes[0] is the text node inside the button (before the caret icon)
    btn.childNodes[0].textContent = label + " ";
    htmx.trigger(form, "change");
  });
}

/* ─── Delete confirmation ─────────────────────────────────────────────────── */

/**
 * Intercepts submit events on user delete forms (.user-delete-form).
 * Uses event delegation on document so it works after HTMX partial
 * re-renders (search results swap the tbody in place).
 * The confirmation message is stored in data-confirm-message on the form.
 */
function initDeleteConfirmation() {
  document.addEventListener("submit", function (event) {
    const form = event.target;
    if (!form.matches(".user-delete-form")) return;

    const message = form.dataset.confirmMessage || "Are you sure you want to delete this user?";
    if (!window.confirm(message)) {
      event.preventDefault();
    }
  });
}

/* ─── User Add/Update Modals Interactive Logic ────────────────────────────── */

/**
 * Handles the "Enable User Login" switch and password fields toggle.
 */
function initPasswordToggle() {
  const handleToggle = (checkbox) => {
    const modal = checkbox.closest(".modal-content");
    if (!modal) return;
    const fields = modal.querySelector("#password_fields");
    if (!fields) return;
    if (checkbox.checked) {
      fields.classList.remove("d-none");
    } else {
      fields.classList.add("d-none");
    }
  };

  document.addEventListener("change", function (event) {
    const checkbox = event.target.closest("#toggle_password");
    if (checkbox) {
      handleToggle(checkbox);
    }
  });

  document.addEventListener("htmx:load", function () {
    const checkbox = document.getElementById("toggle_password");
    if (checkbox) {
      handleToggle(checkbox);
    }
  });
}

/**
 * Handles the image file input preview and dynamic adding of form-control class.
 */
function initImagePreview() {
  document.addEventListener("change", function (event) {
    const fileInput = event.target.closest('input[type="file"]');
    if (!fileInput) return;

    const modal = fileInput.closest(".modal-content");
    if (!modal) return;

    const file = fileInput.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = function (e) {
        const preview = modal.querySelector("#imagePreview");
        if (preview) {
          preview.innerHTML = `<img src="${e.target.result}" class="rounded-circle border shadow-sm preview-avatar">`;
        }
      };
      reader.readAsDataURL(file);
    }
  });

  document.addEventListener("htmx:load", function () {
    const fileInput = document.querySelector('.modal-content input[type="file"]');
    if (fileInput) {
      fileInput.classList.add("form-control");
    }
  });
}

/**
 * Handles showing a loading spinner on form submit button.
 */
function initFormSavingSpinner() {
  document.addEventListener("submit", function (event) {
    const form = event.target.closest(".modal-premium form");
    if (!form) return;

    const saveBtn = form.querySelector(".btn-save-user");
    if (saveBtn) {
      const savingText = saveBtn.dataset.savingText || "Saving...";
      saveBtn.innerHTML = `<span class='spinner-grow spinner-grow-sm' role='status' aria-hidden='true'></span> ${savingText}`;
    }
  });
}

/**
 * Reloads the page when HTMX receives an empty response (indicating a successful action).
 */
function initHtmxBeforeSwapReload() {
  document.addEventListener("htmx:beforeSwap", function (event) {
    const targetId = event.detail.target.id;
    if (
      (targetId === "add-user-modal-content" || targetId === "update-user-modal-content") &&
      !event.detail.xhr.response
    ) {
      location.reload();
    }
  });
}

/* ─── Bootstrap ───────────────────────────────────────────────────────────── */

document.addEventListener("DOMContentLoaded", function () {
  initTechnicianFilter();
  initDeleteConfirmation();
  initPasswordToggle();
  initImagePreview();
  initFormSavingSpinner();
  initHtmxBeforeSwapReload();
});

