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

/* ─── Bootstrap ───────────────────────────────────────────────────────────── */

document.addEventListener("DOMContentLoaded", function () {
  initTechnicianFilter();
  initDeleteConfirmation();
});
