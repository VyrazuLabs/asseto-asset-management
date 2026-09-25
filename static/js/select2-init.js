/**
 * Central Select2 initializer.
 *
 * - Auto-inits every <select> on the page (except [data-no-select2]).
 * - Sets dropdownParent to the enclosing Bootstrap modal (required for modals).
 * - Re-inits selects added later by htmx swaps / modal content loads / DOM clones.
 * - Opt-out:  <select data-no-select2>
 * - Extras:   data-placeholder="..."   placeholder text
 *             data-allow-clear="false"  disable the clear (x) button
 *
 * Manual use: window.initSelect2(rootElement)
 */
(function () {
  'use strict';

  var SELECTOR = 'select:not(.select2-hidden-accessible):not([data-no-select2])';

  function optionsFor(el) {
    var opts = { width: '100%', theme: 'default' };

    var placeholder = el.getAttribute('data-placeholder');
    if (!placeholder) {
      var first = el.options.length ? el.options[0] : null;
      if (first && first.value === '') {
        placeholder = (first.textContent || '').trim();
      }
    }
    if (placeholder) {
      opts.placeholder = placeholder;
      opts.allowClear = el.getAttribute('data-allow-clear') !== 'false';
    }

    var modal = el.closest ? el.closest('.modal') : null;
    if (modal) {
      opts.dropdownParent = window.jQuery(modal);
    }

    var noResults = el.getAttribute('data-select2-no-results');
    var searching = el.getAttribute('data-select2-searching');
    if (noResults || searching) {
      opts.language = {};
      if (noResults) {
        opts.language.noResults = function () { return noResults; };
      }
      if (searching) {
        opts.language.searching = function () { return searching; };
      }
    }

    return opts;
  }

  window.initSelect2 = initSelect2;

  /**
   * cloneNode(true) copies a Select2-initialized <select> (class
   * select2-hidden-accessible + stale data-select2-id, but no live instance)
   * AND the rendered <span class="select2-container">, which is dead markup
   * with no event handlers (clicking it does nothing).
   * Strip that leftover state so the select can be initialized fresh.
   */
  function repairClonedSelect(el) {
    var jq = window.jQuery;
    if (jq(el).data('select2')) return; // live instance -> nothing to repair

    // Drop the cloned id: Select2 keys its Utils cache by data-select2-id,
    // so keeping it would make this select share the original's cache entry.
    el.classList.remove('select2-hidden-accessible');
    el.removeAttribute('aria-hidden');
    el.removeAttribute('data-select2-id');
    if (el.getAttribute('tabindex') === '-1') el.removeAttribute('tabindex');

    // Cloned <option>/<optgroup> children also carry the original's
    // data-select2-id. Select2's cache maps those IDs to item data whose
    // .element points at the ORIGINAL option — selecting in the clone would
    // then set .selected on the original's option and the clone's display
    // would never update. Strip the IDs so each option gets a fresh cache
    // entry bound to the cloned element.
    var stamped = el.querySelectorAll('[data-select2-id]');
    Array.prototype.forEach.call(stamped, function (node) {
      node.removeAttribute('data-select2-id');
    });

    // Select2 does insertAfter($element), so the dead box sits directly
    // next to the select — remove it (both sides, to be safe).
    [el.previousElementSibling, el.nextElementSibling].forEach(function (sib) {
      if (sib && sib.classList &&
          (sib.classList.contains('select2-container') || sib.classList.contains('select2'))) {
        sib.parentNode.removeChild(sib);
      }
    });
  }

  function initSelect2(root) {
    var jq = window.jQuery;
    if (!jq || !jq.fn || !jq.fn.select2) return;

    // Repair cloned selects BEFORE querying, since SELECTOR skips
    // .select2-hidden-accessible elements.
    var scope = root && root.querySelectorAll ? root : document;
    var maybeCloned = scope.querySelectorAll('select.select2-hidden-accessible');
    Array.prototype.forEach.call(maybeCloned, repairClonedSelect);

    var nodes = [];
    if (root && root.nodeType === 1 && root.tagName === 'SELECT') {
      nodes.push(root);
    }
    if (root && root.querySelectorAll) {
      nodes = nodes.concat(jq.makeArray(root.querySelectorAll(SELECTOR)));
    }
    if (!root) {
      nodes = nodes.concat(jq.makeArray(document.querySelectorAll(SELECTOR)));
    }

    nodes.forEach(function (el) {
      var $el = jq(el);
      if ($el.data('select2')) return;
      try {
        $el.select2(optionsFor(el));
      } catch (e) {
        if (window.console && console.warn) console.warn('Select2 init failed', el, e);
      }
    });
  }

  function boot() {
    initSelect2(document);

    // Move the caret straight into the search box whenever a dropdown opens
    // (Select2 doesn't always focus it, e.g. inside modals / cloned selects).
    // select2:open is a jQuery event -> must bind with jQuery, not addEventListener.
    if (window.jQuery) {
      window.jQuery(document).on('select2:open', function () {
        var field = document.querySelector('.select2-container--open .select2-search__field');
        if (field) {
          // Defer so the dropdown open animation doesn't steal focus back
          setTimeout(function () { field.focus(); }, 0);
        }
      });
    }

    // Selects swapped in by htmx (lists, modal bodies, table rows)
    document.addEventListener('htmx:afterSwap', function (evt) {
      if (evt.detail && evt.detail.target) initSelect2(evt.detail.target);
    });

    // Selects injected by JS (cloned contact rows, ajax-loaded content)
    var timer = null;
    var observer = new MutationObserver(function (mutations) {
      var needsInit = false;
      for (var i = 0; i < mutations.length; i++) {
        var added = mutations[i].addedNodes;
        for (var j = 0; j < added.length; j++) {
          var node = added[j];
          if (node.nodeType !== 1) continue;
          if (node.tagName === 'SELECT' || (node.querySelectorAll && node.querySelectorAll('select').length)) {
            needsInit = true;
            break;
          }
        }
        if (needsInit) break;
      }
      if (!needsInit) return;
      clearTimeout(timer);
      timer = setTimeout(function () { initSelect2(document); }, 50);
    });
    observer.observe(document.body, { childList: true, subtree: true });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
