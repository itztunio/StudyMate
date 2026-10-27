// ChatBond AI - Main Client Script
document.addEventListener('DOMContentLoaded', function () {
  // 1. Mobile Menu Toggle
  const menuToggle = document.getElementById('menuToggle');
  const navLinks = document.getElementById('navLinks');
  if (menuToggle && navLinks) {
    menuToggle.addEventListener('click', function () {
      navLinks.classList.toggle('show');
    });
  }

  // 2. Drag & Drop Upload Handling
  const dropZone = document.getElementById('dropZone');
  const fileInput = document.getElementById('chatFileInput');
  const fileNameBadge = document.getElementById('fileNameBadge');
  const selectedNameText = document.getElementById('selectedFileName');
  const analyzeBtn = document.getElementById('analyzeBtn');

  if (dropZone && fileInput) {
    // Click dropZone to open file dialog
    dropZone.addEventListener('click', function (e) {
      if (e.target.tagName !== 'BUTTON' && e.target !== fileInput) {
        fileInput.click();
      }
    });

    ['dragenter', 'dragover'].forEach(eventName => {
      dropZone.addEventListener(eventName, function (e) {
        e.preventDefault();
        e.stopPropagation();
        dropZone.classList.add('drag-over');
      }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
      dropZone.addEventListener(eventName, function (e) {
        e.preventDefault();
        e.stopPropagation();
        dropZone.classList.remove('drag-over');
      }, false);
    });

    dropZone.addEventListener('drop', function (e) {
      const dt = e.dataTransfer;
      const files = dt.files;
      if (files.length > 0) {
        fileInput.files = files;
        updateFileInfo(files[0]);
      }
    });

    fileInput.addEventListener('change', function () {
      if (fileInput.files.length > 0) {
        updateFileInfo(fileInput.files[0]);
      }
    });
  }

  function updateFileInfo(file) {
    if (!file) return;
    if (fileNameBadge && selectedNameText) {
      selectedNameText.textContent = `${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
      fileNameBadge.style.display = 'inline-flex';
    }
    if (analyzeBtn) {
      analyzeBtn.disabled = false;
      analyzeBtn.classList.add('pulse');
    }
  }

  // 3. AI Reply Generator Page Logic
  const replyForm = document.getElementById('replyGeneratorForm');
  const toneButtons = document.querySelectorAll('.tone-btn');
  const selectedToneInput = document.getElementById('selectedTone');
  const repliesContainer = document.getElementById('repliesContainer');
  const repliesLoading = document.getElementById('repliesLoading');
  const repliesError = document.getElementById('repliesError');

  if (toneButtons.length > 0 && selectedToneInput) {
    toneButtons.forEach(btn => {
      btn.addEventListener('click', function () {
        toneButtons.forEach(b => b.classList.remove('active'));
        this.classList.add('active');
        selectedToneInput.value = this.getAttribute('data-tone');
      });
    });
  }

  if (replyForm) {
    replyForm.addEventListener('submit', async function (e) {
      e.preventDefault();
      const message = document.getElementById('receivedMessage').value.trim();
      const context = document.getElementById('messageContext').value.trim();
      const tone = selectedToneInput ? selectedToneInput.value : 'friendly';

      if (!message) {
        alert('Please enter a message to generate replies.');
        return;
      }

      // UI States
      if (repliesLoading) repliesLoading.style.display = 'block';
      if (repliesContainer) repliesContainer.innerHTML = '';
      if (repliesError) repliesError.style.display = 'none';

      try {
        const response = await fetch('/generate-replies', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ message, context, tone })
        });

        const data = await response.json();
        if (repliesLoading) repliesLoading.style.display = 'none';

        if (data.success && data.replies && data.replies.length > 0) {
          renderReplies(data.replies);
        } else {
          showRepliesError(data.error || 'Failed to generate replies. Please try again.');
        }
      } catch (err) {
        if (repliesLoading) repliesLoading.style.display = 'none';
        showRepliesError('Network error connecting to AI service. Please check your connection.');
      }
    });
  }

  function renderReplies(replies) {
    if (!repliesContainer) return;
    repliesContainer.innerHTML = '';
    replies.forEach((reply, index) => {
      const card = document.createElement('div');
      card.className = 'reply-card';
      card.innerHTML = `
        <div class="reply-text" id="replyText_${index}">${escapeHtml(reply)}</div>
        <div class="reply-actions">
          <button class="btn btn-sm btn-secondary copy-btn" data-target="replyText_${index}">
            📋 Copy Reply
          </button>
        </div>
      `;
      repliesContainer.appendChild(card);
    });

    // Attach copy button listeners
    document.querySelectorAll('.copy-btn').forEach(btn => {
      btn.addEventListener('click', function () {
        const targetId = this.getAttribute('data-target');
        const textToCopy = document.getElementById(targetId).innerText;
        navigator.clipboard.writeText(textToCopy).then(() => {
          const originalText = this.innerHTML;
          this.innerHTML = '✅ Copied!';
          setTimeout(() => {
            this.innerHTML = originalText;
          }, 2000);
        });
      });
    });
  }

  function showRepliesError(msg) {
    if (repliesError) {
      repliesError.textContent = msg;
      repliesError.style.display = 'block';
    }
  }

  function escapeHtml(str) {
    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }
});
