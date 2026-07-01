document.addEventListener('DOMContentLoaded', function () {
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

    if (loadMoreWrapper) {
      loadMoreWrapper.style.display = '';
    }
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
    if (fileInput) {
      fileInput.files = dt.files;
    }

    selectedFiles.forEach((file, index) => {
      const previewItem = document.createElement('div');
      previewItem.className = 'comment-upload-preview-item';

      const isImage = file.type.startsWith('image/');
      if (isImage) {
        const img = document.createElement('img');
        img.src = URL.createObjectURL(file);
        img.onload = function() {
          URL.revokeObjectURL(this.src);
        };
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

      btn.addEventListener('click', function(e) {
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

    emojiBtn.addEventListener('click', function(e) {
      e.preventDefault();
      e.stopPropagation();
      picker.classList.toggle('d-none');
    });

    document.addEventListener('click', function(e) {
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
      submitBtn.disabled = true;
      submitBtn.innerHTML = 'Posting...';

      const formData = new FormData(commentForm);

      fetch(commentForm.action, {
        method: 'POST',
        body: formData,
        headers: {
          'X-Requested-With': 'XMLHttpRequest'
        }
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

          if (commentsContainer) {
            commentsContainer.scrollTop = commentsContainer.scrollHeight;
          }

          commentTextarea.value = '';
          selectedFiles = [];
          updateInputAndPreview();
        }
      })
      .catch(error => console.error('Error posting comment:', error))
      .finally(() => {
        submitBtn.disabled = false;
        submitBtn.innerHTML = 'Post Comment <i class="bi bi-send-fill"></i>';
      });
    });
  }
});
