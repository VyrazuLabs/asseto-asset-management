/* =============================================================================
   support_tickets.js — Kanban drag-drop + ticket detail comment logic
   ============================================================================= */

document.addEventListener('DOMContentLoaded', function () {

  // ── Kanban Drag-Drop ──────────────────────────────────────────────────────────

  let kanbanSortableInstances = [];

  function getCSRFToken() {
    const name = 'csrftoken';
    const cookies = document.cookie.split(';');
    for (let c of cookies) {
      c = c.trim();
      if (c.startsWith(name + '=')) return decodeURIComponent(c.substring(name.length + 1));
    }
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') : '';
  }

  function statusColumnMap() {
    return {
      'col-open': '0',
      'col-in_progress': '1',
      'col-in_testing': '2',
      'col-resolved': '3',
      'col-closed': '4',
    };
  }

  function initKanbanDragDrop() {
    kanbanSortableInstances.forEach(inst => inst.destroy());
    kanbanSortableInstances = [];

    document.querySelectorAll('.kanban-cards-container').forEach(container => {
      const sortable = new Sortable(container, {
        group: 'kanban',
        animation: 200,
        ghostClass: 'kanban-card-ghost',
        dragClass: 'kanban-card-dragging',
        delay: 150,
        delayOnTouchOnly: true,
        onEnd: function (evt) {
          const card = evt.item;
          const targetCol = card.closest('.kanban-column');
          const fromCol = evt.from.closest('.kanban-column');
          if (!targetCol || !fromCol) return;
          if (fromCol.id === targetCol.id) {
            updateKanbanCounts();
            return;
          }

          const newStatus = statusColumnMap()[targetCol.id];
          const ticketId = card.dataset.ticketId;
          const hasClient = card.dataset.hasClient === 'true';
          const fromContainer = evt.from;

          if (newStatus === '4' && hasClient) {
            fromContainer.insertBefore(card, evt.from.children[evt.oldIndex] || null);
            updateKanbanCounts();
            showHappyCodeModal(ticketId, card, targetCol.id, fromContainer, evt.oldIndex);
            return;
          }

          updateTicketStatus(ticketId, newStatus, null, card, fromContainer);
        },
      });
      kanbanSortableInstances.push(sortable);
    });
  }

  function updateTicketStatus(ticketId, newStatus, happyCode, card, fromContainer) {
    const formData = new FormData();
    formData.append('status', newStatus);
    if (happyCode) formData.append('happy_code', happyCode);

    fetch('/support/tickets/' + ticketId + '/update-status/', {
      method: 'POST',
      headers: { 'X-CSRFToken': getCSRFToken() },
      body: formData,
    })
      .then(res => res.json().then(data => ({ ok: res.ok, data })))
      .then(({ ok, data }) => {
        if (ok) {
          updateKanbanCounts();
          return;
        }
        if (card && fromContainer) {
          fromContainer.appendChild(card);
          updateKanbanCounts();
        }
        if (data.error) {
          Toastify({ text: data.error, duration: 3000, gravity: 'top', position: 'right', style: { background: '#dc3545' } }).showToast();
        }
      })
      .catch(() => {
        if (card && fromContainer) {
          fromContainer.appendChild(card);
          updateKanbanCounts();
        }
        Toastify({ text: 'Failed to update status. Please try again.', duration: 3000, gravity: 'top', position: 'right', style: { background: '#dc3545' } }).showToast();
      });
  }

  let pendingHappyCodeTicketId = null;
  let pendingHappyCodeCard = null;
  let pendingHappyCodeTargetCol = null;
  let pendingHappyCodeFromContainer = null;
  let pendingHappyCodeOldIndex = null;

  function showHappyCodeModal(ticketId, card, targetColId, fromContainer, oldIndex) {
    pendingHappyCodeTicketId = ticketId;
    pendingHappyCodeCard = card;
    pendingHappyCodeTargetCol = targetColId;
    pendingHappyCodeFromContainer = fromContainer;
    pendingHappyCodeOldIndex = oldIndex;

    const modal = new bootstrap.Modal(document.getElementById('kanbanHappyCodeModal'));
    const input = document.getElementById('kanbanHappyCodeInput');
    const error = document.getElementById('kanbanHappyCodeError');
    input.value = '';
    error.classList.add('d-none');
    modal.show();
  }

  const confirmBtn = document.getElementById('kanbanHappyCodeConfirmBtn');
  const input = document.getElementById('kanbanHappyCodeInput');
  const error = document.getElementById('kanbanHappyCodeError');
  const modalEl = document.getElementById('kanbanHappyCodeModal');

  if (confirmBtn) {
    confirmBtn.addEventListener('click', function () {
      const code = input.value.trim();
      if (!code) {
        error.classList.remove('d-none');
        return;
      }
      error.classList.add('d-none');

      const ticketId = pendingHappyCodeTicketId;
      const card = pendingHappyCodeCard;
      const fromContainer = pendingHappyCodeFromContainer;
      const targetColId = pendingHappyCodeTargetCol;

      const newStatus = statusColumnMap()[targetColId];

      const targetContainer = document.querySelector('#' + targetColId + ' .kanban-cards-container');
      if (targetContainer && card) targetContainer.appendChild(card);

      const modal = bootstrap.Modal.getInstance(modalEl);
      if (modal) modal.hide();

      updateTicketStatus(ticketId, newStatus, code, card, fromContainer);
    });
  }

  if (input) {
    input.addEventListener('input', function () {
      error.classList.add('d-none');
      this.value = this.value.toUpperCase();
    });
  }

  if (modalEl) {
    modalEl.addEventListener('hidden.bs.modal', function () {
      const card = pendingHappyCodeCard;
      const fromContainer = pendingHappyCodeFromContainer;
      if (card && fromContainer && !card.closest('.kanban-column')) {
        fromContainer.appendChild(card);
      }
      updateKanbanCounts();
      pendingHappyCodeTicketId = null;
      pendingHappyCodeCard = null;
      pendingHappyCodeTargetCol = null;
      pendingHappyCodeFromContainer = null;
      pendingHappyCodeOldIndex = null;
    });
  }

  document.addEventListener('click', function (e) {
    const card = e.target.closest('.kanban-card');
    if (card && card.dataset.detailUrl) {
      window.location.href = card.dataset.detailUrl;
    }
  });

  window.switchView = function (view) {
    const listBtn = document.getElementById('list-view-btn');
    const kanbanBtn = document.getElementById('kanban-view-btn');
    const listCont = document.getElementById('list-view-container');
    const kanbanCont = document.getElementById('kanban-view-container');
    const statsSection = document.getElementById('list-only-section');
    const filterSection = document.getElementById('filter-bar-section');

    if (view === 'list') {
      listBtn.classList.add('btn-primary', 'active');
      listBtn.classList.remove('btn-outline-primary');
      kanbanBtn.classList.add('btn-outline-primary');
      kanbanBtn.classList.remove('btn-primary', 'active');
      listCont.style.display = 'block';
      kanbanCont.style.display = 'none';
      statsSection.style.display = 'grid';
      filterSection.style.display = 'block';
      localStorage.setItem('ticket_view_pref', 'list');
    } else {
      kanbanBtn.classList.add('btn-primary', 'active');
      kanbanBtn.classList.remove('btn-outline-primary');
      listBtn.classList.add('btn-outline-primary');
      listBtn.classList.remove('btn-primary', 'active');
      listCont.style.display = 'none';
      kanbanCont.style.display = 'block';
      statsSection.style.display = 'none';
      filterSection.style.display = 'none';
      updateKanbanCounts();
      localStorage.setItem('ticket_view_pref', 'kanban');
    }
  };

  function updateKanbanCounts() {
    ['open', 'in_progress', 'in_testing', 'resolved', 'closed'].forEach(status => {
      const container = document.querySelector(`#col-${status} .kanban-cards-container`);
      if (container) {
        const cards = container.querySelectorAll('.kanban-card');
        const emptyState = container.querySelector('.kanban-empty-state');
        const count = cards.length;
        const countEl = document.getElementById(`count-${status}`);
        if (countEl) countEl.textContent = count;
        if (emptyState) emptyState.style.display = count === 0 ? 'flex' : 'none';
      }
    });
  }

  // ── Ticket Detail: Comments ─────────────────────────────────────────────────

  const fileInput = document.getElementById('comment-attachments-input');
  const attachBtn = document.getElementById('comment-attach-btn');
  const previewContainer = document.getElementById('comment-preview-container');
  const commentForm = document.querySelector('.new-comment-box')?.closest('form');
  const commentTextarea = document.getElementById('comment-textarea');
  const commentsList = document.querySelector('.comments-list');
  const commentsContainer = document.getElementById('comments-container');
  const loadMoreBtn = document.getElementById('btn-load-more');
  const loadMoreWrapper = document.getElementById('load-more-wrapper');
  let selectedFiles = [];

  const COMMENTS_PER_PAGE = 10;
  let oldestVisibleIndex = 0;

  function getCommentWrappers() {
    return document.querySelectorAll('.comment-wrapper');
  }

  function updateCommentVisibility() {
    const wrappers = getCommentWrappers();
    const total = wrappers.length;

    if (total <= COMMENTS_PER_PAGE || oldestVisibleIndex < COMMENTS_PER_PAGE) {
      wrappers.forEach(w => w.classList.remove('comment-hidden'));
      if (loadMoreWrapper) loadMoreWrapper.style.display = 'none';
      oldestVisibleIndex = 0;
      return;
    }

    wrappers.forEach((w, i) => {
      w.classList.toggle('comment-hidden', i < oldestVisibleIndex);
    });

    if (loadMoreWrapper) loadMoreWrapper.style.display = '';
  }

  function initCommentVisibility() {
    const wrappers = getCommentWrappers();
    const total = wrappers.length;
    if (total > COMMENTS_PER_PAGE) {
      oldestVisibleIndex = total - COMMENTS_PER_PAGE;
    }
    updateCommentVisibility();
  }

  if (loadMoreBtn) {
    loadMoreBtn.addEventListener('click', function () {
      oldestVisibleIndex = Math.max(0, oldestVisibleIndex - COMMENTS_PER_PAGE);
      updateCommentVisibility();
    });
  }

  initCommentVisibility();

  if (attachBtn && fileInput) {
    attachBtn.addEventListener('click', function (e) {
      e.preventDefault();
      fileInput.click();
    });

    fileInput.addEventListener('change', function () {
      handleFiles(this.files);
    });
  }

  function handleFiles(files) {
    const filesArray = Array.from(files);
    filesArray.forEach(file => {
      if (!selectedFiles.some(f => f.name === file.name && f.size === file.size)) {
        selectedFiles.push(file);
      }
    });
    updateInputAndPreview();
  }

  function updateInputAndPreview() {
    previewContainer.innerHTML = '';

    const dt = new DataTransfer();
    selectedFiles.forEach(file => dt.items.add(file));
    if (fileInput) fileInput.files = dt.files;

    selectedFiles.forEach((file, index) => {
      const previewItem = document.createElement('div');
      previewItem.className = 'comment-upload-preview-item';

      if (file.type.startsWith('image/')) {
        const img = document.createElement('img');
        img.src = URL.createObjectURL(file);
        img.onload = function () { URL.revokeObjectURL(this.src); };
        previewItem.appendChild(img);
      } else {
        const iconWrap = document.createElement('div');
        iconWrap.className = 'preview-file-icon';
        iconWrap.innerHTML = '<i class="bi bi-file-earmark-text"></i>';
        previewItem.appendChild(iconWrap);
      }

      previewItem.title = `${file.name} (${(file.size / 1024).toFixed(1)} KB)`;

      const removeBtn = document.createElement('button');
      removeBtn.type = 'button';
      removeBtn.className = 'remove-preview-btn';
      removeBtn.innerHTML = '×';
      removeBtn.addEventListener('click', function (e) {
        e.preventDefault();
        e.stopPropagation();
        selectedFiles.splice(index, 1);
        updateInputAndPreview();
      });
      previewItem.appendChild(removeBtn);
      previewContainer.appendChild(previewItem);
    });
  }

  const emojiBtn = document.getElementById('comment-emoji-btn');

  if (emojiBtn && commentTextarea) {
    const emojis = ['😊', '👍', '🔥', '💻', '💡', '⚠️', '✅', '❌', 'ℹ️'];
    const picker = document.createElement('div');
    picker.className = 'emoji-picker-popup d-none';

    emojis.forEach(emo => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.textContent = emo;
      btn.className = 'emoji-btn-item';
      btn.addEventListener('click', function (e) {
        e.preventDefault();
        e.stopPropagation();
        const start = commentTextarea.selectionStart;
        const end = commentTextarea.selectionEnd;
        const text = commentTextarea.value;
        commentTextarea.value = text.substring(0, start) + emo + text.substring(end);
        commentTextarea.focus();
        commentTextarea.selectionStart = commentTextarea.selectionEnd = start + emo.length;
        picker.classList.add('d-none');
      });
      picker.appendChild(btn);
    });

    emojiBtn.parentNode.classList.add('emoji-picker-container');
    emojiBtn.parentNode.appendChild(picker);

    emojiBtn.addEventListener('click', function (e) {
      e.preventDefault();
      e.stopPropagation();
      picker.classList.toggle('d-none');
    });

    document.addEventListener('click', function (e) {
      if (!picker.contains(e.target) && e.target !== emojiBtn) {
        picker.classList.add('d-none');
      }
    });
  }

  if (commentForm && commentTextarea && commentsList) {
    commentForm.addEventListener('submit', function (e) {
      const content = commentTextarea.value.trim();
      if (!content) return;

      e.preventDefault();

      const submitBtn = commentForm.querySelector('.btn-post-comment');
      const originalHTML = submitBtn.innerHTML;
      submitBtn.disabled = true;
      submitBtn.innerHTML = 'Posting...';

      const formData = new FormData(commentForm);

      fetch(commentForm.action, {
        method: 'POST',
        body: formData,
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
      })
        .then(response => response.json())
        .then(data => {
          if (data.success) {
            const emptyState = document.getElementById('comment-empty-state');
            if (emptyState) emptyState.remove();

            const wrapper = document.createElement('div');
            wrapper.className = 'comment-wrapper';
            wrapper.innerHTML = data.html;
            commentsList.appendChild(wrapper);

            const countBadge = document.querySelector('.section-title .badge');
            if (countBadge) countBadge.textContent = parseInt(countBadge.textContent) + 1;

            updateCommentVisibility();

            if (commentsContainer) commentsContainer.scrollTop = commentsContainer.scrollHeight;

            commentTextarea.value = '';
            selectedFiles = [];
            updateInputAndPreview();
          } else {
            alert(data.error || 'An error occurred while posting your comment.');
          }
        })
        .catch(error => {
          console.error('Error posting comment:', error);
          alert('An unexpected error occurred. Please try again.');
        })
        .finally(() => {
          submitBtn.disabled = false;
          submitBtn.innerHTML = originalHTML;
        });
    });
  }

  // ── Initialisation ───────────────────────────────────────────────────────────

  const pref = localStorage.getItem('ticket_view_pref');
  if (pref === 'kanban') {
    window.switchView('kanban');
  } else {
    updateKanbanCounts();
  }
  initKanbanDragDrop();
});
