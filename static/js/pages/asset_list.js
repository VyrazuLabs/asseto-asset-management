/**
 * asset_list.js
 * Client-side script for asset inventory list page.
 */

document.addEventListener("DOMContentLoaded", function () {
  document.addEventListener("click", function (e) {
    var link = e.target && e.target.closest ? e.target.closest(".asset-export-csv") : null;
    if (!link) return;
    e.preventDefault();
    var form = document.getElementById("asset-filter-form");
    var params = form ? new URLSearchParams(new FormData(form)).toString() : "";
    window.location.href = link.getAttribute("href") + (params ? "?" + params : "");
  });
});
