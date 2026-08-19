(function () {
  function renumberRows() {
    const container = document.getElementById('attachment-rows');
    if (!container) return;

    const rows = container.querySelectorAll('.attachment-row');
    const totalForms = document.getElementById('id_form-TOTAL_FORMS');

    rows.forEach(function (row, index) {
      row.querySelectorAll('input, select, textarea').forEach(function (field) {
        if (field.name) {
          field.name = field.name.replace(/^form-(__prefix__|\d+)-/, 'form-' + index + '-');
        }
        if (field.id) {
          field.id = field.id.replace(/^id_form-(__prefix__|\d+)-/, 'id_form-' + index + '-');
        }
      });

      row.querySelectorAll('label[for]').forEach(function (label) {
        const target = label.getAttribute('for');
        if (target) {
          label.setAttribute('for', target.replace(/^id_form-(__prefix__|\d+)-/, 'id_form-' + index + '-'));
        }
      });
    });

    if (totalForms) {
      totalForms.value = rows.length;
    }
  }

  function addAttachment() {
    const container = document.getElementById('attachment-rows');
    const template = document.getElementById('attachment-template');
    if (!container || !template) return;

    const clone = template.cloneNode(true);
    clone.removeAttribute('id');
    container.appendChild(clone);
    renumberRows();

    const newRow = container.querySelector('.attachment-row:last-child');
    const input = newRow.querySelector('input[type="text"]');
    if (input) input.focus();
  }

  window.removeAttachment = function (button) {
    const row = button.closest('.attachment-row');
    if (row) {
      row.remove();
      renumberRows();
    }
  };

  document.addEventListener('DOMContentLoaded', function () {
    const addBtn = document.getElementById('btn-add-attachment');
    if (addBtn) {
      addBtn.addEventListener('click', addAttachment);
    }
  });
})();
